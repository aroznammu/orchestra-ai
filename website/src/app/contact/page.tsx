"use client";

import { motion } from "framer-motion";
import { Mail, MessageSquare, Clock, Github, type LucideIcon } from "lucide-react";
import ContactForm from "@/components/ContactForm";
import { SUPPORT_EMAIL, DASHBOARD_URL, GITHUB_URL } from "@/lib/constants";

interface Channel {
  icon: LucideIcon;
  title: string;
  description: React.ReactNode;
  action?: { label: string; href: string; icon: LucideIcon };
}

const CHANNELS: Channel[] = [
  {
    icon: Mail,
    title: "Email Support",
    description: (
      <>
        Reach us directly at{" "}
        <a href={`mailto:${SUPPORT_EMAIL}`} className="text-indigo-400 underline">
          {SUPPORT_EMAIL}
        </a>
      </>
    ),
  },
  {
    icon: MessageSquare,
    title: "Live Chat",
    description: "Chat with our AI support agent for instant help.",
    action: {
      label: "Open Chat",
      href: `${DASHBOARD_URL}/support`,
      icon: MessageSquare,
    },
  },
  {
    icon: Github,
    title: "GitHub Issues",
    description: "Report bugs or request features on GitHub.",
    action: {
      label: "Open GitHub",
      href: GITHUB_URL,
      icon: Github,
    },
  },
  {
    icon: Clock,
    title: "Response Time",
    description:
      "We typically respond within 24 hours. Priority support customers receive responses within 4 hours.",
  },
];

export default function ContactPage() {
  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden px-6 py-24">
        <div className="pointer-events-none absolute inset-0 radial-glow" />
        <div className="mx-auto max-w-4xl text-center">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <span className="mb-4 inline-block rounded-full border border-indigo-800/60 bg-indigo-950/40 px-4 py-1 text-xs font-medium uppercase tracking-wider text-indigo-300">
              Contact
            </span>
          </motion.div>
          <motion.h1
            className="text-4xl font-bold tracking-tight text-zinc-50 sm:text-5xl"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.05 }}
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
            <div className="glass rounded-2xl p-8">
              <h2 className="mb-6 text-xl font-semibold text-zinc-50">Send us a message</h2>
              <ContactForm />
            </div>
          </motion.div>

          {/* Sidebar */}
          <motion.div
            className="space-y-4 lg:col-span-2"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            {CHANNELS.map((channel) => {
              const Icon = channel.icon;
              const ActionIcon = channel.action?.icon;
              return (
                <div key={channel.title} className="glass rounded-2xl p-6">
                  <div className="icon-glow mb-3 flex h-10 w-10 items-center justify-center rounded-lg">
                    <Icon className="h-5 w-5 text-indigo-400" />
                  </div>
                  <h3 className="text-sm font-semibold text-zinc-50">{channel.title}</h3>
                  <p className="mt-1 text-sm text-zinc-400">{channel.description}</p>
                  {channel.action && ActionIcon && (
                    <a
                      href={channel.action.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-3 inline-flex items-center gap-1.5 rounded-full border border-zinc-700 px-4 py-2 text-xs font-medium text-zinc-300 transition-all hover:border-indigo-600 hover:text-white"
                    >
                      <ActionIcon className="h-3.5 w-3.5" />
                      {channel.action.label}
                    </a>
                  )}
                </div>
              );
            })}
          </motion.div>
        </div>
      </section>
    </>
  );
}
