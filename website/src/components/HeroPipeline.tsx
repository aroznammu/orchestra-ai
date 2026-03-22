"use client";

import { motion } from "framer-motion";

const NODES = [
  { label: "Intent", color: "from-indigo-500 to-indigo-400" },
  { label: "Comply", color: "from-violet-500 to-violet-400" },
  { label: "Content", color: "from-purple-500 to-purple-400" },
  { label: "Video", color: "from-fuchsia-500 to-fuchsia-400" },
  { label: "Vision", color: "from-pink-500 to-pink-400" },
  { label: "Policy", color: "from-rose-500 to-rose-400" },
  { label: "Publish", color: "from-orange-500 to-orange-400" },
  { label: "Analyze", color: "from-amber-500 to-amber-400" },
  { label: "Optimize", color: "from-emerald-500 to-emerald-400" },
  { label: "Respond", color: "from-cyan-500 to-cyan-400" },
];

export default function HeroPipeline() {
  return (
    <div className="relative mx-auto mt-12 max-w-3xl">
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-indigo-600/5 via-purple-600/5 to-cyan-600/5 blur-xl" />

      <div className="relative flex items-center justify-between gap-0.5 overflow-hidden rounded-2xl border border-zinc-800/40 bg-zinc-950/60 px-4 py-4 backdrop-blur-sm sm:gap-1 sm:px-6">
        {/* Traveling pulse */}
        <motion.div
          className="pointer-events-none absolute inset-y-0 w-20 bg-gradient-to-r from-transparent via-indigo-500/20 to-transparent"
          animate={{ left: ["-10%", "110%"] }}
          transition={{ duration: 3, repeat: Infinity, ease: "linear", repeatDelay: 0.5 }}
        />

        {NODES.map((node, i) => (
          <div key={node.label} className="flex items-center">
            <motion.div
              className="relative flex flex-col items-center"
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4, delay: 0.6 + i * 0.07 }}
            >
              <motion.div
                className={`flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br ${node.color} shadow-lg sm:h-9 sm:w-9`}
                whileHover={{ scale: 1.2, y: -2 }}
                transition={{ type: "spring", stiffness: 400, damping: 15 }}
                style={{
                  boxShadow: `0 0 12px -2px var(--tw-gradient-from)`,
                }}
              >
                <span className="text-[8px] font-bold text-white sm:text-[9px]">
                  {i + 1}
                </span>
              </motion.div>
              <span className="mt-1.5 text-[7px] font-medium text-zinc-500 sm:text-[8px]">
                {node.label}
              </span>
            </motion.div>

            {i < NODES.length - 1 && (
              <motion.div
                className="mx-0.5 hidden h-px w-2 bg-gradient-to-r from-zinc-700 to-zinc-800 sm:block md:mx-1 md:w-3"
                initial={{ scaleX: 0 }}
                animate={{ scaleX: 1 }}
                transition={{ duration: 0.3, delay: 0.8 + i * 0.07 }}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
