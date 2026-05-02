"""Persisted assessment progress and Inngest fallback queue (replaces in-memory dicts)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class AssessmentJobState(SQLModel, table=True):
    """Stores live/completed assessment job state (Postgres JSONB)."""

    __tablename__ = "assessment_job_state"

    assessment_id: str = Field(primary_key=True, max_length=64)
    status: str = Field(default="processing", index=True)
    payload: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class InngestFallbackEvent(SQLModel, table=True):
    """Queued Inngest events when direct send fails."""

    __tablename__ = "inngest_fallback_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    event_data: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    queued_at: datetime = Field(default_factory=datetime.utcnow)
    retry_count: int = Field(default=0)
    claimed_at: Optional[datetime] = Field(default=None)
