export function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <p className="text-accent-loss font-medium">Couldn't load data</p>
      <p className="text-text-muted text-sm mt-1 mb-4">{message}</p>
      <button
        onClick={onRetry}
        className="rounded border border-border px-3 py-1.5 text-sm text-text-primary hover:bg-bg-elevated transition-colors"
      >
        Retry
      </button>
    </div>
  );
}