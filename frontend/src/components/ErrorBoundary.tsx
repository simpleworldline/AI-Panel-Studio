import React from 'react';
import { Button } from './ui/Button';

interface Props { children: React.ReactNode }
interface State { hasError: boolean; error: Error | null }

export class ErrorBoundary extends React.Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="text-center max-w-md">
            <p className="text-[var(--color-studio-destructive)] text-lg font-semibold mb-3">
              页面渲染出错
            </p>
            <p className="text-sm text-[var(--color-studio-fg-muted)] mb-2 break-all">
              {this.state.error?.message}
            </p>
            <Button
              variant="primary"
              size="sm"
              onClick={() => {
                this.setState({ hasError: false, error: null });
                window.location.reload();
              }}
            >
              刷新页面
            </Button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
