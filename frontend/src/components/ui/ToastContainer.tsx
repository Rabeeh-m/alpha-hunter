import { useToastStore } from "../../store/toastStore";
import clsx from "clsx";

const VARIANT_STYLES = {
  success: "border-accent-gain/40 text-accent-gain",
  error: "border-accent-loss/40 text-accent-loss",
  info: "border-accent-signal/40 text-accent-signal",
};

export function ToastContainer() {
  const { toasts, dismiss } = useToastStore();

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          role="status"
          onClick={() => dismiss(toast.id)}
          className={clsx(
            "cursor-pointer rounded border bg-bg-surface px-4 py-2 text-sm shadow-lg",
            VARIANT_STYLES[toast.variant]
          )}
        >
          {toast.message}
        </div>
      ))}
    </div>
  );
}