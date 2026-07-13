import { NavLink } from "react-router-dom";
import { LayoutDashboard, ScanLine, Wallet, Settings, Activity } from "lucide-react";
import { useUiStore } from "../store/uiStore";
import clsx from "clsx";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/screener", label: "Screener", icon: ScanLine },
  { to: "/wallets", label: "Wallets", icon: Wallet },
  { to: "/system", label: "System", icon: Activity },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const collapsed = useUiStore((s) => s.sidebarCollapsed);

  return (
    <aside
      className={clsx(
        "flex flex-col border-r border-border bg-bg-surface transition-all duration-300",
        collapsed ? "w-[68px]" : "w-60"
      )}
    >
      <div className="flex h-16 items-center gap-3 border-b border-border px-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-primary">
          <span className="text-xs font-bold text-white">AH</span>
        </div>
        {!collapsed && (
          <span className="text-sm font-semibold tracking-tight text-text-primary">
            Alpha Hunter
          </span>
        )}
      </div>
      <nav className="flex-1 space-y-0.5 px-3 py-4">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-brand-primary-light text-brand-primary"
                  : "text-text-secondary hover:bg-bg-hover hover:text-text-primary"
              )
            }
          >
            <Icon size={18} className="shrink-0" />
            {!collapsed && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>
      <div className={clsx("border-t border-border p-3", collapsed && "flex justify-center")}>
        {!collapsed && (
          <p className="text-xs text-text-muted">Alpha Hunter v1.0</p>
        )}
      </div>
    </aside>
  );
}
