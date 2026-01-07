import { NextRequest, NextResponse } from 'next/server';
import { BACKEND_URL } from '@/lib/auth';

export async function POST(request: NextRequest) {
  try {
    const { email, password } = await request.json();

    if (!email || !password) {
      return NextResponse.json(
        { error: 'Email and password are required' },
        { status: 400 }
      );
    }

    // Forward login request to backend
    // Note: The backend needs to implement /auth/login endpoint
    const response = await fetch(`${BACKEND_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      // If backend doesn't have login endpoint yet, use dev token for development
      if (response.status === 404) {
        // Fallback to dev token
        const devResponse = await fetch(`${BACKEND_URL}/auth/dev-token`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        });

        if (!devResponse.ok) {
          return NextResponse.json(
            { error: 'Authentication service unavailable' },
            { status: 503 }
          );
        }

        const devData = await devResponse.json();
        return NextResponse.json({
          access_token: devData.access_token,
          user: {
            id: 'dev-user-001',
            email: email,
            name: email.split('@')[0],
            subscription_tier: 'enterprise',
          },
        });
      }

      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: error.detail || 'Invalid credentials' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Login error:', error);
    return NextResponse.json(
      { error: 'Failed to connect to authentication service' },
      { status: 500 }
    );
  }
}
