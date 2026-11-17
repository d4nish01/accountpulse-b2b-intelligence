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
