'use client';

import Link from 'next/link';

export default function CheckoutCancelPage() {
  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        {/* Cancel Icon */}
        <div className="w-20 h-20 bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg
            className="w-10 h-10 text-slate-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </div>

        <h1 className="text-3xl font-bold text-white mb-4">
          Checkout Canceled
        </h1>

        <p className="text-slate-400 mb-8">
          No worries! Your checkout was canceled and you haven't been charged.
          You can try again whenever you're ready.
        </p>

        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 mb-8">
          <h2 className="text-lg font-medium text-white mb-4">Need Help?</h2>
          <p className="text-slate-400 text-sm mb-4">
            If you experienced any issues during checkout or have questions about our
            plans, we're here to help.
          </p>
          <ul className="text-left space-y-2 text-slate-400 text-sm">
            <li>• Check out our <Link href="/pricing" className="text-cyan-400 hover:text-cyan-300">pricing FAQ</Link></li>
            <li>• Contact support at <span className="text-cyan-400">support@synapse.local</span></li>
          </ul>
        </div>

        <div className="space-y-3">
          <Link
            href="/pricing"
            className="block w-full py-3 px-4 bg-cyan-500 hover:bg-cyan-600 text-white font-medium rounded-lg transition-colors"
          >
            Return to Pricing
          </Link>

          <Link
            href="/"
            className="block w-full py-3 px-4 bg-slate-800 hover:bg-slate-700 text-white font-medium rounded-lg transition-colors border border-slate-700"
          >
            Go to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
