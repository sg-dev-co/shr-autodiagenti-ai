# app/utils/state_manager.py

"""
세션 상태 관리 모듈.

세션 상태를 초기화하고 초기화하는 함수 제공.
"""

import streamlit as st

def initialize_session_state():
    """세션 상태를 초기화"""
        
    if "has_error" not in st.session_state:
        st.session_state.has_error = False
    if "error_message" not in st.session_state:
        st.session_state.error_message = None
    if "project_id" not in st.session_state:
        st.session_state.project_id = None
    if "project_name" not in st.session_state:
        st.session_state.project_name = None
    if "orig_file_name" not in st.session_state:
        st.session_state.project_name = None
    if "analyzed_date" not in st.session_state:
        st.session_state.analyzed_date = None
    if "entry_points" not in st.session_state:
        st.session_state.entry_points = []
    if "entry_point_info_map" not in st.session_state:
        st.session_state.entry_point_info_map = []
    if "selected_api" not in st.session_state:
        st.session_state.selected_api = None
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = {}
    if "show_results" not in st.session_state:
        st.session_state.show_results = False
    if "filter_options" not in st.session_state:
        st.session_state.filter_options = {}
    if "current_file_name" not in st.session_state:
        st.session_state.current_file_name = None
    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = None
    if "current_analysis_step" not in st.session_state:
        st.session_state.current_analysis_step = 1
    if "total_analysis_steps" not in st.session_state:
        st.session_state.total_analysis_steps = 13
    if "current_status_message" not in st.session_state:
        st.session_state.current_status_message = "분석 준비 중..."
    if "analysis_in_progress" not in st.session_state:
        st.session_state.analysis_in_progress = False
    # 히스토리 관련 상태
    if "is_history_view" not in st.session_state:
        st.session_state.is_history_view = False
    if "selected_history" not in st.session_state:
        st.session_state.selected_history = None
    if "selected_history_project" not in st.session_state:
        st.session_state.selected_history_project = None

    st.session_state.status_result = {}


def reset_analysis_state():
    """분석 관련 상태 초기화"""
    # 분석 관련 상태
    st.session_state.project_id = None
    st.session_state.project_name = None
    st.session_state.current_file_name = None
    st.session_state.orig_file_name = None
    st.session_state.analyzed_date = None
    st.session_state.filter_options = {}
    st.session_state.status_result = {}
    st.session_state.analysis_result = {}
    st.session_state.entry_points = []
    st.session_state.entry_point_info_map = {}
    st.session_state.selected_api = None
    st.session_state.show_results = False
    st.session_state.current_analysis_step = 1
    st.session_state.total_analysis_steps = 13
    st.session_state.current_status_message = "분석 준비 중..."
    st.session_state.analysis_in_progress = False

    # previous_api_selection 초기화
    if "previous_api_selection" in st.session_state:
        del st.session_state.previous_api_selection
    
def reset_error_state():
    """오류 상태 초기화"""
    st.session_state.has_error = False
    st.session_state.error_message = None
    
def reset_history_state():
    """히스토리 관련 상태 초기화"""
    # 히스토리 관련 상태
    st.session_state.is_history_view = False
    st.session_state.selected_history = None
    st.session_state.selected_history_project = None
    