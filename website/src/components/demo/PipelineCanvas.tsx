"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";

export interface PipelineNodeData {
  id: string;
  label: string;
  description: string;
  x: number;
  y: number;
  status: "idle" | "running" | "success" | "failed";
  duration?: string;
  logs: string[];
}

const INITIAL_NODES: PipelineNodeData[] = [
  { id: "classify", label: "Classify", description: "LLM intent classification with fallback chain", x: 5, y: 30, status: "idle", duration: "12ms", logs: ["Received user prompt", "Routing to OpenAI gpt-4o-mini", "Intent: campaign_launch", "Depth: deep, Agent: orchestrator"] },
  { id: "compliance", label: "Compliance", description: "Pre-action regulatory and budget checks", x: 18, y: 65, status: "idle", duration: "8ms", logs: ["Checking prohibited content rules", "Budget validation: $500 within daily cap", "Targeting rules: compliant", "All compliance gates passed ✓"] },
  { id: "content", label: "Content", description: "Multi-provider LLM content generation", x: 31, y: 25, status: "idle", duration: "340ms", logs: ["Generating ad copy for Instagram", "Generating ad copy for TikTok", "Adapting tone for each platform", "Content generated: 2 variants per platform"] },
  { id: "video", label: "Video", description: "Seedance 2.0 text-to-video generation", x: 44, y: 70, status: "idle", duration: "1.2s", logs: ["Initializing Seedance 2.0 via fal.ai", "Generating 5s clip from prompt", "Resolution: 720p, Cost: $0.26", "Video generated successfully"] },
  { id: "vision", label: "Vision Gate", description: "GPT-4o Vision IP compliance scanning", x: 57, y: 30, status: "idle", duration: "420ms", logs: ["Extracting keyframes (5 frames)", "Scanning for celebrity likenesses", "Scanning for copyrighted content", "Scanning for trademarked logos", "All frames cleared ✓"] },
  { id: "policy", label: "Policy", description: "Platform-specific rules enforcement", x: 70, y: 65, status: "idle", duration: "15ms", logs: ["Instagram: character limit OK", "Instagram: hashtag count OK", "TikTok: video duration OK", "TikTok: music policy compliant"] },
  { id: "publish", label: "Publish", description: "Multi-platform dispatch with retry", x: 83, y: 25, status: "idle", duration: "890ms", logs: ["Publishing to Instagram...", "Instagram: POST 201 Created", "Publishing to TikTok...", "TikTok: POST 201 Created", "2/2 platforms published ✓"] },
  { id: "analytics", label: "Analytics", description: "Cross-platform metrics collection", x: 92, y: 60, status: "idle", duration: "45ms", logs: ["Collecting baseline metrics", "Registering campaign for tracking", "Setting up ROI normalization", "Analytics pipeline active"] },
];

const EDGES: [number, number][] = [
  [0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7],
];

const STATUS_COLORS = {
  idle: { bg: "bg-zinc-800/80", border: "border-zinc-700/60", text: "text-zinc-500" },
  running: { bg: "bg-indigo-950/80", border: "border-indigo-500/50", text: "text-indigo-300" },
  success: { bg: "bg-emerald-950/60", border: "border-emerald-500/40", text: "text-emerald-400" },
  failed: { bg: "bg-red-950/60", border: "border-red-500/40", text: "text-red-400" },
};

const GLOW_SHADOWS = {
  idle: "none",
  running: "0 0 20px rgba(79,70,229,0.4), 0 0 40px rgba(79,70,229,0.15)",
  success: "0 0 16px rgba(16,185,129,0.3)",
  failed: "0 0 16px rgba(239,68,68,0.3)",
};

interface Props {
  onNodeClick: (node: PipelineNodeData) => void;
}

export default function PipelineCanvas({ onNodeClick }: Props) {
  const [nodes, setNodes] = useState<PipelineNodeData[]>(INITIAL_NODES);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [hasRun, setHasRun] = useState(false);

  const runSimulation = useCallback(() => {
    if (hasRun) return;
    setHasRun(true);

    nodes.forEach((_, i) => {
      setTimeout(() => {
        setNodes((prev) =>
          prev.map((n, j) =>
            j === i ? { ...n, status: "running" as const } : n
          )
        );
      }, i * 600);

      setTimeout(() => {
        setNodes((prev) =>
          prev.map((n, j) =>
            j === i ? { ...n, status: "success" as const } : n
          )
        );
      }, i * 600 + 500);
    });
  }, [hasRun, nodes.length]);

  useEffect(() => {
    const timer = setTimeout(runSimulation, 800);
    return () => clearTimeout(timer);
  }, [runSimulation]);

  return (
    <div className="pipeline-canvas relative h-[320px] w-full overflow-hidden rounded-2xl border border-zinc-800/40 bg-zinc-950/60 backdrop-blur-sm sm:h-[360px]">
      <div className="pointer-events-none absolute inset-0 radial-glow opacity-30" />

      <svg className="absolute inset-0 h-full w-full" xmlns="http://www.w3.org/2000/svg">
        {EDGES.map(([from, to], i) => {
          const n1 = nodes[from];
          const n2 = nodes[to];
          const fromStatus = n1.status;
          const toStatus = n2.status;
          const isActive = fromStatus === "success" && (toStatus === "running" || toStatus === "success");
          return (
            <g key={i}>
              <line
                x1={`${n1.x + 3}%`}
                y1={`${n1.y}%`}
                x2={`${n2.x + 3}%`}
                y2={`${n2.y}%`}
                stroke={isActive ? "rgba(99,102,241,0.4)" : "rgba(63,63,70,0.3)"}
                strokeWidth={isActive ? 2 : 1}
                strokeDasharray={isActive ? "none" : "4 4"}
                className="transition-all duration-500"
              />
              {isActive && (
                <circle r="3" fill="rgba(99,102,241,0.9)">
                  <animateMotion
                    dur="1.5s"
                    repeatCount="indefinite"
                    path={`M${(n1.x + 3) * 10},${n1.y * 3.6} L${(n2.x + 3) * 10},${n2.y * 3.6}`}
                  />
                </circle>
              )}
            </g>
          );
        })}
      </svg>

      {nodes.map((node) => {
        const colors = STATUS_COLORS[node.status];
        return (
          <motion.div
            key={node.id}
            className={`absolute cursor-pointer rounded-xl border px-3 py-2 backdrop-blur-sm transition-colors duration-300 ${colors.bg} ${colors.border}`}
            style={{
              left: `${node.x}%`,
              top: `${node.y}%`,
              transform: "translate(-50%, -50%)",
              boxShadow: GLOW_SHADOWS[node.status],
            }}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{
              opacity: 1,
              scale: hoveredId === node.id ? 1.08 : 1,
            }}
            transition={{ duration: 0.3 }}
            whileHover={{ scale: 1.08 }}
            onClick={() => onNodeClick(node)}
            onMouseEnter={() => setHoveredId(node.id)}
            onMouseLeave={() => setHoveredId(null)}
          >
            {node.status === "running" && (
              <motion.div
                className="absolute -inset-px rounded-xl border border-indigo-500/30"
                animate={{ opacity: [0.3, 0.8, 0.3] }}
                transition={{ duration: 2, repeat: Infinity }}
              />
            )}
            <div className={`text-[11px] font-semibold ${colors.text} sm:text-xs`}>
              {node.label}
            </div>
            <div className="mt-0.5 text-[9px] text-zinc-600">{node.duration}</div>

            <AnimatePresence>
              {hoveredId === node.id && (
                <motion.div
                  className="absolute left-1/2 top-full z-20 mt-2 -translate-x-1/2 whitespace-nowrap rounded-lg border border-zinc-700/60 bg-zinc-900/95 px-3 py-2 text-[10px] backdrop-blur-md"
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -4 }}
                  transition={{ duration: 0.15 }}
                >
                  <div className="font-medium text-zinc-200">{node.label}</div>
                  <div className="mt-0.5 text-zinc-500">{node.description}</div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        );
      })}

      <motion.div
        className="pointer-events-none absolute inset-y-0 w-24 bg-gradient-to-r from-transparent via-indigo-500/[0.07] to-transparent"
        animate={{ left: ["-15%", "115%"] }}
        transition={{ duration: 4, repeat: Infinity, ease: "linear", repeatDelay: 1 }}
      />
    </div>
  );
}
