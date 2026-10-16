import { useState, useCallback } from 'react';
import { History, MessageSquare, Trash2, Clock, Bot, User } from 'lucide-react';
import { cn, formatRelativeTime, formatDate } from '../../lib/utils';
import { api } from '../../lib/api';
import { useSessions } from '../../hooks/useApi';
import { Button, Spinner, Badge } from '../ui';
import type { ChatSession, ChatMessage } from '../../types';

export function HistoryPanel() {
  const { sessions, loading, error, refetch } = useSessions();
  const [selectedSession, setSelectedSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [messagesLoading, setMessagesLoading] = useState(false);

  const loadMessages = useCallback(async (sessionId: string) => {
    setMessagesLoading(true);
    try {
      const history = await api.getSessionHistory(sessionId);
      setMessages(history.messages);
    } catch (err) {
      console.error('Failed to load session history:', err);
      setMessages([]);
    } finally {
      setMessagesLoading(false);
    }
  }, []);

  const handleSelect = useCallback((session: ChatSession) => {
    setSelectedSession(session);
    loadMessages(session.session_id);
  }, [loadMessages]);

  const handleDelete = useCallback(async (sessionId: string) => {
    if (window.confirm('Tem certeza que deseja excluir esta conversa?')) {
      try {
        await api.deleteSession(sessionId);
        if (selectedSession?.session_id === sessionId) {
          setSelectedSession(null);
          setMessages([]);
        }
        refetch();
      } catch (err) {
        console.error('Failed to delete session:', err);
        alert('Falha ao excluir conversa');
      }
    }
  }, [selectedSession, refetch]);

  return (
    <div className="flex h-full flex-col bg-white">
      <div className="flex h-16 items-center justify-between border-b border-dark-200 px-4 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-100">
            <History className="h-5 w-5 text-primary-600" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-dark-900">Histórico</h1>
            <p className="text-xs text-dark-500">{sessions.length} conversa(s) salva(s)</p>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={refetch} disabled={loading}>
          Atualizar
        </Button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {}
        <div className="w-full sm:w-80 border-r border-dark-200 flex flex-col overflow-hidden">
          {loading ? (
            <div className="flex h-full items-center justify-center">
              <Spinner size="lg" />
            </div>
          ) : error ? (
            <div className="flex h-full flex-col items-center justify-center text-center text-dark-500 p-4">
              <p className="text-sm text-red-600">{error}</p>
              <Button variant="outline" size="sm" onClick={refetch} className="mt-3">
                Tentar novamente
              </Button>
            </div>
          ) : sessions.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center text-center text-dark-500 p-4">
              <MessageSquare className="h-12 w-12 mb-3 text-dark-300" />
              <p className="text-sm">Nenhuma conversa salva</p>
              <p className="text-xs mt-1">Inicie um chat para criar o histórico</p>
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto scrollbar-thin p-2 space-y-1">
              {sessions.map((session) => (
                <button
                  key={session.session_id}
                  onClick={() => handleSelect(session)}
                  className={cn(
                    'w-full flex items-start gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-colors group',
                    selectedSession?.session_id === session.session_id
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-dark-600 hover:bg-dark-100 hover:text-dark-900'
                  )}
                >
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{session.title || 'Sem título'}</p>
                    <p className="mt-0.5 flex items-center gap-1 text-xs text-dark-400">
                      <Clock className="h-3 w-3" />
                      {formatRelativeTime(session.updated_at)}
                    </p>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleDelete(session.session_id); }}
                    className="p-1.5 rounded-lg text-dark-400 opacity-0 group-hover:opacity-100 hover:text-red-600 hover:bg-red-50 transition-all"
                    aria-label="Excluir conversa"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </button>
              ))}
            </div>
          )}
        </div>

        {}
        <div className="hidden sm:flex flex-1 flex-col overflow-hidden">
          {!selectedSession ? (
            <div className="flex h-full flex-col items-center justify-center text-center text-dark-500">
              <MessageSquare className="h-16 w-16 mb-4 text-dark-300" />
              <h3 className="text-lg font-medium text-dark-900 mb-1">Selecione uma conversa</h3>
              <p className="text-sm">Escolha uma conversa na lista ao lado para ver o histórico</p>
            </div>
          ) : (
            <>
              <div className="flex h-14 items-center justify-between border-b border-dark-200 px-4 bg-dark-50">
                <div className="min-w-0">
                  <p className="truncate font-medium text-dark-900">{selectedSession.title || 'Sem título'}</p>
                  <p className="text-xs text-dark-500">
                    {formatDate(selectedSession.created_at)} · {messages.length} mensagem(ns)
                  </p>
                </div>
                <Badge variant="info">{messages.length} msgs</Badge>
              </div>
              <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4">
                {messagesLoading ? (
                  <div className="flex h-full items-center justify-center">
                    <Spinner size="lg" />
                  </div>
                ) : messages.length === 0 ? (
                  <div className="flex h-full items-center justify-center text-dark-500">
                    <p className="text-sm">Nenhuma mensagem nesta conversa</p>
                  </div>
                ) : (
                  messages.map((msg, index) => (
                    <HistoryMessage key={msg.message_id || index} message={msg} />
                  ))
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function HistoryMessage({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';
  return (
    <div className={cn('flex gap-3', isUser && 'flex-row-reverse')}>
      <div
        className={cn(
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
          isUser ? 'bg-primary-600 text-white' : 'bg-dark-100 text-dark-600'
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>
      <div className={cn('flex-1 min-w-0', isUser && 'text-right')}>
        <div
          className={cn(
            'inline-block max-w-[85%] rounded-2xl px-4 py-2.5 text-left',
            isUser ? 'bg-primary-600 text-white rounded-tr-sm' : 'bg-dark-100 text-dark-900 rounded-tl-sm'
          )}
        >
          <p className="text-sm whitespace-pre-wrap break-words">{message.content}</p>
        </div>
        {message.created_at && (
          <div className={cn('mt-1 text-xs text-dark-400', isUser ? 'pr-2' : 'pl-2')}>
            {new Date(message.created_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
          </div>
        )}
      </div>
    </div>
  );
}
