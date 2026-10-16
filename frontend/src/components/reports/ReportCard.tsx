import { useState } from 'react';
import { cn, formatDate } from '../../lib/utils';
import { Button } from '../ui';
import { Spinner } from '../ui/Spinner';
import type { Report, ReportType } from '../../types';

interface ReportCardProps {
  report: Report;
  onView: (report: Report) => void;
  onDelete: (id: number) => void;
  types: ReportType[];
}

type StatusVariant = 'default' | 'success' | 'warning' | 'error' | 'info';

export function ReportCard({ report, onView, onDelete, types }: ReportCardProps) {
  const [hovered, setHovered] = useState(false);
  const typeInfo = types.find(t => t.id === report.report_type);

  const statusConfig: Record<string, { label: string; variant: StatusVariant }> = {
    pending: { label: 'Pendente', variant: 'warning' },
    generating: { label: 'Gerando...', variant: 'info' },
    generated: { label: 'Pronto', variant: 'success' },
    failed: { label: 'Erro', variant: 'error' },
  };

  const status = statusConfig[report.status] || { label: report.status, variant: 'default' };

  return (
    <div
      className={cn(
        'card overflow-hidden transition-all duration-200',
        'hover:shadow-lg hover:-translate-y-0.5'
      )}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div className="card-body">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="font-semibold text-dark-900 truncate">{report.title}</h3>
              <span className={cn('badge', status.variant !== 'default' && `badge-${status.variant}`)}>
                {status.label}
              </span>
            </div>
            <p className="text-sm text-dark-500 truncate mb-2">
              {typeInfo?.name || report.report_type}
            </p>
            <div className="flex items-center gap-4 text-xs text-dark-400">
              <span>Criado: {formatDate(report.created_at)}</span>
              {report.generated_at && (
                <span>Concluído: {formatDate(report.generated_at)}</span>
              )}
            </div>
          </div>
        </div>

        {report.filters && Object.keys(report.filters).length > 0 && (
          <details className="mt-4">
            <summary className="text-xs text-dark-500 cursor-pointer hover:text-dark-700">
              Filtros aplicados
            </summary>
            <pre className="mt-2 text-xs text-dark-600 bg-dark-50 p-3 rounded overflow-x-auto max-h-32 overflow-y-auto">
              {JSON.stringify(report.filters, null, 2)}
            </pre>
          </details>
        )}

        {report.status === 'generating' && (
          <div className="mt-4 flex items-center gap-2">
            <Spinner size="sm" />
            <span className="text-sm text-dark-600">Gerando relatório...</span>
          </div>
        )}
      </div>

      <div className={cn('card-footer flex items-center justify-end gap-2', hovered ? 'opacity-100' : 'opacity-0')}>
        <Button variant="outline" size="sm" onClick={() => onView(report)}>
          Visualizar
        </Button>
        <Button variant="ghost" size="sm" onClick={() => onDelete(report.id)} className="text-red-600 hover:text-red-700">
          Excluir
        </Button>
      </div>
    </div>
  );
}