# app/components/analysis_status.py

"""
분석 진행 상태 컴포넌트 모듈.

분석 진행 상태를 메인 화면 상단에 표시하는 Streamlit 컴포넌트 제공.
"""

import streamlit as st

def render_analysis_progress():
    """분석 진행 상태를 메인 화면 상단에 표시합니다."""
    st.markdown("##### 🚀 분석 진행 상태")

    # 현재 단계와 총 단계 수
    current_step = st.session_state.get("current_analysis_step", 1)
    total_steps = st.session_state.get("total_analysis_steps", 13)
    
    # 분석 실패
    if current_step < 0:
        progress = 0
        status_message = st.session_state.get("current_status_message", "분석 실패")
        st.markdown(f"**현재 단계**: {status_message} ({current_step}/{total_steps})")
        return
    elif current_step == 0:
        status_message = st.session_state.get("current_status_message", "분석 진행 중단")
        st.markdown(f"**현재 단계**: {status_message} ({current_step}/{total_steps})")
        return
        
    # 진행률 바
    progress = current_step / total_steps
    st.progress(progress)
    
    # 현재 상태 메시지
    status_message = st.session_state.get("current_status_message", "분석 준비 중...")
    st.markdown(f"**현재 단계**: {status_message} ({current_step}/{total_steps})")
