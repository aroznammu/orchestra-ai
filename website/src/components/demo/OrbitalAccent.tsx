"use client";

import { motion } from "framer-motion";

const ORBITALS = [
  { size: 6, radius: 40, duration: 6, color: "bg-indigo-500", delay: 0 },
  { size: 5, radius: 55, duration: 8, color: "bg-purple-500", delay: 2 },
  { size: 4, radius: 35, duration: 10, color: "bg-cyan-500", delay: 4 },
  { size: 5, radius: 48, duration: 7, color: "bg-violet-400", delay: 1 },
];

export default function OrbitalAccent() {
  return (
    <div className="pointer-events-none absolute -right-8 top-1/2 hidden h-40 w-40 -translate-y-1/2 lg:block">
      <div className="relative h-full w-full">
        {/* Center node */}
        <motion.div
          className="absolute left-1/2 top-1/2 flex h-10 w-10 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-indigo-500/30 bg-indigo-950/60"
          animate={{
            boxShadow: [
              "0 0 20px rgba(79,70,229,0.2)",
              "0 0 40px rgba(79,70,229,0.5)",
              "0 0 20px rgba(79,70,229,0.2)",
            ],
          }}
          transition={{ duration: 3, repeat: Infinity }}
        >
          <span className="text-[10px] font-bold text-indigo-300">AI</span>
        </motion.div>

        {ORBITALS.map((orb, i) => (
          <motion.div
            key={i}
            className="absolute left-1/2 top-1/2"
            style={{
              width: orb.size,
              height: orb.size,
            }}
            animate={{
              x: [
                orb.radius * Math.cos(0) - orb.size / 2,
                orb.radius * Math.cos(Math.PI / 2) - orb.size / 2,
                orb.radius * Math.cos(Math.PI) - orb.size / 2,
                orb.radius * Math.cos((3 * Math.PI) / 2) - orb.size / 2,
                orb.radius * Math.cos(2 * Math.PI) - orb.size / 2,
              ],
              y: [
                orb.radius * Math.sin(0) * 0.6 - orb.size / 2,
                orb.radius * Math.sin(Math.PI / 2) * 0.6 - orb.size / 2,
                orb.radius * Math.sin(Math.PI) * 0.6 - orb.size / 2,
                orb.radius * Math.sin((3 * Math.PI) / 2) * 0.6 - orb.size / 2,
                orb.radius * Math.sin(2 * Math.PI) * 0.6 - orb.size / 2,
              ],
              opacity: [0.4, 0.8, 0.4, 0.8, 0.4],
            }}
            transition={{
              duration: orb.duration,
              repeat: Infinity,
              ease: "linear",
              delay: orb.delay,
            }}
          >
            <div
              className={`h-full w-full rounded-full ${orb.color}`}
              style={{
                boxShadow: `0 0 8px currentColor`,
              }}
            />
          </motion.div>
        ))}

        {/* Orbital ring hints */}
        <div className="absolute left-1/2 top-1/2 h-20 w-24 -translate-x-1/2 -translate-y-1/2 rounded-full border border-indigo-500/[0.08]" />
        <div className="absolute left-1/2 top-1/2 h-28 w-32 -translate-x-1/2 -translate-y-1/2 rounded-full border border-purple-500/[0.06]" />
      </div>
    </div>
  );
}
