"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import PipelineCanvas from "./PipelineCanvas";
import InspectorPanel from "./InspectorPanel";
import OrbitalAccent from "./OrbitalAccent";
import type { PipelineNodeData } from "./PipelineCanvas";

export default function PipelineDemo() {
  const [selectedNode, setSelectedNode] = useState<PipelineNodeData | null>(null);

  return (
    <motion.div
      className="relative"
      initial={{ opacity: 0, y: 32 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.6 }}
    >
      <div className="flex flex-col gap-4 lg:flex-row">
        <div className="relative min-w-0 flex-1">
          <PipelineCanvas onNodeClick={setSelectedNode} />
          <OrbitalAccent />
        </div>

        <div className={`transition-all duration-300 ${selectedNode ? "h-80 lg:h-auto" : "h-0 overflow-hidden lg:h-auto lg:w-0"}`}>
          <InspectorPanel
            node={selectedNode}
            onClose={() => setSelectedNode(null)}
          />
        </div>
      </div>

      <div className="mt-4 flex items-center justify-center gap-6 text-[10px] text-zinc-600">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-zinc-700" /> Idle
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-indigo-500 shadow-[0_0_6px_rgba(79,70,229,0.5)]" /> Running
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-emerald-500" /> Success
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-red-500" /> Failed
        </span>
      </div>
      <p className="mt-2 text-center text-[10px] text-zinc-700">
        Click any node to inspect logs and details
      </p>
    </motion.div>
  );
}
