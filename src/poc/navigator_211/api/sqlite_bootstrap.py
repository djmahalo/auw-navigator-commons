from __future__ import annotations

from sqlalchemy import text
from .db import engine

SQL = """
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

CREATE TABLE IF NOT EXISTS QueueItem (
  QueueItemId INTEGER PRIMARY KEY AUTOINCREMENT,
  IntakeId INTEGER NOT NULL,
  QueueName TEXT NOT NULL,
  Status TEXT NOT NULL,
  Reason TEXT,
  CreatedAt TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Rule (
  RuleId INTEGER PRIMARY KEY AUTOINCREMENT,
  RuleName TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS RuleResult (
  RuleResultId INTEGER PRIMARY KEY AUTOINCREMENT,
  IntakeId INTEGER NOT NULL,
  RuleId INTEGER NOT NULL,
  Action TEXT NOT NULL,
  OutcomeJson TEXT,
  EvaluatedAt TEXT NOT NULL
);
"""

def bootstrap_sqlite() -> None:
    if engine is None:
        return
    with engine.begin() as conn:
        for stmt in SQL.strip().split(";"):
            s = stmt.strip()
            if s:
                conn.execute(text(s))
