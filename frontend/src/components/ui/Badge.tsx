import type { ReactNode } from "react";
import clsx from "clsx";

const variants = {
  success: "bg-brand-success-light text-brand-success border-brand-success/20",
  danger: "bg-brand-danger-light text-brand-danger border-brand-danger/20",
  warning: "bg-brand-warning-light text-brand-warning border-brand-warning/20",
  info: "bg-brand-info-light text-brand-info border-brand-info/20",
  neutral: "bg-bg-elevated text-text-secondary border-border",
  primary: "bg-brand-primary-light text-brand-primary border-brand-primary/20",
  signal: "bg-brand-warning-light text-brand-warning border-brand-warning/20",
  gain: "bg-brand-success-light text-brand-success border-brand-success/20",
  loss: "bg-brand-danger-light text-brand-danger border-brand-danger/20",
};

export function Badge({
  children,
  variant = "neutral",
  className,
}: {
  children: ReactNode;
  variant?: keyof typeof variants;
  className?: string;
}) {
  return (
    <span className={clsx("inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium", variants[variant], className)}>
      {children}
    </span>
  );
}
