'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/auth/context';
import synapseAPI from '@/lib/api/client';
import type { PricingTier, BillingPeriod } from '@/lib/api/types';

// Default pricing tiers (fallback if API is unavailable)
const DEFAULT_TIERS: PricingTier[] = [
  {
    tier: 'standard',
    name: 'Standard',
    description: 'Perfect for individuals and small teams',
    price_monthly: 2900,
    price_yearly: 29000,
    features: [
      'All 3 AI Agents (Scribe, Architect, Sentry)',
      '60 requests/minute rate limit',
      '10GB context memory',
      'Email support',
      'API access',
    ],
    stripe_price_monthly: '',
    stripe_price_yearly: '',
  },
  {
    tier: 'enterprise',
    name: 'Enterprise',
    description: 'For growing businesses and power users',
    price_monthly: 9900,
    price_yearly: 99000,
    features: [
      'All 3 AI Agents (Scribe, Architect, Sentry)',
      '600 requests/minute rate limit (10x)',
      '100GB context memory',
      'Priority support',
      'Custom integrations',
      'Advanced analytics',
      'Team collaboration',
      'SSO (coming soon)',
    ],
    stripe_price_monthly: '',
    stripe_price_yearly: '',
  },
];

function formatPrice(cents: number): string {
  return `$${(cents / 100).toFixed(0)}`;
}

export default function PricingPage() {
  const [billingPeriod, setBillingPeriod] = useState<BillingPeriod>('monthly');
  const [tiers, setTiers] = useState<PricingTier[]>(DEFAULT_TIERS);
  const [isLoading, setIsLoading] = useState(false);
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);
  const [error, setError] = useState('');
  const { user, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    async function loadPricing() {
      try {
        const config = await synapseAPI.getBillingConfig();
        if (config.pricing_tiers && config.pricing_tiers.length > 0) {
          setTiers(config.pricing_tiers);
        }
      } catch (err) {
        console.error('Failed to load pricing:', err);
        // Use default tiers
      }
    }
    loadPricing();
  }, []);

  const handleSelectPlan = async (tier: 'standard' | 'enterprise') => {
    if (!isAuthenticated) {
      // Redirect to login with return URL
      router.push(`/login?redirect=/pricing&tier=${tier}`);
      return;
    }

    setError('');
    setCheckoutLoading(tier);

    try {
      const checkout = await synapseAPI.createCheckoutSession(tier, billingPeriod);
      // Redirect to Stripe Checkout
      window.location.href = checkout.checkout_url;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create checkout session');
      setCheckoutLoading(null);
    }
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
            {isAuthenticated ? (
              <>
                <Link href="/" className="text-slate-400 hover:text-white transition-colors">
                  Dashboard
                </Link>
                <Link href="/billing" className="text-slate-400 hover:text-white transition-colors">
                  Billing
                </Link>
              </>
            ) : (
              <>
                <Link href="/login" className="text-slate-400 hover:text-white transition-colors">
                  Sign In
                </Link>
                <Link
                  href="/signup"
                  className="px-4 py-2 bg-cyan-500 hover:bg-cyan-600 text-white rounded-lg transition-colors"
                >
                  Get Started
                </Link>
              </>
            )}
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Simple, Transparent Pricing
          </h1>
          <p className="text-xl text-slate-400 mb-8">
            Power your business with AI agents. Start free, upgrade when you're ready.
          </p>

          {/* Billing Toggle */}
          <div className="inline-flex items-center bg-slate-800 rounded-lg p-1 mb-12">
            <button
              onClick={() => setBillingPeriod('monthly')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                billingPeriod === 'monthly'
                  ? 'bg-cyan-500 text-white'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingPeriod('yearly')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                billingPeriod === 'yearly'
                  ? 'bg-cyan-500 text-white'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Yearly <span className="text-emerald-400 ml-1">Save 17%</span>
            </button>
          </div>
        </div>
      </section>

      {/* Error Message */}
      {error && (
        <div className="max-w-4xl mx-auto px-4 mb-8">
          <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 text-red-400">
            {error}
          </div>
        </div>
      )}

      {/* Pricing Cards */}
      <section className="pb-16 px-4">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-8">
          {tiers.map((tier) => {
            const isEnterprise = tier.tier === 'enterprise';
            const price = billingPeriod === 'monthly' ? tier.price_monthly : tier.price_yearly;
            const priceLabel = billingPeriod === 'monthly' ? '/month' : '/year';

            return (
              <div
                key={tier.tier}
                className={`relative bg-slate-900/50 border rounded-2xl p-8 ${
                  isEnterprise
                    ? 'border-cyan-500/50 ring-1 ring-cyan-500/20'
                    : 'border-slate-800'
                }`}
              >
                {isEnterprise && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="bg-cyan-500 text-white text-xs font-medium px-3 py-1 rounded-full">
                      Most Popular
                    </span>
                  </div>
                )}

                <div className="mb-6">
                  <h3 className="text-2xl font-bold text-white mb-2">{tier.name}</h3>
                  <p className="text-slate-400">{tier.description}</p>
                </div>

                <div className="mb-6">
                  <span className="text-4xl font-bold text-white">{formatPrice(price)}</span>
                  <span className="text-slate-400 ml-1">{priceLabel}</span>
                </div>

                <button
                  onClick={() => handleSelectPlan(tier.tier as 'standard' | 'enterprise')}
                  disabled={checkoutLoading !== null}
                  className={`w-full py-3 px-4 rounded-lg font-medium transition-colors mb-8 ${
                    isEnterprise
                      ? 'bg-cyan-500 hover:bg-cyan-600 text-white disabled:bg-cyan-500/50'
                      : 'bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 disabled:bg-slate-800/50'
                  }`}
                >
                  {checkoutLoading === tier.tier ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                          fill="none"
                        />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        />
                      </svg>
                      Processing...
                    </span>
                  ) : (
                    `Get ${tier.name}`
                  )}
                </button>

                <ul className="space-y-3">
                  {tier.features.map((feature, index) => (
                    <li key={index} className="flex items-start gap-3">
                      <svg
                        className="w-5 h-5 text-emerald-400 mt-0.5 flex-shrink-0"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                      <span className="text-slate-300">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-16 px-4 border-t border-slate-800">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-white text-center mb-8">
            Frequently Asked Questions
          </h2>
          <div className="space-y-6">
            <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
              <h3 className="text-lg font-medium text-white mb-2">
                Can I switch plans later?
              </h3>
              <p className="text-slate-400">
                Yes! You can upgrade or downgrade your plan at any time. Changes take effect
                immediately, and we'll prorate the difference.
              </p>
            </div>
            <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
              <h3 className="text-lg font-medium text-white mb-2">
                What payment methods do you accept?
              </h3>
              <p className="text-slate-400">
                We accept all major credit cards (Visa, Mastercard, American Express) through
                our secure payment processor, Stripe.
              </p>
            </div>
            <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
              <h3 className="text-lg font-medium text-white mb-2">
                Is there a free trial?
              </h3>
              <p className="text-slate-400">
                We offer a free tier with limited usage so you can try our AI agents before
                committing. Upgrade anytime to unlock full features.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-8 px-4">
        <div className="max-w-7xl mx-auto text-center text-slate-500 text-sm">
          <p>&copy; {new Date().getFullYear()} Synapse Core. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
