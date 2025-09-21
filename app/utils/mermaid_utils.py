# app/utils/mermaid_utils.py

"""
Mermaid 유틸리티 모듈.

Mermaid 코드를 처리하고 변환하는 유틸리티 함수 제공.
"""

import os
import base64
import requests
from typing import Union
from dotenv import load_dotenv
from app.utils.logger import get_logger

# 로거 선언
logger = get_logger(__name__)

# .env 파일에서 환경 변수 로드
load_dotenv()

ASSETS_BASE_URL = os.getenv("AUTODIAGENTI_API_ASSETS_JS_URL")  # 환경변수로 API 서버 주소 관리

def decode_mermaid_code(raw_code: str) -> str:
    """
    JSON 등에서 이스케이프된 Mermaid 코드 문자열의 개행 문자 등을 디코딩
    예: '\\n' → '\n'
    """
    if not raw_code:
        return ""
    return raw_code.replace("\\n", "\n")

def _fetch_mermaid_data(mermaid_code: str, format_type: str, domain: str) -> Union[bytes, str]:
    """Mermaid 데이터를 가져오는 공통 함수"""
    
    if not mermaid_code or len(mermaid_code.strip()) == 0:
        raise Exception("Mermaid 코드가 비어있습니다")

    # UTF-8 인코딩 후 Base64 인코딩
    encoded = base64.b64encode(mermaid_code.encode('utf-8')).decode('utf-8')

    if domain == "mermaid.ink":
        # mermaid.ink는 GET 방식
        if format_type == "png":
            url = f"https://mermaid.ink/img/{encoded}"
        elif format_type == "svg":
            url = f"https://mermaid.ink/svg/{encoded}"
        else:
            raise Exception(f"지원하지 않는 형식: {format_type}")

        response = requests.get(url, timeout=5)

    elif domain == "kroki.io":
        # kroki.io는 POST 방식 사용
        url = f"https://kroki.io/mermaid/{format_type}"
        headers = {"Content-Type": "application/json"}
        payload = {"diagram_source": mermaid_code}

        response = requests.post(url, headers=headers, json=payload, timeout=5)

    else:
        raise Exception(f"지원하지 않는 도메인: {domain}")

    # 응답 처리
    if response.status_code == 200:
        return response.content if format_type == "png" else response.text
    else:
        raise Exception(f"{domain} 응답 오류: Status {response.status_code}")

def get_mermaid_svg(mermaid_code: str) -> str:
    """Mermaid 코드를 SVG로 변환 (kroki.io → mermaid.ink 순서로 시도)"""
    errors = []  # 실패한 오류들을 모음
    
    # 1차 시도: mermaid.ink
    try:
        logger.info("mermaid.ink로 SVG 생성 시도...")
        return _fetch_mermaid_data(mermaid_code, "svg", "mermaid.ink")
    except Exception as e:
        logger.error(f"mermaid.ink SVG 생성 실패: {str(e)}")
        errors.append(str(e))

    # 2차 시도: kroki.io (백업)
    try:
        logger.info("kroki.io로 SVG 생성 시도...")
        return _fetch_mermaid_data(mermaid_code, "svg", "kroki.io")
    except Exception as e:
        logger.error(f"kroki.io SVG 생성 실패: {str(e)}")
        errors.append(str(e))
    
    # 모든 시도 실패 - 기존 오류 정보 활용
    all_errors = " | ".join(errors)
    raise Exception(f"모든 SVG 생성 서비스가 실패했습니다: {all_errors}")

def get_mermaid_png(mermaid_code: str) -> bytes:
    """Mermaid 코드를 PNG로 변환 (mermaid.ink → kroki.io 순서로 시도)"""
    errors = []

    # 1차 시도: mermaid.ink
    try:
        logger.info("mermaid.ink로 PNG 생성 시도...")
        return _fetch_mermaid_data(mermaid_code, "png", "mermaid.ink")
    except Exception as e:
        logger.error(f"mermaid.ink PNG 생성 실패: {str(e)}")
        errors.append(str(e))
    
    # 2차 시도: kroki.io
    try:
        logger.info("kroki.io로 PNG 생성 시도...")
        return _fetch_mermaid_data(mermaid_code, "png", "kroki.io")
    except Exception as e:
        logger.error(f"kroki.io PNG 생성 실패: {str(e)}")
        errors.append(str(e))
    
    # 모든 시도 실패
    all_errors = " | ".join(errors)
    raise Exception(f"PNG 변환 실패: {all_errors}")

def get_cached_mermaid_png(mermaid_code: str) -> bytes:
    """캐시된 PNG 데이터 반환"""
    import streamlit as st
    
    cache_key = f"png_{hash(mermaid_code)}"
    
    if cache_key not in st.session_state:
        try:
            st.session_state[cache_key] = get_mermaid_png(mermaid_code)
        except Exception as e:
            st.session_state[cache_key] = None
            st.session_state[f"{cache_key}_error"] = str(e)
    
    return st.session_state[cache_key]

def get_cached_mermaid_svg(mermaid_code: str) -> str:
    """캐시된 SVG 데이터 반환"""
    import streamlit as st
    
    cache_key = f"svg_{hash(mermaid_code)}"
    
    if cache_key not in st.session_state:
        try:
            st.session_state[cache_key] = get_mermaid_svg(mermaid_code)
        except Exception as e:
            st.session_state[cache_key] = None
            st.session_state[f"{cache_key}_error"] = str(e)
    
    return st.session_state[cache_key]