import { useEffect } from "react";
import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { useUiStore } from "../store/uiStore";
import { ToastContainer } from "../components/ui/ToastContainer";
import { ErrorBoundary } from "../components/ui/ErrorBoundary";

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
    <div className="flex h-screen bg-bg text-text-primary">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto w-full max-w-7xl px-6 py-8">
            <ErrorBoundary>
              <div className="animate-fade-in">
                <Outlet />
              </div>
            </ErrorBoundary>
          </div>
        </main>
        <footer className="border-t border-border px-6 py-3 text-center text-xs text-text-muted">
          Alpha Hunter — research tool, not financial advice.
        </footer>
      </div>
      <ToastContainer />
    </div>
  );
}
