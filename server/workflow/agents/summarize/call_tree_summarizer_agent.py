# server/workflow/agents/summarize/call_tree_summarizer_agent.py

"""
콜트리 요약 에이전트
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
from server.utils.config import settings, get_llm_with_custom
from server.utils.constants import AgentType, AgentResultGroupKey, DirInfo, RagSourceType, IndexInputType, LLMModel
from server.utils.document_retrieval_utils import load_call_tree_doc, load_documents_by_source_type
from server.utils.file_utils import load_json
from server.workflow.agents.base.base_llm_agent import BaseLLMAgent, LLMAgentState

class InsightLLMOutput(BaseModel):
    success: bool = Field(description="정상 분석여부")
    entry_point: str = Field(description="엔트리포인트(시작점)")
    summary_title: str = Field(description="전체 호출 흐름 요약 제목")
    insight: str = Field(description="전체 호출 흐름 요약")
    reasoning: str = Field(description="호출 순서 및 흐름에 대한 절차적 설명")

class CallTreeSummarizerAgent(BaseLLMAgent):
    def __init__(self, session_id: str = None, project_id: str = None):
        system_prompt = (
            "You are an expert in analyzing and interpreting method call flows in Java (Spring-based) systems. "
            "Your task is to read the provided method call flow data (including the entry point and call tree structure) and generate two outputs:\n"
            "- An insight: a one-sentence summary that captures the overall purpose or meaning of the call flow.\n"
            "- A reasoning: a step-by-step explanation of how the flow progresses from the entry point.\n\n"
            "Guidelines:\n"
            "- Use only the provided call flow and related method summaries. Do not rely on assumptions or external knowledge.\n"
            "- Keep the insight concise and meaningful (1 sentence).\n"
            "- Keep the reasoning procedural and clear (2–3 sentences).\n"
            "- If the input is limited, still provide the most reasonable interpretation possible.\n"
            "- Additionally, generate a concise summary_title that best describes the entry point’s call flow in a single sentence."
            "- Output must be in Korean.\n"
            "- Do not include any quotation marks.\n"
            "- Ensure that the output follows the format exactly, including punctuation and curly braces '{}':\n"
            "{ 'success': '...', 'summary_title': '...', 'entry_point': '...', 'insight': '...', 'reasoning': '...' }"
        )

        super().__init__(system_prompt=system_prompt, role=AgentType.CALL_TREE_SUMMARIZER, session_id=session_id, project_id=project_id)

    def _create_prompt(self, state: LLMAgentState) -> Optional[str]:
        pass
    
    def get_prompt(self, entry_point: str, call_tree: Dict, method_summary_map: Dict) -> List:
        # 프롬프트 템플릿을 위해 개별정의함
        messages = [SystemMessage(content=self.system_prompt)]
        
        human_prompt_template = PromptTemplate(
                                    input_variables=["entry_point", "call_tree", "method_summary_map"],
                                    template = """
                                        자바(Spring 기반) 시스템의 메서드 호출 흐름 데이터가 주어졌습니다.

                                        **주의**: call tree 데이터가 비어 있으면 분석 결과를 생성할 수 없습니다.  
                                        - call tree가 비어 있을 경우, 아래와 같이 출력하세요:  
                                        {{ "success": False, "entry_point": "", "insight": "분석 가능한 호출 흐름이 제공되지 않았습니다.", "reasoning": "" }}

                                        당신의 역할은 자바 메서드 호출 흐름 분석 전문가로서, 다음 작업을 수행해야 합니다:
                                        - **entry_point를 기준으로 호출 흐름을 따라가며 전체 호출 과정에 대한 요약(insight)과 절차 설명(reasoning)을 생성합니다.**
                                        - 호출 흐름(call_tree)과 각 메서드에 대한 요약(method_summary_map)을 참고하여 분석하세요.
                                        - 요약(insight)은 해당 entry_point의 역할과 전반적인 호출 흐름에 대해 분석하여 작성합니다.
                                        - 설명(reasoning)은 호출 트리를 기반으로 한 상세 분석 이유를 분석하여 작성합니다.
                                        - 정상 분석 여부(success)는 call tree 데이터가 비어 있으면 False로 작성하고 , 이 외는 True로 작성합니다.
                                        - 메서드에 대한 요약(method_summary_map)은 제공되지 않을 수 있습니다. 제공되지 않는 경우, call_tree만 참고하여 가능한 최선의 분석을 수행하세요.
                                        - **외부 지식이나 추측은 하지 말고, 제공된 정보에 근거하여 분석합니다.**
                                        - insight는 한 문장으로, reasoning은 2~3문장 이내로 작성합니다.
                                        - 마지막으로, entry_point에 해당하는 호출 흐름을 대표할 수 있는 한 줄 제목(summary_title) 을 작성하세요. 간결하고 직관적으로 표현하세요.

                                        다음 형식으로 정확히 출력하세요:
                                        {{
                                            "success": True,          // 예: True
                                            "entry_point": "...",     // 예: "com.example.AuthController.login"
                                            "summary_title": "...",   // 예: "로그인 요청"
                                            "insight": "...",         // 예: "로그인 요청은 사용자 검증과 토큰 발급의 두 단계를 거칩니다."
                                            "reasoning": "..."        // 예: "login 메서드는 getUser 호출로 사용자 정보를 조회하고, 이후 generateToken을 호출하여 토큰을 생성합니다."
                                        }}

                                        입력값:
                                        - entry_point: 
                                        [{entry_point}]
                                        
                                        - call_tree: 
                                        [{call_tree}]
                                        
                                        - method_summary_map: (선택적)
                                        [{method_summary_map}]
                                        
                                        ※ method_summary_map 값은 선택적으로 제공됩니다. 제공되지 않는 경우, call_tree만 참고하여 가능한 최선의 분석을 수행하세요.
                                    """
                                )
    
        messages.append(HumanMessage(content=human_prompt_template.format(entry_point=entry_point, call_tree=call_tree, method_summary_map=method_summary_map)))
        return messages


    def _run_internal(self, state: LLMAgentState) -> LLMAgentState:
        agent_state = state["autodiagenti_state"]
        project_id = agent_state.get("project_id", "")
        project_name = agent_state.get("project_name", "")
        
        # 모델 정보
        model_info: LLMModel = agent_state.get("llm_model_info")        
        
        # 모델 선언
        llm_model = get_llm_with_custom(llm_model=model_info.model_name, llm_version=model_info.version)
        
        # 1.EntryPoint 목록 추출
        output_dir = os.path.join(DirInfo.PARSER_OUTPUT_DIR, project_id, project_name)
        entry_point_path = os.path.join(output_dir, settings.ENTRY_POINT_FILE_NAME)
        entry_point_list = load_json(entry_point_path)
        
        # LLM 실행
        results = asyncio.run(self._analyze_all(llm=llm_model, schema=InsightLLMOutput, project_id=project_id, entry_point_list=entry_point_list, max_concurrent=settings.MAX_CONCURRENT))
        new_call_tree_docs = results
            
        call_tree_summary_result = {
            "input_type": IndexInputType.CALLTREE_SUMMARY,
            "llm_model": llm_model.deployment_name,         
            "llm_version": llm_model.openai_api_version,    
            "llm_temperature": llm_model.temperature,
            "call_tree_summary_info": new_call_tree_docs
        }
            
        result = {
            AgentResultGroupKey.CALL_TREE_SUMMARY: call_tree_summary_result,
            AgentResultGroupKey.CURRENT_SOURCE_DATA: call_tree_summary_result
        }
        
        return self.wrap_multiple_sources(result)
    
    async def _analyze(self, llm, schema, entry_point, call_tree_doc, method_summary_map, sem, max_concurrent, idx, total):
        async with sem:  # 동시 실행 제한
            current = sem._value                    # 남은 슬롯 개수
            active = max_concurrent - current       # 현재 실행 중 개수
            self.logger.info(f"🚀 entry_point: [{entry_point}]")
            self.logger.info(f"🚀 [{idx+1}/{total}] 실행 시작: {entry_point} (동시 실행: {active})")
            messages = self.get_prompt(entry_point=entry_point, call_tree=call_tree_doc.metadata.get("call_tree", {}), method_summary_map=method_summary_map)
            
            try:
                # LLM 호출
                response = await self._call_llm_with_timeout(llm, schema, messages)
                
                call_tree_doc.metadata["success"] = response.success
                call_tree_doc.metadata["summary_title"] = response.summary_title
                if response.success:
                    call_tree_doc.metadata["insight"] = response.insight.strip().replace("\n", "")
                else:
                    call_tree_doc.metadata["insight"] = ""
                call_tree_doc.metadata["reasoning"] = response.reasoning.strip().replace("\n", "")
                call_tree_doc.metadata["input_type"] = IndexInputType.CALLTREE_SUMMARY
                call_tree_doc.metadata['source_type'] = RagSourceType.CALLTREE_SUMMARY
                call_tree_doc.metadata['document_id'] = None
                call_tree_doc.metadata['analyzed_at'] = datetime.now().isoformat()
            except asyncio.TimeoutError:
                self.logger.warning(f"❌ [TIMEOUT] {entry_point} 분석 시간 초과로 스킵됨")
            except LengthFinishReasonError as err:
                self.logger.warning(f"❌ [SKIP] LengthFinishReasonError LengthLimit 초과. 응답 길이 제한으로 요약 생성 실패. error: {err}")
            except Exception as e:
                self.logger.warning(f"❌ [FAIL] 예기치 못한 오류 발생: {e}")
            
            self.logger.info(f"✅ [{idx+1}/{total}] 실행 완료: {entry_point} (남은 실행: {max_concurrent - sem._value})")
            time.sleep(0.2)
        
            return call_tree_doc
        
    async def _analyze_all(self, project_id, entry_point_list, llm, schema, max_concurrent=settings.MAX_CONCURRENT):
        sem = asyncio.Semaphore(max_concurrent)
        tasks = []
        
        # EntryPoint 별로 요약 실행
        for idx, entry_point in enumerate(entry_point_list):
            # 2. CALLTREE 문서 조회
            call_tree_doc: Optional[Document] = load_call_tree_doc(project_id=project_id, entry_point=entry_point)
            
            if call_tree_doc is None:
                return None  # 해당 entry_point에 대한 call tree 문서가 없음

            # 3. 선택적으로 CODE_ANALYSIS 문서 조회
            code_analysis_docs = load_documents_by_source_type(project_id=project_id, source_type=RagSourceType.CODE_ANALYSIS)
            method_summary_map = {}
            
            for doc in code_analysis_docs:
                if doc.metadata.get("entry_point") == entry_point:
                    method_summary_map.update(doc.page_content)  # 이미 Dict 형태라고 가정 (아닐 경우 json.loads)
            
            tasks.append(self._analyze(llm=llm, schema=schema, entry_point=entry_point, call_tree_doc=call_tree_doc, method_summary_map=method_summary_map, sem=sem, max_concurrent=max_concurrent, idx=idx, total=len(entry_point_list)))
            
        return await asyncio.gather(*tasks)
