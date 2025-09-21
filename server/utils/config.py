# server/utils/config.py

"""
설정 관리 모듈
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

class Settings(BaseSettings):
    # Azure OpenAI 설정
    AOAI_API_KEY: str
    AOAI_ENDPOINT: str
    AOAI_DEPLOY_GPT: str
    AOAI_EMBEDDING_DEPLOYMENT: str
    AOAI_API_VERSION: str

    # SQLite 데이터베이스 설정
    DB_PATH: str = "autodiagenti.db"
    SQLALCHEMY_DATABASE_URI: str = f"sqlite:///./server/storage/db/{DB_PATH}"
    
    # FAISS 경로
    FIASS_INDEX_PATH: str = "server/storage/vectorstore/faiss_db"
    
    ENTRY_POINT_FILE_NAME: str = "entry_point_fqns.json"
    ENTRY_POINT_INFO_FILE_NAME: str = "entry_points.json"
    ALL_METHODS_FILE_NAME: str = "all_methods.json"
    
    # 병렬처리 설정
    MAX_CONCURRENT: int = 20
    LLM_TIMEOUT: int = 30
    
    # parser 설정
    JAR_VERSION: str = "0.4.0"
    JAR_DIR: str = "server/storage/jars"
    JAR_FILENAME: str = f"sg-custom-java-parser-{JAR_VERSION}.jar"
    JAVA_PARSER_JAR_PATH: str = os.path.join(JAR_DIR, JAR_FILENAME)
    
    model_config = SettingsConfigDict(env_file=str(Path(__file__).resolve().parents[1] / ".env"), case_sensitive=True)
    
    def _get_azure_llm(self, azure_llm_model: str, azure_llm_version: str, temperature=0.3, max_tokens=1500):
        return AzureChatOpenAI(
            openai_api_key=self.AOAI_API_KEY,
            azure_endpoint=self.AOAI_ENDPOINT,
            azure_deployment=azure_llm_model,
            api_version=azure_llm_version,
            temperature=temperature,
            streaming=False,
            max_tokens=max_tokens
            
        )
        
    def get_llm_with_custom(self, llm_model: str, llm_version: str, temperature=0.3, max_tokens=1500):
        return self._get_azure_llm(azure_llm_model=llm_model, azure_llm_version=llm_version, temperature=temperature, max_tokens=max_tokens)
        
    def get_llm(self):
        return self._get_azure_llm(azure_llm_model=self.AOAI_DEPLOY_GPT, azure_llm_version=self.AOAI_API_VERSION, temperature=0.3, max_tokens=1500)

    def get_embeddings(self, api_model: str = "", api_version: str = ""):
        embedding_api_model = api_model if api_model else self.AOAI_EMBEDDING_DEPLOYMENT
        embedding_api_version = api_version if api_version else self.AOAI_API_VERSION

        return AzureOpenAIEmbeddings(
            model=embedding_api_model,
            openai_api_version=embedding_api_version,
            api_key=self.AOAI_API_KEY,
            azure_endpoint=self.AOAI_ENDPOINT
        )

# 설정 인스턴스 생성
settings = Settings()

# 편의를 위한 함수들, 하위 호환성을 위해 유지
def get_llm():
    return settings.get_llm()

def get_llm_with_custom(llm_model: str, llm_version: str, temperature=0.3, max_tokens=1500):
    return settings.get_llm_with_custom(llm_model=llm_model, llm_version=llm_version, temperature=temperature, max_tokens=max_tokens)

def get_embeddings():
    return settings.get_embeddings()
