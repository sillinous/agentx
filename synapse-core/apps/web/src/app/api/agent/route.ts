import { NextRequest, NextResponse } from 'next/server';

const FASTAPI_BASE_URL = process.env.FASTAPI_BASE_URL || 'http://127.0.0.1:8000';
const SUPPORTED_AGENTS = ['scribe', 'architect', 'sentry'];

// Token cache for development mode
let cachedToken: string | null = null;
let tokenExpiry: number = 0;

/**
 * Fetches a development token from the backend.
 * Caches the token to avoid repeated requests.
 */
async function getDevToken(): Promise<string> {
  const now = Date.now();

  // Return cached token if still valid (with 5 min buffer)
  if (cachedToken && tokenExpiry > now + 5 * 60 * 1000) {
    return cachedToken;
  }

  try {
    const response = await fetch(`${FASTAPI_BASE_URL}/auth/dev-token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      throw new Error(`Failed to get dev token: ${response.status}`);
    }

    const data = await response.json();
    cachedToken = data.access_token;
    // Tokens expire in 24h, cache for 23h
    tokenExpiry = now + 23 * 60 * 60 * 1000;

    return cachedToken;
  } catch (error) {
    console.error('Error fetching dev token:', error);
    throw new Error('Authentication service unavailable');
  }
}

export async function POST(req: NextRequest) {
  try {
    const { agent, thread_id, prompt, user_id } = await req.json();

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

    // Get authentication token
    let token: string;
    try {
      token = await getDevToken();
    } catch {
      return NextResponse.json(
        { error: 'Failed to authenticate with backend service' },
        { status: 503 }
      );
    }

    // Build request body based on agent type
    const requestBody: Record<string, string> = {
      thread_id,
      prompt,
    };

    // Scribe agent accepts optional user_id
    if (agent === 'scribe' && user_id) {
      requestBody.user_id = user_id;
    }

    // Invoke the agent
    const response = await fetch(`${FASTAPI_BASE_URL}/invoke/${agent}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));

      // Handle auth errors by clearing cached token
      if (response.status === 401) {
        cachedToken = null;
        tokenExpiry = 0;
      }

      return NextResponse.json(
        { error: errorData.detail || `Agent invocation failed: ${response.status}` },
        { status: response.status }
      );
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
    const response = await fetch(`${FASTAPI_BASE_URL}/`, {
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
