"use client";

import { Card, CardContent } from "@/components/ui/card";
import { CreditCard, KeyRound, Settings, Users } from "lucide-react";
import Link from "next/link";

const SECTIONS = [
  {
    href: "/settings/billing",
    label: "Billing & Plans",
    description: "Manage your subscription, upgrade plans, and view invoices.",
    icon: CreditCard,
    ready: true,
  },
  {
    href: "/settings",
    label: "Team Management",
    description: "Invite members, manage roles, and configure team access.",
    icon: Users,
    ready: false,
  },
  {
    href: "/settings",
    label: "API Keys",
    description: "Generate and manage API keys for programmatic access.",
    icon: KeyRound,
    ready: false,
  },
] as const;

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-sm text-zinc-500">
          Manage your account, team, and platform connections.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {SECTIONS.map((s) => {
          const Icon = s.icon;
          const Wrapper = s.ready ? Link : "div";
          return (
            <Wrapper
              key={s.label}
              href={s.ready ? s.href : "#"}
              className="group"
            >
              <Card className="h-full transition-colors hover:border-indigo-500/40">
                <CardContent className="flex flex-col items-start gap-3 py-5">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-zinc-800 group-hover:bg-indigo-600/20">
                    <Icon className="h-5 w-5 text-zinc-400 group-hover:text-indigo-400" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-zinc-200">
                      {s.label}
                    </p>
                    <p className="mt-1 text-xs text-zinc-500">
                      {s.description}
                    </p>
                  </div>
                  {!s.ready && (
                    <span className="rounded bg-zinc-800 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-zinc-500">
                      Coming soon
                    </span>
                  )}
                </CardContent>
              </Card>
            </Wrapper>
          );
        })}
      </div>
    </div>
  );
}
