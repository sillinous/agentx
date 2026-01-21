import { useQuery } from '@tanstack/react-query';
import client from '../client';

interface GitInfo {
  is_repo: boolean;
  branch: string;
  remote: string;
  ahead: number;
  behind: number;
  modified: number;
  untracked: number;
  staged: number;
  last_commit: string;
  last_commit_date: string;
}

interface Monetization {
  score: number;
  category: string;
  signals: string[];
  tech_stack: string[];
  revenue_streams: string[];
}

interface Health {
  score: number;
  status: string;
}

export interface Recommendation {
  type: string;
  category: string;
  action: string;
  impact: string;
  project?: string;
  monetization_score?: number;
}

interface Blocker {
  title: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  description?: string;
}

interface RevenueMetadata {
  model: string;
  current_mrr: number;
  mrr_potential: string;
  launch_date?: string;
}

interface ProjectLinks {
  production?: string;
  staging?: string;
  docs?: string;
  repo?: string;
}

export interface Project {
  name: string;
  path: string;
  type: string;
  git: GitInfo;
  monetization: Monetization;
  health: Health;
  recommendations: Recommendation[];
  updated_at: string;
  // New metadata fields
  has_metadata?: boolean;
  display_name?: string;
  description?: string;
  project_status?: 'planning' | 'in_progress' | 'ready' | 'launched' | 'archived';
  priority?: number;
  completion?: number;
  blocker_count?: number;
  blockers?: Blocker[];
  revenue_metadata?: RevenueMetadata;
  time_to_launch?: string;
  tech_stack_override?: string[];
  stakeholder_notes?: string;
  links?: ProjectLinks;
  metadata_updated_at?: string;
}

interface PortfolioSummary {
  total_projects: number;
  by_potential: {
    high: number;
    medium: number;
    low: number;
  };
  revenue_ready: number;
  total_recommendations: number;
  critical_actions: number;
  revenue_opportunities: number;
  top_projects: Project[];
  updated_at: string;
}

interface ProjectsResponse {
  projects: Project[];
  total: number;
}

interface RecommendationsResponse {
  recommendations: Recommendation[];
  total: number;
  revenue_opportunities: number;
}

export function usePortfolioSummary() {
  return useQuery<PortfolioSummary>({
    queryKey: ['portfolio', 'summary'],
    queryFn: async () => {
      const { data } = await client.get('/portfolio/summary');
      return data;
    },
    refetchInterval: 60000, // Refresh every minute
  });
}

export function useAllProjects() {
  return useQuery<ProjectsResponse>({
    queryKey: ['portfolio', 'projects'],
    queryFn: async () => {
      const { data } = await client.get('/portfolio/projects');
      return data;
    },
    refetchInterval: 60000,
  });
}

export function useProjectDetails(projectName: string) {
  return useQuery<Project>({
    queryKey: ['portfolio', 'projects', projectName],
    queryFn: async () => {
      const { data } = await client.get(`/portfolio/projects/${projectName}`);
      return data;
    },
    enabled: !!projectName,
  });
}

export function useTopRecommendations() {
  return useQuery<RecommendationsResponse>({
    queryKey: ['portfolio', 'recommendations'],
    queryFn: async () => {
      const { data } = await client.get('/portfolio/recommendations');
      return data;
    },
    refetchInterval: 60000,
  });
}
