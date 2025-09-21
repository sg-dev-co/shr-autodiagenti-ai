# server/utils/document_utils.py

"""
문서 관리 유틸리티 모듈
"""

import uuid
from pathlib import Path
from server.utils.constants import RagSourceType
from server.utils.logger import get_logger

# 로거 선언
logger = get_logger(__name__)

def generate_uuid() -> str:
    """고유한 UUID 생성

    Returns:
        str: 생성된 UUID 문자열.
    """
    return str(uuid.uuid4().hex[:8])

def generate_document_id(source_type: str, project_id: str, **kwargs) -> str:
    """
    소스 타입에 따라 고유한 document_id 생성

    Args:
        source_type (str): 문서 출처 타입
        project_id (str): 프로젝트ID (쿼리ID)
        kwargs: 문서 정보에 따라 달라지는 인자들

    Returns:
        str: document_id
    """
    
    uuid = generate_uuid()
    
    if source_type in {RagSourceType.PARSER, RagSourceType.CODE, RagSourceType.COMMENTS}:
        file_path = Path(kwargs.get("file_path") or "unknown.java")
        file_stem = file_path.stem if file_path else "unknown"
        return f"{project_id}::{source_type}::{file_stem}::{uuid}"
    elif source_type in {RagSourceType.CALLTREE, RagSourceType.CALLTREE_SUMMARY, RagSourceType.SEQUENCE_DIAGRAM}:
        entry_point = kwargs.get("entry_point")
        return f"{project_id}::{source_type}::{entry_point}"
    elif source_type in {RagSourceType.CODE_ANALYSIS}:
        method_fqn = kwargs.get("method_fqn")
        return f"{project_id}::{source_type}::{method_fqn}"
    else:
        return f"{project_id}::{uuid}"
