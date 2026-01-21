'use client';

import { useEffect, useState } from 'react';
import { ProjectCard } from '@/components/dashboard/ProjectCard';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { getProjects } from '@/lib/api';
import type { Project } from '@/lib/types';
import { Search, Filter, SortAsc, SortDesc } from 'lucide-react';

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [filteredProjects, setFilteredProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [tierFilter, setTierFilter] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState('overall_score');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const data = await getProjects({ sort_by: sortBy, order: sortOrder });
        setProjects(data.projects);
        setFilteredProjects(data.projects);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchProjects();
  }, [sortBy, sortOrder]);

  useEffect(() => {
    let result = [...projects];

    if (search) {
      const searchLower = search.toLowerCase();
      result = result.filter(
        (p) =>
          p.name.toLowerCase().includes(searchLower) ||
          p.description?.toLowerCase().includes(searchLower) ||
          p.tech_stack?.some((t) => t.toLowerCase().includes(searchLower))
      );
    }

    if (tierFilter) {
      result = result.filter((p) => p.tier === tierFilter);
    }

    if (statusFilter) {
      result = result.filter((p) => p.status === statusFilter);
    }

    setFilteredProjects(result);
  }, [search, tierFilter, statusFilter, projects]);

  const tiers = ['tier1', 'tier2', 'tier3'];
  const statuses = ['discovery', 'development', 'ready', 'launched'];

  const toggleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">All Projects</h1>
        <p className="text-gray-500 mt-1">
          {filteredProjects.length} of {projects.length} projects
        </p>
      </div>

      {/* Filters */}
      <Card>
        <div className="flex flex-wrap items-center gap-4">
          {/* Search */}
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search projects..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Tier Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <span className="text-sm text-gray-500">Tier:</span>
            <div className="flex gap-1">
              <Button
                size="sm"
                variant={tierFilter === null ? 'primary' : 'ghost'}
                onClick={() => setTierFilter(null)}
              >
                All
              </Button>
              {tiers.map((tier) => (
                <Button
                  key={tier}
                  size="sm"
                  variant={tierFilter === tier ? 'primary' : 'ghost'}
                  onClick={() => setTierFilter(tier)}
                >
                  {tier.replace('tier', '')}
                </Button>
              ))}
            </div>
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">Status:</span>
            <div className="flex gap-1">
              <Button
                size="sm"
                variant={statusFilter === null ? 'primary' : 'ghost'}
                onClick={() => setStatusFilter(null)}
              >
                All
              </Button>
              {statuses.map((status) => (
                <Button
                  key={status}
                  size="sm"
                  variant={statusFilter === status ? 'primary' : 'ghost'}
                  onClick={() => setStatusFilter(status)}
                >
                  {status}
                </Button>
              ))}
            </div>
          </div>

          {/* Sort */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">Sort:</span>
            <Button
              size="sm"
              variant={sortBy === 'overall_score' ? 'primary' : 'ghost'}
              onClick={() => toggleSort('overall_score')}
            >
              Score
              {sortBy === 'overall_score' &&
                (sortOrder === 'desc' ? (
                  <SortDesc className="w-3 h-3 ml-1" />
                ) : (
                  <SortAsc className="w-3 h-3 ml-1" />
                ))}
            </Button>
            <Button
              size="sm"
              variant={sortBy === 'revenue_score' ? 'primary' : 'ghost'}
              onClick={() => toggleSort('revenue_score')}
            >
              Revenue
              {sortBy === 'revenue_score' &&
                (sortOrder === 'desc' ? (
                  <SortDesc className="w-3 h-3 ml-1" />
                ) : (
                  <SortAsc className="w-3 h-3 ml-1" />
                ))}
            </Button>
            <Button
              size="sm"
              variant={sortBy === 'name' ? 'primary' : 'ghost'}
              onClick={() => toggleSort('name')}
            >
              Name
              {sortBy === 'name' &&
                (sortOrder === 'desc' ? (
                  <SortDesc className="w-3 h-3 ml-1" />
                ) : (
                  <SortAsc className="w-3 h-3 ml-1" />
                ))}
            </Button>
          </div>
        </div>
      </Card>

      {/* Projects List */}
      {loading ? (
        <div className="animate-pulse space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-32 bg-gray-100 rounded-xl" />
          ))}
        </div>
      ) : filteredProjects.length === 0 ? (
        <Card className="text-center py-12">
          <p className="text-gray-500">No projects found matching your criteria</p>
          <Button
            variant="outline"
            className="mt-4"
            onClick={() => {
              setSearch('');
              setTierFilter(null);
              setStatusFilter(null);
            }}
          >
            Clear filters
          </Button>
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredProjects.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      )}
    </div>
  );
}
