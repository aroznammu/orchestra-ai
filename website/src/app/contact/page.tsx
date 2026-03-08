"use client";

import { motion } from "framer-motion";
import { Mail, MessageSquare, Clock } from "lucide-react";
import ContactForm from "@/components/ContactForm";
import { SUPPORT_EMAIL, DASHBOARD_URL } from "@/lib/constants";

export default function ContactPage() {
  return (
    <>
      {/* Hero */}
      <section className="px-6 py-24">
        <div className="mx-auto max-w-4xl text-center">
          <motion.h1
            className="text-4xl font-bold tracking-tight text-zinc-50 sm:text-5xl"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            Get in{" "}
            <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
              Touch
            </span>
          </motion.h1>
          <motion.p
            className="mx-auto mt-5 max-w-xl text-lg text-zinc-400"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            Have a question, need a demo, or want to discuss enterprise options? We&apos;d love to
            hear from you.
          </motion.p>
        </div>
      </section>

      {/* Contact grid */}
      <section className="px-6 pb-24">
        <div className="mx-auto grid max-w-5xl gap-12 lg:grid-cols-5">
          {/* Form */}
          <motion.div
            className="lg:col-span-3"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-8">
              <h2 className="mb-6 text-xl font-semibold text-zinc-50">Send us a message</h2>
              <ContactForm />
            </div>
          </motion.div>

          {/* Sidebar */}
          <motion.div
            className="space-y-6 lg:col-span-2"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600/10">
                <Mail className="h-5 w-5 text-indigo-400" />
              </div>
              <h3 className="text-sm font-semibold text-zinc-50">Email Support</h3>
              <p className="mt-1 text-sm text-zinc-400">
                Reach us directly at{" "}
                <a
                  href={`mailto:${SUPPORT_EMAIL}`}
                  className="text-indigo-400 underline"
                >
                  {SUPPORT_EMAIL}
                </a>
              </p>
            </div>

            <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600/10">
                <MessageSquare className="h-5 w-5 text-indigo-400" />
              </div>
              <h3 className="text-sm font-semibold text-zinc-50">Live Chat</h3>
              <p className="mt-1 text-sm text-zinc-400">
                Chat with our AI support agent for instant help.
              </p>
              <a
                href={`${DASHBOARD_URL}/support`}
                className="mt-3 inline-flex items-center gap-1.5 rounded-full border border-zinc-700 px-4 py-2 text-xs font-medium text-zinc-300 transition-colors hover:border-indigo-600 hover:text-white"
              >
                <MessageSquare className="h-3.5 w-3.5" />
                Open Chat
              </a>
            </div>

            <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600/10">
                <Clock className="h-5 w-5 text-indigo-400" />
              </div>
              <h3 className="text-sm font-semibold text-zinc-50">Response Time</h3>
              <p className="mt-1 text-sm text-zinc-400">
                We typically respond within 24 hours. Priority support customers receive
                responses within 4 hours.
              </p>
            </div>
          </motion.div>
        </div>
      </section>
    </>
  );
}
