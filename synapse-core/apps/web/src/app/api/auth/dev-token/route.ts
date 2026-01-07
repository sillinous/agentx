import { NextResponse } from 'next/server';
import { BACKEND_URL } from '@/lib/auth';

export async function POST() {
  try {
    const response = await fetch(`${BACKEND_URL}/auth/dev-token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Failed to get dev token' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Dev token error:', error);
    return NextResponse.json(
      { error: 'Failed to connect to backend' },
      { status: 500 }
    );
  }
}
