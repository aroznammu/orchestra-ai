"use client";

import { useState } from "react";
import { Send } from "lucide-react";

const SUBJECTS = ["General Inquiry", "Sales", "Technical Support", "Enterprise"] as const;

export default function ContactForm() {
  const [submitted, setSubmitted] = useState(false);
  const [form, setForm] = useState({
    name: "",
    email: "",
    subject: SUBJECTS[0] as string,
    message: "",
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const mailto = `mailto:support@orchestraai.dev?subject=${encodeURIComponent(
      `[${form.subject}] from ${form.name}`
    )}&body=${encodeURIComponent(form.message)}`;
    window.location.href = mailto;
    setSubmitted(true);
  }

  if (submitted) {
    return (
      <div className="rounded-xl border border-emerald-800/40 bg-emerald-950/20 p-8 text-center">
        <p className="text-lg font-medium text-emerald-400">Thank you!</p>
        <p className="mt-2 text-sm text-zinc-400">
          Your email client should have opened. If not, email us directly at{" "}
          <a href="mailto:support@orchestraai.dev" className="text-indigo-400 underline">
            support@orchestraai.dev
          </a>
        </p>
        <button
          onClick={() => setSubmitted(false)}
          className="mt-4 text-sm text-indigo-400 underline"
        >
          Send another message
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <label htmlFor="name" className="mb-1.5 block text-sm font-medium text-zinc-300">
          Name
        </label>
        <input
          id="name"
          required
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          className="w-full rounded-lg border border-zinc-800 bg-zinc-900/60 px-4 py-2.5 text-sm text-zinc-50 placeholder-zinc-600 outline-none transition-colors focus:border-indigo-600"
          placeholder="Your name"
        />
      </div>

      <div>
        <label htmlFor="email" className="mb-1.5 block text-sm font-medium text-zinc-300">
          Email
        </label>
        <input
          id="email"
          type="email"
          required
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          className="w-full rounded-lg border border-zinc-800 bg-zinc-900/60 px-4 py-2.5 text-sm text-zinc-50 placeholder-zinc-600 outline-none transition-colors focus:border-indigo-600"
          placeholder="you@company.com"
        />
      </div>

      <div>
        <label htmlFor="subject" className="mb-1.5 block text-sm font-medium text-zinc-300">
          Subject
        </label>
        <select
          id="subject"
          value={form.subject}
          onChange={(e) => setForm({ ...form, subject: e.target.value })}
          className="w-full rounded-lg border border-zinc-800 bg-zinc-900/60 px-4 py-2.5 text-sm text-zinc-50 outline-none transition-colors focus:border-indigo-600"
        >
          {SUBJECTS.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="message" className="mb-1.5 block text-sm font-medium text-zinc-300">
          Message
        </label>
        <textarea
          id="message"
          required
          rows={5}
          value={form.message}
          onChange={(e) => setForm({ ...form, message: e.target.value })}
          className="w-full resize-none rounded-lg border border-zinc-800 bg-zinc-900/60 px-4 py-2.5 text-sm text-zinc-50 placeholder-zinc-600 outline-none transition-colors focus:border-indigo-600"
          placeholder="How can we help?"
        />
      </div>

      <button
        type="submit"
        className="inline-flex items-center gap-2 rounded-full bg-indigo-600 px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-indigo-500"
      >
        <Send className="h-4 w-4" />
        Send Message
      </button>
    </form>
  );
}
