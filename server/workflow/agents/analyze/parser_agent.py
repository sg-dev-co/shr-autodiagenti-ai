# server/workflow/agents/analyze/parser_agent.py

"""
파서 에이전트
"""

import os
import subprocess
from datetime import datetime
from server.workflow.agents.base.base_utility_agent import BaseUtilityAgent, AgentState
from server.db.dao.entry_point_list_dao import insert_entry_points_bulk, delete_entry_points_by_project_and_date
from server.db.schema import EntryPointCreate
from server.db.database import run_with_db_session
from server.utils.constants import AgentType, AgentResultGroupKey, IndexInputType, DirInfo
from server.utils.file_utils import load_json
from server.utils.config import settings

class ParserAgent(BaseUtilityAgent):
    def __init__(self, session_id: str = None, project_id: str = None):
        super().__init__(role=AgentType.PARSER, session_id=session_id, project_id=project_id)
        
    def _run_internal(self, state: AgentState) -> AgentState:
        agent_state = state["autodiagenti_state"]
        project_id = agent_state.get("project_id", "")
        project_name = agent_state.get("project_name", "")
        project_path = agent_state.get("project_path", "")
        analyzed_date = agent_state.get("analyzed_date", datetime.now().strftime("%Y%m%d"))
        analyzed_at = agent_state.get("analyzed_at", datetime.now())
        self.logger.info(f"📢 session_id: [{self.session_id}],  project_id: [{project_id}]")
        
        file_info = agent_state.get("file_info", {})
        self.logger.info(f"📢📢 file_info: [{file_info}]")
        file_full_path = os.path.join(file_info.get("file_path", ""), file_info.get("file_name", ""))

        # 분석 설정        
        filter_options = agent_state.get("filter_options", {})
        include_method_text = filter_options.get("include_method_text", True)
        custom_annotations = filter_options.get("custom_annotations", None)
        exclude_packages = filter_options.get("exclude_packages", None)
        
        output_dir = os.path.join(DirInfo.PARSER_OUTPUT_DIR, project_id)
        
        # Parser 호출
        result: bool = self._run_parser_jar(source_dir=project_path, output_dir=output_dir, include_method_text=include_method_text, exclude_packages=exclude_packages, custom_annotations=custom_annotations)
        
        # Entry Point 저장
        if result:
            self._save_entry_point_to_db(project_id=project_id, project_name=project_name, session_id=self.session_id, analyzed_date=analyzed_date, analyzed_at=analyzed_at, file_path=file_full_path)
        
        parser_result = {
            "input_type": IndexInputType.PARSER,
            "output_dir": os.path.join(DirInfo.PARSER_OUTPUT_DIR, project_id, project_name),
            "success": result
        }
        
        result = {
            AgentResultGroupKey.PARSER_RESULT: parser_result,
            AgentResultGroupKey.CURRENT_SOURCE_DATA: parser_result
        }
        
        return self.wrap_multiple_sources(result)
    
    def _run_parser_jar(self,
        source_dir: str,
        output_dir: str,
        include_method_text: bool = True,
        exclude_packages: str = "", # ""java.,jakarta.,org.springframework.",
        custom_annotations: str = '',
        timeout: int = 60
    ) -> bool:
        """
        JavaParser 분석기를 subprocess로 실행하여 call tree 및 메서드 정보를 추출한다.

        Args:
            source_dir (str): 분석 대상 Java 소스 루트 경로
            include_method_text (bool): 메서드 본문 포함 여부
            exclude_packages (str): 제외할 패키지 접두어 (쉼표 구분)
            custom_annotations (str): 엔트리 포인트 구분용 사용자 정의 어노테이션 (쉼표 구분)
            timeout (int): 프로세스 타임아웃 (초)
        Returns:
            bool: 성공 여부 (True: 성공, False: 실패)
        """
        jar_path:str = settings.JAVA_PARSER_JAR_PATH
        output_dir:str = output_dir
        
        if not os.path.isfile(jar_path):
            self.logger.error(f"❌ JAR 파일이 존재하지 않습니다: {jar_path}")
            return False

        if not os.path.isdir(source_dir):
            self.logger.error(f"❌ 소스 디렉토리가 존재하지 않습니다: {source_dir}")
            return False

        os.makedirs(output_dir, exist_ok=True)

        command = [
            "java", 
            "-Dfile.encoding=UTF-8",
            "-jar", 
            jar_path,
            f"--source-dir={source_dir}",
            f"--output-dir={output_dir}",
            f"--include-method-text={str(include_method_text).lower()}"
        ]

        if exclude_packages:
            command.append(f"--exclude-packages={exclude_packages}")
        if custom_annotations:
            command.append(f"--custom-annotations={custom_annotations}")
            
        self.logger.info(f"📢📢📢 command: [{command}]")

        try:
            env = os.environ.copy()
            env["LANG"] = "ko_KR.UTF-8"
            env["LC_ALL"] = "ko_KR.UTF-8"

            self.logger.info(f"🚀 JavaParser 실행 중... \n{' '.join(command)}")
            self._run_with_live_log(command, timeout=timeout, env=env)
            self.logger.info("✅ JavaParser 실행 완료")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"❌ JavaParser 실행 실패 (exit code {e.returncode}): {e}")
        except subprocess.TimeoutExpired:
            self.logger.error("⏰ JavaParser 실행 시간 초과")
        except Exception as e:
            self.logger.exception(f"⚠️ 예기치 못한 오류 발생: {e}")

        return False
    
    def _run_with_live_log(self, command, timeout=None, env=None):
        proc = None
        
        try:
            proc = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                bufsize=1,
                env=env
            )

            for line in proc.stdout:
                print(line, end="")   # 실시간 로그 출력

            proc.wait(timeout=timeout)

            if proc.returncode != 0:
                raise subprocess.CalledProcessError(proc.returncode, command)

        except subprocess.TimeoutExpired:
            proc.kill()
            self.logger.error(f"\n[ERROR] Timeout after {timeout} seconds")
            raise
        
    def _save_entry_point_to_db(self, project_id: str, project_name: str, session_id: str, analyzed_date: str, analyzed_at: str, file_path: str):
        try:
            # Entry Point 파일 로드
            output_dir = os.path.join(DirInfo.PARSER_OUTPUT_DIR, project_id, project_name)
            entry_point_info_path = os.path.join(output_dir, settings.ENTRY_POINT_INFO_FILE_NAME)
            entry_point_info_list = load_json(entry_point_info_path)
        
            data = []
            for entry_point_info in entry_point_info_list:
                method_fqn = entry_point_info.get("method_fqn")
                
                if method_fqn:
                    entry_point = EntryPointCreate(
                        analyzed_date=analyzed_date,
                        project_id=project_id,
                        entry_point=method_fqn,
                        session_id=session_id,
                        api_name=entry_point_info.get("api_name"),
                        api_method=entry_point_info.get("api_method"),
                        annotation=entry_point_info.get("annotation"),
                        file_path=file_path,
                        analyzed_at=analyzed_at
                    )
                    data.append(entry_point)
            
            self.logger.info(f"🖥️ data: {len(data)}")
            
            if data:
                del_count = run_with_db_session(delete_entry_points_by_project_and_date, project_id=project_id, analyzed_date=analyzed_date)
                self.logger.info(f"📢 Entry Point 삭제 건수: [{del_count}], project_id: {project_id}, analyzed_date: {analyzed_date}")
                result = run_with_db_session(insert_entry_points_bulk, data)
                self.logger.info(f"📢 Entry Point 등록 완료. project_id:{project_id}, analyzed_date: {analyzed_date}, result:{result}")
            else:
                self.logger.info(f"📢 Entry Point 등록 대상 데이터가 없음. project_id:{project_id}")
        except Exception as err:
            self.logger.error(f"❌ Entry Point 등록 오류 err:{err}, cause: {err.__cause__}")
    
