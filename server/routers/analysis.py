# server/routers/analysis.py

"""
분석 라우터
"""

from typing import Optional
from fastapi import APIRouter, Depends
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from server.db.database import get_db
from server.db.model import AnalysisHistory
from server.db.dao.analysis_history_dao import get_analysis_history_by_entry_point
from server.routers.response import BaseResponse
from server.workflow.state import get_project_status
from server.workflow.graph import run_autodiagenti_graph
from server.utils.constants import LLMModel
from server.utils.document_retrieval_utils import load_sequence_diagram_doc
from server.utils.logger import get_logger

# 로거 선언
logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/autodiagenti/analyze",
    tags=["autodiagenti", "analysis", "test"],
    responses={404: {"description": "Not found"}},
)

class StatusRequest(BaseModel):
    project_id: str
    
@router.post("/status", response_model=BaseResponse)
def get_analysis_status_post(request: StatusRequest):
    logger.info(f"🖥️ get_analysis_status_post - request: {request}")
    result = get_project_status(request.project_id)
    return BaseResponse(success=True, result=result)


class FileInfo(BaseModel):
    file_name: str
    file_path: str
    orig_file_name: str
    
class FilterOptions(BaseModel):    
    include_method_text: bool = True
    exclude_packages: Optional[str] = None
    custom_annotations: Optional[str] = None
    llm_model: str
    llm_version: str
    
class AnalysisRequest(BaseModel):
    session_id: str
    project_id: str
    project_name: str
    analyzed_date: str
    file_info: FileInfo
    filter_options: FilterOptions
    
@router.post("/run-analysis", summary="분석 실행", description="LangGraph 분석 파이프라인을 시작합니다.", response_model=BaseResponse)
def run_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    logger.info(f"🖥️ run_analysis - request: {request}")
    #--------------------------------------------
    # 옵션값 확인
    #--------------------------------------------
    project_id = request.project_id
    filter_options = request.filter_options
    
    if not filter_options:
        return BaseResponse(success=False, message="옵션 설정을 다시 확인해주세요.")
    
    llm_model_name = filter_options.llm_model
    llm_version = filter_options.llm_version
    llm_model_info:LLMModel = LLMModel.get_by_name(llm_model_name)
    
    if not llm_model_info:
        return BaseResponse(success=False, message="LLM모델 설정을 다시 확인해주세요.") 
    
    logger.info(f"🖥️ run_analysis - request:{llm_model_name}/{llm_version} - llm_model: {llm_model_info.model_name}/{llm_model_info.version}")
    
    #--------------------------------------------
    # 분석 진행
    #--------------------------------------------
    # 백그라운드에서 분석 파이프라인 실행 (add_task는 param 순서대로 매핑함)
    background_tasks.add_task(run_autodiagenti_graph, request.session_id, project_id, request.project_name, request.analyzed_date, request.file_info.model_dump(), request.filter_options.model_dump(), llm_model_info)
    
    result = {"message": f"분석을 시작했습니다: {project_id}"}
    return BaseResponse(success=True, result=result)


class ResultRequest(BaseModel):
    analyzed_date: str
    project_id: str
    entry_point: str
    
@router.post("/result", summary="분석 결과 조회", description="DB에서 분석 결과를 조회합니다.", response_model=BaseResponse)
def get_analysis_result(request: ResultRequest, db: Session = Depends(get_db)):
    logger.info(f"🖥️ get_analysis_result - request: {request}")
    
    result = {}
    
    # DB에서 저장된 분석 결과 조회
    analysis_result: AnalysisHistory = get_analysis_history_by_entry_point(db, analyzed_date=request.analyzed_date, project_id=request.project_id, entry_point=request.entry_point)
    
    if analysis_result:
        result = {
                "entry_point": analysis_result.entry_point,
                "llm_model": analysis_result.llm_model,
                "llm_version": analysis_result.llm_version,
                "llm_temperature": analysis_result.temperature,
                "mermaid_code": analysis_result.mermaid_code,
                "summary_title": analysis_result.summary_title,
                "insight": analysis_result.insight,
                "reasoning": analysis_result.reasoning,
                "method_definitions": analysis_result.analysis_results.get("method_definitions"),
                "analyzed_at": analysis_result.analyzed_at
        }
        logger.info(f"🖥️ get_analysis_result - DB result: {result}")
    
    # DB에 저장된 내역이 없으면 RAG 조회
    if not analysis_result or not result:
        logger.info("📢 DB 조회결과 없음. RAG에서 재조회.")
        # RAG에서 저장된 분석 결과 조회
        sequence_diagram_doc = load_sequence_diagram_doc(project_id=request.project_id, entry_point=request.entry_point)
    
        if sequence_diagram_doc:        
            meta = sequence_diagram_doc.metadata
            result = {
                "entry_point": meta.get("entry_point"),
                "llm_model": meta.get("llm_model"),
                "llm_version": meta.get("llm_version"),
                "llm_temperature": meta.get("llm_temperature"),
                "mermaid_code": meta.get("mermaid_code"),
                "summary_title": meta.get("summary_title"),
                "insight": meta.get("insight"),
                "reasoning": meta.get("reasoning"),
                "method_definitions": meta.get("method_definitions"),
                "analyzed_at": meta.get("analyzed_at")
            }
            logger.info(f"🖥️ get_analysis_result - RAG result: {result}")
    
    logger.info(f"🖥️ get_analysis_result - result: {result}")
    
    if result:     
        return BaseResponse(success=True, result=result)
    else:
        return BaseResponse(success=False, message="No analysis results found.")