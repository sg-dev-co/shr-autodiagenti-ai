# app/components/analysis_filter.py

"""
분석 전 필터 컴포넌트 모듈.

분석 범위를 설정하는 필터 옵션을 표시하는 Streamlit 컴포넌트 제공.
"""

import streamlit as st
from typing import Dict, Any
from utils.constants import LLMModel

def render_analysis_filter():
    """
    분석 전 필터를 렌더링합니다.
    
    Returns:
        Dict[str, Any]: 필터 옵션 설정
    """

    # 기본 분석 루트 (표시용)
    base_path = "src/main/java"
    st.markdown(f"**기본 분석 경로:** `{base_path}` *(수정 불가)*")

    # 분석 옵션 섹션
    st.markdown("---")
    st.markdown("**⚙️ 분석 옵션**")

    # 메서드 본문 포함 여부
    include_method_text = st.checkbox(
        "📝 메서드 본문 포함 여부",
        value=True,
        help="메서드 내부 코드를 분석에 포함할지 여부를 설정합니다."
    )
    
    # 커스텀 어노테이션 (엔트리포인트 식별용)
    custom_annotations = st.text_input(
        "🏷️ 커스텀 어노테이션",
        placeholder="예: RestController,RequestMapping,PostMapping",
        help="엔트리포인트 식별에 사용할 사용자 정의 어노테이션을 쉼표로 구분하여 입력하세요."
    )

    # 제외할 패키지 접두어
    exclude_packages = st.text_input(
        "📦 제외할 패키지 접두어",
        placeholder="예: com.example.test,org.junit",
        help="쉼표로 구분된 패키지 접두어를 입력하세요."
    )
    
    # LLM 모델 선택
    st.markdown("---")
    st.subheader("🖥️ LLM 모델 선택")

    llm_options = LLMModel.get_display_name_to_model_dict()

    llm_model = st.radio(
        "LLM 모델",
        list(llm_options.keys()),
        index=0,
        help="LLM 모델을 선택하세요."
    )

    # 선택된 모델명으로 Enum 조회
    selected_model = llm_options[llm_model]

    # 정리된 필터 옵션 반환
    return {
        "base_path": base_path,
        "include_method_text": include_method_text,
        "custom_annotations": ",".join([a.strip() for a in custom_annotations.split(",") if a.strip()]),
        "exclude_packages": ",".join([p.strip() for p in exclude_packages.split(",") if p.strip()]),
        "llm_model": selected_model.model_name,
        "llm_version": selected_model.version
    }
