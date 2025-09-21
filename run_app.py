#!/usr/bin/env python3
"""
AutoDiagentiAI 통합 실행 스크립트.

이 스크립트는 개발 및 테스트 목적으로 FastAPI 서버와 Streamlit UI를 동시에 실행합니다.
프로덕션 환경에서는 각각 독립적으로 배포하는 것을 권장합니다.
"""

import subprocess
import sys
import time
import os
from pathlib import Path


def check_and_activate_venv():
    """가상환경이 활성화되어 있는지 확인하고, 필요시 활성화합니다."""
    # 가상환경이 이미 활성화되어 있는지 확인
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ 가상환경이 이미 활성화되어 있습니다.")
        return True
    
    # .venv 디렉토리가 존재하는지 확인
    venv_path = Path(".venv")
    if not venv_path.exists():
        print("❌ .venv 디렉토리를 찾을 수 없습니다.")
        print("다음 명령어로 가상환경을 생성해주세요:")
        print("python -m venv .venv")
        return False
    
    # 가상환경 활성화 시도
    print("🔄 가상환경을 자동으로 활성화합니다...")
    
    if os.name == 'nt':  # Windows
        # Windows에서는 현재 프로세스에서 가상환경의 Python을 직접 사용
        venv_python = venv_path / "Scripts" / "python.exe"
        if venv_python.exists():
            print(f"✅ 가상환경 Python 사용: {venv_python}")
            # 현재 프로세스를 가상환경의 Python으로 재시작
            os.execv(str(venv_python), [str(venv_python)] + sys.argv)
        else:
            print("❌ 가상환경 Python을 찾을 수 없습니다.")
            return False
    else:  # Unix/Linux/Mac
        # Unix 계열에서는 가상환경의 Python을 직접 사용
        venv_python = venv_path / "bin" / "python"
        if venv_python.exists():
            print(f"✅ 가상환경 Python 사용: {venv_python}")
            os.execv(str(venv_python), [str(venv_python)] + sys.argv)
        else:
            print("❌ 가상환경 Python을 찾을 수 없습니다.")
            return False
    
    return True


def check_dependencies():
    """필요한 패키지들이 설치되어 있는지 확인합니다."""
    required_packages = [
        "fastapi",
        "streamlit", 
        "streamlit-mermaid",
        "requests",
        "uvicorn",
        "langchain",
        "langchain-openai",
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 다음 패키지들이 설치되지 않았습니다: {', '.join(missing_packages)}")
        print("다음 명령어로 설치해주세요:")
        print("pip install -r requirements.txt")
        return False
    
    print("✅ 모든 필요한 패키지가 설치되어 있습니다.")
    return True


def start_fastapi_server():
    """FastAPI 서버를 시작합니다."""
    print("🚀 FastAPI 서버를 시작합니다...")
    
    server_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", 
        "server.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8002",
        "--reload"
    ])
    
    return server_process


def start_streamlit_app():
    """Streamlit 앱을 시작합니다."""
    print("🎨 Streamlit UI를 시작합니다...")
    
    ui_process = subprocess.Popen([
        sys.executable, "-m", "streamlit", 
        "run", "app/main.py",
        "--server.port", "8501",
        "--server.address", "localhost",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ])
    
    return ui_process


def main():
    """메인 실행 함수."""
    print("🧠 AutoDiagentiAI 시작 중...")
    print("=" * 50)
    
    # 가상환경 확인
    if not check_and_activate_venv():
        sys.exit(1)
    
    # 의존성 확인
    if not check_dependencies():
        sys.exit(1)
    
    # 디렉토리 구조 확인
    required_dirs = [
        "server/storage/uploads",
        "server/storage/diagrams", 
        "server/storage/vectorstore/faiss_db",
        "server/storage/tmp",
        "server/storage/db",
        "server/logs"
    ]
    
    for dir_path in required_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("📁 필요한 디렉토리들이 생성되었습니다.")
    
    try:
        # FastAPI 서버 시작
        server_process = start_fastapi_server()
        
        # 서버 시작 대기
        print("⏳ FastAPI 서버 시작 대기 중...")
        time.sleep(5)
        
        # Streamlit UI 시작
        ui_process = start_streamlit_app()
        
        # Streamlit 시작 대기
        print("⏳ Streamlit UI 시작 대기 중...")
        time.sleep(3)
        
        print("\n" + "=" * 50)
        print("🎉 AutoDiagentiAI가 성공적으로 시작되었습니다!")
        print("\n📱 접속 정보:")
        print("   - Streamlit UI: http://localhost:8501")
        print("   - FastAPI 서버: http://localhost:8002")
        print("   - API 문서: http://localhost:8002/docs")
        print("\n💡 사용법:")
        print("   1. 브라우저에서 http://localhost:8501 접속")
        print("   2. Java Spring 프로젝트 ZIP 파일 업로드")
        print("   3. 분석 설정 후 분석 실행")
        print("   4. 시퀀스 다이어그램 및 AI 요약 결과 확인")
        print("\n🛑 종료하려면 Ctrl+C를 누르세요.")
        print("=" * 50)
        
        # 프로세스들이 종료될 때까지 대기
        try:
            server_process.wait()
            ui_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 사용자에 의해 종료되었습니다.")
            try:
                server_process.terminate()
                ui_process.terminate()
                # 프로세스가 정상적으로 종료될 때까지 잠시 대기
                time.sleep(1)
                if server_process.poll() is None:
                    server_process.kill()
                if ui_process.poll() is None:
                    ui_process.kill()
                print("✅ 모든 프로세스가 종료되었습니다.")
            except Exception as e:
                print(f"⚠️  프로세스 종료 중 오류 발생: {e}")
                print("✅ 강제 종료되었습니다.")
    
    except Exception as e:
        print(f"❌ 오류가 발생했습니다: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
