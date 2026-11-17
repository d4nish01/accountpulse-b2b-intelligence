"""The explainable account-scoring engine.

Design goal: EVERY point on every score must be traceable to one simple rule.
There is deliberately no machine learning here in v1 - a weighted rule set is
easy to defend in an interview ("here is the function, here is why each rule
exists"), and it is how most B2B scoring products actually start.

Total = 100 points across 5 rules:
  industry_fit   30  - does the company operate in an ICP target industry?
  size_fit       25  - is its employee count inside the ICP range?
  revenue_fit    20  - is its revenue inside the ICP range?
  geography_fit  15  - is it in a target country (if the ICP restricts any)?
  signal_fit     10  - does it show the tech/buying signals the ICP requires?

Partial credit is used where "close" still has value (e.g. sub-industry match,
size within 20% of the range). Grade bands: A>=75, B>=50, C>=25, else D.
"""
from typing import List, Dict

# Rule weights - these ARE the product's opinion about what matters most.
WEIGHTS = {
    "industry_fit": 30,
    "size_fit": 25,
    "revenue_fit": 20,
    "geography_fit": 15,
    "signal_fit": 10,
}

GRADE_BANDS = [(75, "A"), (50, "B"), (25, "C"), (0, "D")]


def _norm(value: str) -> str:
    return (value or "").strip().lower()


def _rule_industry(company, icp) -> Dict:
    """Full points if the industry matches; half for a sub-industry match."""
    targets = [_norm(i) for i in icp.list_field("industries")]
    max_points = WEIGHTS["industry_fit"]
    if not targets:
        return {"rule": "industry_fit", "points": max_points, "max_points": max_points,
                "reason": "ICP does not restrict industry, so every company passes."}
    industry = _norm(company.industry)
    sub = _norm(company.sub_industry)
    if industry in targets:
        return {"rule": "industry_fit", "points": max_points, "max_points": max_points,
                "reason": f"Industry '{company.industry}' is a target industry."}
    if sub and sub in targets:
        pts = max_points // 2
        return {"rule": "industry_fit", "points": pts, "max_points": max_points,
                "reason": f"Sub-industry '{company.sub_industry}' matches a target industry (half credit)."}
    return {"rule": "industry_fit", "points": 0, "max_points": max_points,
            "reason": f"Industry '{company.industry}' is not in the ICP target list."}


def _rule_size(company, icp) -> Dict:
    """Full points inside the employee range; half when within 20% of a bound."""
    max_points = WEIGHTS["size_fit"]
    n = company.employee_count or 0
    lo, hi = icp.min_employees, icp.max_employees
    if lo <= n <= hi:
        return {"rule": "size_fit", "points": max_points, "max_points": max_points,
                "reason": f"{n} employees is inside the target range {lo}-{hi}."}
    if n and (abs(n - lo) <= 0.2 * lo or abs(n - hi) <= 0.2 * hi):
        pts = max_points // 2
        return {"rule": "size_fit", "points": pts, "max_points": max_points,
                "reason": f"{n} employees is just outside the target range {lo}-{hi} (half credit)."}
    return {"rule": "size_fit", "points": 0, "max_points": max_points,
            "reason": f"{n} employees is outside the target range {lo}-{hi}."}


def _rule_revenue(company, icp) -> Dict:
    """Full points when revenue sits inside the ICP revenue range."""
    max_points = WEIGHTS["revenue_fit"]
    r = company.revenue_musd or 0.0
    lo, hi = icp.min_revenue_musd, icp.max_revenue_musd
    if lo <= r <= hi:
        return {"rule": "revenue_fit", "points": max_points, "max_points": max_points,
                "reason": f"Revenue ${r:.0f}M is inside the target range ${lo:.0f}M-${hi:.0f}M."}
    return {"rule": "revenue_fit", "points": 0, "max_points": max_points,
            "reason": f"Revenue ${r:.0f}M is outside the target range ${lo:.0f}M-${hi:.0f}M."}


def _rule_geography(company, icp) -> Dict:
    """Full points in a target country, or when the ICP is geography-agnostic."""
    max_points = WEIGHTS["geography_fit"]
    targets = [_norm(c) for c in icp.list_field("countries")]
    if not targets:
        return {"rule": "geography_fit", "points": max_points, "max_points": max_points,
                "reason": "ICP does not restrict geography, so every company passes."}
    if _norm(company.country) in targets:
        return {"rule": "geography_fit", "points": max_points, "max_points": max_points,
                "reason": f"Located in target country '{company.country}'."}
    return {"rule": "geography_fit", "points": 0, "max_points": max_points,
            "reason": f"Country '{company.country}' is not a target country."}


def _rule_signals(company, icp) -> Dict:
    """Points proportional to how many required signals the company shows."""
    max_points = WEIGHTS["signal_fit"]
    required = [_norm(s) for s in icp.list_field("required_signals")]
    if not required:
        return {"rule": "signal_fit", "points": max_points, "max_points": max_points,
                "reason": "ICP requires no specific signals, so every company passes."}
    have = {_norm(s) for s in company.signal_list()}
    matched = [s for s in required if s in have]
    if not matched:
        return {"rule": "signal_fit", "points": 0, "max_points": max_points,
                "reason": "None of the required signals were found on this account."}
    pts = round(max_points * len(matched) / len(required))
    return {"rule": "signal_fit", "points": pts, "max_points": max_points,
            "reason": f"Matches {len(matched)}/{len(required)} required signals: {', '.join(matched)}."}


RULES = [_rule_industry, _rule_size, _rule_revenue, _rule_geography, _rule_signals]


def score_company(company, icp) -> Dict:
    """Score one company against one ICP. Returns total, grade and explanations."""
    explanations: List[Dict] = [rule(company, icp) for rule in RULES]
    total = sum(e["points"] for e in explanations)
    grade = next(g for threshold, g in GRADE_BANDS if total >= threshold)
    return {"total_score": total, "grade": grade, "explanations": explanations}
