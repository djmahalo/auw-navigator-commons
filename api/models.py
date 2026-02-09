from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field


class IntakeCreate(BaseModel):
    caller_id: Optional[str] = None
    channel: str = Field(default="phone", description="phone|web|chat|walkin")
    domain_module: str = Field(..., description="e.g., Housing, Food, Utilities")
    priority: str = Field(default="Normal", description="Low|Normal|High|Critical")
    crisis: bool = False
    narrative: str = ""
    attributes: Dict[str, Any] = Field(default_factory=dict)


class IntakeResponse(BaseModel):
    intake_id: int
    created_at: datetime
    domain_module: str
    priority: str
    crisis: bool
    queue: str
    reason: Optional[str] = None
    rules_applied: List[Dict[str, Any]] = Field(default_factory=list)


class RuleApplied(BaseModel):
    rule_id: int
    rule_name: str
    action: str
    outcome: Dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    db: str
    version: str
