import { useEffect } from "react";
import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { useUiStore } from "../store/uiStore";

export function AppLayout() {
  const theme = useUiStore((s) => s.theme);

  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
  }, [theme]);

  return (
    <div className="flex h-screen bg-bg">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
        <footer className="border-t border-border px-6 py-2 text-xs text-text-faint">
          Alpha Hunter — research tool, not financial advice.
        </footer>
      </div>
    </div>
  );
}