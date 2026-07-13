import clsx from "clsx";
import type { JobStatus } from "../../types/job";

const COLORS: Record<string, string> = {
  success: "bg-brand-success shadow-[0_0_6px_rgba(22,199,132,0.4)]",
  failed: "bg-brand-danger shadow-[0_0_6px_rgba(234,67,67,0.4)]",
  partial: "bg-brand-warning shadow-[0_0_6px_rgba(245,158,11,0.4)]",
};

export function StatusDot({ status }: { status: JobStatus }) {
  return (
    <span
      className={clsx(
        "inline-block h-2 w-2 rounded-full",
        status ? COLORS[status] : "bg-text-faint"
      )}
      aria-label={`Status: ${status ?? "unknown"}`}
    />
  );
}
