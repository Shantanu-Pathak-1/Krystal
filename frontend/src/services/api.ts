// API service for Krystal AI backend integration

const API_BASE_URL = (import.meta as any).env.VITE_API_URL || 'http://localhost:8000';

export interface ChatRequest {
  message: string;
  autonomy_mode?: string;
}

export interface ChatResponse {
  response: string;
  status: string;
  timestamp: string;
}

export interface StatusResponse {
  status: string;
  engine_loaded: boolean;
  message: string;
}

export interface PluginsResponse {
  plugins: Record<string, any>;
  status: string;
}

class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const defaultHeaders = {
      'Content-Type': 'application/json',
    };

    const config: RequestInit = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `HTTP ${response.status}: ${response.statusText}`
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Network error occurred');
    }
  }

  // Chat endpoints
  async chat(request: ChatRequest): Promise<ChatResponse> {
    return this.request<ChatResponse>('/api/chat', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async executeCommand(command: string): Promise<any> {
    return this.request<any>('/api/command', {
      method: 'POST',
      body: JSON.stringify({ command }),
    });
  }

  // Status and health endpoints
  async getStatus(): Promise<StatusResponse> {
    return this.request<StatusResponse>('/api/status');
  }

  async healthCheck(): Promise<{ status: string; engine_loaded: boolean }> {
    return this.request<{ status: string; engine_loaded: boolean }>('/health');
  }

  // Plugin endpoints
  async getPlugins(): Promise<PluginsResponse> {
    return this.request<PluginsResponse>('/api/plugins');
  }

  // Media and sensor endpoints
  async webcamCapture(): Promise<any> {
    return this.request<any>('/api/webcam', {
      method: 'POST',
      body: JSON.stringify({}),
    });
  }

  async startListening(): Promise<any> {
    return this.request<any>('/api/listen', {
      method: 'POST',
      body: JSON.stringify({}),
    });
  }

  async screenCapture(): Promise<any> {
    return this.request<any>('/api/see', {
      method: 'POST',
      body: JSON.stringify({}),
    });
  }

  // Utility endpoints
  async clearContext(): Promise<any> {
    return this.request<any>('/api/clear', {
      method: 'POST',
      body: JSON.stringify({}),
    });
  }

  // Voice input (placeholder)
  async voiceInput(audioData: Blob): Promise<any> {
    const formData = new FormData();
    formData.append('audio', audioData);
    
    return this.request<any>('/api/voice', {
      method: 'POST',
      body: formData,
      headers: {}, // Let browser set Content-Type for FormData
    });
  }
}

// Create singleton instance
export const apiService = new ApiService();

// Export types for use in components
export type { ApiService };
