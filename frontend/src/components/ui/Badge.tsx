import type { ReactNode } from "react";

const variants = {
  gain: "bg-accent-gain/10 text-accent-gain border-accent-gain/30",
  loss: "bg-accent-loss/10 text-accent-loss border-accent-loss/30",
  signal: "bg-accent-signal/10 text-accent-signal border-accent-signal/30",
  neutral: "bg-bg-elevated text-text-muted border-border",
};

export function Badge({
  children,
  variant = "neutral",
}: {
  children: ReactNode;
  variant?: keyof typeof variants;
}) {
  return (
    <span className={`inline-flex items-center rounded border px-1.5 py-0.5 text-xs font-mono ${variants[variant]}`}>
      {children}
    </span>
  );
}