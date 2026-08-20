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
            if "strategy_id" not in cols:
                conn.execute(text("ALTER TABLE positions ADD COLUMN strategy_id INTEGER"))
        if insp.has_table("strategies"):
            cols = [c["name"] for c in insp.get_columns("strategies")]
            if "initial_capital" not in cols:
                conn.execute(text("ALTER TABLE strategies ADD COLUMN initial_capital FLOAT DEFAULT 0"))
            if "available_cash" not in cols:
                conn.execute(text("ALTER TABLE strategies ADD COLUMN available_cash FLOAT DEFAULT 0"))
            if "group_name" not in cols:
                conn.execute(text("ALTER TABLE strategies ADD COLUMN group_name VARCHAR(50) DEFAULT ''"))
        if insp.has_table("trades"):
            cols = [c["name"] for c in insp.get_columns("trades")]
            if "strategy_id" not in cols:
                conn.execute(text("ALTER TABLE trades ADD COLUMN strategy_id INTEGER"))
        if insp.has_table("orders"):
            cols = [c["name"] for c in insp.get_columns("orders")]
            if "broker_type" not in cols:
                conn.execute(text("ALTER TABLE orders ADD COLUMN broker_type VARCHAR(10) DEFAULT 'paper'"))
            if "external_order_id" not in cols:
                conn.execute(text("ALTER TABLE orders ADD COLUMN external_order_id VARCHAR(64)"))
        if insp.has_table("scan_reports"):
            cols = [c["name"] for c in insp.get_columns("scan_reports")]
            if "source" not in cols:
                conn.execute(text("ALTER TABLE scan_reports ADD COLUMN source VARCHAR(10) DEFAULT 'manual'"))
        if not insp.has_table("users"):
            conn.execute(text("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(128) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
