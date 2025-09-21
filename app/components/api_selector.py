# app/components/api_selector.py

"""
API 선택 컴포넌트 모듈.

분석된 Entry Points 중에서 API를 선택하는 Streamlit 컴포넌트 제공.
"""

import streamlit as st
from app.services.api_client import get_analysis_result


def render_api_selector():
    """
    API 선택기를 렌더링합니다.
    
    사이드바에 Entry Points 목록을 표시하고, 선택 기능을 제공합니다.
    초기 로딩 시와 선택이 변경될 때마다 콜백 함수를 호출하여 이벤트를 처리합니다.
    """
    entry_points = st.session_state.get("entry_points", [])
    
    if entry_points:
            
        # 현재 선택된 API를 가져옵니다
        current_selection = st.selectbox(
            "API 엔드포인트",
            entry_points,
            index=0,            
            key="api_selector_fixed"  # 이 한 줄만 추가
        )

        if st.session_state.get("is_history_view", False) and st.session_state.get("selected_history_project", None):
            project_id = st.session_state.get('selected_history_project', None)
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f5f5f5 0%, #e8eaf6 100%); color: #424242; padding: 12px 16px; border-radius: 8px; margin: 8px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.08); border: 1px solid #e0e0e0;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div>
                        <div style="font-size: 0.9em; opacity: 0.8; color: #616161;">🏷️ 선택된 프로젝트 ID</div>
                        <code style="background: transparent; padding: 2px 6px; border-radius: 3px; font-size: 0.9em;">{project_id}</code>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # 선택이 변경되었는지 확인하고 이벤트 핸들링을 수행합니다
        _handle_selection_change(current_selection)
        
        # 세션 상태에 선택된 API를 저장합니다
        st.session_state.selected_api = current_selection
    else:
        st.info("API 목록이 분석되면 여기에 표시됩니다.")


def _handle_selection_change(new_selection: str):
    """
    API 선택 변경을 감지하고 콜백 함수를 호출합니다.
    
    Args:
        new_selection (str): 새로 선택된 API 엔드포인트
        
    Note:
        이 함수는 초기 로딩 시와 선택이 변경되었을 때 모두 콜백을 호출합니다.
        콜백 함수에는 항상 현재 선택된 API 값이 전달됩니다.
    """
    # 이전 선택값이 세션에 저장되어 있는지 확인합니다
    if "previous_api_selection" not in st.session_state:
        # 초기 로딩 시 이전 선택값을 설정하고 콜백을 호출합니다
        st.session_state.previous_api_selection = new_selection
        _on_api_selection_changed(new_selection)
        return
    
    # 선택이 변경되었는지 확인합니다
    if st.session_state.previous_api_selection != new_selection:
        # 이전 선택값을 업데이트합니다
        st.session_state.previous_api_selection = new_selection
        
        # 선택 변경 콜백 함수를 호출합니다
        _on_api_selection_changed(new_selection)


def _on_api_selection_changed(selected_api: str):
    """
    API 선택 변경 시 호출되는 콜백 함수입니다.
    
    Args:
        selected_api (str): 새로 선택된 API 엔드포인트
    """
    
    entry_point_info_map = st.session_state.entry_point_info_map
    entry_point_info = entry_point_info_map.get(selected_api)
    entry_point = entry_point_info.get("entry_point")
    
    #------------------
    # 분석 결과 조회 
    #------------------
    response = None
    # 이미 조회된 데이터가 있는지 확인
    if "analysis_result" in st.session_state and selected_api in st.session_state.analysis_result:
        response = st.session_state.analysis_result[selected_api]
    
    if not response:
        response = get_analysis_result(analyzed_date=st.session_state.analyzed_date, project_id=st.session_state.project_id, entry_point=entry_point)
    
    if not response:
        st.session_state.error_message = "분석 결과가 없습니다."
        st.session_state.analysis_in_progress = False
        st.session_state.show_results = False  # 결과 표시 방지
        st.session_state.has_error = True
        return
    
    st.session_state.analysis_result[selected_api] = response
    
    # API 선택 성공 시 에러 상태 초기화
    st.session_state.has_error = False
    st.session_state.error_message = None
