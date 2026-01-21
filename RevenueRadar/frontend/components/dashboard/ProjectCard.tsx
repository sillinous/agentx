'use client';

import Link from 'next/link';
import { Card } from '@/components/ui/Card';
import { TierBadge, StatusBadge } from '@/components/ui/Badge';
import { formatCurrency } from '@/lib/utils';
import type { Project } from '@/lib/types';
import { ChevronRight, Code, Database, CreditCard, Shield } from 'lucide-react';

interface ProjectCardProps {
  project: Project;
}

export function ProjectCard({ project }: ProjectCardProps) {
  const features = [
    { key: 'has_api', icon: Code, label: 'API' },
    { key: 'has_database', icon: Database, label: 'DB' },
    { key: 'has_stripe', icon: CreditCard, label: 'Payments' },
    { key: 'has_auth', icon: Shield, label: 'Auth' },
  ];

  return (
    <Link href={`/projects/${project.id}`}>
      <Card className="hover:shadow-md transition-shadow cursor-pointer">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="font-semibold text-gray-900">{project.name}</h3>
              <TierBadge tier={project.tier} />
              <StatusBadge status={project.status} />
            </div>

            <p className="text-sm text-gray-500 line-clamp-2 mb-3">
              {project.description || 'No description available'}
            </p>

            <div className="flex items-center gap-4 text-sm">
              <div>
                <span className="text-gray-400">Score:</span>{' '}
                <span className="font-medium text-gray-900">{project.overall_score}</span>
              </div>
              <div>
                <span className="text-gray-400">Revenue:</span>{' '}
                <span className="font-medium text-green-600">
                  {formatCurrency(project.revenue_potential_min)} - {formatCurrency(project.revenue_potential_max)}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2 mt-3">
              {features.map((feature) => {
                const hasFeature = project.metadata?.[feature.key as keyof typeof project.metadata];
                return (
                  <div
                    key={feature.key}
                    className={`flex items-center gap-1 px-2 py-1 rounded text-xs ${
                      hasFeature
                        ? 'bg-green-50 text-green-700'
                        : 'bg-gray-50 text-gray-400'
                    }`}
                  >
                    <feature.icon className="w-3 h-3" />
                    <span>{feature.label}</span>
                  </div>
                );
              })}
            </div>
          </div>

          <ChevronRight className="w-5 h-5 text-gray-400 flex-shrink-0" />
        </div>
      </Card>
    </Link>
  );
}
