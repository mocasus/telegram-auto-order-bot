"""Multi-database connection utility with SQLAlchemy.

Supports SQLite, PostgreSQL, and MySQL via config.yaml.
Auto-detects from ``database.url`` (DATABASE_URL), ``database.type`` (DB_TYPE),
or falls back to ``database.path`` for backward-compatible SQLite.
"""

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session


def build_url(db_config: dict) -> str:
    """Build a SQLAlchemy connection URL from config dict.

    Priority: url > type > path (SQLite fallback).
    """
    url = db_config.get("url") or db_config.get("DATABASE_URL", "")
    if url:
        return url

    db_type = db_config.get("type", "sqlite")
    if db_type == "sqlite":
        path = db_config.get("path", "data/bot.db")
        return f"sqlite:///{path}"
    elif db_type in ("postgresql", "postgres"):
        return _pg_url(db_config)
    elif db_type == "mysql":
        return _mysql_url(db_config)
    else:
        raise ValueError(f"Unsupported database type: {db_type}")


def _pg_url(cfg: dict) -> str:
    host = cfg.get("host", "localhost")
    port = cfg.get("port", 5432)
    user = cfg.get("user", "postgres")
    password = cfg.get("password", "")
    database = cfg.get("database", "bot")
    creds = f"{user}:{password}" if password else user
    return f"postgresql://{creds}@{host}:{port}/{database}"

def _mysql_url(cfg: dict) -> str:
    host = cfg.get("host", "localhost")
    port = cfg.get("port", 3306)
    user = cfg.get("user", "root")
    password = cfg.get("password", "")
    database = cfg.get("database", "bot")
    creds = f"{user}:{password}" if password else user
    return f"mysql+pymysql://{creds}@{host}:{port}/{database}"

def get_engine(db_config: dict) -> Engine:
    """Create a SQLAlchemy engine from config dict."""
    return create_engine(build_url(db_config))


def get_session(db_config: dict) -> Session:
    """Get a new SQLAlchemy session from config dict."""
    engine = get_engine(db_config)
    return sessionmaker(bind=engine)()
