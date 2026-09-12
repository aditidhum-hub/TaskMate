import { authService } from './authService';
import { ChatRequestPayload, ChatResponsePayload, ApiError } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

/**
 * Robust, production-grade API client connecting TaskMate frontend to FastAPI backend.
 * Automatically injects Firebase ID tokens into requests: Authorization: Bearer <token>
 */
export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
  }

  /**
   * Helper to perform authenticated fetch requests with error parsing.
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

    // Retrieve Firebase token if available
    const token = await authService.getIdToken().catch(() => null);

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...((options.headers as Record<string, string>) || {}),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        let errorData: { detail?: unknown } = {};
        try {
          errorData = await response.json();
        } catch {
          // Non-JSON error body
        }

        let userMessage = `Request failed with status ${response.status}`;
        if (response.status === 401) {
          userMessage = 'Authentication required. Please sign in to communicate with TaskMate.';
        } else if (response.status === 422) {
          userMessage =
            typeof errorData.detail === 'string'
              ? errorData.detail
              : 'Invalid request payload. Please check your input.';
        } else if (response.status >= 500) {
          userMessage = 'The TaskMate server encountered an internal error. Please try again.';
        } else if (errorData.detail && typeof errorData.detail === 'string') {
          userMessage = errorData.detail;
        }

        const apiError: ApiError = {
          status: response.status,
          message: userMessage,
          detail: errorData.detail,
        };
        throw apiError;
      }

      return (await response.json()) as T;
    } catch (err: unknown) {
      if ((err as ApiError).status) {
        throw err;
      }
      // Network failure / server offline
      const networkError: ApiError = {
        status: 0,
        message: 'Could not connect to TaskMate backend server. Please verify the backend is running.',
        detail: err instanceof Error ? err.message : String(err),
      };
      throw networkError;
    }
  }

  /**
   * Check backend health probe (/api/health or /health)
   */
  async checkHealth(): Promise<{ status: string; service: string; timestamp?: string }> {
    try {
      return await this.request<{ status: string; service: string; timestamp?: string }>('/api/health');
    } catch {
      return await this.request<{ status: string; service: string; timestamp?: string }>('/health');
    }
  }

  /**
   * Verify if the backend server is reachable.
   */
  async isBackendAvailable(): Promise<boolean> {
    try {
      const health = await this.checkHealth();
      return health.status === 'ok';
    } catch {
      return false;
    }
  }

  /**
   * Send a conversational message to the agent loop via POST /api/chat
   */
  async postChat(
    message: string,
    messageHistory?: Array<Record<string, unknown>>
  ): Promise<ChatResponsePayload> {
    const payload: ChatRequestPayload = {
      message: message.trim(),
      message_history: messageHistory && messageHistory.length > 0 ? messageHistory : undefined,
    };

    return await this.request<ChatResponsePayload>('/api/chat', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }
}

export const apiClient = new ApiClient();
