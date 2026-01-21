import { useState } from 'react';
import {
  usePortfolioSummary,
  useAllProjects,
  useTopRecommendations,
  type Recommendation,
  type Project,
} from '../api/hooks/usePortfolio';
import { Spinner } from '../components/ui';

export default function Portfolio() {
  const { data: summary, isLoading: summaryLoading } = usePortfolioSummary();
  const { data: projectsData, isLoading: projectsLoading } = useAllProjects();
  const { data: recommendations, isLoading: recsLoading } = useTopRecommendations();
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  if (summaryLoading || projectsLoading || recsLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <Spinner size="lg" />
      </div>
    );
  }

  const projects = projectsData?.projects || [];
  const filteredProjects = selectedCategory === 'all'
    ? projects
    : projects.filter(p => {
        if (selectedCategory === 'high') return p.monetization.score >= 70;
        if (selectedCategory === 'medium') return p.monetization.score >= 40 && p.monetization.score < 70;
        if (selectedCategory === 'low') return p.monetization.score < 40;
        if (selectedCategory === 'metadata') return p.has_metadata;
        if (selectedCategory === 'ready') return p.project_status === 'ready' || p.project_status === 'launched';
        return true;
      });

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white">
      {/* Ambient background effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 -left-48 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-1/4 -right-48 w-96 h-96 bg-green-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[40rem] h-[40rem] bg-blue-500/5 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 px-8 py-12 max-w-[1800px] mx-auto">
        {/* Header Section */}
        <div className="mb-16">
          <div className="flex items-end justify-between mb-6">
            <div>
              <h1 className="text-6xl font-black tracking-tight mb-3 bg-gradient-to-r from-white via-cyan-200 to-green-300 bg-clip-text text-transparent">
                Solutions Portfolio
              </h1>
              <p className="text-lg text-slate-400 font-light tracking-wide">
                Revenue Intelligence & Project Analytics
              </p>
            </div>
            <div className="text-right font-mono text-sm text-slate-500">
              <div>Updated: {new Date(summary?.updated_at || '').toLocaleTimeString()}</div>
              <div className="text-xs mt-1">Auto-refresh: 60s</div>
            </div>
          </div>

          {/* Key Metrics Grid */}
          <div className="grid grid-cols-7 gap-4 mt-12">
            <MetricCard
              label="Total Projects"
              value={summary?.total_projects || 0}
              color="slate"
              icon="📊"
            />
            <MetricCard
              label="With Metadata"
              value={projects.filter(p => p.has_metadata).length}
              color="purple"
              icon="📋"
            />
            <MetricCard
              label="High Potential"
              value={summary?.by_potential.high || 0}
              color="green"
              icon="🚀"
              pulse
            />
            <MetricCard
              label="Medium Potential"
              value={summary?.by_potential.medium || 0}
              color="cyan"
              icon="⚡"
            />
            <MetricCard
              label="Revenue Ready"
              value={summary?.revenue_ready || 0}
              color="emerald"
              icon="💰"
              pulse
            />
            <MetricCard
              label="Revenue Opportunities"
              value={summary?.revenue_opportunities || 0}
              color="yellow"
              icon="💡"
              pulse
            />
            <MetricCard
              label="Critical Actions"
              value={summary?.critical_actions || 0}
              color="red"
              icon="⚠️"
            />
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-12 gap-6">
          {/* Left Column - Top Recommendations */}
          <div className="col-span-4">
            <div className="bg-gradient-to-br from-slate-900/80 to-slate-800/80 backdrop-blur-xl rounded-2xl border border-cyan-500/20 shadow-2xl shadow-cyan-500/10 p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-1 h-8 bg-gradient-to-b from-cyan-400 to-green-400 rounded-full" />
                <h2 className="text-2xl font-bold">Top Revenue Actions</h2>
              </div>

              <div className="space-y-3 max-h-[800px] overflow-y-auto custom-scrollbar">
                {recommendations?.recommendations.slice(0, 10).map((rec, idx) => (
                  <RecommendationCard key={idx} recommendation={rec} rank={idx + 1} />
                ))}
              </div>
            </div>
          </div>

          {/* Right Column - Projects */}
          <div className="col-span-8">
            {/* Category Filter */}
            <div className="flex flex-wrap gap-2 mb-6">
              <FilterButton
                active={selectedCategory === 'all'}
                onClick={() => setSelectedCategory('all')}
                label="All Projects"
                count={projects.length}
              />
              <FilterButton
                active={selectedCategory === 'metadata'}
                onClick={() => setSelectedCategory('metadata')}
                label="With Metadata"
                count={projects.filter(p => p.has_metadata).length}
                color="purple"
              />
              <FilterButton
                active={selectedCategory === 'ready'}
                onClick={() => setSelectedCategory('ready')}
                label="Ready to Launch"
                count={projects.filter(p => p.project_status === 'ready' || p.project_status === 'launched').length}
                color="emerald"
              />
              <FilterButton
                active={selectedCategory === 'high'}
                onClick={() => setSelectedCategory('high')}
                label="High Potential"
                count={summary?.by_potential.high || 0}
                color="green"
              />
              <FilterButton
                active={selectedCategory === 'medium'}
                onClick={() => setSelectedCategory('medium')}
                label="Medium"
                count={summary?.by_potential.medium || 0}
                color="cyan"
              />
              <FilterButton
                active={selectedCategory === 'low'}
                onClick={() => setSelectedCategory('low')}
                label="Low"
                count={summary?.by_potential.low || 0}
                color="slate"
              />
            </div>

            {/* Projects Grid */}
            <div className="grid grid-cols-2 gap-6">
              {filteredProjects.map((project) => (
                <ProjectCard key={project.name} project={project} />
              ))}
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Outfit:wght@300;400;700;900&display=swap');

        * {
          font-family: 'Outfit', -apple-system, system-ui, sans-serif;
        }

        .font-mono {
          font-family: 'JetBrains Mono', monospace;
        }

        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }

        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(15, 23, 42, 0.5);
          border-radius: 3px;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(6, 182, 212, 0.3);
          border-radius: 3px;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(6, 182, 212, 0.5);
        }

        @keyframes pulse-glow {
          0%, 100% {
            box-shadow: 0 0 20px rgba(6, 182, 212, 0.3);
          }
          50% {
            box-shadow: 0 0 30px rgba(6, 182, 212, 0.6);
          }
        }

        .animate-pulse-glow {
          animation: pulse-glow 2s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}

interface MetricCardProps {
  label: string;
  value: number;
  color: string;
  icon: string;
  pulse?: boolean;
}

function MetricCard({ label, value, color, icon, pulse }: MetricCardProps) {
  const colorClasses: Record<string, { bg: string; border: string; text: string }> = {
    slate: { bg: 'from-slate-800/80 to-slate-900/80', border: 'border-slate-700/50', text: 'text-slate-300' },
    green: { bg: 'from-green-900/40 to-emerald-900/40', border: 'border-green-500/30', text: 'text-green-300' },
    cyan: { bg: 'from-cyan-900/40 to-blue-900/40', border: 'border-cyan-500/30', text: 'text-cyan-300' },
    emerald: { bg: 'from-emerald-900/40 to-green-900/40', border: 'border-emerald-500/30', text: 'text-emerald-300' },
    yellow: { bg: 'from-yellow-900/40 to-amber-900/40', border: 'border-yellow-500/30', text: 'text-yellow-300' },
    red: { bg: 'from-red-900/40 to-rose-900/40', border: 'border-red-500/30', text: 'text-red-300' },
    purple: { bg: 'from-purple-900/40 to-violet-900/40', border: 'border-purple-500/30', text: 'text-purple-300' },
  };

  const colors = colorClasses[color] || colorClasses.slate;

  return (
    <div
      className={`bg-gradient-to-br ${colors.bg} backdrop-blur-xl rounded-xl border ${colors.border} p-5 ${
        pulse ? 'animate-pulse-glow' : ''
      }`}
    >
      <div className="text-3xl mb-2">{icon}</div>
      <div className={`text-4xl font-black font-mono mb-1 ${colors.text}`}>{value}</div>
      <div className="text-xs text-slate-400 uppercase tracking-wider font-light">{label}</div>
    </div>
  );
}

interface RecommendationCardProps {
  recommendation: Recommendation;
  rank: number;
}

function RecommendationCard({ recommendation, rank }: RecommendationCardProps) {
  const typeColors: Record<string, string> = {
    revenue: 'from-green-500 to-emerald-500',
    critical: 'from-red-500 to-rose-500',
    high: 'from-orange-500 to-amber-500',
    medium: 'from-cyan-500 to-blue-500',
    low: 'from-slate-500 to-gray-500',
  };

  const gradientColor = typeColors[recommendation.type] || typeColors.low;

  return (
    <div className="bg-slate-800/60 backdrop-blur border border-slate-700/50 rounded-xl p-4 hover:border-cyan-500/50 transition-all duration-300 group">
      <div className="flex items-start gap-3">
        <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${gradientColor} flex items-center justify-center text-white font-mono text-sm font-bold flex-shrink-0`}>
          {rank}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-mono text-slate-400">{recommendation.project}</span>
            {recommendation.type === 'revenue' && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-green-500/20 text-green-300 font-medium">
                💰 REVENUE
              </span>
            )}
          </div>
          <h3 className="text-sm font-semibold text-white mb-1 group-hover:text-cyan-300 transition-colors">
            {recommendation.action}
          </h3>
          <p className="text-xs text-slate-400 line-clamp-2">{recommendation.impact}</p>
          <div className="mt-2 text-xs text-slate-500">
            <span className="font-mono">Score: {recommendation.monetization_score || 0}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

interface FilterButtonProps {
  active: boolean;
  onClick: () => void;
  label: string;
  count: number;
  color?: string;
}

function FilterButton({ active, onClick, label, count, color = 'cyan' }: FilterButtonProps) {
  const colorClasses: Record<string, string> = {
    cyan: 'from-cyan-500 to-blue-500',
    green: 'from-green-500 to-emerald-500',
    slate: 'from-slate-600 to-slate-700',
    purple: 'from-purple-500 to-violet-500',
    emerald: 'from-emerald-500 to-green-500',
  };

  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 rounded-lg font-medium text-sm transition-all duration-300 ${
        active
          ? `bg-gradient-to-r ${colorClasses[color]} text-white shadow-lg`
          : 'bg-slate-800/50 text-slate-400 hover:bg-slate-800 hover:text-white'
      }`}
    >
      {label} <span className="font-mono ml-1">({count})</span>
    </button>
  );
}

interface ProjectCardProps {
  project: Project;
}

function ProjectCard({ project }: ProjectCardProps) {
  const scoreColor = (score: number) => {
    if (score >= 70) return 'from-green-500 to-emerald-500';
    if (score >= 40) return 'from-cyan-500 to-blue-500';
    return 'from-slate-600 to-slate-700';
  };

  const statusColors: Record<string, { bg: string; text: string }> = {
    ready: { bg: 'bg-green-500/20', text: 'text-green-300' },
    launched: { bg: 'bg-emerald-500/20', text: 'text-emerald-300' },
    in_progress: { bg: 'bg-cyan-500/20', text: 'text-cyan-300' },
    planning: { bg: 'bg-yellow-500/20', text: 'text-yellow-300' },
    archived: { bg: 'bg-slate-500/20', text: 'text-slate-300' },
  };

  const priorityColors: Record<number, string> = {
    1: 'from-green-500 to-emerald-500',
    2: 'from-cyan-500 to-blue-500',
    3: 'from-yellow-500 to-amber-500',
    4: 'from-orange-500 to-red-500',
    5: 'from-slate-500 to-slate-600',
  };

  const displayName = project.display_name || project.name;
  const status = project.project_status || 'in_progress';
  const statusStyle = statusColors[status] || statusColors.in_progress;
  const techStack = project.tech_stack_override || project.monetization.tech_stack;
  const completion = project.completion ?? project.health.score;

  return (
    <div className={`bg-gradient-to-br from-slate-900/80 to-slate-800/80 backdrop-blur-xl rounded-2xl border overflow-hidden transition-all duration-300 group ${
      project.has_metadata ? 'border-cyan-500/30 hover:border-cyan-400/60' : 'border-slate-700/50 hover:border-slate-600/70'
    }`}>
      {/* Header */}
      <div className="p-5 border-b border-slate-700/50">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              {project.has_metadata && project.priority && (
                <span className={`text-xs px-2 py-0.5 rounded font-mono font-bold bg-gradient-to-r ${priorityColors[project.priority]} text-white`}>
                  P{project.priority}
                </span>
              )}
              <span className={`text-xs px-2 py-0.5 rounded-full ${statusStyle.bg} ${statusStyle.text} font-medium capitalize`}>
                {status.replace('_', ' ')}
              </span>
              {project.has_metadata && (
                <span className="text-xs px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 font-mono">
                  META
                </span>
              )}
            </div>
            <h3 className="text-xl font-bold text-white mb-1 truncate group-hover:text-cyan-300 transition-colors">
              {displayName}
            </h3>
            <p className="text-xs text-slate-400 font-mono">{project.type}</p>
          </div>
          <div className={`ml-3 w-16 h-16 rounded-xl bg-gradient-to-br ${scoreColor(project.monetization.score)} flex items-center justify-center flex-shrink-0`}>
            <div className="text-center">
              <div className="text-2xl font-black text-white font-mono">{project.monetization.score}</div>
              <div className="text-[8px] text-white/70 uppercase tracking-wider">Score</div>
            </div>
          </div>
        </div>

        {/* Description (if has metadata) */}
        {project.description && (
          <p className="text-xs text-slate-400 mb-3 line-clamp-2">{project.description}</p>
        )}

        {/* Revenue Metadata (if has metadata) */}
        {project.revenue_metadata && (
          <div className="flex flex-wrap gap-2 mb-3">
            <span className="text-xs px-2 py-1 rounded-md bg-green-500/10 text-green-300 font-mono">
              MRR: {project.revenue_metadata.mrr_potential}
            </span>
            {project.time_to_launch && (
              <span className="text-xs px-2 py-1 rounded-md bg-cyan-500/10 text-cyan-300 font-mono">
                Launch: {project.time_to_launch}
              </span>
            )}
          </div>
        )}

        {/* Revenue Streams */}
        {project.monetization.revenue_streams.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {project.monetization.revenue_streams.slice(0, 3).map((stream: string, idx: number) => (
              <span
                key={idx}
                className="text-[10px] px-2 py-1 rounded-full bg-green-500/20 text-green-300 font-medium"
              >
                {stream}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Blockers Section (if has blockers) */}
      {project.blockers && project.blockers.length > 0 && (
        <div className="px-4 py-3 border-b border-slate-700/50 bg-red-900/10">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs text-red-400 font-semibold uppercase tracking-wider">Blockers ({project.blockers.length})</span>
          </div>
          <div className="space-y-1">
            {project.blockers.slice(0, 2).map((blocker, idx) => (
              <div key={idx} className="flex items-center gap-2 text-xs">
                <span className={`w-1.5 h-1.5 rounded-full ${
                  blocker.severity === 'critical' ? 'bg-red-500' :
                  blocker.severity === 'high' ? 'bg-orange-500' :
                  blocker.severity === 'medium' ? 'bg-yellow-500' : 'bg-slate-500'
                }`} />
                <span className="text-slate-300 truncate">{blocker.title}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Completion & Git Status */}
      <div className="p-4 border-b border-slate-700/50 bg-slate-900/30">
        {/* Completion Bar */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-slate-500 uppercase tracking-wider">Completion</span>
            <span className="text-xs font-mono text-slate-300">{completion}%</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
            <div
              className={`h-full rounded-full bg-gradient-to-r ${
                completion >= 90 ? 'from-green-500 to-emerald-500' :
                completion >= 70 ? 'from-cyan-500 to-blue-500' :
                completion >= 50 ? 'from-yellow-500 to-amber-500' : 'from-red-500 to-rose-500'
              }`}
              style={{ width: `${completion}%` }}
            />
          </div>
        </div>

        <div className="grid grid-cols-4 gap-3 text-center font-mono text-xs">
          <GitStat icon="📝" value={project.git.modified} label="Modified" />
          <GitStat icon="❓" value={project.git.untracked} label="New" />
          <GitStat icon="↑" value={project.git.ahead} label="Ahead" color="green" />
          <GitStat icon="↓" value={project.git.behind} label="Behind" color="red" />
        </div>
      </div>

      {/* Links & Tech */}
      <div className="p-4">
        {/* Links (if has metadata with links) */}
        {project.links && Object.keys(project.links).length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            {project.links.production && (
              <a href={project.links.production} target="_blank" rel="noopener noreferrer"
                className="text-xs px-2 py-1 rounded-md bg-green-500/10 text-green-300 hover:bg-green-500/20 transition-colors">
                Production
              </a>
            )}
            {project.links.staging && (
              <a href={project.links.staging} target="_blank" rel="noopener noreferrer"
                className="text-xs px-2 py-1 rounded-md bg-cyan-500/10 text-cyan-300 hover:bg-cyan-500/20 transition-colors">
                Staging
              </a>
            )}
            {project.links.docs && (
              <a href={project.links.docs} target="_blank" rel="noopener noreferrer"
                className="text-xs px-2 py-1 rounded-md bg-blue-500/10 text-blue-300 hover:bg-blue-500/20 transition-colors">
                Docs
              </a>
            )}
          </div>
        )}

        {/* Tech Stack Tags */}
        {techStack.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {techStack.slice(0, 6).map((tech: string, idx: number) => (
              <span
                key={idx}
                className="text-[10px] px-2 py-1 rounded-md bg-slate-800 text-slate-300 font-mono"
              >
                {tech}
              </span>
            ))}
          </div>
        )}

        {/* Stakeholder Notes */}
        {project.stakeholder_notes && (
          <div className="mt-3 pt-3 border-t border-slate-800">
            <p className="text-xs text-slate-400 italic line-clamp-2">{project.stakeholder_notes}</p>
          </div>
        )}
      </div>
    </div>
  );
}

interface GitStatProps {
  icon: string;
  value: number;
  label: string;
  color?: string;
}

function GitStat({ icon, value, label, color = 'slate' }: GitStatProps) {
  const textColor = color === 'green' ? 'text-green-400' : color === 'red' ? 'text-red-400' : 'text-slate-400';

  return (
    <div>
      <div className="text-sm mb-1">{icon}</div>
      <div className={`font-bold ${textColor}`}>{value}</div>
      <div className="text-[10px] text-slate-500 uppercase tracking-wider">{label}</div>
    </div>
  );
}
