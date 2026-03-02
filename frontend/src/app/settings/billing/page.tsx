"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ApiError,
  createCheckout,
  createPortalSession,
  getPlans,
  getSubscriptionStatus,
  type PlanInfo,
  type SubscriptionStatus,
} from "@/lib/apiClient";
import { cn } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";
import {
  CheckCircle2,
  CreditCard,
  ExternalLink,
  Loader2,
  Sparkles,
  Zap,
} from "lucide-react";
import { useSearchParams } from "next/navigation";
import { Suspense, useCallback, useState } from "react";

const PLAN_ACCENT: Record<string, { border: string; bg: string; badge: string }> = {
  starter: {
    border: "border-indigo-500/50",
    bg: "bg-indigo-500/5",
    badge: "bg-indigo-500/20 text-indigo-300",
  },
  agency: {
    border: "border-amber-500/50",
    bg: "bg-amber-500/5",
    badge: "bg-amber-500/20 text-amber-300",
  },
};

function StatusBanner({ status }: { status: string | null }) {
  if (status === "success") {
    return (
      <div className="mb-6 flex items-center gap-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-300">
        <CheckCircle2 className="h-4 w-4" />
        Subscription activated successfully!
      </div>
    );
  }
  if (status === "cancelled") {
    return (
      <div className="mb-6 flex items-center gap-2 rounded-lg border border-zinc-700 bg-zinc-800/50 px-4 py-3 text-sm text-zinc-400">
        Checkout was cancelled. You can try again anytime.
      </div>
    );
  }
  return null;
}

function PlanCard({
  plan,
  currentPlan,
  isActive,
  onSubscribe,
  isLoading,
}: {
  plan: PlanInfo;
  currentPlan: string;
  isActive: boolean;
  onSubscribe: (plan: string) => void;
  isLoading: boolean;
}) {
  const accent = PLAN_ACCENT[plan.key] ?? PLAN_ACCENT.starter;
  const isCurrent = plan.key === currentPlan && isActive;

  return (
    <Card className={cn("relative overflow-hidden transition-all", accent.border, accent.bg)}>
      {plan.key === "agency" && (
        <div className="absolute right-4 top-4">
          <span className="flex items-center gap-1 rounded-full bg-amber-500/20 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-amber-300">
            <Sparkles className="h-3 w-3" /> Popular
          </span>
        </div>
      )}

      <CardHeader>
        <CardTitle className="text-lg">{plan.name}</CardTitle>
        <div className="mt-2 flex items-baseline gap-1">
          <span className="text-3xl font-bold text-zinc-100">
            ${(plan.price_monthly / 100).toFixed(0)}
          </span>
          <span className="text-sm text-zinc-500">/month</span>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <ul className="space-y-2">
          {plan.features.map((f) => (
            <li key={f} className="flex items-start gap-2 text-sm text-zinc-300">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
              {f}
            </li>
          ))}
        </ul>

        {isCurrent ? (
          <div className="flex items-center justify-center gap-2 rounded-lg bg-emerald-500/20 py-2.5 text-sm font-medium text-emerald-300">
            <CheckCircle2 className="h-4 w-4" /> Current Plan
          </div>
        ) : (
          <button
            onClick={() => onSubscribe(plan.key)}
            disabled={isLoading}
            className={cn(
              "flex w-full items-center justify-center gap-2 rounded-lg py-2.5 text-sm font-semibold transition-colors",
              plan.key === "agency"
                ? "bg-amber-500 text-zinc-950 hover:bg-amber-400"
                : "bg-indigo-600 text-white hover:bg-indigo-500",
              "disabled:opacity-50",
            )}
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Zap className="h-4 w-4" />
            )}
            Subscribe
          </button>
        )}
      </CardContent>
    </Card>
  );
}

export default function BillingPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-6 w-6 animate-spin text-indigo-400" />
        </div>
      }
    >
      <BillingContent />
    </Suspense>
  );
}

function BillingContent() {
  const searchParams = useSearchParams();
  const checkoutStatus = searchParams.get("status");
  const [loading, setLoading] = useState<string | null>(null);

  const plansQuery = useQuery({
    queryKey: ["billing-plans"],
    queryFn: getPlans,
  });
  const subQuery = useQuery({
    queryKey: ["billing-status"],
    queryFn: getSubscriptionStatus,
    refetchInterval: checkoutStatus === "success" ? 3000 : false,
  });

  const plans = plansQuery.data?.plans ?? [];
  const subscription: SubscriptionStatus | undefined = subQuery.data;

  const isActive =
    subscription?.status === "active" || subscription?.status === "trialing";

  const handleSubscribe = useCallback(
    async (plan: string) => {
      setLoading(plan);
      try {
        const { url } = await createCheckout(plan);
        window.location.href = url;
      } catch (err) {
        if (err instanceof ApiError) {
          alert(err.message);
        }
      } finally {
        setLoading(null);
      }
    },
    [],
  );

  const handlePortal = useCallback(async () => {
    setLoading("portal");
    try {
      const { url } = await createPortalSession();
      window.location.href = url;
    } catch (err) {
      if (err instanceof ApiError) {
        alert(err.message);
      }
    } finally {
      setLoading(null);
    }
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Billing & Plans</h1>
        <p className="text-sm text-zinc-500">
          Choose a plan to unlock AI orchestration, advanced analytics, and
          premium platform integrations.
        </p>
      </div>

      <StatusBanner status={checkoutStatus} />

      {subscription && (
        <Card>
          <CardContent className="flex flex-wrap items-center justify-between gap-4 py-4">
            <div className="flex items-center gap-3">
              <CreditCard className="h-5 w-5 text-zinc-400" />
              <div>
                <p className="text-sm font-medium text-zinc-200">
                  Current plan:{" "}
                  <span className="capitalize text-indigo-400">
                    {subscription.plan}
                  </span>
                </p>
                <p className="text-xs text-zinc-500">
                  Status:{" "}
                  <span
                    className={cn(
                      "capitalize",
                      isActive ? "text-emerald-400" : "text-red-400",
                    )}
                  >
                    {subscription.status}
                  </span>
                </p>
              </div>
            </div>

            {subscription.has_subscription && (
              <button
                onClick={handlePortal}
                disabled={loading === "portal"}
                className="flex items-center gap-2 rounded-lg border border-zinc-700 bg-zinc-800 px-4 py-2 text-sm font-medium text-zinc-200 transition-colors hover:bg-zinc-700 disabled:opacity-50"
              >
                {loading === "portal" ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <ExternalLink className="h-4 w-4" />
                )}
                Manage Subscription
              </button>
            )}
          </CardContent>
        </Card>
      )}

      {plansQuery.isLoading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-6 w-6 animate-spin text-indigo-400" />
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2">
          {plans.map((plan) => (
            <PlanCard
              key={plan.key}
              plan={plan}
              currentPlan={subscription?.plan ?? "free"}
              isActive={isActive}
              onSubscribe={handleSubscribe}
              isLoading={loading === plan.key}
            />
          ))}
        </div>
      )}
    </div>
  );
}
