# server/db/model.py

"""
데이터베이스 테이블을 정의
"""

from sqlalchemy import Column, Integer, Float, String, Text, Boolean, DateTime, PrimaryKeyConstraint, JSON
from sqlalchemy.sql import func
from server.db.database import Base
from datetime import datetime

# 1. entry_point 테이블 모델
class EntryPoint(Base):
    __tablename__ = "entry_point"

    analyzed_date = Column(String, nullable=False)  # YYYYMMDD
    project_id = Column(String, nullable=False)
    entry_point = Column(String, nullable=False)
    
    session_id = Column(String, nullable=True)
    api_name = Column(String, nullable=True)
    api_method = Column(String, nullable=True)
    annotation = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    
    analyzed_at = Column(DateTime, nullable=False, default=datetime.now())
    timestamp = Column(DateTime(timezone=True), server_default=func.now())  # 생성 시점 자동 기록

    __table_args__ = (
        PrimaryKeyConstraint('analyzed_date', 'project_id', 'entry_point', name='pk_entry_point'),
    )


# 2.analysis_history 테이블 모델
class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    analyzed_date = Column(String, nullable=False)  # YYYYMMDD
    project_id = Column(String, nullable=False)
    entry_point = Column(String, nullable=False)
    session_id = Column(String, nullable=False)
    
    project_name = Column(String, nullable=True)
    uploaded_path = Column(String, nullable=True)
    file_name = Column(String, nullable=True)           # Zip File Name
    orig_file_name = Column(String, nullable=True)
    exclude_packages = Column(Text, nullable=True)
    custom_annotations = Column(Text, nullable=True)
    include_method_text = Column(Boolean, nullable=True)
    
    api_name = Column(String, nullable=True)            # 예: "/api/v1/users"
    api_method = Column(String, nullable=True)          # 예: "GET", "POST"
    annotation = Column(Text, nullable=True)            # 예: @RequestMapping("/...")
    
    llm_model = Column(String, nullable=False)
    llm_version = Column(String, nullable=False)
    temperature = Column(Float, nullable=True)

    mermaid_code = Column(Text, nullable=True)          # 멀티라인 텍스트
    summary_title = Column(Text, nullable=True)
    insight = Column(Text, nullable=True)
    reasoning = Column(Text, nullable=True)
    
    analysis_results = Column(JSON, nullable=False)     # 전체 분석 결과 (LLM 포함 전체 JSON)

    analyzed_at = Column(DateTime, nullable=False, default=datetime.now())
    timestamp = Column(DateTime(timezone=True), server_default=func.now())  # 생성 시점 자동 기록

    __table_args__ = (
        PrimaryKeyConstraint(
            'analyzed_date',
            'project_id',
            'entry_point',
            name='pk_analysis_history'
        ),
    )


# 3.project_sequence 테이블 모델
class ProjectSequence(Base):
    __tablename__ = "project_sequence"

    origin_name = Column(String, nullable=False)
    analyzed_date = Column(String, nullable=False)      # YYYYMMDD
    seq = Column(Integer, nullable=False, default=1)    # 최종시퀀스

    created_at = Column(DateTime, nullable=False, default=datetime.now())
    timestamp = Column(DateTime(timezone=True), server_default=func.now())  # 생성 시점 자동 기록

    __table_args__ = (
        PrimaryKeyConstraint('origin_name', 'analyzed_date', name='pk_project_sequence'),
    )
