export interface Project {
  id: string;
  name: string;
  path: string;
  description: string;
  tech_stack: string[];
  maturity_score: number;
  revenue_score: number;
  effort_score: number;
  overall_score: number;
  tier: 'tier1' | 'tier2' | 'tier3';
  status: 'discovery' | 'development' | 'ready' | 'launched';
  revenue_potential_min: number;
  revenue_potential_max: number;
  last_scanned: string;
  metadata: ProjectMetadata;
  created_at: string;
  updated_at: string;
}

export interface ProjectMetadata {
  has_readme: boolean;
  has_docker: boolean;
  has_tests: boolean;
  has_ci_cd: boolean;
  has_stripe: boolean;
  has_auth: boolean;
  has_api: boolean;
  has_database: boolean;
  loc_estimate: number;
}

export interface Opportunity {
  id: string;
  project_id: string;
  project_name?: string;
  title: string;
  description: string;
  category: 'payment' | 'deployment' | 'feature' | 'marketing';
  priority: 'high' | 'medium' | 'low';
  effort_hours: number;
  revenue_impact: number;
  status: 'pending' | 'in_progress' | 'completed' | 'blocked';
  roi?: number;
  created_at: string;
  completed_at?: string;
}

export interface TierSummary {
  count: number;
  projects: string[];
  revenue_min: number;
  revenue_max: number;
}

export interface Overview {
  total_projects: number;
  by_tier: Record<string, number>;
  by_status: Record<string, number>;
  revenue_potential: {
    min: number;
    max: number;
  };
  avg_scores: {
    maturity: number;
    revenue: number;
    overall: number;
  };
  tier_summary: Record<string, TierSummary>;
}

export interface ActionTemplate {
  title: string;
  description: string;
  requires_npm: boolean;
}

export interface ActionResult {
  success: boolean;
  template?: string;
  stdout?: string;
  stderr?: string;
  return_code?: number;
  error?: string;
}
