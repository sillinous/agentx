'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { TierBadge, StatusBadge, PriorityBadge } from '@/components/ui/Badge';
import { getProject, updateOpportunityStatus, executeAction, getActionTemplates } from '@/lib/api';
import { formatCurrency, getCategoryIcon } from '@/lib/utils';
import type { Project, Opportunity, ActionTemplate } from '@/lib/types';
import {
  ArrowLeft,
  Code,
  Database,
  CreditCard,
  Shield,
  FileText,
  Container,
  TestTube,
  GitBranch,
  Clock,
  DollarSign,
  Play,
  Check,
  ExternalLink,
} from 'lucide-react';

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [project, setProject] = useState<(Project & { opportunities: Opportunity[] }) | null>(null);
  const [templates, setTemplates] = useState<Record<string, ActionTemplate>>({});
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [projectData, templatesData] = await Promise.all([
          getProject(params.id as string),
          getActionTemplates(),
        ]);
        setProject(projectData);
        setTemplates(templatesData.templates);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [params.id]);

  const handleStatusChange = async (oppId: string, status: string) => {
    try {
      await updateOpportunityStatus(oppId, status);
      // Refresh project data
      const updated = await getProject(params.id as string);
      setProject(updated);
    } catch (err) {
      console.error(err);
    }
  };

  const handleExecuteAction = async (templateKey: string) => {
    if (!project) return;
    setExecuting(templateKey);
    try {
      const result = await executeAction(templateKey, project.path);
      if (result.success) {
        alert(`Action '${result.template}' executed successfully!`);
      } else {
        alert(`Action failed: ${result.error || result.stderr}`);
      }
    } catch (err) {
      console.error(err);
      alert('Failed to execute action. Check if the required tools are installed.');
    } finally {
      setExecuting(null);
    }
  };

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-gray-200 rounded w-48" />
        <div className="h-64 bg-gray-100 rounded-xl" />
        <div className="h-96 bg-gray-100 rounded-xl" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Project not found</p>
        <Button variant="outline" className="mt-4" onClick={() => router.push('/projects')}>
          Back to Projects
        </Button>
      </div>
    );
  }

  const features = [
    { key: 'has_api', icon: Code, label: 'API', color: 'blue' },
    { key: 'has_database', icon: Database, label: 'Database', color: 'purple' },
    { key: 'has_stripe', icon: CreditCard, label: 'Payments', color: 'green' },
    { key: 'has_auth', icon: Shield, label: 'Auth', color: 'yellow' },
    { key: 'has_readme', icon: FileText, label: 'Docs', color: 'gray' },
    { key: 'has_docker', icon: Container, label: 'Docker', color: 'blue' },
    { key: 'has_tests', icon: TestTube, label: 'Tests', color: 'red' },
    { key: 'has_ci_cd', icon: GitBranch, label: 'CI/CD', color: 'orange' },
  ];

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <Button variant="ghost" onClick={() => router.push('/projects')}>
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Projects
      </Button>

      {/* Project Header */}
      <Card>
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
              <TierBadge tier={project.tier} />
              <StatusBadge status={project.status} />
            </div>
            <p className="text-gray-500 mb-4">{project.description || 'No description'}</p>
            <p className="text-sm text-gray-400 font-mono">{project.path}</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500">Overall Score</p>
            <p className="text-4xl font-bold text-gray-900">{project.overall_score}</p>
          </div>
        </div>

        {/* Scores */}
        <div className="grid grid-cols-4 gap-4 mt-6 pt-6 border-t border-gray-100">
          <div>
            <p className="text-sm text-gray-500">Maturity</p>
            <div className="flex items-center gap-2">
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full"
                  style={{ width: `${project.maturity_score}%` }}
                />
              </div>
              <span className="text-sm font-medium">{project.maturity_score}</span>
            </div>
          </div>
          <div>
            <p className="text-sm text-gray-500">Revenue Ready</p>
            <div className="flex items-center gap-2">
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-500 h-2 rounded-full"
                  style={{ width: `${project.revenue_score}%` }}
                />
              </div>
              <span className="text-sm font-medium">{project.revenue_score}</span>
            </div>
          </div>
          <div>
            <p className="text-sm text-gray-500">Ease of Launch</p>
            <div className="flex items-center gap-2">
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div
                  className="bg-purple-500 h-2 rounded-full"
                  style={{ width: `${project.effort_score}%` }}
                />
              </div>
              <span className="text-sm font-medium">{project.effort_score}</span>
            </div>
          </div>
          <div>
            <p className="text-sm text-gray-500">Revenue Potential</p>
            <p className="text-lg font-bold text-green-600">
              {formatCurrency(project.revenue_potential_min)} - {formatCurrency(project.revenue_potential_max)}/mo
            </p>
          </div>
        </div>

        {/* Features */}
        <div className="flex flex-wrap gap-2 mt-6 pt-6 border-t border-gray-100">
          {features.map((feature) => {
            const hasFeature = project.metadata?.[feature.key as keyof typeof project.metadata];
            return (
              <div
                key={feature.key}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg ${
                  hasFeature ? 'bg-green-50 text-green-700' : 'bg-gray-50 text-gray-400'
                }`}
              >
                <feature.icon className="w-4 h-4" />
                <span className="text-sm font-medium">{feature.label}</span>
                {hasFeature && <Check className="w-4 h-4" />}
              </div>
            );
          })}
        </div>

        {/* Tech Stack */}
        {project.tech_stack && project.tech_stack.length > 0 && (
          <div className="mt-4">
            <p className="text-sm text-gray-500 mb-2">Tech Stack</p>
            <div className="flex flex-wrap gap-2">
              {project.tech_stack.map((tech) => (
                <span
                  key={tech}
                  className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-sm"
                >
                  {tech}
                </span>
              ))}
            </div>
          </div>
        )}
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Opportunities */}
        <div className="lg:col-span-2">
          <Card>
            <CardTitle className="mb-4">Monetization Opportunities</CardTitle>

            {project.opportunities.length === 0 ? (
              <p className="text-gray-500 text-center py-8">
                No opportunities identified. Try rescanning the repository.
              </p>
            ) : (
              <div className="space-y-3">
                {project.opportunities.map((opp) => (
                  <div
                    key={opp.id}
                    className={`p-4 border rounded-lg ${
                      opp.status === 'completed' ? 'bg-green-50 border-green-200' : 'border-gray-200'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-lg">{getCategoryIcon(opp.category)}</span>
                          <span
                            className={`font-medium ${
                              opp.status === 'completed' ? 'line-through text-gray-500' : 'text-gray-900'
                            }`}
                          >
                            {opp.title}
                          </span>
                          <PriorityBadge priority={opp.priority} />
                          <StatusBadge status={opp.status} />
                        </div>
                        <p className="text-sm text-gray-500 mb-2">{opp.description}</p>
                        <div className="flex items-center gap-4 text-xs text-gray-500">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {opp.effort_hours} hours
                          </span>
                          <span className="flex items-center gap-1 text-green-600">
                            <DollarSign className="w-3 h-3" />
                            {formatCurrency(opp.revenue_impact)} impact
                          </span>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        {opp.status === 'pending' && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleStatusChange(opp.id, 'in_progress')}
                          >
                            Start
                          </Button>
                        )}
                        {opp.status === 'in_progress' && (
                          <Button
                            size="sm"
                            variant="primary"
                            onClick={() => handleStatusChange(opp.id, 'completed')}
                          >
                            Complete
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Quick Actions */}
        <div>
          <Card>
            <CardTitle className="mb-4">Quick Actions</CardTitle>

            <div className="space-y-2">
              {Object.entries(templates).map(([key, template]) => (
                <Button
                  key={key}
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => handleExecuteAction(key)}
                  loading={executing === key}
                  disabled={executing !== null}
                >
                  <Play className="w-4 h-4 mr-2" />
                  {template.title}
                </Button>
              ))}
            </div>

            <div className="mt-4 pt-4 border-t border-gray-100">
              <Button
                variant="ghost"
                className="w-full justify-start text-gray-500"
                onClick={() => {
                  // Open in VS Code or file explorer
                  window.open(`vscode://file/${project.path}`, '_blank');
                }}
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                Open in VS Code
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
