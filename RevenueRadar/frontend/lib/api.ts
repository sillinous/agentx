import type { Project, Opportunity, Overview, ActionTemplate, ActionResult } from './types';

const API_BASE = '/api';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }

  return res.json();
}

// Projects
export async function getProjects(params?: {
  tier?: string;
  status?: string;
  sort_by?: string;
  order?: string;
}): Promise<{ projects: Project[]; total: number }> {
  const query = new URLSearchParams(params as Record<string, string>).toString();
  return fetchJson(`/projects${query ? `?${query}` : ''}`);
}

export async function getProject(id: string): Promise<Project & { opportunities: Opportunity[] }> {
  return fetchJson(`/projects/${id}`);
}

export async function updateProject(id: string, data: Partial<Project>): Promise<{ success: boolean }> {
  return fetchJson(`/projects/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function scanProjects(): Promise<{ success: boolean; projects_found: number }> {
  return fetchJson('/projects/scan', { method: 'POST' });
}

// Analytics
export async function getOverview(): Promise<Overview> {
  return fetchJson('/analytics/overview');
}

export async function getQuickWins(limit = 10): Promise<{ opportunities: Opportunity[]; total: number }> {
  return fetchJson(`/analytics/quickwins?limit=${limit}`);
}

export async function getTiers(): Promise<{ tiers: Record<string, { count: number; projects: string[]; revenue_min: number; revenue_max: number }> }> {
  return fetchJson('/analytics/tiers');
}

// Opportunities
export async function getOpportunities(params?: {
  status?: string;
  priority?: string;
}): Promise<{ opportunities: Opportunity[]; total: number }> {
  const query = new URLSearchParams(params as Record<string, string>).toString();
  return fetchJson(`/opportunities${query ? `?${query}` : ''}`);
}

export async function updateOpportunityStatus(
  id: string,
  status: string
): Promise<{ success: boolean }> {
  return fetchJson(`/opportunities/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
}

export async function getPipeline(): Promise<{ pipeline: Record<string, Opportunity[]> }> {
  return fetchJson('/opportunities/pipeline');
}

// Actions
export async function getActionTemplates(): Promise<{ templates: Record<string, ActionTemplate> }> {
  return fetchJson('/actions/templates');
}

/**
 * Execute a predefined action template securely.
 * @param templateKey - Must be a valid key from the templates (e.g., 'deploy_vercel', 'run_tests_npm')
 * @param projectPath - The project directory path where the action will run
 */
export async function executeAction(
  templateKey: string,
  projectPath: string
): Promise<ActionResult> {
  return fetchJson('/actions/execute', {
    method: 'POST',
    body: JSON.stringify({
      template_key: templateKey,
      project_path: projectPath,
    }),
  });
}

// Health
export async function getHealth(): Promise<{ status: string; service: string }> {
  return fetchJson('/health');
}
