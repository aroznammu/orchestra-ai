"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, Terminal, Check } from "lucide-react";
import SectionHeading from "@/components/SectionHeading";
import PricingCard from "@/components/PricingCard";
import { PRICING_TIERS } from "@/lib/constants";

export default function PricingPage() {
  const [spend, setSpend] = useState(5000);

  const savings = Math.round(spend * 0.35);

  return (
    <>
      {/* Hero */}
      <section className="px-6 py-24">
        <div className="mx-auto max-w-4xl text-center">
          <motion.h1
            className="text-4xl font-bold tracking-tight text-zinc-50 sm:text-5xl"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            Simple,{" "}
            <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
              Transparent
            </span>{" "}
            Pricing
          </motion.h1>
          <motion.p
            className="mx-auto mt-5 max-w-xl text-lg text-zinc-400"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            Start with a free trial. No credit card required. Enterprise Cloud or self-host
            — you choose.
          </motion.p>
        </div>
      </section>

      {/* Pricing cards */}
      <section className="px-6 pb-24">
        <div className="mx-auto grid max-w-4xl gap-8 lg:grid-cols-2">
          {PRICING_TIERS.map((tier, i) => (
            <PricingCard key={tier.name} {...tier} index={i} />
          ))}
        </div>
      </section>

      {/* Self-host option */}
      <section className="px-6 pb-24">
        <div className="mx-auto max-w-4xl">
          <motion.div
            className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-8 text-center"
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
          >
            <Terminal className="mx-auto mb-4 h-8 w-8 text-emerald-400" />
            <h3 className="text-2xl font-bold text-zinc-50">
              Or Self-Host Free with Docker
            </h3>
            <p className="mx-auto mt-3 max-w-md text-zinc-400">
              OrchestraAI is open-core under the Apache 2.0 license. Deploy the full platform
              on your own infrastructure in 60 seconds.
            </p>
            <div className="mx-auto mt-6 max-w-md rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-3 text-left font-mono text-sm text-zinc-300">
              <span className="text-emerald-400">$</span> docker compose up -d
            </div>
            <div className="mt-4 flex flex-wrap items-center justify-center gap-3">
              <span className="rounded-full border border-emerald-800/40 bg-emerald-950/20 px-3 py-1 text-xs text-emerald-400">
                Apache 2.0
              </span>
              <span className="rounded-full border border-zinc-800 bg-zinc-900 px-3 py-1 text-xs text-zinc-400">
                PostgreSQL + Redis + Qdrant
              </span>
              <span className="rounded-full border border-zinc-800 bg-zinc-900 px-3 py-1 text-xs text-zinc-400">
                Ollama for local LLM
              </span>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ROI Calculator */}
      <section className="px-6 pb-24">
        <div className="mx-auto max-w-4xl">
          <SectionHeading
            title="Estimate Your Savings"
            subtitle="See how much OrchestraAI can save your team with intelligent budget optimization."
          />
          <motion.div
            className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-8"
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
          >
            <label className="block text-sm font-medium text-zinc-300">
              Current monthly ad spend
            </label>
            <div className="mt-3 flex items-center gap-4">
              <span className="text-2xl font-bold text-zinc-50">
                ${spend.toLocaleString()}
              </span>
              <input
                type="range"
                min={500}
                max={100000}
                step={500}
                value={spend}
                onChange={(e) => setSpend(Number(e.target.value))}
                className="flex-1 accent-indigo-600"
              />
            </div>
            <div className="mt-8 grid gap-6 sm:grid-cols-3">
              <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-4 text-center">
                <p className="text-xs text-zinc-500">Estimated monthly savings</p>
                <p className="mt-1 text-2xl font-bold text-emerald-400">
                  ${savings.toLocaleString()}
                </p>
              </div>
              <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-4 text-center">
                <p className="text-xs text-zinc-500">Annual savings</p>
                <p className="mt-1 text-2xl font-bold text-emerald-400">
                  ${(savings * 12).toLocaleString()}
                </p>
              </div>
              <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-4 text-center">
                <p className="text-xs text-zinc-500">ROI vs Starter plan</p>
                <p className="mt-1 text-2xl font-bold text-indigo-400">
                  {Math.round(((savings - 99) / 99) * 100)}%
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Enterprise */}
      <section className="px-6 pb-24">
        <div className="mx-auto max-w-4xl">
          <motion.div
            className="rounded-2xl border border-indigo-800/40 bg-gradient-to-br from-indigo-950/60 via-zinc-900 to-zinc-900 p-8"
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
          >
            <div className="flex flex-col items-start justify-between gap-6 sm:flex-row sm:items-center">
              <div>
                <h3 className="text-2xl font-bold text-zinc-50">Need More?</h3>
                <p className="mt-2 max-w-md text-zinc-400">
                  SSO/SAML, white-label, dedicated support, SOC 2 compliance, and SLAs for
                  enterprise teams.
                </p>
                <ul className="mt-4 space-y-2">
                  {[
                    "SSO / SAML authentication",
                    "White-label for agencies",
                    "Managed LLM key proxying",
                    "SOC 2 compliance & SLA",
                    "Dedicated support",
                  ].map((item) => (
                    <li key={item} className="flex items-center gap-2 text-sm text-zinc-300">
                      <Check className="h-4 w-4 text-indigo-400" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
              <Link
                href="/contact"
                className="inline-flex items-center gap-2 rounded-full bg-indigo-600 px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-indigo-500"
              >
                Contact Sales
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </motion.div>
        </div>
      </section>
    </>
  );
}
