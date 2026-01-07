/**
 * Server-side authentication utilities for API routes.
 * Handles token caching and backend authentication.
 */

const BACKEND_URL = process.env.BACKEND_URL || process.env.FASTAPI_BASE_URL || 'http://localhost:8000';

// Token cache for development mode
let cachedToken: string | null = null;
let tokenExpiry: number = 0;

/**
 * Fetches a development token from the backend.
 * Caches the token to avoid repeated requests.
 */
export async function getDevToken(): Promise<string> {
  const now = Date.now();

  // Return cached token if still valid (with 5 min buffer)
  if (cachedToken && tokenExpiry > now + 5 * 60 * 1000) {
    return cachedToken;
  }

  const response = await fetch(`${BACKEND_URL}/auth/dev-token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Failed to get dev token: ${response.status}`);
  }

  const data = await response.json();
  const token: string = data.access_token;
  cachedToken = token;
  // Tokens expire in 24h, cache for 23h
  tokenExpiry = now + 23 * 60 * 60 * 1000;

  return token;
}

/**
 * Clears the cached token (useful after auth errors).
 */
export function clearTokenCache(): void {
  cachedToken = null;
  tokenExpiry = 0;
}

/**
 * Creates headers with authentication for backend requests.
 * @param additionalHeaders - Optional additional headers to include
 */
export async function getAuthHeaders(
  additionalHeaders?: Record<string, string>
): Promise<Record<string, string>> {
  const token = await getDevToken();
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
    ...additionalHeaders,
  };
}

/**
 * Makes an authenticated fetch request to the backend.
 * Automatically handles token caching and auth header injection.
 */
export async function authenticatedFetch(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const url = endpoint.startsWith('http') ? endpoint : `${BACKEND_URL}${endpoint}`;
  const headers = await getAuthHeaders(options.headers as Record<string, string>);

  const response = await fetch(url, {
    ...options,
    headers,
  });

  // Clear token cache on auth errors
  if (response.status === 401) {
    clearTokenCache();
  }

  return response;
}

export { BACKEND_URL };
