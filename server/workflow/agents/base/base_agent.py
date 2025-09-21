# server/workflow/agents/base/base_agent.py

import asyncio
import traceback
from abc import ABC, abstractmethod
from typing import Dict, List, Any, TypedDict
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from server.workflow.state import AutoDiagentiAnalysisState
from server.utils.constants import AgentType, AgentRunType
from server.utils.config import settings
from server.workflow.state import set_project_status
from server.utils.logger import get_logger

class AgentState(TypedDict):
    autodiagenti_state: Dict[str, Any]
    agent_state: Dict[str, Any]
    context: str
    messages: List[Any]  # LLM 기반 또는 기타 입력 메시지
    response: str

class BaseAgent(ABC):
    """
    모든 Agent의 공통 추상 클래스.
    BaseAgent(LLM 기반), UtilityAgent(비 LLM) 모두 이 인터페이스를 상속해야 함.
    외부(Graph)에서는 AutoDiagentiAnalysisState 동작하고, 내부에서는 AgentState로 처리.
    """
    def __init__(self, role: AgentType = None, session_id: str = None, project_id: str = None):
        self.role = role
        self.session_id = session_id
        self.project_id = project_id
        self.logger = get_logger(self.__class__.__name__)  # 클래스 이름 기준으로 로거 생성
    
    def run(self, state: AutoDiagentiAnalysisState) -> AutoDiagentiAnalysisState:
        result = {}
        
        try:
            # 상태저장 (RAG 제외)
            if self.role != AgentType.RAG_INDEXER:
                set_project_status(project_id=self.project_id, role=self.role, runStatus=AgentRunType.START)
            
            self.logger.info(f"***** 수행 Agent: {self.role} *****")
            internal_state = self._extract_internal_state(state)
            result = self._run_internal(internal_state)
        except Exception as err:
            self.logger.error(f"❌ 에이전트 실행 중 예외 발생: {str(err)} - state: [{state}], role: [{self.role}], session_id: [{self.session_id}], project_id: [{self.project_id}]")
            self.logger.error(f"❌ Stacktrace:\n {traceback.format_exc()}")
            state["agent_error"] = True
            state["agent_error_message"] = str(err)    
        return self._update_state(state, result)

    @abstractmethod
    def _run_internal(self, state: AgentState) -> AgentState:
        """
        Agent별 핵심 실행 로직을 구현하는 부분
        """
        pass

    def _extract_internal_state(self, state: AutoDiagentiAnalysisState) -> AgentState:
        """
        Graph용 상태(AutoDiagentiAnalysisState) → Agent 내부 상태(AgentState)로 변환
        """
        self.logger.info(f'📢 _extract_internal_state: [{state}]')
        
        return {
            "autodiagenti_state": {**state}
        }

    def _update_state(self, original: AutoDiagentiAnalysisState, result: AgentState) -> AutoDiagentiAnalysisState:
        """
        내부 처리 결과를 AutoDiagentiAnalysisState에 병합
        """
        
        # 상태저장 (RAG 제외)
        if self.role != AgentType.RAG_INDEXER:
            set_project_status(project_id=self.project_id, role=self.role, runStatus=AgentRunType.END)
        
        return {
            **original,
            "agent_result": {
                **original.get("agent_result", {}),                         # 기존 결과 유지
                **result.get("agent_state", {}).get("agent_result", {})     # 새로운 결과 추가
            },
            "agent_role": self.role,    # 실행한 Agent의 role을 함께 기록
            "prev_node": self.role      # 현재 실행 중인 노드/role 이름 (original 항목 값 업데이트)
        }
    
    @retry(
        stop=stop_after_attempt(3),                     # 최대 3회 재시도
        wait=wait_fixed(2),                             # 실패 시 2초 대기 후 재시도
        retry=retry_if_exception_type(Exception)        # 모든 예외에 대해 재시도
    )
    async def _call_llm_with_timeout(self, llm, schema, messages):
        return await asyncio.wait_for(llm.with_structured_output(schema).ainvoke(messages), timeout=settings.LLM_TIMEOUT)
    
    def wrap_agent_result(self, key: str, value: Dict[str, Any]) -> AgentState:
        return {
            "agent_state": {
                "agent_result": {
                    key: value
                }
            }
        }
    
    def wrap_multiple_sources(self, values: Dict[str, Dict[str, Any]]) -> AgentState:
        self.logger.info(f'📢📢 wrap_multiple_sources values: {values}')
        return {
            "agent_state": {
                "agent_result": values
            }
        }
    