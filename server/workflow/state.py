# server/workflow/state.py
"""
워크플로우 상태 관리 모듈
"""

from enum import Enum
from datetime import datetime
from typing import TypedDict, Optional
from dataclasses import field
from server.utils.constants import AgentType, AgentRunType, LLMModel

# 상태 확인용 map
status_map = {}
TOTAL_STEPS = 13

class AnalysisStatus(Enum):
    UPLOAD_STARTED = ("upload_started", 1, "🔄 업로드 중")
    UPLOAD_COMPLETE = ("upload_complete", 2, "✅ 업로드 완료")
    PARSING_STARTED = ("parsing_started", 3, "🔄 CallTree 추출중")
    PARSING_COMPLETE = ("parsing_complete", 4, "✅ CallTree 추출 완료")
    CALLTREE_STARTED = ("calltree_started", 5, "🔄 CallTree 분석중")
    CALLTREE_COMPLETE = ("calltree_complete", 6, "✅ CallTree 분석 완료")
    CODE_ANALYSIS_STARTED = ("code_analysis_started", 7, "🔄 Method 분석중")
    CODE_ANALYSIS_COMPLETE = ("code_analysis_complete", 8, "✅ Method 분석 완료")
    FLOW_SUMMARY_STARTED = ("flow_summary_started", 9, "🔄 CallTree 흐름 요약중")
    FLOW_SUMMARY_COMPLETE = ("flow_summary_complete", 10, "✅ CallTree 흐름 요약 완료")
    DIAGRAM_STARTED = ("diagram_started", 11, "🔄 Sequence Diagram 생성중")
    DIAGRAM_COMPLETE = ("diagram_complete", 12, "✅ Sequence Diagram 생성 완료")
    DONE = ("done", 13, "🟢 완료")
    RAG_INDEXING_STARTED = ("rag_indexing_started", -2, "")
    RAG_INDEXING_COMPLETE = ("rag_indexing_complete", -2, "")
    FAILED = ("failed", -1, "🌧️ 분석 실패")
    
    def __init__(self, status, step, description):
        self.status = status
        self.step = step
        self.description = description
    
def convert_role_to_status(role: AgentType, runStatus: AgentRunType) -> AnalysisStatus:
    if role == AgentType.PARSER:
        if runStatus == AgentRunType.START:
            return AnalysisStatus.PARSING_STARTED
        else:
            return AnalysisStatus.PARSING_COMPLETE
    elif role == AgentType.RECURSIVE_CALL_TREE:
        if runStatus == AgentRunType.START:
            return AnalysisStatus.CALLTREE_STARTED
        else:
            return AnalysisStatus.CALLTREE_COMPLETE
    elif role == AgentType.CODE_ANALYSIS:
        if runStatus == AgentRunType.START:
            return AnalysisStatus.CODE_ANALYSIS_STARTED
        else:
            return AnalysisStatus.CODE_ANALYSIS_COMPLETE
    elif role == AgentType.CALL_TREE_SUMMARIZER:
        if runStatus == AgentRunType.START:
            return AnalysisStatus.FLOW_SUMMARY_STARTED
        else:
            return AnalysisStatus.FLOW_SUMMARY_COMPLETE
    elif role == AgentType.SEQUENCE_DIAGRAM:
        if runStatus == AgentRunType.START:
            return AnalysisStatus.DIAGRAM_STARTED
        else:
            return AnalysisStatus.DIAGRAM_COMPLETE
    elif role == AgentType.RAG_INDEXER:
        if runStatus == AgentRunType.START:
            return AnalysisStatus.RAG_INDEXING_STARTED
        else:
            return AnalysisStatus.RAG_INDEXING_COMPLETE
    elif role == AgentType.UPLOADER:
        if runStatus == AgentRunType.START:
            return AnalysisStatus.UPLOAD_STARTED
        else:
            return AnalysisStatus.UPLOAD_COMPLETE
    else:
        return AnalysisStatus.FAILED

def set_project_status_by_analysis_status(project_id: str, status: AnalysisStatus, custom_message: str=""):
    status_map[project_id] = {
        "status": status.status,
        "step": status.step,
        "total_steps": TOTAL_STEPS,
        "updated_at": datetime.now().isoformat(),
        "message": f"{status.description}({custom_message})" if custom_message else status.description
    }
    
def set_project_status(project_id: str, role: AgentType, runStatus: AgentRunType):
    status: AnalysisStatus = convert_role_to_status(role=role, runStatus=runStatus)
    set_project_status_by_analysis_status(project_id=project_id, status=status)
    
def set_project_done_status(project_id: str):
    set_project_status_by_analysis_status(project_id=project_id, status=AnalysisStatus.DONE)

def set_project_fail_status(project_id: str, error_message: str=""):
    set_project_status_by_analysis_status(project_id=project_id, status=AnalysisStatus.FAILED, custom_message=error_message)

def get_project_status(project_id: str):
    default_status = {
        "status": "",
        "step": 0,
        "total_steps": TOTAL_STEPS,
        "updated_at": datetime.now().isoformat(),
        "message": ""
    }
    
    return status_map.get(project_id, default_status)

class AutoDiagentiAnalysisState(TypedDict, total=False):
    """
    분석 워크플로우의 전체 상태를 관리하는 클래스
    """
    project_id: str = ""
    project_name: str = ""
    project_path: str = ""
    analyzed_date: str = ""
    analyzed_at: str = ""
    max_depth: int = -1
    
    # ✅ 파일 업로드, RAG 등 주요 유틸리티 상태
    file_info: Optional[dict] = field(default=None)
    
    # 필터 옵션
    filter_options: Optional[dict] = field(default=None)
    llm_model_info: LLMModel
    
    # ✅ Agent 관련
    agent_role: str
    agent_error: bool = False
    agent_error_message: str = ""
    agent_result: dict
    prev_node: str