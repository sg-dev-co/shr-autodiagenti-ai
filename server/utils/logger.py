# server/utils/logger.py

"""
로거 관리 유틸리티 모듈
"""

import logging
from datetime import datetime
from pathlib import Path

def get_logger(name: str) -> logging.Logger:
    """
    로거 인스턴스를 생성하고 반환
    
    Args:
        name: 로거 이름 (보통 __name__ 사용)
        
    Returns:
        설정된 로거 인스턴스
    """
    logger = logging.getLogger(name)
    
    # 이미 핸들러가 설정되어 있다면 중복 설정 방지
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # 로그 포맷 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러
    log_dir = Path("server/logs")
    log_dir.mkdir(exist_ok=True)
    
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"autodiagenti_server_{today}.log"
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger