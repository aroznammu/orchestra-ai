"use client";

import { useState, useEffect, useRef } from "react";
import { motion, useInView } from "framer-motion";

const PLATFORMS = [
  { name: "Instagram", color: "#E4405F", abbr: "IG" },
  { name: "TikTok", color: "#00F2EA", abbr: "TT" },
  { name: "YouTube", color: "#FF0000", abbr: "YT" },
  { name: "Twitter / X", color: "#1DA1F2", abbr: "X" },
  { name: "LinkedIn", color: "#0A66C2", abbr: "LI" },
  { name: "Facebook", color: "#1877F2", abbr: "FB" },
];

export default function CrossPlatformScene() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });
  const [activePlatforms, setActivePlatforms] = useState<number[]>([]);

  useEffect(() => {
    if (!isInView) return;
    const timers = PLATFORMS.map((_, i) =>
      setTimeout(() => setActivePlatforms((prev) => [...prev, i]), 800 + i * 600)
    );
    return () => timers.forEach(clearTimeout);
  }, [isInView]);

  return (
    <div ref={ref} className="mx-auto max-w-3xl">
      <motion.div
        className="card-elevated overflow-hidden rounded-2xl p-6 sm:p-8"
        initial={{ opacity: 0, y: 20 }}
        animate={isInView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.5 }}
      >
        <div className="flex flex-col items-center gap-8 sm:flex-row sm:gap-12">
          {/* Hub node */}
          <div className="flex flex-shrink-0 flex-col items-center gap-3">
            <motion.div
              className="relative flex h-20 w-20 items-center justify-center rounded-2xl border border-indigo-500/40 bg-indigo-950/60"
              animate={isInView ? {
                boxShadow: [
                  "0 0 20px rgba(79,70,229,0.2)",
                  "0 0 40px rgba(79,70,229,0.4)",
                  "0 0 20px rgba(79,70,229,0.2)",
                ],
              } : {}}
              transition={{ duration: 3, repeat: Infinity }}
            >
              <span className="text-lg font-bold text-indigo-300">AI</span>
              {activePlatforms.length > 0 && activePlatforms.length < PLATFORMS.length && (
                <motion.div
                  className="absolute -inset-1 rounded-2xl border border-indigo-500/20"
                  animate={{ opacity: [0.3, 0.7, 0.3], scale: [1, 1.05, 1] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                />
              )}
            </motion.div>
            <span className="text-xs font-medium text-zinc-400">OrchestraAI</span>
          </div>

          {/* SVG flow lines + platform nodes */}
          <div className="relative flex-1">
            <svg
              viewBox="0 0 200 240"
              className="absolute left-0 top-0 hidden h-full w-32 sm:block"
              style={{ overflow: "visible" }}
            >
              {PLATFORMS.map((platform, i) => {
                const isActive = activePlatforms.includes(i);
                const y = 20 + i * 40;
                return (
                  <g key={platform.name}>
                    {/* Edge line */}
                    <motion.line
                      x1="0"
                      y1="120"
                      x2="180"
                      y2={y}
                      stroke={isActive ? platform.color : "#3f3f46"}
                      strokeWidth={isActive ? 1.5 : 0.5}
                      strokeDasharray={isActive ? "none" : "4 4"}
                      initial={{ opacity: 0.2 }}
                      animate={{ opacity: isActive ? 0.6 : 0.15 }}
                      transition={{ duration: 0.4 }}
                    />
                    {/* Traveling pulse */}
                    {isActive && (
                      <motion.circle
                        r="3"
                        fill={platform.color}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: [0, 1, 1, 0] }}
                        transition={{ duration: 1.2, repeat: Infinity, repeatDelay: 0.8 }}
                      >
                        <animateMotion
                          dur="1.2s"
                          repeatCount="indefinite"
                          path={`M0,120 L180,${y}`}
                        />
                      </motion.circle>
                    )}
                  </g>
                );
              })}
            </svg>

            {/* Platform cards */}
            <div className="grid grid-cols-2 gap-2 sm:ml-32 sm:grid-cols-2 lg:grid-cols-3">
              {PLATFORMS.map((platform, i) => {
                const isActive = activePlatforms.includes(i);
                return (
                  <motion.div
                    key={platform.name}
                    className="flex items-center gap-2 rounded-lg border px-3 py-2.5"
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={isInView ? {
                      opacity: isActive ? 1 : 0.3,
                      scale: 1,
                      borderColor: isActive ? `${platform.color}40` : "rgba(63,63,70,0.3)",
                      boxShadow: isActive ? `0 0 16px ${platform.color}15` : "none",
                    } : {}}
                    transition={{ duration: 0.4, delay: i * 0.08 }}
                  >
                    <motion.div
                      className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-md text-[10px] font-bold"
                      style={{
                        backgroundColor: isActive ? `${platform.color}20` : "rgba(39,39,42,0.6)",
                        color: isActive ? platform.color : "#71717a",
                      }}
                      animate={isActive ? { scale: [1, 1.1, 1] } : {}}
                      transition={{ duration: 0.4 }}
                    >
                      {platform.abbr}
                    </motion.div>
                    <div>
                      <div className="text-[11px] font-medium text-zinc-300">{platform.name}</div>
                      <div className="text-[9px] text-zinc-600">
                        {isActive ? "Published" : "Pending"}
                      </div>
                    </div>
                    {isActive && (
                      <motion.div
                        className="ml-auto h-1.5 w-1.5 rounded-full bg-emerald-500"
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: "spring", stiffness: 400, damping: 15 }}
                      />
                    )}
                  </motion.div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Status bar */}
        <div className="mt-6 flex items-center justify-between border-t border-zinc-800/60 pt-4">
          <span className="text-[11px] text-zinc-500">Cross-platform dispatch</span>
          <span className="font-mono text-xs text-zinc-400">
            {activePlatforms.length}/{PLATFORMS.length} platforms
          </span>
        </div>
      </motion.div>
    </div>
  );
}
