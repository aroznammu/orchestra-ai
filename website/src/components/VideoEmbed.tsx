"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Play } from "lucide-react";

interface VideoEmbedProps {
  src?: string;
  poster?: string;
}

export default function VideoEmbed({
  src,
  poster,
}: VideoEmbedProps) {
  const [playing, setPlaying] = useState(false);

  if (!src) {
    return (
      <motion.div
        className="flex aspect-video items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900/60"
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5 }}
      >
        <p className="text-sm text-zinc-600">Video coming soon</p>
      </motion.div>
    );
  }

  return (
    <motion.div
      className="group relative overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900/60 glow-sm"
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5 }}
    >
      <div className="aspect-video">
        {playing ? (
          <video
            src={src}
            poster={poster}
            controls
            autoPlay
            className="h-full w-full object-cover"
          />
        ) : (
          <button
            onClick={() => setPlaying(true)}
            className="relative flex h-full w-full items-center justify-center bg-zinc-950"
          >
            {poster && (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={poster} alt="Video thumbnail" className="absolute inset-0 h-full w-full object-cover opacity-60" />
            )}
            <div className="absolute inset-0 bg-gradient-to-t from-zinc-950/80 to-transparent" />
            <div className="relative z-10 flex h-16 w-16 items-center justify-center rounded-full bg-indigo-600/90 shadow-2xl shadow-indigo-600/30 transition-transform group-hover:scale-110">
              <Play className="h-7 w-7 text-white" fill="white" />
            </div>
          </button>
        )}
      </div>
    </motion.div>
  );
}
