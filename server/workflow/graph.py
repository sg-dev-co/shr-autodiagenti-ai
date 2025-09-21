# server/workflow/graph.py

"""
LangGraph 워크플로우 그래프 생성 모듈
"""

import os
import uuid
from typing import Dict
from datetime import datetime
import traceback
from langgraph.graph import StateGraph, END
from langgraph.types import Command
from server.workflow.state import AutoDiagentiAnalysisState, get_project_status, set_project_done_status, set_project_fail_status
from server.utils.constants import AgentType, IndexInputType, AgentResultGroupKey, DirInfo, LLMModel
from server.utils.vectorstore_utils import delete_faiss_index_by_project
from server.utils.logger import get_logger
from server.workflow.agents.retrieval.rag_indexing_agent import RAGIndexingAgent
from server.workflow.agents.analyze.parser_agent import ParserAgent
from server.workflow.agents.analyze.recursive_call_tree_agent import RecursiveCallTreeAgent
from server.workflow.agents.analyze.code_analysis_agent import CodeAnalysisAgent
from server.workflow.agents.summarize.call_tree_summarizer_agent import CallTreeSummarizerAgent
from server.workflow.agents.generate.sequence_diagram_generator_agent import SequenceDiagramGeneratorAgent

# 로거 선언
logger = get_logger(__name__)

def create_autodiagenti_graph(session_id: str = "", project_id: str = ""):
    # 그래프 생성
    workflow = StateGraph(AutoDiagentiAnalysisState)

    # 에이전트 인스턴스 생성
    parser_agent = ParserAgent(session_id=session_id, project_id=project_id)
    recursive_call_tree_agent = RecursiveCallTreeAgent(session_id=session_id, project_id=project_id)
    code_analysis_agent = CodeAnalysisAgent(session_id=session_id, project_id=project_id)
    call_tree_summarizer_agent = CallTreeSummarizerAgent(session_id=session_id, project_id=project_id)
    sequence_diagram_agent = SequenceDiagramGeneratorAgent(session_id=session_id, project_id=project_id)
    rag_indexing_agent = RAGIndexingAgent(session_id=session_id, project_id=project_id)
    
    # 노드 추가
    workflow.add_node(AgentType.SUSPERVISOR, supervisor_node)
    workflow.add_node(AgentType.PARSER, parser_agent.run)
    workflow.add_node(AgentType.RECURSIVE_CALL_TREE, recursive_call_tree_agent.run)
    workflow.add_node(AgentType.CODE_ANALYSIS, code_analysis_agent.run)    
    workflow.add_node(AgentType.CALL_TREE_SUMMARIZER, call_tree_summarizer_agent.run)
    workflow.add_node(AgentType.SEQUENCE_DIAGRAM, sequence_diagram_agent.run)
    workflow.add_node(AgentType.RAG_INDEXER, rag_indexing_agent.run)

    # 모든 분기 노드 종료 처리
    workflow.add_edge(AgentType.PARSER, AgentType.SUSPERVISOR)
    workflow.add_edge(AgentType.RECURSIVE_CALL_TREE, AgentType.SUSPERVISOR)
    workflow.add_edge(AgentType.CODE_ANALYSIS, AgentType.SUSPERVISOR)
    workflow.add_edge(AgentType.CALL_TREE_SUMMARIZER, AgentType.SUSPERVISOR)
    workflow.add_edge(AgentType.SEQUENCE_DIAGRAM, AgentType.SUSPERVISOR)
    workflow.add_edge(AgentType.RAG_INDEXER, AgentType.SUSPERVISOR)
    workflow.add_edge(AgentType.SUSPERVISOR, END)
    
    # Flow 구성
    workflow.set_entry_point(AgentType.PARSER)

    # 그래프 컴파일
    return workflow.compile()

def supervisor_node(state: AutoDiagentiAnalysisState) -> Command:
    prev = state.get("prev_node")
    project_id = state.get("project_id")
    file_info = state.get("file_info") or {}
    file_name = file_info.get("file_name", None)
    source_data = (state.get("agent_result") or {}).get("current_source_data", {})
    input_type = source_data.get("input_type", None) if source_data else None
    logger.info(f"[SUPERVISOR] prev_node: {prev}, file_name: {file_name}, input_type: {input_type}, status: {get_project_status(project_id=project_id)}")
    
    update_state = {"prev_node": AgentType.SUSPERVISOR}
    
    agent_error = state.get("agent_error", False)
    agent_error_message = state.get("agent_error_message", "")
    
    if agent_error:
        logger.error(f"**[비정상종료] 에이전트 실행 중 예외 발생: {agent_error_message} - prev: [{prev}], file_name: [{file_name}], input_type: [{input_type}]")
        set_project_fail_status(project_id=project_id)
        return Command (goto=END)
    
    try:
        if prev == AgentType.PARSER:
            success = source_data.get("success", False)
            logger.info(f"[SUPERVISOR] PARSER success: {success}")
            
            if success:
                logger.info("**[이동] PARSER -> SUPERVISOR -> RAG_INDEXER **")
                return Command(goto=AgentType.RAG_INDEXER, update=update_state)
            else:
                logger.info("**[작업종료][PARSER 실패] PARSER -> END **")
                set_project_fail_status(project_id=project_id)
                return Command(goto=END)
        elif prev == AgentType.RECURSIVE_CALL_TREE:
            logger.info("**[이동] RECURSIVE_CALL_TREE -> SUPERVISOR -> RAG_INDEXER **")
            return Command(goto=AgentType.RAG_INDEXER, update=update_state)
        elif prev == AgentType.CODE_ANALYSIS:
            logger.info("**[이동] CODE_ANALYSIS -> SUPERVISOR -> RAG_INDEXER **")
            return Command(goto=AgentType.RAG_INDEXER, update=update_state)
        elif prev == AgentType.CALL_TREE_SUMMARIZER:
            logger.info("**[이동] CALL_TREE_SUMMARIZER -> SUPERVISOR -> RAG_INDEXER **")
            return Command(goto=AgentType.RAG_INDEXER, update=update_state)
        elif prev == AgentType.SEQUENCE_DIAGRAM:
            logger.info("**[이동] SEQUENCE_DIAGRAM -> SUPERVISOR -> RAG_INDEXER **")
            return Command(goto=AgentType.RAG_INDEXER, update=update_state)
        elif prev == AgentType.RAG_INDEXER:
            if input_type == IndexInputType.PARSER:
                logger.info("**[이동] RAG_INDEXER.PARSER -> SUPERVISOR -> RECURSIVE_CALL_TREE **")
                set_project_done_status(project_id=project_id)
                return Command(goto=AgentType.RECURSIVE_CALL_TREE, update=update_state)
            elif input_type == IndexInputType.CALLTREE:
                logger.info("**[이동] RAG_INDEXER.CALLTREE -> SUPERVISOR -> CODE_ANALYSIS **")
                return Command(goto=AgentType.CODE_ANALYSIS, update=update_state)
            elif input_type == IndexInputType.LLM_CODE:
                logger.info("**[이동] RAG_INDEXER.LLM_CODE -> SUPERVISOR -> CALL_TREE_SUMMARIZER **")
                return Command(goto=AgentType.CALL_TREE_SUMMARIZER, update=update_state)
            elif input_type == IndexInputType.CALLTREE_SUMMARY:
                logger.info("**[이동] RAG_INDEXER.CALLTREE_SUMMARY -> SUPERVISOR -> SEQUENCE_DIAGRAM **")
                return Command(goto=AgentType.SEQUENCE_DIAGRAM, update=update_state)
            elif input_type == IndexInputType.SEQUENCE_DIAGRAM:
                logger.info("**[작업종료] RAG_INDEXER.SEQUENCE_DIAGRAM -> SUPERVISOR -> END **")
                set_project_done_status(project_id=project_id)
                return Command(goto=END)
            else:
                logger.warning(f"**[비정상종료] RAG_INDEXER 처리 이후 분기 불가 - input_type 누락. input_type: {input_type}")
                set_project_fail_status(project_id=project_id)
                return Command(goto=END)
    except Exception as err:
        logger.error(f"**[비정상종료] 에이전트 실행 중 예외 발생: {str(err)} - prev: [{prev}], file_name: [{file_name}], input_type: [{input_type}]")
        logger.error(f"**Stacktrace:\n {traceback.format_exc()}")
        set_project_fail_status(project_id=project_id, error_message=f"cause: {str(err)}")
        return Command (goto=END)
        
    # fallback - 안전하게 종료
    logger.warning(f"**[비정상종료] 분기 불가 - prev: [{prev}], file_name: [{file_name}], input_type: [{input_type}]")
    set_project_fail_status(project_id=project_id)
    return Command(goto=END)

def run_autodiagenti_graph(session_id: str, project_id: str, project_name: str, analyzed_date: str, file_info: Dict, filter_options: Dict, llm_model_info: LLMModel):
    # 세션 ID 생성
    session_id = str(uuid.uuid4())
    result = {}

    try:
        # 그래프 생성
        graph = create_autodiagenti_graph(session_id=session_id, project_id=project_id)

        # 초기 상태 설정
        initial_state: AutoDiagentiAnalysisState = AutoDiagentiAnalysisState(
            project_id=project_id,
            project_name=project_name,
            project_path=os.path.join(DirInfo.UNPACK_DIR, project_id, project_name),
            analyzed_at=datetime.now().isoformat(),
            analyzed_date=analyzed_date,
            file_info=file_info,
            filter_options = filter_options,
            llm_model_info=llm_model_info
        )
        
        # 분석 작업전 동일 프로젝트 ID 벡터 스토어 삭제
        delete_faiss_index_by_project(project_id=project_id)
        
        graph_result = graph.invoke(input=initial_state, config={"recursion_limit": 35})
        agent_error = graph_result.get("agent_error", False)
        agent_error_message = graph_result.get("agent_error_message", "")
        agent_result = graph_result.get("agent_result", {})
        logger.info("✅ graph_result:", graph_result)
        
        if agent_error:
            raise Exception(agent_error_message)
        
        # 결과값 처리
        target_keys = [
            AgentResultGroupKey.SEQUENCE_DIAGRAM_RESULT,
            AgentResultGroupKey.CALL_TREE_SUMMARY
        ]

        result = {key: agent_result.get(key, {}) for key in target_keys }
        logger.info("✅ 분석 완료:", result)
    except Exception as err:
        logger.error(f"❌ 분석 실패: {str(err)}")
        logger.error(f"❌ 분석 실패 Stacktrace:\n {traceback.format_exc()}")
        set_project_fail_status(project_id=project_id, error_message=f"cause: {str(err)}")
    return result

