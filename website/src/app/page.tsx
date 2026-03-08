"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Play, MessageSquare, Quote } from "lucide-react";
import GradientText from "@/components/GradientText";
import PlatformGrid from "@/components/PlatformGrid";
import SectionHeading from "@/components/SectionHeading";
import FeatureCard from "@/components/FeatureCard";
import AnimatedCounter from "@/components/AnimatedCounter";
import CTABanner from "@/components/CTABanner";
import {
  FEATURE_HIGHLIGHTS,
  STATS,
  HOW_IT_WORKS,
  DASHBOARD_URL,
} from "@/lib/constants";

export default function HomePage() {
  return (
    <>
      {/* ============== HERO ============== */}
      <section className="relative overflow-hidden px-6 py-24 sm:py-32 lg:py-40">
        {/* Background decoration */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_30%,rgba(99,102,241,0.08),transparent_60%)]" />
          <div className="absolute inset-0 bg-[linear-gradient(to_bottom,transparent_60%,rgb(9,9,11))]" />
          <div
            className="absolute inset-0 opacity-[0.03]"
            style={{
              backgroundImage:
                "linear-gradient(rgba(255,255,255,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.06) 1px, transparent 1px)",
              backgroundSize: "64px 64px",
            }}
          />
        </div>

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
            Stop Managing Nine Dashboards.{" "}
            <GradientText text="Start Orchestrating." className="block sm:inline" />
          </motion.h1>

          <motion.p
            className="mx-auto mt-6 max-w-2xl text-lg text-zinc-400"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            One AI layer connecting Twitter, YouTube, TikTok, Pinterest, Facebook, Instagram,
            LinkedIn, Snapchat, and Google Ads. Describe what you need in plain English and let
            the 10-node AI agent handle the rest.
          </motion.p>

          <motion.div
            className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <Link
              href={DASHBOARD_URL}
              className="inline-flex items-center gap-2 rounded-full bg-indigo-600 px-8 py-3 text-sm font-medium text-white transition-colors hover:bg-indigo-500"
            >
              Start Free Trial
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="#how-it-works"
              className="inline-flex items-center gap-2 rounded-full border border-zinc-700 px-8 py-3 text-sm font-medium text-zinc-300 transition-colors hover:border-zinc-500 hover:text-white"
            >
              <Play className="h-4 w-4" />
              Watch Demo
            </Link>
          </motion.div>
        </div>
      </section>

      {/* ============== PLATFORM LOGOS BAR ============== */}
      <section className="border-y border-zinc-800/60 px-6 py-14">
        <div className="mx-auto max-w-5xl">
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
            title="How It Works"
            subtitle="From natural language to live campaigns in three steps."
          />
          <div className="grid gap-8 md:grid-cols-3">
            {HOW_IT_WORKS.map((step, i) => (
              <motion.div
                key={step.number}
                className="relative rounded-xl border border-zinc-800 bg-zinc-900/60 p-6"
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.12 }}
              >
                <div className="mb-4 flex items-center gap-3">
                  <span className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-600 text-sm font-bold text-white">
                    {step.number}
                  </span>
                  <step.icon className="h-5 w-5 text-indigo-400" />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-zinc-50">{step.title}</h3>
                <p className="text-sm leading-relaxed text-zinc-400">{step.description}</p>
                {i < HOW_IT_WORKS.length - 1 && (
                  <div className="absolute -right-4 top-1/2 hidden h-px w-8 bg-zinc-800 md:block" />
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
              className="inline-flex items-center gap-1.5 text-sm font-medium text-indigo-400 transition-colors hover:text-indigo-300"
            >
              See all features
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
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

      {/* ============== SOCIAL PROOF PLACEHOLDER ============== */}
      <section className="px-6 py-24">
        <div className="mx-auto max-w-4xl">
          <SectionHeading
            title="Trusted by Marketing Teams"
            subtitle="Join the growing community of teams orchestrating smarter campaigns."
          />
          <div className="grid gap-6 sm:grid-cols-2">
            {[
              {
                quote:
                  "OrchestraAI replaced five tools and cut our campaign setup time by 80%. The AI orchestrator just works.",
                name: "Marketing Director",
                company: "Growth Agency",
              },
              {
                quote:
                  "The financial guardrails alone saved us from a $5,000 mistake on Google Ads. Worth every penny.",
                name: "Head of Digital",
                company: "E-Commerce Brand",
              },
            ].map((t, i) => (
              <motion.div
                key={i}
                className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-6"
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.1 }}
              >
                <Quote className="mb-3 h-5 w-5 text-indigo-400/60" />
                <p className="text-sm leading-relaxed text-zinc-300">&ldquo;{t.quote}&rdquo;</p>
                <div className="mt-4 flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-600/20 text-xs font-bold text-indigo-400">
                    <MessageSquare className="h-3.5 w-3.5" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-zinc-50">{t.name}</p>
                    <p className="text-xs text-zinc-500">{t.company}</p>
                  </div>
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
