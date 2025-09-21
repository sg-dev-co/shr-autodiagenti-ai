# app/components/download_section.py

"""
다운로드 섹션 컴포넌트 모듈.

분석 결과를 다양한 형식으로 다운로드하는 Streamlit 컴포넌트 제공.
"""
import json
import streamlit as st
from typing import Dict
from app.utils.string_utils import sanitize_name
from app.utils.mermaid_utils import decode_mermaid_code, get_cached_mermaid_png, get_cached_mermaid_svg



def render_download_section():
    """
    다운로드 섹션을 렌더링합니다.
    
    선택된 API의 분석 결과를 다양한 형식으로 다운로드할 수 있는 기능을 제공합니다.
    """
    selected_api = st.session_state.get("selected_api")
    
    if not selected_api:
        st.info("👈 왼쪽에서 API를 선택해 주세요.")
        return
    
    project_id = st.session_state.project_id
    analysis_result = st.session_state.get("analysis_result", {})
    api_result = analysis_result.get(selected_api, {})
    
    mermaid_code = api_result.get("mermaid_code", "")
    mermaid_code = decode_mermaid_code(mermaid_code)
    
    selected_api = st.session_state.selected_api
    conv_selected_api = sanitize_name(selected_api)
    
    base_file_name = f"{project_id}_{conv_selected_api}"
    
    # 다운로드 버튼들
    col1, col2, col3, col4 = st.columns([1.2, 1.2, 1.2, 1.4])  # JSON 버튼이 조금 더 넓게
    
    with col1:
        file_name = f"{base_file_name}_sequence_diagram.mmd"
        st.download_button("💾 MMD", mermaid_code.encode("utf-8"), file_name, "text/plain")
        
    with col2:
        file_name = f"{base_file_name}_sequence_diagram.png"

        content = None
        error_message = None

        if mermaid_code and len(mermaid_code.strip()) > 0:
            # 캐시된 데이터 사용
            content = get_cached_mermaid_png(mermaid_code)
            error_key = f"png_{hash(mermaid_code)}_error"
            
            if content is not None:
                st.download_button(
                    label="🖼️ PNG", 
                    data=content, 
                    file_name=file_name, 
                    mime="image/png"
                )
            else:
                st.download_button(
                    label="❌ PNG", 
                    data=b"", 
                    file_name=file_name, 
                    mime="image/png",
                    disabled=True
                )
                
                # 오류 메시지 표시
                if error_key in st.session_state:
                    st.caption(f"PNG 생성 실패: {st.session_state[error_key]}")
        else:
            st.download_button(
                label="❌ PNG", 
                data=b"", 
                file_name=file_name, 
                mime="image/png",
                disabled=True
            )

    
    with col3:
        file_name = f"{base_file_name}_sequence_diagram.svg"
    
        if mermaid_code and len(mermaid_code.strip()) > 0:
            # 캐시된 데이터 사용
            content = get_cached_mermaid_svg(mermaid_code)
            error_key = f"svg_{hash(mermaid_code)}_error"
            
            if content is not None:
                st.download_button(
                    label="💾 SVG",
                    data=content,
                    file_name=file_name,
                    mime="image/svg+xml"
                )
            else:
                st.download_button(
                    label="❌ SVG", 
                    data=b"", 
                    file_name=file_name, 
                    mime="image/svg+xml",
                    disabled=True
                )
                
                # 오류 메시지 표시
                if error_key in st.session_state:
                    st.caption(f"SVG 생성 실패: {st.session_state[error_key]}")
        else:
            st.download_button(
                label="❌ SVG", 
                data=b"", 
                file_name=file_name, 
                mime="image/svg+xml",
                disabled=True
            )

    with col4:
        file_name = f"{base_file_name}_sequence_diagram.json"
        
        entry_point_info_map = st.session_state.entry_point_info_map
        entry_point_info = entry_point_info_map.get(selected_api)
        
        # JSON 데이터 생성
        json_data = {
            "metadata": {
                "project_id": st.session_state.project_id,
                "api_name": selected_api,
                "entry_point_info": entry_point_info
            },
            "analysis_result": api_result
        }
        
        # 다운로드 버튼 표시
        st.download_button(
            label="🧾 JSON",
            data=json.dumps(json_data, indent=2, ensure_ascii=False),
            file_name=file_name,
            mime="application/json"
        )

    # 프로젝트 ID 표시 (다운로드 버튼들 하단에)
    project_id = st.session_state.project_id
    if project_id:
        st.markdown("---")
        st.caption(f"🔍 프로젝트 ID: `{project_id}`")
 
