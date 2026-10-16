import { useState, useCallback, useRef, useEffect } from 'react';
import { Plus, Loader2, MessagesSquare } from 'lucide-react';
import { cn } from '../../lib/utils';
import { api } from '../../lib/api';
import { useSessions, useModels } from '../../hooks/useApi';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { SessionList } from './SessionList';
import { ChatHeader } from './ChatHeader';
import { Button } from '../ui';
import type { ChatMessage } from '../../types';

interface MessageListRef {
  scrollToBottom: (smooth?: boolean) => void;
  scrollToTop: () => void;
}

export function ChatPanel() {
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [streamingContent, setStreamingContent] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [ragEnabled, setRagEnabled] = useState(true);
  const [currentModel, setCurrentModel] = useState('');
  const [sessionTitle, setSessionTitle] = useState('Nova Conversa');
  const [showSessions, setShowSessions] = useState(false);

  const messageListRef = useRef<MessageListRef>(null);

  const { sessions, loading: sessionsLoading, refetch: refetchSessions } = useSessions();
  const { models, loading: modelsLoading } = useModels();

  useEffect(() => {
    if (models?.current_model && !currentModel) {
      setCurrentModel(models.current_model);
    }
  }, [models, currentModel]);

  const loadSessionHistory = useCallback(async (sessionId: string) => {
    try {
      const history = await api.getSessionHistory(sessionId);
      setMessages(history.messages);
      const firstUserMsg = history.messages.find(m => m.role === 'user');
      setSessionTitle(firstUserMsg?.content.slice(0, 50) || 'Conversa');
    } catch (error) {
      console.error('Failed to load session history:', error);
    }
  }, []);

  const handleSelectSession = useCallback((sessionId: string) => {
    setActiveSessionId(sessionId);
    setStreamingContent('');
    setIsStreaming(false);
    loadSessionHistory(sessionId);
    setShowSessions(false);
  }, [loadSessionHistory]);

  const handleNewSession = useCallback(() => {
    setActiveSessionId(null);
    setMessages([]);
    setStreamingContent('');
    setIsStreaming(false);
    setSessionTitle('Nova Conversa');
    setShowSessions(false);
  }, []);

  const handleDeleteSession = useCallback(async (sessionId: string) => {
    if (window.confirm('Tem certeza que deseja excluir esta conversa?')) {
      try {
        await api.deleteSession(sessionId);
        refetchSessions();
        if (activeSessionId === sessionId) {
          handleNewSession();
        }
      } catch (error) {
        console.error('Failed to delete session:', error);
        alert('Falha ao excluir conversa');
      }
    }
  }, [activeSessionId, refetchSessions, handleNewSession]);

  const handleRenameSession = useCallback(async (sessionId: string, newTitle: string) => {
    
    console.log('Rename session:', sessionId, newTitle);
  }, []);

  const handleSendMessage = useCallback(async (message: string) => {
    if (isStreaming) return;

    setIsStreaming(true);
    setStreamingContent('');

    const userMessage: ChatMessage = {
      role: 'user',
      content: message,
      session_id: activeSessionId || '',
      message_id: Date.now(),
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      let accumulated = '';
      for await (const chunk of api.streamMessage(message, {
        session_id: activeSessionId || undefined,
        use_rag: ragEnabled,
        model: currentModel,
        temperature: 0.7,
      })) {
        if (chunk.content) {
          accumulated += chunk.content;
          setStreamingContent((prev) => prev + chunk.content);
        }
        if (chunk.done) {
          if (chunk.session_id && !activeSessionId) {
            setActiveSessionId(chunk.session_id);
            refetchSessions();
          }
          break;
        }
      }

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: accumulated,
        session_id: activeSessionId || '',
        message_id: Date.now() + 1,
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setStreamingContent('');
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente.',
        session_id: activeSessionId || '',
        message_id: Date.now() + 1,
      };
      setMessages((prev) => [...prev, errorMessage]);
      setStreamingContent('');
    } finally {
      setIsStreaming(false);
    }
  }, [activeSessionId, ragEnabled, currentModel, isStreaming, refetchSessions]);

  const handleModelChange = useCallback((model: string) => {
    setCurrentModel(model);
  }, []);

  const handleRAGToggle = useCallback((enabled: boolean) => {
    setRagEnabled(enabled);
  }, []);

  const displayMessages = messages;
  const modelList = models?.models || [];

  return (
    <div className="flex h-full flex-col bg-white">
      {}
      <div className="flex h-16 items-center justify-between border-b border-dark-200 bg-white px-4 lg:hidden">
        <button
          onClick={() => setShowSessions(!showSessions)}
          className="p-2 rounded-lg text-dark-500 hover:bg-dark-100"
          aria-label={showSessions ? 'Fechar conversas' : 'Abrir conversas'}
          title="Conversas"
        >
          <MessagesSquare className="h-6 w-6" />
        </button>
        <h1 className="truncate text-lg font-semibold text-dark-900">{sessionTitle}</h1>
        <Button variant="ghost" size="sm" onClick={handleNewSession} aria-label="Nova conversa" title="Nova conversa">
          <Plus className="h-5 w-5" />
        </Button>
      </div>

      <div className={cn('flex-1 flex', showSessions && 'lg:hidden')}>
        {}
        <aside
          className={cn(
            'hidden lg:block w-72 border-r border-dark-200',
            'transition-transform duration-300 ease-in-out'
          )}
        >
          <SessionList
            sessions={sessions}
            activeSessionId={activeSessionId}
            onSelect={handleSelectSession}
            onNew={handleNewSession}
            onDelete={handleDeleteSession}
            onRename={handleRenameSession}
            loading={sessionsLoading}
          />
        </aside>

        {}
        {showSessions && (
          <div className="fixed inset-0 z-40 lg:hidden">
            <div className="absolute inset-0 bg-black/50" onClick={() => setShowSessions(false)} />
            <aside className="absolute left-0 top-0 bottom-0 z-50 w-72 bg-white shadow-xl">
              <SessionList
                sessions={sessions}
                activeSessionId={activeSessionId}
                onSelect={handleSelectSession}
                onNew={handleNewSession}
                onDelete={handleDeleteSession}
                onRename={handleRenameSession}
                loading={sessionsLoading}
              />
            </aside>
          </div>
        )}

        {}
        <main className="flex-1 flex flex-col min-w-0">
          <ChatHeader
            sessionTitle={sessionTitle}
            currentModel={currentModel}
            models={modelList}
            onModelChange={handleModelChange}
            ragEnabled={ragEnabled}
            onRAGToggle={handleRAGToggle}
            disabled={isStreaming || modelsLoading}
          />

          <MessageList
            ref={messageListRef}
            messages={displayMessages}
            streamingMessage={streamingContent}
            isStreaming={isStreaming}
          />

          <MessageInput
            onSend={handleSendMessage}
            disabled={isStreaming || modelsLoading}
            streaming={isStreaming}
            placeholder="Digite sua mensagem..."
          />
        </main>
      </div>

      {}
      {modelsLoading && (
        <div className="fixed bottom-4 right-4 z-50 flex items-center gap-2 rounded-lg bg-dark-900 px-4 py-2 text-sm text-white shadow-lg">
          <Loader2 className="h-4 w-4 animate-spin" />
          Carregando modelos...
        </div>
      )}
    </div>
  );
}