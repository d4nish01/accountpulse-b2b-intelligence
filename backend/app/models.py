"""SQLAlchemy models - the core entities of AccountPulse.

Company : one row per target business (imported from CSV or sample data).
ICP     : an Ideal Customer Profile - the criteria a "good" account must match.
Score   : the result of scoring one Company against one ICP, WITH the
          per-rule explanation of where every point came from.
Brief   : an AI-generated research brief for a company.
"""
import json
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from .database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, index=True)
    domain = Column(String, default="")
    industry = Column(String, default="", index=True)
    sub_industry = Column(String, default="")
    employee_count = Column(Integer, default=0)
    revenue_musd = Column(Float, default=0.0)  # annual revenue in millions USD
    country = Column(String, default="")
    region = Column(String, default="")
    tech_signals = Column(Text, default="[]")   # JSON list, e.g. ["uses Salesforce", "hiring SDRs"]
    description = Column(Text, default="")
    source = Column(String, default="manual")
    created_at = Column(DateTime, default=datetime.utcnow)

    scores = relationship("Score", back_populates="company", cascade="all, delete-orphan")
    briefs = relationship("Brief", back_populates="company", cascade="all, delete-orphan")

    def signal_list(self):
        try:
            return json.loads(self.tech_signals or "[]")
        except json.JSONDecodeError:
            return []


class ICP(Base):
    __tablename__ = "icps"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    industries = Column(Text, default="[]")        # JSON list of target industries
    min_employees = Column(Integer, default=0)
    max_employees = Column(Integer, default=10**9)
    min_revenue_musd = Column(Float, default=0.0)
    max_revenue_musd = Column(Float, default=10**12)
    countries = Column(Text, default="[]")         # JSON list; empty = any country
    required_signals = Column(Text, default="[]")  # JSON list of tech/buying signals
    created_at = Column(DateTime, default=datetime.utcnow)

    def list_field(self, field):
        try:
            return json.loads(getattr(self, field) or "[]")
        except json.JSONDecodeError:
            return []


class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), index=True)
    icp_id = Column(Integer, ForeignKey("icps.id"), index=True)
    total_score = Column(Float, default=0.0)
    grade = Column(String, default="D")
    explanations = Column(Text, default="[]")  # JSON list of {rule, points, max_points, reason}
    computed_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="scores")


class Brief(Base):
    __tablename__ = "briefs"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), index=True)
    content = Column(Text, default="")
    model = Column(String, default="template")  # "gemini-..." when the LLM was used
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="briefs")
