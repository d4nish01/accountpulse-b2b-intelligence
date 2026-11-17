"""Scoring endpoints: run the engine and read ranked results."""
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Company, ICP, Score
from ..schemas import ScoreOut
from ..scoring import score_company

router = APIRouter(tags=["scoring"])


def score_to_out(s: Score) -> ScoreOut:
    return ScoreOut(
        company_id=s.company_id,
        company_name=s.company.name,
        industry=s.company.industry,
        employee_count=s.company.employee_count,
        total_score=s.total_score,
        grade=s.grade,
        explanations=json.loads(s.explanations or "[]"),
    )


@router.post("/score/run", response_model=list[ScoreOut])
def run_scoring(icp_id: int, db: Session = Depends(get_db)):
    """Score every company against one ICP.

    Old scores for this ICP are replaced, so the rankings always reflect
    the current company data and the current ICP definition.
    """
    icp = db.get(ICP, icp_id)
    if not icp:
        raise HTTPException(status_code=404, detail="ICP not found")

    db.query(Score).filter(Score.icp_id == icp_id).delete()
    results = []
    for company in db.query(Company).all():
        outcome = score_company(company, icp)
        score = Score(
            company_id=company.id,
            icp_id=icp_id,
            total_score=outcome["total_score"],
            grade=outcome["grade"],
            explanations=json.dumps(outcome["explanations"]),
        )
        db.add(score)
        results.append(score)
    db.commit()

    results.sort(key=lambda s: s.total_score, reverse=True)
    return [score_to_out(s) for s in results]


@router.get("/rankings", response_model=list[ScoreOut])
def get_rankings(icp_id: int, db: Session = Depends(get_db)):
    """Read the latest stored rankings for an ICP (run /score/run first)."""
    scores = (
        db.query(Score)
        .filter(Score.icp_id == icp_id)
        .order_by(Score.total_score.desc())
        .all()
    )
    return [score_to_out(s) for s in scores]
