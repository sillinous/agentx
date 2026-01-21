"use client";

import { NextAction } from "@/lib/api";

interface NextActionsProps {
  actions: NextAction[];
}

export default function NextActions({ actions }: NextActionsProps) {
  const priorityConfig: Record<string, { label: string; color: string; bg: string }> = {
    critical: {
      label: "CRITICAL",
      color: "border-danger text-danger",
      bg: "bg-danger/10",
    },
    high: {
      label: "HIGH",
      color: "border-warning text-warning",
      bg: "bg-warning/10",
    },
    medium: {
      label: "MEDIUM",
      color: "border-blue-400 text-blue-400",
      bg: "bg-blue-400/10",
    },
    low: {
      label: "LOW",
      color: "border-zinc-400 text-zinc-400",
      bg: "bg-zinc-400/10",
    },
  };

  return (
    <div className="data-card p-8 rounded-lg">
      <h2 className="font-display text-4xl font-bold mb-6">
        <span className="text-gradient">Next Actions</span>
      </h2>

      <div className="space-y-4">
        {actions.map((action, index) => {
          const config = priorityConfig[action.priority] || priorityConfig.medium;
          return (
            <div
              key={index}
              className={`border-l-4 ${config.color} ${config.bg} p-4 rounded-r-lg animate-slide-up`}
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-3 flex-wrap">
                  <span
                    className={`text-xs font-bold px-2 py-0.5 rounded ${config.bg} ${config.color} uppercase tracking-wider`}
                  >
                    {config.label}
                  </span>
                  {action.project && (
                    <span className="text-xs font-mono text-cyan-400 bg-cyan-400/10 px-2 py-0.5 rounded">
                      {action.project}
                    </span>
                  )}
                  <h3 className="font-display text-lg font-semibold">
                    {action.title}
                  </h3>
                </div>
                <span className="text-sm font-mono text-zinc-400 whitespace-nowrap ml-4">
                  {action.time_estimate}
                </span>
              </div>
              <p className="text-sm text-zinc-400 leading-relaxed">
                {action.description}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
