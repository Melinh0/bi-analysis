import { useRef, useState, useCallback } from 'react';
import { Send, Paperclip, Smile } from 'lucide-react';
import { cn } from '../../lib/utils';
import { Button } from '../ui';

interface MessageInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  streaming?: boolean;
}

export function MessageInput({ onSend, disabled, placeholder = 'Digite sua mensagem...', streaming }: MessageInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [value, setValue] = useState('');
  const [height, setHeight] = useState(44);

  const adjustHeight = useCallback(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const newHeight = Math.min(textareaRef.current.scrollHeight, 200);
      setHeight(newHeight);
      textareaRef.current.style.height = `${newHeight}px`;
    }
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value);
    setTimeout(adjustHeight, 0);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !disabled && !streaming) {
        onSend(value.trim());
        setValue('');
        setHeight(44);
        textareaRef.current?.focus();
      }
    }
  };

  const handleSubmit = () => {
    if (value.trim() && !disabled && !streaming) {
      onSend(value.trim());
      setValue('');
      setHeight(44);
      textareaRef.current?.focus();
    }
  };

  return (
    <div className="border-t border-dark-200 bg-white p-4">
      <div className="relative">
        <div className="flex items-end gap-2">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={value}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              disabled={disabled || streaming}
              placeholder={placeholder}
              className={cn(
                'w-full min-h-[44px] max-h-[200px] pr-12 rounded-xl border border-dark-300 bg-white px-4 py-3 text-sm',
                'placeholder:text-dark-400 resize-none',
                'focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                'transition-colors'
              )}
              style={{ height: `${height}px` }}
              rows={1}
              aria-label="Mensagem"
            />
            <div className="absolute right-3 bottom-3 flex items-center gap-1">
              <button
                type="button"
                className="p-1.5 rounded-lg text-dark-400 hover:text-dark-600 hover:bg-dark-100 transition-colors"
                aria-label="Anexar arquivo"
                disabled={disabled || streaming}
              >
                <Paperclip className="h-5 w-5" />
              </button>
              <button
                type="button"
                className="p-1.5 rounded-lg text-dark-400 hover:text-dark-600 hover:bg-dark-100 transition-colors"
                aria-label="Inserir emoji"
                disabled={disabled || streaming}
              >
                <Smile className="h-5 w-5" />
              </button>
            </div>
          </div>
          <Button
            onClick={handleSubmit}
            disabled={disabled || streaming || !value.trim()}
            className="h-10 w-10 rounded-xl p-0"
            aria-label={streaming ? 'Enviando...' : 'Enviar mensagem'}
          >
            {streaming ? (
              <div className="flex h-5 w-5 items-center justify-center">
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-current border-t-transparent" />
              </div>
            ) : (
              <Send className="h-5 w-5" />
            )}
          </Button>
        </div>
        <p className="mt-2 text-xs text-center text-dark-400">
          Pressione <kbd className="px-1.5 py-0.5 rounded bg-dark-100 font-mono text-xs">Enter</kbd> para enviar,
          <kbd className="px-1.5 py-0.5 rounded bg-dark-100 font-mono text-xs">Shift+Enter</kbd> para nova linha
        </p>
      </div>
    </div>
  );
}