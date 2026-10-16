import { useCallback, useEffect, useRef, useState } from 'react';
import { Check, ChevronDown } from 'lucide-react';
import { cn } from '../../lib/utils';

interface SelectOption {
  value: string;
  label: string;
  description?: string;
  icon?: React.ReactNode;
  disabled?: boolean;
}

interface SelectProps {
  value: string;
  options: SelectOption[];
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  triggerClassName?: string;
}

export function Select({
  value,
  options,
  onChange,
  placeholder = 'Selecione',
  disabled = false,
  className,
  triggerClassName,
}: SelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const rootRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const safeOptions = Array.isArray(options) ? options : [];
  const selectedOption = safeOptions.find((o) => o.value === value);

  const close = useCallback(() => {
    setIsOpen(false);
    setActiveIndex(-1);
  }, []);

  const choose = useCallback(
    (option: SelectOption) => {
      if (option.disabled) return;
      onChange(option.value);
      close();
    },
    [onChange, close]
  );

  useEffect(() => {
    if (!isOpen) return;
    const onPointerDown = (e: PointerEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
        close();
      }
    };
    document.addEventListener('pointerdown', onPointerDown);
    return () => document.removeEventListener('pointerdown', onPointerDown);
  }, [isOpen, close]);

  useEffect(() => {
    if (!isOpen || activeIndex < 0 || !listRef.current) return;
    const el = listRef.current.querySelectorAll<HTMLElement>('[role="option"]')[activeIndex];
    el?.scrollIntoView({ block: 'nearest' });
  }, [isOpen, activeIndex]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (disabled) return;
    if (e.key === 'Escape') {
      if (isOpen) {
        e.preventDefault();
        close();
      }
      return;
    }
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      if (!isOpen) {
        setIsOpen(true);
        setActiveIndex(0);
        return;
      }
      const dir = e.key === 'ArrowDown' ? 1 : -1;
      setActiveIndex((prev) => {
        const next = prev + dir;
        if (next < 0) return safeOptions.length - 1;
        if (next >= safeOptions.length) return 0;
        return next;
      });
      return;
    }
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      if (!isOpen) {
        setIsOpen(true);
        setActiveIndex(0);
        return;
      }
      if (activeIndex >= 0 && safeOptions[activeIndex]) {
        choose(safeOptions[activeIndex]);
      }
      return;
    }
    if (e.key === 'Home') {
      e.preventDefault();
      setActiveIndex(0);
    } else if (e.key === 'End') {
      e.preventDefault();
      setActiveIndex(safeOptions.length - 1);
    }
  };

  return (
    <div ref={rootRef} className={cn('relative inline-block w-full', className)}>
      <button
        type="button"
        onClick={() => !disabled && (isOpen ? close() : setIsOpen(true))}
        disabled={disabled}
        onKeyDown={handleKeyDown}
        className={cn(
          'w-full flex items-center justify-between gap-2 rounded-lg border border-dark-300 bg-white px-3 py-2 text-sm text-dark-900 placeholder:text-dark-400',
          'hover:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500',
          'disabled:opacity-50 disabled:cursor-not-allowed transition-colors',
          triggerClassName
        )}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <span className={cn('truncate flex-1 text-left', !selectedOption && 'text-dark-400')}>
          {selectedOption?.label || placeholder}
        </span>
        <div className={cn('flex items-center gap-1 text-dark-400 transition-transform', isOpen && 'rotate-180')}>
          <ChevronDown className="h-4 w-4" />
        </div>
      </button>

      {isOpen && (
        <>
          <div
            ref={listRef}
            className="absolute z-50 mt-1 max-h-60 w-full overflow-auto rounded-lg border border-dark-300 bg-white shadow-lg focus:outline-none"
          >
            <div className="py-1" role="listbox" aria-label={placeholder}>
              {safeOptions.map((option, index) => (
                <button
                  key={option.value}
                  type="button"
                  role="option"
                  aria-selected={option.value === value}
                  disabled={option.disabled}
                  tabIndex={-1}
                  onMouseEnter={() => setActiveIndex(index)}
                  onClick={() => choose(option)}
                  className={cn(
                    'w-full flex items-center gap-3 px-3 py-2 text-sm',
                    'hover:bg-dark-50 focus:outline-none',
                    option.value === value && 'bg-primary-50 text-primary-700',
                    index === activeIndex && 'bg-dark-50',
                    option.disabled && 'opacity-50 cursor-not-allowed'
                  )}
                >
                  {option.icon && <span className="flex-shrink-0">{option.icon}</span>}
                  <div className="flex-1 min-w-0 text-left">
                    <p className="truncate font-medium">{option.label}</p>
                    {option.description && (
                      <p className="truncate text-xs text-dark-500">{option.description}</p>
                    )}
                  </div>
                  {option.value === value && (
                    <Check className="h-4 w-4 text-primary-600 flex-shrink-0" />
                  )}
                </button>
              ))}
              {safeOptions.length === 0 && (
                <p className="px-3 py-2 text-sm text-dark-400">Nenhuma opção disponível</p>
              )}
            </div>
          </div>
          <div className="fixed inset-0 z-40" onClick={close} aria-hidden="true" />
        </>
      )}
    </div>
  );
}
