# server/workflow/agents/analyze/recursive_call_tree_agent.py

"""
재귀적 호출 트리 분석 에이전트
"""
import os
from datetime import datetime
from typing import List, Any, Dict, Set
from langchain.schema import Document
from server.workflow.agents.base.base_utility_agent import BaseUtilityAgent, AgentState
from server.utils.constants import AgentType, IndexInputType, RagSourceType, DirInfo, AgentResultGroupKey
from server.utils.document_retrieval_utils import load_documents_by_source_type
from server.utils.config import settings
from server.utils.file_utils import load_json

class RecursiveCallTreeAgent(BaseUtilityAgent):
    def __init__(self, session_id: str = None, project_id: str = None):
        super().__init__(role=AgentType.RECURSIVE_CALL_TREE, session_id=session_id, project_id=project_id)
        
    def _run_internal(self, state: AgentState) -> AgentState:
        project_id = state["autodiagenti_state"].get("project_id", "")
        project_name = state["autodiagenti_state"].get("project_name", "")
        max_depth = state["autodiagenti_state"].get("max_depth", -1)
        
        # 1. PARSER 문서 전체 조회 (project_id 기준)
        parser_documents = load_documents_by_source_type(project_id=project_id, source_type=RagSourceType.PARSER)
        
        # 2. EntryPoint 기준 반복 처리
        output_dir = os.path.join(DirInfo.PARSER_OUTPUT_DIR, project_id, project_name)
        entry_point_path = os.path.join(output_dir, settings.ENTRY_POINT_FILE_NAME)
        entry_point_list = load_json(entry_point_path)
        
        # 3.메서드 FQN 목록 추출
        method_fqn_path = os.path.join(output_dir, settings.ALL_METHODS_FILE_NAME)
        valid_method_fqns: set[str] = set(load_json(method_fqn_path))
        
        call_tree_list = []
        for entry_point in entry_point_list:
            # 4.Call Tree 구조 분석
            call_tree = self._prepare_recursive_calltree_input(
                entry_point=entry_point,
                parser_documents=parser_documents,
                valid_method_fqns=valid_method_fqns,
                depth_limit=max_depth
            )
            call_tree_list.append(call_tree)
        
        # 결과값 생성
        call_tree_result = {
            "input_type": IndexInputType.CALLTREE,
            "call_tree_info": call_tree_list
        }
        
        result = {
            AgentResultGroupKey.CURRENT_SOURCE_DATA: call_tree_result,
            AgentResultGroupKey.RECURSIVE_CALL_TREE_RESULT: call_tree_result
        }
        
        return self.wrap_multiple_sources(result)
        
    def _prepare_recursive_calltree_input(self, entry_point: str, parser_documents: List[Document], valid_method_fqns: set[str], depth_limit: int = 3) -> Dict[str, Any]:
        """
        entry_point를 시작점으로 callEdges 정보를 분석해서 하나의 calltree 데이터를 만드는 함수
        
        Args:
            entry_point (str): 분석 대상 메서드 (진입점)
            parser_documents (List[Document]): Parser 문서 리스트
            depth_limit (int): 최대 호출 깊이 제한 (기본값: 3)
            
        Returns:
            Dict[str, Any]: 재귀적 호출 트리 데이터
        """
        
        # 1. parser_documents에서 모든 callEdges, methodMetaMap 수집 (merge)
        all_call_edges = []
        all_method_meta_map = {}
        project_info = {}
        
        for doc in parser_documents:
            meta = doc.metadata
            
            # callEdges 수집
            call_edges = meta.get("call_edges", [])
            all_call_edges.extend(call_edges)
            
            # methodMetaMap 수집
            method_meta_map = meta.get("method_meta_map", {})
            all_method_meta_map.update(method_meta_map)
            
            # 프로젝트 정보 수집 (첫 번째 문서 기준)
            if not project_info:
                project_info = {
                    "project_name": meta.get("project_name", "UnknownProject"),
                    "file_path": meta.get("file_path", ""),
                    "analyzed_at": datetime.now().isoformat()
                }
                
        caller_set = set(edge['caller'] for edge in all_call_edges)
            
        # 2. entry_point 기준으로 DFS → call_tree 생성
        call_tree = self._build_call_tree_recursive(
            method_name=entry_point, 
            valid_method_fqns=valid_method_fqns,
            call_edges=all_call_edges, 
            caller_set=caller_set,
            method_meta_map=all_method_meta_map, 
            depth_limit=depth_limit, 
            visited=set()
        )
        
        # 3. call_sequence = pre-order 순회 결과
        call_sequence = self._get_preorder_sequence(call_tree=call_tree, valid_method_fqns=valid_method_fqns, method_meta_map=all_method_meta_map, caller_set=caller_set)
        
        # 4. depth 계산
        depth = self._calculate_max_depth(call_tree)
        
        # 5. 포함된 메서드들의 summary/comment mapping
        method_summary_map, method_comment_map = self._build_method_maps(call_sequence, all_method_meta_map)
        
        # 6. 최종 결과 구성
        result = {
            "entry_point": entry_point,
            "call_tree": call_tree,
            "call_sequence": call_sequence,
            "depth": depth,
            "method_summary_map": method_summary_map,
            "method_comment_map": method_comment_map,
            "project_name": project_info.get("project_name", ""),
            "file_path": project_info.get("file_path", ""),
            "analyzed_at": project_info.get("analyzed_at", "")
        }
        
        return result
    
    def _build_call_tree_recursive(
        self,
        method_name: str, 
        valid_method_fqns: set[str],
        call_edges: List[Dict], 
        caller_set: Set,
        method_meta_map: Dict,
        depth_limit: int,
        visited: set,
        current_depth: int = 1
    ) -> Dict[str, Any]:
        """
        재귀적으로 호출 트리를 구성하는 헬퍼 함수
        
        Args:
            method_name (str): 현재 메서드명
            call_edges (List[Dict]): 모든 호출 엣지 정보
            method_meta_map (Dict): 메서드 메타 정보 맵
            depth_limit (int): 최대 깊이 제한
            visited (set): 방문한 메서드 집합 (순환 참조 방지)
            current_depth (int): 현재 깊이
            
        Returns:
            Dict[str, Any]: 호출 트리 노드
        """
        # 깊이 제한 체크
        if depth_limit != -1 and current_depth >= depth_limit:
            return {
                "method_fqn": method_name,
                "calls": []
            }
        
        # 순환 참조 방지
        if method_name in visited:
            return {
                "method_fqn": method_name,
                "calls": []
            }
        
        # 현재 메서드를 방문한 것으로 표시
        visited.add(method_name)
        
        # 현재 메서드의 호출 대상들 찾기
        calls = []
        for edge in call_edges:
            if edge.get("caller") == method_name:
                callee = edge.get("callee")
                
                # 유효하지 않은 callee면 무시
                if callee not in valid_method_fqns:
                    self.logger.info(f"📢 invalid callee: [{callee}]")
                    continue
                
                if callee not in caller_set:
                    # getter/setter 메서드는 제외
                    callee_meta = method_meta_map.get(callee, {})
                    if is_getter_setter(callee, callee_meta):
                        self.logger.info(f"📢 getter/setter 제외: [{callee}]")
                        continue
                
                if callee:
                    # 재귀적으로 하위 호출 트리 구성
                    sub_tree = self._build_call_tree_recursive(
                        method_name=callee, 
                        valid_method_fqns=valid_method_fqns,
                        call_edges=call_edges,
                        caller_set=caller_set,
                        method_meta_map=method_meta_map, 
                        depth_limit=depth_limit, 
                        visited=visited.copy(), 
                        current_depth=current_depth + 1
                    )
                    calls.append(sub_tree)
        
        return {
            "method_fqn": method_name,
            "calls": calls
        }


    def _get_preorder_sequence(self, call_tree: Dict[str, Any], valid_method_fqns: set[str], method_meta_map: Dict[str, Any], caller_set: Set) -> List[str]:
        """
        호출 트리를 pre-order로 순회하여 메서드 시퀀스를 반환
        
        Args:
            call_tree (Dict[str, Any]): 호출 트리
            valid_method_fqns (Set[str]): 유효한 메서드 FQN 목록
            all_method_meta_map (Dict[str, Any]): 모든 메서드 메타 정보
            
        Returns:
            List[str]: pre-order 메서드 시퀀스
        """
        sequence = []
        
        def _preorder_traverse(node: Dict[str, Any]):
            method_fqn = node["method_fqn"]
            method_meta = method_meta_map.get(method_fqn, {})

            # 유효한 메서드가 아니거나 getter/setter이면 SKIP
            if method_fqn not in valid_method_fqns:
                self.logger.warning(f"🌧️ method_fqn is not valid. method_fqn: [{method_fqn}]")
                return
            
            # getter/setter 메서드 체크
            if method_fqn not in caller_set:
                if is_getter_setter(method_fqn, method_meta):
                    self.logger.warning(f"🌧️ method_fqn is getter/setter.")
                    return
            
            sequence.append(node["method_fqn"])
            
            for call in node.get("calls", []):
                _preorder_traverse(call)
        
        _preorder_traverse(call_tree)
        return sequence


    def _calculate_max_depth(self, call_tree: Dict[str, Any]) -> int:
        """
        호출 트리의 최대 깊이를 계산
        
        Args:
            call_tree (Dict[str, Any]): 호출 트리
            
        Returns:
            int: 최대 깊이
        """
        def _get_depth(node: Dict[str, Any]) -> int:
            if not node.get("calls"):
                return 1
            
            max_child_depth = 0
            for call in node["calls"]:
                child_depth = _get_depth(call)
                max_child_depth = max(max_child_depth, child_depth)
            
            return 1 + max_child_depth
        
        return _get_depth(call_tree)


    def _build_method_maps(self, call_sequence: List[str], method_meta_map: Dict) -> tuple[Dict[str, Dict[str, Any]], Dict[str, str]]:
        """
        메서드 시퀀스에 포함된 메서드들의 요약 정보와 주석 정보를 하나의 루프로 구성
        
        Args:
            call_sequence (List[str]): 메서드 시퀀스
            method_meta_map (Dict): 메서드 메타 정보 맵
            
        Returns:
            tuple: (methodSummaryMap, methodCommentMap)
        """
        summary_map = {}
        comment_map = {}
        
        for method_name in call_sequence:
            if method_name in method_meta_map:
                meta = method_meta_map[method_name]
                
                # parameters 정보 구성
                parameters = []
                if "parameters" in meta:
                    parameters = meta["parameters"]
                
                # returns 정보 구성 (return_type 필드 사용)
                return_type = meta.get("return_type", "void")
                
                # summary_map 구성
                if "summary" in meta:
                    summary_map[method_name] = {
                        "summary": meta["summary"],
                        "parameters": parameters,
                        "return_type": return_type
                    }
                
                # comment_map 구성
                method_signature = meta.get("method_signature", "")
                comment = meta.get("comment", "")
                if comment:
                    comment_map[method_name] = comment
                elif method_signature:
                    comment_map[method_name] = f"method: {method_signature}"
                else:
                    comment_map[method_name] = f"method: {method_name}"
        
        return summary_map, comment_map
    
def is_getter_setter(method_fqn: str, meta: dict) -> bool:
    name = method_fqn.split('(')[0].split('.')[-1]  # 메서드명
    params = meta.get("parameters") or []
    ret = (meta.get("return_type") or "").lower()
    
    # Getter: getX* (파라미터 0, 반환 void 아님)
    if name.startswith("get") and len(params) == 0 and ret not in ("void", "java.lang.void", ""):
        return True

    # Boolean Getter: isX* (파라미터 0, 반환 boolean)
    if name.startswith("is") and len(params) == 0 and ret in ("boolean", "java.lang.boolean"):
        return True

    # Setter: setX* (파라미터 1, 반환 void)
    if name.startswith("set") and len(params) == 1 and ret in ("void", "java.lang.void", ""):
        return True
    
    return False

