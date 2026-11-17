import type { Brief, Company, ICP, ScoreRow } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) throw new Error(`${options?.method ?? "GET"} ${path} failed: ${res.status}`);
  return res.json();
}

export const api = {
  listCompanies: () => req<Company[]>("/companies"),
  getCompany: (id: number) => req<Company>(`/companies/${id}`),
  loadSampleData: () =>
    req<{ imported: number }>("/companies/load-sample", { method: "POST" }),
  listIcps: () => req<ICP[]>("/icps"),
  createIcp: (icp: Omit<ICP, "id">) =>
    req<ICP>("/icps", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(icp),
    }),
  runScoring: (icpId: number) =>
    req<ScoreRow[]>(`/score/run?icp_id=${icpId}`, { method: "POST" }),
  getRankings: (icpId: number) => req<ScoreRow[]>(`/rankings?icp_id=${icpId}`),
  generateBrief: (companyId: number) =>
    req<Brief>(`/briefs/${companyId}`, { method: "POST" }),
  listBriefs: (companyId: number) => req<Brief[]>(`/briefs/${companyId}`),
};
