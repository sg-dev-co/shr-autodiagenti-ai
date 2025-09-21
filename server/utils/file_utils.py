# server/utils/file_utils.py

"""
파일 관리 유틸리티 모듈
"""

import os
import zipfile
import shutil
import json
from pathlib import Path
from fastapi import UploadFile
from typing import Union, Any
from server.utils.logger import get_logger

# 로거 선언
logger = get_logger(__name__)

async def save_upload_file(upload_file: UploadFile, dest_path: str) -> None:
    """
    업로드된 파일을 지정된 경로에 저장
    
    Args:
        upload_file: FastAPI UploadFile 객체
        dest_path: 저장할 파일 경로
    """
    # 디렉토리가 없으면 생성
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    # 파일 저장
    with open(dest_path, "wb") as buffer:
        contents = await upload_file.read()
        buffer.write(contents)


def unzip_file(zip_path: str, extract_to: str) -> None:
    """
    ZIP 파일을 지정된 경로에 압축 해제
    
    Args:
        zip_path: 압축 해제할 ZIP 파일 경로
        extract_to: 압축 해제할 대상 디렉토리
    """
    # zip 파일 이름에서 확장자 제거 & 최상위 폴더명으로 사용
    base_name = os.path.splitext(os.path.basename(zip_path))[0]
    extract_root = os.path.join(extract_to, base_name)
    
    # 압축 해제 디렉토리 생성
    os.makedirs(extract_root, exist_ok=True)
    
    # ZIP 파일 압축 해제
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_root)


def ensure_directory_exists(directory_path: str) -> None:
    """
    디렉토리가 존재하지 않으면 생성
    
    Args:
        directory_path: 생성할 디렉토리 경로
    """
    os.makedirs(directory_path, exist_ok=True)


def cleanup_temp_files(file_path: str) -> None:
    """
    임시 파일을 삭제
    
    Args:
        file_path: 삭제할 파일 경로
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.error(f"파일 삭제 중 오류 발생: {e}")


def cleanup_temp_directory(directory_path: str) -> None:
    """
    임시 디렉토리와 그 내용을 삭제
    
    Args:
        directory_path: 삭제할 디렉토리 경로
    """
    try:
        if os.path.exists(directory_path):
            shutil.rmtree(directory_path)
    except Exception as e:
        logger.error(f"디렉토리 삭제 중 오류 발생: {e}")


def load_json(path: Union[str, Path]) -> Any:
    """
    JSON 파일을 로드
    
    Args:
        path: 로드할 JSON 파일 경로
    """
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data: Any, path: Union[str, Path]) -> None:
    """
    JSON 파일을 저장
    
    Args:
        data: 저장할 데이터
        path: 저장할 JSON 파일 경로
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)