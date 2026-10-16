import { useState, useCallback } from 'react';
import { Plus, RefreshCw, Filter, FileText, ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from '../../lib/utils';
import { api } from '../../lib/api';
import { useReports, useReportTypes, useTemplates } from '../../hooks/useApi';
import { Button } from '../ui';
import { Modal } from '../ui/Modal';
import { Spinner } from '../ui/Spinner';
import { ReportCard } from './ReportCard';
import { ReportForm } from './ReportForm';
import { ReportViewer } from './ReportViewer';
import type { Report, ReportRequest } from '../../types';

export function ReportsPanel() {
  const [showForm, setShowForm] = useState(false);
  const [viewingReport, setViewingReport] = useState<Report | null>(null);
  const [selectedType, setSelectedType] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(10);

  const { reports, loading, refetch } = useReports();
  const { types, loading: typesLoading } = useReportTypes();
  const { templates, loading: templatesLoading } = useTemplates();

  const filteredReports = selectedType === 'all'
    ? reports
    : reports.filter(r => r.report_type === selectedType);

  const paginatedReports = filteredReports.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  const totalPages = Math.ceil(filteredReports.length / pageSize);

  const handleCreateReport = useCallback(async (data: ReportRequest) => {
    try {
      await api.createReport(data);
      refetch();
      setShowForm(false);
    } catch (error) {
      console.error('Failed to create report:', error);
      alert('Falha ao gerar relatório. Verifique os dados e tente novamente.');
    }
  }, [refetch]);

  const handleDeleteReport = useCallback(async (id: number) => {
    if (window.confirm('Tem certeza que deseja excluir este relatório?')) {
      try {
        await api.deleteReport(id);
        refetch();
      } catch (error) {
        console.error('Failed to delete report:', error);
        alert('Falha ao excluir relatório');
      }
    }
  }, [refetch]);

  const handleViewReport = useCallback((report: Report) => {
    setViewingReport(report);
  }, []);

  const handleDownloadReport = useCallback(async (report: Report) => {
    if (report.generated_content) {
      const blob = new Blob([report.generated_content], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${report.title.replace(/\s+/g, '_')}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  }, []);

  const handleRefresh = useCallback(() => {
    refetch();
  }, [refetch]);

  return (
    <div className="flex h-full flex-col bg-white">
      <div className="flex h-16 items-center justify-between border-b border-dark-200 px-4 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-100">
            <FileText className="h-5 w-5 text-primary-600" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-dark-900">Relatórios</h1>
            <p className="text-xs text-dark-500">{reports.length} relatório(s) total</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="hidden sm:flex items-center gap-2 border border-dark-300 rounded-lg bg-white px-3 py-1.5">
            <Filter className="h-4 w-4 text-dark-400" />
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="text-sm bg-transparent focus:outline-none"
              aria-label="Filtrar por tipo"
            >
              <option value="all">Todos os tipos</option>
              {types.map(type => (
                <option key={type.id} value={type.id}>{type.name}</option>
              ))}
            </select>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={loading}
            className="hidden sm:flex"
          >
            <RefreshCw className={cn('h-4 w-4', loading && 'animate-spin')} />
            Atualizar
          </Button>

          <Button onClick={() => setShowForm(true)} className="flex items-center gap-2">
            <Plus className="h-4 w-4" />
            <span className="hidden sm:inline">Novo Relatório</span>
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin p-4 sm:p-6">
        {loading && !reports.length ? (
          <div className="flex h-full items-center justify-center">
            <Spinner size="lg" />
          </div>
        ) : filteredReports.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center text-dark-500">
            <FileText className="h-16 w-16 mb-4 text-dark-300" />
            <h3 className="text-lg font-medium text-dark-900 mb-1">Nenhum relatório encontrado</h3>
            <p className="text-sm mb-6">{selectedType !== 'all' ? 'Tente alterar o filtro' : 'Clique em "Novo Relatório" para criar o primeiro'}</p>
            <Button onClick={() => setShowForm(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Criar Primeiro Relatório
            </Button>
          </div>
        ) : (
          <>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {paginatedReports.map(report => (
                <ReportCard
                  key={report.id}
                  report={report}
                  onView={handleViewReport}
                  onDelete={handleDeleteReport}
                  types={types}
                />
              ))}
            </div>

            {totalPages > 1 && (
              <div className="mt-6 flex items-center justify-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                  <Button
                    key={page}
                    variant={currentPage === page ? 'primary' : 'ghost'}
                    size="sm"
                    onClick={() => setCurrentPage(page)}
                    className="h-8 w-8 p-0"
                  >
                    {page}
                  </Button>
                ))}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            )}
          </>
        )}
      </div>

      <Modal
        isOpen={showForm}
        onClose={() => setShowForm(false)}
        title="Novo Relatório"
        description="Configure e gere um novo relatório de BI"
        size="lg"
      >
        <ReportForm
          types={types}
          templates={templates}
          onSubmit={handleCreateReport}
          onCancel={() => setShowForm(false)}
          loading={loading || typesLoading || templatesLoading}
        />
      </Modal>

      <Modal
        isOpen={!!viewingReport}
        onClose={() => setViewingReport(null)}
        title=""
        size="full"
      >
        <ReportViewer
          report={viewingReport}
          onClose={() => setViewingReport(null)}
          onDownload={handleDownloadReport}
        />
      </Modal>
    </div>
  );
}