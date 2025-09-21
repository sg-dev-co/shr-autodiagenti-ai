
# server/routers/entry_point_list_router.py

"""
Entry Point 관리 라우터
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from server.db.database import get_db
from server.db.schema import EntryPointCreate
from server.db.dao.entry_point_list_dao import insert_entry_point, get_entry_point_list_by_project, get_all_entry_point_list
from server.routers.response import BaseResponse
from server.utils.logger import get_logger

# 로거 선언
logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/autodiagenti/entry-point",
    tags=["autodiagenti", "entry-point", "db", "test"],
    responses={404: {"description": "Not found"}},
)

# ProjectId로 Entry Point 조회   
class EntryPointRequest(BaseModel):
    project_id: str
    
@router.post("/get-entry-point-list", response_model=BaseResponse)
def get_entry_point_list(request: EntryPointRequest, db: Session = Depends(get_db)):    
    logger.info(f"🖥️ get_entry_point_list - request: {request}")
    
    try:
        entry_point_list = get_entry_point_list_by_project(db, project_id=request.project_id)
        
        logger.info(f"====== entry_point_list: [{entry_point_list}]")

        result = {
            f"{entry_point.api_method}_{entry_point.api_name}" if entry_point.api_method else entry_point.api_name: {
                "analyzed_date": entry_point.analyzed_date,
                "project_id": entry_point.project_id,
                "session_id": entry_point.session_id,
                "entry_point": entry_point.entry_point,
                "api_name": entry_point.api_name,
                "api_method": entry_point.api_method,
                "annotation": entry_point.annotation,
                "analyze_at": entry_point.analyzed_at
            }
            for entry_point in entry_point_list
            if entry_point.api_name
        }
        
        return BaseResponse(success=True, result=result)
    except Exception as err:
        logger.error(f"❌ Entry Point 조회 오류. err:{err}")
        return BaseResponse(success=False, message=f"Error fetching entry point list: {err}")