# server/routers/upload.py

"""
파일 업로드 라우터
"""

import os
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import APIRouter, File, UploadFile, Depends
from server.db.database import get_db
from server.routers.response import BaseResponse
from server.db.dao.project_sequence_dao import generate_project_id
from server.utils.file_utils import save_upload_file, unzip_file, ensure_directory_exists
from server.utils.constants import AgentType, AgentRunType, DirInfo
from server.workflow.state import set_project_status, set_project_fail_status
from server.utils.logger import get_logger

# 로거 선언
logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/autodiagenti/file",
    tags=["autodiagenti", "file", "test"],
    responses={404: {"description": "Not found"}},
)

@router.post("/upload", response_model=BaseResponse)
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    logger.info("📢 START === upload_file ===")
    
    try:
        # Session ID 생성
        session_id = str(uuid.uuid4())
        
        # 디렉토리 생성
        ensure_directory_exists(DirInfo.UPLOAD_DIR)
        ensure_directory_exists(DirInfo.UNPACK_DIR)
        
        # 경로 설정
        analyzed_date = datetime.now().strftime('%Y%m%d')
        orig_file_name = os.path.splitext(file.filename)[0]
        extract_path = os.path.join(DirInfo.UNPACK_DIR)
        
        # 프로젝트 ID 생성
        project_id = generate_project_id(db, origin_name=orig_file_name, analyzed_date=analyzed_date)
        
        if not project_id:
            logger.error(f"❌ 파일 업로드 오류. project_id is empty.")
            logger.info("📢 END === upload_file ===")
            return BaseResponse(success=False, message="Fail to File Upload. project_id is empty.")
        
        # 상태저장
        set_project_status(project_id=project_id, role=AgentType.UPLOADER, runStatus=AgentRunType.START)
        
        # 압축해제 파일명/경로 설정
        zip_file_name = f"{project_id}.zip"
        zip_path = os.path.join(DirInfo.UPLOAD_DIR, zip_file_name)
        
        # 파일 업로드
        await save_upload_file(file, zip_path)
        logger.info("🟢 Complete - save_upload_file")

        # 압축 해제
        unzip_file(zip_path, extract_path)
        logger.info("🟢 Complete - unzip_file")
        
        # 상태저장
        set_project_status(project_id=project_id, role=AgentType.UPLOADER, runStatus=AgentRunType.END)
        
        result = {
            "session_id": session_id,
            "project_id": project_id,
            "project_name": orig_file_name,
            "file_info": {
                "file_name": zip_file_name,
                "file_path": extract_path,
                "orig_file_name": orig_file_name
            },
            "analyzed_date": analyzed_date
        }
        
        logger.info("📢 END === upload_file ===")
        return BaseResponse(success=True, result=result)
    except Exception as err:
        logger.error(f"❌ 파일 업로드 오류. error: [{str(err)}]")
        logger.info("📢 END === upload_file ===")
        return BaseResponse(success=False, message=f"Fail to File Upload. err({str(err)})")
    
    