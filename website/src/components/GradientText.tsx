"use client";

import { motion } from "framer-motion";

interface GradientTextProps {
  text: string;
  className?: string;
}

export default function GradientText({ text, className = "" }: GradientTextProps) {
  return (
    <motion.span
      className={`bg-gradient-to-r from-indigo-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent ${className}`}
      initial={{ backgroundPosition: "0% 50%" }}
      animate={{ backgroundPosition: ["0% 50%", "100% 50%", "0% 50%"] }}
      transition={{ duration: 6, repeat: Infinity, ease: "linear" }}
      style={{ backgroundSize: "200% 200%" }}
    >
      {text}
    </motion.span>
  );
}
