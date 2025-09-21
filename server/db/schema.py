# server/db/schema.py

"""
DTO 클래스 정의
"""

from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


# Entry Point 입력용 스키마
class EntryPointCreate(BaseModel):
    analyzed_date: str              # YYYYMMDD
    project_id: str
    entry_point: str
    session_id: Optional[str] = None
    api_name: Optional[str] = None
    api_method: Optional[str] = None
    annotation: Optional[str] = None
    file_path: Optional[str] = None
    analyzed_at: datetime

class ProjectSequenceCreate(BaseModel):
    analyzed_date: str              # YYYYMMDD
    origin_name: str

class AnalysisHistoryCreate(BaseModel):
    analyzed_date: str                          # 예: "20250831"
    project_id: str
    entry_point: str
    session_id: str
    
    project_name: Optional[str] = None
    uploaded_path: Optional[str] = None
    file_name: Optional[str] = None
    orig_file_name: Optional[str] = None
    exclude_packages: Optional[str] = None
    custom_annotations: Optional[str] = None
    include_method_text: Optional[bool] = None

    api_name: Optional[str] = None
    api_method: Optional[str] = None
    annotation: Optional[str] = None

    llm_model: str
    llm_version: str
    temperature: Optional[float] = None

    mermaid_code: Optional[str] = None
    summary_title: Optional[str] = None
    insight: Optional[str] = None
    reasoning: Optional[str] = None

    analysis_results: Any                      # 전체 분석 JSON
    analyzed_at: datetime
    