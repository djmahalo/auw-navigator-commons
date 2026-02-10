from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

# Load env from config/.env (project root)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / "config" / ".env")

engine: Engine | None = None


def _has_driver(name: str) -> bool:
    try:
        import pyodbc  # type: ignore
        return name in pyodbc.drivers()
    except Exception:
        return False


def _sqlite_url() -> str:
    db_path = PROJECT_ROOT / "data" / "dev.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path.as_posix()}"


def _build_mssql_url() -> str:
    """
    Build a SQLAlchemy URL for Azure SQL via pyodbc.
    Requires Microsoft ODBC Driver 18 for SQL Server installed.
    """
    driver = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME") or os.getenv("DB_DATABASE")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    if not (server and database and user and password):
        raise RuntimeError("Missing DB_SERVER/DB_NAME(or DB_DATABASE)/DB_USER/DB_PASSWORD in config/.env")

    # URL-encode driver spaces
    driver_enc = driver.replace(" ", "+")
    return (
        f"mssql+pyodbc://{user}:{password}@{server}/{database}"
        f"?driver={driver_enc}&Encrypt=yes&TrustServerCertificate=no"
    )


def init_engine() -> None:
    global engine

    # 1) Explicit override
    db_url = os.getenv("DB_URL")
    if db_url:
        engine = create_engine(db_url, future=True)
        return

    # 2) Prefer Azure SQL if Driver 18 is available
    if _has_driver("ODBC Driver 18 for SQL Server"):
        engine = create_engine(_build_mssql_url(), future=True)
        return

    # 3) Fallback to local SQLite (no admin needed)
    engine = create_engine(_sqlite_url(), future=True)


init_engine()
