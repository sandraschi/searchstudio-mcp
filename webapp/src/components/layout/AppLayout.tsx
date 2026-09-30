import {
  Activity,
  CircleHelp,
  GraduationCap,
  HeartPulse,
  LayoutDashboard,
  MessagesSquare,
  ScrollText,
  Search,
  Settings,
  Wrench,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import { apiGet } from "@/api/client";
import { cn } from "@/lib/cn";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/search", label: "Search", icon: Search },
  { to: "/providers", label: "Providers", icon: HeartPulse },
  { to: "/activity", label: "Activity", icon: Activity },
  { to: "/tools", label: "Tools", icon: Wrench },
  { to: "/skills", label: "Skills", icon: GraduationCap },
  { to: "/chat", label: "Chat", icon: MessagesSquare },
  { to: "/settings", label: "Settings", icon: Settings },
  { to: "/help", label: "Help", icon: CircleHelp },
  { to: "/logs", label: "Logs", icon: ScrollText },
];

export function useBackendStatus(): "up" | "down" | "checking" {
  const [status, setStatus] = useState<"up" | "down" | "checking">("checking");
  useEffect(() => {
    let live = true;
    apiGet<{ success: boolean }>("/api/health")
      .then(() => live && setStatus("up"))
      .catch(() => live && setStatus("down"));
    return () => {
      live = false;
    };
  }, []);
  return status;
}

export default function AppLayout() {
  const { pathname } = useLocation();
  const backend = useBackendStatus();
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex">
      <aside className="w-56 shrink-0 border-r border-zinc-800/80 bg-zinc-900/40 p-3 flex flex-col gap-1">
        <div className="flex items-center gap-2 px-2 py-3">
          <Search size={20} className="text-zinc-100" />
          <span className="font-bold tracking-tight">SearchStudio</span>
        </div>
        {NAV.map((item) => {
          const active = item.end
            ? pathname === item.to
            : pathname.startsWith(item.to);
          const Icon = item.icon;
          return (
            <Link
              key={item.to}
              to={item.to}
              className={cn(
                "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-zinc-800 text-zinc-50"
                  : "text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/50",
              )}
            >
              <Icon size={17} />
              {item.label}
            </Link>
          );
        })}
        <div className="mt-auto px-3 py-2 text-xs flex items-center gap-2 text-zinc-500">
          <span
            className={cn(
              "inline-block h-2 w-2 rounded-full",
              backend === "up" && "bg-green-400",
              backend === "down" && "bg-red-400",
              backend === "checking" && "bg-zinc-500 animate-pulse",
            )}
          />
          backend {backend === "checking" ? "…" : backend}
        </div>
      </aside>
      <main className="flex-1 min-w-0 p-5 md:p-7 max-w-6xl">
        <Outlet />
      </main>
    </div>
  );
}
