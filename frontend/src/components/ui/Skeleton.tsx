import clsx from "clsx";

export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      className={clsx(
        "animate-pulse rounded-xl bg-bg-elevated",
        className
      )}
      role="presentation"
      aria-hidden="true"
    />
  );
}
