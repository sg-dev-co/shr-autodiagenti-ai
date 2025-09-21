# server/workflow/agents/generate/sequence_diagram_generator_agent.py

"""
시퀀스 다이어그램 에이전트
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
from server.utils.document_retrieval_utils import load_call_tree_summary_doc, load_documents_by_source_type
from server.utils.file_utils import load_json
from server.workflow.agents.base.base_llm_agent import BaseLLMAgent, LLMAgentState

class DiagramLLMOutput(BaseModel):
    entry_point: str = Field(description="엔트리포인트(시작점)")
    mermaid_code: str = Field(description="valid Mermaid sequence diagram code")

class SequenceDiagramGeneratorAgent(BaseLLMAgent):
    def __init__(self, session_id: str = None, project_id: str = None):
        system_prompt = (
            "You are an expert in generating **Mermaid sequence diagrams** based on Java method call trees and method summaries. "
            "Your task is to create a well-structured `Mermaid` sequence diagram representing the full call flow starting from a given `entry_point` method. "
            "You must **recursively traverse the call_tree** to represent all levels of the structure.\n"
            "Use **only the provided data** to infer call structure and labeling. Do not assume behavior not present in the input.\n\n"

            "Before generating the diagram, first **read and understand the overall call flow** based on:\n"
            "- `call_tree_summary_insight`: a high-level summary of the overall call flow\n"
            "- `call_tree_summary_reasoning`: a step-by-step description of how the methods are called\n\n"

            "Then follow these structured steps:\n"
            "1. Initialize all unique `class_name` values as participants (no duplication).\n"
            "2. Recursively generate call arrows (`->>`) from caller to callee using `display_name` or `method_fqn`.\n"
            "3. After each call, add a note with the method’s `summary` using `Note right of [callee]`.\n"
            "   - *** Only add the note if the `summary` is non-blank (i.e., not `None` or an empty string).***\n"
            "4. Always add a return arrow (`-->>`) unless it’s the entry_point or a message-style method.\n"
            "   - *** Never draw return arrows from the entry_point to any other participant, even if it has a return_type. The entry_point is the origin and should not return to others.*** \n"
            "   - *** To ensure Mermaid renders correctly ***, always end return arrows with `: ` (e.g., `A-->>B: `).\n\n"

            "Output format:\n"
            "{ \n"
            "  'entry_point': '...',       // method FQN\n"
            "  'mermaid_code': '...'       // valid Mermaid sequence diagram code\n"
            "}\n\n"

            "Inputs:\n"
            "- `entry_point`: the root method's FQN and return_type\n"
            "- `call_tree`: nested call structure, each node has `method_fqn` and child `calls`\n"
            "- `method_definitions`: metadata per method_fqn: `class_name`, `summary`, `display_name`, `return_type`, etc.\n"
            "- `depth`: the maximum depth of the call tree (for reference)\n"
            "- `call_tree_summary_insight`: overall insight on the call flow\n"
            "- `call_tree_summary_reasoning`: step-by-step explanation of the call sequence\n\n"

            "Diagram generation rules:\n"
            "- Use `->>` for method calls and `-->>` for return arrows.\n"
            "- Always include return arrows for non-entry-point methods, and always terminate them with `:`.\n"
            "- Omit the return arrow for entry_point only if its return_type is `void`; optionally, use a `note`.\n"
            "- Use `display_name` or `method_fqn` as the label on the arrow (⚠️ Never use `summary`).\n"
            "- Place the `summary` as a note using `Note right of [callee]` right after the call.\n"
            "  (Only if the summary is non-blank; do not include notes for missing or empty summaries.)\n"
            "- For message-style methods (e.g., `kafkaTemplate.send`), omit return arrow and just add a note.\n"
            "- Do not duplicate `participant` declarations (based on class_name).\n"
            "- Output must be in **Korean**.\n"
        )

        super().__init__(system_prompt=system_prompt, role=AgentType.SEQUENCE_DIAGRAM, session_id=session_id, project_id=project_id)

    def _create_prompt(self, state: LLMAgentState) -> Optional[str]:
        pass
    
    def get_prompt(self, entry_point: str, depth: int, call_tree: Dict, method_definitions: Dict, call_tree_summary_insight: str, call_tree_summary_reasoning: str) -> List:
        # 프롬프트 템플릿을 위해 개별정의함
        messages = [SystemMessage(content=self.system_prompt)]
        
        human_prompt_template = PromptTemplate(
                                    input_variables=["entry_point", "depth", "call_tree", "method_definitions"],
                                    template = """
                                        자바(Spring 기반) 시스템의 호출 흐름(call tree) 및 메서드 요약 정보가 주어졌습니다.

                                        당신의 역할은 Java 시스템의 호출 흐름 전문가로서, 아래 데이터를 기반으로 **Mermaid 시퀀스 다이어그램** 코드를 생성하는 것입니다.  
                                        시퀀스 다이어그램은 반드시 **entry_point 메서드부터 시작**하여, 전체 호출 흐름을 **재귀적으로 분석**하고 **시각적으로 표현**해야 합니다.

                                        ## 사고 순서 (Chain-of-Thought 방식으로 단계별로 생각하세요):

                                        1. 먼저 `call_tree_summary_insight`와 `call_tree_summary_reasoning`을 읽고 전체 흐름의 목적과 구조를 파악하세요.
                                        2. 그 다음 `call_tree`를 따라가며 호출 관계를 전체적으로 재귀적으로 분석하세요.
                                        3. 각 호출 지점마다 `method_definitions`에서 해당 메서드의 `class_name`, `summary`, `display_name`, `return_type` 정보를 참고하세요.
                                        4. 호출선은 `display_name` 또는 `method_fqn`으로 표시하고, `summary`는 **note**로 제공합니다.
                                        5. `depth`는 참고용입니다. 무시해도 되지만 흐름을 확인하는 데 도움이 됩니다.

                                        ## 입력 설명:

                                        - `entry_point`: 호출 흐름의 시작점이 되는 메서드의 FQN(method_fqn) 및 `return_type` 정보입니다.
                                        - `depth`: 전체 호출 흐름의 최대 깊이입니다. (참고용 메타데이터입니다)
                                        - `call_tree`: 호출 흐름을 재귀적으로 표현한 구조이며, 각 노드는 `method_fqn`과 하위 `calls`를 포함합니다.
                                        - `method_definitions`: 각 메서드에 대한 메타정보로, `class_name`, `summary`, `display_name`, `return_type` 등을 포함합니다.
                                        - `call_tree_summary_insight`: 전체 흐름의 핵심 요약입니다. 시스템의 목적과 주요 기능 흐름을 먼저 이해하는 데 활용하세요.
                                        - `call_tree_summary_reasoning`: 호출 흐름이 어떤 순서로 작동하는지 절차적으로 설명한 텍스트입니다.

                                        ## 꼭 지켜야 할 지침:

                                        - `call_tree`는 재귀 구조입니다. 모든 하위 호출까지 완전히 탐색하여 시퀀스를 생성하세요.
                                        - 호출은 항상 caller → callee 방향으로 `->>` 화살표를 사용하세요.
                                        - **화살표 라벨**은 `summary`를 절대로 사용하지 마세요. `display_name` 또는 `method_fqn`만 사용하세요.
                                        - 호출 후에는 해당 메서드의 `summary`를 `Note right of [callee]` 형식으로 추가하세요.
                                            - 단, `summary`가 없거나 비어 있으면(`None`이거나 빈 문자열) `Note`를 추가하지 마세요.
                                        - 모든 하위 호출은 `-->>` 리턴 화살표로 반드시 종료하세요. ⚠️ 이때 리턴 화살표의 **라벨은 해당 메서드의 `return_type`으로 명시하세요. 단, return_type이 void이거나 라벨이 비어 있는 경우에는 Mermaid 문법상 **빈 라벨을 피하기 위해 ": " (콜론+스페이스)**를 항상 붙이세요.
                                        - 단, **entry_point 메서드**는 리턴 화살표를 생성하지 마세요. return_type이 무엇이든 상관없이 리턴을 표시하지 않습니다.
                                        - **메시지 전송용 메서드** (예: `kafkaTemplate.send`, `socket.emit`, `rabbitTemplate.convertAndSend`)는 리턴 없이 `note`로 메시지 발신을 표현하세요.
                                        - 모든 화살표 (->> 또는 -->>)의 양 끝에는 반드시 해당 메서드의 `class_name`만 사용하세요.
                                            - 예: UserController->>UserService: updateUserStatus(...)
                                            - 절대 `method_fqn`, `display_name`, `package.class_name` 등을 actor 위치에 사용하지 마세요.
                                            - 이는 Mermaid의 participant 선언과 일치해야 합니다.
                                        - 동일한 `class_name`은 participant로 중복 선언하지 마세요.
                                        - Mermaid 문법에 맞게 문법 오류 없이 시퀀스를 생성하세요.

                                        다음 형식으로 정확히 출력하세요:
                                        {{
                                            "entry_point": "...",     // 예: "com.example.UserService.getUserInfo"
                                            "mermaid_code": "..."     // Mermaid 유효 문법으로 구성된 시퀀스 다이어그램 코드
                                        }}

                                        **입력값**:
                                        entry_point:  
                                        [{entry_point}]

                                        depth:  
                                        [{depth}]

                                        call_tree:  
                                        [{call_tree}]

                                        method_definitions:  
                                        [{method_definitions}]

                                        call_tree_summary_insight:  
                                        [{call_tree_summary_insight}]

                                        call_tree_summary_reasoning:  
                                        [{call_tree_summary_reasoning}]
                                    """
                                )
    
        messages.append(HumanMessage(content=human_prompt_template.format(entry_point=entry_point, depth=depth, call_tree=call_tree, method_definitions=method_definitions, call_tree_summary_insight=call_tree_summary_insight, call_tree_summary_reasoning=call_tree_summary_reasoning)))
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
        
        sequence_diagram_infos = []
        
        # LLM 실행
        results = asyncio.run(self._analyze_all(llm=llm_model, schema=DiagramLLMOutput, project_id=project_id, entry_point_list=entry_point_list, max_concurrent=settings.MAX_CONCURRENT))
        sequence_diagram_infos = results
            
        sequence_diagram_result = {
            "input_type": IndexInputType.SEQUENCE_DIAGRAM,
            "llm_model": llm_model.deployment_name,         
            "llm_version": llm_model.openai_api_version,    
            "llm_temperature": llm_model.temperature,
            "sequence_diagram_info": sequence_diagram_infos
        }
            
        result = {
            AgentResultGroupKey.SEQUENCE_DIAGRAM_RESULT: sequence_diagram_result,
            AgentResultGroupKey.CURRENT_SOURCE_DATA: sequence_diagram_result
        }
        
        return self.wrap_multiple_sources(result)
    
    async def _analyze(self, llm, schema, entry_point, depth, call_tree, method_definitions, call_tree_summary_title, call_tree_summary_insight, call_tree_summary_reasoning, sem, max_concurrent, idx, total):
        async with sem:  # 동시 실행 제한
            current = sem._value                    # 남은 슬롯 개수
            active = max_concurrent - current       # 현재 실행 중 개수
            self.logger.info(f"🚀 entry_point: [{entry_point}]")
            self.logger.info(f"🚀 [{idx+1}/{total}] 실행 시작: {entry_point} (동시 실행: {active})")
            messages = self.get_prompt(entry_point=entry_point, depth=depth, call_tree=call_tree, method_definitions=method_definitions, call_tree_summary_insight=call_tree_summary_insight, call_tree_summary_reasoning=call_tree_summary_reasoning)
            sequence_diagram_info = {}
            
            try:
                # LLM 호출
                response = await self._call_llm_with_timeout(llm, schema, messages)
                
                sequence_diagram_info = {
                                            "entry_point": entry_point,
                                            "mermaid_code": response.mermaid_code,
                                            "summary_title": call_tree_summary_title,
                                            "insight": call_tree_summary_insight,
                                            "reasoning": call_tree_summary_reasoning,
                                            "method_definitions": method_definitions,
                                            "analyzed_at": datetime.now().isoformat()
                                        }
            except asyncio.TimeoutError:
                self.logger.warning(f"❌ [TIMEOUT] {entry_point} 분석 시간 초과로 스킵됨")
            except LengthFinishReasonError as err:
                self.logger.warning(f"❌ [SKIP] LengthFinishReasonError LengthLimit 초과. 응답 길이 제한으로 요약 생성 실패. error: {err}")
            except Exception as e:
                self.logger.warning(f"❌ [FAIL] 예기치 못한 오류 발생: {e}")
            
            self.logger.info(f"✅ [{idx+1}/{total}] 실행 완료: {entry_point} (남은 실행: {max_concurrent - sem._value})")
            time.sleep(0.2)
        
            return sequence_diagram_info

    async def _analyze_all(self, project_id, entry_point_list, llm, schema, max_concurrent=settings.MAX_CONCURRENT):
        sem = asyncio.Semaphore(max_concurrent)
        tasks = []
        
        # EntryPoint 별로 Sequence Diagram 생성
        for idx, entry_point in enumerate(entry_point_list):
            
            # 2. CALLTREE_SUMMARY 문서 조회
            call_tree_summary_doc: Optional[Document] = load_call_tree_summary_doc(project_id=project_id, entry_point=entry_point)
            
            if call_tree_summary_doc is None:
                self.logger.warning(f"🌧️ call_tree_summary_doc is None.")
                continue 

            # 3. CODE_ANALYSIS 문서 조회
            code_analysis_docs = load_documents_by_source_type(project_id=project_id, source_type=RagSourceType.CODE_ANALYSIS)
            call_sequence: List = call_tree_summary_doc.metadata.get("call_sequence", [])
            depth: int = call_tree_summary_doc.metadata.get("depth", 0)
            call_tree: Dict = call_tree_summary_doc.metadata.get("call_tree", {})
            call_tree_summary_title: str = call_tree_summary_doc.metadata.get("summary_title", "")
            call_tree_summary_insight: str = call_tree_summary_doc.metadata.get("insight", "")
            call_tree_summary_reasoning: str = call_tree_summary_doc.metadata.get("reasoning", "")
            
            method_definitions = {}
            for doc in code_analysis_docs:
                method_fqn = doc.metadata.get("method_fqn")
                if method_fqn in call_sequence:
                    method_definition = {
                        "method_fqn": method_fqn,
                        "summary": doc.metadata.get("summary", ""),
                        "class_name": doc.metadata.get("class_name", ""),
                        "package_name": doc.metadata.get("package_name", ""),
                        "return_type": doc.metadata.get("return_type", ""),
                        "display_name": self._extract_method_name_with_args(method_fqn),
                    }
                    
                    method_definitions[method_fqn] = method_definition
                else:
                    self.logger.warning(f"🌧️ It doesn't match the method_fqn. [{entry_point}] - [{method_fqn}]. call_sequence: [{call_sequence}]")
            
            tasks.append(self._analyze(llm=llm, schema=schema, entry_point=entry_point, depth=depth, call_tree=call_tree, method_definitions=method_definitions, call_tree_summary_title=call_tree_summary_title, call_tree_summary_insight=call_tree_summary_insight, call_tree_summary_reasoning=call_tree_summary_reasoning, sem=sem, max_concurrent=max_concurrent, idx=idx, total=len(entry_point_list)))
            
        return await asyncio.gather(*tasks)
    
    def _extract_method_name_with_args(self, fqn: str) -> str:
        try:
            name_part, args_part = fqn.split('(', 1)
            name = name_part.split('.')[-1]
            args = args_part
            return f"{name}({args}"
        except Exception as err:
            self.logger.error(f"❌ _extract_method_name_with_args error: {err}")
            return fqn


