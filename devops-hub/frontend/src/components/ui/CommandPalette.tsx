/* eslint-disable react-refresh/only-export-components */
import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDiscoverAgents, useWorkflows } from '../../api/hooks';

interface CommandItem {
  id: string;
  title: string;
  subtitle?: string;
  icon: string;
  action: () => void;
  category: 'navigation' | 'agents' | 'workflows' | 'actions';
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const { data: agentsResponse } = useDiscoverAgents({});
  const { data: workflowsResponse } = useWorkflows();

  const navigationItems: CommandItem[] = useMemo(() => [
    { id: 'nav-dashboard', title: 'Dashboard', subtitle: 'Overview and statistics', icon: '📊', action: () => navigate('/'), category: 'navigation' },
    { id: 'nav-portfolio', title: 'Portfolio', subtitle: 'Project portfolio', icon: '💼', action: () => navigate('/portfolio'), category: 'navigation' },
    { id: 'nav-agents', title: 'Agents', subtitle: 'Browse and manage agents', icon: '🤖', action: () => navigate('/agents'), category: 'navigation' },
    { id: 'nav-workflows', title: 'Workflows', subtitle: 'Multi-agent workflows', icon: '🔄', action: () => navigate('/workflows'), category: 'navigation' },
    { id: 'nav-workflow-builder', title: 'Workflow Builder', subtitle: 'Create custom workflows', icon: '🛠️', action: () => navigate('/workflows/builder'), category: 'navigation' },
    { id: 'nav-integrations', title: 'Integrations', subtitle: 'External connections', icon: '🔌', action: () => navigate('/integrations'), category: 'navigation' },
    { id: 'nav-human-actions', title: 'Human Actions', subtitle: 'HITL requests', icon: '👤', action: () => navigate('/human-actions'), category: 'navigation' },
    { id: 'nav-health', title: 'System Health', subtitle: 'Monitor system status', icon: '💚', action: () => navigate('/health'), category: 'navigation' },
    { id: 'nav-handbook', title: 'Handbook', subtitle: 'Documentation', icon: '📚', action: () => navigate('/handbook'), category: 'navigation' },
    { id: 'nav-settings', title: 'Settings', subtitle: 'Configuration', icon: '⚙️', action: () => navigate('/settings'), category: 'navigation' },
  ], [navigate]);

  const agentItems: CommandItem[] = useMemo(() =>
    (agentsResponse?.agents || []).map(agent => ({
      id: `agent-${agent.id}`,
      title: agent.name,
      subtitle: agent.description,
      icon: '🤖',
      action: () => navigate(`/agents/${agent.id}`),
      category: 'agents' as const,
    })),
  [agentsResponse, navigate]);

  const workflowItems: CommandItem[] = useMemo(() =>
    (workflowsResponse || []).map(workflow => ({
      id: `workflow-${workflow.id}`,
      title: workflow.name,
      subtitle: workflow.description || `${workflow.steps_count || 0} steps`,
      icon: '🔄',
      action: () => navigate(`/workflows/${workflow.id}`),
      category: 'workflows' as const,
    })),
  [workflowsResponse, navigate]);

  const actionItems: CommandItem[] = useMemo(() => [
    { id: 'action-api-docs', title: 'Open API Docs', subtitle: 'Swagger documentation', icon: '📄', action: () => window.open('/api/docs', '_blank'), category: 'actions' },
    { id: 'action-theme', title: 'Toggle Dark Mode', subtitle: 'Switch theme', icon: '🌙', action: () => {
      const event = new CustomEvent('toggle-theme');
      window.dispatchEvent(event);
      onClose();
    }, category: 'actions' },
  ], [onClose]);

  const allItems = useMemo(() => [
    ...navigationItems,
    ...agentItems,
    ...workflowItems,
    ...actionItems,
  ], [navigationItems, agentItems, workflowItems, actionItems]);

  const filteredItems = useMemo(() => {
    if (!query.trim()) return allItems.slice(0, 10);
    const lowerQuery = query.toLowerCase();
    return allItems.filter(item =>
      item.title.toLowerCase().includes(lowerQuery) ||
      item.subtitle?.toLowerCase().includes(lowerQuery)
    ).slice(0, 15);
  }, [query, allItems]);

  const groupedItems = useMemo(() => {
    const groups: Record<string, CommandItem[]> = {};
    filteredItems.forEach(item => {
      if (!groups[item.category]) groups[item.category] = [];
      groups[item.category].push(item);
    });
    return groups;
  }, [filteredItems]);

  const flatItems = useMemo(() => filteredItems, [filteredItems]);

  // Reset selection when query changes
  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
      setQuery('');
      setSelectedIndex(0);
    }
  }, [isOpen]);

  // Scroll selected item into view
  useEffect(() => {
    if (listRef.current && flatItems.length > 0) {
      const selectedElement = listRef.current.querySelector(`[data-index="${selectedIndex}"]`);
      selectedElement?.scrollIntoView({ block: 'nearest' });
    }
  }, [selectedIndex, flatItems]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => Math.min(prev + 1, flatItems.length - 1));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => Math.max(prev - 1, 0));
        break;
      case 'Enter':
        e.preventDefault();
        if (flatItems[selectedIndex]) {
          flatItems[selectedIndex].action();
          onClose();
        }
        break;
      case 'Escape':
        e.preventDefault();
        onClose();
        break;
    }
  }, [flatItems, selectedIndex, onClose]);

  const handleItemClick = useCallback((item: CommandItem) => {
    item.action();
    onClose();
  }, [onClose]);

  const getCategoryLabel = (category: string) => {
    const labels: Record<string, string> = {
      navigation: 'Navigation',
      agents: 'Agents',
      workflows: 'Workflows',
      actions: 'Actions',
    };
    return labels[category] || category;
  };

  if (!isOpen) return null;

  let itemIndex = -1;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-50"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div className="fixed inset-x-4 top-[15%] sm:inset-x-auto sm:left-1/2 sm:-translate-x-1/2 sm:w-full sm:max-w-xl z-50">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          {/* Search input */}
          <div className="flex items-center px-4 border-b border-gray-200 dark:border-gray-700">
            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Search pages, agents, workflows..."
              className="w-full px-3 py-4 text-gray-900 dark:text-white placeholder-gray-400 bg-transparent outline-none"
            />
            <kbd className="hidden sm:inline-flex items-center px-2 py-1 text-xs text-gray-400 bg-gray-100 dark:bg-gray-700 rounded">
              ESC
            </kbd>
          </div>

          {/* Results */}
          <div ref={listRef} className="max-h-80 overflow-y-auto py-2">
            {flatItems.length === 0 ? (
              <div className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                No results found for "{query}"
              </div>
            ) : (
              Object.entries(groupedItems).map(([category, items]) => (
                <div key={category}>
                  <div className="px-4 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    {getCategoryLabel(category)}
                  </div>
                  {items.map((item) => {
                    itemIndex++;
                    const currentIndex = itemIndex;
                    return (
                      <button
                        key={item.id}
                        data-index={currentIndex}
                        onClick={() => handleItemClick(item)}
                        className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors ${
                          selectedIndex === currentIndex
                            ? 'bg-blue-50 dark:bg-blue-900/30'
                            : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
                        }`}
                      >
                        <span className="flex-shrink-0 text-lg">{item.icon}</span>
                        <div className="flex-grow min-w-0">
                          <div className={`font-medium truncate ${
                            selectedIndex === currentIndex
                              ? 'text-blue-600 dark:text-blue-400'
                              : 'text-gray-900 dark:text-white'
                          }`}>
                            {item.title}
                          </div>
                          {item.subtitle && (
                            <div className="text-sm text-gray-500 dark:text-gray-400 truncate">
                              {item.subtitle}
                            </div>
                          )}
                        </div>
                        {selectedIndex === currentIndex && (
                          <kbd className="hidden sm:inline-flex flex-shrink-0 items-center px-2 py-1 text-xs text-gray-400 bg-gray-100 dark:bg-gray-700 rounded">
                            Enter
                          </kbd>
                        )}
                      </button>
                    );
                  })}
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
            <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1">
                  <kbd className="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded">↑</kbd>
                  <kbd className="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded">↓</kbd>
                  <span className="ml-1">Navigate</span>
                </span>
                <span className="flex items-center gap-1">
                  <kbd className="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded">Enter</kbd>
                  <span className="ml-1">Select</span>
                </span>
              </div>
              <span>{flatItems.length} results</span>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

// Hook to manage command palette state
export function useCommandPalette() {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      // Cmd+K (Mac) or Ctrl+K (Windows/Linux)
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen(prev => !prev);
      }
    }

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  return {
    isOpen,
    open: () => setIsOpen(true),
    close: () => setIsOpen(false),
    toggle: () => setIsOpen(prev => !prev),
  };
}
