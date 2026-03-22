"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
import type { PipelineNodeData } from "./pipelineData";

const STATUS_BADGE = {
  idle: { label: "Idle", className: "bg-zinc-800 text-zinc-400" },
  running: { label: "Running", className: "bg-indigo-950 text-indigo-300" },
  success: { label: "Success", className: "bg-emerald-950 text-emerald-400" },
  failed: { label: "Failed", className: "bg-red-950 text-red-400" },
};

interface Props {
  node: PipelineNodeData | null;
  onClose: () => void;
}

export default function InspectorPanel({ node, onClose }: Props) {
  const [visibleLogs, setVisibleLogs] = useState<string[]>([]);
  const logsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!node) {
      setVisibleLogs([]);
      return;
    }

    setVisibleLogs([]);
    const timers: ReturnType<typeof setTimeout>[] = [];

    node.logs.forEach((log, i) => {
      const timer = setTimeout(() => {
        setVisibleLogs((prev) => [...prev, log]);
      }, i * 350);
      timers.push(timer);
    });

    return () => timers.forEach(clearTimeout);
  }, [node]);

  useEffect(() => {
    if (logsRef.current) {
      logsRef.current.scrollTop = logsRef.current.scrollHeight;
    }
  }, [visibleLogs]);

  return (
    <AnimatePresence>
      {node && (
        <motion.div
          className="flex h-full w-full flex-col overflow-hidden rounded-2xl border border-zinc-800/60 bg-zinc-950/80 backdrop-blur-xl lg:w-80"
          initial={{ x: 80, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 80, opacity: 0 }}
          transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
        >
          <div className="flex items-center justify-between border-b border-zinc-800/60 px-4 py-3">
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-indigo-500" />
              <span className="text-sm font-semibold text-zinc-200">
                {node.label}
              </span>
            </div>
            <button
              onClick={onClose}
              className="flex h-7 w-7 items-center justify-center rounded-lg text-zinc-500 transition-colors hover:bg-zinc-800 hover:text-zinc-300"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>

          <div className="space-y-3 border-b border-zinc-800/60 px-4 py-3">
            <div>
              <div className="text-[10px] uppercase tracking-wider text-zinc-600">
                Status
              </div>
              <div className="mt-1">
                <span
                  className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold ${STATUS_BADGE[node.status].className}`}
                >
                  {STATUS_BADGE[node.status].label}
                </span>
              </div>
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wider text-zinc-600">
                Duration
              </div>
              <div className="mt-0.5 font-mono text-xs text-zinc-300">
                {node.duration || "—"}
              </div>
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wider text-zinc-600">
                Description
              </div>
              <div className="mt-0.5 text-xs leading-relaxed text-zinc-400">
                {node.description}
              </div>
            </div>
          </div>

          <div className="flex min-h-0 flex-1 flex-col px-4 py-3">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-[10px] uppercase tracking-wider text-zinc-600">
                Logs
              </span>
              <span className="text-[9px] font-mono text-zinc-600">
                {visibleLogs.length}/{node.logs.length}
              </span>
            </div>
            <div
              ref={logsRef}
              className="flex-1 overflow-y-auto rounded-lg bg-black/40 p-3 font-mono text-[11px] leading-relaxed"
            >
              {visibleLogs.map((log, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.15 }}
                  className="text-zinc-400"
                >
                  <span className="mr-2 text-zinc-700">{String(i + 1).padStart(2, "0")}</span>
                  <span className={log.includes("✓") ? "text-emerald-400" : ""}>{log}</span>
                </motion.div>
              ))}
              {visibleLogs.length < node.logs.length && (
                <motion.span
                  className="inline-block h-3 w-1.5 bg-indigo-500"
                  animate={{ opacity: [1, 0] }}
                  transition={{ duration: 0.6, repeat: Infinity }}
                />
              )}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
