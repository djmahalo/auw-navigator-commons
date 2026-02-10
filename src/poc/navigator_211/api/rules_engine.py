from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Tuple
from sqlalchemy import text


def evaluate_rules_and_enqueue(conn, intake_id: int) -> Tuple[str, str | None, List[Dict[str, Any]]]:
    """
    Minimal rules evaluator (SQLite-safe):
    - If Intake.Crisis = 1 => queue 'Crisis'
    - Else if Priority in ('High','Critical') => queue 'Priority'
    - Else => queue = DomainModule (default_domain)
    Writes QueueItem row and returns (queue, reason, rules_applied)
    """
    row = conn.execute(
        text("SELECT Crisis, Priority, DomainModule FROM Intake WHERE IntakeId = :id"),
        {"id": intake_id},
    ).mappings().first()

    if not row:
        return ("General", "Intake not found", [])

    crisis = bool(row["Crisis"])
    priority = (row["Priority"] or "").strip()
    domain = (row["DomainModule"] or "").strip() or "General"

    if crisis:
        queue = "Crisis"
        reason = "Crisis flag is true"
        applied = [{"rule": "crisis_flag", "action": "route", "queue": queue}]
    elif priority.lower() in ("high", "critical"):
        queue = "Priority"
        reason = f"Priority is {priority}"
        applied = [{"rule": "priority_high", "action": "route", "queue": queue}]
    else:
        queue = domain
        reason = "Auto-routed"
        applied = [{"rule": "default_domain", "action": "route", "queue": queue}]

    created_at = datetime.utcnow().isoformat()

    conn.execute(
        text(
            """
            INSERT INTO QueueItem (IntakeId, QueueName, Status, Reason, CreatedAt)
            VALUES (:IntakeId, :QueueName, 'New', :Reason, :CreatedAt)
            """
        ),
        {"IntakeId": intake_id, "QueueName": queue, "Reason": reason, "CreatedAt": created_at},
    )

    return (queue, reason, applied)
