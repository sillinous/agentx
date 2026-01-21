/**
 * Skeleton - Elegant loading placeholders with smooth shimmer effect
 * 
 * Design: Refined minimalism with subtle motion
 */

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'rectangular' | 'circular' | 'card';
  width?: string | number;
  height?: string | number;
  animation?: 'pulse' | 'shimmer' | 'none';
}

export function Skeleton({
  className = '',
  variant = 'text',
  width,
  height,
  animation = 'shimmer',
}: SkeletonProps) {
  const baseStyles = 'bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 bg-[length:200%_100%]';
  
  const variantStyles = {
    text: 'h-4 rounded',
    rectangular: 'rounded-md',
    circular: 'rounded-full',
    card: 'rounded-lg',
  };

  const animationStyles = {
    pulse: 'animate-pulse',
    shimmer: 'animate-shimmer',
    none: '',
  };

  const style: React.CSSProperties = {};
  if (width) style.width = typeof width === 'number' ? `${width}px` : width;
  if (height) style.height = typeof height === 'number' ? `${height}px` : height;

  return (
    <div
      className={`${baseStyles} ${variantStyles[variant]} ${animationStyles[animation]} ${className}`}
      style={style}
      role="status"
      aria-label="Loading..."
    />
  );
}

/**
 * SkeletonCard - Pre-composed card skeleton
 */
interface SkeletonCardProps {
  className?: string;
  style?: React.CSSProperties;
}

export function SkeletonCard({ className = '', style }: SkeletonCardProps) {
  return (
    <div className={`p-6 border border-gray-200 dark:border-gray-700 rounded-lg space-y-4 bg-white dark:bg-gray-800 ${className}`} style={style}>
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-2 flex-1">
          <Skeleton variant="text" width="60%" height={20} />
          <Skeleton variant="text" width="40%" height={16} />
        </div>
        <Skeleton variant="circular" width={40} height={40} />
      </div>

      {/* Content */}
      <div className="space-y-2">
        <Skeleton variant="text" width="90%" />
        <Skeleton variant="text" width="75%" />
        <Skeleton variant="text" width="85%" />
      </div>

      {/* Footer */}
      <div className="flex gap-3 pt-2">
        <Skeleton variant="rectangular" width={80} height={32} className="rounded-full" />
        <Skeleton variant="rectangular" width={80} height={32} className="rounded-full" />
      </div>
    </div>
  );
}

/**
 * SkeletonList - Multiple skeleton cards
 */
interface SkeletonListProps {
  count?: number;
  className?: string;
}

export function SkeletonList({ count = 3, className = '' }: SkeletonListProps) {
  return (
    <div className={`space-y-4 ${className}`}>
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} style={{ animationDelay: `${i * 0.1}s` }} />
      ))}
    </div>
  );
}

/**
 * SkeletonTable - Table skeleton
 */
interface SkeletonTableProps {
  rows?: number;
  columns?: number;
  className?: string;
}

export function SkeletonTable({ rows = 5, columns = 4, className = '' }: SkeletonTableProps) {
  return (
    <div className={`space-y-3 ${className}`}>
      {/* Header */}
      <div className="flex gap-4 pb-3 border-b border-gray-200">
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={i} variant="text" width="25%" height={16} />
        ))}
      </div>

      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div
          key={rowIndex}
          className="flex gap-4"
          style={{ animationDelay: `${rowIndex * 0.05}s` }}
        >
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton
              key={colIndex}
              variant="text"
              width={`${20 + Math.random() * 10}%`}
              height={14}
            />
          ))}
        </div>
      ))}
    </div>
  );
}
