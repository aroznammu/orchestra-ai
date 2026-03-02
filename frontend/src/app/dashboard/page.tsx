"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  get,
  type CampaignListResponse,
  type OverviewResponse,
  type PlatformMetrics,
} from "@/lib/apiClient";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  AlertCircle,
  DollarSign,
  type LucideIcon,
  Megaphone,
  TrendingUp,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

// ---------------------------------------------------------------------------
// Data fetching
// ---------------------------------------------------------------------------

function useOverview() {
  return useQuery<OverviewResponse>({
    queryKey: ["analytics", "overview"],
    queryFn: () => get<OverviewResponse>("/analytics/overview"),
    retry: 1,
    staleTime: 60_000,
  });
}

function useCampaigns() {
  return useQuery<CampaignListResponse>({
    queryKey: ["campaigns"],
    queryFn: () =>
      get<CampaignListResponse>("/campaigns", { status_filter: "active" }),
    retry: 1,
    staleTime: 60_000,
  });
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmt$(n: number): string {
  return n >= 1_000
    ? `$${(n / 1_000).toFixed(1)}k`
    : `$${n.toFixed(2)}`;
}

function fmtPct(n: number): string {
  return `${n.toFixed(1)}%`;
}

function avgRoi(platforms: Record<string, PlatformMetrics>): number {
  const entries = Object.values(platforms);
  if (entries.length === 0) return 0;
  return entries.reduce((sum, p) => sum + p.roi, 0) / entries.length;
}

interface MetricDef {
  label: string;
  value: string;
  icon: LucideIcon;
  color: string;
}

function buildMetrics(
  overview: OverviewResponse | undefined,
  activeCampaigns: number,
): MetricDef[] {
  const spend = overview?.total_spend ?? 0;
  const roi = overview ? avgRoi(overview.platforms) : 0;
  const engagement = overview?.average_engagement_rate ?? 0;

  return [
    {
      label: "Total Spend",
      value: fmt$(spend),
      icon: DollarSign,
      color: "text-emerald-400",
    },
    {
      label: "Average ROI",
      value: `${roi.toFixed(1)}x`,
      icon: TrendingUp,
      color: "text-indigo-400",
    },
    {
      label: "Active Campaigns",
      value: String(activeCampaigns),
      icon: Megaphone,
      color: "text-amber-400",
    },
    {
      label: "Engagement Rate",
      value: fmtPct(engagement),
      icon: Activity,
      color: "text-rose-400",
    },
  ];
}

function buildChartData(
  platforms: Record<string, PlatformMetrics>,
): { platform: string; impressions: number; clicks: number; spend: number }[] {
  return Object.entries(platforms).map(([name, m]) => ({
    platform: name.charAt(0).toUpperCase() + name.slice(1),
    impressions: m.impressions,
    clicks: m.clicks,
    spend: m.spend,
  }));
}

// ---------------------------------------------------------------------------
// Skeleton components
// ---------------------------------------------------------------------------

function MetricCardSkeleton() {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div className="h-4 w-24 animate-pulse rounded bg-zinc-800" />
        <div className="h-4 w-4 animate-pulse rounded bg-zinc-800" />
      </CardHeader>
      <CardContent>
        <div className="h-7 w-20 animate-pulse rounded bg-zinc-800" />
        <div className="mt-2 h-3 w-28 animate-pulse rounded bg-zinc-800" />
      </CardContent>
    </Card>
  );
}

function ChartSkeleton() {
  return (
    <div className="flex h-80 items-center justify-center">
      <div className="h-full w-full animate-pulse rounded-lg bg-zinc-800/50" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function DashboardPage() {
  const overview = useOverview();
  const campaigns = useCampaigns();

  const isLoading = overview.isLoading || campaigns.isLoading;
  const hasError = overview.isError && campaigns.isError;

  const activeCampaigns = campaigns.data?.total ?? 0;
  const metrics = buildMetrics(overview.data, activeCampaigns);
  const chartData = overview.data
    ? buildChartData(overview.data.platforms)
    : [];
  const hasChartData = chartData.length > 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-sm text-zinc-500">
          Cross-platform marketing performance at a glance
        </p>
      </div>

      {hasError && (
        <div className="flex items-center gap-2 rounded-lg border border-red-800/50 bg-red-950/30 p-4 text-sm text-red-400">
          <AlertCircle className="h-4 w-4 shrink-0" />
          Failed to load dashboard data. Make sure the backend is running on
          port 8000.
        </div>
      )}

      {/* Metric cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {isLoading
          ? Array.from({ length: 4 }).map((_, i) => (
              <MetricCardSkeleton key={i} />
            ))
          : metrics.map(({ label, value, icon: Icon, color }) => (
              <Card key={label}>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-zinc-400">
                    {label}
                  </CardTitle>
                  <Icon className={`h-4 w-4 ${color}`} />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{value}</div>
                </CardContent>
              </Card>
            ))}
      </div>

      {/* Platform performance chart */}
      <Card>
        <CardHeader>
          <CardTitle>Platform Performance</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <ChartSkeleton />
          ) : !hasChartData ? (
            <div className="flex h-80 flex-col items-center justify-center gap-2 text-zinc-500">
              <Megaphone className="h-10 w-10 text-zinc-700" />
              <p className="text-sm">
                No platform data yet. Connect platforms and launch a campaign to
                see metrics here.
              </p>
            </div>
          ) : (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                  <XAxis
                    dataKey="platform"
                    stroke="#71717a"
                    fontSize={12}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    stroke="#71717a"
                    fontSize={12}
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(v: number) =>
                      v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v)
                    }
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#18181b",
                      border: "1px solid #27272a",
                      borderRadius: "0.5rem",
                      color: "#fafafa",
                      fontSize: "0.75rem",
                    }}
                  />
                  <Bar
                    dataKey="impressions"
                    fill="#818cf8"
                    radius={[4, 4, 0, 0]}
                    name="Impressions"
                  />
                  <Bar
                    dataKey="clicks"
                    fill="#34d399"
                    radius={[4, 4, 0, 0]}
                    name="Clicks"
                  />
                  <Bar
                    dataKey="spend"
                    fill="#f59e0b"
                    radius={[4, 4, 0, 0]}
                    name="Spend ($)"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Insights & Recommendations */}
      {overview.data &&
        (overview.data.insights.length > 0 ||
          overview.data.recommendations.length > 0) && (
          <div className="grid gap-4 md:grid-cols-2">
            {overview.data.insights.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm font-medium text-zinc-400">
                    AI Insights
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 text-sm text-zinc-300">
                    {overview.data.insights.map((insight) => (
                      <li key={insight} className="flex gap-2">
                        <span className="mt-1 block h-1.5 w-1.5 shrink-0 rounded-full bg-indigo-500" />
                        {insight}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
            {overview.data.recommendations.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm font-medium text-zinc-400">
                    Recommendations
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 text-sm text-zinc-300">
                    {overview.data.recommendations.map((rec) => (
                      <li key={rec} className="flex gap-2">
                        <span className="mt-1 block h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" />
                        {rec}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
          </div>
        )}
    </div>
  );
}
