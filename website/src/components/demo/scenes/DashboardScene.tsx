"use client";

import { useRef } from "react";
import { motion, useScroll, useTransform, useInView } from "framer-motion";
import BrowserMockup from "@/components/BrowserMockup";

const CALLOUTS = [
  { label: "Live Agent Pipeline", x: "right-2", y: "top-[45%]", delay: 1.0 },
  { label: "Cross-Platform Analytics", x: "left-[10%]", y: "top-[38%]", delay: 1.4 },
  { label: "Real-time Throughput", x: "right-2", y: "bottom-[18%]", delay: 1.8 },
];

export default function DashboardScene() {
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true, margin: "-100px" });

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"],
  });

  const scale = useTransform(scrollYProgress, [0, 0.5], [0.92, 1]);
  const y = useTransform(scrollYProgress, [0, 0.5], [30, 0]);

  return (
    <div ref={containerRef} className="mx-auto max-w-5xl">
      <motion.div style={{ scale, y }} className="relative">
        <BrowserMockup />

        {/* Annotation callouts */}
        {CALLOUTS.map((callout) => (
          <motion.div
            key={callout.label}
            className={`absolute ${callout.x} ${callout.y} z-20 hidden lg:block`}
            initial={{ opacity: 0, x: 20 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.5, delay: callout.delay }}
          >
            <div className="flex items-center gap-2">
              <div className="h-px w-6 bg-gradient-to-r from-indigo-500/60 to-transparent" />
              <div className="rounded-full border border-indigo-500/30 bg-indigo-950/80 px-3 py-1 backdrop-blur-md">
                <span className="text-[10px] font-medium text-indigo-300">{callout.label}</span>
              </div>
            </div>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
