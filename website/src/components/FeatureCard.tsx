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
      className="glass group rounded-xl p-6 transition-all"
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.4, delay: index * 0.08 }}
    >
      <div className="icon-glow mb-4 flex h-12 w-12 items-center justify-center rounded-lg">
        <Icon className="h-5 w-5 text-indigo-400" />
      </div>
      <h3 className="mb-2 text-lg font-semibold text-zinc-50">{title}</h3>
      <p className="text-sm leading-relaxed text-zinc-400">{description}</p>
    </motion.div>
  );
}
