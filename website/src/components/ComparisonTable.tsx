"use client";

import { motion } from "framer-motion";
import { Check, X, ChevronsRight } from "lucide-react";
import { COMPARISON_DATA } from "@/lib/constants";

function Cell({ value }: { value: boolean }) {
  return value ? (
    <Check className="mx-auto h-5 w-5 text-emerald-400" />
  ) : (
    <X className="mx-auto h-5 w-5 text-zinc-700" />
  );
}

export default function ComparisonTable() {
  return (
    <div>
      {/* Mobile scroll hint */}
      <p className="mb-2 flex items-center gap-1 text-xs text-zinc-600 sm:hidden">
        <ChevronsRight className="h-3 w-3" /> Scroll to compare
      </p>
      <motion.div
        className="-mx-4 overflow-x-auto rounded-xl border border-zinc-800 bg-zinc-900/40 px-0 sm:mx-0"
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-60px" }}
        transition={{ duration: 0.5 }}
      >
        <table className="w-full min-w-[600px] text-sm">
          <thead>
            <tr className="border-b border-zinc-800">
              <th className="px-4 py-4 text-left font-medium text-zinc-400 sm:px-6">Capability</th>
              <th className="px-3 py-4 text-center font-semibold text-indigo-400 sm:px-4">OrchestraAI</th>
              <th className="px-3 py-4 text-center font-medium text-zinc-400 sm:px-4">Hootsuite</th>
              <th className="px-3 py-4 text-center font-medium text-zinc-400 sm:px-4">Buffer</th>
              <th className="px-3 py-4 text-center font-medium text-zinc-400 sm:px-4">DIY Scripts</th>
            </tr>
          </thead>
          <tbody>
            {COMPARISON_DATA.map((row, i) => (
              <motion.tr
                key={row.capability}
                className="border-b border-zinc-800/60 transition-colors hover:bg-zinc-800/20"
                initial={{ opacity: 0, x: -8 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.3, delay: i * 0.03 }}
              >
                <td className="px-4 py-3.5 text-zinc-300 sm:px-6">{row.capability}</td>
                <td className="px-3 py-3.5 sm:px-4"><Cell value={row.orchestra} /></td>
                <td className="px-3 py-3.5 sm:px-4"><Cell value={row.hootsuite} /></td>
                <td className="px-3 py-3.5 sm:px-4"><Cell value={row.buffer} /></td>
                <td className="px-3 py-3.5 sm:px-4"><Cell value={row.diy} /></td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </motion.div>
    </div>
  );
}
