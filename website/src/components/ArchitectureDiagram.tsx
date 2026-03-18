"use client";

import { motion } from "framer-motion";
import { ARCHITECTURE_NODES } from "@/lib/constants";

export default function ArchitectureDiagram() {
  return (
    <motion.div
      className="overflow-x-auto rounded-xl border border-zinc-800 bg-zinc-900/40 p-6 sm:p-8"
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.5 }}
    >
      <div className="flex min-w-[700px] items-center justify-between gap-1">
        {ARCHITECTURE_NODES.map((node, i) => (
          <div key={node.id} className="flex items-center">
            <motion.div
              className="group relative flex flex-col items-center"
              initial={{ opacity: 0, scale: 0.8 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.3, delay: i * 0.06 }}
            >
              <div className={`flex h-12 w-12 items-center justify-center rounded-xl border transition-all sm:h-14 sm:w-14 ${
                i === 0 || i === ARCHITECTURE_NODES.length - 1
                  ? "border-indigo-600/50 bg-indigo-600/20"
                  : "border-zinc-700 bg-zinc-800/80 group-hover:border-indigo-600/40 group-hover:bg-indigo-600/10"
              }`}>
                <span className="text-[10px] font-bold text-indigo-400 sm:text-xs">
                  {i === 0 ? "IN" : i === ARCHITECTURE_NODES.length - 1 ? "OUT" : String(i).padStart(2, "0")}
                </span>
              </div>
              <p className="mt-2 text-center text-[10px] font-semibold text-zinc-300 sm:text-xs">
                {node.label}
              </p>
              <p className="text-center text-[9px] text-zinc-600 sm:text-[10px]">
                {node.description}
              </p>
            </motion.div>
            {i < ARCHITECTURE_NODES.length - 1 && (
              <motion.div
                className="mx-1 h-px w-4 bg-gradient-to-r from-zinc-700 to-indigo-800/40 sm:w-6"
                initial={{ scaleX: 0 }}
                whileInView={{ scaleX: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.2, delay: i * 0.06 + 0.1 }}
              />
            )}
          </div>
        ))}
      </div>
    </motion.div>
  );
}
