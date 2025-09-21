# server/routers/response.py

"""
공통 응답 모델
"""

from pydantic import BaseModel
from typing import Any

class BaseResponse(BaseModel):
    success: bool = True          # True | False
    message: str = ""             # 항상 포함되도록 기본값 설정
    result: Any = None            # 항상 포함되도록 기본 None (또는 {})
