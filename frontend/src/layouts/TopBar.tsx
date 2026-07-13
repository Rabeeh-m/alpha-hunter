import { Moon, Sun, PanelLeftClose, PanelLeft } from "lucide-react";
import { useUiStore } from "../store/uiStore";
import { useTokens } from "../hooks/useTokens";

export function TopBar() {
    const { theme, toggleTheme, sidebarCollapsed, toggleSidebar } = useUiStore();
    const { data } = useTokens({ page_size: 15 });
    const tokens = data?.items;

    return (
        <header className="flex h-14 items-center gap-4 border-b border-border bg-bg-surface/80 px-4 backdrop-blur-xl">
            <button onClick={toggleSidebar} className="rounded-lg p-1.5 text-text-muted transition-colors hover:bg-bg-hover hover:text-text-primary">
                {sidebarCollapsed ? <PanelLeft size={18} /> : <PanelLeftClose size={18} />}
            </button>

            <div className="flex-1 overflow-hidden">
                <div className="flex animate-[scroll_30s_linear_infinite] gap-8 whitespace-nowrap font-mono text-xs">
                    {tokens?.map((t) => (
                        <span key={t.id} className="text-text-muted">
                            {t.symbol}{" "}
                            <span className="text-text-primary">
                                ${t.price_usd ? Number(t.price_usd).toPrecision(4) : "—"}
                            </span>
                        </span>
                    ))}
                </div>
            </div>

            <button onClick={toggleTheme} className="rounded-lg p-1.5 text-text-muted transition-colors hover:bg-bg-hover hover:text-text-primary">
                {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
            </button>
        </header>
    );
}
