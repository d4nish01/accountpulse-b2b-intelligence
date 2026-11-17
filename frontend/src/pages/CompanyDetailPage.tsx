import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";
import type { Brief, Company, ICP, ScoreRow } from "../types";

export default function CompanyDetailPage() {
  const { id } = useParams();
  const companyId = Number(id);
  const [company, setCompany] = useState<Company | null>(null);
  const [score, setScore] = useState<ScoreRow | null>(null);
  const [briefs, setBriefs] = useState<Brief[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getCompany(companyId).then(setCompany).catch(() => setError("Company not found"));
    api.listBriefs(companyId).then(setBriefs);
    // Find this company's latest score under any ICP, if scoring has run.
    api.listIcps().then(async (icps: ICP[]) => {
      for (const icp of icps) {
        const rows = await api.getRankings(icp.id).catch(() => [] as ScoreRow[]);
        const hit = rows.find((r) => r.company_id === companyId);
        if (hit) { setScore(hit); break; }
      }
    });
  }, [companyId]);

  async function brief() {
    setBusy(true);
    try {
      const b = await api.generateBrief(companyId);
      setBriefs([b, ...briefs]);
    } finally {
      setBusy(false);
    }
  }

  if (error) return <p className="error">{error}</p>;
  if (!company) return <p>Loading...</p>;

  return (
    <div>
      <div className="card">
        <h2>{company.name}</h2>
        <p className="muted">
          {company.domain} | {company.industry}
          {company.sub_industry ? ` / ${company.sub_industry}` : ""} |{" "}
          {company.employee_count} employees | ${company.revenue_musd}M revenue |{" "}
          {company.country} ({company.region})
        </p>
        <p>{company.description}</p>
        {company.tech_signals.length > 0 && (
          <p className="muted">Signals: {company.tech_signals.join(", ")}</p>
        )}
      </div>

      {score && (
        <div className="card">
          <h3>
            Score: {score.total_score}/100{" "}
            <span className={`grade grade-${score.grade}`}>{score.grade}</span>
          </h3>
          <p className="muted">Where every point came from:</p>
          {score.explanations.map((e) => (
            <p className="explain" key={e.rule}>
              <b>{e.rule}</b> {e.points}/{e.max_points} - {e.reason}
            </p>
          ))}
        </div>
      )}

      <div className="card">
        <h3>AI Research Briefs</h3>
        <button disabled={busy} onClick={brief}>
          {busy ? "Generating..." : "Generate brief"}
        </button>
        {briefs.map((b) => (
          <div key={b.id} style={{ marginTop: 16 }}>
            <p className="muted">model: {b.model}</p>
            <div className="brief">{b.content}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
