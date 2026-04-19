"use client";

import { Card, CardContent } from "@/components/ui/card";
import {
  ApiError,
  type APIKey,
  type APIKeyCreateResponse,
  type APIKeyRole,
  type CreateAPIKeyPayload,
  createAPIKey,
  listAPIKeys,
  revokeAPIKey,
} from "@/lib/apiClient";
import { cn } from "@/lib/utils";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  Copy,
  KeyRound,
  Loader2,
  Plus,
  ShieldAlert,
  Trash2,
} from "lucide-react";
import Link from "next/link";
import { type FormEvent, useMemo, useState } from "react";

const ROLE_OPTIONS: { value: APIKeyRole; label: string; hint: string }[] = [
  {
    value: "viewer",
    label: "Viewer",
    hint: "Read-only: analytics, campaigns, dashboards.",
  },
  {
    value: "member",
    label: "Member",
    hint: "Can publish campaigns and run the orchestrator.",
  },
  {
    value: "admin",
    label: "Admin",
    hint: "Full tenant-level management. Cannot trigger kill-switch.",
  },
];

const EXPIRY_OPTIONS: { value: number | null; label: string }[] = [
  { value: 30, label: "30 days" },
  { value: 90, label: "90 days" },
  { value: 365, label: "1 year" },
  { value: null, label: "Never expires" },
];

function formatDate(iso: string | null): string {
  if (!iso) return "Never";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function maskKey(prefix: string): string {
  return `${prefix}${"•".repeat(28)}`;
}

function RoleBadge({ role }: { role: string }) {
  const palette: Record<string, string> = {
    owner: "bg-amber-500/20 text-amber-300 border-amber-500/40",
    admin: "bg-indigo-500/20 text-indigo-300 border-indigo-500/40",
    member: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
    viewer: "bg-zinc-700/50 text-zinc-300 border-zinc-600/60",
  };
  const cls = palette[role] ?? palette.viewer;
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium capitalize",
        cls,
      )}
    >
      {role}
    </span>
  );
}

function CreatedKeyCallout({
  created,
  onDismiss,
}: {
  created: APIKeyCreateResponse;
  onDismiss: () => void;
}) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(created.key);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard may be blocked; user can still select the value.
    }
  }

  return (
    <Card className="border-emerald-500/40 bg-emerald-500/5">
      <CardContent className="space-y-3 py-5">
        <div className="flex items-start gap-2">
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
          <div className="space-y-1">
            <p className="text-sm font-semibold text-emerald-200">
              Key created — copy it now.
            </p>
            <p className="text-xs text-emerald-200/80">
              This is the only time the full key will be shown. Store it in a
              secret manager; you will not be able to retrieve it again.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 rounded-lg border border-emerald-500/30 bg-zinc-950/70 px-3 py-2 font-mono text-xs text-emerald-100">
          <code className="flex-1 truncate">{created.key}</code>
          <button
            onClick={copy}
            type="button"
            className="flex items-center gap-1 rounded-md border border-emerald-500/40 bg-emerald-500/10 px-2 py-1 text-[11px] font-semibold text-emerald-200 hover:bg-emerald-500/20"
          >
            <Copy className="h-3 w-3" />
            {copied ? "Copied" : "Copy"}
          </button>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-emerald-200/70">
          <span>
            Use header{" "}
            <code className="rounded bg-zinc-800 px-1 py-0.5">X-API-Key</code>{" "}
            when calling the API.
          </span>
          <button
            onClick={onDismiss}
            type="button"
            className="rounded-md border border-emerald-500/40 px-2 py-1 font-semibold text-emerald-200 hover:bg-emerald-500/10"
          >
            I&apos;ve saved it
          </button>
        </div>
      </CardContent>
    </Card>
  );
}

function CreateKeyForm({
  onCreated,
}: {
  onCreated: (created: APIKeyCreateResponse) => void;
}) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [role, setRole] = useState<APIKeyRole>("member");
  const [expiresInDays, setExpiresInDays] = useState<number | null>(90);
  const [error, setError] = useState<string | null>(null);

  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (payload: CreateAPIKeyPayload) => createAPIKey(payload),
    onSuccess: (created) => {
      onCreated(created);
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
      setName("");
      setRole("member");
      setExpiresInDays(90);
      setOpen(false);
      setError(null);
    },
    onError: (err: unknown) => {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Failed to create key.",
      );
    },
  });

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!name.trim()) {
      setError("Name is required.");
      return;
    }
    mutation.mutate({
      name: name.trim(),
      role,
      expires_in_days: expiresInDays,
    });
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        type="button"
        className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-indigo-500"
      >
        <Plus className="h-4 w-4" />
        New API key
      </button>
    );
  }

  return (
    <Card>
      <CardContent className="space-y-4 py-5">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-zinc-200">Create API key</h3>
          <button
            onClick={() => setOpen(false)}
            type="button"
            className="text-xs text-zinc-500 hover:text-zinc-300"
          >
            Cancel
          </button>
        </div>

        {error && (
          <div className="flex items-start gap-2 rounded-lg border border-red-800/50 bg-red-950/30 p-3 text-sm text-red-400">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-zinc-400">
              Name
            </label>
            <input
              type="text"
              required
              maxLength={255}
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="CI bot, analytics exporter, …"
              className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 outline-none transition-colors focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-zinc-400">
              Role
            </label>
            <div className="grid gap-2 sm:grid-cols-3">
              {ROLE_OPTIONS.map((opt) => (
                <label
                  key={opt.value}
                  className={cn(
                    "flex cursor-pointer flex-col gap-1 rounded-lg border px-3 py-2 text-xs transition-colors",
                    role === opt.value
                      ? "border-indigo-500/70 bg-indigo-500/10 text-indigo-200"
                      : "border-zinc-700 bg-zinc-800/60 text-zinc-300 hover:border-zinc-600",
                  )}
                >
                  <div className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="role"
                      value={opt.value}
                      checked={role === opt.value}
                      onChange={() => setRole(opt.value)}
                      className="accent-indigo-500"
                    />
                    <span className="font-semibold">{opt.label}</span>
                  </div>
                  <span className="text-[11px] text-zinc-500">{opt.hint}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-zinc-400">
              Expiration
            </label>
            <div className="flex flex-wrap gap-2">
              {EXPIRY_OPTIONS.map((opt) => (
                <button
                  key={opt.label}
                  type="button"
                  onClick={() => setExpiresInDays(opt.value)}
                  className={cn(
                    "rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors",
                    expiresInDays === opt.value
                      ? "border-indigo-500/70 bg-indigo-500/10 text-indigo-200"
                      : "border-zinc-700 bg-zinc-800/60 text-zinc-300 hover:border-zinc-600",
                  )}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-2">
            <button
              onClick={() => setOpen(false)}
              type="button"
              className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm font-medium text-zinc-300 hover:bg-zinc-700"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={mutation.isPending}
              className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-indigo-500 disabled:opacity-50"
            >
              {mutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Plus className="h-4 w-4" />
              )}
              Create key
            </button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

function KeyRow({
  row,
  onRevoke,
  isRevoking,
  highlightPrefix,
}: {
  row: APIKey;
  onRevoke: (id: string, name: string) => void;
  isRevoking: boolean;
  highlightPrefix: string | null;
}) {
  const expired =
    row.expires_at !== null && new Date(row.expires_at).getTime() < Date.now();
  const inactive = !row.is_active || expired;

  return (
    <Card
      className={cn(
        "transition-colors",
        inactive && "opacity-60",
        highlightPrefix && "border-emerald-500/40 bg-emerald-500/5",
      )}
    >
      <CardContent className="flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-zinc-800">
            <KeyRound className="h-4 w-4 text-zinc-400" />
          </div>
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-sm font-semibold text-zinc-200">{row.name}</p>
              <RoleBadge role={row.role} />
              {!row.is_active && (
                <span className="rounded bg-zinc-800 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-zinc-500">
                  Revoked
                </span>
              )}
              {row.is_active && expired && (
                <span className="rounded bg-red-900/40 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-red-300">
                  Expired
                </span>
              )}
            </div>
            <p className="font-mono text-xs text-zinc-500">
              {highlightPrefix ? maskKey(highlightPrefix) : "oa_" + "•".repeat(30)}
            </p>
            <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-zinc-500">
              <span>Created {formatDate(row.created_at)}</span>
              <span>Last used {formatDate(row.last_used_at)}</span>
              <span>Expires {formatDate(row.expires_at)}</span>
            </div>
          </div>
        </div>

        {row.is_active && (
          <button
            onClick={() => onRevoke(row.id, row.name)}
            disabled={isRevoking}
            type="button"
            className="inline-flex items-center gap-2 self-start rounded-lg border border-red-800/40 bg-red-950/40 px-3 py-1.5 text-xs font-semibold text-red-300 transition-colors hover:bg-red-900/40 disabled:opacity-50"
          >
            {isRevoking ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : (
              <Trash2 className="h-3 w-3" />
            )}
            Revoke
          </button>
        )}
      </CardContent>
    </Card>
  );
}

export default function APIKeysPage() {
  const queryClient = useQueryClient();
  const [createdKey, setCreatedKey] = useState<APIKeyCreateResponse | null>(
    null,
  );
  const [revokingId, setRevokingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data, isLoading, isError, error: queryError } = useQuery({
    queryKey: ["api-keys"],
    queryFn: listAPIKeys,
  });

  const forbidden =
    isError && queryError instanceof ApiError && queryError.status === 403;

  const revokeMutation = useMutation({
    mutationFn: (id: string) => revokeAPIKey(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
      setError(null);
    },
    onError: (err: unknown) => {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Failed to revoke key.",
      );
    },
    onSettled: () => setRevokingId(null),
  });

  const keys = useMemo<APIKey[]>(() => data?.keys ?? [], [data]);

  async function handleRevoke(id: string, name: string) {
    if (
      !window.confirm(
        `Revoke "${name}"? Any client using this key will start receiving 401 errors immediately.`,
      )
    ) {
      return;
    }
    setRevokingId(id);
    revokeMutation.mutate(id);
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Link
          href="/settings"
          className="inline-flex items-center gap-1 text-xs text-zinc-500 transition-colors hover:text-zinc-300"
        >
          <ArrowLeft className="h-3 w-3" />
          Back to Settings
        </Link>
        <h1 className="text-2xl font-bold tracking-tight">API Keys</h1>
        <p className="text-sm text-zinc-500">
          Issue scoped, revocable API keys for CI jobs, integrations, and
          programmatic access. Keys are hashed with SHA-256 before storage — we
          cannot recover them later.
        </p>
      </div>

      {forbidden && (
        <Card className="border-amber-500/30 bg-amber-500/5">
          <CardContent className="flex items-start gap-3 py-4">
            <ShieldAlert className="mt-0.5 h-5 w-5 text-amber-400" />
            <div className="space-y-1">
              <p className="text-sm font-semibold text-amber-200">
                Admin access required
              </p>
              <p className="text-xs text-amber-200/80">
                Only <span className="font-semibold">owners</span> and{" "}
                <span className="font-semibold">admins</span> can manage API
                keys. Ask a teammate with those privileges to issue a key for
                your workflow.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {error && !forbidden && (
        <div className="flex items-start gap-2 rounded-lg border border-red-800/50 bg-red-950/30 p-3 text-sm text-red-400">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {createdKey && (
        <CreatedKeyCallout
          created={createdKey}
          onDismiss={() => setCreatedKey(null)}
        />
      )}

      {!forbidden && (
        <div className="flex items-center justify-between">
          <p className="text-xs uppercase tracking-wider text-zinc-500">
            {keys.length} key{keys.length === 1 ? "" : "s"}
          </p>
          <CreateKeyForm onCreated={setCreatedKey} />
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-6 w-6 animate-spin text-indigo-400" />
        </div>
      ) : forbidden ? null : keys.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-10 text-center">
            <KeyRound className="h-8 w-8 text-zinc-600" />
            <p className="text-sm font-semibold text-zinc-300">
              No API keys yet
            </p>
            <p className="max-w-md text-xs text-zinc-500">
              Generate a key to pull analytics, trigger campaigns, or export
              reports from outside the dashboard. Each key inherits a role that
              you control.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {keys.map((row) => (
            <KeyRow
              key={row.id}
              row={row}
              onRevoke={handleRevoke}
              isRevoking={revokingId === row.id}
              highlightPrefix={
                createdKey && createdKey.id === row.id
                  ? createdKey.prefix
                  : null
              }
            />
          ))}
        </div>
      )}

      <Card>
        <CardContent className="space-y-2 py-5">
          <h3 className="text-sm font-semibold text-zinc-200">
            How to authenticate with your key
          </h3>
          <p className="text-xs text-zinc-500">
            Send the key in the <code className="rounded bg-zinc-800 px-1 py-0.5">X-API-Key</code>{" "}
            header, or as a bearer token in <code className="rounded bg-zinc-800 px-1 py-0.5">Authorization</code>.
          </p>
          <pre className="overflow-x-auto rounded-lg border border-zinc-800 bg-zinc-950/70 p-3 font-mono text-[11px] text-zinc-300">
{`curl https://api.orchestraai.dev/api/v1/analytics/overview \\
  -H "X-API-Key: oa_YOUR_KEY_HERE"`}
          </pre>
        </CardContent>
      </Card>
    </div>
  );
}
