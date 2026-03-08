"use client";

import { motion } from "framer-motion";
import { PLATFORMS } from "@/lib/constants";

export default function PlatformGrid() {
  return (
    <div className="flex flex-wrap items-center justify-center gap-4 sm:gap-6">
      {PLATFORMS.map((name, i) => (
        <motion.div
          key={name}
          className="flex items-center gap-2 rounded-full border border-zinc-800 bg-zinc-900/60 px-4 py-2 text-sm text-zinc-300"
          initial={{ opacity: 0, scale: 0.9 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.3, delay: i * 0.05 }}
          whileHover={{ borderColor: "rgb(99 102 241 / 0.5)" }}
        >
          <span className="h-2 w-2 rounded-full bg-indigo-500" />
          {name}
        </motion.div>
      ))}
    </div>
  );
}
