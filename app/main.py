# app/main.py

"""
AutoDiagentiAI Streamlit 메인 애플리케이션.
"""

import streamlit as st
from app.components.file_uploader import render_file_uploader
from app.components.analysis_filter import render_analysis_filter
from app.components.api_selector import render_api_selector
from app.components.sequence_diagram import render_sequence_diagram
from app.components.llm_summary import render_llm_summary
from app.components.download_section import render_download_section
from app.components.analysis_status import render_analysis_progress
from app.components.analysis_controller import start_project_analysis
from app.components.history_list import render_history
from app.utils.state_manager import initialize_session_state

def render_welcome_screen():
    """웰컴 화면 렌더링"""
    st.markdown("""
    <div style='display: flex; justify-content: space-between; flex-wrap: wrap; gap: 1rem; padding: 0.5rem 0;'>
        <div style='flex: 1; min-width: 220px; background: #f9f9f9; border-radius: 10px; padding: 1rem;'>
            <h4>📁 프로젝트 업로드</h4>
            <p style='color: #555; font-size: 0.95rem;'>ZIP 파일을 업로드하여 분석을 시작하세요.</p>
        </div>
        <div style='flex: 1; min-width: 220px; background: #f9f9f9; border-radius: 10px; padding: 1rem;'>
            <h4>⚙️ 자동 분석</h4>
            <p style='color: #555; font-size: 0.95rem;'>API 엔트리포인트와 내부 호출 흐름을 자동 탐색합니다.</p>
        </div>
        <div style='flex: 1; min-width: 220px; background: #f9f9f9; border-radius: 10px; padding: 1rem;'>
            <h4>📊 시각화</h4>
            <p style='color: #555; font-size: 0.95rem;'>Mermaid 다이어그램으로 직관적으로 흐름을 표현합니다.</p>
        </div>
        <div style='flex: 1; min-width: 220px; background: #f9f9f9; border-radius: 10px; padding: 1rem;'>
            <h4>🖥️ AI 해석</h4>
            <p style='color: #555; font-size: 0.95rem;'>LLM을 활용해 흐름을 이해하고 요약 설명을 제공합니다.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_ui():
    """메인 애플리케이션 함수"""
    # 페이지 설정
    st.set_page_config(page_title="AutoDiagenti AI", page_icon="✨", layout="wide")
    
    # 헤더 설정
    st.markdown("## ✨ AutoDiagenti AI")
    with st.container():
        st.caption("Spring Framework 기반 프로젝트의 API 흐름 분석 및 시각화 도구")
        st.markdown("<hr style='margin: 0.5rem 0;'>", unsafe_allow_html=True)
        
    
    # 분석 상태(고정)
    if "progress_placeholder" not in st.session_state:
        st.session_state.progress_placeholder = st.empty()  

    # 메인 영역: 프로젝트 분석 + CallTree 결과
    if "error_message" in st.session_state:
        if st.session_state.error_message:
            st.error(st.session_state.error_message)
    
    with st.sidebar:
        tab1, tab2 = st.tabs(["🧊 분석", "🧭 히스토리"])

        with tab1:
            st.header("📁 프로젝트 업로드")
            render_file_uploader()

            # 📂 분석 범위 설정 영역 (업로드 후 표시)
            if st.session_state.get("uploaded_file"):
                    st.markdown("---")
                    with st.expander("⚙️ 분석 설정", expanded=False):
                        filter_options = render_analysis_filter()
                        # 필터 옵션을 세션에 저장
                        st.session_state.filter_options = filter_options
                    
                    # 분석 시작 버튼
                    st.markdown("---")

                    # 분석 중인지 확인
                    is_analyzing = st.session_state.get("analysis_in_progress", False)

                    if is_analyzing:
                        st.button("🔍 분석 중...", disabled=True, key="start_project_analysis_disabled")
                    else:
                        if st.button("🔍 분석 시작", key="start_project_analysis"):
                            st.session_state.analysis_in_progress = True
                            start_project_analysis()
                            

        with tab2:
            st.header("📋 분석 히스토리")
            render_history()
        
    # 🔍 API 선택 영역 (분석 완료 후에만 표시)
    if st.session_state.get("show_results", False):
        with st.sidebar:
            st.markdown("---")

            if st.session_state.get("is_history_view", False):
                st.subheader("🔍 API 흐름 선택(히스토리)")
            else:
                st.subheader("🔍 API 흐름 선택")

            render_api_selector()


    # 메인 영역에서 조건부 렌더링
    if not st.session_state.get("uploaded_file") and not st.session_state.get("show_results"):
        # 웰컴 메시지 표시
        render_welcome_screen()
    else:
        # 🔄 분석 중이면 상태 표시
        if st.session_state.get("analysis_in_progress", False):
            with st.session_state.progress_placeholder.container():
                render_analysis_progress()
        
        if not st.session_state.get("has_error", False):
            # 기존 프로젝트 분석 기능
            if st.session_state.selected_api:
                col1, col2 = st.columns([4, 1])  # 좌측: 시퀀스 / 우측: 요약
                
                with col1:
                    if st.session_state.get("is_history_view"):
                        st.subheader("📋 시퀀스 다이어그램(히스토리)")  # 히스토리 표기
                        render_sequence_diagram()
                    else:
                        st.subheader("📈 시퀀스 다이어그램")
                        render_sequence_diagram()
                
                with col2:
                    if st.session_state.get("is_history_view"):
                        st.subheader("🤖 LLM 해석(히스토리)")
                        render_llm_summary()
                    else:
                        st.subheader("🤖 LLM 해석 요약")
                        render_llm_summary()
                    
                    st.markdown("---")
                    st.subheader("📥 결과 내보내기")
                    render_download_section()
            elif st.session_state.get("show_results", False):
                st.info("API를 선택하면 다이어그램과 요약이 표시됩니다.")
            else:
                if "error_message" in st.session_state and st.session_state.error_message:
                    st.info("파일을 다시 업로드하고 분석을 시작해주세요.")
                else:
                    # 업로드 후에는 다른 메시지 표시
                    if st.session_state.get("uploaded_file"):
                        st.info("✅ 프로젝트 분석 준비가 완료되었습니다. 분석을 시작해주세요.")
                    else:
                        st.info("프로젝트를 업로드하고 분석을 시작해주세요.")
        else:
            st.info("파일을 다시 업로드하고 분석을 시작해주세요.")


if __name__ == "__main__":
    # 세션 상태 초기화
    initialize_session_state()
    
    render_ui()
