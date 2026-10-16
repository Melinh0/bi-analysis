import { useCallback, useState } from 'react';
import axios from 'axios';
import { BarChart3, Download, FileText, RefreshCw } from 'lucide-react';
import { cn } from '../../lib/utils';
import { api } from '../../lib/api';
import { useExtractionJobs } from '../../hooks/useApi';
import { Button, Badge, Card, CardBody, CardHeader, CardTitle, Spinner } from '../ui';
import { GraficoBarras, GraficoLinha, formatarNumero, formatarTaxa } from './Graficos';
import type { AnaliseJob, ExtractionJob } from '../../types';

function Kpi({ titulo, valor, ajuda }: { titulo: string; valor: string; ajuda?: string }) {
  return (
    <div className="rounded-xl border border-dark-200 bg-white p-4">
      <p className="text-xs font-medium text-dark-500">{titulo}</p>
      <p className="mt-1 text-xl font-semibold text-dark-900">{valor}</p>
      {ajuda && <p className="mt-0.5 text-[11px] text-dark-400">{ajuda}</p>}
    </div>
  );
}

function exportarCsv(analise: AnaliseJob) {
  const colunas = ['id', 'titulo', 'autor', 'url', 'data', 'curtidas', 'comentarios', 'visualizacoes', 'pontuacao', 'compartilhamentos', 'engajamento'];
  const linhas = (analise.itens || []).map((item) =>
    [
      item.id,
      (item.titulo || '').replace(/"/g, '""'),
      item.autor || '',
      item.url || '',
      item.data || '',
      item.curtidas ?? '',
      item.comentarios ?? '',
      item.visualizacoes ?? '',
      item.pontuacao ?? '',
      item.compartilhamentos ?? '',
      item.engajamento ?? '',
    ].join(';')
  );
  const csv = [colunas.join(';'), ...linhas].join('\n');
  const blob = new Blob([`\ufeff${csv}`], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `analise_job_${analise.job_id}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

const ROTULO_FONTE: Record<string, string> = {
  youtube: 'YouTube',
  reddit: 'Reddit',
  wikipedia: 'Wikipédia',
  instagram: 'Instagram',
  tiktok: 'TikTok',
  twitter: 'Twitter / X (removido)',
  knewin: 'Knewin (removido)',
  manual: 'Manual',
};

export function AnalisePanel() {
  const { jobs, loading, refetch } = useExtractionJobs();
  const [jobSelecionado, setJobSelecionado] = useState<AnaliseJob | null>(null);
  const [jobIdSelecionado, setJobIdSelecionado] = useState<number | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [mensagemRelatorio, setMensagemRelatorio] = useState<string | null>(null);
  const [gerando, setGerando] = useState(false);

  const jobsAnalisaveis: ExtractionJob[] = jobs
    .filter((job) => job.status === 'completed' && job.items_stored > 0)
    .slice(0, 30);

  const analisar = useCallback(async (jobId: number) => {
    setJobIdSelecionado(jobId);
    setCarregando(true);
    setErro(null);
    setMensagemRelatorio(null);
    try {
      setJobSelecionado(await api.getExtractionAnalise(jobId));
    } catch {
      setErro('Não foi possível carregar a análise deste job.');
    } finally {
      setCarregando(false);
    }
  }, []);

  const gerarRelatorio = useCallback(async () => {
    if (!jobSelecionado) return;
    setGerando(true);
    setMensagemRelatorio(null);
    try {
      await api.createReport({
        title: `Análise do job #${jobSelecionado.job_id} — ${ROTULO_FONTE[jobSelecionado.fonte] || jobSelecionado.fonte}`,
        report_type: 'trend_report',
        filters: {
          source_type: jobSelecionado.fonte,
          content_type: jobSelecionado.tipo_conteudo,
        },
      });
      setMensagemRelatorio('Relatório em geração — acompanhe na aba Relatórios.');
    } catch (error) {
      const detail = axios.isAxiosError(error) ? error.response?.data?.detail : undefined;
      setMensagemRelatorio(
        typeof detail === 'string' ? `Falha ao gerar relatório: ${detail}` : 'Falha ao gerar relatório.'
      );
    } finally {
      setGerando(false);
    }
  }, [jobSelecionado]);

  const analise = jobSelecionado;

  return (
    <div className="flex h-full flex-col bg-white">
      <div className="flex h-16 items-center justify-between border-b border-dark-200 px-4 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-100">
            <BarChart3 className="h-5 w-5 text-primary-600" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-dark-900">Análises</h1>
            <p className="text-xs text-dark-500">Gráficos, comparações e relatórios dos dados coletados</p>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={refetch} disabled={loading}>
          <RefreshCw className={cn('h-4 w-4', loading && 'animate-spin')} />
          Atualizar
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin p-4 sm:p-6">
        <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
          <div className="rounded-xl border border-dark-200 bg-white">
            <div className="border-b border-dark-200 px-4 py-3">
              <h2 className="text-sm font-semibold text-dark-900">Extrações concluídas</h2>
              <p className="text-xs text-dark-500">Escolha um job para analisar</p>
            </div>
            <div className="max-h-[520px] divide-y divide-dark-100 overflow-y-auto">
              {jobsAnalisaveis.length === 0 ? (
                <p className="px-4 py-8 text-center text-sm text-dark-500">
                  Nenhuma extração concluída ainda. Execute uma extração em Scrapers.
                </p>
              ) : (
                jobsAnalisaveis.map((job) => (
                  <button
                    key={job.id}
                    onClick={() => analisar(job.id)}
                    className={cn(
                      'flex w-full items-center justify-between gap-2 px-4 py-3 text-left transition-colors hover:bg-dark-50',
                      jobIdSelecionado === job.id && 'bg-primary-50'
                    )}
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-dark-900">
                        #{job.id} · {ROTULO_FONTE[job.source_type] || job.source_type}
                      </p>
                      <p className="truncate text-xs text-dark-500">
                        {job.content_type} · {new Date(job.started_at).toLocaleString('pt-BR')}
                      </p>
                    </div>
                    <Badge variant="success">{job.items_stored} itens</Badge>
                  </button>
                ))
              )}
            </div>
          </div>

          <div className="space-y-6">
            {carregando ? (
              <div className="flex h-64 items-center justify-center">
                <Spinner size="lg" />
              </div>
            ) : erro ? (
              <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{erro}</div>
            ) : !analise ? (
              <div className="flex h-64 flex-col items-center justify-center rounded-xl border border-dashed border-dark-300 text-center text-dark-500">
                <BarChart3 className="mb-2 h-10 w-10 text-dark-300" />
                <p className="text-sm">Selecione uma extração concluída para ver a análise</p>
              </div>
            ) : (
              <>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-base font-semibold text-dark-900">
                      Job #{analise.job_id} · {ROTULO_FONTE[analise.fonte] || analise.fonte}
                    </h2>
                    <p className="text-xs text-dark-500">
                      {analise.alvo || 'alvo não informado'} · {analise.tipo_conteudo}
                      {analise.iniciado_em ? ` · iniciado em ${new Date(analise.iniciado_em).toLocaleString('pt-BR')}` : ''}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => exportarCsv(analise)}>
                      <Download className="h-4 w-4" />
                      CSV
                    </Button>
                    <Button size="sm" onClick={gerarRelatorio} loading={gerando}>
                      <FileText className="h-4 w-4" />
                      Gerar relatório
                    </Button>
                  </div>
                </div>

                {mensagemRelatorio && (
                  <div className="rounded-lg border border-primary-200 bg-primary-50 px-4 py-3 text-sm text-primary-800">
                    {mensagemRelatorio}
                  </div>
                )}

                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  <Kpi titulo="Itens analisados" valor={String(analise.resumo.total_itens)} />
                  <Kpi titulo="Engajamento total" valor={formatarNumero(analise.resumo.engajamento_total)} ajuda="curtidas + comentários + compartilhamentos" />
                  <Kpi titulo="Visualizações" valor={formatarNumero(analise.resumo.visualizacoes_total)} />
                  <Kpi
                    titulo="Taxa de engajamento"
                    valor={formatarTaxa(analise.resumo.taxa_engajamento)}
                    ajuda="engajamento / visualizações"
                  />
                </div>

                {analise.perfis.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Perfis / comunidades</CardTitle>
                    </CardHeader>
                    <CardBody className="grid gap-3 sm:grid-cols-2">
                      {(analise.perfis || []).map((perfil) => (
                        <div key={perfil.id} className="rounded-lg border border-dark-200 p-3">
                          <p className="truncate text-sm font-medium text-dark-900">{perfil.titulo}</p>
                          {perfil.url && (
                            <a
                              href={perfil.url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-xs text-primary-600 hover:underline"
                            >
                              abrir perfil
                            </a>
                          )}
                          <div className="mt-2 flex flex-wrap gap-3 text-xs text-dark-500">
                            {perfil.inscritos !== null && perfil.inscritos !== undefined && (
                              <span>{formatarNumero(perfil.inscritos)} inscritos</span>
                            )}
                            {perfil.karma_total !== null && perfil.karma_total !== undefined && (
                              <span>{formatarNumero(perfil.karma_total)} karma</span>
                            )}
                            {perfil.visualizacoes_totais !== null && perfil.visualizacoes_totais !== undefined && (
                              <span>{formatarNumero(perfil.visualizacoes_totais)} views totais</span>
                            )}
                            {perfil.videos !== null && perfil.videos !== undefined && (
                              <span>{formatarNumero(perfil.videos)} vídeos</span>
                            )}
                            {perfil.online !== null && perfil.online !== undefined && (
                              <span>{formatarNumero(perfil.online)} online</span>
                            )}
                          </div>
                          {perfil.descricao && (
                            <p className="mt-2 line-clamp-2 text-xs text-dark-500">{perfil.descricao}</p>
                          )}
                        </div>
                      ))}
                    </CardBody>
                  </Card>
                )}

                <div className="grid gap-4 lg:grid-cols-2">
                  <GraficoBarras
                    titulo="Top 10 por engajamento"
                    dados={(analise.ranking || []).map((r) => ({
                      rotulo: (r.titulo || `#${r.id}`).slice(0, 18),
                      valor: r.valor,
                      cor: '#6366f1',
                    }))}
                  />
                  <GraficoLinha
                    titulo="Evolução no tempo (engajamento por dia)"
                    dados={(analise.serie_temporal || []).map((p) => ({
                      rotulo: p.data,
                      valor: p.engajamento || 0,
                    }))}
                    cor="#0ea5e9"
                  />
                  <GraficoBarras
                    titulo="Top 10 por visualizações"
                    dados={[...(analise.itens || [])]
                      .sort((a, b) => (b.visualizacoes || 0) - (a.visualizacoes || 0))
                      .slice(0, 10)
                      .map((item) => ({
                        rotulo: (item.titulo || `#${item.id}`).slice(0, 18),
                        valor: item.visualizacoes || 0,
                        cor: '#22c55e',
                      }))}
                  />
                  <GraficoLinha
                    titulo="Evolução no tempo (visualizações por dia)"
                    dados={(analise.serie_temporal || []).map((p) => ({
                      rotulo: p.data,
                      valor: p.visualizacoes || 0,
                    }))}
                    cor="#f59e0b"
                  />
                </div>

                <div>
                  <h3 className="mb-2 text-sm font-semibold text-dark-900">
                    Tabela comparativa ({(analise.itens || []).length} itens)
                  </h3>
                  <div className="max-h-96 overflow-auto rounded-xl border border-dark-200">
                    <table className="min-w-full divide-y divide-dark-200 text-sm">
                      <thead className="sticky top-0 bg-dark-50">
                        <tr>
                          <th className="px-3 py-2 text-left font-medium text-dark-600">#</th>
                          <th className="px-3 py-2 text-left font-medium text-dark-600">Título</th>
                          <th className="px-3 py-2 text-left font-medium text-dark-600">Autor</th>
                          <th className="px-3 py-2 text-right font-medium text-dark-600">Curtidas</th>
                          <th className="px-3 py-2 text-right font-medium text-dark-600">Coment.</th>
                          <th className="px-3 py-2 text-right font-medium text-dark-600">Views</th>
                          <th className="px-3 py-2 text-right font-medium text-dark-600">Engaj.</th>
                          <th className="px-3 py-2 text-left font-medium text-dark-600">Data</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-dark-100">
                        {(analise.itens || []).map((item) => (
                          <tr key={item.id} className="hover:bg-dark-50">
                            <td className="px-3 py-2 text-dark-400">{item.id}</td>
                            <td className="px-3 py-2 text-dark-900">
                              <span className="block max-w-[22rem] truncate" title={item.titulo}>
                                {item.url ? (
                                  <a href={item.url} target="_blank" rel="noreferrer" className="hover:text-primary-600 hover:underline">
                                    {item.titulo}
                                  </a>
                                ) : (
                                  item.titulo
                                )}
                              </span>
                            </td>
                            <td className="px-3 py-2 text-dark-600">{item.autor || '—'}</td>
                            <td className="px-3 py-2 text-right text-dark-900">{formatarNumero(item.curtidas)}</td>
                            <td className="px-3 py-2 text-right text-dark-900">{formatarNumero(item.comentarios)}</td>
                            <td className="px-3 py-2 text-right text-dark-900">{formatarNumero(item.visualizacoes)}</td>
                            <td className="px-3 py-2 text-right font-medium text-dark-900">{formatarNumero(item.engajamento)}</td>
                            <td className="px-3 py-2 text-dark-500">{item.data || '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
