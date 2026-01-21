"use client";

import { ProjectStatus } from "@/lib/api";

interface ProjectCardProps {
  project: ProjectStatus;
  index: number;
}

export default function ProjectCard({ project, index }: ProjectCardProps) {
  const statusColors: Record<string, string> = {
    ready: "text-primary border-primary bg-primary/10",
    launched: "text-green-400 border-green-400 bg-green-400/10",
    in_progress: "text-warning border-warning bg-warning/10",
    planning: "text-zinc-500 border-zinc-500 bg-zinc-500/10",
    archived: "text-zinc-600 border-zinc-600 bg-zinc-600/10",
  };

  const priorityLabels = ["🚀 P1", "⚡ P2", "📋 P3", "📝 P4", "📄 P5"];

  return (
    <div
      className={`data-card p-6 rounded-lg animate-fade-in ${
        project.has_metadata ? "ring-1 ring-cyan-500/30" : ""
      }`}
      style={{ animationDelay: `${index * 0.1}s` }}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <span
              className={`text-xs font-semibold uppercase tracking-wider px-2 py-0.5 rounded ${
                statusColors[project.status] || statusColors.in_progress
              }`}
            >
              {project.status.replace("_", " ")}
            </span>
            {project.has_metadata && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 font-mono">
                META
              </span>
            )}
          </div>
          <h3 className="font-display text-2xl font-bold mb-1 truncate">
            {project.name}
          </h3>
          {project.description && (
            <p className="text-sm text-zinc-400 line-clamp-2 mb-2">
              {project.description}
            </p>
          )}
        </div>
        <span className="text-2xl ml-3 flex-shrink-0">
          {priorityLabels[project.priority - 1] || priorityLabels[4]}
        </span>
      </div>

      <div className="space-y-3">
        <div>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-zinc-400">Completion</span>
            <span className="text-primary font-semibold">
              {project.completion}%
            </span>
          </div>
          <div className="h-2 bg-zinc-900 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${
                project.completion >= 90
                  ? "bg-gradient-to-r from-green-500 to-emerald-400"
                  : project.completion >= 70
                  ? "bg-gradient-to-r from-primary to-blue-400"
                  : project.completion >= 50
                  ? "bg-gradient-to-r from-yellow-500 to-amber-400"
                  : "bg-gradient-to-r from-red-500 to-rose-400"
              }`}
              style={{ width: `${project.completion}%` }}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 pt-2">
          <div>
            <div className="text-xs text-zinc-500 uppercase mb-1">
              MRR Potential
            </div>
            <div className="text-lg font-bold text-gradient">
              {project.mrr_potential}
            </div>
          </div>
          <div>
            <div className="text-xs text-zinc-500 uppercase mb-1">Blockers</div>
            <div
              className={`text-lg font-bold ${
                project.blockers === 0 ? "text-primary" : "text-danger"
              }`}
            >
              {project.blockers}
            </div>
          </div>
        </div>

        <div className="pt-2 border-t border-zinc-800">
          <div className="flex justify-between items-center">
            <div>
              <div className="text-xs text-zinc-500 uppercase mb-1">
                Time to Launch
              </div>
              <div className="text-sm font-semibold">{project.time_to_launch}</div>
            </div>
            {project.links?.production && (
              <a
                href={project.links.production}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs px-2 py-1 rounded bg-green-500/10 text-green-400 hover:bg-green-500/20 transition-colors"
              >
                View Live →
              </a>
            )}
          </div>
        </div>

        {project.stakeholder_notes && (
          <div className="pt-2 border-t border-zinc-800">
            <p className="text-xs text-zinc-400 italic line-clamp-2">
              {project.stakeholder_notes}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
