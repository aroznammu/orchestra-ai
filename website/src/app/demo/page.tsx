"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, BrainCircuit, Video, ShieldCheck, BarChart3, Database, Eye } from "lucide-react";
import VideoEmbed from "@/components/VideoEmbed";
import CTABanner from "@/components/CTABanner";
import { DASHBOARD_URL } from "@/lib/constants";

const DEMO_FEATURES = [
  {
    icon: BrainCircuit,
    title: "AI Orchestrator",
    description: "Type a natural language command and watch the 10-node agent pipeline execute in real-time.",
  },
  {
    icon: Video,
    title: "Video Generation",
    description: "Generate marketing videos from text descriptions with automatic IP compliance scanning.",
  },
  {
    icon: ShieldCheck,
    title: "Financial Guardrails",
    description: "See the 3-tier spend caps and kill switch in action protecting your budget.",
  },
  {
    icon: BarChart3,
    title: "Cross-Platform Analytics",
    description: "Unified dashboard showing normalized ROI across all 9 connected platforms.",
  },
  {
    icon: Database,
    title: "Data Moat Engine",
    description: "Watch your competitive advantage compound as campaigns feed the intelligence flywheel.",
  },
  {
    icon: Eye,
    title: "Visual Compliance",
    description: "GPT-4o Vision scans every video frame for IP violations before delivery.",
  },
];

export default function DemoPage() {
  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden px-6 py-24">
        <div className="pointer-events-none absolute inset-0 radial-glow" />
        <div className="mx-auto max-w-4xl text-center">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <span className="mb-4 inline-block rounded-full border border-indigo-800/60 bg-indigo-950/40 px-4 py-1 text-xs font-medium uppercase tracking-wider text-indigo-300">
              Product Demo
            </span>
          </motion.div>
          <motion.h1
            className="text-4xl font-bold tracking-tight text-zinc-50 sm:text-5xl"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.05 }}
          >
            See OrchestraAI{" "}
            <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
              in Action
            </span>
          </motion.h1>
          <motion.p
            className="mx-auto mt-5 max-w-xl text-lg text-zinc-400"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            Watch how a single natural language command orchestrates content creation, compliance
            checks, and cross-platform publishing.
          </motion.p>
        </div>
      </section>

      {/* Video */}
      <section className="px-6 pb-24">
        <div className="mx-auto max-w-4xl">
          <VideoEmbed />
        </div>
      </section>

      {/* Feature highlights */}
      <section className="px-6 pb-24">
        <div className="mx-auto max-w-5xl">
          <motion.h2
            className="mb-12 text-center text-2xl font-bold text-zinc-50 sm:text-3xl"
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4 }}
          >
            What You&apos;ll See in the Dashboard
          </motion.h2>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {DEMO_FEATURES.map((feature, i) => {
              const Icon = feature.icon;
              return (
                <motion.div
                  key={feature.title}
                  className="glass rounded-xl p-6"
                  initial={{ opacity: 0, y: 16 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.3, delay: i * 0.06 }}
                >
                  <div className="icon-glow mb-3 flex h-10 w-10 items-center justify-center rounded-lg">
                    <Icon className="h-5 w-5 text-indigo-400" />
                  </div>
                  <h3 className="text-sm font-semibold text-zinc-50">{feature.title}</h3>
                  <p className="mt-1 text-sm text-zinc-400">{feature.description}</p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Try it yourself */}
      <section className="px-6 pb-24">
        <div className="mx-auto max-w-4xl text-center">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
          >
            <h2 className="text-3xl font-bold text-zinc-50">Ready to try it yourself?</h2>
            <p className="mx-auto mt-4 max-w-lg text-zinc-400">
              The best way to understand OrchestraAI is to use it. Start a free trial and
              experience the full platform with your own campaigns.
            </p>
            <Link
              href={DASHBOARD_URL}
              className="group mt-8 inline-flex items-center gap-2 rounded-full bg-indigo-600 px-8 py-3.5 text-sm font-medium text-white shadow-lg shadow-indigo-600/20 transition-all hover:bg-indigo-500 hover:shadow-indigo-600/30"
            >
              Start Free Trial
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </Link>
          </motion.div>
        </div>
      </section>

      {/* CTA */}
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
