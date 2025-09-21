# server/utils/constants.py

"""
상수 관리 모듈
"""

from enum import Enum

class AgentType:
    SUSPERVISOR = "SUPERVISOR"
    UPLOADER = "UPLOADER"
    RAG_INDEXER = "RAG_INDEXER_AGENT"
    PARSER = "PARSER_AGENT"
    RECURSIVE_CALL_TREE = "RECURSIVE_CALL_TREE_AGENT"
    CALL_TREE_SUMMARIZER = "CALL_TREE_SUMMARIZER_AGENT"
    CODE_ANALYSIS = "CODE_ANALYSIS_AGENT"
    SEQUENCE_DIAGRAM = "SEQUENCE_DIAGRAM_AGENT"
    
class AgentRunType:
    START = "START"
    END = "END"

class IndexInputType:
    PARSER = "PARSER"                           
    LLM_CODE = "LLM_CODE"                       
    CALLTREE = "CALLTREE"                       
    CALLTREE_SUMMARY = "CALLTREE_SUMMARY"       
    SEQUENCE_DIAGRAM = "SEQUENCE_DIAGRAM"       

class RagSourceType:
    PARSER = "PARSER"
    CODE = "CODE"
    COMMENTS = "COMMENTS"
    CALLTREE = "CALLTREE"
    CALLTREE_SUMMARY = "CALLTREE_SUMMARY"
    CODE_ANALYSIS = "CODE_ANALYSIS"
    SEQUENCE_DIAGRAM = "SEQUENCE_DIAGRAM"
    
    
class AgentResultGroupKey:
    CURRENT_SOURCE_DATA = "current_source_data"
    RAG_INDEXING_RESULT = "rag_indexing_result"
    PARSER_RESULT = "parser_result"
    RECURSIVE_CALL_TREE_RESULT = "recursive_call_tree_result"
    CALL_TREE_SUMMARY = "call_tree_summary"
    CODE_ANALYSIS_RESULT = "code_analysis_result"
    SEQUENCE_DIAGRAM_RESULT = "sequence_diagram_result"
    
class DirInfo:
    UPLOAD_DIR = "server/storage/uploads"
    UNPACK_DIR = "server/storage/tmp/unpacked"
    PARSER_OUTPUT_DIR = "server/storage/tmp/analyzer-output"
    

class LLMModel(Enum):
    AZURE_GPT_4O = ("gpt-4o", "2024-10-21", "azure")
    AZURE_GPT_4O_MINI = ("gpt-4o-mini", "2024-10-21", "azure")
    
    def __init__(self, model_name, version, provider):
        self.model_name = model_name
        self.version = version
        self.provider = provider
        
    @classmethod
    def get_by_name(cls, model_name):
        """모델명으로 모델을 찾는 함수"""
        return next((member for member in cls if member.model_name == model_name), None)
