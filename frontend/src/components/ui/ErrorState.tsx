import { AlertTriangle, RefreshCw } from "lucide-react";

export function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-danger-light">
        <AlertTriangle className="h-6 w-6 text-brand-danger" />
      </div>
      <p className="text-sm font-medium text-text-primary">Couldn't load data</p>
      <p className="mt-1 mb-4 text-sm text-text-secondary">{message}</p>
      <button
        onClick={onRetry}
        className="inline-flex items-center gap-2 rounded-xl bg-brand-primary px-4 py-2.5 text-sm font-medium text-white shadow-card transition-all hover:bg-brand-primary-hover hover:shadow-card-hover focus:outline-none focus:ring-2 focus:ring-brand-primary focus:ring-offset-2"
      >
        <RefreshCw className="h-4 w-4" />
        Retry
      </button>
    </div>
  );
}
