"use client";

import { RevenueMetrics } from "@/lib/api";

interface RevenueOverviewProps {
  revenue: RevenueMetrics;
}

export default function RevenueOverview({ revenue }: RevenueOverviewProps) {
  return (
    <div className="data-card p-8 rounded-lg">
      <h2 className="font-display text-4xl font-bold mb-6 text-gradient">
        Portfolio Overview
      </h2>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <MetricCard
          label="Current MRR"
          value={`$${revenue.current_mrr.toLocaleString()}`}
          color="text-primary"
        />
        <MetricCard
          label="Ready to Launch"
          value={String(revenue.ready_to_launch)}
          color="text-green-400"
          highlight={revenue.ready_to_launch > 0}
        />
        <MetricCard
          label="Launched"
          value={String(revenue.launched)}
          color="text-cyan-400"
        />
        <MetricCard
          label="With Metadata"
          value={String(revenue.projects_with_metadata)}
          color="text-purple-400"
        />
      </div>

      <div className="grid grid-cols-3 gap-4 pt-6 border-t border-zinc-800">
        <div>
          <div className="text-sm text-zinc-500 uppercase mb-2">
            Total Projects
          </div>
          <div className="text-3xl font-bold">
            {revenue.total_projects}
          </div>
        </div>
        <div>
          <div className="text-sm text-zinc-500 uppercase mb-2">
            Active Streams
          </div>
          <div className="text-3xl font-bold">
            {revenue.active_streams}
          </div>
        </div>
        <div>
          <div className="text-sm text-zinc-500 uppercase mb-2">
            Metadata Coverage
          </div>
          <div className="text-3xl font-bold text-purple-400">
            {revenue.total_projects > 0
              ? Math.round(
                  (revenue.projects_with_metadata / revenue.total_projects) * 100
                )
              : 0}
            %
          </div>
        </div>
      </div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  color,
  highlight,
}: {
  label: string;
  value: string;
  color: string;
  highlight?: boolean;
}) {
  return (
    <div className={`space-y-2 ${highlight ? "animate-pulse" : ""}`}>
      <div className="text-xs text-zinc-500 uppercase tracking-wider">
        {label}
      </div>
      <div className={`text-2xl lg:text-3xl font-bold ${color}`}>{value}</div>
    </div>
  );
}
