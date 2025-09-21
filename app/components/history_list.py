# app/components/history_list.py

"""
히스토리 목록 컴포넌트 모듈.

히스토리 목록을 표시하는 Streamlit 컴포넌트 제공.
"""

import streamlit as st
from app.services.api_client import get_recent_analysis_projects, get_entry_point_list, search_analysis_projects, delete_history
from app.utils.constants import LLMModel
from app.utils.string_utils import format_iso_datetime
from app.utils.state_manager import reset_analysis_state, reset_error_state
from app.utils.logger import get_logger

# 로거 선언
logger = get_logger(__name__)

def render_history():
    """히스토리 목록을 렌더링합니다."""

    # CSS 스타일 추가
    st.markdown("""
    <style>
    .history-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border-left: 5px solid #007bff;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .history-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        border-left-color: #0056b3;
    }
    
    .history-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #007bff, #00d4ff);
    }
    
    .project-name {
        font-size: 18px;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 12px;
    }
    
    .project-info {
        color: #6c757d;
        font-size: 14px;
        line-height: 1.8;
        margin-bottom: 15px;
    }
    
    .info-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        padding: 4px 0;
    }
    
    .info-label {
        font-weight: 600;
        color: #495057;
        min-width: 80px;
    }
    
    .info-value {
        color: #6c757d;
        flex: 1;
        text-align: right;
    }
    
    .project-id {
        font-family: 'Courier New', monospace;
        background: #f8f9fa;
        padding: 6px 10px;
        border-radius: 6px;
        font-size: 12px;
        color: #495057;
        border: 1px solid #e9ecef;
        margin-top: 10px;
    }
    
    .llm-model-badge {
        background: linear-gradient(135deg, #28a745, #20c997);
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
    }
    
    .entry-point-badge {
        background: linear-gradient(135deg, #007bff, #0056b3);
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
    }
    
    .search-container {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 0 0 20px 0;
    }
    
    .section-title {
        color: #495057;
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 15px;
        padding-bottom: 8px;
        border-bottom: 2px solid #e9ecef;
    }
    </style>
    """, unsafe_allow_html=True)

    # 검색 기능
    with st.container():
        search_term = st.text_input("🔍 프로젝트 ID 검색", placeholder="프로젝트 ID 또는 프로젝트명 입력...", key="history_search")
        
    # 히스토리 목록
    if search_term and search_term.strip():  # 검색어가 있고 공백이 아닐 때만
        with st.expander(f"🔍 '{search_term}' 검색 결과", expanded=True):
            render_search_results(search_term)
    else:
        limit = 3
        with st.expander(f" 최근 분석 {limit}개", expanded=True):
            render_recent_history(limit=limit)

def render_search_results(search_term: str):
    """검색 결과를 표시합니다."""
    search_results = None

    try:
        search_results = search_analysis_projects(keyword=search_term)
        logger.info(f"📢 search_analysis_projects search_results: {search_results}")
    except Exception as err:
        logger.error(f"검색 중 오류가 발생했습니다: {str(err)}")
    
    if not search_results:
        st.info(f"'{search_term}'에 대한 검색 결과가 없습니다.")
        return
    
    if search_results and len(search_results) > 0:
        for idx, item in enumerate(search_results):
            is_last = (idx == len(search_results) - 1)
            render_history_card(item, is_last=is_last)
    else:
        st.info(f"'{search_term}'에 대한 검색 결과가 없습니다.")
    

def render_recent_history(limit: int = 3):
    """최근 분석 히스토리를 표시합니다."""
    try:
        history_data = get_recent_analysis_projects(limit=limit)

        if not history_data:
            st.info(f"최근 분석 히스토리가 없습니다.")  
            return
        
    except Exception as err:
        logger.error(f"최근 분석 히스토리 조회 중 오류가 발생했습니다: {str(err)}")
        st.info(f"최근 분석 히스토리가 없습니다.")
        return

    # 히스토리 표시    
    for idx, item in enumerate(history_data[:limit]):
        is_last = (idx == len(history_data[:limit]) - 1)
        render_history_card(item, is_last=is_last)
            
def render_history_card(item: dict, is_last: bool = False):
    """개별 히스토리 카드를 렌더링합니다."""
    
    logger.info(f"📢📢 render_history_card - item: [{item}]")
    
    project_id = item.get("project_id")
    project_name = item.get("project_name")
    analyzed_date = item.get("analyzed_date")
    analyzed_at = format_iso_datetime(item.get("analyzed_at"))
    entry_point_count = item.get("entry_point_count")
    llm_model_name = item.get("llm_model")
    model_display = LLMModel.get_display_name(llm_model_name)
    include_method_text = item.get("include_method_text", True)
    
    # 카드 HTML 생성
    card_html = f"""
    <div class="history-card">
        <div class="project-name">📁 {project_name}</div>
        <div class="project-info">
            <div class="info-row">
                <span class="info-label">분석일시:</span>
                <span class="info-value">{analyzed_at}</span>
            </div>
            <div class="info-row">
                <span class="info-label">EntryPoint:</span>
                <span class="info-value">
                    <span class="entry-point-badge">{entry_point_count}개</span>
                </span>
            </div>
            <div class="info-row">
                <span class="info-label">LLM 모델:</span>
                <span class="info-value">
                    <span class="llm-model-badge">{model_display}</span>
                </span>
            </div>
            <div class="info-row">
                <span class="info-label">분석 대상:</span>
                <span class="info-value">{'전체 소스코드' if include_method_text else '메타정보'}</span>
            </div>
        </div>
        <div class="project-id">{project_id}</div>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)
    
    # 버튼 컨테이너
    st.markdown("""
    <style>
    .stButton > button {
        margin: 0 !important;
        padding: 8px 12px !important;
        width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="small")  # gap을 최소화
    
    with col1:
        if st.button(f"🔍 상세보기", key=f"detail_{project_id}"):
            _handle_history_selection(project_id, item)
    
    with col2:
        if st.button(f"🗑️ 삭제", key=f"delete_{project_id}"):
            _handle_history_deletion(analyzed_date=analyzed_date, project_id=project_id, item=item)
    
    # 삭제 확인 상태 표시
    if st.session_state.get(f"confirm_delete_{project_id}", False):
        st.markdown("⚠️ **삭제 확인**: 위의 삭제 버튼을 다시 클릭하면 삭제됩니다.")
    
    # 마지막 카드가 아닐 때만 구분선 표시
    if not is_last:
        st.markdown("---")  # 카드 간 구분선

def _handle_history_selection(project_id: str, item: dict):
    """히스토리 선택을 처리합니다."""

    try:
        #--------------------------------------------
        # 분석 결과 조회
        #--------------------------------------------
        # 1. 기존 분석 상태 초기화
        reset_analysis_state()

        # 2. 오류 상태 초기화
        reset_error_state()

        # 프로젝트 정보 설정
        st.session_state.project_id = project_id
        st.session_state.project_name = item.get("project_name")
        st.session_state.analyzed_date = item.get("analyzed_at")
        
        # EntryPoint 조회
        response = get_entry_point_list(project_id=st.session_state.project_id)
        
        if not response:
            st.session_state.error_message = "분석 결과 대상 Entry Point가 없습니다."
            st.session_state.analysis_in_progress = False
            st.session_state.show_results = False  # 결과 표시 방지
            st.session_state.has_error = True
            return    
        
        # EntryPoint Map 
        st.session_state.entry_point_info_map = response
        
        entry_point_list = response.keys()
        
        if not entry_point_list:
            st.session_state.has_error = True
            st.session_state.error_message = "분석 결과 대상 Entry Point가 없습니다."
            st.session_state.analysis_in_progress = False
            st.session_state.show_results = False  # 결과 표시 방지
            return
        
        # 분석 상태 업데이트
        st.session_state.entry_points = entry_point_list
        st.session_state.show_results = True
        st.session_state.analysis_in_progress = False

        # 첫 번째 API로 선택 초기화
        if entry_point_list:
            first_api = list(entry_point_list)[0]
            st.session_state.selected_api = first_api
        
        # 히스토리 상태 업데이트
        st.session_state.is_history_view = True                     # 히스토리 뷰로 전환
        st.session_state.selected_history = item                    # 선택된 히스토리 데이터
        st.session_state.selected_history_project = project_id      # 선택된 프로젝트 ID
        st.session_state.show_results = True                        # 결과 표시

        # 추가: selectbox key 초기화
        if "api_selector_fixed" in st.session_state:
            del st.session_state.api_selector_fixed

        logger.info(f"히스토리 데이터를 불러오는데 성공했습니다: {str(response)}")
        st.rerun()
    except Exception as err:
        logger.error(f"히스토리 데이터를 불러오는 중 오류가 발생했습니다: {str(err)}")
        st.session_state.has_error = True
        st.session_state.error_message = f"히스토리 데이터를 불러오는 중 오류가 발생했습니다: {str(err)}"
        return

def _handle_history_deletion(analyzed_date: str, project_id: str, item: dict):
    """히스토리 삭제를 처리합니다."""
    
    # 히스토리 삭제
    response = delete_history(analyzed_date=analyzed_date, project_id=project_id)
    logger.info(f"📢 delete_history response: {response}")

    # 삭제된 항목을 세션 상태에서 제거
    if "deleted_history_items" not in st.session_state:
        st.session_state.deleted_history_items = set()
    st.session_state.deleted_history_items.add(project_id)
    
    logger.info(f"'{item.get('project_name')}' 분석 결과가 삭제되었습니다.")
    st.session_state[f"confirm_delete_{analyzed_date}_{project_id}"] = False
    st.rerun()