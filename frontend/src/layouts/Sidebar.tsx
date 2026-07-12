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
                "flex flex-col border-r border-border bg-bg-surface transition-all",
                collapsed ? "w-16" : "w-56"
            )}
        >
            <div className="flex h-14 items-center px-4 font-mono font-semibold text-accent-gain">
                {collapsed ? "AH" : "ALPHA HUNTER"}
            </div>
            <nav className="flex-1 space-y-1 px-2">
                {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
                    <NavLink
                        key={to}
                        to={to}
                        end={to === "/"}
                        className={({ isActive }) =>
                            clsx(
                                "flex items-center gap-3 rounded px-3 py-2 text-sm transition-colors",
                                isActive
                                    ? "bg-accent-gain/10 text-accent-gain"
                                    : "text-text-muted hover:bg-bg-elevated hover:text-text-primary"
                            )
                        }
                    >
                        <Icon size={18} />
                        {!collapsed && <span>{label}</span>}
                    </NavLink>
                ))}
            </nav>
        </aside>
    );
}