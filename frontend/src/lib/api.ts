import axios, { type AxiosInstance, type AxiosError } from 'axios';
import type {
  ChatMessage,
  ChatSession,
  ChatHistoryResponse,
  ModelsResponse,
  Report,
  ReportListResponse,
  ReportRequest,
  ReportType,
  ReportTypesResponse,
  TemplatesResponse,
  HealthResponse,
  ExtractionJob,
  ExtractionJobListResponse,
  ExtractionRequest,
  AnaliseJob,
  SettingsResponse,
  SettingsUpdate,
  SessionStatus,
  SessionListResponse,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 120000,
    });

    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  async healthCheck(): Promise<HealthResponse> {
    const { data } = await this.client.get<HealthResponse>('/health');
    return data;
  }

  async sendMessage(
    message: string,
    options: {
      session_id?: string;
      use_rag?: boolean;
      model?: string;
      temperature?: number;
      stream?: boolean;
      filters?: Record<string, unknown>;
    } = {}
  ): Promise<ChatMessage> {
    const { data } = await this.client.post<ChatMessage>('/chat', {
      message,
      ...options,
    });
    return data;
  }

  async *streamMessage(
    message: string,
    options: {
      session_id?: string;
      use_rag?: boolean;
      model?: string;
      temperature?: number;
      filters?: Record<string, unknown>;
    } = {}
  ): AsyncGenerator<{ content?: string; done?: boolean; session_id?: string }> {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...options, message, stream: true }),
    });

    if (!response.ok) {
      throw new Error('Failed to send message');
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) return;

    let buffer = '';
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const parsed = JSON.parse(line.slice(6));
              yield parsed;
            } catch {
              
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  async getSessions(): Promise<ChatSession[]> {
    const { data } = await this.client.get<ChatSession[]>('/chat/sessions');
    return data;
  }

  async getSessionHistory(sessionId: string): Promise<ChatHistoryResponse> {
    const { data } = await this.client.get<ChatHistoryResponse>(`/chat/sessions/${sessionId}`);
    return data;
  }

  async deleteSession(sessionId: string): Promise<void> {
    await this.client.delete(`/chat/sessions/${sessionId}`);
  }

  async getModels(): Promise<ModelsResponse> {
    const { data } = await this.client.get<ModelsResponse>('/models');
    return data;
  }

  async getReports(): Promise<Report[]> {
    const { data } = await this.client.get<ReportListResponse>('/reports');
    return Array.isArray(data?.reports) ? data.reports : [];
  }

  async getReport(reportId: number): Promise<Report> {
    const { data } = await this.client.get<Report>(`/reports/${reportId}`);
    return data;
  }

  async createReport(request: ReportRequest): Promise<Report> {
    const { data } = await this.client.post<Report>('/reports', request);
    return data;
  }

  async deleteReport(reportId: number): Promise<void> {
    await this.client.delete(`/reports/${reportId}`);
  }

  async getReportTypes(): Promise<ReportType[]> {
    const { data } = await this.client.get<ReportTypesResponse>('/reports/types/list');
    return Array.isArray(data?.types) ? data.types : [];
  }

  async getTemplates(): Promise<string[]> {
    const { data } = await this.client.get<TemplatesResponse>('/reports/templates/list');
    return Array.isArray(data?.templates) ? data.templates : [];
  }

  async createExtraction(request: ExtractionRequest): Promise<ExtractionJob> {
    const { data } = await this.client.post<ExtractionJob>('/extraction', request);
    return data;
  }

  async getExtractionJobs(): Promise<ExtractionJob[]> {
    const { data } = await this.client.get<ExtractionJobListResponse>('/extraction');
    return Array.isArray(data?.jobs) ? data.jobs : [];
  }

  async getExtractionJob(jobId: number): Promise<ExtractionJob> {
    const { data } = await this.client.get<ExtractionJob>(`/extraction/${jobId}`);
    return data;
  }

  async getExtractionAnalise(jobId: number): Promise<AnaliseJob> {
    const { data } = await this.client.get<AnaliseJob>(`/extraction/${jobId}/analise`);
    return data;
  }

  async getSettings(): Promise<SettingsResponse> {
    const { data } = await this.client.get<SettingsResponse>('/settings');
    return data;
  }

  async updateSettings(update: SettingsUpdate): Promise<SettingsResponse> {
    const { data } = await this.client.put<SettingsResponse>('/settings', update);
    return data;
  }

  async getPlatformSessions(): Promise<SessionStatus[]> {
    const { data } = await this.client.get<SessionListResponse>('/sessions');
    return Array.isArray(data?.sessions) ? data.sessions : [];
  }

  async getPlatformSession(fonte: string): Promise<SessionStatus> {
    const { data } = await this.client.get<SessionStatus>(`/sessions/${fonte}`);
    return data;
  }

  async startPlatformLogin(fonte: string, timeout?: number): Promise<SessionStatus> {
    const { data } = await this.client.post<SessionStatus>(`/sessions/${fonte}/login`, null, {
      params: timeout ? { timeout } : undefined,
    });
    return data;
  }

  async logoutPlatform(fonte: string): Promise<SessionStatus> {
    const { data } = await this.client.delete<SessionStatus>(`/sessions/${fonte}`);
    return data;
  }
}

export const api = new ApiService();