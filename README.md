# AccountPulse - B2B Account Intelligence

AccountPulse helps a B2B sales team answer one question: **which accounts should
we talk to first, and why?** You import target companies, describe your Ideal
Customer Profile (ICP), and AccountPulse scores every account against it with a
fully explainable breakdown, ranks them, and generates an AI research brief for
each top account.

Inspired by the account-intelligence category (Demandbase, 6sense, ZoomInfo),
rebuilt as a minimal, readable MVP.

## Architecture

```
┌────────────────────┐      REST/JSON       ┌──────────────────────────┐
│  React + TS (Vite) │  ──────────────────▶ │  FastAPI (Python)        │
│  frontend/         │                      │  backend/                │
│  - Rankings table  │                      │  - company CSV import    │
│  - Company detail  │                      │  - ICP CRUD              │
│  - ICP builder     │                      │  - scoring engine        │
└────────────────────┘                      │  - AI briefs (Gemini)    │
                                            └───────────┬──────────────┘
                                                        │
                                            ┌───────────▼──────────────┐
                                            │  PostgreSQL (Docker) or  │
                                            │  SQLite (local default)  │
                                            └──────────────────────────┘
```

## Quick start (no Docker needed)

Backend:

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# API docs: http://localhost:8000/docs
```

Frontend (in a second terminal):

```bash
cd frontend
npm install
npm run dev
# App: http://localhost:5173
```

Then in the UI: click **Load sample companies**, go to **ICP Builder**, create an
ICP (e.g. industries `Software, Fintech`, 500-10000 employees, country `India`,
signals `uses AWS, hiring SDRs`), back on **Rankings** press **Run scoring**.

## With Docker

```bash
cp .env.example .env       # add GEMINI_API_KEY if you have one
docker compose up --build
```

## How the scoring works (the part to explain in an interview)

`backend/app/scoring.py` is the whole engine - no ML, just five weighted rules,
each returning points **and a sentence explaining itself**:

| Rule | Max points | Question it answers |
|---|---|---|
| industry_fit | 30 | Is the company in a target industry? (half credit for sub-industry match) |
| size_fit | 25 | Is its employee count in range? (half credit within 20% of a bound) |
| revenue_fit | 20 | Is its revenue in range? |
| geography_fit | 15 | Is it in a target country? |
| signal_fit | 10 | What fraction of required buying/tech signals does it show? |

Grades: A >= 75, B >= 50, C >= 25, else D.

Why rule-based first? Because account scoring must be *explainable to a sales
rep* to be trusted, and a weighted rule set is the honest baseline any ML model
would have to beat. Every score stored in the DB carries its explanation list.

## AI research briefs

`POST /briefs/{company_id}` generates an account brief. If `GEMINI_API_KEY` is
set (free key: https://aistudio.google.com/apikey) the brief comes from Gemini;
otherwise the endpoint returns a structured template brief built from the
company's own data, so the product never hard-fails.

## API summary

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | liveness |
| GET | `/companies` | list companies |
| POST | `/companies/import` | upload a companies CSV |
| POST | `/companies/load-sample` | load bundled sample data |
| GET/POST | `/icps` | list / create ICPs |
| POST | `/score/run?icp_id=` | score all companies against an ICP |
| GET | `/rankings?icp_id=` | latest ranked results |
| POST/GET | `/briefs/{company_id}` | generate / list research briefs |

CSV format: see `sample_data/companies.csv` (the `tech_signals` column separates
signals with `;`).

## Project status / roadmap

- [x] Company import (CSV + sample data)
- [x] ICP builder
- [x] Explainable rule-based scoring + rankings
- [x] AI research briefs (Gemini, with template fallback)
- [ ] Auth & multi-user workspaces
- [ ] Real firmographic data providers (Clearbit-style enrichment)
- [ ] ML-learned weights once enough outcome data exists
