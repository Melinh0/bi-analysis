import { Plus, Trash2, Pencil, Clock, MessageSquare } from 'lucide-react';
import { useState } from 'react';
import { cn, formatRelativeTime } from '../../lib/utils';
import { Button } from '../ui';
import type { ChatSession } from '../../types';

interface SessionListProps {
  sessions: ChatSession[];
  activeSessionId: string | null;
  onSelect: (sessionId: string) => void;
  onNew: () => void;
  onDelete: (sessionId: string) => void;
  onRename: (sessionId: string, newTitle: string) => void;
  loading?: boolean;
}

export function SessionList({
  sessions,
  activeSessionId,
  onSelect,
  onNew,
  onDelete,
  onRename,
  loading,
}: SessionListProps) {
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState('');

  const handleRenameStart = (session: ChatSession) => {
    setRenamingId(session.session_id);
    setRenameValue(session.title || '');
  };

  const handleRenameConfirm = (sessionId: string) => {
    if (renameValue.trim() && renameValue.trim() !== sessions.find(s => s.session_id === sessionId)?.title) {
      onRename(sessionId, renameValue.trim());
    }
    setRenamingId(null);
    setRenameValue('');
  };

  const handleKeyDown = (e: React.KeyboardEvent, sessionId: string) => {
    if (e.key === 'Enter') handleRenameConfirm(sessionId);
    if (e.key === 'Escape') {
      setRenamingId(null);
      setRenameValue('');
    }
  };

  return (
    <div className="flex h-full flex-col bg-white border-r border-dark-200">
      <div className="flex h-16 items-center justify-between border-b border-dark-200 px-4">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-dark-900">
          <MessageSquare className="h-5 w-5 text-primary-600" />
          Conversas
        </h2>
        <Button variant="ghost" size="sm" onClick={onNew} aria-label="Nova conversa">
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      {loading ? (
        <div className="flex h-full items-center justify-center px-4">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary-600 border-t-transparent" />
        </div>
      ) : sessions.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center px-4 text-center text-dark-500">
          <MessageSquare className="h-12 w-12 mb-3 text-dark-300" />
          <p className="text-sm">Nenhuma conversa ainda</p>
          <p className="text-xs mt-1">Clique em + para iniciar</p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto scrollbar-thin p-2 space-y-1">
          {sessions.map((session) => (
            <SessionItem
              key={session.session_id}
              session={session}
              isActive={session.session_id === activeSessionId}
              onSelect={onSelect}
              onDelete={onDelete}
              onRenameStart={handleRenameStart}
              onRenameConfirm={handleRenameConfirm}
              onKeyDown={handleKeyDown}
              renamingId={renamingId}
              renameValue={renameValue}
              setRenameValue={setRenameValue}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function SessionItem({
  session,
  isActive,
  onSelect,
  onDelete,
  onRenameStart,
  onRenameConfirm,
  onKeyDown,
  renamingId,
  renameValue,
  setRenameValue,
}: {
  session: ChatSession;
  isActive: boolean;
  onSelect: (sessionId: string) => void;
  onDelete: (sessionId: string) => void;
  onRenameStart: (session: ChatSession) => void;
  onRenameConfirm: (sessionId: string) => void;
  onKeyDown: (e: React.KeyboardEvent, sessionId: string) => void;
  renamingId: string | null;
  renameValue: string;
  setRenameValue: (value: string) => void;
}) {
  const isRenaming = renamingId === session.session_id;

  return (
    <div
      className={cn(
        'relative group',
        isActive && 'bg-primary-50'
      )}
    >
      {isRenaming ? (
        <div className="p-2">
          <input
            type="text"
            value={renameValue}
            onChange={(e) => setRenameValue(e.target.value)}
            onKeyDown={(e) => onKeyDown(e, session.session_id)}
            onBlur={() => onRenameConfirm(session.session_id)}
            autoFocus
            className="w-full rounded-lg border border-primary-500 bg-white px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20"
            aria-label="Renomear conversa"
          />
        </div>
      ) : (
        <button
          onClick={() => onSelect(session.session_id)}
          className={cn(
            'w-full flex items-start gap-3 rounded-lg px-3 py-2.5 text-left text-sm',
            'transition-colors',
            isActive
              ? 'bg-primary-50 text-primary-700'
              : 'text-dark-600 hover:bg-dark-100 hover:text-dark-900'
          )}
        >
          <div className="flex-1 min-w-0">
            <p className={cn('font-medium truncate', isActive ? 'text-primary-900' : '')}>
              {session.title || 'Sem título'}
            </p>
            <p className={cn('mt-0.5 truncate text-xs', isActive ? 'text-primary-600' : 'text-dark-400')}>
              <Clock className="inline h-3 w-3 mr-1" /> {formatRelativeTime(session.updated_at)}
            </p>
          </div>
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={(e) => { e.stopPropagation(); onRenameStart(session); }}
              className="p-1.5 rounded-lg text-dark-400 hover:text-dark-600 hover:bg-dark-200 transition-colors"
              aria-label="Renomear"
            >
              <Pencil className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); onDelete(session.session_id); }}
              className="p-1.5 rounded-lg text-dark-400 hover:text-red-600 hover:bg-red-50 transition-colors"
              aria-label="Excluir"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        </button>
      )}
    </div>
  );
}