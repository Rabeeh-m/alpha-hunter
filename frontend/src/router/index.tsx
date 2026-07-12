import { createBrowserRouter } from "react-router-dom";
import { AppLayout } from "../layouts/AppLayout";
import { DashboardPage } from "../pages/DashboardPage";
import { ScreenerPage } from "../pages/ScreenerPage";
import { TokenDetailsPage } from "../pages/TokenDetailsPage";
import { ComingSoonPage } from "../pages/ComingSoonPage";
import { SystemPage } from "../pages/SystemPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "screener", element: <ScreenerPage /> },
      { path: "tokens/:id", element: <TokenDetailsPage /> },
      { path: "wallets", element: <ComingSoonPage title="Wallet Intelligence" milestone="V2" /> },
      { path: "system", element: <ComingSoonPage title="System Status" milestone="M5" /> },
      { path: "settings", element: <ComingSoonPage title="Settings" milestone="V11" /> },
      { path: "system", element: <SystemPage /> },
    ],
  },
]);