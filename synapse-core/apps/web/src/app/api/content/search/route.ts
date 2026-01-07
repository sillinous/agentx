import { NextRequest, NextResponse } from 'next/server';
import { authenticatedFetch } from '@/lib/auth';

// Semantic search for content
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const response = await authenticatedFetch('/content/search', {
      method: 'POST',
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: error.detail || 'Search failed' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Content search error:', error);
    return NextResponse.json(
      { error: 'Failed to connect to backend' },
      { status: 500 }
    );
  }
}
