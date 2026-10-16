import { useState } from 'react';
import { Button, Input, Textarea, Select } from '../ui';
import type { ReportType, ReportRequest } from '../../types';

interface ReportFormProps {
  types: ReportType[];
  templates: string[];
  onSubmit: (data: ReportRequest) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
  initialData?: Partial<ReportRequest>;
}

export function ReportForm({ types, templates, onSubmit, onCancel, loading, initialData }: ReportFormProps) {
  const [formData, setFormData] = useState<ReportRequest>({
    title: '',
    report_type: '',
    filters: {},
    template: '',
    ...initialData,
  });
  const [errors, setErrors] = useState<Partial<Record<keyof ReportRequest, string>>>({});
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [filterText, setFilterText] = useState(JSON.stringify(formData.filters, null, 2));

  const typeOptions = types.map(t => ({
    value: t.id,
    label: t.name,
    description: t.description,
  }));

  const templateOptions = [
    { value: '', label: 'Nenhum (padrão)' },
    ...templates.map(t => ({ value: t, label: t })),
  ];

  const validateForm = () => {
    const newErrors: Partial<Record<keyof ReportRequest, string>> = {};
    if (!formData.title.trim()) newErrors.title = 'Título é obrigatório';
    if (!formData.report_type) newErrors.report_type = 'Tipo de relatório é obrigatório';
    try {
      JSON.parse(filterText);
    } catch {
      newErrors.filters = 'JSON inválido nos filtros';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    try {
      const filters = JSON.parse(filterText);
      await onSubmit({ ...formData, filters });
    } catch (error) {
      console.error('Failed to submit report:', error);
    }
  };

  const handleFilterChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setFilterText(e.target.value);
    setErrors(prev => ({ ...prev, filters: undefined }));
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label className="text-sm font-medium text-dark-700">Configurações Básicas</label>
      </div>

      <Input
        label="Título do Relatório"
        placeholder="Ex: Relatório Mensal de Vendas - Janeiro 2024"
        value={formData.title}
        onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
        error={errors.title}
        required
      />

      <Select
        value={formData.report_type}
        options={typeOptions}
        onChange={(value) => setFormData(prev => ({ ...prev, report_type: value }))}
        placeholder="Selecione o tipo de relatório"
        disabled={loading}
      />

      <div className="flex items-center gap-2">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={showAdvanced}
            onChange={(e) => setShowAdvanced(e.target.checked)}
            className="rounded border-dark-300 text-primary-600 focus:ring-primary-500"
          />
          <span className="text-sm text-dark-700">Mostrar opções avançadas</span>
        </label>
      </div>

      {showAdvanced && (
        <div className="space-y-4 border-t border-dark-200 pt-4">
          <div>
            <label className="text-sm font-medium text-dark-700">Template Personalizado</label>
            <Select
              value={formData.template || ''}
              options={templateOptions}
              onChange={(value) => setFormData(prev => ({ ...prev, template: value || undefined }))}
              placeholder="Selecione um template (opcional)"
              disabled={loading}
            />
          </div>

          <Textarea
            label="Filtros (JSON)"
            placeholder='{"source_type": "instagram", "content_type": "comment", "date_from": "2024-01-01", "date_to": "2024-12-31"}'
            value={filterText}
            onChange={handleFilterChange}
            error={errors.filters}
            helperText="Deixe vazio ou {} para usar todos os dados. Campos disponíveis: source_type, content_type, date_from, date_to, sentiment, etc."
            rows={6}
            className="font-mono text-sm"
            disabled={loading}
          />
        </div>
      )}

      <div className="flex justify-end gap-3 pt-4 border-t border-dark-200">
        <Button type="button" variant="secondary" onClick={onCancel} disabled={loading}>
          Cancelar
        </Button>
        <Button type="submit" variant="primary" loading={loading}>
          Gerar Relatório
        </Button>
      </div>
    </form>
  );
}