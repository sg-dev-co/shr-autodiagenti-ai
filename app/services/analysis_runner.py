# app/services/analysis_runner.py

"""
분석 실행 모듈.

분석 단계를 실행하고 진행 상황을 세션 상태에 반영하는 함수 제공.
"""

import time
import streamlit as st
from app.components.analysis_status import render_analysis_progress
from app.services.api_client import get_analysis_status, upload_file, run_analysis
from app.utils.logger import get_logger

# 로거 선언
logger = get_logger(__name__)

def execute_analysis_steps(filter_options: dict) -> bool:
    """
    분석 단계를 실행하고 진행 상황을 세션 상태에 반영

    Returns:
        bool: 분석 성공 여부
    """
    
    # 파일 업로드 시작
    upload_result = None
    
    try:
        upload_result = upload_file(uploaded_file=st.session_state.uploaded_file)
        
        if upload_file is None:
            st.session_state.analysis_in_progress = False
            st.session_state.show_results = False  # 결과 표시 방지
            st.session_state.error_message = f"❌ 파일 업로드 처리에 실패했습니다: Upload File Result is None"
            return False
    except Exception as err:
        st.session_state.analysis_in_progress = False
        st.session_state.show_results = False  # 결과 표시 방지
        st.session_state.error_message = f"❌ 파일 업로드 처리에 실패했습니다: {err}"
        return False
        
    # project id 설정    
    project_id = upload_result.get("project_id")
    st.session_state.project_id = project_id
    
    # analyzed_date 설정
    analyzed_date = upload_result.get("analyzed_date")
    st.session_state.analyzed_date = analyzed_date
    
    # orig_file_name 설정
    orig_file_name = upload_result.get("file_info", {}).get("orig_file_name")
    st.session_state.orig_file_name = orig_file_name
    
    # 분석 API 호출
    run_analysis(session_id=upload_result.get("session_id"), 
                project_id=project_id, 
                project_name=upload_result.get("project_name"), 
                analyzed_date=upload_result.get("analyzed_date"), 
                file_info=upload_result.get("file_info", {}),
                filter_options=filter_options)
    
    """
    상태 API 응답을 기반으로 분석 단계 진행 UI 표시
    """
    for _ in range(300):  # 최대 5분간 polling
        try:
            response = get_analysis_status(project_id=st.session_state.project_id)
        except Exception as e:
            logger.error(f"❌ Status API 호출 실패: {str(e)}")
            # 재시도 또는 에러 처리
            time.sleep(2)  # 2초 대기 후 재시도
            continue

        st.session_state.status_result = response
        
        status = response.get("status")
        step = response.get("step", 1)
        total_steps = response.get("total_steps", 13)
        message = response.get("message", "")
        updated_at = response.get("updated_at", "")
        
        # 응답값 반영
        st.session_state.total_analysis_steps = status
        st.session_state.current_analysis_step = step
        st.session_state.total_analysis_steps = total_steps
        st.session_state.current_status_message = message

        # 상태 표시 UI 갱신
        with st.session_state.progress_placeholder.container():
            render_analysis_progress()
            
        # ✅ 상태에 따른 분기 처리
        if status == "done": # 완료되면 종료
            return True
        elif status == "error" or step < 0:
            logger.error(f"분석 실패. status: {status}")
            st.session_state.analysis_in_progress = False
            st.session_state.show_results = False  # 결과 표시 방지
            st.session_state.error_message = f"❌ 분석 중 오류 발생: {message}"
            return False
        elif status == "failed":
            logger.error(f"분석 실패. status: {status}")
            st.session_state.analysis_in_progress = False
            st.session_state.show_results = False  # 결과 표시 방지
            st.session_state.error_message = f"❌ 분석 중 오류 발생: {message}"
            return False
        elif step == 0:
            logger.error(f"분석 진행 중단. step: {step}")
            st.session_state.analysis_in_progress = False
            st.session_state.show_results = False  # 결과 표시 방지
            st.session_state.error_message = f"❌ 분석 중단"
            return False
        time.sleep(1)  # 1초 간격 polling

    st.session_state.analysis_in_progress = False
    st.session_state.show_results = False  # 결과 표시 방지
    st.session_state.error_message = f"Time Out"
    return False
