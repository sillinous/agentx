import { useState } from 'react';
import { Card, Select, Input, SkeletonCard, NoAgentsFound, SearchNoResults, Breadcrumbs } from '../components/ui';
import { AgentCard } from '../components/agents';
import { useDiscoverAgents, useDomains, useCapabilities } from '../api/hooks';

export default function Agents() {
  const [filters, setFilters] = useState({
    domain: '',
    capability: '',
    status: 'production',
    agent_type: '',
  });
  const [search, setSearch] = useState('');

  const { data: domains } = useDomains();
  const { data: capabilities } = useCapabilities();
  const { data: response, isLoading } = useDiscoverAgents({
    domain: filters.domain || undefined,
    capability: filters.capability || undefined,
    status: filters.status || undefined,
    agent_type: filters.agent_type || undefined,
  });

  const filteredAgents =
    response?.agents.filter(
      (agent) =>
        agent.name.toLowerCase().includes(search.toLowerCase()) ||
        agent.description.toLowerCase().includes(search.toLowerCase())
    ) || [];

  return (
    <div className="space-y-6">
      <Breadcrumbs />

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Agents</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Discover and interact with available agents
        </p>
      </div>

      {/* Filters */}
      <Card>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <Input
            placeholder="Search agents..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <Select
            value={filters.domain}
            onChange={(e) => setFilters({ ...filters, domain: e.target.value })}
            options={[
              { value: '', label: 'All Domains' },
              ...(domains?.map((d) => ({ value: d, label: d })) || []),
            ]}
          />
          <Select
            value={filters.agent_type}
            onChange={(e) => setFilters({ ...filters, agent_type: e.target.value })}
            options={[
              { value: '', label: 'All Types' },
              { value: 'supervisor', label: 'Supervisor' },
              { value: 'coordinator', label: 'Coordinator' },
              { value: 'worker', label: 'Worker' },
              { value: 'analyst', label: 'Analyst' },
            ]}
          />
          <Select
            value={filters.capability}
            onChange={(e) => setFilters({ ...filters, capability: e.target.value })}
            options={[
              { value: '', label: 'All Capabilities' },
              ...(capabilities?.map((c) => ({ value: c, label: c })) || []),
            ]}
          />
          <Select
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
            options={[
              { value: '', label: 'All Status' },
              { value: 'production', label: 'Production' },
              { value: 'staging', label: 'Staging' },
              { value: 'draft', label: 'Draft' },
              { value: 'deprecated', label: 'Deprecated' },
            ]}
          />
        </div>
      </Card>

      {/* Results */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : filteredAgents.length > 0 ? (
        <>
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">
              Showing {filteredAgents.length} agent{filteredAgents.length !== 1 && 's'}
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredAgents.map((agent) => (
              <AgentCard key={agent.id} agent={agent} />
            ))}
          </div>
        </>
      ) : search || filters.domain || filters.capability || filters.agent_type ? (
        <SearchNoResults query={search || 'your filters'} />
      ) : (
        <NoAgentsFound />
      )}
    </div>
  );
}
