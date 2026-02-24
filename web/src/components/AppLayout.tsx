import { Outlet, Link, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  FileText,
  RefreshCw,
  BarChart3,
  Download,
  HelpCircle,
  LogOut,
  Menu,
  X,
  Home,
  MessageSquare,
} from "lucide-react";
import { NavLink } from "@/components/NavLink";
import { StatusBadge } from "@/components/StatusBadge";
import { ConnectionIndicator } from "@/components/ConnectionIndicator";
import PatientSelector from "@/components/PatientSelector";
import FloatingCopilot from "@/components/FloatingCopilot";
import { useGuestAuth } from "@/lib/guest-auth";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { cn } from "@/lib/utils";
import edgemedLogo from "@/assets/edgemed-logo.svg";

const navItems = [
  { title: "Home", url: "/", icon: Home, external: true },
  { title: "Workspace", url: "/app/workspace", icon: LayoutDashboard },
  { title: "Records", url: "/app/records", icon: FileText },
  { title: "Copilot Chat", url: "/app/copilot", icon: MessageSquare },
  { title: "Sync Status", url: "/app/sync", icon: RefreshCw },
  { title: "Analytics", url: "/app/analytics", icon: BarChart3 },
  { title: "Download App", url: "/app/download", icon: Download },
  { title: "Docs / FAQ", url: "/app/docs", icon: HelpCircle },
];

export default function AppLayout() {
  const { logout } = useGuestAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background">
      {mobileOpen && (
        <div
          className="fixed inset-0 z-30 bg-foreground/20 md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-border bg-sidebar transition-transform duration-200 md:relative md:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-14 items-center justify-between border-b border-border px-4">
          <Link to="/app/workspace" className="flex items-center gap-2">
            <img src={edgemedLogo} alt="EdgeMed" className="h-9 w-9 rounded-lg object-contain" />
            <span className="font-semibold text-foreground">EdgeMed</span>
          </Link>
          <button
            className="md:hidden text-muted-foreground"
            onClick={() => setMobileOpen(false)}
            aria-label="Close sidebar"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-4" aria-label="Main navigation">
          {navItems.map((item) => (
            <NavLink
              key={item.url}
              to={item.url}
              end={item.url === "/app/workspace"}
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-sidebar-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
              activeClassName="bg-sidebar-accent text-sidebar-accent-foreground"
              onClick={() => setMobileOpen(false)}
            >
              <item.icon className="h-4 w-4 shrink-0" />
              <span>{item.title}</span>
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-border p-3 space-y-2">
          <p className="text-[10px] text-warning/80 leading-tight text-center">
            Documentation only — not for diagnosis or treatment.
          </p>
          <p className="text-[10px] text-muted-foreground leading-tight text-center">
            <a
              href="https://developers.google.com/health-ai-developer-foundations"
              target="_blank"
              rel="noopener noreferrer"
              className="underline hover:text-foreground"
            >
              MedGemma / HAI-DEF by Google
            </a>
          </p>
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start gap-2 text-muted-foreground"
            onClick={handleLogout}
          >
            <LogOut className="h-4 w-4" />
            End Session
          </Button>
        </div>
      </aside>

      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-14 items-center justify-between border-b border-border bg-card px-4">
          <div className="flex items-center gap-3">
            <button
              className="md:hidden text-muted-foreground"
              onClick={() => setMobileOpen(true)}
              aria-label="Open sidebar"
            >
              <Menu className="h-5 w-5" />
            </button>
            <h1 className="text-sm font-semibold text-foreground hidden sm:block">
              EdgeMed Agent
            </h1>
            <StatusBadge variant="info">DEMO</StatusBadge>
          </div>
          <div className="flex items-center gap-3">
            <PatientSelector />
            <ConnectionIndicator />
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>

      <FloatingCopilot />
    </div>
  );
}
