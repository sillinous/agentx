'use client';

import { useAuth } from '@/components/AuthProvider';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import Link from 'next/link';
import {
  Zap,
  BarChart3,
  TrendingUp,
  ArrowRight,
  Clock,
  DollarSign,
  Activity,
  History,
  ExternalLink,
  RefreshCw,
} from 'lucide-react';
import { TopDeals } from '@/components/TopDeals';
import { useDashboardData } from '@/hooks/useDashboardData';
import { SkeletonDashboard } from '@/components/ui/skeleton';

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuth();
  const { stats, loading: dataLoading, refresh } = useDashboardData();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
    }
  }, [user, authLoading, router]);

  if (authLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-4 animate-pulse">
            <Zap className="w-8 h-8 text-white" />
          </div>
          <p className="text-gray-600">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  // Show skeleton while loading data
  if (dataLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50">
        <div className="container mx-auto px-4 py-8">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              Welcome back, {user.email?.split('@')[0]}!
            </h1>
            <p className="text-xl text-gray-600">
              Your AI-powered deal analysis command center
            </p>
          </div>
          <SkeletonDashboard />
        </div>
      </div>
    );
  }

  const formatPrice = (price: number) => {
    if (price >= 1000000) return `$${(price / 1000000).toFixed(1)}M`;
    if (price >= 1000) return `$${(price / 1000).toFixed(0)}K`;
    return `$${price.toFixed(0)}`;
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 60) return 'text-blue-600 bg-blue-100';
    if (score >= 40) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Welcome back, {user.email?.split('@')[0]}!
          </h1>
          <p className="text-xl text-gray-600">
            Your AI-powered deal analysis command center
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <BarChart3 className="w-6 h-6 text-blue-600" />
              </div>
              <span className="text-2xl font-bold text-gray-900">
                {stats?.analysesRemaining === 'unlimited' ? '∞' : stats?.analysesRemaining ?? 3}
              </span>
            </div>
            <div className="text-sm text-gray-600">Analyses Remaining</div>
            <div className="text-xs text-gray-500 mt-1">{stats?.planName ?? 'Free Plan'}</div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <Activity className="w-6 h-6 text-purple-600" />
              </div>
              <span className="text-2xl font-bold text-gray-900">{stats?.totalAnalyses ?? 0}</span>
            </div>
            <div className="text-sm text-gray-600">Total Analyses</div>
            <div className="text-xs text-gray-500 mt-1">All time</div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-green-600" />
              </div>
              <span className="text-2xl font-bold text-gray-900">
                {formatPrice(stats?.averageDealValue ?? 0)}
              </span>
            </div>
            <div className="text-sm text-gray-600">Avg Deal Value</div>
            <div className="text-xs text-gray-500 mt-1">Analyzed</div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                <Clock className="w-6 h-6 text-yellow-600" />
              </div>
              <span className="text-2xl font-bold text-gray-900">{stats?.savedDeals ?? 0}</span>
            </div>
            <div className="text-sm text-gray-600">Saved Deals</div>
            <div className="text-xs text-gray-500 mt-1">Watchlist</div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Quick Actions */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Quick Actions</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Link
                  href="/analyze"
                  className="p-6 bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg border-2 border-blue-200 hover:border-blue-400 transition-all group"
                >
                  <Zap className="w-8 h-8 text-blue-600 mb-3" />
                  <h3 className="font-semibold text-gray-900 mb-1">Analyze New Deal</h3>
                  <p className="text-sm text-gray-600 mb-3">
                    Paste a Flippa URL to get instant AI insights
                  </p>
                  <div className="flex items-center text-blue-600 text-sm font-medium">
                    <span>Start Analysis</span>
                    <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                  </div>
                </Link>

                <div className="p-6 bg-gray-50 rounded-lg border-2 border-gray-200">
                  <DollarSign className="w-8 h-8 text-gray-400 mb-3" />
                  <h3 className="font-semibold text-gray-900 mb-1">Upgrade Plan</h3>
                  <p className="text-sm text-gray-600 mb-3">
                    Get unlimited analyses and advanced features
                  </p>
                  <div className="flex items-center text-gray-600 text-sm font-medium">
                    <span>Coming Soon</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Top Deals Widget */}
            <TopDeals />

            {/* Recent Analyses */}
            {stats?.recentAnalyses && stats.recentAnalyses.length > 0 && (
              <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-bold text-gray-900">Recent Analyses</h2>
                  <button
                    onClick={refresh}
                    className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                    title="Refresh"
                  >
                    <RefreshCw className="w-4 h-4" />
                  </button>
                </div>
                <div className="space-y-3">
                  {stats.recentAnalyses.map((analysis) => (
                    <Link
                      key={analysis.id}
                      href={`/analysis/${analysis.id}`}
                      className="block p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <h3 className="font-medium text-gray-900 truncate">
                            {analysis.listing?.title || 'Flippa Listing'}
                          </h3>
                          <div className="flex items-center gap-2 mt-1 text-sm text-gray-500">
                            <span>{new Date(analysis.created_at).toLocaleDateString()}</span>
                            {analysis.listing?.asking_price && (
                              <>
                                <span>•</span>
                                <span>{formatPrice(analysis.listing.asking_price)}</span>
                              </>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span
                            className={`px-2 py-1 rounded-full text-xs font-medium ${getScoreColor(analysis.score)}`}
                          >
                            {analysis.score}/100
                          </span>
                          <ExternalLink className="w-4 h-4 text-gray-400" />
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
                {stats.totalAnalyses > 5 && (
                  <Link
                    href="/history"
                    className="flex items-center justify-center gap-2 mt-4 p-3 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                  >
                    <History className="w-4 h-4" />
                    <span>View All {stats.totalAnalyses} Analyses</span>
                  </Link>
                )}
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Account Info */}
            <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Account</h2>
              <div className="space-y-3">
                <div>
                  <div className="text-sm text-gray-600 mb-1">Email</div>
                  <div className="font-medium text-gray-900">{user.email}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600 mb-1">Plan</div>
                  <div className="font-medium text-gray-900">Free Trial</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600 mb-1">Member Since</div>
                  <div className="font-medium text-gray-900">
                    {new Date(user.created_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            </div>

            {/* Tips */}
            <div className="bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl p-6 shadow-lg text-white">
              <h2 className="text-xl font-bold mb-3">Pro Tip</h2>
              <p className="text-blue-100 text-sm mb-4">
                Use FlipFlow to analyze deals before making offers. Our AI has helped investors
                avoid overpaying by an average of $12,000 per deal.
              </p>
              <Link
                href="/analyze"
                className="inline-flex items-center text-sm font-semibold hover:underline"
              >
                <span>Try it now</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
