import { useRef, useEffect, useImperativeHandle, forwardRef } from 'react';
import { Bot } from 'lucide-react';
import { Message } from './Message';
import type { ChatMessage } from '../../types';

interface MessageListProps {
  messages: ChatMessage[];
  streamingMessage?: string;
  isStreaming?: boolean;
  emptyState?: React.ReactNode;
}

interface MessageListRef {
  scrollToBottom: (smooth?: boolean) => void;
  scrollToTop: () => void;
}

export const MessageList = forwardRef<MessageListRef, MessageListProps>(
  ({ messages, streamingMessage, isStreaming, emptyState }, ref) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const endRef = useRef<HTMLDivElement>(null);

    useImperativeHandle(ref, () => ({
      scrollToBottom: (smooth = true) => {
        endRef.current?.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto' });
      },
      scrollToTop: () => {
        containerRef.current?.scrollTo({ top: 0, behavior: 'smooth' });
      },
    }));

    useEffect(() => {
      endRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, streamingMessage, isStreaming]);

    if (messages.length === 0 && !streamingMessage && !isStreaming) {
      return (
        <div className="flex h-full items-center justify-center p-6">
          <div className="text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary-100">
              <Bot className="h-8 w-8 text-primary-600" />
            </div>
            <h3 className="text-lg font-medium text-dark-900">Nenhuma mensagem ainda</h3>
            <p className="mt-1 text-sm text-dark-500">
              {emptyState || 'Inicie uma conversa digitando uma mensagem abaixo'}
            </p>
          </div>
        </div>
      );
    }

    return (
      <div
        ref={containerRef}
        className="flex h-full flex-col overflow-y-auto scrollbar-thin p-4 space-y-4"
        role="log"
        aria-live="polite"
        aria-label="Mensagens do chat"
      >
        {messages.map((message) => (
          <Message key={`${message.session_id}-${message.message_id}`} message={message} />
        ))}

        {(streamingMessage || isStreaming) && (
          <Message
            message={{
              role: 'assistant',
              content: streamingMessage || '',
              session_id: '',
              message_id: -1,
            }}
            isStreaming={true}
          />
        )}

        <div ref={endRef} />
      </div>
    );
  }
);

MessageList.displayName = 'MessageList';