"use client";

import { Card, CardContent } from "@/components/ui/card";
import {
  ApiError,
  createCampaign,
  launchCampaign,
  listCampaigns,
  pauseCampaign,
  type CampaignCreatePayload,
  type CampaignResponse,
} from "@/lib/apiClient";
import { cn } from "@/lib/utils";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  Loader2,
  Megaphone,
  Pause,
  Play,
  Plus,
  Sparkles,
  X,
  Zap,
} from "lucide-react";
import Link from "next/link";
import { type FormEvent, useCallback, useState } from "react";

const STATUS_STYLES: Record<string, { dot: string; text: string }> = {
  draft: { dot: "bg-zinc-500", text: "text-zinc-400" },
  scheduled: { dot: "bg-blue-500", text: "text-blue-400" },
  active: { dot: "bg-emerald-500", text: "text-emerald-400" },
  paused: { dot: "bg-amber-500", text: "text-amber-400" },
  completed: { dot: "bg-indigo-500", text: "text-indigo-400" },
  failed: { dot: "bg-red-500", text: "text-red-400" },
};

function StatusBadge({ status }: { status: string }) {
  const style = STATUS_STYLES[status] ?? STATUS_STYLES.draft;
  return (
    <span className={cn("flex items-center gap-1.5 text-xs font-medium capitalize", style.text)}>
      <span className={cn("h-1.5 w-1.5 rounded-full", style.dot)} />
      {status}
    </span>
  );
}

function CampaignRow({
  campaign,
  onLaunch,
  onPause,
  actionLoading,
}: {
  campaign: CampaignResponse;
  onLaunch: (id: string) => void;
  onPause: (id: string) => void;
  actionLoading: string | null;
}) {
  const isLoading = actionLoading === campaign.id;
  const canLaunch = campaign.status === "draft" || campaign.status === "paused";
  const canPause = campaign.status === "active";

  return (
    <div className="flex items-center justify-between border-b border-zinc-800/60 px-5 py-4 last:border-b-0">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-3">
          <p className="truncate text-sm font-medium text-zinc-200">{campaign.name}</p>
          <StatusBadge status={campaign.status} />
        </div>
        {campaign.description && (
          <p className="mt-0.5 truncate text-xs text-zinc-500">{campaign.description}</p>
        )}
        <div className="mt-1.5 flex items-center gap-4 text-[11px] text-zinc-500">
          <span>Budget: ${campaign.budget.toLocaleString()}</span>
          <span>Spent: ${campaign.spent.toLocaleString()}</span>
          {campaign.platforms.length > 0 && (
            <span>{campaign.platforms.join(", ")}</span>
          )}
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {new Date(campaign.created_at).toLocaleDateString()}
          </span>
        </div>
      </div>

      <div className="ml-4 flex shrink-0 items-center gap-2">
        {canLaunch && (
          <button
            onClick={() => onLaunch(campaign.id)}
            disabled={isLoading}
            className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-emerald-500 disabled:opacity-50"
          >
            {isLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Play className="h-3 w-3" />}
            Launch
          </button>
        )}
        {canPause && (
          <button
            onClick={() => onPause(campaign.id)}
            disabled={isLoading}
            className="flex items-center gap-1.5 rounded-lg bg-amber-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-amber-500 disabled:opacity-50"
          >
            {isLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Pause className="h-3 w-3" />}
            Pause
          </button>
        )}
      </div>
    </div>
  );
}

function CreateCampaignModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [budget, setBudget] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [show402, setShow402] = useState(false);

  const handleSubmit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault();
      if (!name.trim()) return;
      setLoading(true);
      setError(null);

      const payload: CampaignCreatePayload = {
        name: name.trim(),
        description: description.trim() || undefined,
        budget: budget ? parseFloat(budget) : 0,
      };

      try {
        await createCampaign(payload);
        onCreated();
        onClose();
      } catch (err) {
        if (err instanceof ApiError && err.status === 402) {
          setShow402(true);
        } else {
          setError(err instanceof Error ? err.message : "Failed to create campaign");
        }
      } finally {
        setLoading(false);
      }
    },
    [name, description, budget, onCreated, onClose],
  );

  if (show402) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-950/80 backdrop-blur-sm">
        <div className="mx-4 max-w-md rounded-2xl border border-indigo-500/30 bg-zinc-900 p-8 text-center shadow-2xl shadow-indigo-500/10">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-600/20">
            <Sparkles className="h-8 w-8 text-indigo-400" />
          </div>
          <h2 className="mt-5 text-xl font-bold text-zinc-100">
            Upgrade to Enterprise Cloud
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-zinc-400">
            Creating campaigns requires an active subscription. Upgrade to the
            Starter or Agency plan to unlock campaign management and AI
            orchestration.
          </p>
          <div className="mt-6 flex flex-col gap-3">
            <Link
              href="/settings/billing"
              className="flex items-center justify-center gap-2 rounded-lg bg-indigo-600 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-500"
            >
              <Zap className="h-4 w-4" />
              View Plans & Upgrade
            </Link>
            <button
              onClick={onClose}
              className="text-sm text-zinc-500 transition-colors hover:text-zinc-300"
            >
              Maybe later
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-950/80 backdrop-blur-sm">
      <div className="mx-4 w-full max-w-lg rounded-2xl border border-zinc-800 bg-zinc-900 p-6 shadow-2xl">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-zinc-100">New Campaign</h2>
          <button onClick={onClose} className="text-zinc-500 hover:text-zinc-300">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-zinc-400">
              Campaign Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Summer Product Launch"
              required
              className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-zinc-400">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description of your campaign goals..."
              rows={3}
              className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-zinc-400">
              Budget ($)
            </label>
            <input
              type="number"
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
              placeholder="0.00"
              min="0"
              step="0.01"
              className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          {error && (
            <div className="flex items-center gap-2 rounded-lg border border-red-800/40 bg-red-950/30 px-3 py-2 text-xs text-red-400">
              <AlertCircle className="h-3.5 w-3.5 shrink-0" />
              {error}
            </div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-300 transition-colors hover:bg-zinc-800"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !name.trim()}
              className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-indigo-500 disabled:opacity-50"
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
              Create Campaign
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function PaywallOverlay({ onDismiss }: { onDismiss: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-950/80 backdrop-blur-sm">
      <div className="mx-4 max-w-md rounded-2xl border border-indigo-500/30 bg-zinc-900 p-8 text-center shadow-2xl shadow-indigo-500/10">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-600/20">
          <Sparkles className="h-8 w-8 text-indigo-400" />
        </div>
        <h2 className="mt-5 text-xl font-bold text-zinc-100">
          Upgrade to Enterprise Cloud
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-zinc-400">
          This action requires an active subscription. Upgrade to the Starter or
          Agency plan to manage campaigns with AI-powered orchestration.
        </p>
        <div className="mt-6 flex flex-col gap-3">
          <Link
            href="/settings/billing"
            className="flex items-center justify-center gap-2 rounded-lg bg-indigo-600 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-500"
          >
            <Zap className="h-4 w-4" />
            View Plans & Upgrade
          </Link>
          <button
            onClick={onDismiss}
            className="text-sm text-zinc-500 transition-colors hover:text-zinc-300"
          >
            Maybe later
          </button>
        </div>
      </div>
    </div>
  );
}

export default function CampaignsPage() {
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [showPaywall, setShowPaywall] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const campaignsQuery = useQuery({
    queryKey: ["campaigns"],
    queryFn: listCampaigns,
  });

  const campaigns = campaignsQuery.data?.campaigns ?? [];

  const handleAction = useCallback(
    async (action: (id: string) => Promise<CampaignResponse>, id: string) => {
      setActionLoading(id);
      try {
        await action(id);
        queryClient.invalidateQueries({ queryKey: ["campaigns"] });
      } catch (err) {
        if (err instanceof ApiError && err.status === 402) {
          setShowPaywall(true);
        } else {
          alert(err instanceof Error ? err.message : "Action failed");
        }
      } finally {
        setActionLoading(null);
      }
    },
    [queryClient],
  );

  const isEmpty = !campaignsQuery.isLoading && campaigns.length === 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Campaigns</h1>
          <p className="text-sm text-zinc-500">
            Manage your cross-platform marketing campaigns
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-indigo-500"
        >
          <Plus className="h-4 w-4" />
          New Campaign
        </button>
      </div>

      {campaignsQuery.isLoading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-6 w-6 animate-spin text-indigo-400" />
        </div>
      ) : campaignsQuery.isError ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <AlertCircle className="h-8 w-8 text-red-400" />
            <p className="mt-3 text-sm text-red-400">
              Failed to load campaigns. Please try again.
            </p>
          </CardContent>
        </Card>
      ) : isEmpty ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-20">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-zinc-800">
              <Megaphone className="h-7 w-7 text-zinc-500" />
            </div>
            <h2 className="mt-4 text-lg font-semibold text-zinc-300">
              No campaigns yet
            </h2>
            <p className="mt-2 max-w-sm text-center text-sm text-zinc-500">
              Create your first campaign to get started with AI-powered
              cross-platform marketing.
            </p>
            <button
              onClick={() => setShowCreate(true)}
              className="mt-5 flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-indigo-500"
            >
              <Plus className="h-4 w-4" />
              Create Campaign
            </button>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <div className="flex items-center justify-between border-b border-zinc-800/60 px-5 py-3">
            <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
              {campaigns.length} campaign{campaigns.length !== 1 ? "s" : ""}
            </p>
            <div className="flex items-center gap-1.5 text-xs text-zinc-600">
              <CheckCircle2 className="h-3 w-3" />
              {campaigns.filter((c) => c.status === "active").length} active
            </div>
          </div>
          {campaigns.map((c) => (
            <CampaignRow
              key={c.id}
              campaign={c}
              onLaunch={(id) => handleAction(launchCampaign, id)}
              onPause={(id) => handleAction(pauseCampaign, id)}
              actionLoading={actionLoading}
            />
          ))}
        </Card>
      )}

      {showCreate && (
        <CreateCampaignModal
          onClose={() => setShowCreate(false)}
          onCreated={() => queryClient.invalidateQueries({ queryKey: ["campaigns"] })}
        />
      )}

      {showPaywall && <PaywallOverlay onDismiss={() => setShowPaywall(false)} />}
    </div>
  );
}
