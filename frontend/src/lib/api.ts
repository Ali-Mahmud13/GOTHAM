/**
 * API Client for GOTHAM Backend
 * 
 * Provides type-safe methods to interact with the FastAPI backend.
 * Uses fetch API with proper error handling.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Custom error class for API errors
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public data?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Handle API response and errors
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `API Error: ${response.status} ${response.statusText}`;
    let errorData: unknown;
    
    try {
      errorData = await response.json();
      if (typeof errorData === 'object' && errorData !== null && 'detail' in errorData) {
        errorMessage = String(errorData.detail);
      }
    } catch {
      // If response is not JSON, use status text
    }
    
    throw new ApiError(errorMessage, response.status, errorData);
  }
  
  return response.json() as Promise<T>;
}

/**
 * Chat API Response Types
 */
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  response: string;
  session_id: string;
}

export interface AssessmentRequest {
  message: string;
  session_id?: string;
  patient_id?: string;
}

export interface AssessmentResponse {
  assessment_id: string;
  session_id: string;
  status: string;
  message: string;
}

export interface AssessmentStatus {
  status: 'processing' | 'completed' | 'failed';
  response?: string;
  current_step?: number;
  total_steps?: number;
  step_label?: string;
  completed_steps?: string[];
  [key: string]: unknown;
}

/**
 * API Client
 */
export const api = {
  /**
   * Send a chat message and get immediate response
   */
  chat: async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    
    return handleResponse<ChatResponse>(response);
  },

  /**
   * Trigger background risk assessment (uses Inngest)
   */
  assess: async (request: AssessmentRequest): Promise<AssessmentResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/chat/assess`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    
    return handleResponse<AssessmentResponse>(response);
  },

  /**
   * Get assessment status and results
   */
  getAssessmentStatus: async (assessmentId: string): Promise<AssessmentStatus> => {
    const response = await fetch(`${API_BASE_URL}/api/chat/assess/${assessmentId}`);
    return handleResponse<AssessmentStatus>(response);
  },

  /**
   * Health check endpoint
   */
  health: async (): Promise<{ status: string }> => {
    const response = await fetch(`${API_BASE_URL}/health`);
    return handleResponse<{ status: string }>(response);
  },
};

