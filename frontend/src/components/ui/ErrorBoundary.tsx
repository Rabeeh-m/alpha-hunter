import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}
interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // deliberately console.error only -- no backend error-reporting
    // endpoint exists yet; wiring one is a later milestone, not implied
    // scope creep on a UI-shell task
    console.error("UI error boundary caught:", error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex h-full flex-col items-center justify-center gap-2 text-center">
          <p className="text-accent-loss font-medium">Something broke</p>
          <p className="text-text-muted text-sm">{this.state.error.message}</p>
          <button
            onClick={() => this.setState({ error: null })}
            className="mt-2 rounded border border-border px-3 py-1.5 text-sm hover:bg-bg-elevated"
          >
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}