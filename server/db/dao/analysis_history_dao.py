# server/db/dao/analysis_history_dao.py
    
from typing import List, Dict
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from server.db.model import AnalysisHistory
from server.db.schema import AnalysisHistoryCreate

from server.utils.logger import get_logger

# 로거 선언
logger = get_logger(__name__)

def insert_bulk_analysis_history(db: Session, data_list: list[AnalysisHistoryCreate]) -> None:
    """
    여러 분석 이력을 analysis_history 테이블에 일괄 저장
    """
    try:
        models = [
            AnalysisHistory(**data.model_dump()) for data in data_list    
        ]
        db.bulk_save_objects(models)
        db.commit()
        return True
    except Exception as err:
        logger.error(f"🌧️ Error insert_bulk_analysis_history. {str(err)}")
        db.rollback()
        return False
        
def delete_analysis_history_by_project_id_and_date(db: Session, analyzed_date: str, project_id: str) -> int:
    """
    특정 날짜 + project_id에 해당하는 전체 분석 이력을 삭제
    → 삭제된 건수를 반환
    """
    try:
        deleted_count = db.query(AnalysisHistory).filter_by(
                            analyzed_date=analyzed_date,
                            project_id=project_id
                        ).delete()
        db.commit()
        return deleted_count
    except Exception as err:
        logger.error(f"🌧️ Error delete_analysis_history_by_project_id_and_date. {str(err)}")
        db.rollback()
        return -1

def get_analysis_history_by_entry_point(
    db: Session,
    analyzed_date: str,
    project_id: str,
    entry_point: str
) -> AnalysisHistory:
    """
    특정 Entry Point에 대한 분석 이력 조회
    """
    return (
        db.query(AnalysisHistory)
        .filter_by(
            analyzed_date=analyzed_date,
            project_id=project_id,
            entry_point=entry_point
        )
        .order_by(AnalysisHistory.timestamp.desc())
        .first()
    )

def get_latest_analysis_histories_by_project_id(
    db: Session,
    project_id: str,
    limit: int = 3
) -> list[AnalysisHistory]:
    """
    특정 프로젝트 ID 기준으로 최신 분석 이력 3건 조회
    """
    return (
        db.query(AnalysisHistory)
        .filter(AnalysisHistory.project_id == project_id)
        .order_by(AnalysisHistory.analyzed_at.desc())
        .limit(limit)
        .all()
    )


def get_recent_project_ids(db: Session, limit: int = 3) -> list[str]:
    """
    전체 분석 이력에서 project_id를 기준으로 그룹핑하여
    가장 최근 분석된 project_id 3개 조회
    """
    subquery = (
        db.query(
            AnalysisHistory.project_id,
            func.max(AnalysisHistory.analyzed_at).label("latest_analyzed_at")
        )
        .group_by(AnalysisHistory.project_id)
        .subquery()
    )

    result = (
        db.query(subquery.c.project_id)
        .order_by(subquery.c.latest_analyzed_at.desc())
        .limit(limit)
        .all()
    )

    return [row.project_id for row in result]


def get_recent_project_summaries(db: Session, limit: int = 3) -> List[Dict]:
    """
    최근 분석된 프로젝트들 중 project_id 기준으로 그룹핑하여,
    최신 분석 요약 정보 반환 (최대 N개)
    """
    subquery = (
        db.query(
            AnalysisHistory.project_id,
            func.max(AnalysisHistory.analyzed_at).label("latest_analyzed_at")
        )
        .group_by(AnalysisHistory.project_id)
        .order_by(desc("latest_analyzed_at"))
        .limit(limit)
        .subquery()
    )

    results = (
        db.query(
            AnalysisHistory.project_id,
            func.max(AnalysisHistory.project_name).label("project_name"),      
            func.max(AnalysisHistory.orig_file_name).label("orig_file_name"),
            func.max(AnalysisHistory.analyzed_at).label("analyzed_at"),
            func.max(AnalysisHistory.analyzed_date).label("analyzed_date"),
            func.count(AnalysisHistory.entry_point).label("entry_point_count"),
            func.max(AnalysisHistory.llm_model).label("llm_model"),
            func.max(AnalysisHistory.llm_version).label("llm_version"),
            func.max(AnalysisHistory.include_method_text).label("include_method_text")
        )
        .join(subquery, AnalysisHistory.project_id == subquery.c.project_id)
        .group_by(AnalysisHistory.project_id)
        .order_by(desc("analyzed_at"))
        .all()
    )

    return [
        {
            "project_id": row.project_id,
            "project_name": row.project_name,
            "orig_file_name": row.orig_file_name,
            "analyzed_at": row.analyzed_at,
            "analyzed_date": row.analyzed_date,
            "entry_point_count": row.entry_point_count,
            "llm_model": row.llm_model,
            "llm_version": row.llm_version,
            "include_method_text": row.include_method_text
        }
        for row in results
    ]


def search_project_summaries_by_keyword(db: Session, keyword: str, limit: int = 3) -> List[Dict]:
    """
    입력된 키워드로 project_id LIKE 검색하여,
    프로젝트별 최신 분석 요약 정보 반환
    """
    subquery = (
        db.query(
            AnalysisHistory.project_id,
            func.max(AnalysisHistory.analyzed_at).label("latest_analyzed_at")
        )
        .filter(AnalysisHistory.project_id.like(f"%{keyword}%"))
        .group_by(AnalysisHistory.project_id)
        .order_by(desc("latest_analyzed_at"))
        .limit(limit)
        .subquery()
    )

    results = (
        db.query(
            AnalysisHistory.project_id,
            func.max(AnalysisHistory.project_name).label("project_name"),      
            func.max(AnalysisHistory.orig_file_name).label("orig_file_name"),
            func.max(AnalysisHistory.analyzed_at).label("analyzed_at"),
            func.max(AnalysisHistory.analyzed_date).label("analyzed_date"),
            func.count(AnalysisHistory.entry_point).label("entry_point_count"),
            func.max(AnalysisHistory.llm_model).label("llm_model"),
            func.max(AnalysisHistory.llm_version).label("llm_version"),
            func.max(AnalysisHistory.include_method_text).label("include_method_text")
        )
        .join(subquery, AnalysisHistory.project_id == subquery.c.project_id)
        .group_by(AnalysisHistory.project_id)
        .order_by(desc("analyzed_at"))
        .all()
    )

    return [
        {
            "project_id": row.project_id,
            "project_name": row.project_name,
            "orig_file_name": row.orig_file_name,
            "analyzed_at": row.analyzed_at,
            "analyzed_date": row.analyzed_date,
            "entry_point_count": row.entry_point_count,
            "llm_model": row.llm_model,
            "llm_version": row.llm_version,
            "include_method_text": row.include_method_text
        }
        for row in results
    ]



    