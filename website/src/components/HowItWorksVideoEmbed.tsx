"use client";

import { motion } from "framer-motion";
import { Play } from "lucide-react";
import { useState } from "react";

const DEMO_CLIP =
  "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4";

export default function HowItWorksVideoEmbed() {
  const [playing, setPlaying] = useState(false);

  return (
    <motion.div
      className="mx-auto mt-14 max-w-3xl"
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.5 }}
    >
      <p className="mb-4 text-center text-lg font-semibold leading-snug text-zinc-100 sm:text-xl">
        See the AI pause a bleeding campaign in 90 seconds.
      </p>
      <div className="rounded-3xl border border-white/[0.08] bg-gradient-to-b from-white/[0.06] to-transparent p-4 shadow-[0_0_0_1px_rgba(255,255,255,0.04)_inset] backdrop-blur-xl sm:p-5">
        <div className="relative aspect-video overflow-hidden rounded-2xl border border-zinc-800/70 bg-zinc-950 shadow-2xl shadow-black/40">
          {!playing ? (
            <button
              type="button"
              onClick={() => setPlaying(true)}
              className="group absolute inset-0 flex flex-col items-center justify-center gap-4 bg-zinc-950/85 transition hover:bg-zinc-950/75"
            >
              <span className="relative flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-xl shadow-indigo-900/50 ring-4 ring-indigo-500/20 transition group-hover:scale-105">
                <Play className="h-9 w-9 translate-x-1" fill="currentColor" />
              </span>
              <span className="text-sm font-medium text-zinc-300">Watch demo</span>
            </button>
          ) : (
            <video
              className="h-full w-full object-cover"
              src={DEMO_CLIP}
              controls
              playsInline
              autoPlay
            />
          )}
        </div>
        <p className="mt-3 text-center text-xs text-zinc-600">
          Placeholder clip — swap for your narrated product recording anytime.
        </p>
      </div>
    </motion.div>
  );
}
