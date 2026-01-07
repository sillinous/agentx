import { NextRequest, NextResponse } from 'next/server';
import { authenticatedFetch } from '@/lib/auth';

// List conversations
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const agentType = searchParams.get('agent_type');
    const limit = searchParams.get('limit') || '20';

    const params = new URLSearchParams();
    if (agentType) params.set('agent_type', agentType);
    params.set('limit', limit);

    const response = await authenticatedFetch(`/conversations?${params}`, {
      method: 'GET',
      cache: 'no-store',
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: error.detail || 'Failed to list conversations' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('List conversations error:', error);
    return NextResponse.json(
      { error: 'Failed to connect to backend' },
      { status: 500 }
    );
  }
}
