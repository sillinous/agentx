interface BadgeProps {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'purple';
  children: React.ReactNode;
  className?: string;
}

export default function Badge({ variant = 'default', children, className = '' }: BadgeProps) {
  const variants = {
    default: 'bg-gray-100 text-gray-800',
    success: 'bg-green-100 text-green-800',
    warning: 'bg-yellow-100 text-yellow-800',
    danger: 'bg-red-100 text-red-800',
    info: 'bg-blue-100 text-blue-800',
    purple: 'bg-purple-100 text-purple-800',
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${variants[variant]} ${className}`}
    >
      {children}
    </span>
  );
}

// Helper for status badges
export function StatusBadge({ status }: { status: string }) {
  const statusVariants: Record<string, BadgeProps['variant']> = {
    production: 'success',
    staging: 'warning',
    draft: 'default',
    deprecated: 'danger',
    retired: 'danger',
    running: 'info',
    completed: 'success',
    failed: 'danger',
    pending: 'default',
    paused: 'warning',
    cancelled: 'default',
    healthy: 'success',
    success: 'success',
    error: 'danger',
  };

  return <Badge variant={statusVariants[status] || 'default'}>{status}</Badge>;
}

// Helper for domain badges
export function DomainBadge({ domain }: { domain: string }) {
  const domainVariants: Record<string, BadgeProps['variant']> = {
    system: 'purple',
    business: 'info',
    utility: 'default',
  };

  return <Badge variant={domainVariants[domain] || 'default'}>{domain}</Badge>;
}

// Helper for type badges
export function TypeBadge({ type }: { type: string }) {
  const typeVariants: Record<string, BadgeProps['variant']> = {
    supervisor: 'purple',
    coordinator: 'info',
    worker: 'default',
    analyst: 'success',
  };

  return <Badge variant={typeVariants[type] || 'default'}>{type}</Badge>;
}
