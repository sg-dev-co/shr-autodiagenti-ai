# server/utils/document_retrieval_utils.py

"""
문서 검색 관리 유틸리티 모듈
"""


from typing import Optional, List
from langchain.schema import Document
from langchain.vectorstores.faiss import FAISS
from server.utils.logger import get_logger
from server.utils.vectorstore_utils import load_faiss_vector_store
from server.utils.constants import RagSourceType

# 로거 선언
logger = get_logger(__name__)

def load_call_tree_doc(project_id: str, entry_point: str) -> Optional[Document]:
    """
    지정된 project_id 및 entry_point에 해당하는 CALLTREE 문서를 조회

    Args:
        project_id (str): 분석 대상 project_id
        entry_point (str): entry point 메서드의 FQN

    Returns:
        Optional[Document]: 해당 문서가 존재하면 반환, 없으면 None
    """
    return load_document_by_source_type_and_entry_point(project_id, RagSourceType.CALLTREE, entry_point)


def load_call_tree_summary_doc(project_id: str, entry_point: str) -> Optional[Document]:
    """
    지정된 project_id 및 entry_point에 해당하는 CALLTREE_SUMMARY 문서를 조회

    Args:
        project_id (str): 분석 대상 project_id
        entry_point (str): entry point 메서드의 FQN

    Returns:
        Optional[Document]: 해당 문서가 존재하면 반환, 없으면 None
    """
    return load_document_by_source_type_and_entry_point(project_id, RagSourceType.CALLTREE_SUMMARY, entry_point)


def load_sequence_diagram_doc(project_id: str, entry_point: str) -> Optional[Document]:
    """
    지정된 project_id 및 entry_point에 해당하는 SEQUENCE_DIAGRAM 문서를 조회

    Args:
        project_id (str): 분석 대상 project_id
        entry_point (str): entry point 메서드의 FQN

    Returns:
        Optional[Document]: 해당 문서가 존재하면 반환, 없으면 None
    """
    return load_document_by_source_type_and_entry_point(project_id, RagSourceType.SEQUENCE_DIAGRAM, entry_point)


def load_document_by_source_type_and_entry_point(project_id: str, source_type: RagSourceType, entry_point: str) -> Optional[Document]:
    """
    source_type과 entry_point 조건에 맞는 문서를 벡터스토어에서 단건 조회

    Args:
        project_id (str): 쿼리 ID (예: 프로젝트 ID)
        source_type (RagSourceType): 문서의 소스 타입 (예: CALLTREE, CODE_ANALYSIS 등)
        entry_point (str): 메서드 FQN (예: com.example.MyController.login)

    Returns:
        Optional[Document]: 조건에 부합하는 문서 1건 또는 None
    """
    vectorstore = load_faiss_vector_store(project_id)
    
    if vectorstore is None:
        return None
    
    if not isinstance(vectorstore, FAISS):
        raise TypeError("Loaded vectorstore is not a FAISS instance")

    all_docs: List[Document] = vectorstore.docstore._dict.values()
    
    for doc in all_docs:
        if (
            doc.metadata.get("source_type") == source_type and
            doc.metadata.get("entry_point") == entry_point
        ):
            return doc

    return None

def load_documents_by_source_type(project_id: str, source_type: str) -> List[Document]:
    """
    지정된 project_id source_type 조건에 맞는 문서들을 모두 조회

    Args:
        project_id (str): 쿼리 ID (예: 프로젝트 ID)
        source_type (str): 문서의 소스 타입 (예: CALLTREE, CODE_ANALYSIS 등)

    Returns:
        List[Document]: 해당 조건에 부합하는 문서 리스트
    """
    vectorstore = load_faiss_vector_store(project_id)
    if vectorstore is None:
        return []
    
    if not isinstance(vectorstore, FAISS):
        raise TypeError("Loaded vectorstore is not a FAISS instance")

    # 벡터스토어에서 전체 문서 검색
    all_documents: List[Document] = vectorstore.docstore._dict.values()
    
    filtered_documents = [
        doc for doc in all_documents
        if doc.metadata.get("source_type") == source_type
    ]
    return filtered_documents

