"use client";

import { useState, useEffect, useRef } from "react";
import { motion, useInView } from "framer-motion";
import { Check, AlertTriangle, Shield } from "lucide-react";

const CHECKS = [
  { label: "Content Policy", description: "No prohibited content detected", warn: false },
  { label: "Budget Cap", description: "Spend within daily/weekly/monthly limits", warn: false },
  { label: "Targeting Rules", description: "Audience criteria compliant", warn: true },
  { label: "Platform Guidelines", description: "Instagram & TikTok rules met", warn: false },
  { label: "IP Compliance Scan", description: "No trademark or copyright violations", warn: false },
  { label: "Data Privacy", description: "GDPR consent and processing verified", warn: false },
];

type CheckState = "pending" | "checking" | "warning" | "passed";

export default function ComplianceScene() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });
  const [states, setStates] = useState<CheckState[]>(CHECKS.map(() => "pending"));

  useEffect(() => {
    if (!isInView) return;

    const timers: ReturnType<typeof setTimeout>[] = [];

    CHECKS.forEach((check, i) => {
      timers.push(setTimeout(() => {
        setStates((prev) => prev.map((s, j) => (j === i ? "checking" : s)));
      }, 400 + i * 500));

      if (check.warn) {
        timers.push(setTimeout(() => {
          setStates((prev) => prev.map((s, j) => (j === i ? "warning" : s)));
        }, 400 + i * 500 + 400));

        timers.push(setTimeout(() => {
          setStates((prev) => prev.map((s, j) => (j === i ? "passed" : s)));
        }, 400 + i * 500 + 1200));
      } else {
        timers.push(setTimeout(() => {
          setStates((prev) => prev.map((s, j) => (j === i ? "passed" : s)));
        }, 400 + i * 500 + 400));
      }
    });

    return () => timers.forEach(clearTimeout);
  }, [isInView]);

  const passedCount = states.filter((s) => s === "passed").length;

  return (
    <div ref={ref} className="mx-auto max-w-2xl">
      <motion.div
        className="card-elevated overflow-hidden rounded-2xl"
        initial={{ opacity: 0, y: 20 }}
        animate={isInView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.5 }}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-zinc-800/60 px-5 py-3">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-indigo-400" />
            <span className="text-xs font-medium text-zinc-400">Compliance Gate</span>
          </div>
          <span className="font-mono text-[11px] text-zinc-600">
            {passedCount}/{CHECKS.length} passed
          </span>
        </div>

        {/* Checklist */}
        <div className="space-y-1 p-4">
          {CHECKS.map((check, i) => {
            const state = states[i];
            return (
              <motion.div
                key={check.label}
                className="flex items-center gap-3 rounded-lg border px-4 py-3"
                initial={{ opacity: 0, x: -20 }}
                animate={isInView ? {
                  opacity: state === "pending" ? 0.35 : 1,
                  x: 0,
                  borderColor:
                    state === "passed" ? "rgba(16,185,129,0.3)"
                    : state === "warning" ? "rgba(245,158,11,0.4)"
                    : state === "checking" ? "rgba(99,102,241,0.3)"
                    : "rgba(63,63,70,0.2)",
                  backgroundColor:
                    state === "warning" ? "rgba(245,158,11,0.04)"
                    : state === "passed" ? "rgba(16,185,129,0.03)"
                    : "transparent",
                } : {}}
                transition={{ duration: 0.3, delay: i * 0.08 }}
              >
                {/* Status icon */}
                <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center">
                  {state === "passed" && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ type: "spring", stiffness: 500, damping: 15 }}
                    >
                      <Check className="h-4 w-4 text-emerald-400" />
                    </motion.div>
                  )}
                  {state === "warning" && (
                    <motion.div animate={{ scale: [1, 1.15, 1] }} transition={{ duration: 0.6, repeat: Infinity }}>
                      <AlertTriangle className="h-4 w-4 text-amber-400" />
                    </motion.div>
                  )}
                  {state === "checking" && (
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-indigo-500/30 border-t-indigo-500" />
                  )}
                  {state === "pending" && (
                    <div className="h-2 w-2 rounded-full bg-zinc-700" />
                  )}
                </div>

                {/* Text */}
                <div className="min-w-0 flex-1">
                  <div className="text-xs font-medium text-zinc-200">{check.label}</div>
                  <div className="text-[11px] text-zinc-500">{check.description}</div>
                </div>

                {/* Duration badge */}
                {state === "passed" && (
                  <motion.span
                    className="rounded-full bg-emerald-950/60 px-2 py-0.5 font-mono text-[9px] text-emerald-400"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.1 }}
                  >
                    {Math.floor(Math.random() * 30 + 5)}ms
                  </motion.span>
                )}
                {state === "warning" && (
                  <span className="rounded-full bg-amber-950/60 px-2 py-0.5 text-[9px] text-amber-400">
                    reviewing...
                  </span>
                )}
              </motion.div>
            );
          })}
        </div>

        {/* Summary bar */}
        <div className="border-t border-zinc-800/60 px-5 py-3">
          <div className="flex items-center justify-between">
            <span className="text-[11px] text-zinc-500">Pre-action validation</span>
            <motion.span
              className="text-xs font-semibold"
              animate={{
                color: passedCount === CHECKS.length ? "#34d399" : "#a1a1aa",
              }}
            >
              {passedCount === CHECKS.length ? "All checks passed" : "Running checks..."}
            </motion.span>
          </div>
          <div className="mt-2 h-1 overflow-hidden rounded-full bg-zinc-800">
            <motion.div
              className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-emerald-500"
              animate={{ width: `${(passedCount / CHECKS.length) * 100}%` }}
              transition={{ duration: 0.4 }}
            />
          </div>
        </div>
      </motion.div>
    </div>
  );
}
