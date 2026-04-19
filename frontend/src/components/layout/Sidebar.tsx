"use client";

import { cn } from "@/lib/utils";
import {
  BarChart3,
  BrainCircuit,
  HelpCircle,
  LayoutDashboard,
  Megaphone,
  Plug,
  Settings,
  ShieldAlert,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/campaigns", label: "Campaigns", icon: Megaphone },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/orchestrator", label: "AI Orchestrator", icon: BrainCircuit },
  { href: "/platforms", label: "Platforms", icon: Plug },
  { href: "/kill-switch", label: "Kill Switch", icon: ShieldAlert },
  { href: "/support", label: "Support", icon: HelpCircle },
  { href: "/settings", label: "Settings", icon: Settings },
] as const;

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="group/sidebar fixed inset-y-0 left-0 z-30 flex w-16 flex-col border-r border-zinc-800 bg-zinc-950 transition-all duration-200 hover:w-60">
      <div className="flex h-16 items-center gap-3 px-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-indigo-600 font-bold text-white">
          O
        </div>
        <span className="whitespace-nowrap text-sm font-semibold text-zinc-100 opacity-0 transition-opacity duration-200 group-hover/sidebar:opacity-100">
          OrchestraAI
        </span>
      </div>

      <nav className="mt-4 flex flex-1 flex-col gap-1 px-2">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                active
                  ? "bg-indigo-600/15 text-indigo-400"
                  : "text-zinc-400 hover:bg-zinc-800/60 hover:text-zinc-200",
              )}
            >
              <Icon className="h-5 w-5 shrink-0" />
              <span className="whitespace-nowrap opacity-0 transition-opacity duration-200 group-hover/sidebar:opacity-100">
                {label}
              </span>
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-zinc-800 p-3">
        <div className="flex items-center gap-3 px-1">
          <div className="h-7 w-7 shrink-0 rounded-full bg-zinc-700" />
          <span className="truncate text-xs text-zinc-500 opacity-0 transition-opacity duration-200 group-hover/sidebar:opacity-100">
            Enterprise Cloud
          </span>
        </div>
      </div>
    </aside>
  );
}
