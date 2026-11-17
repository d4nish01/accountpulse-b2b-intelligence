# AccountPulse - Interview Defense Guide

How to talk about this project with confidence. Every claim below maps to real
code in this repo - if asked "show me", you can open the file.

## The 30-second pitch

"AccountPulse is a B2B account-intelligence tool. Sales teams at B2B companies
have thousands of possible accounts and no idea which to call first. AccountPulse
lets them import their account list, define their Ideal Customer Profile, and
then scores every account out of 100 with a full explanation of why - so a rep
sees not just a number but the reasoning. Top accounts get an AI-generated
research brief so the rep walks into the conversation prepared. It is inspired
by what Demandbase does at enterprise scale, rebuilt as a minimal MVP."

## Architecture (draw this if asked)

- React + TypeScript frontend (Vite) - three screens: Rankings, Company detail,
  ICP builder
- FastAPI backend - REST API, one router per concern
- Scoring engine - a single pure-Python module (`backend/app/scoring.py`)
- PostgreSQL in Docker, SQLite locally so anyone can run it in 2 minutes
- Gemini API for research briefs, with a template fallback so the product never
  breaks when the key or network is missing

## Key design decisions and WHY (this is what interviewers probe)

**1. Why rule-based scoring instead of ML?**
Account scores are only useful if a sales rep trusts them, and trust comes from
explainability. "This account scored 90: 30 because it is in a target industry,
25 because its size fits, ..." is something a rep can act on; a neural net
probability is not. Rule-based is also the honest baseline: any ML model would
have to beat it to justify itself. The code is one readable module with 5 rules
and weights at the top - `scoring.py`.

**2. Why store the explanations in the database with the score?**
Because a score without its reasons is not auditable. The `scores` table keeps
the per-rule breakdown as JSON, so the UI can always answer "why this number?"
without recomputing. Trade-off accepted: storage is cheap, auditability is core.

**3. Why does re-scoring replace old scores for an ICP?**
Rankings must reflect the current ICP and current data - keeping stale scores
would silently show wrong rankings. If history were needed, that is a
score_snapshots table; noted as a roadmap item.

**4. Why a template fallback for the AI briefs?**
Graceful degradation. An LLM call can fail (no key, quota, outage) and the
product must still work. The brief endpoint always returns something useful.
Same principle as a circuit breaker.

**5. Why FastAPI + React + Postgres?**
FastAPI: fast to write, typed via Pydantic, auto-generated API docs at /docs -
great for an MVP that must be demo-able. React+TS: type safety across the API
boundary (`frontend/src/types.ts` mirrors the backend schemas). Postgres: the
production standard; SQLite keeps local setup at zero.

## Likely questions and short answers

- **How would you get real company data?** Start with the customer's own CRM
  export (CSV import already exists). Then enrichment providers
  (Clearbit/Apollo-style APIs) behind a provider interface so sources are
  swappable.
- **How does this compare to Demandbase?** Same core loop - accounts in, ICP,
  scoring, activation - minus the hard parts: real-time intent data, ad
  activation, enterprise integrations. AccountPulse proves the loop, not the scale.
- **How would you learn the weights?** Once customers mark which scored accounts
  converted, fit logistic regression from rule outputs to conversion. The rule
  outputs become features - explainability survives because each feature is a rule.
- **What breaks at scale?** Scoring is O(companies) per run - fine to ~1M rows;
  beyond that, incremental scoring on data change and background jobs.
- **What would you build next?** Auth/workspaces, data-provider enrichment, then
  intent signals (website visits, hiring spikes) as new scoring rules.

## Walk-through for a live demo

1. `uvicorn app.main:app --reload` in backend/, `npm run dev` in frontend/
2. UI: "Load sample companies" (16 realistic companies)
3. ICP Builder: industries Software/Fintech, 500-10000 employees, India, signals
   "uses AWS, hiring SDRs"
4. Rankings > Run scoring: Freshworks and Chargebee top with grade A
5. Open a company: show the per-rule point breakdown - this is the money slide
6. Generate brief (template mode offline, Gemini with a key)
