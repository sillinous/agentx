import { NextRequest, NextResponse } from 'next/server';
import { authenticatedFetch } from '@/lib/auth';

interface RouteContext {
  params: Promise<{ threadId: string }>;
}

// Get a specific conversation
export async function GET(
  request: NextRequest,
  context: RouteContext
) {
  try {
    const { threadId } = await context.params;

    const response = await authenticatedFetch(`/conversations/${threadId}`, {
      method: 'GET',
      cache: 'no-store',
    });

    if (!response.ok) {
      if (response.status === 404) {
        return NextResponse.json(
          { error: 'Conversation not found' },
          { status: 404 }
        );
      }
      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: error.detail || 'Failed to get conversation' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Get conversation error:', error);
    return NextResponse.json(
      { error: 'Failed to connect to backend' },
      { status: 500 }
    );
  }
}

// Save/update a conversation
export async function PUT(
  request: NextRequest,
  context: RouteContext
) {
  try {
    const { threadId } = await context.params;
    const body = await request.json();

    const response = await authenticatedFetch(`/conversations/${threadId}`, {
      method: 'PUT',
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: error.detail || 'Failed to save conversation' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Save conversation error:', error);
    return NextResponse.json(
      { error: 'Failed to connect to backend' },
      { status: 500 }
    );
  }
}
