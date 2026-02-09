from __future__ import annotations

import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")

engine = None

if DB_SERVER and DB_NAME and DB_USER and DB_PASSWORD:
    conn_str = (
        f"mssql+pyodbc://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}:1433/{DB_NAME}"
        f"?driver={DB_DRIVER.replace(' ', '+')}"
        f"&Encrypt=yes&TrustServerCertificate=no"
    )
    engine = create_engine(conn_str, pool_pre_ping=True, future=True)
