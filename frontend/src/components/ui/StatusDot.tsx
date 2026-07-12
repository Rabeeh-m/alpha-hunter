import clsx from "clsx";
import type { JobStatus } from "../../types/job";

const COLORS: Record<string, string> = {
  success: "bg-accent-gain",
  failed: "bg-accent-loss",
  partial: "bg-accent-signal",
};

export function StatusDot({ status }: { status: JobStatus }) {
  return (
    <span
      className={clsx("inline-block h-2 w-2 rounded-full", status ? COLORS[status] : "bg-text-faint")}
    />
  );
}