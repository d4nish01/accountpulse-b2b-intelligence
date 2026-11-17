"""ICP endpoints: create and list Ideal Customer Profiles."""
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ICP
from ..schemas import ICPCreate, ICPOut

router = APIRouter(prefix="/icps", tags=["icps"])


def icp_to_out(i: ICP) -> ICPOut:
    return ICPOut(
        id=i.id, name=i.name,
        industries=i.list_field("industries"),
        min_employees=i.min_employees, max_employees=i.max_employees,
        min_revenue_musd=i.min_revenue_musd, max_revenue_musd=i.max_revenue_musd,
        countries=i.list_field("countries"),
        required_signals=i.list_field("required_signals"),
    )


@router.get("", response_model=list[ICPOut])
def list_icps(db: Session = Depends(get_db)):
    return [icp_to_out(i) for i in db.query(ICP).order_by(ICP.id).all()]


@router.post("", response_model=ICPOut)
def create_icp(payload: ICPCreate, db: Session = Depends(get_db)):
    icp = ICP(
        name=payload.name,
        industries=json.dumps(payload.industries),
        min_employees=payload.min_employees,
        max_employees=payload.max_employees,
        min_revenue_musd=payload.min_revenue_musd,
        max_revenue_musd=payload.max_revenue_musd,
        countries=json.dumps(payload.countries),
        required_signals=json.dumps(payload.required_signals),
    )
    db.add(icp)
    db.commit()
    db.refresh(icp)
    return icp_to_out(icp)


@router.get("/{icp_id}", response_model=ICPOut)
def get_icp(icp_id: int, db: Session = Depends(get_db)):
    icp = db.get(ICP, icp_id)
    if not icp:
        raise HTTPException(status_code=404, detail="ICP not found")
    return icp_to_out(icp)
