"""Company endpoints: list, detail, CSV import, load bundled sample data."""
import csv
import io
import json
import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Company
from ..schemas import CompanyOut

router = APIRouter(prefix="/companies", tags=["companies"])

_CANDIDATES = [
    "/sample_data/companies.csv",  # docker-compose mount
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "sample_data", "companies.csv"),  # repo layout
]
SAMPLE_CSV = next((p for p in _CANDIDATES if os.path.exists(p)), _CANDIDATES[-1])

# The CSV columns AccountPulse understands. Extra columns are ignored.
COLUMNS = ["name", "domain", "industry", "sub_industry", "employee_count",
           "revenue_musd", "country", "region", "tech_signals", "description"]


def company_to_out(c: Company) -> CompanyOut:
    return CompanyOut(
        id=c.id, name=c.name, domain=c.domain, industry=c.industry,
        sub_industry=c.sub_industry, employee_count=c.employee_count,
        revenue_musd=c.revenue_musd, country=c.country, region=c.region,
        tech_signals=c.signal_list(), description=c.description, source=c.source,
    )


@router.get("", response_model=list[CompanyOut])
def list_companies(db: Session = Depends(get_db)):
    return [company_to_out(c) for c in db.query(Company).order_by(Company.name).all()]


@router.get("/{company_id}", response_model=CompanyOut)
def get_company(company_id: int, db: Session = Depends(get_db)):
    c = db.get(Company, company_id)
    if not c:
        raise HTTPException(status_code=404, detail="Company not found")
    return company_to_out(c)


def _import_rows(rows, source: str, db: Session) -> int:
    """Shared CSV-row import logic. tech_signals cell uses ';' as separator."""
    count = 0
    for row in rows:
        signals = [s.strip() for s in (row.get("tech_signals") or "").split(";") if s.strip()]
        company = Company(
            name=(row.get("name") or "").strip(),
            domain=(row.get("domain") or "").strip(),
            industry=(row.get("industry") or "").strip(),
            sub_industry=(row.get("sub_industry") or "").strip(),
            employee_count=int(float(row.get("employee_count") or 0)),
            revenue_musd=float(row.get("revenue_musd") or 0),
            country=(row.get("country") or "").strip(),
            region=(row.get("region") or "").strip(),
            tech_signals=json.dumps(signals),
            description=(row.get("description") or "").strip(),
            source=source,
        )
        if not company.name:
            continue
        db.add(company)
        count += 1
    db.commit()
    return count


@router.post("/import")
async def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a CSV of companies. See sample_data/companies.csv for the format."""
    content = (await file.read()).decode("utf-8-sig")
    rows = csv.DictReader(io.StringIO(content))
    count = _import_rows(rows, source=file.filename or "csv-upload", db=db)
    return {"imported": count}


@router.post("/load-sample")
def load_sample_data(db: Session = Depends(get_db)):
    """Load the bundled sample companies so the app works out of the box."""
    if not os.path.exists(SAMPLE_CSV):
        raise HTTPException(status_code=404, detail=f"Sample CSV not found at {SAMPLE_CSV}")
    with open(SAMPLE_CSV, newline="", encoding="utf-8") as f:
        count = _import_rows(csv.DictReader(f), source="sample-data", db=db)
    return {"imported": count}
