import { cn } from '../../lib/utils';
import { Bot, User, Copy, Check, FileText } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useState } from 'react';
import type { ChatMessage, Source } from '../../types';

interface MessageProps {
  message: ChatMessage;
  isStreaming?: boolean;
  onCopy?: (content: string) => void;
}

export function Message({ message, isStreaming = false, onCopy }: MessageProps) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    onCopy?.(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={cn('flex gap-3', isUser && 'flex-row-reverse')}>
      <div
        className={cn(
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium',
          isUser ? 'bg-primary-600 text-white' : 'bg-dark-100 text-dark-600'
        )}
        aria-hidden="true"
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      <div className={cn('flex-1 min-w-0', isUser ? 'text-right' : '')}>
        <div className={cn('inline-block max-w-[85%] rounded-2xl px-4 py-2.5', isUser ? 'bg-primary-600 text-white rounded-tr-sm' : 'bg-dark-100 text-dark-900 rounded-tl-sm')}>
          <div className="prose prose-sm dark:prose-invert max-w-none text-inherit">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>

          {message.sources && message.sources.length > 0 && (
            <div className={cn('mt-3 space-y-1.5', isUser ? 'text-right' : '')}>
              {message.sources.map((source, index) => (
                <SourceBadge key={index} source={source} index={index + 1} />
              ))}
            </div>
          )}

          <div className={cn('mt-2 flex items-center gap-1.5 text-xs opacity-60', isUser ? 'justify-end' : 'justify-start')}>
            {!isUser && isStreaming && (
              <span className="flex items-center gap-1 animate-pulse text-primary-600">
                <span className="h-1.5 w-1.5 rounded-full bg-current animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="h-1.5 w-1.5 rounded-full bg-current animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="h-1.5 w-1.5 rounded-full bg-current animate-bounce" style={{ animationDelay: '300ms' }} />
              </span>
            )}
            <button
              onClick={handleCopy}
              className="flex items-center gap-1 p-1 rounded hover:bg-black/10 hover:text-white transition-colors"
              aria-label={copied ? 'Copiado!' : 'Copiar mensagem'}
              title={copied ? 'Copiado!' : 'Copiar mensagem'}
            >
              {copied ? <Check className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />}
            </button>
          </div>
        </div>

        <div className={cn('mt-1 text-xs text-dark-400', isUser ? 'text-right pr-2' : 'pl-2')}>
          {message.created_at && new Date(message.created_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
}

function SourceBadge({ source, index }: { source: Source; index: number }) {
  return (
    <details className="group">
      <summary className="flex items-center gap-1.5 cursor-pointer p-2 rounded-lg bg-white/50 hover:bg-white transition-colors">
        <FileText className="h-3.5 w-3.5 text-dark-400" />
        <span className="text-xs font-medium text-dark-600 truncate flex-1">
          Fonte {index}
        </span>
        {source.distance !== undefined && (
          <span className="text-xs px-1.5 py-0.5 rounded bg-dark-100 text-dark-500 font-mono">
            {source.distance.toFixed(3)}
          </span>
        )}
        <span className="text-dark-400">▼</span>
      </summary>
      <div className="mt-2 ml-10 border-l-2 border-dark-200 pl-3">
        <pre className="text-xs text-dark-600 bg-dark-50 p-3 rounded-r-lg overflow-x-auto whitespace-pre-wrap max-h-40 overflow-y-auto">
          {source.content}
        </pre>
        {source.metadata && Object.keys(source.metadata).length > 0 && (
          <details className="mt-2">
            <summary className="text-xs text-dark-500 cursor-pointer hover:text-dark-700">Metadados</summary>
            <pre className="mt-1 text-xs text-dark-500 bg-dark-50 p-2 rounded overflow-x-auto">
              {JSON.stringify(source.metadata, null, 2)}
            </pre>
          </details>
        )}
      </div>
    </details>
  );
}