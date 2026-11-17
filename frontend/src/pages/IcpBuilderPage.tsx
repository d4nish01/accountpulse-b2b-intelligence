import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";

export default function IcpBuilderPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "",
    industries: "",
    min_employees: 0,
    max_employees: 10000,
    min_revenue_musd: 0,
    max_revenue_musd: 5000,
    countries: "",
    required_signals: "",
  });
  const [error, setError] = useState("");

  function set(key: string, value: string | number) {
    setForm({ ...form, [key]: value });
  }

  async function submit() {
    setError("");
    try {
      await api.createIcp({
        name: form.name,
        industries: form.industries.split(",").map((s) => s.trim()).filter(Boolean),
        min_employees: Number(form.min_employees),
        max_employees: Number(form.max_employees),
        min_revenue_musd: Number(form.min_revenue_musd),
        max_revenue_musd: Number(form.max_revenue_musd),
        countries: form.countries.split(",").map((s) => s.trim()).filter(Boolean),
        required_signals: form.required_signals.split(",").map((s) => s.trim()).filter(Boolean),
      });
      navigate("/");
    } catch (e) {
      setError(String(e));
    }
  }

  return (
    <div className="card" style={{ maxWidth: 560 }}>
      <h2>New Ideal Customer Profile</h2>
      <label>Name</label>
      <input style={{ width: "100%" }} value={form.name}
        onChange={(e) => set("name", e.target.value)}
        placeholder="e.g. Mid-market Indian SaaS" />
      <label>Target industries (comma-separated)</label>
      <input style={{ width: "100%" }} value={form.industries}
        onChange={(e) => set("industries", e.target.value)}
        placeholder="Software, Fintech" />
      <label>Employee range</label>
      <div style={{ display: "flex", gap: 8 }}>
        <input type="number" value={form.min_employees}
          onChange={(e) => set("min_employees", e.target.value)} />
        <input type="number" value={form.max_employees}
          onChange={(e) => set("max_employees", e.target.value)} />
      </div>
      <label>Revenue range ($M)</label>
      <div style={{ display: "flex", gap: 8 }}>
        <input type="number" value={form.min_revenue_musd}
          onChange={(e) => set("min_revenue_musd", e.target.value)} />
        <input type="number" value={form.max_revenue_musd}
          onChange={(e) => set("max_revenue_musd", e.target.value)} />
      </div>
      <label>Target countries (comma-separated, empty = any)</label>
      <input style={{ width: "100%" }} value={form.countries}
        onChange={(e) => set("countries", e.target.value)} placeholder="India, USA" />
      <label>Required signals (comma-separated)</label>
      <input style={{ width: "100%" }} value={form.required_signals}
        onChange={(e) => set("required_signals", e.target.value)}
        placeholder="uses Salesforce, hiring SDRs" />
      <div style={{ marginTop: 20 }}>
        <button onClick={submit} disabled={!form.name.trim()}>Create ICP</button>
      </div>
      {error && <p className="error">{error}</p>}
    </div>
  );
}
