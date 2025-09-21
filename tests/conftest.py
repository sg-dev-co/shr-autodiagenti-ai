# tests/conftest.py

"""
Pytest 공통 픽스처
"""

import pytest
import tempfile
import os


@pytest.fixture
def temp_directory():
    """임시 디렉토리 픽스처"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def temp_file():
    """임시 파일 픽스처"""
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        yield temp_file.name
    # 테스트 후 파일 정리
    if os.path.exists(temp_file.name):
        os.unlink(temp_file.name)
