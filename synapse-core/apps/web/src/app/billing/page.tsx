'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/auth/context';
import synapseAPI from '@/lib/api/client';
import type { SubscriptionStatus, Invoice } from '@/lib/api/types';

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

function formatCurrency(cents: number, currency: string = 'usd'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency.toUpperCase(),
  }).format(cents / 100);
}

export default function BillingPage() {
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState('');
  const { user, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login?redirect=/billing');
      return;
    }

    async function loadBillingData() {
      setIsLoading(true);
      try {
        const [subStatus, invoiceData] = await Promise.all([
          synapseAPI.getSubscriptionStatus(),
          synapseAPI.getInvoices(10),
        ]);
        setSubscription(subStatus);
        setInvoices(invoiceData.invoices || []);
      } catch (err) {
        console.error('Failed to load billing data:', err);
        setError('Failed to load billing information');
      } finally {
        setIsLoading(false);
      }
    }

    loadBillingData();
  }, [isAuthenticated, router]);

  const handleManageBilling = async () => {
    setActionLoading('portal');
    try {
      const { portal_url } = await synapseAPI.getBillingPortal(window.location.href);
      window.location.href = portal_url;
    } catch (err) {
      setError('Failed to open billing portal');
      setActionLoading(null);
    }
  };

  const handleCancelSubscription = async () => {
    if (!confirm('Are you sure you want to cancel your subscription? You will retain access until the end of your billing period.')) {
      return;
    }

    setActionLoading('cancel');
    setError('');
    try {
      await synapseAPI.cancelSubscription(false);
      // Refresh subscription status
      const subStatus = await synapseAPI.getSubscriptionStatus();
      setSubscription(subStatus);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel subscription');
    } finally {
      setActionLoading(null);
    }
  };

  const handleReactivateSubscription = async () => {
    setActionLoading('reactivate');
    setError('');
    try {
      await synapseAPI.reactivateSubscription();
      // Refresh subscription status
      const subStatus = await synapseAPI.getSubscriptionStatus();
      setSubscription(subStatus);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reactivate subscription');
    } finally {
      setActionLoading(null);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400 mx-auto mb-4"></div>
          <p className="text-slate-400">Loading billing information...</p>
        </div>
      </div>
    );
  }

  const tierColors: Record<string, string> = {
    free: 'text-slate-400 bg-slate-800',
    standard: 'text-cyan-400 bg-cyan-500/20',
    enterprise: 'text-amber-400 bg-amber-500/20',
  };

  const statusColors: Record<string, string> = {
    active: 'text-emerald-400 bg-emerald-500/20',
    trialing: 'text-blue-400 bg-blue-500/20',
    past_due: 'text-red-400 bg-red-500/20',
    canceled: 'text-slate-400 bg-slate-800',
    none: 'text-slate-400 bg-slate-800',
  };

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <header className="border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/" className="text-xl font-bold text-white">
            Synapse<span className="text-cyan-400">Core</span>
          </Link>
          <nav className="flex items-center gap-4">
            <Link href="/" className="text-slate-400 hover:text-white transition-colors">
              Dashboard
            </Link>
            <Link href="/pricing" className="text-slate-400 hover:text-white transition-colors">
              Pricing
            </Link>
          </nav>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-white mb-8">Billing & Subscription</h1>

        {error && (
          <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 text-red-400 mb-6">
            {error}
          </div>
        )}

        {/* Current Plan */}
        <section className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">Current Plan</h2>

          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <span
                  className={`px-3 py-1 rounded-full text-sm font-medium capitalize ${
                    tierColors[subscription?.tier || 'free']
                  }`}
                >
                  {subscription?.tier || 'Free'}
                </span>
                <span
                  className={`px-3 py-1 rounded-full text-sm font-medium capitalize ${
                    statusColors[subscription?.status || 'none']
                  }`}
                >
                  {subscription?.status === 'none' ? 'No subscription' : subscription?.status}
                </span>
              </div>

              {subscription?.current_period_end && subscription.status === 'active' && (
                <p className="text-slate-400 text-sm">
                  {subscription.cancel_at_period_end
                    ? `Cancels on ${formatDate(subscription.current_period_end)}`
                    : `Renews on ${formatDate(subscription.current_period_end)}`}
                </p>
              )}
            </div>

            <div className="flex gap-3">
              {subscription?.tier !== 'free' && subscription?.status === 'active' && (
                <>
                  <button
                    onClick={handleManageBilling}
                    disabled={actionLoading !== null}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors disabled:opacity-50"
                  >
                    {actionLoading === 'portal' ? 'Opening...' : 'Manage Payment'}
                  </button>

                  {subscription.cancel_at_period_end ? (
                    <button
                      onClick={handleReactivateSubscription}
                      disabled={actionLoading !== null}
                      className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg transition-colors disabled:opacity-50"
                    >
                      {actionLoading === 'reactivate' ? 'Processing...' : 'Reactivate'}
                    </button>
                  ) : (
                    <button
                      onClick={handleCancelSubscription}
                      disabled={actionLoading !== null}
                      className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors disabled:opacity-50"
                    >
                      {actionLoading === 'cancel' ? 'Canceling...' : 'Cancel Plan'}
                    </button>
                  )}
                </>
              )}

              {(subscription?.tier === 'free' || subscription?.status === 'none') && (
                <Link
                  href="/pricing"
                  className="px-4 py-2 bg-cyan-500 hover:bg-cyan-600 text-white rounded-lg transition-colors"
                >
                  Upgrade Plan
                </Link>
              )}

              {subscription?.tier === 'standard' && subscription?.status === 'active' && (
                <Link
                  href="/pricing"
                  className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-lg transition-colors"
                >
                  Upgrade to Enterprise
                </Link>
              )}
            </div>
          </div>
        </section>

        {/* Plan Features */}
        <section className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">Plan Features</h2>

          <div className="grid md:grid-cols-2 gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-cyan-500/20 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div>
                <p className="text-white font-medium">Rate Limit</p>
                <p className="text-slate-400 text-sm">
                  {subscription?.tier === 'enterprise' ? '600' : '60'} requests/minute
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-emerald-500/20 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                </svg>
              </div>
              <div>
                <p className="text-white font-medium">Context Storage</p>
                <p className="text-slate-400 text-sm">
                  {subscription?.tier === 'enterprise' ? '100GB' : '10GB'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-amber-500/20 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <div>
                <p className="text-white font-medium">AI Agents</p>
                <p className="text-slate-400 text-sm">Scribe, Architect, Sentry</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              </div>
              <div>
                <p className="text-white font-medium">Support</p>
                <p className="text-slate-400 text-sm">
                  {subscription?.tier === 'enterprise' ? 'Priority' : 'Email'}
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Billing History */}
        <section className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Billing History</h2>

          {invoices.length === 0 ? (
            <p className="text-slate-400 text-center py-8">No invoices yet</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-slate-400 text-sm border-b border-slate-800">
                    <th className="pb-3 font-medium">Date</th>
                    <th className="pb-3 font-medium">Amount</th>
                    <th className="pb-3 font-medium">Status</th>
                    <th className="pb-3 font-medium text-right">Invoice</th>
                  </tr>
                </thead>
                <tbody className="text-slate-300">
                  {invoices.map((invoice) => (
                    <tr key={invoice.id} className="border-b border-slate-800/50">
                      <td className="py-4">{formatDate(invoice.created)}</td>
                      <td className="py-4">{formatCurrency(invoice.amount_paid, invoice.currency)}</td>
                      <td className="py-4">
                        <span
                          className={`px-2 py-1 rounded text-xs font-medium capitalize ${
                            invoice.status === 'paid'
                              ? 'bg-emerald-500/20 text-emerald-400'
                              : 'bg-slate-700 text-slate-400'
                          }`}
                        >
                          {invoice.status}
                        </span>
                      </td>
                      <td className="py-4 text-right">
                        {invoice.invoice_pdf && (
                          <a
                            href={invoice.invoice_pdf}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-cyan-400 hover:text-cyan-300 text-sm"
                          >
                            Download PDF
                          </a>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
