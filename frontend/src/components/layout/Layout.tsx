import { useState } from 'react';
import { cn } from '../../lib/utils';
import { Menu, X, Bot, BarChart3, PieChart, Settings, History, Database, Plug } from 'lucide-react';

export type TabId = 'chat' | 'reports' | 'analise' | 'scrapers' | 'conexoes' | 'history' | 'settings';

interface LayoutProps {
  children: React.ReactNode;
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
}

const navigation = [
  { id: 'chat' as const, label: 'Chat', icon: Bot },
  { id: 'analise' as const, label: 'Análises', icon: BarChart3 },
  { id: 'reports' as const, label: 'Relatórios', icon: PieChart },
  { id: 'conexoes' as const, label: 'Conexões', icon: Plug },
  { id: 'scrapers' as const, label: 'Scrapers', icon: Database },
  { id: 'history' as const, label: 'Histórico', icon: History },
  { id: 'settings' as const, label: 'Configurações', icon: Settings },
];

export function Layout({ children, activeTab, onTabChange }: LayoutProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-dark-50">
      {}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/50 lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      {}
      <aside
        className={cn(
          'z-30 flex w-64 flex-shrink-0 flex-col bg-white border-r border-dark-200',
          'fixed inset-y-0 left-0 transition-transform duration-300 ease-in-out lg:static lg:translate-x-0',
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex h-16 items-center justify-between border-b border-dark-200 px-4 lg:px-6">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600">
              <Bot className="h-5 w-5 text-white" />
            </div>
            <span className="font-semibold text-dark-900">BI Analysis</span>
          </div>
          <button
            onClick={() => setMobileMenuOpen(false)}
            className="p-1.5 rounded-lg text-dark-400 hover:text-dark-600 hover:bg-dark-100 lg:hidden"
            aria-label="Fechar menu"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-1" aria-label="Navegação principal">
          {navigation.map(item => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  onTabChange(item.id);
                  setMobileMenuOpen(false);
                }}
                className={cn(
                  'w-full flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-dark-600 hover:bg-dark-100 hover:text-dark-900'
                )}
                aria-current={isActive ? 'page' : undefined}
              >
                <Icon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="border-t border-dark-200 p-4">
          <div className="flex items-center gap-3 rounded-lg bg-dark-50 p-3">
            <div className="flex h-8 w-8 items-center justify-center rounded bg-primary-100">
              <Bot className="h-4 w-4 text-primary-600" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-dark-900 truncate">Powered by Ollama</p>
              <p className="text-xs text-dark-500">Local LLM + RAG Pipeline</p>
            </div>
          </div>
        </div>
      </aside>

      {}
      <div className="flex flex-1 flex-col overflow-hidden min-w-0">
        {}
        <header className="flex h-16 flex-shrink-0 items-center justify-between border-b border-dark-200 bg-white px-4 lg:hidden">
          <button
            onClick={() => setMobileMenuOpen(true)}
            className="p-2 rounded-lg text-dark-500 hover:bg-dark-100"
            aria-label="Abrir menu"
          >
            <Menu className="h-6 w-6" />
          </button>
          <h1 className="text-lg font-semibold text-dark-900">BI Analysis</h1>
          <div className="w-10" />
        </header>

        {}
        <main className="flex-1 overflow-hidden">{children}</main>
      </div>
    </div>
  );
}
