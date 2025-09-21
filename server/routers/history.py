# server/routers/history.py

"""
히스토리 라우터
"""

from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from server.db.database import get_db
from server.db.model import AnalysisHistory
from server.db.dao.analysis_history_dao import get_recent_project_summaries, search_project_summaries_by_keyword, delete_analysis_history_by_project_id_and_date
from server.routers.response import BaseResponse
from server.utils.logger import get_logger

# 로거 선언
logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/autodiagenti/history",
    tags=["autodiagenti", "history", "test"],
    responses={404: {"description": "Not found"}},
)

class RecentHistoriesRequest(BaseModel):
    limit: Optional[int] = 3

@router.post("/recent-analysis-projects", response_model=BaseResponse)
def get_recent_analysis_projects(request: RecentHistoriesRequest, db: Session = Depends(get_db)):
    logger.info(f"🖥️ get_recent_analysis_projects - request: {request}")
    result = get_recent_project_summaries(db, limit=request.limit)
    logger.info(f"🖥️ get_recent_analysis_projects - result: {result}")
    return BaseResponse(success=True, result=result)


class SearchHistoriesRequest(BaseModel):
    keyword: str
    limit: Optional[int] = 3

@router.post("/search-analysis-projects", response_model=BaseResponse)
def search_analysis_projects(request: SearchHistoriesRequest, db: Session = Depends(get_db)):
    logger.info(f"🖥️ search_analysis_projects - request: {request}")
    result = search_project_summaries_by_keyword(db, keyword=request.keyword, limit=request.limit)
    logger.info(f"🖥️ search_analysis_projects - result: {result}")
    return BaseResponse(success=True, result=result)


class DeleteHistoryRequest(BaseModel):
    analyzed_date: str
    project_id: str

@router.post("/delete-project", response_model=BaseResponse)
def delete_history(request: DeleteHistoryRequest, db: Session = Depends(get_db)):
    logger.info(f"🖥️ delete_history - request: {request}")
    deleted_count = delete_analysis_history_by_project_id_and_date(db, analyzed_date=request.analyzed_date, project_id=request.project_id)
    
    if deleted_count < 0:
        return BaseResponse(success=False, message="히스토리 삭제 처리에 실패했습니다. 잠시 후 다시 시도해주세요.")
    
    result = {
        "deleted_count": deleted_count
    }
    logger.info(f"🖥️ delete_history - result: {result}")
    return BaseResponse(success=True, result=result)

