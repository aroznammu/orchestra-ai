"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Play,
  Quote,
  AlertTriangle,
  Clock,
  DollarSign,
  CheckCircle2,
  Sparkles,
  Shield,
  Star,
  Users,
  Zap,
} from "lucide-react";
import GradientText from "@/components/GradientText";
import PlatformGrid from "@/components/PlatformGrid";
import SectionHeading from "@/components/SectionHeading";
import FeatureCard from "@/components/FeatureCard";
import BrowserMockup, { FeatureShowcase } from "@/components/BrowserMockup";
import HeroPipeline from "@/components/HeroPipeline";
import {
  FEATURE_HIGHLIGHTS,
  STATS,
  HOW_IT_WORKS,
  TESTIMONIALS,
  DASHBOARD_URL,
  GUARDED_TRIAL_MICROCOPY,
} from "@/lib/constants";
import EnterpriseTrustStrip from "@/components/EnterpriseTrustStrip";
import HowItWorksVideoEmbed from "@/components/HowItWorksVideoEmbed";

const AnimatedCounter = dynamic(() => import("@/components/AnimatedCounter"), { ssr: false });
const CTABanner = dynamic(() => import("@/components/CTABanner"));
const ComparisonTable = dynamic(() => import("@/components/ComparisonTable"));
const ArchitectureDiagram = dynamic(() => import("@/components/ArchitectureDiagram"));
const PipelineDemo = dynamic(() => import("@/components/demo/PipelineDemo"), { ssr: false });

const PAIN_POINTS = [
  {
    icon: AlertTriangle,
    title: "9 dashboards, 9 logins, 9 reports",
    description:
      "Toggling between nine ad platforms burns hours daily and guarantees blind spots.",
  },
  {
    icon: DollarSign,
    title: "Runaway spend, zero guardrails",
    description:
      "One misconfigured campaign drains your budget overnight. Most tools can't stop it.",
  },
  {
    icon: Clock,
    title: "Manual setup doesn't scale",
    description:
      "Adapting creative and targeting for each platform is tedious and error-prone.",
  },
];

const SOLUTION_POINTS = [
  {
    icon: Sparkles,
    title: "One command, every platform",
    description:
      "Describe what you need in plain English. AI handles the rest across all 9 platforms.",
  },
  {
    icon: Shield,
    title: "3-tier financial protection",
    description:
      "Daily, weekly, and monthly spend caps with anomaly detection and a one-click kill switch.",
  },
  {
    icon: CheckCircle2,
    title: "Compounding intelligence",
    description:
      "Every campaign makes the system smarter. Your data moat grows -- competitors can't copy it.",
  },
];

const TRUST_METRICS = [
  { icon: Zap, value: "10", label: "AI Agent Nodes" },
  { icon: Shield, value: "3-Tier", label: "Financial Protection" },
  { icon: Users, value: "9", label: "Platforms Connected" },
  { icon: Star, value: "< 1min", label: "Campaign Launch" },
];

function InlineCTA({
  text = "Start Free Trial",
  href = DASHBOARD_URL,
  secondary,
  showTrialMicrocopy = false,
}: {
  text?: string;
  href?: string;
  secondary?: string;
  /** Guardrailed trial line under the button (trial CTAs only) */
  showTrialMicrocopy?: boolean;
}) {
  return (
    <motion.div
      className="section-glow-divider py-12 text-center"
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.4 }}
    >
      {secondary && (
        <p className="mb-4 text-sm text-zinc-500">{secondary}</p>
      )}
      <Link
        href={href}
        className="btn-primary group inline-flex items-center gap-2 rounded-xl px-8 py-3.5 text-sm font-semibold text-white"
      >
        {text}
        <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
      </Link>
      {showTrialMicrocopy && (
        <p className="mx-auto mt-3 max-w-xl text-sm text-zinc-500">{GUARDED_TRIAL_MICROCOPY}</p>
      )}
    </motion.div>
  );
}

export default function HomePage() {
  return (
    <>
      {/* ============== HERO ============== */}
      <section className="relative overflow-hidden px-6 pb-16 pt-28 sm:pb-20 sm:pt-36 lg:pt-44">
        {/* Layered backgrounds for depth */}
        <div className="pointer-events-none absolute inset-0 hero-mesh" />
        <div className="pointer-events-none absolute inset-0 radial-glow" />
        <div className="pointer-events-none absolute inset-0 grid-pattern opacity-40" />
        <div className="pointer-events-none absolute inset-0 fade-bottom" />

        {/* Ambient floating orbs */}
        <div className="ambient-orb absolute -left-32 top-20 h-72 w-72 bg-indigo-600/20" />
        <div className="ambient-orb absolute -right-24 top-40 h-56 w-56 bg-purple-600/15" />
        <div className="ambient-orb absolute bottom-20 left-1/3 h-48 w-48 bg-cyan-500/10" />

        <div className="relative z-10 mx-auto max-w-4xl text-center">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <span className="mb-6 inline-flex items-center gap-2 rounded-full border border-indigo-800/60 bg-indigo-950/40 px-4 py-1.5 text-xs font-medium text-indigo-300">
              <span className="relative flex h-1.5 w-1.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-indigo-400 opacity-75" />
                <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-indigo-400" />
              </span>
              AI-Native Marketing Orchestration
            </span>
          </motion.div>

          <motion.h1
            className="text-balance text-4xl font-extrabold leading-[1.05] tracking-tighter sm:text-5xl lg:text-[3.75rem] xl:text-[4rem]"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            One AI Command.{" "}
            <GradientText text="Nine Platforms." className="block sm:inline" />{" "}
            <span className="block font-semibold text-zinc-400 sm:inline">Zero Wasted Spend.</span>
          </motion.h1>

          <motion.p
            className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-zinc-400"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            OrchestraAI connects nine major ad platforms under a single intelligent
            layer with 3-tier financial guardrails that make runaway spend impossible.
          </motion.p>

          <motion.p
            className="mx-auto mt-3 text-base font-medium tracking-wide text-indigo-400/80"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.28 }}
          >
            Stop managing campaigns. Start orchestrating.
          </motion.p>

          <motion.div
            className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <Link
              href={DASHBOARD_URL}
              className="btn-primary group inline-flex items-center gap-2 rounded-xl px-8 py-3.5 text-sm font-semibold text-white"
            >
              Start Free Trial
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </Link>
            <Link
              href="/demo"
              className="btn-secondary group inline-flex items-center gap-2 rounded-xl px-8 py-3.5 text-sm font-medium text-zinc-300"
            >
              <Play className="h-4 w-4" />
              View Demo
            </Link>
          </motion.div>
          <motion.p
            className="mx-auto mt-4 max-w-xl text-sm text-zinc-500"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.38 }}
          >
            {GUARDED_TRIAL_MICROCOPY}
          </motion.p>

          {/* Social proof micro-bar */}
          <motion.div
            className="mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-zinc-500"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.5 }}
          >
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
              No credit card required
            </span>
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
              Deploy in 60 seconds
            </span>
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
              Open-source core (Apache 2.0)
            </span>
          </motion.div>

          {/* Signature pipeline visualization */}
          <HeroPipeline />

          {/* Product UI visual anchor */}
          <BrowserMockup />
        </div>
      </section>

      <EnterpriseTrustStrip />

      {/* ============== PRODUCT SHOWCASE PANELS ============== */}
      <section className="px-6 pb-8 pt-16">
        <FeatureShowcase />
      </section>

      {/* ============== TRUST METRICS BAR ============== */}
      <section className="neon-line section-glow-divider border-b border-zinc-800/60 px-6 py-14">
        <div className="mx-auto max-w-4xl">
          <div className="grid grid-cols-2 gap-8 lg:grid-cols-4">
            {TRUST_METRICS.map((m, i) => (
              <motion.div
                key={m.label}
                className="flex flex-col items-center gap-2 text-center"
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.08 }}
              >
                <m.icon className="h-5 w-5 text-indigo-400" />
                <span className="text-2xl font-bold text-zinc-50">{m.value}</span>
                <span className="text-xs text-zinc-500">{m.label}</span>
              </motion.div>
            ))}
          </div>
          <motion.p
            className="mt-6 text-center text-xs text-zinc-600"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0.4 }}
          >
            Built by engineers with experience across adtech, ML infrastructure, and distributed systems.
          </motion.p>
        </div>
      </section>

      {/* ============== INTERACTIVE PIPELINE DEMO ============== */}
      <section className="relative overflow-hidden px-6 py-28 sm:py-32">
        <div className="ambient-orb absolute -left-20 top-20 h-72 w-72 bg-indigo-600/[0.06]" />
        <div className="ambient-orb absolute -right-16 bottom-10 h-56 w-56 bg-purple-600/[0.04]" />
        <div className="relative mx-auto max-w-6xl">
          <SectionHeading
            badge="Live Demo"
            title="Experience the Pipeline"
            subtitle="Watch 8 AI agents process a campaign in real-time. Click any node to inspect."
          />
          <PipelineDemo />
        </div>
      </section>

      {/* ============== PROBLEM ============== */}
      <section className="section-shadow relative px-6 py-28 sm:py-32">
        <div className="ambient-orb absolute -right-20 top-10 h-64 w-64 bg-red-600/5" />
        <div className="relative mx-auto max-w-5xl">
          <SectionHeading
            badge="The Problem"
            title="Marketing at Scale Is Broken"
            subtitle="Every marketing team hits the same walls. Sound familiar?"
          />
          <div className="grid gap-6 md:grid-cols-3">
            {PAIN_POINTS.map((p, i) => (
              <motion.div
                key={p.title}
                className="card-elevated rounded-2xl p-6"
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.1 }}
              >
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-red-950/60 text-red-400">
                  <p.icon className="h-5 w-5" />
                </div>
                <h3 className="mb-2 text-base font-semibold text-zinc-100">{p.title}</h3>
                <p className="text-sm leading-relaxed text-zinc-400">{p.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ============== SOLUTION ============== */}
      <section className="section-shadow relative px-6 py-28 sm:py-32">
        <div className="ambient-orb absolute -left-16 bottom-10 h-56 w-56 bg-indigo-600/8" />
        <div className="relative mx-auto max-w-5xl">
          <SectionHeading
            badge="The Solution"
            title="One AI Layer. Total Control."
            subtitle="OrchestraAI replaces the chaos with a single intelligent command center."
          />
          <div className="grid gap-6 md:grid-cols-3">
            {SOLUTION_POINTS.map((s, i) => (
              <motion.div
                key={s.title}
                className="card-elevated rounded-2xl p-6"
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.1 }}
              >
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-950/60 text-indigo-400">
                  <s.icon className="h-5 w-5" />
                </div>
                <h3 className="mb-2 text-base font-semibold text-zinc-100">{s.title}</h3>
                <p className="text-sm leading-relaxed text-zinc-400">{s.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ============== CATEGORY POSITIONING ============== */}
      <section className="relative overflow-hidden px-6 py-28 sm:py-32">
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-transparent via-indigo-950/[0.04] to-transparent" />
        <div className="ambient-orb absolute left-1/2 top-1/2 h-96 w-96 -translate-x-1/2 -translate-y-1/2 bg-indigo-600/[0.06]" />
        <div className="relative mx-auto max-w-3xl text-center">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
          >
            <span className="mb-4 inline-block rounded-full border border-indigo-800/60 bg-indigo-950/40 px-4 py-1 text-xs font-medium uppercase tracking-wider text-indigo-300">
              A New Category
            </span>
            <h2 className="text-[2rem] font-extrabold leading-[1.2] tracking-tight text-white sm:text-[2.25rem] lg:text-[2.5rem]">
              The Future of{" "}
              <GradientText text="Marketing Orchestration" />
            </h2>
            <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-zinc-400">
              Traditional tools schedule posts. OrchestraAI thinks, protects, and
              optimizes -- replacing fragile automation with intelligent
              orchestration.
            </p>
          </motion.div>
          <div className="mx-auto mt-12 grid max-w-3xl gap-8 grid-cols-2 sm:grid-cols-4">
            {[
              { value: "AI-Native", desc: "LangGraph agents, not rule-based scripts" },
              { value: "Zero Infra", desc: "No pipelines to maintain or debug" },
              { value: "Self-Improving", desc: "Every campaign compounds your moat" },
              { value: "Dev-First", desc: "Full API, SDK, CLI, and self-host" },
            ].map((item, i) => (
              <motion.div
                key={item.value}
                className="text-center"
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.1 }}
              >
                <div className="text-xl font-bold text-white">{item.value}</div>
                <p className="mt-2 text-sm leading-relaxed text-zinc-500">{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ============== PLATFORM LOGOS BAR ============== */}
      <section className="neon-line section-glow-divider border-y border-zinc-800/60 px-6 py-16">
        <div className="mx-auto max-w-6xl">
          <p className="mb-8 text-center text-sm font-medium uppercase tracking-widest text-zinc-500">
            One AI layer &middot; Nine platforms &middot; Zero silos
          </p>
          <PlatformGrid />
        </div>
      </section>

      {/* ============== HOW IT WORKS ============== */}
      <section id="how-it-works" className="section-shadow relative px-6 py-28 sm:py-32">
        <div className="ambient-orb absolute right-0 top-1/3 h-48 w-48 bg-purple-600/8" />
        <div className="relative mx-auto max-w-5xl">
          <SectionHeading
            badge="How It Works"
            title="From Natural Language to Live Campaigns"
            subtitle="Three steps. One command. Every platform."
          />
          <div className="grid gap-6 md:grid-cols-3">
            {HOW_IT_WORKS.map((step, i) => (
              <motion.div
                key={step.number}
                className="card-elevated relative rounded-2xl p-6"
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.12 }}
              >
                <div className="mb-4 flex items-center gap-3">
                  <span className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-600 text-sm font-bold text-white shadow-lg shadow-indigo-600/20">
                    {step.number}
                  </span>
                  <step.icon className="h-5 w-5 text-indigo-400" />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-zinc-50">{step.title}</h3>
                <p className="text-sm leading-relaxed text-zinc-400">{step.description}</p>
                {i < HOW_IT_WORKS.length - 1 && (
                  <div className="absolute -right-3 top-1/2 hidden h-px w-6 bg-gradient-to-r from-indigo-500/40 to-transparent md:block" />
                )}
              </motion.div>
            ))}
          </div>
          <HowItWorksVideoEmbed />
        </div>
      </section>

      {/* ============== FEATURE HIGHLIGHTS ============== */}
      <section className="section-shadow relative px-6 py-28 sm:py-32">
        <div className="ambient-orb absolute -left-20 top-20 h-64 w-64 bg-indigo-600/6" />
        <div className="relative mx-auto max-w-6xl">
          <SectionHeading
            badge="Features"
            title="Built for Modern Marketing Teams"
            subtitle="Save time, reduce risk, and maximize ROI across all platforms."
          />
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURE_HIGHLIGHTS.map((f, i) => (
              <FeatureCard key={f.title} {...f} index={i} />
            ))}
          </div>
          <div className="mt-10 text-center">
            <Link
              href="/features"
              className="group inline-flex items-center gap-1.5 text-sm font-medium text-indigo-400 transition-colors hover:text-indigo-300"
            >
              See all features
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </Link>
          </div>
        </div>
      </section>

      {/* ============== INLINE CTA (after Features) ============== */}
      <InlineCTA
        text="Start Free Trial"
        secondary="No credit card required. Deploy in under 60 seconds."
        showTrialMicrocopy
      />

      {/* ============== ARCHITECTURE ============== */}
      <section className="relative px-6 py-28 sm:py-32">
        <div className="ambient-orb absolute right-10 bottom-0 h-48 w-48 bg-cyan-500/6" />
        <div className="relative mx-auto max-w-5xl">
          <SectionHeading
            badge="Architecture"
            title="10-Node AI Agent Pipeline"
            subtitle="LangGraph StateGraph with compliance gates, financial guardrails, and IP scanning."
          />
          <ArchitectureDiagram />
        </div>
      </section>

      {/* ============== STATS ============== */}
      <section className="neon-line section-glow-divider border-y border-zinc-800/60 px-6 py-28">
        <div className="mx-auto grid max-w-4xl grid-cols-2 gap-12 lg:grid-cols-4">
          {STATS.map((stat) => (
            <AnimatedCounter key={stat.label} {...stat} />
          ))}
        </div>
      </section>

      {/* ============== COMPARISON TABLE ============== */}
      <section className="px-6 py-28 sm:py-32">
        <div className="mx-auto max-w-5xl">
          <SectionHeading
            badge="Comparison"
            title="Why Not Hootsuite?"
            subtitle="OrchestraAI was built to solve problems that existing tools ignore."
          />
          <ComparisonTable />
        </div>
      </section>

      {/* ============== INLINE CTA (after Comparison) ============== */}
      <InlineCTA
        text="See It in Action"
        href="/demo"
        secondary="Watch the AI orchestrate a live cross-platform campaign."
      />

      {/* ============== DEVELOPER SECTION ============== */}
      <section className="relative px-6 py-28 sm:py-32">
        <div className="ambient-orb absolute -right-16 bottom-20 h-56 w-56 bg-cyan-500/6" />
        <div className="relative mx-auto max-w-6xl">
          <div className="grid items-center gap-12 lg:grid-cols-2">
            {/* Code snippet */}
            <motion.div
              className="overflow-hidden rounded-2xl border border-zinc-800/60 bg-[#111117]"
              initial={{ opacity: 0, x: -24 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
            >
              <div className="flex items-center gap-2 border-b border-zinc-800/60 px-4 py-3">
                <div className="flex gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-red-500/50" />
                  <span className="h-2.5 w-2.5 rounded-full bg-amber-500/50" />
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-500/50" />
                </div>
                <span className="ml-2 text-[11px] text-zinc-600">orchestrator.py</span>
              </div>
              <pre className="overflow-x-auto p-5 text-[13px] leading-relaxed">
                <code>
                  <span className="text-purple-400">from</span>{" "}
                  <span className="text-zinc-300">orchestra</span>{" "}
                  <span className="text-purple-400">import</span>{" "}
                  <span className="text-cyan-400">Orchestrator</span>
                  {"\n\n"}
                  <span className="text-zinc-500"># One command. Nine platforms.</span>
                  {"\n"}
                  <span className="text-zinc-300">result</span>{" "}
                  <span className="text-purple-400">=</span>{" "}
                  <span className="text-purple-400">await</span>{" "}
                  <span className="text-cyan-400">Orchestrator</span>
                  <span className="text-zinc-500">.</span>
                  <span className="text-amber-400">ask</span>
                  <span className="text-zinc-500">(</span>
                  {"\n"}
                  {"  "}
                  <span className="text-emerald-400">&quot;Launch a summer sale campaign</span>
                  {"\n"}
                  {"   "}
                  <span className="text-emerald-400">across Instagram and TikTok</span>
                  {"\n"}
                  {"   "}
                  <span className="text-emerald-400">with a $500 budget&quot;</span>
                  {"\n"}
                  <span className="text-zinc-500">)</span>
                  {"\n\n"}
                  <span className="text-zinc-500"># AI handles the rest:</span>
                  {"\n"}
                  <span className="text-zinc-500"># Intent → Compliance → Content →</span>
                  {"\n"}
                  <span className="text-zinc-500"># Video → Policy → Publish → Analytics</span>
                  {"\n\n"}
                  <span className="text-purple-400">print</span>
                  <span className="text-zinc-500">(</span>
                  <span className="text-zinc-300">result</span>
                  <span className="text-zinc-500">.</span>
                  <span className="text-amber-400">platforms_published</span>
                  <span className="text-zinc-500">)</span>
                  {"  "}
                  <span className="text-zinc-600"># [&apos;instagram&apos;, &apos;tiktok&apos;]</span>
                  {"\n"}
                  <span className="text-purple-400">print</span>
                  <span className="text-zinc-500">(</span>
                  <span className="text-zinc-300">result</span>
                  <span className="text-zinc-500">.</span>
                  <span className="text-amber-400">spend_remaining</span>
                  <span className="text-zinc-500">)</span>
                  {"   "}
                  <span className="text-zinc-600"># $487.40</span>
                </code>
              </pre>
            </motion.div>

            {/* Text + CTA */}
            <motion.div
              initial={{ opacity: 0, x: 24 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.1 }}
            >
              <span className="mb-4 inline-block rounded-full border border-indigo-800/60 bg-indigo-950/40 px-4 py-1 text-xs font-medium uppercase tracking-wider text-indigo-300">
                Built for Developers
              </span>
              <h2 className="mt-2 text-[2rem] font-extrabold leading-[1.2] tracking-tight text-white sm:text-[2.25rem] lg:text-[2.5rem]">
                API-First. Open Source.{" "}
                <span className="text-zinc-400">Production-Ready.</span>
              </h2>
              <p className="mt-4 text-lg leading-relaxed text-zinc-400">
                OrchestraAI is built on FastAPI, LangGraph, and PostgreSQL with a
                fully typed Python SDK. Self-host with Docker in 60 seconds or use
                our managed cloud. Apache 2.0 licensed.
              </p>
              <ul className="mt-6 space-y-3">
                {[
                  "10-node LangGraph agent pipeline",
                  "9 platform connectors with OAuth2",
                  "Full REST API with OpenAPI docs",
                  "Alembic migrations, Redis caching, Qdrant vectors",
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2.5 text-sm text-zinc-300">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-indigo-400" />
                    {item}
                  </li>
                ))}
              </ul>
              <div className="mt-8 flex flex-wrap gap-3">
                <Link
                  href={DASHBOARD_URL}
                  className="btn-primary inline-flex items-center gap-2 rounded-xl px-6 py-3 text-sm font-semibold text-white"
                >
                  Start Building
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <a
                  href="https://github.com/aroznammu/orchestra-ai"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-secondary inline-flex items-center gap-2 rounded-xl px-6 py-3 text-sm font-medium text-zinc-300"
                >
                  <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" /></svg>
                  View on GitHub
                </a>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ============== SOCIAL PROOF ============== */}
      <section className="relative px-6 py-28 sm:py-32">
        <div className="ambient-orb absolute -left-10 top-10 h-56 w-56 bg-purple-600/6" />
        <div className="relative mx-auto max-w-5xl">
          <SectionHeading
            badge="Testimonials"
            title="Trusted by Marketing Teams"
            subtitle="Real results from teams that switched to AI-powered orchestration."
          />
          <div className="grid gap-6 sm:grid-cols-3">
            {TESTIMONIALS.map((t, i) => (
              <motion.div
                key={i}
                className="card-elevated rounded-2xl p-6"
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.1 }}
              >
                {t.metric && (
                  <div className="mb-3 inline-flex rounded-full bg-indigo-950/60 px-3 py-1 text-[10px] font-semibold text-indigo-300">
                    {t.metric}
                  </div>
                )}
                <Quote className="mb-2 h-4 w-4 text-indigo-400/40" />
                <p className="text-sm leading-relaxed text-zinc-300">
                  &ldquo;{t.quote}&rdquo;
                </p>
                <div className="mt-4 border-t border-zinc-800/60 pt-4">
                  <div className="flex items-start gap-3">
                    <div
                      className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-600 to-purple-600 text-xs font-bold text-white"
                      aria-hidden
                    >
                      {t.name
                        .split(" ")
                        .map((w) => w[0])
                        .join("")
                        .slice(0, 2)
                        .toUpperCase()}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-semibold text-zinc-50">{t.name}</p>
                      <p className="text-xs text-zinc-500">{t.role}</p>
                      <div className="mt-2 flex items-center gap-2">
                        <span
                          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-zinc-700/60 bg-zinc-900 text-[10px] font-bold text-zinc-500"
                          aria-hidden
                        >
                          {t.companyLogo}
                        </span>
                        <span className="text-xs font-medium text-zinc-400">{t.company}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ============== CTA BANNER ============== */}
      <section className="px-6 pb-28">
        <div className="mx-auto max-w-4xl">
          <CTABanner />
        </div>
      </section>
    </>
  );
}
