import { NextRequest, NextResponse } from 'next/server';

const FASTAPI_BASE_URL = process.env.FASTAPI_BASE_URL || 'http://127.0.0.1:8000'; // Default to local FastAPI

export async function POST(req: NextRequest) {
  try {
    const { agent, thread_id, prompt } = await req.json();

    if (!agent || !thread_id || !prompt) {
      return NextResponse.json(
        { error: 'Missing required fields: agent, thread_id, prompt' },
        { status: 400 },
      );
    }

    // For now, we only support the 'scribe' agent
    if (agent !== 'scribe') {
      return NextResponse.json({ error: `Agent '${agent}' not supported yet.` }, { status: 400 });
    }

    const response = await fetch(`${FASTAPI_BASE_URL}/invoke/${agent}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // In a real application, this token would be passed from the client
        Authorization: 'Bearer mock-jwt-token',
      },
      body: JSON.stringify({ thread_id, prompt }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      return NextResponse.json(
        { error: errorData.detail || 'Failed to invoke agent' },
        { status: response.status },
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
