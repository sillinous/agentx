import { Link, useLocation } from 'react-router-dom';
import { useMemo } from 'react';

interface BreadcrumbItem {
  label: string;
  href?: string;
}

// Route to breadcrumb label mapping
const routeLabels: Record<string, string> = {
  '': 'Dashboard',
  'portfolio': 'Portfolio',
  'agents': 'Agents',
  'workflows': 'Workflows',
  'builder': 'Builder',
  'integrations': 'Integrations',
  'human-actions': 'Human Actions',
  'health': 'System Health',
  'handbook': 'Handbook',
  'settings': 'Settings',
  'evaluations': 'Evaluations',
};

interface BreadcrumbsProps {
  customItems?: BreadcrumbItem[];
  className?: string;
}

export default function Breadcrumbs({ customItems, className = '' }: BreadcrumbsProps) {
  const location = useLocation();

  const items = useMemo(() => {
    if (customItems) return customItems;

    const pathSegments = location.pathname.split('/').filter(Boolean);
    const breadcrumbs: BreadcrumbItem[] = [
      { label: 'Home', href: '/' },
    ];

    let currentPath = '';
    pathSegments.forEach((segment, index) => {
      currentPath += `/${segment}`;
      const isLast = index === pathSegments.length - 1;

      // Check if this segment looks like an ID (UUID or slug with dashes)
      const isId = segment.includes('-') && segment.length > 20;

      const label = isId
        ? segment.split('-').slice(0, 2).join(' ').replace(/\b\w/g, c => c.toUpperCase())
        : routeLabels[segment] || segment.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

      breadcrumbs.push({
        label,
        href: isLast ? undefined : currentPath,
      });
    });

    return breadcrumbs;
  }, [location.pathname, customItems]);

  // Don't show breadcrumbs on the dashboard
  if (location.pathname === '/') return null;

  return (
    <nav aria-label="Breadcrumb" className={`mb-4 ${className}`}>
      <ol className="flex items-center gap-2 text-sm">
        {items.map((item, index) => {
          const isLast = index === items.length - 1;

          return (
            <li key={index} className="flex items-center gap-2">
              {index > 0 && (
                <svg
                  className="w-4 h-4 text-gray-400 dark:text-gray-500 flex-shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              )}
              {item.href && !isLast ? (
                <Link
                  to={item.href}
                  className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
                >
                  {item.label}
                </Link>
              ) : (
                <span className={`${isLast ? 'text-gray-900 dark:text-white font-medium' : 'text-gray-500 dark:text-gray-400'}`}>
                  {item.label}
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
