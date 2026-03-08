"use client";

import { motion } from "framer-motion";
import { ShieldCheck } from "lucide-react";
import SectionHeading from "@/components/SectionHeading";
import CTABanner from "@/components/CTABanner";
import { SECURITY_FEATURES } from "@/lib/constants";

export default function SecurityPage() {
  return (
    <>
      {/* Hero */}
      <section className="px-6 py-24">
        <div className="mx-auto max-w-4xl text-center">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <ShieldCheck className="mx-auto mb-6 h-12 w-12 text-indigo-400" />
          </motion.div>
          <motion.h1
            className="text-4xl font-bold tracking-tight text-zinc-50 sm:text-5xl"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            Security &{" "}
            <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
              Compliance
            </span>
          </motion.h1>
          <motion.p
            className="mx-auto mt-5 max-w-2xl text-lg text-zinc-400"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            Enterprise-grade security at every layer. Encryption at rest, tenant isolation,
            GDPR compliance, and full audit trails built in from day one.
          </motion.p>
        </div>
      </section>

      {/* Security features */}
      <section className="px-6 pb-24">
        <div className="mx-auto max-w-6xl space-y-12">
          {SECURITY_FEATURES.map((feature, i) => {
            const Icon = feature.icon;
            return (
              <motion.div
                key={feature.title}
                className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-8"
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-60px" }}
                transition={{ duration: 0.4, delay: i * 0.05 }}
              >
                <div className="flex items-start gap-4">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-indigo-600/10">
                    <Icon className="h-5 w-5 text-indigo-400" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-zinc-50">{feature.title}</h3>
                    <p className="mt-1 text-sm text-zinc-400">{feature.description}</p>
                    <ul className="mt-4 grid gap-2 sm:grid-cols-2">
                      {feature.items.map((item) => (
                        <li
                          key={item}
                          className="flex items-start gap-2 text-sm text-zinc-300"
                        >
                          <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-indigo-500" />
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* Trust badges */}
      <section className="px-6 pb-24">
        <div className="mx-auto max-w-4xl">
          <SectionHeading
            title="Built for Trust"
            subtitle="Security isn't a feature we added — it's how we built the platform."
          />
          <div className="grid gap-4 sm:grid-cols-3">
            {[
              { label: "SOC 2 Ready", detail: "Logical access controls and audit trails" },
              { label: "GDPR Compliant", detail: "Data export, deletion, and consent management" },
              {
                label: "Apache 2.0",
                detail: "Open-core — audit the source code yourself",
              },
            ].map((badge, i) => (
              <motion.div
                key={badge.label}
                className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 text-center"
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.3, delay: i * 0.08 }}
              >
                <ShieldCheck className="mx-auto mb-2 h-6 w-6 text-emerald-400" />
                <p className="text-sm font-semibold text-zinc-50">{badge.label}</p>
                <p className="mt-1 text-xs text-zinc-500">{badge.detail}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-6 pb-24">
        <div className="mx-auto max-w-4xl">
          <CTABanner
            title="Your data. Your control."
            subtitle="Self-host on your infrastructure or trust our enterprise cloud with SOC 2 readiness."
          />
        </div>
      </section>
    </>
  );
}
