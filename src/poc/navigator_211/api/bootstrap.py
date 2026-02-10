from __future__ import annotations

from sqlalchemy import text
from .db import engine

def ensure_tables() -> None:
    if engine is None:
        return

    with engine.begin() as conn:
        # Intake table
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS Intake (
            IntakeId INTEGER PRIMARY KEY AUTOINCREMENT,
            CreatedAt TEXT NOT NULL,
            CallerId TEXT,
            Channel TEXT,
            DomainModule TEXT,
            Priority TEXT,
            Crisis INTEGER,
            Narrative TEXT,
            AttributesJson TEXT
        );
        """))

        # Queue table
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS QueueItem (
            QueueItemId INTEGER PRIMARY KEY AUTOINCREMENT,
            IntakeId INTEGER NOT NULL,
            QueueName TEXT NOT NULL,
            Status TEXT NOT NULL,
            Reason TEXT,
            CreatedAt TEXT NOT NULL
        );
        """))
