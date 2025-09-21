# app/utils/string_utils.py

import re
from datetime import datetime

def sanitize_name(name):
    """
    특수문자를 제거하고 안전한 형태로 변환
    
    Args:
        name (str): 변환할 문자열
        
    Returns:
        str: 특수문자가 제거되고 안전한 형태로 변환된 문자열
        
    Examples:
        >>> sanitize_name("test:file")
        "testfile"
        >>> sanitize_name("my project")
        "my_project"
    """
    # 특수문자 제거하고 공백은 밑줄로
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.strip().replace(".", "_")
    name = name.strip().replace("{", "-")
    name = name.strip().replace("}", "-")
    name = name.strip().replace(" ", "_")
    return name


def format_iso_datetime(iso_string: str) -> str:
    """
    ISO 형식 날짜 문자열을 년월일 시분초 형태로 변환
    
    Args:
        iso_string (str): ISO 형식의 날짜 문자열 (예: "2025-09-13T17:07:44.578665")
        
    Returns:
        str: 포맷팅된 날짜 문자열 (예: "2025년 09월 13일 17시 07분")
    """
    try:
        if not iso_string:
            return ""

        # ISO 형식을 파싱하여 포맷팅
        parsed_date = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        return parsed_date.strftime("%Y년 %m월 %d일 %H시 %M분")
    except:
        # 파싱 실패 시 원본 반환
        return iso_string