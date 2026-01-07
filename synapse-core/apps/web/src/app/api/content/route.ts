import { NextRequest, NextResponse } from 'next/server';
import { authenticatedFetch } from '@/lib/auth';

// List generated content
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const contentType = searchParams.get('content_type');
    const limit = searchParams.get('limit') || '20';

    const params = new URLSearchParams();
    if (contentType) params.set('content_type', contentType);
    params.set('limit', limit);

    const response = await authenticatedFetch(`/content?${params}`, {
      method: 'GET',
      cache: 'no-store',
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: error.detail || 'Failed to list content' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('List content error:', error);
    return NextResponse.json(
      { error: 'Failed to connect to backend' },
      { status: 500 }
    );
  }
}
