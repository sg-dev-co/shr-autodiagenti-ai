# server/workflow/agents/base/utility_agent.py

from abc import abstractmethod
from server.workflow.agents.base.base_agent import BaseAgent, AgentState

class BaseUtilityAgent(BaseAgent):
    """
    LLM을 사용하지 않는 유틸리티 Agent의 공통 추상 클래스.
    run()은 BaseAgent에서 처리되며, _run_internal()만 구현.
    """

    @abstractmethod
    def _run_internal(self, state: AgentState) -> AgentState:
        """
        유틸리티 로직을 하위 클래스에서 정의.
        예: 파일 저장, RAG 저장 등
        """
        pass
