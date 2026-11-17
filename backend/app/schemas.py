"""Pydantic schemas - what the API accepts and returns."""
from typing import List, Optional
from pydantic import BaseModel


class CompanyOut(BaseModel):
    id: int
    name: str
    domain: str
    industry: str
    sub_industry: str
    employee_count: int
    revenue_musd: float
    country: str
    region: str
    tech_signals: List[str]
    description: str
    source: str

    class Config:
        from_attributes = True


class ICPCreate(BaseModel):
    name: str
    industries: List[str] = []
    min_employees: int = 0
    max_employees: int = 10**9
    min_revenue_musd: float = 0.0
    max_revenue_musd: float = 10**12
    countries: List[str] = []
    required_signals: List[str] = []


class ICPOut(ICPCreate):
    id: int

    class Config:
        from_attributes = True


class ExplanationOut(BaseModel):
    rule: str
    points: float
    max_points: float
    reason: str


class ScoreOut(BaseModel):
    company_id: int
    company_name: str
    industry: str
    employee_count: int
    total_score: float
    grade: str
    explanations: List[ExplanationOut]


class BriefOut(BaseModel):
    id: int
    company_id: int
    content: str
    model: str

    class Config:
        from_attributes = True
