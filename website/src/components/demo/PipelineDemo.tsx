"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import PipelineCanvas from "./PipelineCanvas";
import InspectorPanel from "./InspectorPanel";
import useIs3DCapable from "./useIs3DCapable";
import type { PipelineNodeData } from "./pipelineData";

const GraphCanvas3D = dynamic(() => import("./GraphCanvas3D"), {
  ssr: false,
  loading: () => <LoadingSkeleton />,
});

function LoadingSkeleton() {
  return (
    <div className="flex h-[320px] w-full items-center justify-center rounded-2xl border border-zinc-800/40 bg-zinc-950/60 sm:h-[400px]">
      <div className="flex flex-col items-center gap-3">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500/30 border-t-indigo-500" />
        <span className="text-xs text-zinc-600">Loading 3D scene...</span>
      </div>
    </div>
  );
}

export default function PipelineDemo() {
  const [selectedNode, setSelectedNode] = useState<PipelineNodeData | null>(null);
  const is3D = useIs3DCapable();

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
          {is3D ? (
            <GraphCanvas3D onNodeClick={setSelectedNode} />
          ) : (
            <PipelineCanvas onNodeClick={setSelectedNode} />
          )}
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
        {is3D ? "Drag to orbit. Click any node to inspect." : "Click any node to inspect logs and details"}
      </p>
    </motion.div>
  );
}
