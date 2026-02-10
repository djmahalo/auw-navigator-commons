from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Mapping

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from .db import engine
from .models import HealthResponse, IntakeCreate, IntakeResponse
from .rules_engine import evaluate_rules_and_enqueue

router = APIRouter()


# -----------------------
# Helpers
# -----------------------
def _to_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    if isinstance(v, (int, float)):
        return bool(int(v))
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("1", "true", "t", "yes", "y", "on"):
            return True
        if s in ("0", "false", "f", "no", "n", "off", ""):
            return False
        return True
    return bool(v)


def _parse_json(v: Any) -> Any:
    import json

    if v is None:
        return None
    if isinstance(v, (dict, list)):
        return v
    if not isinstance(v, str):
        return v
    s = v.strip()
    if not s:
        return None
    try:
        return json.loads(s)
    except Exception:
        return v


def _safe_json(obj: Any) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False)


def _shape_intake_list_row(row: Mapping[str, Any]) -> Dict[str, Any]:
    d = dict(row)
    if "crisis" in d:
        d["crisis"] = _to_bool(d["crisis"])
    return d


def _shape_intake_detail_row(row: Mapping[str, Any]) -> Dict[str, Any]:
    d = dict(row)
    if "Crisis" in d:
        d["Crisis"] = _to_bool(d["Crisis"])
    if "AttributesJson" in d:
        d["AttributesJson"] = _parse_json(d["AttributesJson"])
    return d


# -----------------------
# Health check
# -----------------------
@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    if engine is None:
        return HealthResponse(status="ok", db="not_configured", version="0.1.0")

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return HealthResponse(status="ok", db="ok", version="0.1.0")
    except Exception as e:
        return HealthResponse(status="ok", db=f"error: {type(e).__name__}", version="0.1.0")


# -----------------------
# Create intake (insert + run rules_engine)
# -----------------------
@router.post("/intakes", response_model=IntakeResponse)
def create_intake(payload: IntakeCreate) -> IntakeResponse:
    if engine is None:
        raise HTTPException(status_code=500, detail="DB not configured")

    created_at = datetime.utcnow()

    try:
        with engine.begin() as conn:
            # 1) Insert intake
            conn.execute(
                text(
                    """
                    INSERT INTO Intake
                    (CreatedAt, CallerId, Channel, DomainModule, Priority, Crisis, Narrative, AttributesJson)
                    VALUES
                    (:CreatedAt, :CallerId, :Channel, :DomainModule, :Priority, :Crisis, :Narrative, :AttributesJson)
                    """
                ),
                {
                    "CreatedAt": created_at.isoformat(),
                    "CallerId": payload.caller_id,
                    "Channel": payload.channel,
                    "DomainModule": payload.domain_module,
                    "Priority": payload.priority,
                    "Crisis": 1 if payload.crisis else 0,
                    "Narrative": payload.narrative,
                    "AttributesJson": _safe_json(payload.attributes),
                },
            )

            intake_id = int(conn.execute(text("SELECT last_insert_rowid()")).scalar_one())

            # 2) Run rules + enqueue (writes QueueItem row)
            queue, reason, applied = evaluate_rules_and_enqueue(conn, intake_id)

        return IntakeResponse(
            intake_id=intake_id,
            created_at=created_at,
            domain_module=payload.domain_module,
            priority=payload.priority,
            crisis=payload.crisis,
            queue=queue,
            reason=reason or "",
            rules_applied=applied,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------
# Step E: Requeue an existing intake (rerun rules + enqueue again)
# -----------------------
@router.post("/intakes/{intake_id}/requeue")
def requeue_intake(intake_id: int):
    if engine is None:
        raise HTTPException(status_code=500, detail="DB not configured")

    try:
        with engine.begin() as conn:
            # Ensure intake exists
            exists = conn.execute(
                text("SELECT 1 FROM Intake WHERE IntakeId = :id"),
                {"id": intake_id},
            ).scalar()

            if not exists:
                raise HTTPException(status_code=404, detail="not found")

            queue, reason, applied = evaluate_rules_and_enqueue(conn, intake_id)

        return {
            "intake_id": intake_id,
            "queue": queue,
            "reason": reason,
            "rules_applied": applied,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------
# Step F: List intakes showing the LATEST queue row per intake
# -----------------------
@router.get("/intakes")
def list_intakes(limit: int = 50):
    if engine is None:
        return {"count": 0, "items": []}

    # Latest QueueItem per IntakeId = row with max QueueItemId
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                WITH latest_q AS (
                    SELECT IntakeId, MAX(QueueItemId) AS max_qid
                    FROM QueueItem
                    GROUP BY IntakeId
                )
                SELECT
                    i.IntakeId      AS intake_id,
                    i.CreatedAt     AS created_at,
                    i.DomainModule  AS domain_module,
                    i.Priority      AS priority,
                    i.Crisis        AS crisis,
                    q.QueueName     AS queue,
                    q.Reason        AS reason
                FROM Intake i
                LEFT JOIN latest_q lq
                    ON lq.IntakeId = i.IntakeId
                LEFT JOIN QueueItem q
                    ON q.QueueItemId = lq.max_qid
                ORDER BY i.IntakeId DESC
                LIMIT :limit
                """
            ),
            {"limit": limit},
        ).mappings().all()

    items = [_shape_intake_list_row(r) for r in rows]
    return {"count": len(items), "items": items}


# -----------------------
# Get single intake (also shows latest queue row)
# -----------------------
@router.get("/intakes/{intake_id}")
def get_intake(intake_id: int):
    if engine is None:
        raise HTTPException(status_code=500, detail="DB not configured")

    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                WITH latest_q AS (
                    SELECT IntakeId, MAX(QueueItemId) AS max_qid
                    FROM QueueItem
                    WHERE IntakeId = :id
                    GROUP BY IntakeId
                )
                SELECT
                    i.*,
                    q.QueueName AS queue,
                    q.Reason    AS reason,
                    q.Status    AS queue_status
                FROM Intake i
                LEFT JOIN latest_q lq
                    ON lq.IntakeId = i.IntakeId
                LEFT JOIN QueueItem q
                    ON q.QueueItemId = lq.max_qid
                WHERE i.IntakeId = :id
                """
            ),
            {"id": intake_id},
        ).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="not found")

    return _shape_intake_detail_row(row)


# -----------------------
# List queues (history)
# -----------------------
@router.get("/queues")
def list_queues() -> List[Dict[str, Any]]:
    if engine is None:
        return []

    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT * FROM QueueItem ORDER BY QueueItemId DESC")
        ).mappings().all()
        return [dict(r) for r in rows]
