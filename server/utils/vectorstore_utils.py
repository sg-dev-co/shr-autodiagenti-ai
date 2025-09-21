# server/utils/vectorstore_utils.py

"""
벡터스토어 관리 유틸리티 모듈
"""

import os
import shutil
from typing import List, Optional
from langchain.schema import Document
from langchain.vectorstores import FAISS
from langchain_core.vectorstores import VectorStore
from langchain_openai import AzureOpenAIEmbeddings
from server.utils.config import settings, get_embeddings
from server.utils.logger import get_logger

# 로거 선언
logger = get_logger(__name__)

FAISS_FILENAME_TEMPLATE = "q_{project_id}_faiss_index"

def load_faiss_vector_store(project_id: str, embeddings: Optional[AzureOpenAIEmbeddings] = None, path: Optional[str] = None) -> Optional[VectorStore]:
    """FAISS 벡터 스토어를 로드

    Args:
        project_id (str): 클라이언트로부터 전달받은 project_id
        embeddings (AzureOpenAIEmbeddings): 임베딩 모델

    Returns:
        VectorStore: FAISS 벡터 스토어 객체
    """
    try:
        if not path:
            faiss_index_path = get_vectorstore_path(project_id=project_id)
        else:
            faiss_index_path = path
        
        if not embeddings:
            # 임베딩 모델 생성
            embeddings = get_embeddings()
        
        logger.debug(f"📢 FIASS_INDEX_PATH: {faiss_index_path}")
        vectorstore = FAISS.load_local(faiss_index_path, embeddings, allow_dangerous_deserialization=True)  # pickle 로딩 허용
        return vectorstore
    except Exception as err:
        logger.warning(f"🌧️ 벡터스토어 로드 오류. error: {err}")
        return None

def save_documents_to_faiss_vector_store(project_id:str, documents: List[Document]) -> Optional[VectorStore]:
    """FAISS 벡터 스토어 생성하고 문서를 저장

    Args:
        project_id (str): 클라이언트로부터 전달받은 project_id
        documents (List[Document]): 저장 대상 문서

    Returns:
        Optional[VectorStore]: FAISS 벡터 스토어 객체
    """
    
    if not documents:
        logger.warning(f"🌧️ documents is empty.")
        return None
    
    try:
        # FAISS 저장 경로 조회
        faiss_index_path = get_vectorstore_path(project_id=project_id)
        
        # 임베딩 모델 생성
        embeddings: AzureOpenAIEmbeddings = get_embeddings()
        
        # 벡터 저장소 로드
        vectorstore = load_faiss_vector_store(project_id=project_id, embeddings=embeddings, path=faiss_index_path)
        
        if vectorstore:
            vectorstore.add_documents(documents=documents)
        else:
            # 벡터 변환 및 FAISS 벡터 저장소 생성
            vectorstore = FAISS.from_documents(documents=documents, embedding=embeddings, normalize_L2=True)
        
            # FAISS 저장 디렉토리 확인
            os.makedirs(faiss_index_path, exist_ok=True)
        
        # 벡터 저장(local)
        vectorstore.save_local(faiss_index_path)
        logger.debug(f"\n✅ FAISS 벡터 저장소 생성 완료! ({faiss_index_path})")
        
        return vectorstore
            
    except Exception as err:
        logger.error(f"🌧️ 벡터스토어 저장 오류. error: {err}")
        return None
    
def get_vectorstore_path(project_id: str) -> str:
    """FAISS 벡터 스토어 경로를 조회

    Args:
        project_id (str): 클라이언트로부터 전달받은 project_id

    Returns:
        str: FIASS 벡터 스토어 경로
    """
    return os.path.join(settings.FIASS_INDEX_PATH, FAISS_FILENAME_TEMPLATE.format(project_id=project_id))

def delete_faiss_index_by_project(project_id: str) -> bool:
    faiss_index_path = get_vectorstore_path(project_id=project_id)
    if os.path.exists(faiss_index_path):
        shutil.rmtree(faiss_index_path)
        logger.info(f"🧹 FAISS index for project {project_id} deleted: {faiss_index_path}")
        return True
    else:
        logger.warning(f"❗ FAISS path not found: {faiss_index_path}")
        return False
