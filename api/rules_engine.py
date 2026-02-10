from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple, Optional
from sqlalchemy import text
from sqlalchemy.engine import Connection


def evaluate_rules_and_enqueue(conn: Connection, intake_id: int) -> Tuple[str, Optional[str], List[Dict[str, Any]]]:
    """
    Loads intake + enabled rules from DB, evaluates them, writes RuleResult,
    and enqueues to QueueItem with final queue decision.
    """
    intake = conn.execute(
        text("""
            SELECT IntakeId, DomainModule, Priority, Crisis, Narrative, AttributesJson
            FROM dbo.Intake
            WHERE IntakeId = :id
        """),
        {"id": intake_id},
    ).mappings().first()

    if not intake:
        raise RuntimeError("Intake not found for evaluation")

    attrs = _loads_json(intake.get("AttributesJson"))

    # Fetch enabled rules
    rules = conn.execute(
        text("""
            SELECT RuleId, RuleName, MatchJson, Action, ActionParamsJson, PriorityOrder
            FROM dbo.Rule
            WHERE IsEnabled = 1
            ORDER BY PriorityOrder ASC, RuleId ASC
        """)
    ).mappings().all()

    applied: List[Dict[str, Any]] = []
    final_queue = "General"
    final_reason: Optional[str] = None

    # Evaluate in order; first matching rule(s) can set queue / reason.
    for rule in rules:
        match = _loads_json(rule["MatchJson"])
        if _matches(match, intake, attrs):
            outcome = _apply_action(intake, attrs, rule["Action"], _loads_json(rule.get("ActionParamsJson")))

            # Persist rule result
            conn.execute(
                text("""
                    INSERT INTO dbo.RuleResult (IntakeId, RuleId, Action, OutcomeJson)
                    VALUES (:IntakeId, :RuleId, :Action, :OutcomeJson)
                """),
                {
                    "IntakeId": intake_id,
                    "RuleId": rule["RuleId"],
                    "Action": rule["Action"],
                    "OutcomeJson": json.dumps(outcome, ensure_ascii=False, separators=(",", ":")),
                },
            )

            applied.append(
                {
                    "rule_id": int(rule["RuleId"]),
                    "rule_name": rule["RuleName"],
                    "action": rule["Action"],
                    "outcome": outcome,
                }
            )

            # Queue decision logic: if action sets queue, take it (you can change to "highest severity wins")
            if "queue" in outcome:
                final_queue = outcome["queue"]
            if "reason" in outcome and outcome["reason"]:
                final_reason = outcome["reason"]

    # Enqueue
    conn.execute(
        text("""
            INSERT INTO dbo.QueueItem (IntakeId, QueueName, Status, Reason)
            VALUES (:IntakeId, :QueueName, 'Open', :Reason)
        """),
        {"IntakeId": intake_id, "QueueName": final_queue, "Reason": final_reason},
    )

    return final_queue, final_reason, applied


def _apply_action(intake: Dict[str, Any], attrs: Dict[str, Any], action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    action = (action or "").lower().strip()
    params = params or {}

    if action == "set_queue":
        return {
            "queue": params.get("queue", "General"),
            "reason": params.get("reason", None),
        }

    if action == "set_priority":
        return {"priority": params.get("priority", intake.get("Priority", "Normal"))}

    if action == "flag_crisis":
        return {"crisis": True, "reason": params.get("reason", "Crisis flagged by rule")}

    # Default no-op
    return {"note": f"Unknown action '{action}' (no-op)", "reason": params.get("reason")}


def _matches(match: Dict[str, Any], intake: Dict[str, Any], attrs: Dict[str, Any]) -> bool:
    """
    Simple JSON match language:
    {
      "all": [
        {"field": "DomainModule", "op": "eq", "value": "Housing"},
        {"attr": "risk_days", "op": "lte", "value": 7},
        {"field": "Crisis", "op": "eq", "value": true}
      ]
    }
    Supports: eq, neq, contains, lt, lte, gt, gte, in
    'field' reads from intake row, 'attr' reads from AttributesJson
    """
    if not match:
        return False

    clauses = match.get("all") or []
    for c in clauses:
        if not _eval_clause(c, intake, attrs):
            return False
    return True


def _eval_clause(clause: Dict[str, Any], intake: Dict[str, Any], attrs: Dict[str, Any]) -> bool:
    op = (clause.get("op") or "eq").lower()
    expected = clause.get("value")

    if "field" in clause:
        actual = intake.get(clause["field"])
    elif "attr" in clause:
        actual = attrs.get(clause["attr"])
    else:
        return False

    try:
        if op == "eq":
            return actual == expected
        if op == "neq":
            return actual != expected
        if op == "contains":
            return (str(expected).lower() in str(actual).lower()) if actual is not None else False
        if op == "lt":
            return actual < expected
        if op == "lte":
            return actual <= expected
        if op == "gt":
            return actual > expected
        if op == "gte":
            return actual >= expected
        if op == "in":
            return actual in (expected or [])
    except Exception:
        return False

    return False


def _loads_json(val: Any) -> Dict[str, Any]:
    if val is None or val == "":
        return {}
    if isinstance(val, dict):
        return val
    try:
        return json.loads(val)
    except Exception:
        return {}
