import { useState } from 'react';
import { Card, Input, SkeletonCard, NoWorkflowsFound, SearchNoResults } from '../components/ui';
import { WorkflowCard } from '../components/workflows';
import { useWorkflows } from '../api/hooks';

export default function Workflows() {
  const [search, setSearch] = useState('');
  const { data: workflows, isLoading } = useWorkflows();

  const filteredWorkflows = workflows?.filter(
    (workflow) =>
      workflow.name.toLowerCase().includes(search.toLowerCase()) ||
      workflow.description.toLowerCase().includes(search.toLowerCase())
  ) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Workflows</h1>
        <p className="text-gray-500 mt-1">
          Execute multi-agent workflow templates
        </p>
      </div>

      {/* Search */}
      <Card>
        <Input
          placeholder="Search workflows..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </Card>

      {/* Results */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : filteredWorkflows.length > 0 ? (
        <>
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">
              Showing {filteredWorkflows.length} workflow{filteredWorkflows.length !== 1 && 's'}
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredWorkflows.map((workflow) => (
              <WorkflowCard key={workflow.id} workflow={workflow} />
            ))}
          </div>
        </>
      ) : search ? (
        <SearchNoResults query={search} />
      ) : (
        <NoWorkflowsFound />
      )}
    </div>
  );
}
