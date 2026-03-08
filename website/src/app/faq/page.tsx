"use client";

import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { Search } from "lucide-react";
import AccordionItem from "@/components/AccordionItem";
import CTABanner from "@/components/CTABanner";
import { FAQ_DATA } from "@/lib/constants";

export default function FAQPage() {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    if (!query.trim()) return FAQ_DATA;

    const q = query.toLowerCase();
    return FAQ_DATA.map((cat) => ({
      ...cat,
      items: cat.items.filter(
        (item) =>
          item.question.toLowerCase().includes(q) ||
          item.answer.toLowerCase().includes(q)
      ),
    })).filter((cat) => cat.items.length > 0);
  }, [query]);

  return (
    <>
      {/* Hero */}
      <section className="px-6 py-24">
        <div className="mx-auto max-w-3xl text-center">
          <motion.h1
            className="text-4xl font-bold tracking-tight text-zinc-50 sm:text-5xl"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
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
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search questions..."
              className="w-full rounded-full border border-zinc-800 bg-zinc-900/60 py-3 pl-11 pr-4 text-sm text-zinc-50 placeholder-zinc-600 outline-none transition-colors focus:border-indigo-600"
            />
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
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 px-6">
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
