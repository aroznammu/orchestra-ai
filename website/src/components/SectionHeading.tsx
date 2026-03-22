"use client";

import { motion } from "framer-motion";

interface SectionHeadingProps {
  title: string;
  subtitle?: string;
  badge?: string;
  centered?: boolean;
}

export default function SectionHeading({
  title,
  subtitle,
  badge,
  centered = true,
}: SectionHeadingProps) {
  return (
    <motion.div
      className={`mb-16 ${centered ? "text-center" : ""}`}
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.5 }}
    >
      {badge && (
        <span className="mb-4 inline-block rounded-full border border-indigo-800/60 bg-indigo-950/40 px-4 py-1 text-xs font-medium uppercase tracking-wider text-indigo-300">
          {badge}
        </span>
      )}
      <h2 className="text-[2rem] font-extrabold leading-[1.2] tracking-tight text-white sm:text-[2.25rem] lg:text-[2.5rem]">
        {title}
      </h2>
      {subtitle && (
        <p className={`mt-4 text-lg leading-relaxed text-zinc-400 ${centered ? "mx-auto max-w-2xl" : ""}`}>
          {subtitle}
        </p>
      )}
    </motion.div>
  );
}
