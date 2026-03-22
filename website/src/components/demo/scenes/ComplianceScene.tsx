"use client";

import { useState, useEffect, useRef, useMemo } from "react";
import { motion, useInView } from "framer-motion";
import { Check, AlertTriangle, Shield, ScanLine } from "lucide-react";

const CHECKS = [
  { label: "Content Policy", description: "No prohibited content detected", warn: false },
  { label: "Budget Cap", description: "Spend within daily/weekly/monthly limits", warn: false },
  { label: "Targeting Rules", description: "Audience criteria compliant", warn: true },
  { label: "Platform Guidelines", description: "Instagram & TikTok rules met", warn: false },
  { label: "Data Privacy", description: "GDPR consent and processing verified", warn: false },
];

const PASS_MS = [14, 22, 19, 31, 17];

type CheckState = "pending" | "checking" | "warning" | "passed";

type IpScanPhase = "idle" | "scanning" | "checks";

export default function ComplianceScene() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });
  const [states, setStates] = useState<CheckState[]>(CHECKS.map(() => "pending"));
  const [ipPhase, setIpPhase] = useState<IpScanPhase>("idle");
  const [ipChecks, setIpChecks] = useState({ celebrity: false, logos: false });

  const passedMs = useMemo(() => PASS_MS, []);

  useEffect(() => {
    if (!isInView) return;

    const t0 = setTimeout(() => setIpPhase("scanning"), 200);
    const t1 = setTimeout(() => {
      setIpPhase("checks");
      setIpChecks({ celebrity: true, logos: false });
    }, 1600);
    const t2 = setTimeout(() => setIpChecks({ celebrity: true, logos: true }), 2400);

    const timers: ReturnType<typeof setTimeout>[] = [t0, t1, t2];

    CHECKS.forEach((check, i) => {
      timers.push(setTimeout(() => {
        setStates((prev) => prev.map((s, j) => (j === i ? "checking" : s)));
      }, 800 + i * 480));

      if (check.warn) {
        timers.push(setTimeout(() => {
          setStates((prev) => prev.map((s, j) => (j === i ? "warning" : s)));
        }, 800 + i * 480 + 400));

        timers.push(setTimeout(() => {
          setStates((prev) => prev.map((s, j) => (j === i ? "passed" : s)));
        }, 800 + i * 480 + 1200));
      } else {
        timers.push(setTimeout(() => {
          setStates((prev) => prev.map((s, j) => (j === i ? "passed" : s)));
        }, 800 + i * 480 + 400));
      }
    });

    return () => timers.forEach(clearTimeout);
  }, [isInView]);

  const passedCount = states.filter((s) => s === "passed").length;
  const ipDone = ipChecks.celebrity && ipChecks.logos;

  return (
    <div ref={ref} className="mx-auto max-w-2xl space-y-5">
      {/* Visual IP compliance gate — primary moat */}
      <motion.div
        className="card-elevated overflow-hidden rounded-2xl border border-emerald-500/20 bg-gradient-to-br from-emerald-950/[0.15] to-zinc-950/40"
        initial={{ opacity: 0, y: 16 }}
        animate={isInView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.45 }}
      >
        <div className="flex items-center justify-between border-b border-zinc-800/60 px-4 py-3 sm:px-5">
          <div className="flex items-center gap-2">
            <ScanLine className="h-4 w-4 text-emerald-400" />
            <span className="text-xs font-semibold text-zinc-200">Visual IP compliance scan</span>
          </div>
          <span className="rounded-full bg-emerald-950/70 px-2 py-0.5 text-[9px] font-medium text-emerald-300">
            GPT-4o Vision · frame-level
          </span>
        </div>
        <div className="p-4 sm:p-5">
          <p className="mb-4 text-[11px] leading-relaxed text-zinc-500">
            Every generated frame is analyzed for celebrity likeness and copyrighted logos before the
            asset can leave the gate.
          </p>
          <div className="relative flex gap-2 sm:gap-3">
            {[0, 1, 2].map((fi) => (
              <motion.div
                key={fi}
                className="relative flex-1 overflow-hidden rounded-lg border border-zinc-700/50 bg-zinc-900/80"
                initial={{ opacity: 0, y: 8 }}
                animate={isInView ? { opacity: 1, y: 0 } : {}}
                transition={{ delay: 0.1 + fi * 0.08 }}
              >
                <div
                  className="aspect-[9/16] max-h-[120px] w-full bg-gradient-to-b from-zinc-700/40 to-zinc-900 sm:max-h-[140px]"
                  style={{
                    backgroundImage:
                      "linear-gradient(135deg, rgba(99,102,241,0.12), transparent), linear-gradient(0deg, rgba(24,24,27,0.9), rgba(39,39,42,0.5))",
                  }}
                />
                {ipPhase !== "idle" && (
                  <motion.div
                    className="pointer-events-none absolute inset-x-0 h-0.5 bg-emerald-400/90 shadow-[0_0_12px_rgba(52,211,153,0.6)]"
                    initial={{ top: "0%" }}
                    animate={
                      ipPhase === "scanning"
                        ? { top: ["0%", "100%", "0%"] }
                        : { top: "100%" }
                    }
                    transition={
                      ipPhase === "scanning"
                        ? { duration: 1.4, ease: "easeInOut", repeat: 1 }
                        : { duration: 0.3 }
                    }
                  />
                )}
                <span className="absolute bottom-1 left-1 font-mono text-[8px] text-zinc-500">
                  f{fi + 1}
                </span>
              </motion.div>
            ))}
          </div>
          <div className="mt-4 space-y-2">
            <motion.div
              className="flex items-center justify-between rounded-lg border px-3 py-2.5"
              animate={{
                borderColor: ipChecks.celebrity ? "rgba(16,185,129,0.35)" : "rgba(63,63,70,0.35)",
                backgroundColor: ipChecks.celebrity ? "rgba(16,185,129,0.05)" : "transparent",
              }}
            >
              <span className="text-xs text-zinc-300">Celebrity likeness</span>
              {ipChecks.celebrity ? (
                <span className="flex items-center gap-1 text-[11px] font-medium text-emerald-400">
                  <Check className="h-3.5 w-3.5" />
                  Safe
                </span>
              ) : (
                <span className="text-[10px] text-zinc-600">Scanning…</span>
              )}
            </motion.div>
            <motion.div
              className="flex items-center justify-between rounded-lg border px-3 py-2.5"
              animate={{
                borderColor: ipChecks.logos ? "rgba(16,185,129,0.35)" : "rgba(63,63,70,0.35)",
                backgroundColor: ipChecks.logos ? "rgba(16,185,129,0.05)" : "transparent",
              }}
            >
              <span className="text-xs text-zinc-300">Copyrighted logos</span>
              {ipChecks.logos ? (
                <span className="flex items-center gap-1 text-[11px] font-medium text-emerald-400">
                  <Check className="h-3.5 w-3.5" />
                  Safe
                </span>
              ) : (
                <span className="text-[10px] text-zinc-600">Scanning…</span>
              )}
            </motion.div>
          </div>
        </div>
      </motion.div>

      <motion.div
        className="card-elevated overflow-hidden rounded-2xl"
        initial={{ opacity: 0, y: 20 }}
        animate={isInView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.5, delay: 0.08 }}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-zinc-800/60 px-5 py-3">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-indigo-400" />
            <span className="text-xs font-medium text-zinc-400">Additional compliance gates</span>
          </div>
          <span className="font-mono text-[11px] text-zinc-600">
            {passedCount}/{CHECKS.length} passed
            {ipDone ? " · IP scan OK" : ""}
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
                animate={
                  isInView
                    ? {
                        opacity: state === "pending" ? 0.35 : 1,
                        x: 0,
                        borderColor:
                          state === "passed"
                            ? "rgba(16,185,129,0.3)"
                            : state === "warning"
                              ? "rgba(245,158,11,0.4)"
                              : state === "checking"
                                ? "rgba(99,102,241,0.3)"
                                : "rgba(63,63,70,0.2)",
                        backgroundColor:
                          state === "warning"
                            ? "rgba(245,158,11,0.04)"
                            : state === "passed"
                              ? "rgba(16,185,129,0.03)"
                              : "transparent",
                      }
                    : {}
                }
                transition={{ duration: 0.3, delay: i * 0.06 }}
              >
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
                  {state === "pending" && <div className="h-2 w-2 rounded-full bg-zinc-700" />}
                </div>

                <div className="min-w-0 flex-1">
                  <div className="text-xs font-medium text-zinc-200">{check.label}</div>
                  <div className="text-[11px] text-zinc-500">{check.description}</div>
                </div>

                {state === "passed" && (
                  <motion.span
                    className="rounded-full bg-emerald-950/60 px-2 py-0.5 font-mono text-[9px] text-emerald-400"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.1 }}
                  >
                    {passedMs[i]}ms
                  </motion.span>
                )}
                {state === "warning" && (
                  <span className="rounded-full bg-amber-950/60 px-2 py-0.5 text-[9px] text-amber-400">
                    reviewing…
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
                color: passedCount === CHECKS.length && ipDone ? "#34d399" : "#a1a1aa",
              }}
            >
              {passedCount === CHECKS.length && ipDone ? "All checks passed" : "Running checks…"}
            </motion.span>
          </div>
          <div className="mt-2 h-1 overflow-hidden rounded-full bg-zinc-800">
            <motion.div
              className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-emerald-500"
              animate={{
                width: `${((passedCount + (ipDone ? 1 : 0)) / (CHECKS.length + 1)) * 100}%`,
              }}
              transition={{ duration: 0.4 }}
            />
          </div>
        </div>
      </motion.div>
    </div>
  );
}
