"use client";

import { useState, useEffect, useRef } from "react";
import { motion, useInView } from "framer-motion";
import { Pen, ScanSearch, Sparkles } from "lucide-react";

const STEPS = [
  {
    icon: Pen,
    label: "Drafting",
    color: "from-indigo-500 to-indigo-400",
    glow: "rgba(99,102,241,0.4)",
    description: "AI generates platform-optimized copy",
  },
  {
    icon: ScanSearch,
    label: "Reviewing",
    color: "from-purple-500 to-purple-400",
    glow: "rgba(124,58,237,0.4)",
    description: "Compliance & policy validation",
  },
  {
    icon: Sparkles,
    label: "Optimizing",
    color: "from-cyan-500 to-cyan-400",
    glow: "rgba(6,182,212,0.4)",
    description: "Tone, length & hashtag refinement",
  },
];

const AI_TEXT =
  "Launching summer sale campaign across Instagram and TikTok. Generating 2 platform-optimized variants with trend-aware hashtags and budget allocation of $250 per platform...";

export default function ContentCreationScene() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });
  const [activeStep, setActiveStep] = useState(-1);
  const [typedChars, setTypedChars] = useState(0);

  useEffect(() => {
    if (!isInView) return;

    const stepTimers = STEPS.map((_, i) =>
      setTimeout(() => setActiveStep(i), 600 + i * 1400)
    );

    return () => stepTimers.forEach(clearTimeout);
  }, [isInView]);

  useEffect(() => {
    if (activeStep < 0) return;
    setTypedChars(0);
    let i = 0;
    const interval = setInterval(() => {
      i++;
      setTypedChars(i);
      if (i >= AI_TEXT.length) clearInterval(interval);
    }, 18);
    return () => clearInterval(interval);
  }, [activeStep]);

  return (
    <div ref={ref} className="mx-auto max-w-4xl">
      {/* Step indicators */}
      <div className="mb-8 flex items-center justify-center gap-2 sm:gap-4">
        {STEPS.map((step, i) => {
          const Icon = step.icon;
          const isActive = activeStep >= i;
          const isCurrent = activeStep === i;
          return (
            <div key={step.label} className="flex items-center gap-2 sm:gap-4">
              <motion.div
                className="flex items-center gap-2 rounded-full border px-3 py-1.5 sm:px-4 sm:py-2"
                animate={{
                  borderColor: isActive ? "rgba(99,102,241,0.5)" : "rgba(63,63,70,0.4)",
                  backgroundColor: isCurrent ? "rgba(99,102,241,0.1)" : "transparent",
                }}
                transition={{ duration: 0.4 }}
              >
                <motion.div
                  animate={{
                    scale: isCurrent ? [1, 1.2, 1] : 1,
                    opacity: isActive ? 1 : 0.4,
                  }}
                  transition={isCurrent ? { duration: 1.5, repeat: Infinity } : { duration: 0.3 }}
                >
                  <Icon className="h-4 w-4" style={{ color: isActive ? "#818cf8" : "#52525b" }} />
                </motion.div>
                <span className={`text-xs font-medium sm:text-sm ${isActive ? "text-zinc-200" : "text-zinc-600"}`}>
                  {step.label}
                </span>
              </motion.div>

              {i < STEPS.length - 1 && (
                <motion.div
                  className="h-px w-6 sm:w-10"
                  animate={{
                    backgroundColor: activeStep > i ? "rgba(99,102,241,0.5)" : "rgba(63,63,70,0.3)",
                  }}
                  transition={{ duration: 0.4 }}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* AI output panel */}
      <motion.div
        className="card-elevated overflow-hidden rounded-2xl"
        initial={{ opacity: 0, y: 20 }}
        animate={isInView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.5, delay: 0.3 }}
      >
        <div className="border-b border-zinc-800/60 px-5 py-3">
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-indigo-500" />
            <span className="text-xs font-medium text-zinc-400">AI Content Engine</span>
            {activeStep >= 0 && (
              <motion.span
                className="ml-auto rounded-full bg-indigo-950/80 px-2 py-0.5 text-[10px] font-medium text-indigo-300"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
              >
                {STEPS[Math.min(activeStep, STEPS.length - 1)].label}...
              </motion.span>
            )}
          </div>
        </div>

        <div className="p-5">
          <div className="min-h-[120px] rounded-lg border border-zinc-800/40 bg-zinc-950/60 p-4 font-mono text-sm leading-relaxed">
            {activeStep >= 0 ? (
              <>
                <span className="text-zinc-300">{AI_TEXT.slice(0, typedChars)}</span>
                {typedChars < AI_TEXT.length && (
                  <motion.span
                    className="inline-block h-4 w-0.5 translate-y-0.5 bg-indigo-500"
                    animate={{ opacity: [1, 0] }}
                    transition={{ duration: 0.5, repeat: Infinity }}
                  />
                )}
              </>
            ) : (
              <span className="text-zinc-700">Waiting for command...</span>
            )}
          </div>

          {/* Step detail cards */}
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            {STEPS.map((step, i) => {
              const isActive = activeStep >= i;
              const isDone = activeStep > i;
              return (
                <motion.div
                  key={step.label}
                  className="rounded-lg border p-3"
                  initial={{ opacity: 0, x: -16 }}
                  animate={isInView ? {
                    opacity: isActive ? 1 : 0.3,
                    x: 0,
                    borderColor: isActive ? "rgba(99,102,241,0.3)" : "rgba(63,63,70,0.3)",
                  } : {}}
                  transition={{ duration: 0.4, delay: 0.5 + i * 0.15 }}
                >
                  <div className="flex items-center gap-2">
                    <div className={`h-1.5 w-1.5 rounded-full ${isDone ? "bg-emerald-500" : isActive ? "bg-indigo-500" : "bg-zinc-700"}`} />
                    <span className="text-xs font-medium text-zinc-300">{step.label}</span>
                  </div>
                  <p className="mt-1 text-[11px] text-zinc-500">{step.description}</p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </motion.div>
    </div>
  );
}
