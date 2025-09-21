# app/services/api_client.py

"""
API 클라이언트 모듈.

Streamlit UI에서 FastAPI 백엔드와 통신하는 API 클라이언트 제공
"""

import requests
import os
from typing import Optional, Dict
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# 포트 충돌 방지를 위해 환경변수 사용
API_BASE_URL = os.getenv("AUTODIAGENTI_API_BASE_URL")  # 환경변수로 API 서버 주소 관리

def _post_and_extract(api_path: str, payload: dict, field: str = None, multipart: bool = False, uploaded_file: Optional[object] = None) -> dict:
    """API 공통 호출 함수

    Args:
        api_path (str): 호출할 API 경로 (ex. "/chart/")
        payload (dict): 요청에 포함할 데이터(JSON)
        field (str, optional): result 내부에서 특정 필드만 추출할 경우 사용. Defaults to None.
        multipart (bool, optional): multipart 전송여부. Defaults to False.
        uploaded_file (Optional[object], optional): multipart 전송 file 데이터. Defaults to None.

    Returns:
        dict: response data (result 전체 또는 result[field] 값)
    """

    if not API_BASE_URL:
        raise Exception("🌧️API_BASE_URL 환경변수가 설정되지 않았습니다.")
    
    url = f"{API_BASE_URL}{api_path}"
    response = None
    
    try:
        if multipart:
            files = {"file": uploaded_file} if uploaded_file else None
            response = requests.post(url, data=payload, files=files, timeout=30)
        else:
            response = requests.post(url, json=payload, timeout=30)
        
        response.raise_for_status()
        
        response_json = response.json()
        
        if response_json.get("success") is not True:
            raise Exception(f"Fail to Request API. message: {response_json.get("message")}")
        
        data = response_json["result"]
        
        if field:
            return data.get(field)  # field가 있을 때만 해당 데이터 반환
        return data             # 기본적으로 result 전체 반환
    except requests.exceptions.RequestException as err:
        raise Exception(f"❌ API 호출 오류: ", err)
    except Exception as err:
        raise RuntimeError(f"📡 API 요청 실패: ", err)

def upload_file(uploaded_file: Optional[object] = None) -> dict:
    """
    파일 업로드
    """
    return _post_and_extract(api_path="/file/upload", payload={}, multipart=True, uploaded_file=uploaded_file)

def get_analysis_status(project_id: str) -> dict:
    """
    분석 상태 조회
    """
    return _post_and_extract(api_path="/analyze/status", payload={"project_id": project_id}, multipart=False, uploaded_file=None)

def run_analysis(session_id: str, project_id: str, project_name: str, analyzed_date: str, file_info: Dict, filter_options: Dict) -> dict:
    """
    분석 시작
    """
    request_payload = {
        "session_id": session_id,
        "project_id": project_id,
        "project_name": project_name,
        "analyzed_date": analyzed_date,
        "file_info": file_info,
        "filter_options": filter_options
    }
    
    return _post_and_extract(api_path="/analyze/run-analysis", payload=request_payload, multipart=False, uploaded_file=None)

def get_analysis_result(analyzed_date: str, project_id: str, entry_point: str) -> dict:
    """
    분석 결과 조회
    """
    return _post_and_extract(api_path="/analyze/result", payload={"analyzed_date": analyzed_date, "project_id": project_id, "entry_point": entry_point}, multipart=False, uploaded_file=None)

def get_entry_point_list(project_id: str) -> dict:
    """
    엔트리 포인트 목록 조회
    """
    return _post_and_extract(api_path="/entry-point/get-entry-point-list", payload={"project_id": project_id}, multipart=False, uploaded_file=None)

def get_recent_analysis_projects(limit: int = 3) -> dict:
    """
    최근 분석 프로젝트 조회
    """
    return _post_and_extract(api_path="/history/recent-analysis-projects", payload={"limit": limit}, multipart=False, uploaded_file=None)

def search_analysis_projects(keyword:str, limit: int = 3) -> dict:
    """
    키워드로 분석 프로젝트 조회
    """
    return _post_and_extract(api_path="/history/search-analysis-projects", payload={"keyword": keyword, "limit": limit}, multipart=False, uploaded_file=None)

def delete_history(analyzed_date:str, project_id: str):
    """
    히스토리 삭제
    """
    return _post_and_extract(api_path="/history/delete-project", payload={"analyzed_date": analyzed_date, "project_id": project_id}, multipart=False, uploaded_file=None)