import { useRef } from 'react';
import { Button } from '../ui';
import type { Report } from '../../types';

interface ReportViewerProps {
  report: Report | null;
  onClose: () => void;
  onDownload: (report: Report) => void;
}

export function ReportViewer({ report, onClose, onDownload }: ReportViewerProps) {
  const contentRef = useRef<HTMLDivElement>(null);

  const handleDownload = () => {
    if (report) onDownload(report);
  };

  if (!report) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-4xl max-h-[90vh] rounded-2xl bg-white shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between border-b border-dark-200 p-4">
          <div>
            <h2 className="text-lg font-semibold text-dark-900 truncate">{report.title}</h2>
            <p className="text-sm text-dark-500">
              {report.report_type} • {report.status === 'generated' ? 'Concluído' : 'Processando...'}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleDownload} disabled={report.status !== 'generated'}>
              Baixar
            </Button>
            <Button variant="ghost" size="sm" onClick={onClose}>
              Fechar
            </Button>
          </div>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {report.status === 'generating' || report.status === 'pending' ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-3 border-primary-600 border-t-transparent mb-4" />
              <p className="text-dark-600">Gerando relatório, por favor aguarde...</p>
              <p className="text-sm text-dark-400 mt-1">Isso pode levar alguns minutos</p>
            </div>
          ) : report.status === 'failed' ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <svg className="h-12 w-12 text-red-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <p className="text-red-600 font-medium">Falha ao gerar relatório</p>
              <p className="text-sm text-dark-500 mt-1">Tente novamente ou entre em contato com o suporte</p>
            </div>
          ) : (
            <div
              ref={contentRef}
              className="prose prose-dark max-w-none dark:prose-invert"
              dangerouslySetInnerHTML={{ __html: report.generated_content || '' }}
            />
          )}
        </div>

        {report.generated_content && report.status === 'generated' && (
          <div className="border-t border-dark-200 p-4 bg-dark-50">
            <div className="flex items-center justify-between">
              <p className="text-sm text-dark-500">
                Relatório gerado em {new Date(report.generated_at!).toLocaleString('pt-BR')}
              </p>
              <Button variant="primary" size="sm" onClick={handleDownload}>
                Baixar Relatório
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}