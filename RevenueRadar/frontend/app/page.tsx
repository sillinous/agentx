'use client';

import { useEffect, useState } from 'react';
import { KPIGrid } from '@/components/dashboard/KPIGrid';
import { TierChart } from '@/components/dashboard/TierChart';
import { QuickWinsList } from '@/components/dashboard/QuickWinsList';
import { ProjectCard } from '@/components/dashboard/ProjectCard';
import { Card, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { getOverview, getProjects, getQuickWins, scanProjects } from '@/lib/api';
import type { Overview, Project } from '@/lib/types';
import { RefreshCw, Scan, AlertCircle } from 'lucide-react';

export default function DashboardPage() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [quickWins, setQuickWins] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [overviewData, projectsData, quickWinsData] = await Promise.all([
        getOverview(),
        getProjects({ sort_by: 'overall_score', order: 'desc' }),
        getQuickWins(10),
      ]);
      setOverview(overviewData);
      setProjects(projectsData.projects);
      setQuickWins(quickWinsData.opportunities || []);
    } catch (err) {
      setError('Failed to load data. Make sure the backend is running on port 8000.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleScan = async () => {
    setScanning(true);
    try {
      const result = await scanProjects();
      if (result.success) {
        await fetchData();
      }
    } catch (err) {
      setError('Failed to scan repositories.');
      console.error(err);
    } finally {
      setScanning(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Connection Error</h2>
        <p className="text-gray-500 mb-4 text-center max-w-md">{error}</p>
        <div className="flex gap-3">
          <Button onClick={fetchData} variant="outline">
            <RefreshCw className="w-4 h-4 mr-2" />
            Retry
          </Button>
          <Button onClick={handleScan} loading={scanning}>
            <Scan className="w-4 h-4 mr-2" />
            Scan Repos
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Portfolio Dashboard</h1>
          <p className="text-gray-500 mt-1">
            Monitor monetization opportunities across your repositories
          </p>
        </div>
        <div className="flex gap-3">
          <Button onClick={fetchData} variant="outline" disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button onClick={handleScan} loading={scanning}>
            <Scan className="w-4 h-4 mr-2" />
            Scan Repositories
          </Button>
        </div>
      </div>

      {/* KPIs */}
      <KPIGrid overview={overview} loading={loading} />

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Tier Distribution */}
        <div className="lg:col-span-1">
          <TierChart overview={overview} />
        </div>

        {/* Right Column - Quick Wins */}
        <div className="lg:col-span-2">
          <QuickWinsList opportunities={quickWins} loading={loading} />
        </div>
      </div>

      {/* Top Projects */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <CardTitle>Top Projects by Score</CardTitle>
          <a href="/projects" className="text-sm text-blue-600 hover:text-blue-700">
            View all →
          </a>
        </div>

        {loading ? (
          <div className="animate-pulse space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-24 bg-gray-100 rounded-lg" />
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {projects.slice(0, 5).map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
