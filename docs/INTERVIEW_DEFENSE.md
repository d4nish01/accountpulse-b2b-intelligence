# AccountPulse — Interview Defense Guide

**Repo:** github.com/d4nish01/accountpulse-b2b-intelligence
**Stack:** React + TypeScript, FastAPI (Python), PostgreSQL/SQLite, Docker, Gemini API

Every claim in this document maps to real code in the repository. If an
interviewer says "show me", open the file named in the section.

---

## 1. The 30-second pitch

"AccountPulse is a B2B account-intelligence tool. B2B sales teams have thousands
of possible accounts and no reliable way to decide which to call first.
AccountPulse lets them import their account list, define their Ideal Customer
Profile, and scores every account out of 100 — with a complete explanation of
why. A rep sees not just a number but the reasoning behind it, and top accounts
get an AI-generated research brief so the rep walks in prepared. It's the core
loop of what Demandbase does at enterprise scale, rebuilt as a minimal,
readable MVP."

If asked why you built it: "I wanted to understand the account-intelligence
category from the inside — the only way to really learn a product space is to
build the core loop yourself."

---

## 2. Architecture walkthrough

```
React + TS (Vite)  ──REST/JSON──▶  FastAPI  ──▶  PostgreSQL (Docker) / SQLite (local)
frontend/                        backend/
- Rankings table                 - routers/companies.py  (CSV import, sample data)
- Company detail                 - routers/icp.py        (ICP CRUD)
- ICP builder                    - routers/scoring.py    (run scoring, rankings)
                                 - routers/briefs.py     (AI briefs, Gemini + fallback)
                                 - scoring.py            (THE engine - pure functions)
                                 - models.py / database.py
```

Walk it left to right: "The frontend is three screens. All state lives in the
backend behind a REST API. The scoring engine is deliberately a separate pure
module — no framework code in it — so it can be unit-tested and explained in
isolation. The database is Postgres in Docker; locally it falls back to SQLite
so anyone clones the repo and runs it in two minutes."

Talking points per layer:

- **Frontend:** `frontend/src/types.ts` mirrors the backend Pydantic schemas —
  type safety across the API boundary catches contract drift at compile time.
- **Backend:** one router per concern, thin endpoints, logic in plain functions.
- **DB:** three core entities — Company, ICP, Score — plus Brief. Score rows
  carry their explanation JSON, so "why this number?" is always answerable
  without recompute.

---

## 3. Explain the scoring engine in 60 seconds

"AccountPulse scores are a weighted sum of five rules, each worth a fixed share
of 100 points: industry fit 30, company size 25, revenue 20, geography 15, and
buying signals 10. Each rule is a small function that returns two things: the
points it awarded, and one sentence explaining the decision in plain English —
'5,200 employees is inside the target range 500–10,000'. The total maps to
grades A through D. I chose rules over ML for v1 because a sales rep only acts
on a score they trust, and trust comes from being able to say exactly where
every point came from. The whole engine is one file, `scoring.py`, maybe 150
lines — anyone can read it in five minutes."

If they ask "why these weights?": "They encode a product opinion: in B2B,
*who the company is* (industry and size) predicts fit better than *where it is*
or *what tools it uses*, so firmographics carry 75 of the 100 points. The exact
numbers are tunable — the structure is the product decision."

---

## 4. Every design decision, with its reason

**D1. Rule-based scoring, not ML (v1).**
Reason: explainability is a feature, not a limitation — account scores drive
human action, and reps distrust black boxes. Rules are also the honest baseline
any ML model must beat. *File: backend/app/scoring.py.*

**D2. Explanations stored in the DB with each score.**
Reason: auditability. The `scores.explanations` column keeps the per-rule
breakdown, so the UI answers "why?" from stored state. Trade-off: some
redundant storage, accepted because storage is cheap and auditability is core.

**D3. Re-scoring replaces old scores for that ICP.**
Reason: rankings must reflect the current ICP definition and current data;
mixing old and new scores silently corrupts the ranking. If history is needed
later, that's a separate snapshot table (roadmap).

**D4. Partial credit instead of binary rules.**
Reason: real ICP fit is fuzzy. A company 10% outside the employee range is
still a decent prospect — half credit within 20% of a bound captures that
without complicating the model. Sub-industry match gets half industry points
for the same reason.

**D5. Template fallback for AI briefs.**
Reason: graceful degradation. LLM calls fail (no key, quota, outage); the
product must never hard-fail. The brief endpoint always returns something
useful — same principle as a circuit breaker. *File: routers/briefs.py.*

**D6. SQLite default, Postgres in Docker.**
Reason: developer experience. An interviewer or teammate can run the backend
with zero services; production-shaped deployments get Postgres via compose.
One `DATABASE_URL` env var switches between them.

**D7. FastAPI + Pydantic.**
Reason: typed request/response models, validation for free, and auto-generated
interactive docs at `/docs` — critical for an MVP that must be demo-able.

**D8. React + TypeScript + Vite.**
Reason: the industry-default SPA stack; TypeScript's shared types with the API
schemas prevent an entire class of frontend/backend mismatch bugs.

**D9. JSON columns for lists (industries, signals) instead of join tables.**
Reason: MVP pragmatism. These lists are small, never queried relationally, and
join tables would triple the schema for no current benefit. If filtering by
industry inside the DB becomes hot, normalize then.

**D10. No auth in v1.**
Reason: scope discipline. The core value is the scoring loop; auth is solved
infrastructure. It's the first roadmap item because a real product needs
workspaces.

---

## 5. Twenty likely interview questions, with model answers

**Product sense**

1. **What problem does this solve?**
   B2B reps waste most of their time on accounts that were never going to buy.
   AccountPulse ranks the account universe by ICP fit so effort goes to the
   accounts most likely to convert — and explains itself so reps trust it.

2. **Who is the user?**
   Two: the sales/marketing ops person who defines the ICP and owns the data,
   and the individual rep who consumes rankings and briefs before outreach.

3. **How is this different from a spreadsheet with filters?**
   Filters can't combine five fuzzy criteria into one comparable number, can't
   attach reasoning to each row, and can't generate a research brief per
   account. The scoring engine turns five soft judgments into one ordered list.

4. **How does it compare to Demandbase / 6sense?**
   Same core loop — accounts in, ICP, score, act — minus the enterprise moat:
   real-time intent data, ad-platform activation, deep CRM integrations.
   AccountPulse proves the loop; those products win on data network effects.

5. **What's the moat for a product like this?**
   Data, not scoring. The scoring logic is replicable in a weekend (I did it);
   proprietary intent and firmographic data is what incumbents actually sell.

6. **What would you build next, in order?**
   Auth + workspaces, then a data-provider integration for enrichment, then
   intent signals (hiring spikes, tech installs) as new scoring rules, then
   CRM sync so scores live where reps already work.

7. **How would you price it?**
   Per-seat SaaS with a platform fee, like the category standard; free tier
   capped on accounts scored to seed bottoms-up adoption.

**Technical depth**

8. **Walk me through the scoring code.**
   `score_company(company, icp)` runs five rule functions, each returning
   `{rule, points, max_points, reason}`. Totals are summed, mapped to a grade,
   and the whole explanation list is persisted with the score row.

9. **Why weights of 30/25/20/15/10?**
   Product judgment: identity signals (industry, size) outrank circumstantial
   ones (geography, tools). The numbers are configuration, not magic — the
   design decision is making them explicit constants at the top of the module.

10. **How would you learn better weights from data?**
    Collect outcomes — which scored accounts became opportunities — then fit
    logistic regression with the five rule outputs as features. Explainability
    survives because every feature is a named rule, so you can still say
    "industry fit contributes the most."

11. **What breaks at 1 million companies?**
    Re-scoring is O(n) per run — fine to ~1M rows on one machine. Beyond that:
    score incrementally on data change, move scoring to background workers,
    and index the scores table per ICP. The API shape doesn't change.

12. **Why not compute scores on read instead of storing them?**
    Reads would get slower as rules grow, and "why did this account rank third
    last week?" becomes unanswerable. Storing scores makes reads trivial and
    history auditable.

13. **How does the AI brief work?**
    The backend builds a structured prompt from the company's firmographics and
    signals, calls Gemini's generateContent API with the key from an env var,
    and stores the result. Any failure — no key, timeout, bad response — falls
    back to a template brief built from the same data.

14. **Why not a local model for the briefs?**
    Quality-per-ops-cost. A hosted free tier beats a self-hosted 7B model for
    an MVP; the provider is isolated behind one function, so swapping later is
    a one-file change.

15. **How is the frontend kept in sync with the API?**
    `types.ts` mirrors the Pydantic schemas by hand today; at team scale I'd
    generate TS types from FastAPI's OpenAPI spec so drift becomes impossible.

16. **What would you test first?**
    The scoring rules — pure functions, deterministic, the product's core
    claim. Table-driven tests: known company, known ICP, expected points and
    grade. Then API-level tests on import and scoring runs.

**Trade-offs and honesty**

17. **What's the weakest part of this MVP?**
    The data. The sample CSV is hand-made; real value needs live firmographic
    and intent data. That's exactly why the incumbents are data companies.

18. **What did you deliberately not build?**
    Auth, multi-user, real enrichment, ML scoring, and CRM sync — each is a
    known pattern, and spending MVP time on them would have hidden the one
    thing that matters: is the scoring loop useful and explainable?

19. **If a customer says the scores are wrong, what do you do?**
    Show them the explanation breakdown for the disputed accounts — that's why
    it exists. Either the ICP is wrong (fix the profile) or a rule misjudges
    (fix the rule with a regression test). The debugging path is the feature.

20. **What did you learn building this?**
    That explainability shapes everything downstream — schema (explanations
    stored), API (scores come with reasons), UI (the breakdown is the detail
    page's centerpiece), and even the pitch ("you never see a bare number").
    A constraint you choose early becomes the product's identity.

---

## 6. Live demo script (5 minutes)

1. Backend: `cd backend && uvicorn app.main:app --reload` → show `/docs`.
2. Frontend: `cd frontend && npm run dev` → open `localhost:5173`.
3. Click **Load sample companies** — 16 realistic companies imported.
4. **ICP Builder**: name "Mid-market Indian SaaS", industries `Software, Fintech`,
   employees 500–10,000, country `India`, signals `uses AWS, hiring SDRs`.
5. **Rankings → Run scoring**: Freshworks and Chargebee on top with grade A.
6. Open **Freshworks**: the per-rule point breakdown — *this is the money slide.*
7. Click **Generate brief**: with `GEMINI_API_KEY` set it is a real AI brief;
   without it, the template brief appears — show that the product degrades
   gracefully instead of erroring.

## 7. Numbers to have in your head

- 5 scoring rules, 100 points, weights 30/25/20/15/10, grades A≥75 / B≥50 / C≥25 / D
- 16 sample companies; scoring a full run is one POST and returns the ranking
- Backend ≈ 600 lines of Python; scoring engine ≈ 150 lines, zero dependencies
