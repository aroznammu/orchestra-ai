"use client";

import { motion } from "framer-motion";

const ITEMS = [
  "Stripe verified",
  "SOC 2-ready architecture",
  "Meta Ads API",
  "ByteDance Seedance 2.0",
  "Llama 3",
] as const;

export default function EnterpriseTrustStrip() {
  return (
    <motion.section
      className="border-y border-zinc-800/50 bg-zinc-950/40 px-6 py-8"
      aria-label="Enterprise integrations and security"
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.45 }}
    >
      <p className="mb-5 text-center text-[11px] font-semibold uppercase tracking-[0.2em] text-zinc-500">
        Powered by & secured by
      </p>
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-center gap-x-10 gap-y-4">
        {ITEMS.map((label, i) => (
          <motion.span
            key={label}
            className="text-sm font-medium text-zinc-500 grayscale transition hover:grayscale-0 hover:text-zinc-400"
            initial={{ opacity: 0, y: 6 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.35, delay: i * 0.05 }}
          >
            {label}
          </motion.span>
        ))}
      </div>
    </motion.section>
  );
}
