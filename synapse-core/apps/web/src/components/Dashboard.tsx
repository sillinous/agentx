'use client';

import { Activity, Cpu } from 'lucide-react';

// KPI Card
export interface KPIData {
  title: string;
  value: string;
  trend: string;
  color: string;
}

interface KPICardProps {
  data: KPIData;
}

export function KPICard({ data }: KPICardProps) {
  return (
    <div className="bg-slate-900/50 border border-white/5 p-6 rounded-2xl hover:border-cyan-500/30 transition-colors group">
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-slate-400 text-sm font-medium">{data.title}</h3>
        <div className={`text-xs px-2 py-1 rounded bg-white/5 ${data.color}`}>
          {data.trend}
        </div>
      </div>
      <div className="text-3xl font-bold text-white group-hover:text-cyan-50 group-hover:drop-shadow-[0_0_10px_rgba(0,240,255,0.3)] transition-all">
        {data.value}
      </div>
    </div>
  );
}

// KPI Row
interface KPIRowProps {
  data: KPIData[];
}

export function KPIRow({ data }: KPIRowProps) {
  return (
    <div className="col-span-12 grid grid-cols-3 gap-6">
      {data.map((kpi, idx) => (
        <KPICard key={idx} data={kpi} />
      ))}
    </div>
  );
}

// Revenue Chart
export function RevenueChart() {
  const data = [40, 60, 45, 70, 85, 60, 75, 50, 65, 90, 80, 95];

  return (
    <div className="col-span-8 bg-slate-900/50 border border-white/5 rounded-2xl p-6 relative overflow-hidden">
      <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/5 blur-3xl rounded-full pointer-events-none"></div>
      <h3 className="text-lg font-medium mb-6 flex items-center gap-2">
        <Activity className="w-4 h-4 text-cyan-400" /> Revenue Velocity
      </h3>
      <div className="h-64 flex items-end justify-between gap-2 opacity-80">
        {data.map((h, i) => (
          <div
            key={i}
            style={{ height: `${h}%` }}
            className="w-full bg-slate-700 rounded-t-sm hover:bg-cyan-500 transition-colors"
          ></div>
        ))}
      </div>
    </div>
  );
}

// Activity Feed Item
export interface ActivityItem {
  agent: string;
  action: string;
  time: string;
  type: 'alert' | 'success' | 'info';
}

interface ActivityFeedItemProps {
  item: ActivityItem;
}

export function ActivityFeedItem({ item }: ActivityFeedItemProps) {
  return (
    <div className="p-3 rounded-lg bg-white/5 border border-white/5 text-sm">
      <div className="flex justify-between items-center mb-1">
        <span className="font-mono text-xs text-cyan-400 uppercase tracking-wider">
          {item.agent}
        </span>
        <span className="text-xs text-slate-500">{item.time}</span>
      </div>
      <p className="text-slate-300">{item.action}</p>
    </div>
  );
}

// Activity Feed
interface ActivityFeedProps {
  items: ActivityItem[];
}

export function ActivityFeed({ items }: ActivityFeedProps) {
  return (
    <div className="col-span-4 bg-slate-900/50 border border-white/5 rounded-2xl p-6 flex flex-col">
      <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
        <Cpu className="w-4 h-4 text-amber-400" /> Agent Feed
      </h3>
      <div className="flex-1 overflow-y-auto space-y-4 pr-2">
        {items.map((item, idx) => (
          <ActivityFeedItem key={idx} item={item} />
        ))}
      </div>
    </div>
  );
}

// Control Dashboard - combines all dashboard components
interface ControlDashboardProps {
  kpiData: KPIData[];
  activityFeed: ActivityItem[];
}

export function ControlDashboard({ kpiData, activityFeed }: ControlDashboardProps) {
  return (
    <div className="max-w-7xl mx-auto h-full grid grid-cols-12 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <KPIRow data={kpiData} />
      <RevenueChart />
      <ActivityFeed items={activityFeed} />
    </div>
  );
}

export default ControlDashboard;
