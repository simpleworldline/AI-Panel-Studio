import { Component, type ReactNode } from 'react';
import { Button } from './ui/Button';

interface Props { children: ReactNode; }
interface State { hasError: boolean; error: Error | null; }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-[var(--color-studio-bg)]">
          <div className="text-center px-4">
            <h2 className="text-xl font-semibold text-[var(--color-studio-fg)] mb-2">页面出现错误</h2>
            <p className="text-sm text-[var(--color-studio-fg-muted)] mb-6 max-w-md">
              {this.state.error?.message || '发生了未预期的错误'}
            </p>
            <Button variant="primary" onClick={() => { this.setState({ hasError: false, error: null }); window.location.href = '/'; }}>
              返回首页
            </Button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
