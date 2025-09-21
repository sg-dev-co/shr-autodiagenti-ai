# server/db/dao/entry_point_list_dao.py

from typing import List
from sqlalchemy.orm import Session
from server.db.model import EntryPoint
from server.db.schema import EntryPointCreate
from server.utils.logger import get_logger

# 로거 선언
logger = get_logger(__name__)

def insert_entry_point(db: Session, data: EntryPointCreate) -> EntryPoint:
    """
    Entry Point 데이터를 entry_point_list 테이블에 저장
    """
    db_query = EntryPoint(
        analyzed_date=data.analyzed_date,
        project_id=data.project_id,
        session_id=data.session_id,
        entry_point=data.entry_point,
        api_name=data.api_name,
        api_method=data.api_method,
        annotaion=data.annotation,
        file_path=data.file_path,
        analyzed_at=data.analyzed_at
    )
    db.add(db_query)
    db.commit()
    db.refresh(db_query)
    return db_query

def insert_entry_points_bulk(db: Session, entry_points: List[EntryPointCreate]) -> bool:
    """
    EntryPoint 여러 건을 일괄 저장
    """
    try:
        entry_point_models = [
            EntryPoint(**ep.model_dump()) for ep in entry_points  # ✅ 변환
        ]
        db.bulk_save_objects(entry_point_models)
        db.commit()
        return True
    except Exception as err:
        logger.error(f"🌧️ Error insert_entry_points_bulk. {str(err)}")
        db.rollback()
        return False

def delete_entry_points_by_project_and_date(db: Session, analyzed_date: str, project_id: str) -> int:
    """
    특정 날짜 + 프로젝트의 entry_point 전체 삭제
    → 삭제된 건수를 반환
    """
    try:
        deleted_count = db.query(EntryPoint).filter_by(
                            analyzed_date=analyzed_date,
                            project_id=project_id
                        ).delete()
        db.commit()
        return deleted_count
    except Exception as err:
        logger.error(f"🌧️ Error delete_entry_points_by_project_and_date. {str(err)}")
        db.rollback()
        return -1

def get_entry_point_by_pk(db: Session, analyzed_date: str, project_id: str, entry_point: str) -> EntryPoint:
    """
    특정 일자, project_id, Entry Point 에 해당하는 Entry Point 정보를 조회
    """
    return db.query(EntryPoint).filter_by(
            analyzed_date=analyzed_date,
            project_id=project_id,
            entry_point=entry_point
        ).first()

def get_entry_point_list_by_project(db:Session, project_id: str) -> list[EntryPoint]:
    """
    특정 project_id에 해당하는 Entry Point 목록을 조회
    """
    return db.query(EntryPoint).filter(EntryPoint.project_id == project_id).order_by(EntryPoint.analyzed_date).all()
    

def get_all_entry_point_list(db: Session) -> list[EntryPoint]:
    """
    모든 Entry Point 목록을 조회
    """
    return db.query(EntryPoint).order_by(EntryPoint.project_id, EntryPoint.entry_point).all()

