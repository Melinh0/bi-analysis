import { Bot, Check, WifiOff, ChevronDown, Sparkles } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { cn } from '../../lib/utils';
import type { Model } from '../../types';

interface ModelSelectorProps {
  currentModel: string;
  models: Model[];
  onSelect: (model: string) => void;
  disabled?: boolean;
}

export function ModelSelector({ currentModel, models, onSelect, disabled }: ModelSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  const currentModelInfo = models.find((m) => m.name === currentModel);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        if (buttonRef.current && !buttonRef.current.contains(event.target as Node)) {
          setIsOpen(false);
        }
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        ref={buttonRef}
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={cn(
          'flex items-center gap-2 rounded-lg border border-dark-300 bg-white px-3 py-2 text-sm font-medium',
          'hover:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500',
          'disabled:opacity-50 disabled:cursor-not-allowed transition-colors'
        )}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label="Selecionar modelo"
      >
        <Bot className="h-4 w-4 text-dark-500" />
        <span className="truncate max-w-[150px]">{currentModelInfo?.name || currentModel}</span>
        <span className={cn('flex items-center gap-1.5 h-5 w-5 rounded-full', currentModelInfo?.available ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700')}>
          {currentModelInfo?.available ? (
            <>
              <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
              <span className="text-xs hidden sm:inline">Online</span>
            </>
          ) : (
            <>
              <WifiOff className="h-3 w-3" />
              <span className="text-xs hidden sm:inline">Offline</span>
            </>
          )}
        </span>
        <ChevronDown className={cn('h-4 w-4 text-dark-400 transition-transform', isOpen && 'rotate-180')} />
      </button>

      {isOpen && (
        <div className="absolute right-0 z-50 mt-1 w-64 origin-top-right rounded-lg border border-dark-300 bg-white shadow-lg focus:outline-none animate-in fade-in-0 zoom-in-95 duration-100">
          <div className="p-2">
            <div className="flex items-center gap-2 px-2 py-1.5 text-xs font-semibold text-dark-500 uppercase tracking-wider">
              <Sparkles className="h-4 w-4" />
              Modelos Disponíveis
            </div>
            <div className="py-1" role="listbox" aria-label="Modelos">
              {models.map((model) => (
                <button
                  key={model.name}
                  type="button"
                  role="option"
                  aria-selected={model.name === currentModel}
                  onClick={() => {
                    onSelect(model.name);
                    setIsOpen(false);
                  }}
                  disabled={disabled || !model.available}
                  className={cn(
                    'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm',
                    'hover:bg-dark-50 focus:outline-none focus:bg-dark-50',
                    model.name === currentModel && 'bg-primary-50 text-primary-700',
                    !model.available && 'opacity-50 cursor-not-allowed'
                  )}
                >
                  <Bot className={cn('h-4 w-4 flex-shrink-0', model.available ? 'text-primary-600' : 'text-dark-400')} />
                  <div className="flex-1 min-w-0 text-left">
                    <p className="truncate font-medium">{model.name}</p>
                    <p className={cn('truncate text-xs', model.available ? 'text-green-600' : 'text-red-600')}>
                      {model.available ? 'Disponível' : 'Indisponível'}
                    </p>
                  </div>
                  {model.name === currentModel && <Check className="h-4 w-4 text-primary-600 flex-shrink-0" />}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}