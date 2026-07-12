export function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <p className="text-text-primary font-medium">{title}</p>
      <p className="text-text-muted text-sm mt-1">{description}</p>
    </div>
  );
}