"use client";

import { motion } from "framer-motion";

const BAR_HEIGHTS = [60, 45, 80, 35, 70, 55, 90, 40, 65];
const BAR_LABELS = ["Twitter", "YT", "TT", "Pin", "FB", "IG", "LI", "Snap", "Ggl"];
const AGENTS = [
  { name: "Classify", latency: "12ms" },
  { name: "Compliance", latency: "8ms" },
  { name: "Content", latency: "340ms" },
  { name: "Video", latency: "1.2s" },
  { name: "Publish", latency: "45ms" },
];

export interface BrowserMockupProps {
  /** Financial safety affordances for the interactive /demo walkthrough */
  demoFinancialControls?: boolean;
}

export default function BrowserMockup({ demoFinancialControls = false }: BrowserMockupProps) {
  return (
    <motion.div
      className="relative mx-auto mt-16 max-w-5xl"
      initial={{ opacity: 0, y: 40, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.9, delay: 0.5, ease: [0.22, 1, 0.36, 1] }}
      whileHover={{ scale: 1.015 }}
    >
      {/* Glow behind the mockup */}
      <div className="pointer-events-none absolute -inset-4 rounded-2xl bg-gradient-to-b from-indigo-600/15 via-purple-600/10 to-transparent blur-2xl" />

      <div className="relative overflow-hidden rounded-xl border border-zinc-700/60 bg-zinc-900/90 shadow-2xl shadow-indigo-950/40 backdrop-blur-md">
        {/* Browser chrome */}
        <div className="flex items-center gap-2 border-b border-zinc-800/80 px-4 py-3">
          <div className="flex gap-1.5">
            <span className="h-3 w-3 rounded-full bg-red-500/60" />
            <span className="h-3 w-3 rounded-full bg-amber-500/60" />
            <span className="h-3 w-3 rounded-full bg-emerald-500/60" />
          </div>
          <div className="mx-auto flex items-center gap-2 rounded-md bg-zinc-800/80 px-4 py-1.5 text-xs text-zinc-500">
            <svg className="h-3 w-3 text-emerald-500" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            <span className="text-zinc-400">useorchestra.dev/dashboard</span>
          </div>
        </div>

        {/* Dashboard content */}
        <div className="p-4 sm:p-6">
          {/* Header */}
          <div className="mb-6 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-xs font-bold text-white shadow-lg shadow-indigo-600/30">O</div>
              <div>
                <div className="text-sm font-semibold text-zinc-200">Dashboard</div>
                <div className="text-[10px] text-zinc-500">Cross-platform marketing performance</div>
              </div>
            </div>
            <div className="hidden items-center gap-1.5 rounded-full bg-emerald-950/60 px-3 py-1 sm:flex">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
              </span>
              <span className="text-[10px] font-medium text-emerald-400">All systems operational</span>
            </div>
          </div>

          {demoFinancialControls && (
            <motion.div
              className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35, delay: 0.4 }}
            >
              <button
                type="button"
                className="w-full rounded-lg border border-red-600/50 bg-red-950/50 px-4 py-2.5 text-center text-[10px] font-bold uppercase tracking-wide text-red-200 shadow-lg shadow-red-950/40 transition hover:bg-red-900/50 sm:w-auto sm:text-[11px]"
              >
                EMERGENCY KILL SWITCH: HALT ALL SPEND
              </button>
              <span className="text-center text-[10px] text-zinc-500 sm:text-right">
                One tap pauses every connected account
              </span>
            </motion.div>
          )}

          {/* Metric cards */}
          <div className="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              { label: "Active Campaigns", value: "12", delta: "+3", color: "text-indigo-400", deltaColor: "text-emerald-400", key: "campaigns" },
              { label: "Total Impressions", value: "2.4M", delta: "+18%", color: "text-emerald-400", deltaColor: "text-emerald-400", key: "impr" },
              { label: "Monthly Spend", value: "$8,240", delta: "62% cap", color: "text-amber-400", deltaColor: "text-amber-400", key: "spend" },
              { label: "Avg. ROI", value: "340%", delta: "+24%", color: "text-purple-400", deltaColor: "text-emerald-400", key: "roi" },
            ].map((m) => (
              <div key={m.key} className="rounded-lg border border-zinc-800/60 bg-zinc-950/60 p-3">
                <div className="flex items-baseline justify-between">
                  <span className={`text-lg font-bold ${m.color}`}>{m.value}</span>
                  <span className={`text-[9px] font-medium ${m.deltaColor}`}>{m.delta}</span>
                </div>
                <div className="mt-1 text-[10px] text-zinc-500">{m.label}</div>
                {demoFinancialControls && m.key === "roi" && (
                  <div className="mt-2 inline-flex items-center gap-1 rounded-md border border-amber-500/25 bg-amber-950/35 px-2 py-1 text-[8px] font-semibold leading-tight text-amber-100/95">
                    <span aria-hidden>⚡</span>
                    Autonomous Budget Reallocation Active
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Chart + Sidebar */}
          <div className="flex gap-3">
            {/* Chart */}
            <div className="flex-1 rounded-lg border border-zinc-800/60 bg-zinc-950/60 p-4">
              <div className="mb-3 flex items-center justify-between">
                <span className="text-xs font-medium text-zinc-400">Platform Performance</span>
                <span className="rounded-md bg-zinc-800/80 px-2 py-0.5 text-[9px] text-zinc-500">Last 30 days</span>
              </div>
              <div className="flex items-end gap-1.5 h-24">
                {BAR_HEIGHTS.map((h, i) => (
                  <motion.div
                    key={i}
                    className="flex-1 rounded-sm bg-gradient-to-t from-indigo-600 to-indigo-400"
                    initial={{ height: 0 }}
                    animate={{ height: `${h}%` }}
                    transition={{ duration: 0.6, delay: 0.8 + i * 0.06, ease: "easeOut" }}
                  />
                ))}
              </div>
              <div className="mt-2 flex justify-between text-[8px] text-zinc-600">
                {BAR_LABELS.map((l) => (
                  <span key={l}>{l}</span>
                ))}
              </div>
            </div>

            {/* Agent sidebar */}
            <div className="hidden w-52 flex-shrink-0 rounded-lg border border-zinc-800/60 bg-zinc-950/60 p-4 sm:block">
              <div className="mb-3 text-xs font-medium text-zinc-400">AI Agent Pipeline</div>
              <div className="space-y-2.5">
                {AGENTS.map((a, i) => (
                  <motion.div
                    key={a.name}
                    className="flex items-center gap-2"
                    initial={{ opacity: 0, x: 8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.3, delay: 1.2 + i * 0.08 }}
                  >
                    <span className="relative flex h-1.5 w-1.5">
                      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
                      <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-500" />
                    </span>
                    <span className="text-[10px] text-zinc-400">{a.name}</span>
                    <span className="ml-auto font-mono text-[9px] text-zinc-600">{a.latency}</span>
                  </motion.div>
                ))}
              </div>
              {/* Mini throughput indicator */}
              <div className="mt-4 border-t border-zinc-800/50 pt-3">
                <div className="flex items-center justify-between text-[9px]">
                  <span className="text-zinc-500">Throughput</span>
                  <span className="font-mono text-emerald-400">847 req/min</span>
                </div>
                <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-zinc-800">
                  <motion.div
                    className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-emerald-500"
                    initial={{ width: 0 }}
                    animate={{ width: "72%" }}
                    transition={{ duration: 1.2, delay: 1.5, ease: "easeOut" }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Subtle top-border glow on the mockup */}
        <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-indigo-500/40 to-transparent" />
      </div>

      {/* Bottom glow */}
      <div className="pointer-events-none absolute inset-x-0 -bottom-16 mx-auto h-32 w-2/3 rounded-full bg-indigo-600/10 blur-3xl" />
    </motion.div>
  );
}

export function FeatureShowcase() {
  const panels = [
    {
      title: "AI Agent Pipeline",
      desc: "10-node LangGraph orchestration with automatic fallback",
      visual: (
        <div className="space-y-2">
          {["Classify", "Compliance", "Content", "Video", "Publish"].map((n, i) => (
            <motion.div
              key={n}
              className="flex items-center gap-2"
              initial={{ opacity: 0, x: -12 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.3, delay: i * 0.08 }}
            >
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
              </span>
              <span className="text-xs text-zinc-300">{n}</span>
              <span className="ml-auto h-px flex-1 bg-gradient-to-r from-zinc-800 to-transparent" />
              <span className="font-mono text-[9px] text-emerald-400">OK</span>
            </motion.div>
          ))}
        </div>
      ),
    },
    {
      title: "Financial Guardrails",
      desc: "3-tier spend caps with anomaly detection",
      visual: (
        <div className="space-y-3">
          {[
            { label: "Daily", pct: 45, color: "from-emerald-500 to-emerald-400" },
            { label: "Weekly", pct: 62, color: "from-amber-500 to-amber-400" },
            { label: "Monthly", pct: 28, color: "from-indigo-500 to-indigo-400" },
          ].map((cap, i) => (
            <div key={cap.label}>
              <div className="mb-1 flex items-center justify-between text-[10px]">
                <span className="text-zinc-400">{cap.label}</span>
                <span className="font-mono text-zinc-500">{cap.pct}%</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-zinc-800">
                <motion.div
                  className={`h-full rounded-full bg-gradient-to-r ${cap.color}`}
                  initial={{ width: 0 }}
                  whileInView={{ width: `${cap.pct}%` }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.8, delay: 0.2 + i * 0.12, ease: "easeOut" }}
                />
              </div>
            </div>
          ))}
        </div>
      ),
    },
    {
      title: "Cross-Platform ROI",
      desc: "Normalized metrics across all 9 platforms",
      visual: (
        <div className="flex items-end gap-1 h-16">
          {[55, 72, 40, 88, 65, 48, 78, 35, 60].map((h, i) => (
            <motion.div
              key={i}
              className="flex-1 rounded-t-sm bg-gradient-to-t from-indigo-600 to-purple-400"
              initial={{ height: 0 }}
              whileInView={{ height: `${h}%` }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.1 + i * 0.05, ease: "easeOut" }}
            />
          ))}
        </div>
      ),
    },
  ];

  return (
    <div className="mx-auto grid max-w-6xl gap-4 sm:grid-cols-3">
      {panels.map((p, i) => (
        <motion.div
          key={p.title}
          className="card-elevated group rounded-2xl p-5"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4, delay: i * 0.1 }}
        >
          <h4 className="text-sm font-semibold text-zinc-100">{p.title}</h4>
          <p className="mt-1 text-[11px] leading-relaxed text-zinc-500">{p.desc}</p>
          <div className="mt-4 rounded-lg border border-zinc-800/40 bg-zinc-950/60 p-3">
            {p.visual}
          </div>
        </motion.div>
      ))}
    </div>
  );
}
