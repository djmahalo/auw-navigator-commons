from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from .models import IntakeCreate, IntakeResponse, HealthResponse
from .db import engine
from .rules_engine import evaluate_rules_and_enqueue


from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from .models import IntakeCreate, IntakeResponse, HealthResponse
from .db import engine
from .rules_engine import evaluate_rules_and_enqueue

router = APIRouter()

def _require_engine():
    if engine is None:
        raise HTTPException(
            status_code=500,
            detail="DB is not configured. Set DB_SERVER, DB_NAME, DB_USER, DB_PASSWORD in config/.env"
        )




@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    # Quick DB ping
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {type(e).__name__}"
    return HealthResponse(status="ok", db=db_status, version="0.1.0")


@router.post("/intakes", response_model=IntakeResponse)
def create_intake(payload: IntakeCreate) -> IntakeResponse:
    """
    Create an intake, evaluate rules, and enqueue it.
    """
    created_at = datetime.utcnow()

    try:
        with engine.begin() as conn:
            # Insert intake
            result = conn.execute(
                text("""
                    INSERT INTO dbo.Intake
                        (CreatedAt, CallerId, Channel, DomainModule, Priority, Crisis, Narrative, AttributesJson)
                    OUTPUT INSERTED.IntakeId
                    VALUES
                        (:CreatedAt, :CallerId, :Channel, :DomainModule, :Priority, :Crisis, :Narrative, :AttributesJson)
                """),
                {
                    "CreatedAt": created_at,
                    "CallerId": payload.caller_id,
                    "Channel": payload.channel,
                    "DomainModule": payload.domain_module,
                    "Priority": payload.priority,
                    "Crisis": payload.crisis,
                    "Narrative": payload.narrative,
                    "AttributesJson": __safe_json(payload.attributes),
                },
            )
            intake_id = int(result.scalar_one())

            # Evaluate rules + enqueue
            queue, reason, applied = evaluate_rules_and_enqueue(conn, intake_id)

            return IntakeResponse(
                intake_id=intake_id,
                created_at=created_at,
                domain_module=payload.domain_module,
                priority=payload.priority,
                crisis=payload.crisis,
                queue=queue,
                reason=reason,
                rules_applied=applied,
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create intake: {type(e).__name__}: {e}")


@router.get("/queues")
def list_queues() -> List[Dict[str, Any]]:
    """
    Show all queue items (most recent first).
    """
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT TOP 200
                q.QueueItemId, q.IntakeId, q.QueueName, q.Status, q.Reason, q.CreatedAt,
                i.DomainModule, i.Priority, i.Crisis
            FROM dbo.QueueItem q
            JOIN dbo.Intake i ON i.IntakeId = q.IntakeId
            ORDER BY q.QueueItemId DESC
        """)).mappings().all()
        return [dict(r) for r in rows]


@router.get("/intakes/{intake_id}")
def get_intake(intake_id: int) -> Dict[str, Any]:
    with engine.connect() as conn:
        intake = conn.execute(
            text("SELECT * FROM dbo.Intake WHERE IntakeId = :id"),
            {"id": intake_id},
        ).mappings().first()

        if not intake:
            raise HTTPException(status_code=404, detail="Intake not found")

        rules = conn.execute(
            text("""
                SELECT r.RuleId, r.RuleName, rr.Action, rr.OutcomeJson, rr.EvaluatedAt
                FROM dbo.RuleResult rr
                JOIN dbo.Rule r ON r.RuleId = rr.RuleId
                WHERE rr.IntakeId = :id
                ORDER BY rr.RuleResultId ASC
            """),
            {"id": intake_id},
        ).mappings().all()

        queue = conn.execute(
            text("SELECT TOP 1 * FROM dbo.QueueItem WHERE IntakeId = :id ORDER BY QueueItemId DESC"),
            {"id": intake_id},
        ).mappings().first()

        return {
            "intake": dict(intake),
            "rules_applied": [dict(r) for r in rules],
            "queue_item": dict(queue) if queue else None,
        }


def __safe_json(obj: Any) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
