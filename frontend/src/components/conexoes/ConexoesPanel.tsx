import { useCallback, useEffect, useRef, useState } from 'react';
import {
  Plug,
  RefreshCw,
  Loader2,
  LogIn,
  LogOut,
  CheckCircle2,
  XCircle,
  Clock,
  ShieldCheck,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { api } from '../../lib/api';
import { Button, Card, CardBody, CardHeader, CardTitle, CardDescription } from '../ui';
import type { SessionStatus, SessionStatusValue } from '../../types';

const POLL_MS = 2500;

const STATUS_LABEL: Record<SessionStatusValue, string> = {
  connected: 'Conectado',
  disconnected: 'Desconectado',
  logging_in: 'Aguardando login…',
  failed: 'Falha',
};

function StatusBadge({ status }: { status: SessionStatusValue }) {
  const map: Record<SessionStatusValue, { cls: string; Icon: typeof CheckCircle2 }> = {
    connected: { cls: 'bg-success-50 text-success-700', Icon: CheckCircle2 },
    disconnected: { cls: 'bg-dark-100 text-dark-600', Icon: XCircle },
    logging_in: { cls: 'bg-warning-50 text-warning-700', Icon: Clock },
    failed: { cls: 'bg-danger-50 text-danger-700', Icon: XCircle },
  };
  const { cls, Icon } = map[status] ?? map.disconnected;
  return (
    <span className={cn('inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium', cls)}>
      <Icon className="h-3.5 w-3.5" />
      {STATUS_LABEL[status] ?? status}
    </span>
  );
}

function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export function ConexoesPanel() {
  const [sessions, setSessions] = useState<SessionStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await api.getPlatformSessions();
      setSessions(data);
      setError(null);
    } catch {
      setError('Não foi possível carregar as conexões. O backend está rodando?');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(load, POLL_MS);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [load]);

  const handleLogin = useCallback(
    async (fonte: string) => {
      setActionError(null);
      try {
        const updated = await api.startPlatformLogin(fonte);
        setSessions((prev) => prev.map((s) => (s.fonte === fonte ? updated : s)));
      } catch (err) {
        const detail =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
          'Falha ao iniciar o login.';
        setActionError(detail);
      }
    },
    []
  );

  const handleLogout = useCallback(
    async (fonte: string) => {
      setActionError(null);
      try {
        const updated = await api.logoutPlatform(fonte);
        setSessions((prev) => prev.map((s) => (s.fonte === fonte ? updated : s)));
      } catch {
        setActionError('Falha ao desconectar a sessão.');
      }
    },
    []
  );

  return (
    <div className="flex-1 overflow-y-auto p-4 lg:p-6">
      <div className="mx-auto max-w-3xl space-y-6">
        <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-dark-900">Conexões</h1>
            <p className="text-sm text-dark-500">
              Conecte as plataformas <strong>antes</strong> de extrair dados. O login é feito manualmente no navegador.
            </p>
          </div>
          <Button variant="outline" onClick={() => { setLoading(true); load(); }} className="mt-2 sm:mt-0">
            <RefreshCw className="mr-2 h-4 w-4" />
            Atualizar
          </Button>
        </div>

        {actionError && (
          <div className="rounded-lg border border-danger-300 bg-danger-50 px-4 py-3 text-sm text-danger-700">
            {actionError}
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-danger-300 bg-danger-50 px-4 py-3 text-sm text-danger-700">
            {error}
          </div>
        )}

        {loading && sessions.length === 0 ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
          </div>
        ) : (
          <div className="space-y-4">
            {sessions.map((s) => (
              <Card key={s.fonte}>
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-50">
                        <Plug className="h-5 w-5 text-primary-600" />
                      </div>
                      <div>
                        <CardTitle className="text-base">{s.nome}</CardTitle>
                        <CardDescription className="mt-0.5">
                          <StatusBadge status={s.status} />
                        </CardDescription>
                      </div>
                    </div>
                    <div className="flex flex-shrink-0 items-center gap-2">
                      {s.status === 'connected' && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleLogout(s.fonte)}
                        >
                          <LogOut className="mr-1.5 h-3.5 w-3.5" />
                          Desconectar
                        </Button>
                      )}
                      {(s.status === 'disconnected' || s.status === 'failed') && (
                        <Button
                          size="sm"
                          onClick={() => handleLogin(s.fonte)}
                        >
                          <LogIn className="mr-1.5 h-3.5 w-3.5" />
                          Conectar
                        </Button>
                      )}
                      {s.status === 'logging_in' && (
                        <Button size="sm" disabled>
                          <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
                          Aguardando…
                        </Button>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardBody className="pt-0">
                  {s.status === 'logging_in' && (
                    <div className="rounded-lg border border-warning-300 bg-warning-50 px-4 py-3 text-sm text-warning-800">
                      <p className="flex items-center gap-2 font-medium">
                        <Clock className="h-4 w-4" />
                        Janela do navegador aberta
                      </p>
                      <p className="mt-1">
                        Faça o login na janela do {s.nome} que foi aberta. Ao concluir, o status aqui atualiza sozinho.
                      </p>
                    </div>
                  )}
                  {s.status === 'failed' && s.error && (
                    <div className="rounded-lg border border-danger-300 bg-danger-50 px-4 py-3 text-sm text-danger-700">
                      {s.error}
                    </div>
                  )}
                  {s.status === 'disconnected' && !s.error && (
                    <div className="flex items-start gap-2 rounded-lg bg-dark-50 px-4 py-3 text-sm text-dark-600">
                      <ShieldCheck className="mt-0.5 h-4 w-4 flex-shrink-0 text-dark-400" />
                      <p>
                        Sem sessão ativa. Clique em <strong>Conectar</strong> para abrir o navegador e fazer o login.
                        A sessão é salva no perfil do navegador e reutilizada nas extrações.
                      </p>
                    </div>
                  )}
                  {s.status === 'connected' && (
                    <div className="grid grid-cols-1 gap-2 text-sm text-dark-600 sm:grid-cols-2">
                      <p>
                        <span className="text-dark-400">Último login:</span>{' '}
                        {formatDate(s.last_login)}
                      </p>
                      <p>
                        <span className="text-dark-400">Última validação:</span>{' '}
                        {formatDate(s.last_validated)}
                      </p>
                    </div>
                  )}
                </CardBody>
              </Card>
            ))}
          </div>
        )}

        <div className="rounded-lg border border-dark-200 bg-dark-50 px-4 py-3 text-xs text-dark-500">
          <p>
            <strong>Como funciona:</strong> ao clicar em Conectar, um navegador Chrome abre na tela. Faça o login
            normalmente (incluindo 2FA, se houver). A sessão fica salva e é reutilizada nas extrações — não é
            preciso conectar de novo a cada extração.
          </p>
        </div>
      </div>
    </div>
  );
}
