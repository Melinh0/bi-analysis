import { Component, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: { componentStack?: string }) {
    console.error('[ErrorBoundary]', error, info.componentStack);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex h-full min-h-[300px] flex-col items-center justify-center gap-4 p-8 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-red-100">
            <AlertTriangle className="h-7 w-7 text-red-600" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-dark-900">
              {this.props.fallbackTitle || 'Algo deu errado'}
            </h2>
            <p className="mt-1 max-w-md text-sm text-dark-500">
              Ocorreu um erro inesperado ao renderizar esta seção. Você pode tentar novamente
              sem perder o resto da aplicação.
            </p>
            {this.state.error && (
              <details className="mt-3 rounded-lg bg-dark-50 p-3 text-left">
                <summary className="cursor-pointer text-xs font-medium text-dark-600">
                  Detalhes técnicos
                </summary>
                <pre className="mt-2 whitespace-pre-wrap break-words text-xs text-dark-500">
                  {this.state.error.message}
                </pre>
              </details>
            )}
          </div>
          <button
            type="button"
            onClick={this.handleRetry}
            className="inline-flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500/40"
          >
            <RefreshCw className="h-4 w-4" />
            Tentar novamente
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
