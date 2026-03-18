"use client";

import { PLATFORMS } from "@/lib/constants";

export default function PlatformGrid() {
  const doubled = [...PLATFORMS, ...PLATFORMS];

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-y-0 left-0 z-10 w-16 bg-gradient-to-r from-zinc-950 to-transparent" />
      <div className="pointer-events-none absolute inset-y-0 right-0 z-10 w-16 bg-gradient-to-l from-zinc-950 to-transparent" />
      <div className="animate-marquee flex w-max gap-4">
        {doubled.map((name, i) => (
          <div
            key={`${name}-${i}`}
            className="flex shrink-0 items-center gap-2 rounded-full border border-zinc-800 bg-zinc-900/60 px-5 py-2.5 text-sm text-zinc-300 transition-colors hover:border-indigo-800/60 hover:text-indigo-300"
          >
            <span className="h-2 w-2 rounded-full bg-indigo-500" />
            {name}
          </div>
        ))}
      </div>
    </div>
  );
}
