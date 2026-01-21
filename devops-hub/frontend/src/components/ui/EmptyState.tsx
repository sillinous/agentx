/**
 * EmptyState - Contextual empty states with actionable guidance
 * 
 * Design: Refined minimalism with clear visual hierarchy and helpful CTAs
 */

import type { ReactNode } from 'react';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
    variant?: 'primary' | 'secondary';
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
  illustration?: 'agents' | 'workflows' | 'search' | 'error' | 'docs' | 'generic';
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  secondaryAction,
  illustration = 'generic',
  className = '',
}: EmptyStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center py-16 px-6 text-center ${className}`}
      role="status"
      aria-live="polite"
    >
      {/* Illustration or Icon */}
      <div className="mb-6">
        {icon || <EmptyStateIllustration type={illustration} />}
      </div>

      {/* Title */}
      <h3 className="text-xl font-semibold text-gray-900 mb-2">
        {title}
      </h3>

      {/* Description */}
      {description && (
        <p className="text-gray-600 max-w-md mb-8 leading-relaxed">
          {description}
        </p>
      )}

      {/* Actions */}
      {(action || secondaryAction) && (
        <div className="flex flex-col sm:flex-row gap-3">
          {action && (
            <button
              onClick={action.onClick}
              className={`
                px-6 py-2.5 rounded-lg font-medium transition-all duration-200
                ${action.variant === 'secondary'
                  ? 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                  : 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm hover:shadow-md'
                }
              `}
            >
              {action.label}
            </button>
          )}
          {secondaryAction && (
            <button
              onClick={secondaryAction.onClick}
              className="px-6 py-2.5 rounded-lg font-medium text-gray-700 hover:text-gray-900 transition-colors"
            >
              {secondaryAction.label}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Illustrations for different empty state types
 */
function EmptyStateIllustration({ type }: { type: string }) {
  const illustrations = {
    agents: (
      <svg className="w-24 h-24 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
    workflows: (
      <svg className="w-24 h-24 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
      </svg>
    ),
    search: (
      <svg className="w-24 h-24 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    ),
    error: (
      <svg className="w-24 h-24 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    docs: (
      <svg className="w-24 h-24 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
      </svg>
    ),
    generic: (
      <svg className="w-24 h-24 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
      </svg>
    ),
  };

  return illustrations[type as keyof typeof illustrations] || illustrations.generic;
}

/**
 * Pre-composed empty state variants for common scenarios
 */
export function NoAgentsFound({ onCreateAgent }: { onCreateAgent?: () => void }) {
  return (
    <EmptyState
      illustration="agents"
      title="No agents found"
      description="Get started by registering your first agent or try adjusting your search filters."
      action={onCreateAgent ? {
        label: 'Register Agent',
        onClick: onCreateAgent,
      } : undefined}
      secondaryAction={{
        label: 'View Documentation',
        onClick: () => window.open('/docs', '_blank'),
      }}
    />
  );
}

export function NoWorkflowsFound({ onCreateWorkflow }: { onCreateWorkflow?: () => void }) {
  return (
    <EmptyState
      illustration="workflows"
      title="No workflows yet"
      description="Workflows let you chain multiple agents together. Create your first workflow to automate complex tasks."
      action={onCreateWorkflow ? {
        label: 'Create Workflow',
        onClick: onCreateWorkflow,
      } : undefined}
      secondaryAction={{
        label: 'Browse Templates',
        onClick: () => console.log('Browse templates'),
      }}
    />
  );
}

export function SearchNoResults({ query }: { query: string }) {
  return (
    <EmptyState
      illustration="search"
      title="No results found"
      description={`We couldn't find anything matching "${query}". Try different keywords or check your spelling.`}
    />
  );
}

export function ErrorState({ message, onRetry }: { message?: string; onRetry?: () => void }) {
  return (
    <EmptyState
      illustration="error"
      title="Something went wrong"
      description={message || "We're having trouble loading this content. Please try again."}
      action={onRetry ? {
        label: 'Try Again',
        onClick: onRetry,
        variant: 'primary',
      } : undefined}
      secondaryAction={{
        label: 'Contact Support',
        onClick: () => window.open('/support', '_blank'),
      }}
    />
  );
}
