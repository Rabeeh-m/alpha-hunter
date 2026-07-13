export function ComingSoonPage({ title, milestone }: { title: string; milestone: string }) {
  return (
    <div className="flex h-full flex-col items-center justify-center text-center">
      <span className="rounded-full bg-brand-primary-light px-3 py-1 font-mono text-xs font-medium text-brand-primary">{milestone}</span>
      <h2 className="mt-4 text-xl font-semibold tracking-tight text-text-primary">{title}</h2>
      <p className="mt-1 text-sm text-text-secondary">This page isn't built yet.</p>
    </div>
  );
}
