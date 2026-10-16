import { useState, useCallback, useEffect } from 'react';
import axios from 'axios';
import { Database, Play, RefreshCw, Loader2, AlertCircle, CheckCircle2, Clock, Info } from 'lucide-react';
import { cn } from '../../lib/utils';
import { api } from '../../lib/api';
import { useExtractionJobs } from '../../hooks/useApi';
import { Button, Badge, Select, Spinner } from '../ui';
import type { SourceType, ContentType, ExtractionJob } from '../../types';

const SOURCE_OPTIONS: { value: SourceType; label: string }[] = [
  { value: 'instagram', label: 'Instagram' },
  { value: 'tiktok', label: 'TikTok' },
  { value: 'youtube', label: 'YouTube' },
  { value: 'reddit', label: 'Reddit' },
  { value: 'wikipedia', label: 'Wikipédia (tópico)' },
];

const CONTENT_TYPE_BY_SOURCE: Record<SourceType, { value: ContentType; label: string }[]> = {
  instagram: [
    { value: 'post', label: 'Posts' },
    { value: 'reel', label: 'Reels' },
    { value: 'comment', label: 'Comentários' },
  ],
  knewin: [{ value: 'news', label: 'Notícias' }],
  twitter: [{ value: 'tweet', label: 'Tweets' }],
  tiktok: [
    { value: 'video', label: 'Vídeo (URL)' },
    { value: 'profile', label: 'Perfil (@usuário)' },
    { value: 'hashtag', label: 'Hashtag / busca' },
  ],
  youtube: [
    { value: 'search', label: 'Vídeos / busca' },
    { value: 'video', label: 'Vídeo (URL)' },
    { value: 'channel', label: 'Canal (perfil)' },
  ],
  reddit: [{ value: 'submission', label: 'Postagem / comunidade' }],
  wikipedia: [{ value: 'topic', label: 'Tópico (pageviews)' }],
  manual: [{ value: 'report', label: 'Relatório' }],
};

const ALVO_FIELD: Partial<Record<SourceType, { label: string; placeholder: string; helper: string }>> = {
  tiktok: {
    label: 'URL do vídeo, @usuário, #hashtag ou termo',
    placeholder: 'https://www.tiktok.com/@user/video/... | @user | #musica | funk 2026',
    helper: 'Aceita URL de vídeo, URL ou @handle de perfil, #hashtag — ou um termo de busca livre.',
  },
  youtube: {
    label: 'URL do vídeo, @canal, link do canal ou termo',
    placeholder: 'https://www.youtube.com/watch?v=... | @canal | ec0nomia',
    helper: 'Aceita URL de vídeo (youtu.be/watch), URL ou @handle de canal — ou um termo de busca livre.',
  },
  reddit: {
    label: 'URL da postagem, r/comunidade, u/usuário ou termo',
    placeholder: 'r/tecnologia | u/spez | https://reddit.com/r/.../comments/...',
    helper: 'Cole a URL de uma postagem ou comunidade, escreva r/subreddit, u/usuário — ou simplesmente um termo de busca.',
  },
  wikipedia: {
    label: 'Artigo da Wikipédia (nome ou URL)',
    placeholder: 'Inteligência artificial | https://pt.wikipedia.org/wiki/Economia',
    helper: 'Coleta visualizações diárias do artigo nos últimos 30 dias (curva de interesse pelo tópico).',
  },
};

const INSTAGRAM_URL_FIELD: Partial<
  Record<ContentType, { label: string; placeholder: string; param: string }>
> = {
  post: {
    label: 'URL do perfil',
    placeholder: 'https://www.instagram.com/usuario/',
    param: 'profile_url',
  },
  reel: {
    label: 'URL do perfil',
    placeholder: 'https://www.instagram.com/usuario/',
    param: 'profile_url',
  },
  comment: {
    label: 'URL da postagem',
    placeholder: 'https://www.instagram.com/p/ABC123/',
    param: 'post_url',
  },
};

const LOGIN_MANUAL_SOURCES: SourceType[] = ['instagram', 'tiktok', 'youtube', 'reddit'];
const inputClass =
  'w-full rounded-lg border border-dark-300 bg-white px-3 py-2 text-sm text-dark-900 placeholder:text-dark-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20';

function statusBadge(status: ExtractionJob['status']) {
  switch (status) {
    case 'completed':
      return (
        <Badge variant="success">
          <CheckCircle2 className="h-3 w-3" /> Concluído
        </Badge>
      );
    case 'running':
      return (
        <Badge variant="info">
          <Loader2 className="h-3 w-3 animate-spin" /> Executando
        </Badge>
      );
    case 'failed':
      return (
        <Badge variant="error">
          <AlertCircle className="h-3 w-3" /> Falhou
        </Badge>
      );
    default:
      return (
        <Badge variant="default">
          <Clock className="h-3 w-3" /> Pendente
        </Badge>
      );
  }
}

export function ScrapersPanel() {
  const [sourceType, setSourceType] = useState<SourceType>('youtube');
  const [contentType, setContentType] = useState<ContentType>('search');
  const [targetUrl, setTargetUrl] = useState('');
  const [alvo, setAlvo] = useState('');
  const [starting, setStarting] = useState(false);
  const [sessionError, setSessionError] = useState<string | null>(null);

  const { jobs, loading, refetch } = useExtractionJobs();

  const alvoField = ALVO_FIELD[sourceType];
  const urlField =
    sourceType === 'instagram' ? INSTAGRAM_URL_FIELD[contentType] : undefined;
  const urlMissing = !!urlField && !targetUrl.trim();
  const alvoMissing = !!alvoField && !alvo.trim();
  const usaLoginManual = LOGIN_MANUAL_SOURCES.includes(sourceType);

  useEffect(() => {
    const hasActiveJob = jobs.some(
      (job) => job.status === 'running' || job.status === 'pending'
    );
    if (!hasActiveJob) return;
    const timer = window.setInterval(() => refetch(), 3000);
    return () => window.clearInterval(timer);
  }, [jobs, refetch]);

  const handleSourceChange = useCallback((value: string) => {
    const source = value as SourceType;
    setSourceType(source);
    setContentType(CONTENT_TYPE_BY_SOURCE[source][0].value);
  }, []);

  const handleStart = useCallback(async () => {
    if (sourceType === 'instagram' && urlField && !targetUrl.trim()) {
      alert(`Informe a ${urlField.label.toLowerCase()} para iniciar a extração.`);
      return;
    }
    if (alvoField && !alvo.trim()) {
      alert(`Informe ${alvoField.label.toLowerCase()} para iniciar a extração.`);
      return;
    }

    if (LOGIN_MANUAL_SOURCES.includes(sourceType)) {
      setSessionError(null);
      try {
        const sessao = await api.getPlatformSession(sourceType);
        if (sessao.status !== 'connected') {
          setSessionError(
            `Conecte a conta ${sessao.nome} na aba Conexões antes de extrair. ` +
            'Clique em Conectar e faça o login manual na janela do navegador.'
          );
          return;
        }
      } catch {
        setSessionError('Não foi possível verificar a sessão. O backend está rodando?');
        return;
      }
    }

    setStarting(true);
    try {
      const queryParams: Record<string, unknown> = {};
      if (urlField) queryParams[urlField.param] = targetUrl.trim();
      if (alvoField) queryParams.alvo = alvo.trim();
      await api.createExtraction({
        source_type: sourceType,
        content_type: contentType,
        query_params: Object.keys(queryParams).length > 0 ? queryParams : undefined,
      });
      refetch();
      setTargetUrl('');
      setAlvo('');
    } catch (error) {
      console.error('Failed to start extraction:', error);
      const detail = axios.isAxiosError(error) ? error.response?.data?.detail : undefined;
      alert(
        typeof detail === 'string'
          ? detail
          : 'Falha ao iniciar extração. Verifique os logs do backend.'
      );
    } finally {
      setStarting(false);
    }
  }, [sourceType, contentType, targetUrl, alvo, urlField, alvoField, refetch]);

  return (
    <div className="flex h-full flex-col bg-white">
      <div className="flex h-16 items-center justify-between border-b border-dark-200 px-4 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-100">
            <Database className="h-5 w-5 text-primary-600" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-dark-900">Scrapers</h1>
            <p className="text-xs text-dark-500">Extração de dados de fontes externas</p>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={refetch} disabled={loading}>
          <RefreshCw className={cn('h-4 w-4', loading && 'animate-spin')} />
          Atualizar
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin p-4 sm:p-6">
        <div className="rounded-xl border border-dark-200 bg-white p-4 sm:p-6 shadow-sm">
          <h2 className="text-sm font-semibold text-dark-900 mb-4">Iniciar nova extração</h2>

          {usaLoginManual && (
            <div className="mb-4 flex gap-3 rounded-lg border border-primary-200 bg-primary-50 px-4 py-3">
              <Info className="mt-0.5 h-4 w-4 shrink-0 text-primary-600" />
              <p className="text-xs leading-relaxed text-primary-800">
                <strong>Requer conexão:</strong> acesse a aba <strong>Conexões</strong>, clique em
                Conectar e faça o login manual na janela do navegador. A sessão fica salva em{' '}
                <code className="rounded bg-primary-100 px-1">data/browser_profiles/</code> e é
                reutilizada nas próximas extrações — depois disso a coleta roda sozinha.
              </p>
            </div>
          )}

          {sessionError && (
            <div className="mb-4 rounded-lg border border-danger-300 bg-danger-50 px-4 py-3 text-sm text-danger-700">
              {sessionError}
            </div>
          )}

          <div className="grid gap-4 sm:grid-cols-3">
            <div>
              <label className="mb-1.5 block text-xs font-medium text-dark-600">Fonte</label>
              <Select value={sourceType} options={SOURCE_OPTIONS} onChange={handleSourceChange} />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-dark-600">Tipo de conteúdo</label>
              <Select
                value={contentType}
                options={CONTENT_TYPE_BY_SOURCE[sourceType]}
                onChange={(v) => setContentType(v as ContentType)}
              />
            </div>
          </div>

          {alvoField && (
            <div className="mt-4">
              <label className="mb-1.5 block text-xs font-medium text-dark-600">
                {alvoField.label} <span className="text-red-500">(obrigatório)</span>
              </label>
              <input
                type="text"
                value={alvo}
                onChange={(e) => setAlvo(e.target.value)}
                placeholder={alvoField.placeholder}
                className={inputClass}
              />
              <p className="mt-1 text-xs text-dark-500">{alvoField.helper}</p>
            </div>
          )}

          {urlField && (
            <div className="mt-4">
              <label className="mb-1.5 block text-xs font-medium text-dark-600">
                {urlField.label} <span className="text-red-500">(obrigatório)</span>
              </label>
              <input
                type="url"
                value={targetUrl}
                onChange={(e) => setTargetUrl(e.target.value)}
                placeholder={urlField.placeholder}
                className={inputClass}
              />
            </div>
          )}

          <div className="mt-4 flex justify-end">
            <Button
              onClick={handleStart}
              disabled={starting || urlMissing || alvoMissing}
              className="flex items-center gap-2"
            >
              {starting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
              Iniciar Extração
            </Button>
          </div>
        </div>

        <div className="mt-6">
          <h2 className="text-sm font-semibold text-dark-900 mb-3">Histórico de extrações</h2>
          {loading && !jobs.length ? (
            <div className="flex h-40 items-center justify-center">
              <Spinner size="lg" />
            </div>
          ) : jobs.length === 0 ? (
            <div className="flex h-40 flex-col items-center justify-center text-center text-dark-500 rounded-xl border border-dashed border-dark-300">
              <Database className="h-10 w-10 mb-2 text-dark-300" />
              <p className="text-sm">Nenhuma extração executada ainda</p>
            </div>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-dark-200">
              <table className="min-w-full divide-y divide-dark-200 text-sm">
                <thead className="bg-dark-50">
                  <tr>
                    <th className="px-4 py-2.5 text-left font-medium text-dark-600">ID</th>
                    <th className="px-4 py-2.5 text-left font-medium text-dark-600">Fonte</th>
                    <th className="px-4 py-2.5 text-left font-medium text-dark-600">Conteúdo</th>
                    <th className="px-4 py-2.5 text-left font-medium text-dark-600">Status</th>
                    <th className="px-4 py-2.5 text-left font-medium text-dark-600">Extraídos</th>
                    <th className="px-4 py-2.5 text-left font-medium text-dark-600">Armazenados</th>
                    <th className="px-4 py-2.5 text-left font-medium text-dark-600">Iniciado</th>
                    <th className="px-4 py-2.5 text-left font-medium text-dark-600">Erro</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-dark-200">
                  {jobs.map((job) => (
                    <tr key={job.id} className="hover:bg-dark-50">
                      <td className="px-4 py-2.5 text-dark-900">#{job.id}</td>
                      <td className="px-4 py-2.5 text-dark-900 capitalize">{job.source_type}</td>
                      <td className="px-4 py-2.5 text-dark-600 capitalize">{job.content_type}</td>
                      <td className="px-4 py-2.5">{statusBadge(job.status)}</td>
                      <td className="px-4 py-2.5 text-dark-900">{job.items_extracted}</td>
                      <td className="px-4 py-2.5 text-dark-900">{job.items_stored}</td>
                      <td className="px-4 py-2.5 text-dark-500">
                        {new Date(job.started_at).toLocaleString('pt-BR')}
                      </td>
                      <td className="px-4 py-2.5">
                        {job.error_message ? (
                          <span
                            className="block max-w-xs truncate text-xs text-red-600"
                            title={job.error_message}
                          >
                            {job.error_message}
                          </span>
                        ) : (
                          <span className="text-xs text-dark-400">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
