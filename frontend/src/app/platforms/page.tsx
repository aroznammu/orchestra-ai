"use client";

import { Card, CardContent } from "@/components/ui/card";
import {
  ApiError,
  disconnectPlatform,
  initPlatformAuth,
  listAvailablePlatforms,
  listPlatformConnections,
  type AvailablePlatform,
  type PlatformConnection,
  type PlatformKey,
} from "@/lib/apiClient";
import { cn } from "@/lib/utils";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  Link2,
  Link2Off,
  Loader2,
  Plug,
  Shield,
} from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

// ---------------------------------------------------------------------------
// Display metadata
// ---------------------------------------------------------------------------

type PlatformDisplay = {
  label: string;
  accent: string;
  initial: string;
};

const PLATFORM_META: Record<PlatformKey, PlatformDisplay> = {
  facebook: { label: "Facebook", accent: "from-blue-600 to-blue-500", initial: "f" },
  instagram: {
    label: "Instagram",
    accent: "from-pink-500 via-fuchsia-500 to-amber-400",
    initial: "Ig",
  },
  tiktok: { label: "TikTok", accent: "from-rose-500 to-cyan-500", initial: "TT" },
  twitter: { label: "Twitter / X", accent: "from-zinc-600 to-zinc-400", initial: "X" },
  youtube: { label: "YouTube", accent: "from-red-600 to-red-500", initial: "YT" },
  google_ads: {
    label: "Google Ads",
    accent: "from-sky-500 via-amber-400 to-emerald-500",
    initial: "G",
  },
  linkedin: { label: "LinkedIn", accent: "from-sky-700 to-sky-500", initial: "in" },
  snapchat: { label: "Snapchat", accent: "from-yellow-400 to-amber-500", initial: "Sc" },
  pinterest: { label: "Pinterest", accent: "from-red-700 to-rose-500", initial: "P" },
};

function fallbackMeta(key: string): PlatformDisplay {
  return {
    label: key.replace(/_/g, " "),
    accent: "from-zinc-700 to-zinc-600",
    initial: key.slice(0, 2).toUpperCase(),
  };
}

// ---------------------------------------------------------------------------
// Row
// ---------------------------------------------------------------------------

function PlatformCard({
  platform,
  connection,
  onConnect,
  onDisconnect,
  busy,
}: {
  platform: AvailablePlatform;
  connection: PlatformConnection | null;
  onConnect: (key: PlatformKey) => void;
  onDisconnect: (key: PlatformKey) => void;
  busy: PlatformKey | null;
}) {
  const meta = PLATFORM_META[platform.platform] ?? fallbackMeta(platform.platform);
  const isConnected = Boolean(connection && connection.is_active);
  const isBusy = busy === platform.platform;
  const isStub = platform.is_stub;

  return (
    <Card className="overflow-hidden transition-colors hover:border-indigo-500/40">
      <CardContent className="flex flex-col gap-4 py-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div
              className={cn(
                "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br text-sm font-bold text-white shadow-inner",
                meta.accent,
              )}
            >
              {meta.initial}
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-zinc-100">
                {platform.name || meta.label}
              </p>
              <p className="text-[11px] uppercase tracking-wider text-zinc-500">
                {platform.platform.replace(/_/g, " ")}
              </p>
            </div>
          </div>

          {isConnected ? (
            <span className="flex items-center gap-1.5 whitespace-nowrap text-[11px] font-medium text-emerald-400">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              Connected
            </span>
          ) : (
            <span className="flex items-center gap-1.5 whitespace-nowrap text-[11px] font-medium text-zinc-500">
              <span className="h-1.5 w-1.5 rounded-full bg-zinc-600" />
              Not connected
            </span>
          )}
        </div>

        {isStub && (
          <div className="flex items-start gap-2 rounded-lg border border-amber-800/40 bg-amber-950/30 px-3 py-2 text-[11px] text-amber-300">
            <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" />
            <span>
              Connector runs in stub mode. Publishes will be simulated until
              production OAuth credentials are configured on the backend.
            </span>
          </div>
        )}

        {isConnected && connection && (
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 rounded-lg border border-zinc-800/60 bg-zinc-900/40 px-3 py-2 text-[11px] text-zinc-400">
            <span className="text-zinc-500">Account</span>
            <span className="truncate text-right">
              {connection.platform_user_id ?? "—"}
            </span>
            <span className="text-zinc-500">Since</span>
            <span className="text-right">
              {new Date(connection.connected_at).toLocaleDateString()}
            </span>
          </div>
        )}

        <div className="flex items-center justify-end pt-1">
          {isConnected ? (
            <button
              onClick={() => onDisconnect(platform.platform)}
              disabled={isBusy}
              className="flex items-center gap-1.5 rounded-lg border border-zinc-700 px-3 py-1.5 text-xs font-medium text-zinc-300 transition-colors hover:border-red-500/50 hover:bg-red-950/30 hover:text-red-300 disabled:opacity-50"
            >
              {isBusy ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Link2Off className="h-3.5 w-3.5" />
              )}
              Disconnect
            </button>
          ) : (
            <button
              onClick={() => onConnect(platform.platform)}
              disabled={isBusy}
              className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-indigo-500 disabled:opacity-50"
            >
              {isBusy ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Link2 className="h-3.5 w-3.5" />
              )}
              Connect
            </button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function PlatformsPage() {
  const queryClient = useQueryClient();
  const [banner, setBanner] = useState<{
    tone: "success" | "error";
    text: string;
    href?: string;
  } | null>(null);
  const [busy, setBusy] = useState<PlatformKey | null>(null);

  const availableQuery = useQuery({
    queryKey: ["platforms", "available"],
    queryFn: listAvailablePlatforms,
    staleTime: 10 * 60_000,
  });

  const connectionsQuery = useQuery({
    queryKey: ["platforms", "connections"],
    queryFn: listPlatformConnections,
    staleTime: 30_000,
  });

  const connectionByPlatform = useMemo(() => {
    const map = new Map<PlatformKey, PlatformConnection>();
    for (const c of connectionsQuery.data?.connections ?? []) {
      map.set(c.platform, c);
    }
    return map;
  }, [connectionsQuery.data]);

  const connectMutation = useMutation({
    mutationFn: async (platform: PlatformKey) => {
      const origin =
        typeof window !== "undefined" ? window.location.origin : "";
      const redirectUri = `${origin}/platforms?oauth=${platform}`;
      return initPlatformAuth(platform, redirectUri);
    },
    onMutate: (platform) => setBusy(platform),
    onSuccess: (data, platform) => {
      setBusy(null);
      setBanner({
        tone: "success",
        text: `Opening ${PLATFORM_META[platform]?.label ?? platform} authorization in a new tab.`,
        href: data.auth_url,
      });
      if (typeof window !== "undefined") {
        window.open(data.auth_url, "_blank", "noopener,noreferrer");
      }
    },
    onError: (err) => {
      setBusy(null);
      if (err instanceof ApiError && err.status === 501) {
        setBanner({
          tone: "error",
          text: "This platform's OAuth flow isn't configured on the backend yet.",
        });
      } else {
        setBanner({
          tone: "error",
          text: err instanceof Error ? err.message : "Failed to start auth flow.",
        });
      }
    },
  });

  const disconnectMutation = useMutation({
    mutationFn: disconnectPlatform,
    onMutate: (platform) => setBusy(platform),
    onSuccess: (_data, platform) => {
      setBusy(null);
      setBanner({
        tone: "success",
        text: `Disconnected ${PLATFORM_META[platform]?.label ?? platform}.`,
      });
      queryClient.invalidateQueries({ queryKey: ["platforms", "connections"] });
    },
    onError: (err) => {
      setBusy(null);
      if (err instanceof ApiError && err.status === 403) {
        setBanner({
          tone: "error",
          text: "Disconnecting a platform requires admin or owner permissions.",
        });
      } else {
        setBanner({
          tone: "error",
          text: err instanceof Error ? err.message : "Failed to disconnect.",
        });
      }
    },
  });

  const platforms = availableQuery.data?.platforms ?? [];
  const connectedCount = connectionsQuery.data?.connections.filter((c) => c.is_active).length ?? 0;
  const isLoading = availableQuery.isLoading || connectionsQuery.isLoading;
  const isError = availableQuery.isError || connectionsQuery.isError;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Platforms</h1>
          <p className="text-sm text-zinc-500">
            Connect the ad and social platforms OrchestraAI should orchestrate.
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-1.5 text-xs text-zinc-400">
          <Plug className="h-3.5 w-3.5 text-emerald-400" />
          <span className="font-medium text-zinc-200">{connectedCount}</span>
          <span>of {platforms.length} connected</span>
        </div>
      </div>

      {banner && (
        <div
          className={cn(
            "flex items-start gap-2 rounded-lg border px-3 py-2 text-xs",
            banner.tone === "success"
              ? "border-emerald-800/40 bg-emerald-950/30 text-emerald-300"
              : "border-red-800/40 bg-red-950/30 text-red-300",
          )}
        >
          {banner.tone === "success" ? (
            <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          ) : (
            <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          )}
          <div className="flex-1">
            <p>{banner.text}</p>
            {banner.href && (
              <a
                href={banner.href}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-1 inline-flex items-center gap-1 text-emerald-400 underline-offset-2 hover:underline"
              >
                Open auth window manually
                <ExternalLink className="h-3 w-3" />
              </a>
            )}
          </div>
          <button
            onClick={() => setBanner(null)}
            className="text-zinc-500 hover:text-zinc-300"
            aria-label="Dismiss"
          >
            ✕
          </button>
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-6 w-6 animate-spin text-indigo-400" />
        </div>
      ) : isError ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <AlertCircle className="h-8 w-8 text-red-400" />
            <p className="mt-3 text-sm text-red-400">
              Failed to load platforms. Please try again.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {platforms.map((p) => (
            <PlatformCard
              key={p.platform}
              platform={p}
              connection={connectionByPlatform.get(p.platform) ?? null}
              onConnect={(key) => connectMutation.mutate(key)}
              onDisconnect={(key) => disconnectMutation.mutate(key)}
              busy={busy}
            />
          ))}
        </div>
      )}

      <Card>
        <CardContent className="flex items-start gap-3 py-5">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-indigo-600/15 text-indigo-400">
            <Shield className="h-4 w-4" />
          </div>
          <div className="text-sm leading-relaxed">
            <p className="font-medium text-zinc-200">Tokens stay encrypted at rest.</p>
            <p className="mt-1 text-xs text-zinc-500">
              Platform OAuth access tokens are stored with AES-256-GCM (Fernet
              fallback), scoped per tenant, and can be revoked at any time by
              disconnecting. Disconnects require admin or owner permissions — see{" "}
              <Link
                href="/settings"
                className="text-indigo-400 hover:text-indigo-300"
              >
                Settings
              </Link>{" "}
              to review your role.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
