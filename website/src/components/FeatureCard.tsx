"use client";

import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";

interface FeatureCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
  index: number;
}

export default function FeatureCard({
  icon: Icon,
  title,
  description,
  index,
}: FeatureCardProps) {
  return (
    <motion.div
      className="group rounded-xl border border-zinc-800 bg-zinc-900/60 p-6 transition-colors hover:border-indigo-800/60 hover:bg-zinc-900/80"
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.4, delay: index * 0.08 }}
    >
      <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-lg bg-indigo-600/10">
        <Icon className="h-5 w-5 text-indigo-400" />
      </div>
      <h3 className="mb-2 text-lg font-semibold text-zinc-50">{title}</h3>
      <p className="text-sm leading-relaxed text-zinc-400">{description}</p>
    </motion.div>
  );
}
