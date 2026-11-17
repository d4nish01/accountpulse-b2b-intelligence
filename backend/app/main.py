"""AccountPulse API - B2B account intelligence.

Run locally (no Docker needed):
    cd backend
    pip install -r requirements.txt
    uvicorn app.main:app --reload

Then open http://localhost:8000/docs for the interactive API docs.
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .database import Base, engine
from .routers import companies, icp, scoring, briefs

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AccountPulse API", version="0.1.0")

# The React dev server runs on :5173; allow it to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(companies.router)
app.include_router(icp.router)
app.include_router(scoring.router)
app.include_router(briefs.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.on_event("startup")
def seed_sample_data_if_empty():
    """If the database has no companies, load the bundled sample CSV.

    Keeps demo deploys self-healing: a fresh container (redeploy resets the
    SQLite file) comes up with data already in it.
    """
    import csv
    import json

    from .database import SessionLocal
    from .models import Company, ICP
    from .routers.companies import SAMPLE_CSV, _import_rows

    db = SessionLocal()
    try:
        if db.query(Company).count() == 0 and os.path.exists(SAMPLE_CSV):
            with open(SAMPLE_CSV, newline="", encoding="utf-8") as f:
                _import_rows(csv.DictReader(f), source="sample-data", db=db)
        # A demo ICP so a fresh deploy is instantly usable in a demo.
        if db.query(ICP).count() == 0:
            db.add(ICP(
                name="Mid-market Indian SaaS",
                industries=json.dumps(["Software", "Fintech"]),
                min_employees=500, max_employees=10000,
                min_revenue_musd=50, max_revenue_musd=2000,
                countries=json.dumps(["India"]),
                required_signals=json.dumps(["uses AWS", "hiring SDRs"]),
            ))
            db.commit()
    finally:
        db.close()


# In the single-image deploy, serve the built frontend and let the React
# router handle every non-API path. Registered API routes above win because
# they were added first.
STATIC_DIR = os.getenv("STATIC_DIR", "")
if STATIC_DIR and os.path.isdir(STATIC_DIR):

    @app.get("/{full_path:path}", include_in_schema=False)
    def frontend_app(full_path: str):
        candidate = os.path.join(STATIC_DIR, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
