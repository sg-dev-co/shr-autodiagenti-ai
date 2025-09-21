# server/db/database.py

"""
SQLAlchemy 설정 
- SQLite 데이터베이스 연결 설정 및 DB 세션 관리
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from server.utils.config import settings

# SQLite 엔진 생성
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    connect_args={"check_same_thread": False},  # SQLite 전용 설정
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# SQLAlchemy 모델 기본 클래스
Base = declarative_base()

# DB 세션 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def run_with_db_session(func, *args, **kwargs):
    db = SessionLocal()
    try:
        return func(db, *args, **kwargs)
    finally:
        db.close()