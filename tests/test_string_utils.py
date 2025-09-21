# tests/test_string_utils.py

"""
string_utils 테스트 코드
"""

from app.utils.string_utils import sanitize_name, format_iso_datetime


class TestSanitizeName:
    """sanitize_name 함수 테스트"""
    
    def test_sanitize_name_basic(self):
        """기본 특수문자 제거 테스트"""
        assert sanitize_name("test:file") == "testfile"
        assert sanitize_name("my project") == "my_project"
        assert sanitize_name("file.name") == "file_name"
    
    def test_sanitize_name_special_chars(self):
        """특수문자 제거 테스트"""
        assert sanitize_name("file<>|") == "file"
        assert sanitize_name("test*?") == "test"
        assert sanitize_name("path\\file") == "pathfile"
        assert sanitize_name("file/name") == "filename"
        assert sanitize_name("file:name") == "filename"
        assert sanitize_name("file\"name") == "filename"
    
    def test_sanitize_name_braces_and_dots(self):
        """중괄호와 점 처리 테스트"""
        assert sanitize_name("test{value}") == "test-value-"
        assert sanitize_name("a.b.c") == "a_b_c"
        assert sanitize_name("file{name}.txt") == "file-name-_txt"
    
    def test_sanitize_name_spaces(self):
        """공백 처리 테스트"""
        assert sanitize_name("my project") == "my_project"
        assert sanitize_name("  spaced  ") == "spaced"
        assert sanitize_name("multi   space") == "multi___space"
    
    def test_sanitize_name_empty_and_whitespace(self):
        """빈 문자열과 공백 테스트"""
        assert sanitize_name("") == ""
        assert sanitize_name("   ") == ""
        assert sanitize_name("\t\n") == ""
    
    def test_sanitize_name_mixed_special_chars(self):
        """혼합 특수문자 테스트"""
        assert sanitize_name("file<>|*?:\\/\"") == "file"
        assert sanitize_name("test{value}.txt") == "test-value-_txt"
        assert sanitize_name("path/to/file.name") == "pathtofile_name"
    
    def test_sanitize_name_unicode(self):
        """유니코드 테스트"""
        assert sanitize_name("한글파일") == "한글파일"
        assert sanitize_name("한글 파일") == "한글_파일"
        assert sanitize_name("한글{파일}") == "한글-파일-"


class TestFormatIsoDatetime:
    """format_iso_datetime 함수 테스트"""
    
    def test_format_iso_datetime_valid(self):
        """유효한 ISO 형식 날짜 테스트"""
        result = format_iso_datetime("2025-09-13T17:07:44.578665")
        assert "2025년 09월 13일 17시 07분" in result
        
        result2 = format_iso_datetime("2024-12-25T00:00:00")
        assert "2024년 12월 25일 00시 00분" in result2
    
    def test_format_iso_datetime_with_z_suffix(self):
        """Z 접미사 ISO 형식 테스트"""
        result = format_iso_datetime("2025-09-13T17:07:44Z")
        assert "2025년 09월 13일 17시 07분" in result
    
    def test_format_iso_datetime_empty_and_none(self):
        """빈 문자열과 None 테스트"""
        assert format_iso_datetime("") == ""
        assert format_iso_datetime(None) == ""
    
    def test_format_iso_datetime_invalid_format(self):
        """잘못된 형식 날짜 테스트"""
        invalid_cases = [
            "invalid-date",
            "2025-13-45T25:70:80",  # 잘못된 날짜/시간
            "not-a-date",
            "2025/09/13",  # 잘못된 구분자
            "2025-09-13",  # 시간 부분 누락
        ]
        
        for invalid_date in invalid_cases:
            # 파싱 실패 시 원본 반환
            assert format_iso_datetime(invalid_date) == invalid_date
    
    def test_format_iso_datetime_edge_cases(self):
        """엣지 케이스 테스트"""
        # 윤년 테스트
        result = format_iso_datetime("2024-02-29T12:00:00")
        assert "2024년 02월 29일 12시 00분" in result
        
        # 자정 테스트
        result = format_iso_datetime("2025-01-01T00:00:00")
        assert "2025년 01월 01일 00시 00분" in result
        
        # 23:59:59 테스트
        result = format_iso_datetime("2025-12-31T23:59:59")
        assert "2025년 12월 31일 23시 59분" in result
    
    def test_format_iso_datetime_microseconds(self):
        """마이크로초 포함 테스트"""
        result = format_iso_datetime("2025-09-13T17:07:44.123456")
        assert "2025년 09월 13일 17시 07분" in result
        
        result2 = format_iso_datetime("2025-09-13T17:07:44.000000")
        assert "2025년 09월 13일 17시 07분" in result2


