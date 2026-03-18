"use client";

import { motion } from "framer-motion";
import { Check } from "lucide-react";
import CTABanner from "@/components/CTABanner";
import SectionHeading from "@/components/SectionHeading";
import { FEATURES_DETAILED, TECH_STACK } from "@/lib/constants";

export default function FeaturesPage() {
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
              Platform Capabilities
            </span>
          </motion.div>
          <motion.h1
            className="text-4xl font-bold tracking-tight text-zinc-50 sm:text-5xl"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.05 }}
          >
            Everything You Need to{" "}
            <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
              Orchestrate Marketing
            </span>
          </motion.h1>
          <motion.p
            className="mx-auto mt-5 max-w-2xl text-lg text-zinc-400"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            Eight powerful capabilities working in concert. AI orchestration, video generation,
            financial guardrails, cross-platform intelligence, and more.
          </motion.p>
        </div>
      </section>

      {/* Feature sections */}
      <section className="px-6 pb-24">
        <div className="mx-auto max-w-6xl space-y-28">
          {FEATURES_DETAILED.map((feature, sectionIdx) => {
            const isReversed = sectionIdx % 2 !== 0;
            const Icon = feature.icon;

            return (
              <motion.div
                key={feature.id}
                className={`flex flex-col items-start gap-12 lg:flex-row ${
                  isReversed ? "lg:flex-row-reverse" : ""
                }`}
                initial={{ opacity: 0, y: 32 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-80px" }}
                transition={{ duration: 0.5 }}
              >
                {/* Info side */}
                <div className="flex-1">
                  <div className="icon-glow mb-4 flex h-12 w-12 items-center justify-center rounded-xl">
                    <Icon className="h-6 w-6 text-indigo-400" />
                  </div>
                  <p className="text-xs font-medium uppercase tracking-widest text-indigo-400">
                    {feature.subtitle}
                  </p>
                  <h2 className="mt-2 text-3xl font-bold text-zinc-50">{feature.title}</h2>
                  <p className="mt-4 leading-relaxed text-zinc-400">{feature.description}</p>

                  {feature.code && (
                    <div className="mt-6 rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-3 font-mono text-sm text-zinc-300">
                      <span className="text-emerald-400">$</span> {feature.code}
                    </div>
                  )}
                </div>

                {/* Bullet list side */}
                <div className="flex-1">
                  <ul className="space-y-3">
                    {feature.bullets.map((bullet, i) => (
                      <motion.li
                        key={i}
                        className="flex items-start gap-3 text-sm text-zinc-300"
                        initial={{ opacity: 0, x: isReversed ? -12 : 12 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.3, delay: i * 0.04 }}
                      >
                        <Check className="mt-0.5 h-4 w-4 shrink-0 text-indigo-400" />
                        <span>{bullet}</span>
                      </motion.li>
                    ))}
                  </ul>
                </div>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* Tech Stack */}
      <section className="border-t border-zinc-800/60 px-6 py-24">
        <div className="mx-auto max-w-4xl">
          <SectionHeading
            badge="Tech Stack"
            title="Built on Production-Grade Infrastructure"
            subtitle="Every layer chosen for reliability, performance, and developer experience."
          />
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {TECH_STACK.map((item, i) => (
              <motion.div
                key={item.layer}
                className="glass rounded-lg px-5 py-4"
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.3, delay: i * 0.04 }}
              >
                <p className="text-xs font-medium uppercase tracking-wider text-indigo-400">{item.layer}</p>
                <p className="mt-1 text-sm text-zinc-300">{item.tech}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-6 pb-24">
        <div className="mx-auto max-w-4xl">
          <CTABanner
            title="See it in action"
            subtitle="Start a free trial and experience every feature with your own campaigns."
          />
        </div>
      </section>
    </>
  );
}
