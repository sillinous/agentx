"use client";

import { useEffect, useState } from "react";

interface StatusIndicatorProps {
  apiHealthy: boolean;
  lastUpdated: string;
}

export default function StatusIndicator({
  apiHealthy,
  lastUpdated,
}: StatusIndicatorProps) {
  const [timeAgo, setTimeAgo] = useState("");

  useEffect(() => {
    const updateTimeAgo = () => {
      const now = new Date();
      const updated = new Date(lastUpdated);
      const diffMs = now.getTime() - updated.getTime();
      const diffSec = Math.floor(diffMs / 1000);

      if (diffSec < 60) {
        setTimeAgo(`${diffSec}s ago`);
      } else if (diffSec < 3600) {
        setTimeAgo(`${Math.floor(diffSec / 60)}m ago`);
      } else {
        setTimeAgo(`${Math.floor(diffSec / 3600)}h ago`);
      }
    };

    updateTimeAgo();
    const interval = setInterval(updateTimeAgo, 1000);
    return () => clearInterval(interval);
  }, [lastUpdated]);

  return (
    <div className="flex items-center gap-6">
      <div className="flex items-center gap-2">
        <div
          className={`w-3 h-3 rounded-full ${
            apiHealthy
              ? "bg-primary animate-pulse-slow"
              : "bg-danger animate-pulse"
          }`}
        />
        <span className="text-sm font-mono">
          API: {apiHealthy ? "ONLINE" : "OFFLINE"}
        </span>
      </div>
      <div className="text-sm text-zinc-500 font-mono">
        Updated {timeAgo}
      </div>
    </div>
  );
}
