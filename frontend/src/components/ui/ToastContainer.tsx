import { useToastStore } from "../../store/toastStore";
import { X, CheckCircle, AlertTriangle, Info } from "lucide-react";
import clsx from "clsx";

const VARIANT_STYLES = {
  success: "bg-brand-success-light border-brand-success/20 text-brand-success",
  error: "bg-brand-danger-light border-brand-danger/20 text-brand-danger",
  info: "bg-brand-info-light border-brand-info/20 text-brand-info",
};

const ICONS = {
  success: CheckCircle,
  error: AlertTriangle,
  info: Info,
};

export function ToastContainer() {
  const { toasts, dismiss } = useToastStore();

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2" role="region" aria-label="Notifications">
      {toasts.map((toast) => {
        const Icon = ICONS[toast.variant];
        return (
          <div
            key={toast.id}
            role="alert"
            onClick={() => dismiss(toast.id)}
            className={clsx(
              "flex cursor-pointer items-center gap-3 rounded-xl border px-4 py-3 text-sm shadow-elevated backdrop-blur-xl transition-all hover:scale-[1.02]",
              VARIANT_STYLES[toast.variant]
            )}
          >
            <Icon className="h-4 w-4 shrink-0" />
            <span className="flex-1">{toast.message}</span>
            <X className="h-3.5 w-3.5 shrink-0 opacity-50 hover:opacity-100" />
          </div>
        );
      })}
    </div>
  );
}
