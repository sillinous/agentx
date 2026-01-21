import { NextResponse } from 'next/server';

export const runtime = 'edge';

export async function GET() {
  // Check required environment variables
  const requiredVars = [
    'ANTHROPIC_API_KEY',
    'NEXT_PUBLIC_SUPABASE_URL',
    'NEXT_PUBLIC_SUPABASE_ANON_KEY',
    'SUPABASE_SERVICE_KEY',
    'STRIPE_SECRET_KEY',
    'NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY',
    'STRIPE_WEBHOOK_SECRET',
  ];

  const missingVars = requiredVars.filter((v) => !process.env[v]);
  const isHealthy = missingVars.length === 0;

  const checks = {
    status: isHealthy ? 'healthy' : 'degraded',
    timestamp: new Date().toISOString(),
    version: process.env.npm_package_version || '0.1.0',
    environment: process.env.NODE_ENV,
    services: {
      anthropic: !!process.env.ANTHROPIC_API_KEY,
      supabase: !!process.env.NEXT_PUBLIC_SUPABASE_URL && !!process.env.SUPABASE_SERVICE_KEY,
      stripe: !!process.env.STRIPE_SECRET_KEY && !!process.env.STRIPE_WEBHOOK_SECRET,
      resend: !!process.env.RESEND_API_KEY,
      cron: !!process.env.CRON_SECRET,
    },
    validation: {
      valid: isHealthy,
      missingCount: missingVars.length,
      // Only show missing vars in development
      ...(process.env.NODE_ENV === 'development' && { missing: missingVars }),
    },
  };

  return NextResponse.json(checks, {
    status: isHealthy ? 200 : 503,
  });
}
