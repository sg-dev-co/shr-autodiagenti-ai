# app/components/sequence_diagram.py

"""
시퀀스 다이어그램 컴포넌트 모듈.

선택된 API의 시퀀스 다이어그램을 표시하는 Streamlit 컴포넌트 제공
"""

import streamlit as st
from streamlit_mermaid import st_mermaid
from typing import Dict, Any
from app.utils.mermaid_utils import decode_mermaid_code


def render_sequence_diagram():
    """
    시퀀스 다이어그램을 렌더링
    """
    selected_api = st.session_state.get("selected_api")
    
    if not selected_api:
        return
    
    # API 분석 결과 확인
    analysis_result = st.session_state.get("analysis_result", {})
    api_result = analysis_result.get(selected_api, {})
    
    # 다이어그램 목록 확인
    mermaid_code = api_result.get("mermaid_code", "")
    
    if not mermaid_code:
        st.warning("이 API에 대한 시퀀스 다이어그램이 없습니다.")
        return
    
    # 다이어그램 표시
    _render_diagram_content(selected_api, api_result)


def _render_diagram_content(selected_api: str, api_result: Dict[str, Any]):
    """
    다이어그램 내용을 렌더링
    
    Args:
        api_result: 분석 결과 데이터
    """

    # 다이어그램 제목
    title = api_result.get("summary_title", "N/A")
    st.success(f"📝 {title}")
    
    # API 정보 표시
    if selected_api:
        entry_point = api_result.get("entry_point")     # 프로젝트 ID 표시
        llm_model = api_result.get("llm_model")         # LLM 모델 표시 정보
        
        if entry_point and llm_model:
            st.markdown(f"🔗 **API:** `{selected_api}` | &nbsp;&nbsp; **Entry Point Method FQN:** `{entry_point}` | &nbsp;&nbsp; **LLM Model:** `{llm_model}`")
        elif entry_point:  
            st.markdown(f"🔗 **API:** `{selected_api}` | &nbsp;&nbsp; **Entry Point Method FQN:** `{entry_point}`")
        elif llm_model:
            st.markdown(f"🔗 **API:** `{selected_api}` | &nbsp;&nbsp; **LLM Model:** `{llm_model}`") 
        else:
            st.markdown(f"**API:** `{selected_api}`")
            
    mermaid_code = api_result.get("mermaid_code", "")
    mermaid_code = decode_mermaid_code(mermaid_code)
    
    if mermaid_code:
        try:
            st_mermaid(mermaid_code, height=1200)
        except Exception as e:
            st.error(f"다이어그램 렌더링 오류: {str(e)}")
            st.code(mermaid_code, language="mermaid")
    else:
        st.warning("다이어그램 데이터가 없습니다.")