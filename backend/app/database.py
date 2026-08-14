"""数据库连接与会话。"""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from . import config

engine = create_engine(
    config.DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def migrate():
    """为已存在的表补充缺失列（轻量迁移）。"""
    insp = inspect(engine)
    with engine.begin() as conn:
        if insp.has_table("positions"):
            cols = [c["name"] for c in insp.get_columns("positions")]
            if "hold_days" not in cols:
                conn.execute(text("ALTER TABLE positions ADD COLUMN hold_days INTEGER DEFAULT 0"))
            if "high_since_buy" not in cols:
                conn.execute(text("ALTER TABLE positions ADD COLUMN high_since_buy FLOAT DEFAULT 0"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
