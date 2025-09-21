# server/workflow/agents/analyze/code_analysis_agent.py

""" 
코드 분석 에이전트
"""

import os
import time
import asyncio
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from langchain.schema import Document
from langchain.schema import SystemMessage, HumanMessage
from langchain.prompts import PromptTemplate
from openai import LengthFinishReasonError
from server.utils.config import get_llm_with_custom
from server.utils.constants import AgentType, AgentResultGroupKey, DirInfo, RagSourceType, IndexInputType, LLMModel
from server.utils.document_retrieval_utils import load_documents_by_source_type
from server.utils.file_utils import load_json
from server.workflow.agents.base.base_llm_agent import BaseLLMAgent, LLMAgentState
from server.utils.config import settings

class InsightLLMOutput(BaseModel):
    method_fqn: str = Field(description="Method FQN")
    summary: str = Field(description="Summary Method Description")
    description: str = Field(description="메서드 구조 및 흐름에 대한 절차적 설명")

class CodeAnalysisAgent(BaseLLMAgent):
    def __init__(self, session_id: str = None, project_id: str = None):
        system_prompt = (
            "You are an expert in analyzing Java (Spring-based) methods and summarizing their behavior. "
            "Your task is to read the given method data (including method text, comments, and metadata) and generate two outputs:\n"
            "- A summary: a concise 2–3 sentence description of what the method does (including its main logic).\n"
            "- A description: a step-by-step explanation of how the method operates.\n\n"
            "Guidelines:\n"
            "- Use all available inputs: methodText, comment, and context metadata.\n"
            "- If both methodText and comment are missing, return an empty result.\n"
            "- Do not rely on assumptions or external knowledge; only use provided data.\n"
            "- Output must be in Korean.\n"
            "- Do not include any quotation marks.\n"
            "- Ensure that the output follows the format exactly, including punctuation and curly braces '{}':\n"
            "{ 'method_fqn': '...', 'summary': '...', 'description': '...' }"
        )

        super().__init__(system_prompt=system_prompt, role=AgentType.CODE_ANALYSIS, session_id=session_id, project_id=project_id)

    def _create_prompt(self, state: LLMAgentState) -> Optional[str]:
        pass
    
    def get_prompt(self, method_meta: Dict) -> List:
        method_fqn = method_meta.get("method_fqn", "")
        method_text = method_meta.get("method_text", "")
        comment = method_meta.get("comment", "")
        method_signature = method_meta.get("method_signature", "")
        return_type = method_meta.get("return_type", "")
        modifiers = method_meta.get("modifiers", [])
        parameters = method_meta.get("parameters", [])
        file_path = method_meta.get("file_path", "")
        package_name = method_meta.get("package_name", "")
        class_name = method_meta.get("class_name", "")
    
        # 프롬프트 템플릿을 위해 개별정의함
        messages = [SystemMessage(content=self.system_prompt)]
        
        human_prompt_template = PromptTemplate(
                                    input_variables=["method_fqn", "method_text", "comment", "method_signature", "return_type", "modifiers", "parameters", "file_path", "package_name", "class_name"],
                                    template = """
                                        자바(Spring 기반) 시스템의 메서드 정보가 주어졌습니다.

                                        **주의**: method_text와 comment가 모두 비어 있을 경우, 분석 결과를 생성할 수 없습니다.  
                                        - 이 경우, 아래와 같이 출력하세요:  
                                        {{ "method_fqn": "...", "summary": "", "description": "" }}

                                        당신의 역할은 자바 메서드 분석 전문가로서, 다음 작업을 수행해야 합니다:
                                        - 주어진 메서드 정보(method_text 또는 comment)를 바탕으로 해당 메서드가 어떤 기능을 수행하는지 분석하고 요약합니다.
                                        - method_text와 comment 중 **가능한 정보를 활용하여 분석**하며, 둘 중 하나만 제공될 수도 있습니다.
                                        - context 정보를 통해 메서드의 정의 위치, 접근 범위, 파라미터 등을 이해하고 분석에 참고합니다.

                                        요약 항목 정의:
                                        - summary: 메서드의 핵심 기능에 대한 요약 설명 (2~3문장)
                                        - description: 메서드 내부 구조 및 처리 흐름에 대한 절차적 설명

                                        다음 형식으로 정확히 출력하세요:
                                        {{
                                            "method_fqn": "...",           // 예: "sg.sample.controller.AuthController.login(java.util.Map<java.lang.String, java.lang.String>)"
                                            "summary": "...",              // 예: "사용자 로그인 요청을 처리하고 인증 토큰을 생성합니다."
                                            "description": "..."           // 예: "사용자 입력을 검증한 후, getUser를 호출하여 사용자 정보를 조회하고, 이후 generateToken으로 인증 토큰을 생성합니다."
                                        }}

                                        입력값:
                                        - method_fqn:
                                        [{method_fqn}]

                                        - method_text:
                                        [{method_text}]

                                        - comment:
                                        [{comment}]

                                        - context 정보:
                                        - 메서드 시그니처:
                                        [{method_signature}]

                                        - 반환 타입:
                                        [{return_type}]

                                        - 접근 제어자 및 기타 키워드:
                                        [{modifiers}]

                                        - 파라미터 목록:
                                        [{parameters}]

                                        - 선언 위치:
                                            파일 경로: [{file_path}]
                                            패키지명: [{package_name}]
                                            클래스명: [{class_name}]
                                    """
                                )
    
        messages.append(HumanMessage(content=human_prompt_template.format(method_fqn=method_fqn, method_text=method_text, comment=comment, method_signature=method_signature, return_type=return_type, modifiers=modifiers, parameters=parameters, file_path=file_path, package_name=package_name, class_name=class_name)))
        return messages
    
    def _run_internal(self, state: LLMAgentState) -> LLMAgentState:
        agent_state = state["autodiagenti_state"]
        project_id = agent_state.get("project_id", "")
        project_name = agent_state.get("project_name", "")
        
        # 모델 정보
        model_info: LLMModel = agent_state.get("llm_model_info")
        
        # 모델 선언
        llm_model = get_llm_with_custom(llm_model=model_info.model_name, llm_version=model_info.version)
        
        # parser_documents 에서 모든 callEdges 수집, caller_set 설정
        parser_documents: List[Document] = load_documents_by_source_type(project_id=project_id, source_type=RagSourceType.PARSER)
        
        all_call_edges = []
        for doc in parser_documents:
            meta = doc.metadata
            
            # callEdges 수집
            call_edges = meta.get("call_edges", [])
            all_call_edges.extend(call_edges)
        
        caller_set = set(edge['caller'] for edge in all_call_edges)
        
        # method 데이터 추출
        all_methods: List[Dict] = self._load_methods_from_rag(project_id=project_id)
        
        new_method_meta_list = []
        
        # 메서드 FQN 목록 추출
        output_dir = os.path.join(DirInfo.PARSER_OUTPUT_DIR, project_id, project_name)
        method_fqn_path = os.path.join(output_dir, settings.ALL_METHODS_FILE_NAME)
        valid_method_fqns: set[str] = set(load_json(method_fqn_path))
        
        target_methods = []
        
        # 메서드 별로 분석 실행
        for idx, method_meta in enumerate(all_methods):
            method_fqn = method_meta.get("method_fqn", "")
            
            if not method_fqn:
                self.logger.warning(f"🌧️ method_fqn is empty. skip. method_fqn: [{method_fqn}]")
                continue
            
            # 유효하지 않은 callee면 무시
            if method_fqn not in valid_method_fqns:
                self.logger.info(f"📢 invalid method_fqn: [{method_fqn}]")
                continue
            
            # method_fqn이 caller에 속하지 않는 경우에만 getter/setter 메서드 체크
            if method_fqn not in caller_set:
                # getter/setter 메서드는 제외
                if is_getter_setter(method_fqn, method_meta):
                    self.logger.info(f"📢 getter/setter 제외: [{method_fqn}]")
                    continue
            
            target_methods.append(method_meta)
            
        # LLM 실행
        results = asyncio.run(self._analyze_all(llm=llm_model, schema=InsightLLMOutput, methods=target_methods, max_concurrent=settings.MAX_CONCURRENT))
        new_method_meta_list = results
            
        code_analysis_result = {
            "input_type": IndexInputType.LLM_CODE,
            "llm_model": llm_model.deployment_name,         
            "llm_version": llm_model.openai_api_version,    
            "llm_temperature": llm_model.temperature,
            "code_analysis_info": new_method_meta_list
        }
        
        result = {
            AgentResultGroupKey.CURRENT_SOURCE_DATA: code_analysis_result,
            AgentResultGroupKey.CODE_ANALYSIS_RESULT: code_analysis_result
        }
     
        return self.wrap_multiple_sources(result)
        
    def _load_methods_from_rag(self, project_id: str) -> List[Dict]:
        """
        project_id를 기준으로 RAG에 저장된 source_type='METHOD' 문서를 모두 불러와
        MethodMeta 리스트로 변환합니다.

        Args:
            project_id (str): 프로젝트 또는 쿼리 ID

        Returns:
            List[Dict]: MethodMeta 리스트 (method_fqn, method_text 등 포함)
        """
        all_methods: List[Dict] = []
        all_method_fqns = {}
        
        documents: List[Document] = load_documents_by_source_type(project_id=project_id, source_type=RagSourceType.CODE)
        
        for doc in documents:
            method_map = doc.metadata.get("methods", {})
            
            for method_fqn, method_info in method_map.items():
                if "method_fqn" not in method_info:
                    method_info["method_fqn"] = method_fqn  # 반드시 보강
                        
                if method_fqn not in all_method_fqns:
                    all_method_fqns[method_fqn] = method_info
        
        all_methods = list(all_method_fqns.values())
        
        self.logger.info(f"[✅ RAG] project_id={project_id}, 총 {len(all_methods)}개 메서드 로딩 완료")
        return all_methods
    
    async def _analyze(self, llm, schema, method_meta, sem, max_concurrent, idx, total):
        async with sem:  # 동시 실행 제한
            current = sem._value                    # 남은 슬롯 개수
            active = max_concurrent - current       # 현재 실행 중 개수
            self.logger.info(f"🚀 method_meta: [{method_meta}]")
            self.logger.info(f"🚀 [{idx+1}/{total}] 실행 시작: {method_meta["method_fqn"]} (동시 실행: {active})")

            messages = self.get_prompt(method_meta=method_meta)
            
            try:
                # LLM 호출
                response = await self._call_llm_with_timeout(llm, schema, messages)
                
                method_meta["analyzed_at"] = datetime.now().isoformat()
                method_meta["summary"] = response.summary.strip().replace("\n", "")
                method_meta["description"] = response.description.strip().replace("\n", "")
            except asyncio.TimeoutError:
                self.logger.warning(f"❌ [TIMEOUT] {method_meta['method_fqn']} 분석 시간 초과로 스킵됨")
            except LengthFinishReasonError as err:
                self.logger.warning(f"❌ [SKIP] LengthFinishReasonError LengthLimit 초과. 응답 길이 제한으로 요약 생성 실패. error: {err}")
            except Exception as e:
                self.logger.warning(f"❌ [FAIL] 예기치 못한 오류 발생: {e}")
            
            self.logger.info(f"✅ [{idx+1}/{total}] 실행 완료: {method_meta['method_fqn']} (남은 실행: {max_concurrent - sem._value})")
            time.sleep(0.2)
        
            return method_meta
    
    async def _analyze_all(self, methods, llm, schema, max_concurrent=settings.MAX_CONCURRENT):
        sem = asyncio.Semaphore(max_concurrent)
        tasks = [self._analyze(llm=llm, schema=schema, method_meta=m, sem=sem, max_concurrent=max_concurrent, idx=idx, total=len(methods)) for idx, m in enumerate(methods)]
        return await asyncio.gather(*tasks)
    
def is_getter_setter(method_fqn: str, meta: dict) -> bool:
    name = method_fqn.split('(')[0].split('.')[-1]  # 메서드명
    params = meta.get("parameters") or []
    ret = (meta.get("return_type") or "").lower()
    
    # Getter: getX* (파라미터 0, 반환 void 아님)
    if name.startswith("get") and len(params) == 0 and ret not in ("void", "java.lang.void", ""):
        return True

    # Boolean Getter: isX* (파라미터 0, 반환 boolean)
    if name.startswith("is") and len(params) == 0 and ret in ("boolean", "java.lang.boolean"):
        return True

    # Setter: setX* (파라미터 1, 반환 void)
    if name.startswith("set") and len(params) == 1 and ret in ("void", "java.lang.void", ""):
        return True

    return False


