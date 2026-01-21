import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/billing/config`, {
      headers: { 'Content-Type': 'application/json' },
      cache: 'no-store',
    });

    if (!response.ok) {
      // Return default config if backend unavailable
      return NextResponse.json({
        stripe_configured: false,
        public_key: null,
        pricing_tiers: [],
      });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Billing config fetch failed:', error);
    return NextResponse.json({
      stripe_configured: false,
      public_key: null,
      pricing_tiers: [],
    });
  }
}
