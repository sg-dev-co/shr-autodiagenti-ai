# app/components/file_uploader.py

"""
파일 업로드 컴포넌트 모듈.

ZIP 파일 업로드 및 분석 시작을 위한 Streamlit 컴포넌트 제공.
"""

import streamlit as st
import hashlib
import time
from typing import Optional

def render_file_uploader():
    """
    파일 업로더를 렌더링합니다.
    
    ZIP 파일 업로드 및 분석 시작 기능을 제공합니다.
    """
    # 파일 업로드
    uploaded_file = st.file_uploader("ZIP 파일을 업로드하세요", type=["zip"])
    
    if uploaded_file:
        # 파일이 변경되었는지 확인하고 Toast 메시지 표시
        current_file_name = uploaded_file.name
        
        if (not st.session_state.get("analysis_in_progress", False) and 
            not st.session_state.get("show_results", False) and
            ("current_file_name" not in st.session_state or st.session_state.current_file_name != current_file_name)):
            st.toast(f"📁 {current_file_name} 분석 준비 완료")
            st.session_state.current_file_name = current_file_name
        
        # 프로젝트 ID와 업로드된 파일을 세션에 저장
        st.session_state.uploaded_file = uploaded_file


