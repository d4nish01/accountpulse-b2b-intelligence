import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import type { ICP, ScoreRow } from "../types";

export default function RankingsPage() {
  const [icps, setIcps] = useState<ICP[]>([]);
  const [selectedIcp, setSelectedIcp] = useState<number | null>(null);
  const [rows, setRows] = useState<ScoreRow[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    api.listIcps().then((list) => {
      setIcps(list);
      if (list.length > 0) setSelectedIcp(list[0].id);
    });
  }, []);

  useEffect(() => {
    if (selectedIcp !== null) {
      api.getRankings(selectedIcp).then(setRows).catch(() => setRows([]));
    }
  }, [selectedIcp]);

  async function bootstrap() {
    // First run: pull in the sample companies so there is data to score.
    setBusy(true);
    try {
      const res = await api.loadSampleData();
      setMessage(`Loaded ${res.imported} sample companies.`);
    } catch {
      setMessage("Sample data already loaded or unavailable.");
    } finally {
      setBusy(false);
    }
  }

  async function run() {
    if (selectedIcp === null) return;
    setBusy(true);
    try {
      setRows(await api.runScoring(selectedIcp));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="card">
        <h2>Account Rankings</h2>
        <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          <select
            value={selectedIcp ?? ""}
            onChange={(e) => setSelectedIcp(Number(e.target.value))}
          >
            {icps.length === 0 && <option value="">No ICPs yet - create one</option>}
            {icps.map((i) => (
              <option key={i.id} value={i.id}>{i.name}</option>
            ))}
          </select>
          <button disabled={busy || selectedIcp === null} onClick={run}>
            {busy ? "Scoring..." : "Run scoring"}
          </button>
          <button disabled={busy} onClick={bootstrap} style={{ background: "#5a6b87" }}>
            Load sample companies
          </button>
          <span className="muted">{message}</span>
        </div>
      </div>

      {rows.length > 0 && (
        <div className="card">
          <table>
            <thead>
              <tr>
                <th>#</th><th>Company</th><th>Industry</th><th>Employees</th>
                <th>Score</th><th>Grade</th><th>Why (top reason)</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, idx) => (
                <tr key={r.company_id}>
                  <td>{idx + 1}</td>
                  <td><Link to={`/companies/${r.company_id}`}>{r.company_name}</Link></td>
                  <td>{r.industry}</td>
                  <td>{r.employee_count}</td>
                  <td>
                    <div className="score-bar"><div style={{ width: `${r.total_score}%` }} /></div>
                    <span className="muted">{r.total_score}/100</span>
                  </td>
                  <td><span className={`grade grade-${r.grade}`}>{r.grade}</span></td>
                  <td className="muted">
                    {[...r.explanations].sort((a, b) => b.points - a.points)[0]?.reason}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
