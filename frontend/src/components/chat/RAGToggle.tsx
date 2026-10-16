import { Brain, Sparkles } from 'lucide-react';
import { cn } from '../../lib/utils';

interface RAGToggleProps {
  enabled: boolean;
  onChange: (enabled: boolean) => void;
  disabled?: boolean;
}

export function RAGToggle({ enabled, onChange, disabled }: RAGToggleProps) {
  return (
    <label className="relative inline-flex items-center cursor-pointer" aria-label={enabled ? 'Desativar RAG' : 'Ativar RAG'}>
      <input
        type="checkbox"
        checked={enabled}
        onChange={(e) => onChange(e.target.checked)}
        disabled={disabled}
        className="sr-only peer"
        aria-label={enabled ? 'RAG ativado' : 'RAG desativado'}
      />
      <div className={cn(
        'w-11 h-6 rounded-full transition-colors',
        'peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-500/20',
        enabled ? 'bg-primary-600' : 'bg-dark-300',
        disabled && 'opacity-50 cursor-not-allowed'
      )}>
        <div className={cn(
          'h-5 w-5 rounded-full bg-white shadow-lg transform transition-transform duration-200',
          'flex items-center justify-center',
          enabled ? 'translate-x-5' : 'translate-x-0'
        )}>
          {enabled ? <Brain className="h-3 w-3 text-primary-600" /> : <Sparkles className="h-3 w-3 text-dark-400" />}
        </div>
      </div>
      <span className={cn('ml-2 text-sm font-medium', enabled ? 'text-primary-700' : 'text-dark-600', disabled && 'opacity-50')}>
        {enabled ? 'RAG Ativo' : 'RAG Inativo'}
      </span>
      <div className="absolute left-1/2 top-full mt-2 -translate-x-1/2 px-2 py-1 rounded bg-dark-900 text-white text-xs whitespace-nowrap opacity-0 invisible peer-hover:opacity-100 peer-hover:visible transition-all">
        {enabled
          ? 'Busca no banco de conhecimento antes de responder'
          : 'Resposta direta do modelo sem busca externa'}
      </div>
    </label>
  );
}