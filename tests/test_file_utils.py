# tests/test_file_utils.py

"""
file_utils 테스트 코드
"""

import pytest
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi import UploadFile
from server.utils.file_utils import (
    save_upload_file,
    unzip_file,
    ensure_directory_exists,
    cleanup_temp_files,
    cleanup_temp_directory,
    load_json,
    save_json
)


class TestSaveUploadFile:
    """save_upload_file 함수 테스트"""
    
    @pytest.mark.asyncio
    async def test_save_upload_file_basic(self):
        """기본 파일 저장 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            dest_path = os.path.join(temp_dir, "test_file.txt")
            
            # Mock UploadFile 생성
            mock_file = MagicMock(spec=UploadFile)
            mock_file.read.return_value = b"test content"
            
            await save_upload_file(mock_file, dest_path)
            
            # 파일이 생성되었는지 확인
            assert os.path.exists(dest_path)
            with open(dest_path, "rb") as f:
                assert f.read() == b"test content"
    
    @pytest.mark.asyncio
    async def test_save_upload_file_with_nested_directories(self):
        """중첩 디렉토리 파일 저장 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            dest_path = os.path.join(temp_dir, "nested", "deep", "test_file.txt")
            
            mock_file = MagicMock(spec=UploadFile)
            mock_file.read.return_value = b"nested content"
            
            await save_upload_file(mock_file, dest_path)
            
            # 디렉토리와 파일이 생성되었는지 확인
            assert os.path.exists(dest_path)
            assert os.path.exists(os.path.dirname(dest_path))
    
    @pytest.mark.asyncio
    async def test_save_upload_file_empty_content(self):
        """빈 내용 파일 저장 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            dest_path = os.path.join(temp_dir, "empty_file.txt")
            
            mock_file = MagicMock(spec=UploadFile)
            mock_file.read.return_value = b""
            
            await save_upload_file(mock_file, dest_path)
            
            assert os.path.exists(dest_path)
            with open(dest_path, "rb") as f:
                assert f.read() == b""


class TestUnzipFile:
    """unzip_file 함수 테스트"""
    
    def test_unzip_file_basic(self):
        """기본 ZIP 파일 압축 해제 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 테스트용 ZIP 파일 생성
            zip_path = os.path.join(temp_dir, "test.zip")
            extract_to = os.path.join(temp_dir, "extract")
            
            # 간단한 ZIP 파일 생성
            import zipfile
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                zipf.writestr("file1.txt", "content1")
                zipf.writestr("file2.txt", "content2")
            
            unzip_file(zip_path, extract_to)
            
            # 압축 해제된 파일들 확인
            expected_dir = os.path.join(extract_to, "test")
            assert os.path.exists(expected_dir)
            assert os.path.exists(os.path.join(expected_dir, "file1.txt"))
            assert os.path.exists(os.path.join(expected_dir, "file2.txt"))
    
    def test_unzip_file_with_nested_structure(self):
        """중첩 구조 ZIP 파일 압축 해제 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "nested.zip")
            extract_to = os.path.join(temp_dir, "extract")
            
            import zipfile
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                zipf.writestr("folder/file1.txt", "content1")
                zipf.writestr("folder/subfolder/file2.txt", "content2")
            
            unzip_file(zip_path, extract_to)
            
            expected_dir = os.path.join(extract_to, "nested")
            assert os.path.exists(os.path.join(expected_dir, "folder", "file1.txt"))
            assert os.path.exists(os.path.join(expected_dir, "folder", "subfolder", "file2.txt"))
    
    def test_unzip_file_empty_zip(self):
        """빈 ZIP 파일 압축 해제 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "empty.zip")
            extract_to = os.path.join(temp_dir, "extract")
            
            import zipfile
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                pass  # 빈 ZIP 파일
            
            unzip_file(zip_path, extract_to)
            
            expected_dir = os.path.join(extract_to, "empty")
            assert os.path.exists(expected_dir)


class TestEnsureDirectoryExists:
    """ensure_directory_exists 함수 테스트"""
    
    def test_ensure_directory_exists_new_directory(self):
        """새 디렉토리 생성 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir = os.path.join(temp_dir, "new_directory")
            
            ensure_directory_exists(new_dir)
            
            assert os.path.exists(new_dir)
            assert os.path.isdir(new_dir)
    
    def test_ensure_directory_exists_existing_directory(self):
        """기존 디렉토리 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 디렉토리가 이미 존재하는 경우
            ensure_directory_exists(temp_dir)
            
            assert os.path.exists(temp_dir)
            assert os.path.isdir(temp_dir)
    
    def test_ensure_directory_exists_nested_directories(self):
        """중첩 디렉토리 생성 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_dir = os.path.join(temp_dir, "level1", "level2", "level3")
            
            ensure_directory_exists(nested_dir)
            
            assert os.path.exists(nested_dir)
            assert os.path.isdir(nested_dir)


class TestCleanupTempFiles:
    """cleanup_temp_files 함수 테스트"""
    
    def test_cleanup_temp_files_existing_file(self):
        """기존 파일 삭제 테스트"""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(b"test content")
        
        # 파일이 존재하는지 확인
        assert os.path.exists(temp_path)
        
        # 파일 삭제
        cleanup_temp_files(temp_path)
        
        # 파일이 삭제되었는지 확인
        assert not os.path.exists(temp_path)
    
    def test_cleanup_temp_files_nonexistent_file(self):
        """존재하지 않는 파일 삭제 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            nonexistent_file = os.path.join(temp_dir, "nonexistent.txt")
            
            # 파일이 존재하지 않는지 확인
            assert not os.path.exists(nonexistent_file)
            
            # 삭제 시도 (오류 없이 실행되어야 함)
            cleanup_temp_files(nonexistent_file)
    
    @patch('server.utils.file_utils.os.remove')
    def test_cleanup_temp_files_exception_handling(self, mock_remove):
        """파일 삭제 예외 처리 테스트"""
        mock_remove.side_effect = PermissionError("Permission denied")
        
        # 예외가 발생해도 함수가 정상 종료되어야 함
        cleanup_temp_files("/some/path")


class TestCleanupTempDirectory:
    """cleanup_temp_directory 함수 테스트"""
    
    def test_cleanup_temp_directory_existing_directory(self):
        """기존 디렉토리 삭제 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 디렉토리 내에 파일 생성
            test_file = os.path.join(temp_dir, "test.txt")
            with open(test_file, "w") as f:
                f.write("test content")
            
            # 디렉토리가 존재하는지 확인
            assert os.path.exists(temp_dir)
            
            # 디렉토리 삭제
            cleanup_temp_directory(temp_dir)
            
            # 디렉토리가 삭제되었는지 확인
            assert not os.path.exists(temp_dir)
    
    def test_cleanup_temp_directory_nonexistent_directory(self):
        """존재하지 않는 디렉토리 삭제 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            nonexistent_dir = os.path.join(temp_dir, "nonexistent")
            
            # 디렉토리가 존재하지 않는지 확인
            assert not os.path.exists(nonexistent_dir)
            
            # 삭제 시도 (오류 없이 실행되어야 함)
            cleanup_temp_directory(nonexistent_dir)
    
    @patch('server.utils.file_utils.shutil.rmtree')
    def test_cleanup_temp_directory_exception_handling(self, mock_rmtree):
        """디렉토리 삭제 예외 처리 테스트"""
        mock_rmtree.side_effect = PermissionError("Permission denied")
        
        # 예외가 발생해도 함수가 정상 종료되어야 함
        cleanup_temp_directory("/some/path")


class TestLoadJson:
    """load_json 함수 테스트"""
    
    def test_load_json_basic(self):
        """기본 JSON 파일 로드 테스트"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            test_data = {"key": "value", "number": 123, "list": [1, 2, 3]}
            json.dump(test_data, temp_file, ensure_ascii=False, indent=2)
            temp_path = temp_file.name
        
        try:
            result = load_json(temp_path)
            assert result == test_data
        finally:
            os.unlink(temp_path)
    
    def test_load_json_with_path_object(self):
        """Path 객체 JSON 파일 로드 테스트"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            test_data = {"path": "object", "test": True}
            json.dump(test_data, temp_file, ensure_ascii=False, indent=2)
            temp_path = Path(temp_file.name)
        
        try:
            result = load_json(temp_path)
            assert result == test_data
        finally:
            os.unlink(temp_path)
    
    def test_load_json_empty_object(self):
        """빈 JSON 객체 로드 테스트"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump({}, temp_file, ensure_ascii=False, indent=2)
            temp_path = temp_file.name
        
        try:
            result = load_json(temp_path)
            assert result == {}
        finally:
            os.unlink(temp_path)
    
    def test_load_json_unicode_content(self):
        """유니코드 JSON 로드 테스트"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
            test_data = {"한글": "테스트", "emoji": "🚀", "special": "특수문자!@#$%"}
            json.dump(test_data, temp_file, ensure_ascii=False, indent=2)
            temp_path = temp_file.name
        
        try:
            result = load_json(temp_path)
            assert result == test_data
        finally:
            os.unlink(temp_path)


class TestSaveJson:
    """save_json 함수 테스트"""
    
    def test_save_json_basic(self):
        """기본 JSON 파일 저장 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data = {"key": "value", "number": 123, "list": [1, 2, 3]}
            file_path = os.path.join(temp_dir, "test.json")
            
            save_json(test_data, file_path)
            
            # 파일이 생성되었는지 확인
            assert os.path.exists(file_path)
            
            # 파일 내용 확인
            with open(file_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            assert loaded_data == test_data
    
    def test_save_json_with_path_object(self):
        """Path 객체 JSON 파일 저장 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data = {"path": "object", "test": True}
            file_path = Path(temp_dir) / "test.json"
            
            save_json(test_data, file_path)
            
            assert file_path.exists()
            
            with open(file_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            assert loaded_data == test_data
    
    def test_save_json_nested_directories(self):
        """중첩된 디렉토리에 JSON 파일 저장 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data = {"nested": "directory", "test": True}
            file_path = os.path.join(temp_dir, "level1", "level2", "test.json")
            
            save_json(test_data, file_path)
            
            # 중첩된 디렉토리가 생성되었는지 확인
            assert os.path.exists(file_path)
            assert os.path.exists(os.path.dirname(file_path))
    
    def test_save_json_unicode_content(self):
        """유니코드 내용이 포함된 JSON 저장 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data = {"한글": "테스트", "emoji": "🚀", "special": "특수문자!@#$%"}
            file_path = os.path.join(temp_dir, "unicode.json")
            
            save_json(test_data, file_path)
            
            assert os.path.exists(file_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            assert loaded_data == test_data
    
    def test_save_json_empty_data(self):
        """빈 데이터 JSON 저장 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data = {}
            file_path = os.path.join(temp_dir, "empty.json")
            
            save_json(test_data, file_path)
            
            assert os.path.exists(file_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            assert loaded_data == test_data


class TestFileUtilsIntegration:
    """통합 테스트 - 여러 함수를 함께 사용하는 경우"""
    
    def test_save_and_load_json_workflow(self):
        """JSON 저장 및 로드 워크플로우 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data = {"workflow": "test", "steps": ["save", "load"], "success": True}
            file_path = os.path.join(temp_dir, "workflow.json")
            
            # JSON 저장
            save_json(test_data, file_path)
            
            # JSON 로드
            loaded_data = load_json(file_path)
            
            assert loaded_data == test_data
    
    def test_directory_creation_and_cleanup_workflow(self):
        """디렉토리 생성 및 정리 워크플로우 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 중첩된 디렉토리 생성
            nested_dir = os.path.join(temp_dir, "level1", "level2", "level3")
            ensure_directory_exists(nested_dir)
            
            # 파일 생성
            test_file = os.path.join(nested_dir, "test.txt")
            with open(test_file, "w") as f:
                f.write("test content")
            
            # 디렉토리와 파일이 존재하는지 확인
            assert os.path.exists(nested_dir)
            assert os.path.exists(test_file)
            
            # 디렉토리 정리
            cleanup_temp_directory(nested_dir)
            
            # 디렉토리가 삭제되었는지 확인
            assert not os.path.exists(nested_dir)


# PITEST를 위한 추가 테스트 케이스들
class TestFileUtilsMutationTargets:
    """PITEST mutation testing을 위한 특별한 테스트 케이스들"""
    
    def test_os_makedirs_exist_ok_mutations(self):
        """os.makedirs의 exist_ok 파라미터 변경에 대한 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # exist_ok=True로 디렉토리 생성
            new_dir = os.path.join(temp_dir, "test_dir")
            ensure_directory_exists(new_dir)
            assert os.path.exists(new_dir)
            
            # 같은 디렉토리를 다시 생성 (exist_ok=True이므로 오류 없음)
            ensure_directory_exists(new_dir)
            assert os.path.exists(new_dir)
    
    def test_path_object_conversion_mutations(self):
        """Path 객체 변환에 대한 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # str을 Path로 변환
            str_path = os.path.join(temp_dir, "str_path.json")
            path_obj = Path(str_path)
            
            test_data = {"path": "conversion", "test": True}
            save_json(test_data, str_path)
            
            # Path 객체로 로드
            loaded_data = load_json(path_obj)
            assert loaded_data == test_data
    
    def test_json_dump_parameters_mutations(self):
        """json.dump 파라미터 변경에 대한 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data = {"한글": "테스트", "special": "chars!@#$%"}
            file_path = os.path.join(temp_dir, "test.json")
            
            save_json(test_data, file_path)
            
            # ensure_ascii=False, indent=2 파라미터로 저장되었는지 확인
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "한글" in content  # ensure_ascii=False
                assert "  " in content    # indent=2
