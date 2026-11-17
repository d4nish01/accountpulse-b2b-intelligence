export interface Company {
  id: number;
  name: string;
  domain: string;
  industry: string;
  sub_industry: string;
  employee_count: number;
  revenue_musd: number;
  country: string;
  region: string;
  tech_signals: string[];
  description: string;
  source: string;
}

export interface ICP {
  id: number;
  name: string;
  industries: string[];
  min_employees: number;
  max_employees: number;
  min_revenue_musd: number;
  max_revenue_musd: number;
  countries: string[];
  required_signals: string[];
}

export interface Explanation {
  rule: string;
  points: number;
  max_points: number;
  reason: string;
}

export interface ScoreRow {
  company_id: number;
  company_name: string;
  industry: string;
  employee_count: number;
  total_score: number;
  grade: string;
  explanations: Explanation[];
}

export interface Brief {
  id: number;
  company_id: number;
  content: string;
  model: string;
}
