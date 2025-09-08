from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """데이터베이스 테이블 초기화"""
    # 모든 모델을 import 해야 Base.metadata.create_all이 작동
    from . import models
    from sqlalchemy import text
    
    # PostgreSQL에서 CASCADE 옵션으로 안전하게 테이블 삭제
    try:
        with engine.connect() as conn:
            # 외래키 제약조건을 무시하고 모든 테이블 삭제
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
            conn.commit()
        print("기존 스키마 재생성 완료")
    except Exception as e:
        print(f"스키마 재생성 중 오류 (무시): {e}")
    
    # 새 테이블 생성
    try:
        Base.metadata.create_all(bind=engine)
        print("새 테이블 생성 완료")
    except Exception as e:
        print(f"테이블 생성 중 오류: {e}")
        raise e
