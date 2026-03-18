"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Play, Quote } from "lucide-react";
import GradientText from "@/components/GradientText";
import PlatformGrid from "@/components/PlatformGrid";
import SectionHeading from "@/components/SectionHeading";
import FeatureCard from "@/components/FeatureCard";
import AnimatedCounter from "@/components/AnimatedCounter";
import CTABanner from "@/components/CTABanner";
import ComparisonTable from "@/components/ComparisonTable";
import ArchitectureDiagram from "@/components/ArchitectureDiagram";
import {
  FEATURE_HIGHLIGHTS,
  STATS,
  HOW_IT_WORKS,
  TESTIMONIALS,
  DASHBOARD_URL,
} from "@/lib/constants";

export default function HomePage() {
  return (
    <>
      {/* ============== HERO ============== */}
      <section className="relative overflow-hidden px-6 py-28 sm:py-36 lg:py-44">
        <div className="pointer-events-none absolute inset-0 radial-glow" />
        <div className="pointer-events-none absolute inset-0 fade-bottom" />
        <div className="pointer-events-none absolute inset-0 grid-pattern opacity-60" />

        <div className="relative z-10 mx-auto max-w-4xl text-center">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <span className="mb-6 inline-block rounded-full border border-indigo-800/60 bg-indigo-950/40 px-4 py-1.5 text-xs font-medium text-indigo-300">
              AI-Native Marketing Orchestration
            </span>
          </motion.div>

          <motion.h1
            className="text-4xl font-bold leading-tight tracking-tight sm:text-5xl lg:text-6xl"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            Orchestrate Everything.{" "}
            <GradientText text="Overspend Nothing." className="block sm:inline" />
          </motion.h1>

          <motion.p
            className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-zinc-400"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            One AI layer connecting Twitter, YouTube, TikTok, Pinterest, Facebook, Instagram,
            LinkedIn, Snapchat, and Google Ads. 10 AI agent nodes. 3-tier financial guardrails.
            Zero runaway spend.
          </motion.p>

          <motion.div
            className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <Link
              href={DASHBOARD_URL}
              className="group inline-flex items-center gap-2 rounded-full bg-indigo-600 px-8 py-3.5 text-sm font-medium text-white shadow-lg shadow-indigo-600/20 transition-all hover:bg-indigo-500 hover:shadow-indigo-600/30"
            >
              Start Free Trial
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </Link>
            <Link
              href="/demo"
              className="group inline-flex items-center gap-2 rounded-full border border-zinc-700 px-8 py-3.5 text-sm font-medium text-zinc-300 transition-all hover:border-zinc-500 hover:text-white"
            >
              <Play className="h-4 w-4" />
              Watch Demo
            </Link>
          </motion.div>
        </div>
      </section>

      {/* ============== PLATFORM LOGOS BAR ============== */}
      <section className="border-y border-zinc-800/60 px-6 py-12">
        <div className="mx-auto max-w-6xl">
          <p className="mb-8 text-center text-sm font-medium uppercase tracking-widest text-zinc-500">
            One AI layer &middot; Nine platforms &middot; Zero silos
          </p>
          <PlatformGrid />
        </div>
      </section>

      {/* ============== HOW IT WORKS ============== */}
      <section id="how-it-works" className="px-6 py-24">
        <div className="mx-auto max-w-5xl">
          <SectionHeading
            badge="How It Works"
            title="From Natural Language to Live Campaigns"
            subtitle="Three steps. One command. Every platform."
          />
          <div className="grid gap-6 md:grid-cols-3">
            {HOW_IT_WORKS.map((step, i) => (
              <motion.div
                key={step.number}
                className="glass relative rounded-xl p-6"
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
                  <div className="absolute -right-3 top-1/2 hidden h-px w-6 bg-gradient-to-r from-zinc-700 to-transparent md:block" />
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ============== FEATURE HIGHLIGHTS ============== */}
      <section className="px-6 py-24">
        <div className="mx-auto max-w-6xl">
          <SectionHeading
            badge="Features"
            title="Built for Modern Marketing Teams"
            subtitle="Every feature designed to save time, reduce risk, and maximize ROI across all your platforms."
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

      {/* ============== ARCHITECTURE ============== */}
      <section className="px-6 py-24">
        <div className="mx-auto max-w-5xl">
          <SectionHeading
            badge="Architecture"
            title="10-Node AI Agent Pipeline"
            subtitle="Every request flows through a LangGraph StateGraph with compliance gates, financial guardrails, and visual IP scanning."
          />
          <ArchitectureDiagram />
        </div>
      </section>

      {/* ============== STATS ============== */}
      <section className="border-y border-zinc-800/60 px-6 py-20">
        <div className="mx-auto grid max-w-4xl grid-cols-2 gap-12 lg:grid-cols-4">
          {STATS.map((stat) => (
            <AnimatedCounter key={stat.label} {...stat} />
          ))}
        </div>
      </section>

      {/* ============== COMPARISON TABLE ============== */}
      <section className="px-6 py-24">
        <div className="mx-auto max-w-5xl">
          <SectionHeading
            badge="Comparison"
            title="Why Not Hootsuite?"
            subtitle="OrchestraAI was built to solve problems that existing tools ignore."
          />
          <ComparisonTable />
        </div>
      </section>

      {/* ============== SOCIAL PROOF ============== */}
      <section className="px-6 py-24">
        <div className="mx-auto max-w-5xl">
          <SectionHeading
            badge="Testimonials"
            title="Trusted by Marketing Teams"
            subtitle="Join the growing community of teams orchestrating smarter campaigns."
          />
          <div className="grid gap-6 sm:grid-cols-3">
            {TESTIMONIALS.map((t, i) => (
              <motion.div
                key={i}
                className="glass rounded-xl p-6"
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.1 }}
              >
                <Quote className="mb-3 h-5 w-5 text-indigo-400/60" />
                <p className="text-sm leading-relaxed text-zinc-300">
                  &ldquo;{t.quote}&rdquo;
                </p>
                <div className="mt-4 border-t border-zinc-800/60 pt-4">
                  <p className="text-sm font-medium text-zinc-50">{t.role}</p>
                  <p className="text-xs text-zinc-500">{t.company}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ============== CTA BANNER ============== */}
      <section className="px-6 pb-24">
        <div className="mx-auto max-w-4xl">
          <CTABanner />
        </div>
      </section>
    </>
  );
}
