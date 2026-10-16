import { useState } from 'react';
import { Layout, type TabId } from './components/layout/Layout';
import { ChatPanel } from './components/chat';
import { ReportsPanel } from './components/reports';
import { AnalisePanel } from './components/analise';
import { ScrapersPanel } from './components/scrapers';
import { ConexoesPanel } from './components/conexoes';
import { HistoryPanel } from './components/history';
import { SettingsPanel } from './components/settings';
import { ErrorBoundary } from './components/ui/ErrorBoundary';

function App() {
  const [activeTab, setActiveTab] = useState<TabId>('chat');

  const renderContent = () => {
    switch (activeTab) {
      case 'chat':
        return (
          <ErrorBoundary fallbackTitle="Erro no Chat">
            <ChatPanel />
          </ErrorBoundary>
        );
      case 'analise':
        return (
          <ErrorBoundary fallbackTitle="Erro nas Análises">
            <AnalisePanel />
          </ErrorBoundary>
        );
      case 'reports':
        return (
          <ErrorBoundary fallbackTitle="Erro nos Relatórios">
            <ReportsPanel />
          </ErrorBoundary>
        );
      case 'scrapers':
        return (
          <ErrorBoundary fallbackTitle="Erro nos Scrapers">
            <ScrapersPanel />
          </ErrorBoundary>
        );
      case 'conexoes':
        return (
          <ErrorBoundary fallbackTitle="Erro nas Conexões">
            <ConexoesPanel />
          </ErrorBoundary>
        );
      case 'history':
        return (
          <ErrorBoundary fallbackTitle="Erro no Histórico">
            <HistoryPanel />
          </ErrorBoundary>
        );
      case 'settings':
        return (
          <ErrorBoundary fallbackTitle="Erro nas Configurações">
            <SettingsPanel />
          </ErrorBoundary>
        );
      default:
        return (
          <ErrorBoundary fallbackTitle="Erro no Chat">
            <ChatPanel />
          </ErrorBoundary>
        );
    }
  };

  return (
    <Layout activeTab={activeTab} onTabChange={setActiveTab}>
      {renderContent()}
    </Layout>
  );
}

export default App;
