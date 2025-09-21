# server/workflow/agents/retrieval/rag_indexing_agent.py

"""
RAG 인덱싱 에이전트
"""

from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from langchain.schema import Document
from server.workflow.agents.base.base_utility_agent import BaseUtilityAgent, AgentState
from server.db.dao.analysis_history_dao import insert_bulk_analysis_history, delete_analysis_history_by_project_id_and_date
from server.db.dao.entry_point_list_dao import get_entry_point_list_by_project
from server.db.model import EntryPoint
from server.db.schema import AnalysisHistoryCreate
from server.db.database import run_with_db_session
from server.utils.document_utils import generate_document_id
from server.utils.file_utils import load_json
from server.utils.vectorstore_utils import save_documents_to_faiss_vector_store, get_vectorstore_path
from server.utils.constants import IndexInputType, RagSourceType, AgentType, AgentResultGroupKey

class RAGIndexingAgent(BaseUtilityAgent):
    def __init__(self, session_id: str = None, project_id: str = None):
        super().__init__(role=AgentType.RAG_INDEXER, session_id=session_id, project_id=project_id)

    def _run_internal(self, state: AgentState) -> AgentState:
        agent_state = state["autodiagenti_state"]
        project_id = agent_state.get("project_id", "")
        project_name = agent_state.get("project_name", "")
        analyzed_date = agent_state.get("analyzed_date", datetime.now().strftime("%Y%m%d"))
        
        agent_result = agent_state.get("agent_result", {})
        source_data = agent_result.get(AgentResultGroupKey.CURRENT_SOURCE_DATA, {})
        input_type = source_data.get("input_type", "")
        
        # 문서 생성 (split은 적용하지 않음 - 이미 메서드 단위 분할된 형태)
        documents: List[Document] = self._create_document(project_id=project_id, project_name=project_name, input_type=input_type, source_data=source_data)
        
        # 벡터 변환 및 FAISS 벡터 스토어 저장
        save_documents_to_faiss_vector_store(project_id=project_id, documents=documents)
        
        # 분석결과 데이터 저장
        if input_type == IndexInputType.SEQUENCE_DIAGRAM:
            file_info = agent_state.get("file_info", {})
            filter_options = agent_state.get("filter_options", {})
            self._save_analysis_result_to_db(project_id=project_id, project_name=project_name, analyzed_date=analyzed_date, file_info=file_info, filter_options=filter_options, docs=documents)
        
        result = {
            "project_id": project_id,
            "input_type": input_type,
            "chunks_size": len(documents),
            "vector_store": "faiss",
            "vector_store_path": get_vectorstore_path(project_id=project_id)
        }

        return self.wrap_agent_result(AgentResultGroupKey.RAG_INDEXING_RESULT, result)

    def _create_document(self, project_id, project_name, input_type, source_data) -> List[Document]:
        documents: List[Document] = []
        
        # input_type에 따라 처리
        if input_type == IndexInputType.PARSER: # 다건            
            output_dir = source_data.get("output_dir", "")
            
            if not output_dir:
                self.logger.warning(f"❌ 처리 대상 문서가 없습니다(output_dir is empty). input_type:[{input_type}]")
                return []
            
            files = Path(output_dir).rglob("*.json")
            
            # Document 변환
            for file_path in files:
                doc: Document = None            
                if file_path.name.endswith("_call_tree.json"):
                    doc = self._to_document_parser(file_path, project_id, project_name)
                    if doc is not None:
                        documents.append(doc)
                elif file_path.name.endswith("_comments.json"):
                    doc = self._to_document_comments(file_path, project_id, project_name)
                    if doc is not None:
                        documents.append(doc)
                if file_path.name.endswith("_methods.json") and not file_path.name.startswith("all_"):
                    doc = self._to_document_code(file_path, project_id, project_name)
                    if doc is not None:
                        documents.append(doc)
        elif input_type == IndexInputType.CALLTREE: # 다건
            call_tree_info_list = source_data.get("call_tree_info")
            if call_tree_info_list is not None:
                documents = self._to_documents_calltree(project_id=project_id, project_name=project_name, call_tree_info_list=call_tree_info_list)
        elif input_type == IndexInputType.LLM_CODE: # 다건
            code_analysis_result = source_data
            if code_analysis_result is not None:
                documents = self._to_documents_llm_code_summaries(project_id=project_id, project_name=project_name, code_analysis_result=code_analysis_result)
        elif input_type == IndexInputType.CALLTREE_SUMMARY: # 다건
            call_tree_summary_result = source_data
            if call_tree_summary_result is not None:
                documents = self._to_documents_llm_call_tree_summaries(project_id=project_id, project_name=project_name, call_tree_summary_result=call_tree_summary_result)
        elif input_type == IndexInputType.SEQUENCE_DIAGRAM: # 다건
            sequence_diagram_result = source_data
            if sequence_diagram_result is not None:
                documents = self._to_documents_llm_sequence_diagrams(project_id=project_id, project_name=project_name, sequence_diagram_result=sequence_diagram_result)
            
        return documents

    def _to_document_parser(self, path: Path, project_id: str, project_name: str) -> Document:
        """
        PARSER 타입 JSON 파일을 LangChain Document 객체로 변환

        Args:
            path (Path): PARSER JSON 파일 경로
            project_id (str): 분석 세션에 해당하는 프로젝트 ID(쿼리 ID)

        Returns:
            Document: page_content와 metadata가 포함된 LangChain 문서 객체
        """

        # JSON 파일 로딩
        parser_json = load_json(path)
        
        if not parser_json:
            return None
        
        # 기본 메타데이터 추출
        file_path = parser_json.get("file_path")
        package_name = parser_json.get("package_name")
        analyzed_at = parser_json.get("analyzed_at", datetime.now().isoformat())
        call_edges = parser_json.get("call_edges", [])
        method_meta_map = parser_json.get("method_meta_map", {})

        # 문서ID 생성
        document_id = generate_document_id(source_type=RagSourceType.PARSER, project_id=project_id, file_path=file_path)

        # page_content 요약용 텍스트 생성
        method_lines = []
        for method_fqn, meta in method_meta_map.items():
            label = " (entry_point)" if meta.get("entry_point") else ""
            method_lines.append(f"- {method_fqn}{label}")
        methods_summary = "\n".join(method_lines)

        # LLM 요약을 위한 page_content 구성
        page_content = f"""
            [{project_name}] {file_path}
            
            package {package_name}
            
            Methods:
            {methods_summary}
            
            Note: See metadata['call_edges'] and metadata['method_meta_map'] for full context.
        """.strip()

        # Document 객체 생성
        return Document(
            page_content=page_content,
            metadata={
                "source_type": RagSourceType.PARSER,
                "document_id": document_id,
                "project_id": project_id,
                "project_name": project_name,
                "file_path": file_path,
                "package_name": package_name,
                "analyzed_at": analyzed_at,
                "call_edges": call_edges,
                "method_meta_map": method_meta_map,
            }
        )

    def _to_document_comments(self, path: Path, project_id: str, project_name: str) -> Document:
        """
        COMMENTS 타입 JSON 파일을 LangChain Document 객체로 변환

        Args:
            path (Path): COMMENTS JSON 파일 경로
            project_id (str): 분석 세션에 해당하는 프로젝트 ID(쿼리 ID)

        Returns:
            Document: page_content와 metadata가 포함된 LangChain 문서 객체
        """

        # JSON 파일 로딩
        comments_json = load_json(path)
        
        if not comments_json:
            return None
        
        # 기본 정보 유추
        file_name = path.name
        analyzed_at = datetime.now().isoformat()
        file_path = comments_json.get("file_path", "")
        
        # 문서ID 생성
        document_id = generate_document_id(source_type=RagSourceType.COMMENTS, project_id=project_id, file_path=file_path)

        # 요약용 comment 목록 구성
        comment_lines = []
        for method_fqn, meta in comments_json.items():
            label = " (entry_point)" if meta.get("entry_point") else ""
            comment = meta.get("comment", "")
            
            if comment:
                comment = str(comment).strip()
                comment_lines.append(f"- {method_fqn}{label}\n  ⤷ {comment}")
        comments_summary = "\n".join(comment_lines)

        # LLM 요약을 위한 page_content 구성
        page_content = f"""
            [{project_name}] {file_name}

            Method Comments:
            {comments_summary}
        """.strip()

        # Document 객체 생성
        return Document(
            page_content=page_content,
            metadata={
                "source_type": RagSourceType.COMMENTS,
                "document_id": document_id,
                "project_id": project_id,
                "project_name": project_name,
                "file_name": file_name,
                "analyzed_at": analyzed_at,
                "raw_comments": comments_json,
            }
        )

    def _to_document_code(self, path: Path, project_id: str, project_name:str) -> Document:
        """
        CODE 타입 JSON 파일을 LangChain Document 객체로 변환
        (Java 메서드별 코드 정보)

        Args:
            path (Path): methods.json 파일 경로
            project_id (str): 분석 세션에 해당하는 프로젝트 ID(쿼리 ID)

        Returns:
            Document: page_content와 metadata가 포함된 LangChain 문서 객체
        """

        # JSON 파일 로딩
        methods_json = load_json(path)
        
        if not methods_json:
            return None
        
        # 기본 정보 유추
        file_name = path.name
        analyzed_at = datetime.now().isoformat()
        first_method = next(iter(methods_json.values()))
        file_path = first_method.get("file_path", "")
        
        # 문서ID 생성
        document_id = generate_document_id(source_type=RagSourceType.CODE, project_id=project_id, file_path=file_path)

        # page_content 요약용 텍스트 구성 
        method_lines = []
        for method_fqn in methods_json.keys():
            method_lines.append(f"- {method_fqn}")
        method_summary = "\n".join(method_lines)

        page_content = f"""
            [{project_name}] {file_name}

            Java Methods:
            {method_summary}

            Note: See metadata['methods'] for full method bodies.
        """.strip()

        # Document 객체 생성
        return Document(
            page_content=page_content,
            metadata={
                "source_type": RagSourceType.CODE,
                "document_id": document_id,
                "project_id": project_id,
                "project_name": project_name,
                "file_name": file_name,
                "analyzed_at": analyzed_at,
                "methods": methods_json,
            }
        )
        
    def _to_documents_calltree(self, project_id: str, project_name: str, call_tree_info_list: List[Dict[str, Any]]) -> List[Document]:
        """
        CALLTREE 재귀분석 결과를 LangChain Document 리스트로 변환

        Args:
            project_id (str): 해당 분석의 프로젝트 ID
            project_name (str): 해당 분석의 프로젝트명
            calltree_info_list (List[Dict[str, Any]]): CALLTREE 재귀분석 결과 리스트

        Returns:
            List[Document]: RAG 저장용 Document 객체 리스트
        """
        documents = []

        for item in call_tree_info_list:
            entry_point = item.get("entry_point")
            file_path = item.get("file_path")
            project_name = item.get("project_name")
            
            # document_id는 entry_point 기준
            document_id = generate_document_id(source_type=RagSourceType.CALLTREE, project_id=project_id, entry_point=entry_point)
            
            doc = Document(
                page_content="\n".join(item.get("call_sequence", [])),
                metadata={
                    "source_type": RagSourceType.CALLTREE,
                    "document_id": document_id,
                    "project_id": project_id,
                    "project_name": project_name,
                    "file_path": file_path,
                    "entry_point": entry_point,
                    "call_sequence": item.get("call_sequence", []),
                    "call_tree": item.get("call_tree", {}),
                    "depth": item.get("depth"),
                    "analyzed_at": item.get("analyzed_at"),
                }
            )
            documents.append(doc)
        
        return documents
    
    def _to_documents_llm_code_summaries(self, project_id: str, project_name: str, code_analysis_result: Dict) -> List[Document]:
        """
        LLM 기반 코드 요약 결과 리스트를 LangChain Document 리스트로 변환

        Args:
            project_id (str): 해당 분석의 프로젝트 ID
            project_name (str): 해당 분석의 프로젝트명
            method_summaries (List[dict]): LLM 코드 분석 결과 리스트

        Returns:
            List[Document]: 변환된 LangChain 문서 리스트
        """
        documents = []
        
        method_analyses: List[dict] = code_analysis_result.get("code_analysis_info", [])
        llm_model = code_analysis_result.get("llm_model")
        llm_version = code_analysis_result.get("llm_version")
        llm_temperature = code_analysis_result.get("llm_temperature")
        
        for item in method_analyses:
            file_path = item.get("file_path")
            method_fqn = item.get("method_fqn")
            summary = item.get("summary")
            
            # document_id는 method_fqn 기준
            document_id = generate_document_id(source_type=RagSourceType.CODE_ANALYSIS, project_id=project_id, method_fqn=method_fqn)
            
            if not method_fqn:
                self.logger.warning(f"🌧️ 필수 정보 누락으로 SKIP. method_fqn:[{method_fqn}], item: [{item}]")
                continue 
            
            metadata = {
                "source_type": RagSourceType.CODE_ANALYSIS,
                "document_id": document_id,
                "project_id": project_id,
                "project_name": project_name,
                "file_path": file_path,
                "method_fqn": method_fqn,
                "package_name": item.get("package_name"),
                "class_name": item.get("class_name"),
                "method_signature": item.get("method_signature"),
                "modifiers": item.get("modifiers"),
                "parameters": item.get("parameters"),
                "return_type": item.get("return_type"),
                "analyzed_at": item.get("analyzed_at"),
                "description": item.get("description") if item.get("description") else None,
                "llm_model": llm_model,
                "llm_version": llm_version,
                "llm_temperature": llm_temperature
            }
            
            if summary:
                metadata["summary"] = summary

            doc = Document(
                page_content=summary,
                metadata=metadata
            )
            documents.append(doc)

        return documents
    
    def _to_documents_llm_call_tree_summaries(self, project_id: str, project_name: str, call_tree_summary_result: Dict) -> List[Document]:
        """
        LLM 기반 CALLTREE_SUMMARY 결과를 LangChain Document 리스트로 변환

        Args:
            project_id (str): 해당 분석의 프로젝트 ID
            project_name (str): 해당 분석의 프로젝트명
            call_tree_summaries (List[Document]): CALLTREE_SUMMARY 문서 리스트

        Returns:
            List[Document]: document_id가 포함된 문서 리스트
        """
        updated_documents = []
        
        call_tree_summaries: List[Document] = call_tree_summary_result.get("call_tree_summary_info", [])
        llm_model = call_tree_summary_result.get("llm_model")
        llm_version = call_tree_summary_result.get("llm_version")
        llm_temperature = call_tree_summary_result.get("llm_temperature")

        for doc in call_tree_summaries:
            metadata = doc.metadata.copy()
            entry_point = metadata.get("entry_point")
            
            # document_id는 entry_point 기준
            document_id = generate_document_id(source_type=RagSourceType.CALLTREE_SUMMARY, project_id=project_id, entry_point=entry_point)
            
            metadata["document_id"] = document_id
            metadata["llm_model"] = llm_model
            metadata["llm_version"] = llm_version
            metadata["llm_temperature"] = llm_temperature
            updated_documents.append(Document(page_content=doc.page_content, metadata=metadata))

        return updated_documents
    
    def _to_documents_llm_sequence_diagrams(self, project_id: str, project_name: str, sequence_diagram_result: dict) -> List[Document]:
        """
        LLM 기반 SEQUENCE_DIAGRAM 결과를 LangChain Document 리스트로 변환

        Args:
            project_id (str): 해당 분석의 프로젝트 ID
            project_name (str): 해당 분석의 프로젝트명
            sequence_diagrams (List[Document]): SEQUENCE_DIAGRAM 결과 리스트

        Returns:
            List[Document]: document_id가 포함된 문서 리스트
        """
        documents = []
        
        sequence_diagrams = sequence_diagram_result.get("sequence_diagram_info", [])
        llm_model = sequence_diagram_result.get("llm_model")
        llm_version = sequence_diagram_result.get("llm_version")
        llm_temperature = sequence_diagram_result.get("llm_temperature")
        
        for item in sequence_diagrams:
            entry_point = item.get("entry_point")
            mermaid_code = item.get("mermaid_code", "")
            
            # document_id는 entry_point 기준
            document_id = generate_document_id(source_type=RagSourceType.SEQUENCE_DIAGRAM, project_id=project_id, entry_point=entry_point)
            
            doc = Document(
                page_content=mermaid_code,
                metadata={
                    "source_type": RagSourceType.SEQUENCE_DIAGRAM,
                    "document_id": document_id,
                    "project_id": project_id,
                    "project_name": project_name,
                    "entry_point": entry_point,
                    "mermaid_code": mermaid_code,
                    "summary_title": item.get("summary_title"),
                    "insight": item.get("insight"),
                    "reasoning": item.get("reasoning"),
                    "method_definitions": item.get("method_definitions"),
                    "llm_model": llm_model,
                    "llm_version": llm_version,
                    "llm_temperature": llm_temperature,
                    "analyzed_at": item.get("analyzed_at"),
                }
            )
            documents.append(doc)
        
        return documents

    def _save_analysis_result_to_db(self, project_id: str, project_name: str, analyzed_date: str, file_info: Dict, filter_options: Dict, docs: List[Document]):
        try:
            file_path = file_info.get("file_path", "")
            file_name = file_info.get("file_name", "")
            orig_file_name = file_info.get("orig_file_name", "")
            include_method_text = filter_options.get("include_method_text", True)
            custom_annotations = filter_options.get("custom_annotations", None)
            exclude_packages = filter_options.get("exclude_packages", None)
            
            entry_point_info_list: list[EntryPoint] = run_with_db_session (get_entry_point_list_by_project, project_id=project_id)
            entry_point_info_dict: Dict[str, EntryPoint] = {entry_point_info.entry_point: entry_point_info for entry_point_info in entry_point_info_list }
            
            data = []
            for doc in docs:
                meta = doc.metadata
                entry_point = meta.get("entry_point")
                entry_point_info: EntryPoint = entry_point_info_dict.get(entry_point)
                
                if not entry_point_info:
                    self.logger.warning(f"🌧️ entry_point_info is empty. project_id: [{project_id}], entry_point: [{entry_point}]")
                    continue
                
                result = {
                    "entry_point": meta.get("entry_point"),
                    "llm_model": meta.get("llm_model"),
                    "llm_version": meta.get("llm_version"),
                    "llm_temperature": meta.get("llm_temperature"),
                    "mermaid_code": meta.get("mermaid_code"),
                    "summary_title": meta.get("summary_title"),
                    "insight": meta.get("insight"),
                    "reasoning": meta.get("reasoning"),
                    "method_definitions": meta.get("method_definitions"),
                    "analyzed_at": meta.get("analyzed_at")
                }
                
                analysis_result = AnalysisHistoryCreate(
                    analyzed_date=analyzed_date,
                    project_id=project_id,
                    entry_point=entry_point,
                    session_id=self.session_id,
                    project_name=project_name,
                    uploaded_path=file_path,
                    file_name=file_name,
                    orig_file_name = orig_file_name,
                    exclude_packages=exclude_packages,
                    custom_annotations=custom_annotations,
                    include_method_text=include_method_text,
                    api_name=entry_point_info.api_name,
                    api_method=entry_point_info.api_method,
                    annotation=entry_point_info.annotation,
                    llm_model=meta.get("llm_model"),
                    llm_version=meta.get("llm_version"),
                    temperature=meta.get("llm_temperature"),
                    mermaid_code=meta.get("mermaid_code"),
                    summary_title=meta.get("summary_title"),
                    insight=meta.get("insight"),
                    reasoning=meta.get("reasoning"),
                    analysis_results=result,
                    analyzed_at=meta.get("analyzed_at")
                )
                data.append(analysis_result)
                
            if data:
                del_count = run_with_db_session(delete_analysis_history_by_project_id_and_date, project_id=project_id, analyzed_date=analyzed_date)
                result = run_with_db_session(insert_bulk_analysis_history, data)
            else:
                self.logger.info(f"📢 Analysis History 등록 대상 데이터가 없음. project_id:{project_id}")
        except Exception as err:
            self.logger.error(f"❌ Analysis History 등록 오류 err:{err}, cause: {err.__cause__}")
