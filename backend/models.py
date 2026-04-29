from typing import Any
from pydantic import BaseModel, Field


# ── Requests ──────────────────────────────────────────────────────────────────

class SimulateTextRequest(BaseModel):
    description: str = Field(..., min_length=1)


class SimulateJsonRequest(BaseModel):
    scene: dict[str, Any]


class WhatIfRequest(BaseModel):
    scene: dict[str, Any]
    changes: dict[str, Any] = Field(
        ...,
        description=(
            "Flat key→value overrides applied to matching scene objects. "
            "Top-level scene keys (gravity, damping, duration) can be overridden directly. "
            "Object-level keys are matched by object name, e.g. "
            '{"ball": {"mass": 5.0}, "slope": {"friction": 0.1}}'
        ),
    )


# ── Responses ─────────────────────────────────────────────────────────────────

class SimulationResponse(BaseModel):
    scene: dict[str, Any]
    result: dict[str, Any]
    explanation: str
