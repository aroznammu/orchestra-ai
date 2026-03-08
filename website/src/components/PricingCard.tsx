"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Check } from "lucide-react";
import type { PricingTier } from "@/lib/constants";
import { DASHBOARD_URL } from "@/lib/constants";

interface PricingCardProps extends PricingTier {
  index: number;
}

export default function PricingCard({
  name,
  price,
  period,
  description,
  features,
  cta,
  popular,
  index,
}: PricingCardProps) {
  return (
    <motion.div
      className={`relative flex flex-col rounded-2xl border p-8 ${
        popular
          ? "border-indigo-600 bg-zinc-900/80 shadow-lg shadow-indigo-900/20"
          : "border-zinc-800 bg-zinc-900/60"
      }`}
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.4, delay: index * 0.1 }}
    >
      {popular && (
        <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-indigo-600 px-4 py-1 text-xs font-medium text-white">
          Most Popular
        </span>
      )}

      <h3 className="text-xl font-semibold text-zinc-50">{name}</h3>
      <p className="mt-2 text-sm text-zinc-400">{description}</p>

      <div className="mt-6">
        <span className="text-4xl font-bold text-zinc-50">${price}</span>
        <span className="text-zinc-400">{period}</span>
      </div>

      <ul className="mt-8 flex-1 space-y-3">
        {features.map((feature) => (
          <li key={feature} className="flex items-start gap-3 text-sm text-zinc-300">
            <Check className="mt-0.5 h-4 w-4 shrink-0 text-indigo-400" />
            {feature}
          </li>
        ))}
      </ul>

      <Link
        href={DASHBOARD_URL}
        className={`mt-8 block rounded-full py-3 text-center text-sm font-medium transition-colors ${
          popular
            ? "bg-indigo-600 text-white hover:bg-indigo-500"
            : "border border-zinc-700 text-zinc-300 hover:border-indigo-600 hover:text-white"
        }`}
      >
        {cta}
      </Link>
    </motion.div>
  );
}
