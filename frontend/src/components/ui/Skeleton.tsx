export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded bg-bg-elevated ${className}`} />;
}