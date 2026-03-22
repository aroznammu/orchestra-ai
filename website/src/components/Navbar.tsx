"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X, ArrowRight } from "lucide-react";
import { NAV_ITEMS, DASHBOARD_URL } from "@/lib/constants";

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  function closeMobile() {
    setMobileOpen(false);
  }

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 border-b transition-all duration-300 ${
        scrolled
          ? "border-zinc-800/60 bg-zinc-950/90 shadow-lg shadow-black/20 backdrop-blur-xl"
          : "border-transparent bg-zinc-950/65 backdrop-blur-md"
      }`}
    >
      <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <Link href="/" className="flex items-center gap-2.5" onClick={closeMobile}>
          <motion.span
            className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-sm font-bold text-white"
            whileHover={{ scale: 1.1, rotate: -5 }}
            transition={{ type: "spring", stiffness: 400, damping: 15 }}
          >
            O
          </motion.span>
          <span className="text-lg font-semibold text-zinc-50">OrchestraAI</span>
        </Link>

        <div className="hidden items-center gap-8 md:flex">
          {NAV_ITEMS.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={`relative text-sm transition-colors ${
                pathname === href
                  ? "font-medium text-indigo-400"
                  : "text-zinc-400 hover:text-zinc-50"
              }`}
            >
              {label}
              {pathname === href && (
                <motion.div
                  className="absolute -bottom-1 left-0 right-0 h-px bg-indigo-400"
                  layoutId="nav-indicator"
                  transition={{ type: "spring", stiffness: 300, damping: 30 }}
                />
              )}
            </Link>
          ))}
        </div>

        <div className="hidden md:block">
          <Link
            href={DASHBOARD_URL}
            className="group inline-flex items-center gap-1.5 rounded-full bg-indigo-600 px-5 py-2 text-sm font-medium text-white transition-all hover:bg-indigo-500 hover:shadow-lg hover:shadow-indigo-900/30"
          >
            Get Started
            <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
          </Link>
        </div>

        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="flex h-11 w-11 items-center justify-center rounded-lg text-zinc-400 transition-colors hover:bg-zinc-800 md:hidden"
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </nav>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            className="border-t border-zinc-800 bg-zinc-950/98 backdrop-blur-xl md:hidden"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
          >
            <div className="flex flex-col gap-1 px-6 py-4">
              {NAV_ITEMS.map(({ href, label }) => (
                <Link
                  key={href}
                  href={href}
                  onClick={closeMobile}
                  className={`flex min-h-[44px] items-center rounded-lg px-4 text-sm transition-colors ${
                    pathname === href
                      ? "bg-indigo-600/10 font-medium text-indigo-400"
                      : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-50"
                  }`}
                >
                  {label}
                </Link>
              ))}
              <Link
                href={DASHBOARD_URL}
                onClick={closeMobile}
                className="mt-3 inline-flex min-h-[44px] items-center justify-center gap-1.5 rounded-full bg-indigo-600 px-5 text-sm font-medium text-white"
              >
                Get Started
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
