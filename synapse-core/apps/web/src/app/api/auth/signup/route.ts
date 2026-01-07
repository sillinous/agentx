import { NextRequest, NextResponse } from 'next/server';
import { BACKEND_URL } from '@/lib/auth';

export async function POST(request: NextRequest) {
  try {
    const { name, email, password } = await request.json();

    if (!name || !email || !password) {
      return NextResponse.json(
        { error: 'Name, email, and password are required' },
        { status: 400 }
      );
    }

    if (password.length < 8) {
      return NextResponse.json(
        { error: 'Password must be at least 8 characters' },
        { status: 400 }
      );
    }

    // Forward signup request to backend
    // Note: The backend needs to implement /auth/signup endpoint
    const response = await fetch(`${BACKEND_URL}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password }),
    });

    if (!response.ok) {
      // If backend doesn't have signup endpoint yet, return success for development
      if (response.status === 404) {
        // In development, just return success
        // Real implementation will create user in database
        return NextResponse.json({
          success: true,
          message: 'Account created successfully (dev mode)',
        });
      }

      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: error.detail || 'Signup failed' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Signup error:', error);
    return NextResponse.json(
      { error: 'Failed to connect to authentication service' },
      { status: 500 }
    );
  }
}
