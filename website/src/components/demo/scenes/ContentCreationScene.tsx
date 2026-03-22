"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, useInView } from "framer-motion";
import { Pen, ScanSearch, Sparkles, Clapperboard, Send } from "lucide-react";

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

const EXAMPLE_PROMPT =
  "Generate a 10-second video ad for our Summer Sale, allocate $500, and publish to TikTok and Instagram.";

const AI_TEXT =
  "Launching summer sale campaign across Instagram and TikTok. Generating 2 platform-optimized variants with trend-aware hashtags and budget allocation of $250 per platform. Invoking Seedance 2.0 for a 10s vertical video asset...";

const DEMO_VIDEO_SRC =
  "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4";

type VideoPhase = "idle" | "skeleton" | "ready";

export default function ContentCreationScene() {
  const rootRef = useRef<HTMLDivElement>(null);
  const pipelineRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(rootRef, { once: false, margin: "-80px" });

  const [pipelineStarted, setPipelineStarted] = useState(false);
  const [promptDone, setPromptDone] = useState(false);
  const [typedPromptLen, setTypedPromptLen] = useState(0);
  const [isTypingPrompt, setIsTypingPrompt] = useState(false);
  const [activeStep, setActiveStep] = useState(-1);
  const [typedChars, setTypedChars] = useState(0);
  const [videoPhase, setVideoPhase] = useState<VideoPhase>("idle");

  const runExamplePrompt = useCallback(() => {
    if (isTypingPrompt || promptDone) return;
    setIsTypingPrompt(true);
    setTypedPromptLen(0);
  }, [isTypingPrompt, promptDone]);

  useEffect(() => {
    if (!isTypingPrompt || promptDone) return;
    let i = 0;
    const interval = setInterval(() => {
      i += 1;
      setTypedPromptLen(Math.min(i, EXAMPLE_PROMPT.length));
      if (i >= EXAMPLE_PROMPT.length) {
        clearInterval(interval);
        setIsTypingPrompt(false);
        setPromptDone(true);
        requestAnimationFrame(() => {
          pipelineRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
        });
        setTimeout(() => setPipelineStarted(true), 420);
      }
    }, 22);
    return () => clearInterval(interval);
  }, [isTypingPrompt, promptDone]);

  useEffect(() => {
    if (!pipelineStarted) return;
    const stepTimers = STEPS.map((_, idx) =>
      setTimeout(() => setActiveStep(idx), 500 + idx * 1200)
    );
    return () => stepTimers.forEach(clearTimeout);
  }, [pipelineStarted]);

  useEffect(() => {
    if (activeStep < 0) return;
    setTypedChars(0);
    let i = 0;
    const interval = setInterval(() => {
      i += 1;
      setTypedChars(i);
      if (i >= AI_TEXT.length) clearInterval(interval);
    }, 16);
    return () => clearInterval(interval);
  }, [activeStep]);

  useEffect(() => {
    if (!pipelineStarted || activeStep < 1) {
      setVideoPhase("idle");
      return;
    }
    setVideoPhase("skeleton");
    const t = setTimeout(() => setVideoPhase("ready"), 1600);
    return () => clearTimeout(t);
  }, [pipelineStarted, activeStep]);

  return (
    <div ref={rootRef} className="mx-auto max-w-4xl">
      {/* Mock command input — walkthrough trigger */}
      <motion.div
        className="mb-8 rounded-2xl border border-zinc-800/60 bg-zinc-950/40 p-4 backdrop-blur-sm"
        initial={{ opacity: 0, y: 12 }}
        animate={isInView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.45 }}
      >
        <div className="mb-2 flex items-center justify-between gap-3">
          <span className="text-xs font-medium text-zinc-400">Orchestrator command</span>
          <span className="rounded-md bg-indigo-950/70 px-2 py-0.5 text-[10px] font-medium text-indigo-300">
            Seedance 2.0 enabled
          </span>
        </div>
        <div className="flex min-h-[52px] items-start gap-2 rounded-xl border border-zinc-800/50 bg-zinc-900/80 px-3 py-3 font-mono text-sm text-zinc-200">
          <Send className="mt-0.5 h-4 w-4 shrink-0 text-zinc-600" />
          <div className="min-h-[1.25rem] flex-1 leading-relaxed">
            {typedPromptLen > 0 ? (
              <>
                <span>{EXAMPLE_PROMPT.slice(0, typedPromptLen)}</span>
                {isTypingPrompt && (
                  <motion.span
                    className="ml-0.5 inline-block h-4 w-0.5 translate-y-0.5 bg-indigo-400"
                    animate={{ opacity: [1, 0] }}
                    transition={{ duration: 0.45, repeat: Infinity }}
                  />
                )}
              </>
            ) : (
              <span className="text-zinc-600">Waiting for command…</span>
            )}
          </div>
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={runExamplePrompt}
            disabled={isTypingPrompt || promptDone}
            className="rounded-full bg-gradient-to-r from-indigo-600 to-purple-600 px-4 py-2 text-xs font-semibold text-white shadow-md shadow-indigo-900/30 transition hover:from-indigo-500 hover:to-purple-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Try an example prompt
          </button>
          {!promptDone && (
            <span className="text-[11px] text-zinc-500">
              Simulates a full pipeline run including video generation.
            </span>
          )}
        </div>
      </motion.div>

      <div ref={pipelineRef} id="demo-step-1-panel" className="scroll-mt-28">
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
          transition={{ duration: 0.5, delay: 0.15 }}
        >
          <div className="border-b border-zinc-800/60 px-5 py-3">
            <div className="flex flex-wrap items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-indigo-500" />
              <span className="text-xs font-medium text-zinc-400">AI content engine</span>
              {activeStep >= 0 && (
                <motion.span
                  className="ml-auto rounded-full bg-indigo-950/80 px-2 py-0.5 text-[10px] font-medium text-indigo-300"
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                >
                  {STEPS[Math.min(activeStep, STEPS.length - 1)].label}…
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
                <span className="text-zinc-600">
                  Run an example prompt above to start the pipeline.
                </span>
              )}
            </div>

            {/* Seedance 2.0 video block */}
            <motion.div
              className="mt-4 overflow-hidden rounded-xl border border-violet-800/40 bg-gradient-to-br from-violet-950/30 to-zinc-950/60"
              initial={false}
              animate={{
                opacity: activeStep >= 1 ? 1 : 0.35,
              }}
              transition={{ duration: 0.35 }}
            >
              <div className="flex items-center gap-2 border-b border-zinc-800/50 px-4 py-2.5">
                <Clapperboard className="h-4 w-4 text-violet-400" />
                <span className="text-xs font-semibold text-zinc-200">Video generation (Seedance 2.0)</span>
                <span className="ml-auto rounded-full bg-violet-950/80 px-2 py-0.5 text-[9px] font-medium text-violet-300">
                  10s vertical · TikTok / Reels
                </span>
              </div>
              <div className="relative aspect-video w-full bg-zinc-950/80 sm:aspect-[16/9]">
                {videoPhase === "idle" && (
                  <div className="flex h-full min-h-[160px] items-center justify-center text-xs text-zinc-600">
                    Awaiting copy pass…
                  </div>
                )}
                {videoPhase === "skeleton" && (
                  <div className="absolute inset-0 flex flex-col gap-2 p-4">
                    <motion.div
                      className="h-full rounded-lg bg-zinc-800/60"
                      animate={{ opacity: [0.5, 1, 0.5] }}
                      transition={{ duration: 1.2, repeat: Infinity }}
                    />
                    <div className="flex gap-2">
                      <div className="h-2 flex-1 rounded bg-zinc-800/50" />
                      <div className="h-2 w-20 rounded bg-zinc-800/50" />
                    </div>
                  </div>
                )}
                {videoPhase === "ready" && (
                  <motion.div
                    className="h-full w-full"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.5 }}
                  >
                    <video
                      className="h-full w-full object-cover"
                      src={DEMO_VIDEO_SRC}
                      controls
                      playsInline
                      muted
                      loop
                    />
                  </motion.div>
                )}
              </div>
            </motion.div>

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
                    animate={
                      isInView
                        ? {
                            opacity: isActive ? 1 : 0.3,
                            x: 0,
                            borderColor: isActive ? "rgba(99,102,241,0.3)" : "rgba(63,63,70,0.3)",
                          }
                        : {}
                    }
                    transition={{ duration: 0.4, delay: 0.35 + i * 0.12 }}
                  >
                    <div className="flex items-center gap-2">
                      <div
                        className={`h-1.5 w-1.5 rounded-full ${
                          isDone ? "bg-emerald-500" : isActive ? "bg-indigo-500" : "bg-zinc-700"
                        }`}
                      />
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
    </div>
  );
}
