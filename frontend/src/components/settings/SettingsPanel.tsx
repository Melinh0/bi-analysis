import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
  Settings,
  Server,
  Cpu,
  Database,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Save,
  Eye,
  EyeOff,
  KeyRound,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { api } from '../../lib/api';
import { useModels } from '../../hooks/useApi';
import { Button, Badge, Spinner, Card, CardHeader, CardBody, CardTitle, CardDescription } from '../ui';
import type { AppSettings, SettingsUpdate } from '../../types';

interface HealthInfo {
  status: string;
  version: string;
}

function Field({
  label,
  value,
  onChange,
  type = 'text',
  placeholder,
  helperText,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: 'text' | 'password' | 'url';
  placeholder?: string;
  helperText?: string;
}) {
  const [visible, setVisible] = useState(false);
  const isSecret = type === 'password';

  return (
    <div>
      <label className="mb-1.5 block text-xs font-medium text-dark-600">{label}</label>
      <div className="relative">
        <input
          type={isSecret && visible ? 'text' : type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          autoComplete="off"
          spellCheck={false}
          className="w-full rounded-lg border border-dark-300 bg-white px-3 py-2 text-sm text-dark-900 placeholder:text-dark-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
          style={isSecret ? { paddingRight: '2.25rem' } : undefined}
        />
        {isSecret && (
          <button
            type="button"
            onClick={() => setVisible((v) => !v)}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-dark-400 hover:text-dark-600"
            aria-label={visible ? 'Ocultar valor' : 'Mostrar valor'}
            tabIndex={-1}
          >
            {visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        )}
      </div>
      {helperText && <p className="mt-1 text-xs text-dark-500">{helperText}</p>}
    </div>
  );
}

function SectionCard({
  icon,
  title,
  description,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          {icon}
          <CardTitle className="text-base">{title}</CardTitle>
        </div>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardBody className="grid gap-4 sm:grid-cols-2">{children}</CardBody>
    </Card>
  );
}

export function SettingsPanel() {
  const { models, loading: modelsLoading, refetch: refetchModels } = useModels();
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);

  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [draft, setDraft] = useState<AppSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [envFile, setEnvFile] = useState<string>('.env');
  const [envExists, setEnvExists] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await api.healthCheck();
        if (!cancelled) setHealth(data);
      } catch {
        if (!cancelled) setHealth({ status: 'error', version: '—' });
      } finally {
        if (!cancelled) setHealthLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const loadSettings = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const data = await api.getSettings();
      const normalized: AppSettings = {
        ollama_base_url: data.settings?.ollama_base_url ?? '',
        ollama_api_key: data.settings?.ollama_api_key ?? '',
        ollama_model: data.settings?.ollama_model ?? '',
        ollama_embedding_model: data.settings?.ollama_embedding_model ?? '',
        ollama_available_models: data.settings?.ollama_available_models ?? '',
        instagram_email: data.settings?.instagram_email ?? '',
        instagram_password: data.settings?.instagram_password ?? '',
        log_level: data.settings?.log_level ?? 'INFO',
      };
      setSettings(normalized);
      setDraft(normalized);
      setEnvFile(data.env_file);
      setEnvExists(data.env_exists);
    } catch {
      setLoadError('Não foi possível carregar as configurações do backend.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  const dirty = !!settings && !!draft && JSON.stringify(settings) !== JSON.stringify(draft);

  const update = useCallback((key: keyof AppSettings, value: string) => {
    setDraft((current) => (current ? { ...current, [key]: value } : current));
  }, []);

  const handleSave = useCallback(async () => {
    if (!settings || !draft) return;
    setSaving(true);
    setSaveError(null);
    try {
      const payload: SettingsUpdate = {};
      (Object.keys(draft) as (keyof AppSettings)[]).forEach((key) => {
        if (draft[key] !== settings[key]) payload[key] = draft[key];
      });
      if (Object.keys(payload).length > 0) {
        const data = await api.updateSettings(payload);
        setSettings(data.settings);
        setDraft(data.settings);
        setEnvFile(data.env_file);
        setEnvExists(data.env_exists);
        setSaved(true);
        window.setTimeout(() => setSaved(false), 3000);
        refetchModels();
      }
    } catch (err) {
      const detail = axios.isAxiosError(err) ? err.response?.data?.detail : undefined;
      setSaveError(typeof detail === 'string' ? detail : 'Falha ao salvar as configurações.');
    } finally {
      setSaving(false);
    }
  }, [settings, draft, refetchModels]);

  const availableModelNames = models?.models.map((m) => m.name).join(', ') ?? '';

  return (
    <div className="flex h-full flex-col bg-white">
      <div className="flex h-16 items-center justify-between border-b border-dark-200 px-4 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-100">
            <Settings className="h-5 w-5 text-primary-600" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-dark-900">Configurações</h1>
            <p className="text-xs text-dark-500">Credenciais dos scrapers, modelos e status do sistema</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => { refetchModels(); loadSettings(); }}
            disabled={modelsLoading || loading}
          >
            <RefreshCw className={cn('h-4 w-4', (modelsLoading || loading) && 'animate-spin')} />
            Atualizar
          </Button>
          <Button
            size="sm"
            onClick={handleSave}
            disabled={!dirty || saving || loading}
            loading={saving}
          >
            {saved ? <CheckCircle2 className="h-4 w-4" /> : <Save className="h-4 w-4" />}
            {saved ? 'Salvo' : 'Salvar'}
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin p-4 sm:p-6 space-y-6">
        {saveError && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {saveError}
          </div>
        )}

        {}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Server className="h-5 w-5 text-primary-600" />
              <CardTitle className="text-base">Sistema</CardTitle>
            </div>
            <CardDescription>Status do backend e versão em execução</CardDescription>
          </CardHeader>
          <CardBody className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-dark-600">Status do backend</span>
              {healthLoading ? (
                <Spinner size="sm" />
              ) : health?.status === 'ok' ? (
                <Badge variant="success">
                  <CheckCircle2 className="h-3 w-3" /> Online
                </Badge>
              ) : (
                <Badge variant="error">
                  <XCircle className="h-3 w-3" /> Offline
                </Badge>
              )}
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-dark-600">Versão</span>
              <span className="text-sm font-medium text-dark-900">{health?.version || '—'}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-dark-600">Modelo de embedding</span>
              <span className="text-sm font-medium text-dark-900">{models?.embedding_model || '—'}</span>
            </div>
            <div className="flex items-center justify-between gap-4">
              <span className="text-sm text-dark-600">Arquivo de configuração</span>
              <span className="truncate text-xs font-medium text-dark-900" title={envFile}>
                {envFile}
                {!envExists && <span className="ml-2 text-dark-400">(será criado ao salvar)</span>}
              </span>
            </div>
          </CardBody>
        </Card>

        {loading ? (
          <div className="flex h-40 items-center justify-center">
            <Spinner size="lg" />
          </div>
        ) : loadError ? (
          <div className="flex h-40 flex-col items-center justify-center gap-3 text-center">
            <p className="text-sm text-red-600">{loadError}</p>
            <Button variant="outline" size="sm" onClick={loadSettings}>
              Tentar novamente
            </Button>
          </div>
        ) : draft ? (
          <>
            {}
            <SectionCard
              icon={<Cpu className="h-5 w-5 text-primary-600" />}
              title="Modelos de IA (Ollama)"
              description="Endpoint, chave e modelos usados no chat e nos relatórios"
            >
              <Field
                label="URL base"
                value={draft.ollama_base_url}
                onChange={(v) => update('ollama_base_url', v)}
                type="url"
                placeholder="https://api.ollama.com"
              />
              <Field
                label="Chave de API"
                value={draft.ollama_api_key}
                onChange={(v) => update('ollama_api_key', v)}
                type="password"
                placeholder="chave da API do Ollama"
              />
              <Field
                label="Modelo padrão"
                value={draft.ollama_model}
                onChange={(v) => update('ollama_model', v)}
                placeholder="ex.: gemma4:cloud"
                helperText={
                  availableModelNames
                    ? `Disponíveis: ${availableModelNames}`
                    : 'Nenhum modelo listado pelo backend'
                }
              />
              <Field
                label="Modelo de embedding"
                value={draft.ollama_embedding_model}
                onChange={(v) => update('ollama_embedding_model', v)}
                placeholder="ex.: nomic-embed-text"
              />
              <div className="sm:col-span-2">
                <Field
                  label="Modelos disponíveis (separados por vírgula)"
                  value={draft.ollama_available_models}
                  onChange={(v) => update('ollama_available_models', v)}
                  placeholder="gemma4:cloud, qwen2.5-coder:1.5b-base"
                />
              </div>
            </SectionCard>

            {}
            <SectionCard
              icon={<KeyRound className="h-5 w-5 text-primary-600" />}
              title="Instagram"
              description="Opcional: a sessão é gerenciada na aba Conexões; credenciais aqui são apenas fallback"
            >
              <Field
                label="E-mail"
                value={draft.instagram_email}
                onChange={(v) => update('instagram_email', v)}
                placeholder="seu@email.com"
              />
              <Field
                label="Senha"
                value={draft.instagram_password}
                onChange={(v) => update('instagram_password', v)}
                type="password"
                placeholder="senha do Instagram"
              />
            </SectionCard>

            {}
            <SectionCard
              icon={<Database className="h-5 w-5 text-primary-600" />}
              title="Geral"
              description="Nível de log do backend"
            >
              <Field
                label="Nível de log"
                value={draft.log_level}
                onChange={(v) => update('log_level', v.toUpperCase())}
                placeholder="INFO"
                helperText="Valores aceitos: DEBUG, INFO, WARNING, ERROR"
              />
            </SectionCard>
          </>
        ) : null}

        {}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Database className="h-5 w-5 text-primary-600" />
              <CardTitle className="text-base">Sobre</CardTitle>
            </div>
          </CardHeader>
          <CardBody className="space-y-2 text-sm text-dark-600">
            <p>
              <span className="font-medium text-dark-900">BI Analysis</span> — Plataforma de análise de
              inteligência de negócio com extração de dados, pipeline RAG e relatórios.
            </p>
            <p className="text-xs text-dark-500">
              LLM local via Ollama · Base de dados vetorial · Geração de relatórios com IA
            </p>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
