export function ComingSoonPage({ title, milestone }: { title: string; milestone: string }) {
  return (
    <div className="flex h-full flex-col items-center justify-center text-center">
      <p className="font-mono text-sm text-accent-signal">{milestone}</p>
      <h2 className="mt-2 text-lg font-medium text-text-primary">{title}</h2>
      <p className="mt-1 text-sm text-text-muted">This page isn't built yet.</p>
    </div>
  );
}