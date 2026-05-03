from __future__ import annotations

from pydantic import BaseModel, Field


class DemandCreate(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    requester: str = Field(min_length=2, max_length=120)
    business_unit: str = Field(min_length=2, max_length=120)
    problem_statement: str = Field(min_length=20, max_length=6000)
    expected_impact: str = Field(min_length=5, max_length=1200)
    target_date: str = Field(min_length=4, max_length=80)
    constraints: str = Field(default="", max_length=1600)
    optional_skills: str = Field(default="", max_length=800)


class RebalanceRequest(BaseModel):
    removed_resource_id: str = Field(min_length=2, max_length=40)
    reason: str = Field(default="Resource availability changed.", max_length=400)


class ExplainRequest(BaseModel):
    demand_id: int
    question: str = Field(min_length=3, max_length=500)
