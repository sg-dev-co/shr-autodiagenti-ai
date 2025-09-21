# server/workflow/agents/base/base_llm_agent.py

import uuid
from abc import abstractmethod
from typing import List, Optional
from langchain.schema import HumanMessage, SystemMessage
from langchain_core.messages import BaseMessage
from server.workflow.agents.base.base_agent import BaseAgent, AgentState

# LLM 전용 상태 (messages 타입을 BaseMessage로 고정)
class LLMAgentState(AgentState):
    messages: List[BaseMessage]

class BaseLLMAgent(BaseAgent):
    def __init__(self, system_prompt: str, role: str = None, session_id: str = None, project_id: str = None):
        super().__init__(role=role, session_id=session_id, project_id=project_id)
        self.system_prompt = system_prompt
        
        if not self.session_id:
            self.session_id = str(uuid.uuid4())

    def _prepare_messages(self, state: LLMAgentState) -> LLMAgentState:
        context = state.get("context", "")

        # 시스템 프롬프트 추가
        messages = [SystemMessage(content=self.system_prompt)]

        # 프롬프트 생성 (검색된 컨텍스트 포함)
        prompt = self._create_prompt({**state, "context": context})
        messages.append(HumanMessage(content=prompt))

        return {**state, "messages": messages}  # type: ignore
    
    @abstractmethod
    def _create_prompt(self, state: LLMAgentState) -> Optional[str]:
        """
        하위 클래스에서 프롬프트 생성 방식 정의
        """
        pass
    
    @abstractmethod
    def _run_internal(self, state: LLMAgentState) -> LLMAgentState:
        """
        Agent별 실행 메서드.
        필요 시 self._run_simple_llm(state) 호출 가능.
        """
        pass
    