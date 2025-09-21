# server/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect
from server.routers import analysis, entry_point, upload, history
from server.db.database import Base, engine
from server.db import model
from server.utils.logger import get_logger

# 로거 선언
logger = get_logger(__name__)

# 모든 테이블 삭제
# Base.metadata.drop_all(bind=engine)

# 데이터베이스 초기화
logger.info("테이블 생성 중...")
Base.metadata.create_all(bind=engine)
logger.info("테이블 생성 완료!")

# 테이블 목록 출력
inspector = inspect(engine)
logger.info(inspector.get_table_names())

# FastAPI 앱 생성
app = FastAPI(
    title="AutoDiagentiAI API",
    description="Java Spring 프로젝트 분석 및 시퀀스 다이어그램 생성 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경용, 프로덕션에서는 특정 도메인 지정
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(upload.router)
app.include_router(analysis.router)
app.include_router(entry_point.router)
app.include_router(history.router)

@app.get("/")
async def root():
    return {"message": "AutoDiagentiAI API Server", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)