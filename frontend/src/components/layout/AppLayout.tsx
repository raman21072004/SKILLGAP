import { FlaskConical, History, LayoutDashboard, LogOut, Menu, PlusCircle, Settings, X } from "lucide-react";
import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "@/store/auth";
import { cn } from "@/utils/cn";
import { Logo } from "./Logo";

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/analyses/new", label: "New analysis", icon: PlusCircle },
  { to: "/history", label: "History", icon: History },
  { to: "/lab", label: "NLP Lab", icon: FlaskConical },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const signOut = async () => {
    await logout();
    toast.success("Signed out");
    navigate("/login");
  };

  const nav = (
    <nav aria-label="Main" className="flex flex-col gap-1">
      {NAV.map(({ to, label, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          end={to === "/dashboard"}
          onClick={() => setOpen(false)}
          className={({ isActive }) =>
            cn("flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-semibold transition-colors",
              isActive ? "bg-pine-soft text-pine" : "text-muted hover:bg-paper hover:text-ink")
          }
        >
          <Icon className="h-4 w-4" aria-hidden />
          {label}
        </NavLink>
      ))}
    </nav>
  );

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[15rem_1fr]">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-3 focus:top-3 focus:z-50 focus:rounded focus:bg-surface focus:p-2">Skip to content</a>
      <aside className="hidden border-r border-line bg-surface lg:flex lg:flex-col lg:justify-between lg:p-4">
        <div className="space-y-8">
          <div className="px-2 pt-1"><Logo to="/dashboard" /></div>
          {nav}
        </div>
        <div className="border-t border-line pt-4">
          <p className="truncate px-2 text-sm font-semibold">{user?.full_name}</p>
          <p className="truncate px-2 text-xs text-muted">{user?.email}</p>
          <button onClick={signOut} className="mt-3 flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-semibold text-muted hover:bg-paper hover:text-ink">
            <LogOut className="h-4 w-4" aria-hidden /> Sign out
          </button>
        </div>
      </aside>

      <header className="sticky top-0 z-30 flex items-center justify-between border-b border-line bg-surface px-4 py-3 lg:hidden">
        <Logo to="/dashboard" />
        <button onClick={() => setOpen((o) => !o)} aria-label={open ? "Close menu" : "Open menu"} aria-expanded={open} className="rounded-lg p-2 hover:bg-paper">
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </header>
      {open && (
        <div className="border-b border-line bg-surface p-4 lg:hidden">
          {nav}
          <button onClick={signOut} className="mt-2 flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-semibold text-muted hover:bg-paper">
            <LogOut className="h-4 w-4" aria-hidden /> Sign out
          </button>
        </div>
      )}

      <main id="main" className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 lg:px-10">
        <Outlet />
      </main>
    </div>
  );
}
