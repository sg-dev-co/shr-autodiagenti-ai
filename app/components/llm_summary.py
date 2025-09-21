# app/components/llm_summary.py

"""
LLM 해석 컴포넌트 모듈.

선택된 API에 대한 LLM 기반 설명과 요약을 표시하는 Streamlit 컴포넌트 제공.
"""

import json
from typing import Dict, Any
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, StAggridTheme

def render_llm_summary():
    """
    LLM 해석을 렌더링합니다.
    선택된 API에 대한 LLM 기반 설명과 요약을 표시합니다.
    """
    selected_api = st.session_state.get("selected_api")

    if not selected_api:
        st.info("👈 왼쪽에서 API를 선택해 주세요.")
        return

    analysis_result = st.session_state.get("analysis_result", {})
    api_result = analysis_result.get(selected_api, {})

    if not api_result:
        st.warning("⚠️ 선택된 API에 대한 분석이 완료되지 않았습니다.")
        st.markdown("먼저 코드를 분석한 뒤 요약 결과를 확인할 수 있습니다.")
        return

    llm_summary = api_result.get("insight")

    if not llm_summary:
        st.info("ℹ️ 선택된 API에 대한 LLM 분석 결과가 없습니다.")
        st.markdown("분석은 완료되었으나 LLM 요약이 제공되지 않았습니다.")
        return

    _render_summary_panel(api_result)


def _render_summary_panel(api_result: Dict[str, Any]):
    """
    구조화된 요약 정보 패널을 렌더링합니다.

    Args:
        api_result: 분석 결과
    """
    with st.container():
        st.markdown("##### 📢 기능 요약")
        st.info(api_result.get("insight", "요약 정보 없음"))

        st.markdown("")
        st.markdown("##### 🔄 처리 흐름")
        flow = api_result.get("reasoning", [])
        st.markdown(f"""
            <div style="
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                border-left: 4px solid #007bff;
                margin: 15px 0;
                line-height: 1.8;
                word-wrap: break-word;
                word-break: break-word;
                word-spacing: 0.1em;
                letter-spacing: 0.02em;
                font-size: 17px;
            ">
                {flow}
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("")

        with st.container():
            st.markdown("##### 🧩 주요 메서드 해석 요약")

            # 메서드 목록 생성
            methods = api_result.get("method_definitions", [])
            
            if not methods:
                st.markdown("메서드 해석 정보 없음")
            else:
                method_fqns = list(methods.keys())

                # 셀렉트 박스용 표시명 생성 (클래스명 + 메서드명)
                display_options = []
                display_to_fqn = {}

                for fqn in method_fqns:
                    method_info = methods[fqn]
                    class_name = method_info.get('class_name', '')
                    display_name = method_info.get('display_name', '')

                    # 셀렉트 박스용 표시명
                    select_display_name = f"{class_name}.{display_name}" if class_name else display_name
                    display_to_fqn[select_display_name] = fqn   # 매핑 저장
                    display_options.append(select_display_name)

                # 셀렉트 박스 생성
                st.markdown("**📘 메서드를 선택하세요**")
                selected_display = st.selectbox("", display_options, label_visibility="collapsed")

                # 선택된 항목으로 실제 FQN 찾기
                selected_fqn = display_to_fqn[selected_display]

                if selected_fqn:
                    method_info = methods[selected_fqn]
                    package_name = method_info.get('package_name', '')
                    class_name = method_info.get('class_name', '')
                    display_name = method_info.get('display_name', '')
                    summary = method_info.get('summary', '요약 없음')
                    return_type = method_info.get('return_type', '')
                    

                    # 데이터프레임 생성
                    df = pd.DataFrame({
                        "항목": ["메서드", "FQN", "패키지", "클래스", "요약", "반환값"],
                        "내용": [display_name, selected_fqn, package_name, class_name, summary, return_type]
                    })

                    # 옵션 빌더로 셀 스타일 설정
                    gb = GridOptionsBuilder.from_dataframe(df)
                    gb.configure_column("항목", wrapText=True, autoHeight=True, maxWidth=80) 
                    gb.configure_column("내용", wrapText=True, autoHeight=True)  # ✅ 줄바꿈 + 자동 높이
                    gb.configure_pagination(enabled=False) 
                    gridOptions = gb.build()
                    gridOptions['domLayout'] = 'autoHeight'

                    # 테이블 렌더링
                    AgGrid(df, 
                            gridOptions=gridOptions, 
                            fit_columns_on_grid_load=True,
                            custom_css={
                                "#gridToolBar": {
                                    "padding": "0px",
                                    "border": "none"
                                },
                                ".ag-root-wrapper": {
                                    "border": "none"
                                }
                            },
                            theme="balham"
                        )   
