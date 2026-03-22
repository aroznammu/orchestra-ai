"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import SectionHeading from "@/components/SectionHeading";
import CTABanner from "@/components/CTABanner";
import ContentCreationScene from "@/components/demo/scenes/ContentCreationScene";
import ComplianceScene from "@/components/demo/scenes/ComplianceScene";
import CrossPlatformScene from "@/components/demo/scenes/CrossPlatformScene";
import DashboardScene from "@/components/demo/scenes/DashboardScene";
import DemoWatchVideoSection from "@/components/demo/DemoWatchVideoSection";
import { DASHBOARD_URL, GUARDED_TRIAL_MICROCOPY } from "@/lib/constants";

export default function DemoPage() {
  return (
    <>
      {/* ============== SCENE 1: Hero Intro ============== */}
      <section className="relative overflow-hidden px-6 py-28">
        <div className="pointer-events-none absolute inset-0 radial-glow" />
        <div className="mx-auto max-w-4xl text-center">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <span className="mb-4 inline-block rounded-full border border-indigo-800/60 bg-indigo-950/40 px-4 py-1 text-xs font-medium uppercase tracking-wider text-indigo-300">
              Interactive Walkthrough
            </span>
          </motion.div>
          <motion.h1
            className="text-4xl font-extrabold tracking-tight text-zinc-50 sm:text-5xl lg:text-6xl"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.05 }}
          >
            See OrchestraAI{" "}
            <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">
              in Action
            </span>
          </motion.h1>
          <motion.p
            className="mx-auto mt-5 max-w-xl text-lg text-zinc-400"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            Watch how a single natural language command orchestrates copy,{" "}
            <span className="text-violet-300/90">Seedance 2.0 video</span>, compliance checks, and
            cross-platform publishing.
          </motion.p>
          <motion.p
            className="mx-auto mt-3 max-w-md text-sm text-zinc-600"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            Prefer video? Watch the overview first, or scroll for the interactive
            walkthrough below.
          </motion.p>
        </div>
      </section>

      {/* Divider */}
      <div className="section-glow-divider neon-line mx-auto h-px max-w-4xl" />

      {/* 90s overview — early placement for visitors who want a quick watch */}
      <DemoWatchVideoSection />

      <div className="section-glow-divider neon-line mx-auto h-px max-w-4xl" />

      {/* ============== SCENE 2: Content Creation ============== */}
      <section className="section-shadow relative px-6 py-28">
        <div className="ambient-orb absolute -left-20 top-10 h-48 w-48 bg-indigo-600/[0.04]" />
        <SectionHeading
          badge="Step 1"
          title="AI Content Generation"
          subtitle="Draft, review, and optimize copy — then render a 10s Seedance 2.0 video for vertical placements."
        />
        <ContentCreationScene />
      </section>

      <div className="section-glow-divider neon-line mx-auto h-px max-w-4xl" />

      {/* ============== SCENE 3: Compliance Check ============== */}
      <section className="section-shadow relative px-6 py-28">
        <div className="ambient-orb absolute -right-16 bottom-10 h-56 w-56 bg-purple-600/[0.04]" />
        <SectionHeading
          badge="Step 2"
          title="Compliance Validation"
          subtitle="Every piece of content passes through 6 automated compliance gates before publishing."
        />
        <ComplianceScene />
      </section>

      <div className="section-glow-divider neon-line mx-auto h-px max-w-4xl" />

      {/* ============== SCENE 4: Cross-Platform Publishing ============== */}
      <section className="section-shadow relative px-6 py-28">
        <div className="ambient-orb absolute -left-12 top-1/2 h-44 w-44 bg-cyan-600/[0.04]" />
        <SectionHeading
          badge="Step 3"
          title="Cross-Platform Publishing"
          subtitle="Content flows from the AI hub to all connected platforms simultaneously."
        />
        <CrossPlatformScene />
      </section>

      <div className="section-glow-divider neon-line mx-auto h-px max-w-4xl" />

      {/* ============== SCENE 5: Dashboard Snapshot ============== */}
      <section className="relative px-6 py-28">
        <div className="ambient-orb absolute -right-20 top-20 h-52 w-52 bg-indigo-600/[0.04]" />
        <SectionHeading
          badge="Step 4"
          title="Live Dashboard"
          subtitle="Monitor campaigns, agent activity, and cross-platform performance in real-time."
        />
        <DashboardScene />
      </section>

      <div className="section-glow-divider neon-line mx-auto h-px max-w-4xl" />

      {/* ============== SCENE 6: CTA End Frame ============== */}
      <section className="relative px-6 py-28">
        <div className="pointer-events-none absolute inset-0 radial-glow opacity-40" />
        <div className="mx-auto max-w-4xl text-center">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
          >
            <h2 className="text-3xl font-extrabold tracking-tight text-zinc-50 sm:text-4xl">
              Start Building with{" "}
              <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">
                OrchestraAI
              </span>{" "}
              Today
            </h2>
            <p className="mx-auto mt-4 max-w-lg text-zinc-400">
              The best way to understand OrchestraAI is to use it. Start a free trial and
              experience the full platform with your own campaigns.
            </p>
            <Link
              href={DASHBOARD_URL}
              className="btn-primary group mt-8 inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-indigo-600 to-purple-600 px-8 py-3.5 text-sm font-medium text-white shadow-lg shadow-indigo-600/20"
            >
              Start Free Trial
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </Link>
            <p className="mx-auto mt-3 max-w-md text-sm text-zinc-500">{GUARDED_TRIAL_MICROCOPY}</p>
          </motion.div>
        </div>
      </section>

      {/* Footer CTA */}
      <section className="px-6 pb-24">
        <div className="mx-auto max-w-4xl">
          <CTABanner
            title="Questions about the demo?"
            subtitle="Our team is happy to walk you through a personalized demo."
            buttonText="Contact Us"
            buttonHref="/contact"
          />
        </div>
      </section>
    </>
  );
}
