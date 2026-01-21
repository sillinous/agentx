import { clsx, type ClassValue } from 'clsx';

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat('en-US').format(value);
}

export function getTierColor(tier: string): string {
  switch (tier) {
    case 'tier1':
      return 'bg-green-500';
    case 'tier2':
      return 'bg-yellow-500';
    case 'tier3':
      return 'bg-gray-500';
    default:
      return 'bg-gray-400';
  }
}

export function getTierBgColor(tier: string): string {
  switch (tier) {
    case 'tier1':
      return 'bg-green-50 border-green-200';
    case 'tier2':
      return 'bg-yellow-50 border-yellow-200';
    case 'tier3':
      return 'bg-gray-50 border-gray-200';
    default:
      return 'bg-gray-50 border-gray-200';
  }
}

export function getTierLabel(tier: string): string {
  switch (tier) {
    case 'tier1':
      return 'Tier 1 - Immediate Revenue';
    case 'tier2':
      return 'Tier 2 - High Priority';
    case 'tier3':
      return 'Tier 3 - Scalable';
    default:
      return tier;
  }
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'discovery':
      return 'bg-blue-100 text-blue-800';
    case 'development':
      return 'bg-purple-100 text-purple-800';
    case 'ready':
      return 'bg-green-100 text-green-800';
    case 'launched':
      return 'bg-emerald-100 text-emerald-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

export function getPriorityColor(priority: string): string {
  switch (priority) {
    case 'high':
      return 'bg-red-100 text-red-800';
    case 'medium':
      return 'bg-yellow-100 text-yellow-800';
    case 'low':
      return 'bg-gray-100 text-gray-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

export function getCategoryIcon(category: string): string {
  switch (category) {
    case 'payment':
      return '💳';
    case 'deployment':
      return '🚀';
    case 'feature':
      return '✨';
    case 'marketing':
      return '📢';
    default:
      return '📋';
  }
}

export function calculateROI(revenueImpact: number, effortHours: number): number {
  return effortHours > 0 ? revenueImpact / effortHours : 0;
}
