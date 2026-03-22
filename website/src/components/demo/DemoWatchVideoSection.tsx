"use client";

import { motion } from "framer-motion";
import { Play } from "lucide-react";
import { useState } from "react";

const DEMO_VIDEO = "/orchestraai_demo.mp4";

export default function DemoWatchVideoSection() {
  const [active, setActive] = useState(false);

  return (
    <section
      id="demo-overview-video"
      className="relative scroll-mt-24 px-6 py-16 sm:py-20"
      aria-labelledby="demo-watch-heading"
    >
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-transparent via-indigo-950/[0.06] to-transparent" />
      <div className="relative mx-auto max-w-3xl text-center">
        <motion.h2
          id="demo-watch-heading"
          className="text-2xl font-extrabold tracking-tight text-zinc-50 sm:text-3xl"
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.45 }}
        >
          Rather just watch? See OrchestraAI in action in 90 seconds.
        </motion.h2>
        <motion.p
          className="mx-auto mt-3 max-w-lg text-sm text-zinc-500"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4, delay: 0.05 }}
        >
          Watch a full walkthrough of the OrchestraAI pipeline — from natural
          language command to live campaign in under 90 seconds.
        </motion.p>

        <motion.div
          className="mx-auto mt-10 max-w-2xl"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.08 }}
        >
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-3 shadow-2xl shadow-indigo-950/20 backdrop-blur-xl">
            <div className="relative aspect-video overflow-hidden rounded-xl border border-zinc-800/60 bg-zinc-950">
              {!active ? (
                <button
                  type="button"
                  onClick={() => setActive(true)}
                  className="group absolute inset-0 flex flex-col items-center justify-center gap-3 bg-zinc-950/90 transition hover:bg-zinc-950/80"
                >
                  <span className="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-indigo-600 to-purple-600 text-white shadow-lg shadow-indigo-900/40 transition group-hover:scale-105">
                    <Play className="h-7 w-7 translate-x-0.5" fill="currentColor" />
                  </span>
                  <span className="text-sm font-medium text-zinc-300">Play overview</span>
                </button>
              ) : (
                <video
                  className="h-full w-full object-cover"
                  src={DEMO_VIDEO}
                  controls
                  playsInline
                  autoPlay
                />
              )}
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
