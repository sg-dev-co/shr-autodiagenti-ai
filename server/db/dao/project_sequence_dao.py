# server/db/dao/project_sequence_dao.py

from datetime import datetime
from sqlalchemy.orm import Session
from server.db.model import ProjectSequence
from server.utils.logger import get_logger

# 로거 선언
logger = get_logger(__name__)

def generate_project_id(db: Session, origin_name: str, analyzed_date: str) -> str:
    """
    origin_name + analyzed_date 조합으로 project_id 생성.
    - 기존 시퀀스 있으면 +1
    - 없으면 1부터 시작
    - 반환값 예: demo_20250906_001
    """
    record = db.query(ProjectSequence).filter_by(
        origin_name=origin_name,
        analyzed_date=analyzed_date
    ).first()
    
    if record:
        record.seq += 1
    else:
        record = ProjectSequence(
            origin_name=origin_name,
            analyzed_date=analyzed_date,
            seq=1,
            created_at=datetime.now()
        )
        db.add(record)
        
    db.commit()
    db.refresh(record)
    
    # 3자리 시퀀스 문자열로 조합
    project_id = f"{origin_name}_{analyzed_date}_{record.seq:03}"
    return project_id

