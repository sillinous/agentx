'use client';

import { cn } from '@/lib/utils';
import { ReactNode } from 'react';

interface BadgeProps {
  children: ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'purple';
  size?: 'sm' | 'md';
  className?: string;
}

const variantClasses = {
  default: 'bg-gray-100 text-gray-800',
  success: 'bg-green-100 text-green-800',
  warning: 'bg-yellow-100 text-yellow-800',
  danger: 'bg-red-100 text-red-800',
  info: 'bg-blue-100 text-blue-800',
  purple: 'bg-purple-100 text-purple-800',
};

const sizeClasses = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-sm',
};

export function Badge({ children, variant = 'default', size = 'sm', className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center font-medium rounded-full',
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
    >
      {children}
    </span>
  );
}

export function TierBadge({ tier }: { tier: string }) {
  const variant = tier === 'tier1' ? 'success' : tier === 'tier2' ? 'warning' : 'default';
  const label = tier === 'tier1' ? 'Tier 1' : tier === 'tier2' ? 'Tier 2' : 'Tier 3';
  return <Badge variant={variant}>{label}</Badge>;
}

export function StatusBadge({ status }: { status: string }) {
  const variants: Record<string, BadgeProps['variant']> = {
    discovery: 'info',
    development: 'purple',
    ready: 'success',
    launched: 'success',
    pending: 'default',
    in_progress: 'warning',
    completed: 'success',
    blocked: 'danger',
  };
  return <Badge variant={variants[status] || 'default'}>{status.replace('_', ' ')}</Badge>;
}

export function PriorityBadge({ priority }: { priority: string }) {
  const variants: Record<string, BadgeProps['variant']> = {
    high: 'danger',
    medium: 'warning',
    low: 'default',
  };
  return <Badge variant={variants[priority] || 'default'}>{priority}</Badge>;
}
