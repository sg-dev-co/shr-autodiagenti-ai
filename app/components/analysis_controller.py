# app/components/analysis_controller.py

"""
프로젝트 분석 컴포넌트 모듈.

프로젝트 분석을 시작하고 결과를 표시하는 Streamlit 컴포넌트 제공.
"""

import streamlit as st
from app.services.analysis_runner import execute_analysis_steps
from app.services.api_client import get_entry_point_list
from app.utils.state_manager import reset_analysis_state, reset_error_state, reset_history_state
from server.utils.logger import get_logger

# 로거 선언
logger = get_logger(__name__)

def start_project_analysis():
    """
    프로젝트 분석을 시작합니다.
    """
    filter_options = st.session_state.get("filter_options", {})

    #--------------------------------------------
    # 분석 실행
    #--------------------------------------------
    # 기존 분석 상태 초기화
    reset_analysis_state()
    
    # 오류 상태 초기화
    reset_error_state()

    # 히스토리 상태 초기화
    reset_history_state()
    
    st.session_state.analysis_in_progress = True
    st.session_state.current_status_message = "프로젝트 분석을 시작합니다..."
    st.session_state.error_message = None
    
    # 분석 단계 실행 (UI 상태 업데이트는 내부에서 수행)
    if not execute_analysis_steps(filter_options):
        st.session_state.analysis_in_progress = False
        st.session_state.show_results = False  # 결과 표시 방지
        st.session_state.has_error = True
        st.session_state.analysis_in_progress = False
        return
    
    #--------------------------------------------
    # 분석 결과 조회
    #--------------------------------------------
    # EntryPoint 조회
    response = get_entry_point_list(project_id=st.session_state.project_id)
    logger.info(f"📢 get_entry_point_list response: {response}")
    
    if not response:
        st.session_state.error_message = "분석 결과 대상 Entry Point가 없습니다."
        st.session_state.analysis_in_progress = False
        st.session_state.show_results = False  # 결과 표시 방지
        st.session_state.has_error = True
        return    
    
    # EntryPoint Map 
    st.session_state.entry_point_info_map = response
    
    entry_point_list = response.keys()
    logger.info(f"📢 entry_point_list: {entry_point_list}")
    
    if not entry_point_list:
        st.session_state.error_message = "분석 결과 대상 Entry Point가 없습니다."
        st.session_state.analysis_in_progress = False
        st.session_state.show_results = False  # 결과 표시 방지
        st.session_state.has_error = True
        return
    
    st.session_state.entry_points = entry_point_list
    st.session_state.show_results = True
    st.session_state.analysis_in_progress = False
    st.session_state.has_error = False
    
    logger.info(f"✅ 분석이 완료되었습니다! {len(st.session_state.entry_points)}개의 Entry Points를 발견했습니다.")
    st.rerun()
