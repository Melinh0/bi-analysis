export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  session_id: string;
  message_id: number;
  sources?: Source[];
  created_at?: string;
}

export interface Source {
  content: string;
  metadata: Record<string, unknown>;
  distance?: number;
}

export interface ChatSession {
  session_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChatHistoryResponse {
  messages: ChatMessage[];
}

export interface Model {
  name: string;
  available: boolean;
}

export interface ModelsResponse {
  current_model: string;
  embedding_model: string;
  models: Model[];
}

export interface Report {
  id: number;
  title: string;
  report_type: string;
  status: 'pending' | 'generating' | 'generated' | 'failed';
  generated_content: string | null;
  created_at: string;
  generated_at: string | null;
  filters?: Record<string, unknown>;
}

export interface ReportListResponse {
  reports: Report[];
}

export interface ReportRequest {
  title: string;
  report_type: string;
  filters: Record<string, unknown>;
  template?: string;
}

export interface ReportType {
  id: string;
  name: string;
  description: string;
}

export interface ReportTypesResponse {
  types: ReportType[];
}

export interface Template {
  name: string;
  description: string;
}

export interface TemplatesResponse {
  templates: string[];
}

export interface HealthResponse {
  status: string;
  version: string;
  database: string;
  ollama: string;
}


export type SourceType = 'instagram' | 'knewin' | 'twitter' | 'youtube' | 'reddit' | 'wikipedia' | 'manual' | 'tiktok';

export type ContentType = 'post' | 'comment' | 'reel' | 'news' | 'tweet' | 'video' | 'channel' | 'search' | 'submission' | 'topic' | 'report' | 'profile' | 'hashtag';

export interface ExtractionJob {
  id: number;
  source_type: SourceType;
  content_type: ContentType;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at: string;
  completed_at: string | null;
  items_extracted: number;
  items_stored: number;
  error_message: string | null;
}

export interface ExtractionJobListResponse {
  jobs: ExtractionJob[];
}

export interface ExtractionRequest {
  source_type: SourceType;
  content_type: ContentType;
  query_params?: Record<string, unknown>;
}

export interface ScheduledJob {
  id: number;
  name: string;
  source_type: SourceType;
  content_type: ContentType;
  cron_expression: string;
  is_active: boolean;
  last_run: string | null;
  next_run: string | null;
}

export interface AppSettings {
  ollama_base_url: string;
  ollama_api_key: string;
  ollama_model: string;
  ollama_embedding_model: string;
  ollama_available_models: string;
  instagram_email: string;
  instagram_password: string;
  log_level: string;
}

export type SettingsUpdate = Partial<AppSettings>;

export interface SettingsResponse {
  settings: AppSettings;
  env_file: string;
  env_exists: boolean;
}

export interface AnaliseItem {
  id: number;
  external_id?: string | null;
  url?: string | null;
  autor?: string | null;
  plataforma?: string | null;
  tipo_item?: string | null;
  imagem?: string | null;
  titulo: string;
  conteudo: string;
  publicado_em?: string | null;
  data?: string | null;
  curtidas?: number | null;
  comentarios?: number | null;
  visualizacoes?: number | null;
  pontuacao?: number | null;
  compartilhamentos?: number | null;
  engajamento: number;
}

export interface AnalisePerfil {
  id: number;
  titulo: string;
  url?: string | null;
  autor?: string | null;
  descricao?: string | null;
  imagem?: string | null;
  inscritos?: number | null;
  visualizacoes_totais?: number | null;
  karma_total?: number | null;
  videos?: number | null;
  online?: number | null;
  data?: string | null;
  engajamento: number;
}

export interface AnaliseResumo {
  total_itens: number;
  total_perfis: number;
  totais: Record<string, number>;
  engajamento_total: number;
  media_engajamento: number;
  visualizacoes_total: number;
  taxa_engajamento?: number | null;
  destaque?: { id: number; titulo: string; url?: string | null; engajamento: number } | null;
}

export interface AnalisePontoSerie {
  data: string;
  engajamento?: number;
  visualizacoes?: number;
  comentarios?: number;
  itens?: number;
}

export interface AnaliseRanking {
  posicao: number;
  id: number;
  titulo: string;
  url?: string | null;
  autor?: string | null;
  valor: number;
  curtidas?: number | null;
  comentarios?: number | null;
  visualizacoes?: number | null;
  metrica: string;
}

export interface AnaliseJob {
  job_id: number;
  fonte: string;
  tipo_conteudo: string;
  status: string;
  alvo?: string | null;
  iniciado_em?: string | null;
  resumo: AnaliseResumo;
  perfis: AnalisePerfil[];
  itens: AnaliseItem[];
  serie_temporal: AnalisePontoSerie[];
  ranking: AnaliseRanking[];
}

export type SessionStatusValue = 'connected' | 'disconnected' | 'logging_in' | 'failed';

export interface SessionStatus {
  fonte: string;
  nome: string;
  status: SessionStatusValue;
  last_login?: string | null;
  last_validated?: string | null;
  error?: string | null;
}

export interface SessionListResponse {
  sessions: SessionStatus[];
}