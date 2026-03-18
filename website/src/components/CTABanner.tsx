"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { DASHBOARD_URL } from "@/lib/constants";

interface CTABannerProps {
  title?: string;
  subtitle?: string;
  buttonText?: string;
  buttonHref?: string;
}

export default function CTABanner({
  title = "Stop managing nine dashboards. Start orchestrating.",
  subtitle = "Self-host in 60 seconds with Docker, or start a free trial of Enterprise Cloud.",
  buttonText = "Get Started Free",
  buttonHref = DASHBOARD_URL,
}: CTABannerProps) {
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
        <h2 className="text-3xl font-bold text-zinc-50 sm:text-4xl">{title}</h2>
        <p className="mx-auto mt-4 max-w-xl text-zinc-400">{subtitle}</p>
        <Link
          href={buttonHref}
          className="group mt-8 inline-flex items-center gap-2 rounded-full bg-indigo-600 px-8 py-3 text-sm font-medium text-white shadow-lg shadow-indigo-600/20 transition-all hover:bg-indigo-500 hover:shadow-indigo-600/30"
        >
          {buttonText}
          <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
        </Link>
      </div>
    </motion.section>
  );
}
