'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';

export default function CheckoutSuccessPage() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('session_id');
  const [countdown, setCountdown] = useState(5);

  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          window.location.href = '/';
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        {/* Success Icon */}
        <div className="w-20 h-20 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg
            className="w-10 h-10 text-emerald-400"
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
        </div>

        <h1 className="text-3xl font-bold text-white mb-4">
          Payment Successful!
        </h1>

        <p className="text-slate-400 mb-8">
          Thank you for your subscription! Your account has been upgraded and you now have
          access to all premium features.
        </p>

        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 mb-8">
          <h2 className="text-lg font-medium text-white mb-4">What's Next?</h2>
          <ul className="text-left space-y-3">
            <li className="flex items-start gap-3">
              <span className="w-6 h-6 bg-cyan-500/20 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-cyan-400 text-sm">1</span>
              </span>
              <span className="text-slate-300">
                Explore the AI agents in your dashboard
              </span>
            </li>
            <li className="flex items-start gap-3">
              <span className="w-6 h-6 bg-cyan-500/20 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-cyan-400 text-sm">2</span>
              </span>
              <span className="text-slate-300">
                Check your email for a welcome guide and tips
              </span>
            </li>
            <li className="flex items-start gap-3">
              <span className="w-6 h-6 bg-cyan-500/20 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-cyan-400 text-sm">3</span>
              </span>
              <span className="text-slate-300">
                Manage your subscription anytime in the billing page
              </span>
            </li>
          </ul>
        </div>

        <div className="space-y-4">
          <Link
            href="/"
            className="block w-full py-3 px-4 bg-cyan-500 hover:bg-cyan-600 text-white font-medium rounded-lg transition-colors"
          >
            Go to Dashboard
          </Link>

          <p className="text-slate-500 text-sm">
            Redirecting in {countdown} seconds...
          </p>
        </div>

        {sessionId && (
          <p className="mt-6 text-slate-600 text-xs">
            Session ID: {sessionId}
          </p>
        )}
      </div>
    </div>
  );
}
