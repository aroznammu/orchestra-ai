"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { DASHBOARD_URL, GUARDED_TRIAL_MICROCOPY } from "@/lib/constants";

interface CTABannerProps {
  title?: string;
  subtitle?: string;
  buttonText?: string;
  buttonHref?: string;
  /** Trial microcopy under the button; defaults to on only for dashboard signup links */
  showTrialFootnote?: boolean;
}

export default function CTABanner({
  title = "Stop managing nine dashboards. Start orchestrating.",
  subtitle = "Self-host in 60 seconds with Docker, or start a free trial of Enterprise Cloud.",
  buttonText = "Get Started Free",
  buttonHref = DASHBOARD_URL,
  showTrialFootnote,
}: CTABannerProps) {
  const trialFootnoteVisible = showTrialFootnote ?? buttonHref === DASHBOARD_URL;
  return (
    <motion.section
      className="relative overflow-hidden rounded-2xl border border-indigo-800/30 bg-gradient-to-br from-indigo-950/80 via-zinc-900 to-purple-950/60 px-6 py-16 text-center sm:px-12"
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.5 }}
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(99,102,241,0.15),transparent_60%)]" />
      <div className="pointer-events-none absolute inset-0 grid-pattern opacity-40" />
      <div className="relative z-10">
        <h2 className="text-3xl font-extrabold leading-[1.2] text-white sm:text-4xl">{title}</h2>
        <p className="mx-auto mt-4 max-w-xl leading-relaxed text-zinc-400">{subtitle}</p>
        <Link
          href={buttonHref}
          className="btn-primary group mt-8 inline-flex items-center gap-2 rounded-xl px-8 py-3.5 text-sm font-semibold text-white"
        >
          {buttonText}
          <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
        </Link>
        {trialFootnoteVisible && (
          <p className="mx-auto mt-3 max-w-lg text-sm text-zinc-500">{GUARDED_TRIAL_MICROCOPY}</p>
        )}
      </div>
    </motion.section>
  );
}
