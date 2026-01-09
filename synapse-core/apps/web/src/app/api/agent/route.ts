import { NextRequest, NextResponse } from 'next/server';
import { authenticatedFetch, clearTokenCache, BACKEND_URL } from '@/lib/auth';

const SUPPORTED_AGENTS = ['scribe', 'architect', 'sentry'];

export async function POST(req: NextRequest) {
  try {
    const { agent, thread_id, prompt, user_id, stream } = await req.json();

    // Validate required fields
    if (!agent || !thread_id || !prompt) {
      return NextResponse.json(
        { error: 'Missing required fields: agent, thread_id, prompt' },
        { status: 400 }
      );
    }

    // Validate agent type
    if (!SUPPORTED_AGENTS.includes(agent)) {
      return NextResponse.json(
        {
          error: `Agent '${agent}' not supported. Available: ${SUPPORTED_AGENTS.join(', ')}`,
        },
        { status: 400 }
      );
    }

    // Build request body for unified invoke endpoint
    const requestBody: Record<string, unknown> = {
      agent,
      thread_id,
      prompt,
      stream: Boolean(stream),
    };

    if (user_id) {
      requestBody.user_id = user_id;
    }

    // Use unified invoke endpoint
    const response = await authenticatedFetch('/invoke', {
      method: 'POST',
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));

      // Handle auth errors by clearing cached token
      if (response.status === 401) {
        clearTokenCache();
      }

      return NextResponse.json(
        { error: errorData.detail || `Agent invocation failed: ${response.status}` },
        { status: response.status }
      );
    }

    // Handle streaming response
    if (stream && response.body) {
      return new Response(response.body, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          Connection: 'keep-alive',
        },
      });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error: unknown) {
    console.error('API Route Error:', error);
    const message = error instanceof Error ? error.message : 'Internal Server Error';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * Health check endpoint to verify backend connectivity
 */
export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      return NextResponse.json(
        { status: 'unhealthy', error: 'Backend unreachable' },
        { status: 503 }
      );
    }

    const data = await response.json();
    return NextResponse.json({
      status: 'healthy',
      backend: data,
      supported_agents: SUPPORTED_AGENTS,
    });
  } catch {
    return NextResponse.json(
      { status: 'unhealthy', error: 'Backend connection failed' },
      { status: 503 }
    );
  }
}
