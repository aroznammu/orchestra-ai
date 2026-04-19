"use client";

import { Card, CardContent } from "@/components/ui/card";
import {
  activateKillSwitch,
  ApiError,
  deactivateKillSwitch,
  getKillSwitchHistory,
  getKillSwitchStatus,
  type KillSwitchEvent,
} from "@/lib/apiClient";
import { cn } from "@/lib/utils";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Globe,
  History,
  Loader2,
  Power,
  Shield,
  ShieldAlert,
  ShieldCheck,
  User,
} from "lucide-react";
import { type FormEvent, useState } from "react";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatTimestamp(iso: string): string {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function eventTone(action: string): { label: string; className: string } {
  const a = action.toLowerCase();
  if (a.includes("activate") && !a.includes("deactivate")) {
    return {
      label: "Activated",
      className: "border-red-700/50 bg-red-950/40 text-red-300",
    };
  }
  if (a.includes("deactivate")) {
    return {
      label: "Deactivated",
      className: "border-emerald-700/50 bg-emerald-950/40 text-emerald-300",
    };
  }
  return {
    label: action,
    className: "border-zinc-700/50 bg-zinc-900/60 text-zinc-300",
  };
}

// ---------------------------------------------------------------------------
// Confirmation modal
// ---------------------------------------------------------------------------

function ActivateModal({
  onClose,
  onSubmit,
  submitting,
}: {
  onClose: () => void;
  onSubmit: (reason: string) => Promise<void>;
  submitting: boolean;
}) {
  const [reason, setReason] = useState("");
  const [acknowledged, setAcknowledged] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = reason.trim().length >= 5 && acknowledged && !submitting;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    setError(null);
    try {
      await onSubmit(reason.trim());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to activate.");
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-950/80 backdrop-blur-sm">
      <div className="mx-4 w-full max-w-lg rounded-2xl border border-red-500/40 bg-zinc-900 p-6 shadow-2xl shadow-red-500/10">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-red-600/20">
            <ShieldAlert className="h-5 w-5 text-red-400" />
          </div>
          <div className="flex-1">
            <h2 className="text-lg font-bold text-zinc-100">
              Activate Kill Switch?
            </h2>
            <p className="mt-1 text-sm text-zinc-400">
              This will immediately halt all ad spend across every connected
              platform for your tenant. Running campaigns will be paused at the
              bidder level.
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-zinc-400">
              Reason (required, min 5 characters)
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g. Anomalous spend detected on Google Ads; investigating."
              rows={3}
              required
              minLength={5}
              className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500"
            />
          </div>

          <label className="flex cursor-pointer items-start gap-2 rounded-lg border border-zinc-800 bg-zinc-950/40 px-3 py-2.5 text-xs text-zinc-300">
            <input
              type="checkbox"
              checked={acknowledged}
              onChange={(e) => setAcknowledged(e.target.checked)}
              className="mt-0.5 accent-red-500"
            />
            <span>
              I understand that active campaigns will stop bidding on every
              connected platform until the kill switch is deactivated.
            </span>
          </label>

          {error && (
            <div className="flex items-center gap-2 rounded-lg border border-red-800/40 bg-red-950/30 px-3 py-2 text-xs text-red-400">
              <AlertCircle className="h-3.5 w-3.5 shrink-0" />
              {error}
            </div>
          )}

          <div className="flex justify-end gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-300 transition-colors hover:bg-zinc-800 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!canSubmit}
              className="flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-red-500 disabled:opacity-50"
            >
              {submitting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Power className="h-4 w-4" />
              )}
              Activate Kill Switch
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Event history row
// ---------------------------------------------------------------------------

function EventRow({ event }: { event: KillSwitchEvent }) {
  const tone = eventTone(event.action);
  const isGlobal = event.tenant_id === "GLOBAL";

  return (
    <div className="flex flex-col gap-2 border-b border-zinc-800/60 px-5 py-4 last:border-b-0 sm:flex-row sm:items-start sm:justify-between">
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span
            className={cn(
              "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider",
              tone.className,
            )}
          >
            {tone.label}
          </span>
          {isGlobal && (
            <span className="inline-flex items-center gap-1 rounded-full border border-amber-700/50 bg-amber-950/40 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-amber-300">
              <Globe className="h-3 w-3" /> Global
            </span>
          )}
        </div>
        <p className="mt-1.5 text-sm text-zinc-200">{event.reason}</p>
        <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-zinc-500">
          <span className="inline-flex items-center gap-1">
            <User className="h-3 w-3" /> {event.triggered_by}
          </span>
          <span className="inline-flex items-center gap-1">
            <Clock className="h-3 w-3" /> {formatTimestamp(event.timestamp)}
          </span>
          {event.affected_platforms.length > 0 && (
            <span>
              {event.affected_platforms.length} platform
              {event.affected_platforms.length === 1 ? "" : "s"}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function KillSwitchPage() {
  const queryClient = useQueryClient();
  const [showActivate, setShowActivate] = useState(false);
  const [banner, setBanner] = useState<{
    tone: "success" | "error";
    text: string;
  } | null>(null);

  const statusQuery = useQuery({
    queryKey: ["kill-switch", "status"],
    queryFn: getKillSwitchStatus,
    refetchInterval: 15_000,
  });

  const historyQuery = useQuery({
    queryKey: ["kill-switch", "history"],
    queryFn: getKillSwitchHistory,
    staleTime: 30_000,
  });

  const activateMutation = useMutation({
    mutationFn: activateKillSwitch,
    onSuccess: () => {
      setShowActivate(false);
      setBanner({
        tone: "success",
        text: "Kill switch activated. All spend has been halted for your tenant.",
      });
      queryClient.invalidateQueries({ queryKey: ["kill-switch"] });
    },
    onError: (err) => {
      if (err instanceof ApiError && err.status === 403) {
        setBanner({
          tone: "error",
          text: "Activating the kill switch requires the owner role.",
        });
      } else {
        setBanner({
          tone: "error",
          text: err instanceof Error ? err.message : "Activation failed.",
        });
      }
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: deactivateKillSwitch,
    onSuccess: () => {
      setBanner({
        tone: "success",
        text: "Kill switch deactivated. Spend can resume.",
      });
      queryClient.invalidateQueries({ queryKey: ["kill-switch"] });
    },
    onError: (err) => {
      if (err instanceof ApiError && err.status === 403) {
        setBanner({
          tone: "error",
          text: "Deactivating the kill switch requires the owner role.",
        });
      } else {
        setBanner({
          tone: "error",
          text: err instanceof Error ? err.message : "Deactivation failed.",
        });
      }
    },
  });

  const status = statusQuery.data;
  const tenantActive = status?.tenant_active ?? false;
  const globalActive = status?.global_active ?? false;
  const isAffected = status?.is_affected ?? false;
  const events = historyQuery.data ?? [];

  const stateHeadline = !status
    ? "Checking status…"
    : isAffected
      ? globalActive
        ? "Global kill switch is active"
        : "Your tenant kill switch is active"
      : "All systems operating normally";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Kill Switch</h1>
        <p className="text-sm text-zinc-500">
          Emergency halt for all ad spend across every connected platform.
        </p>
      </div>

      {banner && (
        <div
          className={cn(
            "flex items-start justify-between gap-3 rounded-lg border px-3 py-2 text-xs",
            banner.tone === "success"
              ? "border-emerald-800/40 bg-emerald-950/30 text-emerald-300"
              : "border-red-800/40 bg-red-950/30 text-red-300",
          )}
        >
          <div className="flex items-start gap-2">
            {banner.tone === "success" ? (
              <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            ) : (
              <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            )}
            <span>{banner.text}</span>
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

      <Card
        className={cn(
          "border-2 transition-colors",
          isAffected
            ? "border-red-500/50 bg-gradient-to-br from-red-950/40 to-zinc-900"
            : "border-emerald-500/40 bg-gradient-to-br from-emerald-950/20 to-zinc-900",
        )}
      >
        <CardContent className="flex flex-col gap-5 py-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <div
              className={cn(
                "flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl",
                isAffected
                  ? "bg-red-600/20 text-red-400"
                  : "bg-emerald-600/15 text-emerald-400",
              )}
            >
              {isAffected ? (
                <ShieldAlert className="h-7 w-7" />
              ) : (
                <ShieldCheck className="h-7 w-7" />
              )}
            </div>
            <div>
              <p
                className={cn(
                  "text-xs font-semibold uppercase tracking-wider",
                  isAffected ? "text-red-400" : "text-emerald-400",
                )}
              >
                {isAffected ? "HALTED" : "ACTIVE"}
              </p>
              <h2 className="text-lg font-bold text-zinc-100">
                {stateHeadline}
              </h2>
              <p className="mt-1 text-xs text-zinc-500">
                {globalActive
                  ? "A global halt is in effect; contact platform admins to lift it."
                  : tenantActive
                    ? "Spend will stay paused until you deactivate below."
                    : "All tenant campaigns can bid normally."}
              </p>
            </div>
          </div>

          <div className="flex shrink-0 items-center gap-2">
            {tenantActive ? (
              <button
                onClick={() => deactivateMutation.mutate()}
                disabled={deactivateMutation.isPending || globalActive}
                title={
                  globalActive
                    ? "A global halt is in effect and cannot be lifted here."
                    : undefined
                }
                className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-emerald-900/30 transition-colors hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {deactivateMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <ShieldCheck className="h-4 w-4" />
                )}
                Deactivate
              </button>
            ) : (
              <button
                onClick={() => setShowActivate(true)}
                disabled={globalActive}
                title={
                  globalActive
                    ? "A global halt is already in effect for this environment."
                    : undefined
                }
                className="flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-red-900/30 transition-colors hover:bg-red-500 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <Power className="h-4 w-4" />
                Activate Kill Switch
              </button>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="flex items-start gap-3 py-5">
            <Globe className="h-5 w-5 shrink-0 text-zinc-500" />
            <div>
              <p className="text-xs uppercase tracking-wider text-zinc-500">
                Global
              </p>
              <p className="mt-0.5 text-sm font-semibold text-zinc-200">
                {globalActive ? "Active" : "Inactive"}
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-start gap-3 py-5">
            <Shield className="h-5 w-5 shrink-0 text-zinc-500" />
            <div>
              <p className="text-xs uppercase tracking-wider text-zinc-500">
                Tenant
              </p>
              <p className="mt-0.5 text-sm font-semibold text-zinc-200">
                {tenantActive ? "Active" : "Inactive"}
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-start gap-3 py-5">
            <AlertTriangle className="h-5 w-5 shrink-0 text-zinc-500" />
            <div>
              <p className="text-xs uppercase tracking-wider text-zinc-500">
                Spend impact
              </p>
              <p className="mt-0.5 text-sm font-semibold text-zinc-200">
                {isAffected ? "Halted" : "Flowing"}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      <div>
        <div className="mb-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <History className="h-4 w-4 text-zinc-500" />
            <h2 className="text-sm font-semibold text-zinc-200">
              Event history
            </h2>
          </div>
          <p className="text-[11px] text-zinc-500">
            {events.length} event{events.length === 1 ? "" : "s"}
          </p>
        </div>

        {historyQuery.isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-5 w-5 animate-spin text-indigo-400" />
          </div>
        ) : historyQuery.isError ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-10">
              <AlertCircle className="h-6 w-6 text-red-400" />
              <p className="mt-3 text-sm text-red-400">
                Failed to load event history.
              </p>
            </CardContent>
          </Card>
        ) : events.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-10 text-center">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-zinc-800">
                <ShieldCheck className="h-5 w-5 text-zinc-500" />
              </div>
              <p className="mt-3 text-sm font-medium text-zinc-300">
                No kill switch events recorded
              </p>
              <p className="mt-1 max-w-sm text-xs text-zinc-500">
                Activations and deactivations will appear here, along with the
                reason, the user who triggered them, and a timestamp.
              </p>
            </CardContent>
          </Card>
        ) : (
          <Card>
            {events.map((e) => (
              <EventRow key={e.id} event={e} />
            ))}
          </Card>
        )}
      </div>

      {showActivate && (
        <ActivateModal
          onClose={() => setShowActivate(false)}
          onSubmit={async (reason) => {
            await activateMutation.mutateAsync(reason);
          }}
          submitting={activateMutation.isPending}
        />
      )}
    </div>
  );
}
