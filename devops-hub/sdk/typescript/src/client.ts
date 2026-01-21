/**
 * DevOps Hub SDK - HTTP Client
 */

import type { SDKConfig, ApiResponse, ApiError } from './types';

export class DevOpsHubError extends Error {
  status: number;
  code?: string;
  details?: Record<string, unknown>;

  constructor(error: ApiError) {
    super(error.message);
    this.name = 'DevOpsHubError';
    this.status = error.status;
    this.code = error.code;
    this.details = error.details;
  }
}

export class HttpClient {
  private baseUrl: string;
  private apiKey?: string;
  private timeout: number;
  private defaultHeaders: Record<string, string>;

  constructor(config: SDKConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, '');
    this.apiKey = config.apiKey;
    this.timeout = config.timeout ?? 30000;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      ...config.headers,
    };
  }

  private getHeaders(): Record<string, string> {
    const headers = { ...this.defaultHeaders };
    if (this.apiKey) {
      headers['X-API-Key'] = this.apiKey;
    }
    return headers;
  }

  async request<T>(
    method: string,
    path: string,
    options: {
      body?: unknown;
      params?: Record<string, string | number | boolean | undefined>;
      headers?: Record<string, string>;
    } = {}
  ): Promise<ApiResponse<T>> {
    const url = new URL(`${this.baseUrl}${path}`);

    if (options.params) {
      Object.entries(options.params).forEach(([key, value]) => {
        if (value !== undefined) {
          url.searchParams.append(key, String(value));
        }
      });
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url.toString(), {
        method,
        headers: { ...this.getHeaders(), ...options.headers },
        body: options.body ? JSON.stringify(options.body) : undefined,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      const responseHeaders: Record<string, string> = {};
      response.headers.forEach((value, key) => {
        responseHeaders[key] = value;
      });

      if (!response.ok) {
        let errorData: ApiError;
        try {
          const errorBody = await response.json();
          errorData = {
            message: errorBody.detail || errorBody.message || response.statusText,
            status: response.status,
            code: errorBody.code,
            details: errorBody,
          };
        } catch {
          errorData = {
            message: response.statusText,
            status: response.status,
          };
        }
        throw new DevOpsHubError(errorData);
      }

      const data = await response.json() as T;
      return { data, status: response.status, headers: responseHeaders };
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof DevOpsHubError) {
        throw error;
      }
      if (error instanceof Error && error.name === 'AbortError') {
        throw new DevOpsHubError({
          message: 'Request timeout',
          status: 408,
          code: 'TIMEOUT',
        });
      }
      throw new DevOpsHubError({
        message: error instanceof Error ? error.message : 'Unknown error',
        status: 0,
        code: 'NETWORK_ERROR',
      });
    }
  }

  async get<T>(path: string, params?: Record<string, string | number | boolean | undefined>): Promise<ApiResponse<T>> {
    return this.request<T>('GET', path, { params });
  }

  async post<T>(path: string, body?: unknown, params?: Record<string, string | number | boolean | undefined>): Promise<ApiResponse<T>> {
    return this.request<T>('POST', path, { body, params });
  }

  async put<T>(path: string, body?: unknown): Promise<ApiResponse<T>> {
    return this.request<T>('PUT', path, { body });
  }

  async patch<T>(path: string, body?: unknown): Promise<ApiResponse<T>> {
    return this.request<T>('PATCH', path, { body });
  }

  async delete<T>(path: string): Promise<ApiResponse<T>> {
    return this.request<T>('DELETE', path);
  }

  setApiKey(apiKey: string): void {
    this.apiKey = apiKey;
  }

  clearApiKey(): void {
    this.apiKey = undefined;
  }
}
