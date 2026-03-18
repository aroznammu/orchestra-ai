"use client";

import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { Search } from "lucide-react";
import AccordionItem from "@/components/AccordionItem";
import CTABanner from "@/components/CTABanner";
import { FAQ_DATA } from "@/lib/constants";

export default function FAQPage() {
  const [query, setQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  const categories = useMemo(() => FAQ_DATA.map((c) => c.category), []);

  const filtered = useMemo(() => {
    let data = FAQ_DATA;

    if (activeCategory) {
      data = data.filter((cat) => cat.category === activeCategory);
    }

    if (!query.trim()) return data;

    const q = query.toLowerCase();
    return data
      .map((cat) => ({
        ...cat,
        items: cat.items.filter(
          (item) =>
            item.question.toLowerCase().includes(q) ||
            item.answer.toLowerCase().includes(q)
        ),
      }))
      .filter((cat) => cat.items.length > 0);
  }, [query, activeCategory]);

  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden px-6 py-24">
        <div className="pointer-events-none absolute inset-0 radial-glow" />
        <div className="mx-auto max-w-3xl text-center">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <span className="mb-4 inline-block rounded-full border border-indigo-800/60 bg-indigo-950/40 px-4 py-1 text-xs font-medium uppercase tracking-wider text-indigo-300">
              FAQ
            </span>
          </motion.div>
          <motion.h1
            className="text-4xl font-bold tracking-tight text-zinc-50 sm:text-5xl"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.05 }}
          >
            Frequently Asked{" "}
            <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
              Questions
            </span>
          </motion.h1>
          <motion.p
            className="mx-auto mt-5 max-w-xl text-lg text-zinc-400"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            Everything you need to know about OrchestraAI. Can&apos;t find what you&apos;re looking
            for? Contact our support team.
          </motion.p>

          {/* Search */}
          <motion.div
            className="relative mx-auto mt-10 max-w-md"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.15 }}
          >
            <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search questions..."
              className="w-full rounded-full border border-zinc-800 bg-zinc-900/60 py-3 pl-11 pr-4 text-sm text-zinc-50 placeholder-zinc-600 outline-none transition-colors focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
          </motion.div>
        </div>
      </section>

      {/* Category filter tabs */}
      <section className="px-6 pb-8">
        <div className="mx-auto max-w-3xl">
          <motion.div
            className="flex flex-wrap justify-center gap-2"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.2 }}
          >
            <button
              onClick={() => setActiveCategory(null)}
              className={`rounded-full px-4 py-1.5 text-xs font-medium transition-all ${
                activeCategory === null
                  ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/20"
                  : "border border-zinc-800 text-zinc-400 hover:border-zinc-600 hover:text-zinc-200"
              }`}
            >
              All
            </button>
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setActiveCategory(activeCategory === cat ? null : cat)}
                className={`rounded-full px-4 py-1.5 text-xs font-medium transition-all ${
                  activeCategory === cat
                    ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/20"
                    : "border border-zinc-800 text-zinc-400 hover:border-zinc-600 hover:text-zinc-200"
                }`}
              >
                {cat}
              </button>
            ))}
          </motion.div>
        </div>
      </section>

      {/* FAQ accordion */}
      <section className="px-6 pb-24">
        <div className="mx-auto max-w-3xl">
          {filtered.length === 0 && (
            <p className="text-center text-zinc-500">
              No questions match &ldquo;{query}&rdquo;. Try a different search or{" "}
              <a href="/contact" className="text-indigo-400 underline">
                contact us
              </a>
              .
            </p>
          )}

          {filtered.map((category, catIdx) => (
            <motion.div
              key={category.category}
              className="mb-12"
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: catIdx * 0.05 }}
            >
              <h2 className="mb-4 text-sm font-semibold uppercase tracking-widest text-indigo-400">
                {category.category}
              </h2>
              <div className="glass rounded-xl px-6">
                {category.items.map((item) => (
                  <AccordionItem
                    key={item.question}
                    question={item.question}
                    answer={item.answer}
                  />
                ))}
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="px-6 pb-24">
        <div className="mx-auto max-w-3xl">
          <CTABanner
            title="Still have questions?"
            subtitle="Our support team is ready to help. Reach out via email or live chat."
            buttonText="Contact Support"
            buttonHref="/contact"
          />
        </div>
      </section>
    </>
  );
}
