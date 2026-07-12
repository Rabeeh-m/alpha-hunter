import { Moon, Sun, PanelLeftClose, PanelLeft } from "lucide-react";
import { useUiStore } from "../store/uiStore";
import { useTokens } from "../hooks/useTokens";

export function TopBar() {
    const { theme, toggleTheme, sidebarCollapsed, toggleSidebar } = useUiStore();
    const { data: tokens } = useTokens(15, 0);

    return (
        <header className="flex h-14 items-center gap-4 border-b border-border px-4">
            <button onClick={toggleSidebar} className="text-text-muted hover:text-text-primary">
                {sidebarCollapsed ? <PanelLeft size={18} /> : <PanelLeftClose size={18} />}
            </button>

            {/* Ticker tape — scrolling live-feed strip, the signature element */}
            <div className="flex-1 overflow-hidden">
                <div className="flex animate-[scroll_30s_linear_infinite] gap-6 whitespace-nowrap font-mono text-xs">
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

            <button onClick={toggleTheme} className="text-text-muted hover:text-text-primary">
                {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
            </button>
        </header>
    );
}