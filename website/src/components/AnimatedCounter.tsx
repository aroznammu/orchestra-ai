"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useInView } from "framer-motion";
import type { Stat } from "@/lib/constants";

export default function AnimatedCounter({ value, prefix, suffix, label }: Stat) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    if (!inView) return;

    const isDecimal = value % 1 !== 0;
    const duration = 1200;
    const steps = 40;
    const interval = duration / steps;
    let step = 0;

    const timer = setInterval(() => {
      step++;
      const progress = step / steps;
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = eased * value;
      setDisplay(isDecimal ? parseFloat(current.toFixed(2)) : Math.round(current));
      if (step >= steps) clearInterval(timer);
    }, interval);

    return () => clearInterval(timer);
  }, [inView, value]);

  const formatted = value % 1 !== 0 ? display.toFixed(2) : display.toString();

  return (
    <motion.div
      ref={ref}
      className="text-center"
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5 }}
    >
      <div className="text-4xl font-bold text-zinc-50 sm:text-5xl">
        {prefix}
        {formatted}
        {suffix && <span className="text-indigo-400">{suffix}</span>}
      </div>
      <p className="mt-2 text-sm text-zinc-400">{label}</p>
    </motion.div>
  );
}
