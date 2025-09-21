# app/utils/constants.py

"""
상수 모듈.

상수 정의 및 유틸리티 함수 제공.
"""

from enum import Enum

class LLMModel(Enum):
    AZURE_GPT_4O = ("gpt-4o", "2024-10-21", "azure", "GPT-4o")
    AZURE_GPT_4O_MINI = ("gpt-4o-mini", "2024-10-21", "azure", "GPT-4o Mini")      

    def __init__(self, model_name, version, provider, display_name):
        self.model_name = model_name
        self.version = version
        self.provider =provider
        self.display_name = display_name

    @classmethod
    def get_by_model_name(cls, model_name):
        """모델델명으로 모델을 찾는 함수"""
        return next((member for member in cls if member.model_name == model_name), None)

    @classmethod
    def get_display_name(cls, model_name: str) -> str:
        """model_name으로 display_name을 반환하는 함수"""
        model = cls.get_by_model_name(model_name)
        return model.display_name if model else model_name

    @classmethod
    def get_display_name_to_model_dict(cls):
        """표시명 -> 모델 매핑 딕셔너리를 반환하는 함수"""
        return {member.model_name: member for member in cls}

    