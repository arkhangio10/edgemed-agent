import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useGuestAuth } from "@/lib/guest-auth";

import Landing from "./pages/Landing";
import Auth from "./pages/Auth";
import AppLayout from "./components/AppLayout";
import Workspace from "./pages/Workspace";
import Records from "./pages/Records";
import RecordDetail from "./pages/RecordDetail";
import SyncStatus from "./pages/SyncStatus";
import Analytics from "./pages/Analytics";
import CopilotChat from "./pages/CopilotChat";
import DownloadApp from "./pages/DownloadApp";
import Docs from "./pages/Docs";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useGuestAuth();
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }
  if (!isAuthenticated) return <Navigate to="/auth" replace />;
  return <>{children}</>;
}

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/auth" element={<Auth />} />
          <Route path="/download" element={<Navigate to="/app/download" replace />} />
          <Route path="/docs" element={<Navigate to="/app/docs" replace />} />
          <Route
            path="/app"
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="workspace" replace />} />
            <Route path="workspace" element={<Workspace />} />
            <Route path="records" element={<Records />} />
            <Route path="records/:id" element={<RecordDetail />} />
            <Route path="copilot" element={<CopilotChat />} />
            <Route path="sync" element={<SyncStatus />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="download" element={<DownloadApp />} />
            <Route path="docs" element={<Docs />} />
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
