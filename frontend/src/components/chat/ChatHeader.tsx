import { ModelSelector } from './ModelSelector';
import { RAGToggle } from './RAGToggle';

interface ChatHeaderProps {
  sessionTitle: string;
  currentModel: string;
  models: Array<{ name: string; available: boolean }>;
  onModelChange: (model: string) => void;
  ragEnabled: boolean;
  onRAGToggle: (enabled: boolean) => void;
  disabled?: boolean;
}

export function ChatHeader({
  sessionTitle,
  currentModel,
  models,
  onModelChange,
  ragEnabled,
  onRAGToggle,
  disabled,
}: ChatHeaderProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 border-b border-dark-200 bg-white">
      <div className="min-w-0">
        <h1 className="truncate text-lg font-semibold text-dark-900">{sessionTitle || 'Nova Conversa'}</h1>
        <p className="text-xs text-dark-500">Powered by Ollama + RAG</p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <RAGToggle enabled={ragEnabled} onChange={onRAGToggle} disabled={disabled} />
        <ModelSelector
          currentModel={currentModel}
          models={models}
          onSelect={onModelChange}
          disabled={disabled}
        />
      </div>
    </div>
  );
}