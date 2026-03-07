"use client";

import { ApiError, askOrchestrator, type OrchestrateResponse } from "@/lib/apiClient";
import { cn } from "@/lib/utils";
import {
  AlertCircle,
  BarChart3,
  BrainCircuit,
  CheckCircle2,
  FileText,
  Globe,
  Loader2,
  Scale,
  Send,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  User,
  Video,
  XCircle,
  Zap,
} from "lucide-react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import { type FormEvent, useCallback, useEffect, useRef, useState } from "react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface SectionData {
  kind: "content" | "analytics" | "compliance" | "optimization" | "policy" | "platform" | "video" | "video_compliance" | "text";
  data: Record<string, unknown>;
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  intent?: string | null;
  sections?: SectionData[];
  error?: boolean;
  timestamp: Date;
}

// ---------------------------------------------------------------------------
// ID generator
// ---------------------------------------------------------------------------

let _msgId = 0;
function nextId(): string {
  return `msg-${++_msgId}-${Date.now()}`;
}

// ---------------------------------------------------------------------------
// Build assistant message from backend response
// ---------------------------------------------------------------------------

function hasData(obj: unknown): obj is Record<string, unknown> {
  return !!obj && typeof obj === "object" && Object.keys(obj).length > 0;
}

function buildAssistantMessage(res: OrchestrateResponse): ChatMessage {
  console.log("Raw OrchestrateResponse:", JSON.parse(JSON.stringify(res)));

  const sections: SectionData[] = [];

  const sectionMap: { kind: SectionData["kind"]; value: unknown }[] = [
    { kind: "compliance", value: res.compliance },
    { kind: "analytics", value: res.analytics },
    { kind: "content", value: res.content },
    { kind: "video", value: res.video },
    { kind: "video_compliance", value: res.video_compliance },
    { kind: "optimization", value: res.optimization },
    { kind: "policy", value: res.policy },
    { kind: "platform", value: res.platform },
  ];

  for (const { kind, value } of sectionMap) {
    if (hasData(value)) {
      sections.push({ kind, data: value });
    }
  }

  let text = "";
  if (res.error) {
    text = res.error;
  } else if (sections.length === 0) {
    text = res.is_complete
      ? "Done. No additional output was returned."
      : "Processing your request...";
  }

  return {
    id: nextId(),
    role: "assistant",
    text,
    intent: res.intent,
    sections: sections.length > 0 ? sections : undefined,
    error: !!res.error,
    timestamp: new Date(),
  };
}

// ---------------------------------------------------------------------------
// Section renderers
// ---------------------------------------------------------------------------

const SECTION_META: Record<
  string,
  { label: string; icon: React.ReactNode; accent: string }
> = {
  content: {
    label: "Generated Content",
    icon: <FileText className="h-3.5 w-3.5" />,
    accent: "border-indigo-500/40 bg-indigo-500/5",
  },
  analytics: {
    label: "Analytics",
    icon: <BarChart3 className="h-3.5 w-3.5" />,
    accent: "border-emerald-500/40 bg-emerald-500/5",
  },
  compliance: {
    label: "Compliance Check",
    icon: <ShieldCheck className="h-3.5 w-3.5" />,
    accent: "border-amber-500/40 bg-amber-500/5",
  },
  optimization: {
    label: "Optimization",
    icon: <TrendingUp className="h-3.5 w-3.5" />,
    accent: "border-cyan-500/40 bg-cyan-500/5",
  },
  policy: {
    label: "Policy Validation",
    icon: <Scale className="h-3.5 w-3.5" />,
    accent: "border-violet-500/40 bg-violet-500/5",
  },
  platform: {
    label: "Platform Result",
    icon: <Globe className="h-3.5 w-3.5" />,
    accent: "border-sky-500/40 bg-sky-500/5",
  },
  video: {
    label: "Generated Video",
    icon: <Video className="h-3.5 w-3.5" />,
    accent: "border-fuchsia-500/40 bg-fuchsia-500/5",
  },
  video_compliance: {
    label: "Visual Compliance",
    icon: <ShieldAlert className="h-3.5 w-3.5" />,
    accent: "border-red-500/40 bg-red-500/5",
  },
  text: {
    label: "Details",
    icon: <FileText className="h-3.5 w-3.5" />,
    accent: "border-zinc-700/50 bg-zinc-800/40",
  },
};

function ContentSection({ data }: { data: Record<string, unknown> }) {
  const variants = data.variants as Record<string, unknown>[] | undefined;
  const reasoning = data.reasoning as string | undefined;
  const selected = (data.selected_variant as number) ?? 0;

  if (!variants || variants.length === 0) {
    return <KeyValueTable data={data} />;
  }

  return (
    <div className="space-y-2">
      {variants.map((v, i) => {
        const text = (v.text ?? v.content ?? "") as string;
        const hashtags = (v.hashtags ?? []) as string[];
        return (
          <div
            key={i}
            className={cn(
              "rounded-lg border p-3",
              i === selected
                ? "border-indigo-500/50 bg-indigo-500/10"
                : "border-zinc-700/40 bg-zinc-800/30",
            )}
          >
            <div className="mb-1 flex items-center gap-2">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
                Variant {i + 1}
              </span>
              {i === selected && (
                <span className="flex items-center gap-0.5 rounded bg-indigo-500/20 px-1.5 py-0.5 text-[10px] font-medium text-indigo-300">
                  <CheckCircle2 className="h-2.5 w-2.5" /> selected
                </span>
              )}
            </div>
            <div className="prose-sm text-sm leading-relaxed text-zinc-200">
              <ReactMarkdown>{text}</ReactMarkdown>
            </div>
            {hashtags.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {hashtags.map((h) => (
                  <span
                    key={h}
                    className="rounded-full bg-zinc-700/60 px-2 py-0.5 text-[10px] text-zinc-400"
                  >
                    {h.startsWith("#") ? h : `#${h}`}
                  </span>
                ))}
              </div>
            )}
          </div>
        );
      })}
      {reasoning && (
        <p className="text-xs italic text-zinc-500">{reasoning}</p>
      )}
    </div>
  );
}

function AnalyticsSection({ data }: { data: Record<string, unknown> }) {
  const metrics = data.metrics as Record<string, unknown> | undefined;
  const insights = data.insights as string[] | undefined;
  const recommendations = data.recommendations as string[] | undefined;
  const summary = data.cross_platform_summary as Record<string, unknown> | undefined;

  const hasStructuredKeys =
    hasData(metrics) ||
    hasData(summary) ||
    (Array.isArray(insights) && insights.length > 0) ||
    (Array.isArray(recommendations) && recommendations.length > 0);

  if (!hasStructuredKeys) {
    return <KeyValueTable data={data} />;
  }

  return (
    <div className="space-y-3">
      {metrics && Object.keys(metrics).length > 0 && (
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
          {Object.entries(metrics).map(([k, v]) => (
            <div
              key={k}
              className="rounded-lg border border-zinc-700/40 bg-zinc-800/40 px-3 py-2"
            >
              <p className="text-[10px] font-medium uppercase tracking-wider text-zinc-500">
                {k.replace(/_/g, " ")}
              </p>
              <p className="mt-0.5 text-sm font-semibold text-zinc-200">
                {typeof v === "number" ? v.toLocaleString() : String(v)}
              </p>
            </div>
          ))}
        </div>
      )}
      {summary && Object.keys(summary).length > 0 && !metrics && (
        <KeyValueTable data={summary} />
      )}
      {insights && insights.length > 0 && (
        <div>
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-emerald-400/80">
            Insights
          </p>
          <ul className="space-y-1">
            {insights.map((t) => (
              <li key={t} className="flex gap-2 text-xs text-zinc-300">
                <span className="mt-1.5 block h-1 w-1 shrink-0 rounded-full bg-emerald-500" />
                {t}
              </li>
            ))}
          </ul>
        </div>
      )}
      {recommendations && recommendations.length > 0 && (
        <div>
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-indigo-400/80">
            Recommendations
          </p>
          <ul className="space-y-1">
            {recommendations.map((t) => (
              <li key={t} className="flex gap-2 text-xs text-zinc-300">
                <span className="mt-1.5 block h-1 w-1 shrink-0 rounded-full bg-indigo-500" />
                {t}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function ComplianceSection({ data }: { data: Record<string, unknown> }) {
  const approved = data.approved as boolean | undefined;
  const riskLevel = data.risk_level as string | undefined;
  const riskScore = data.risk_score as number | undefined;
  const violations = data.violations as string[] | undefined;
  const warnings = data.warnings as string[] | undefined;
  const recs = data.recommendations as string[] | undefined;

  const hasStructuredKeys =
    typeof approved === "boolean" ||
    typeof riskLevel === "string" ||
    typeof riskScore === "number" ||
    (Array.isArray(violations) && violations.length > 0);

  if (!hasStructuredKeys) {
    return <KeyValueTable data={data} />;
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3">
        {approved ? (
          <span className="flex items-center gap-1 text-xs font-medium text-emerald-400">
            <CheckCircle2 className="h-3.5 w-3.5" /> Approved
          </span>
        ) : (
          <span className="flex items-center gap-1 text-xs font-medium text-red-400">
            <XCircle className="h-3.5 w-3.5" /> Rejected
          </span>
        )}
        {riskLevel && (
          <span
            className={cn(
              "rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase",
              riskLevel === "low" && "bg-emerald-500/20 text-emerald-300",
              riskLevel === "medium" && "bg-amber-500/20 text-amber-300",
              riskLevel === "high" && "bg-red-500/20 text-red-300",
              riskLevel === "critical" && "bg-red-700/30 text-red-200",
            )}
          >
            {riskLevel} risk
          </span>
        )}
        {typeof riskScore === "number" && (
          <span className="text-[10px] text-zinc-500">
            Score: {riskScore.toFixed(2)}
          </span>
        )}
      </div>
      {violations && violations.length > 0 && (
        <ul className="space-y-1">
          {violations.map((v) => (
            <li key={v} className="flex gap-2 text-xs text-red-400">
              <XCircle className="mt-0.5 h-3 w-3 shrink-0" /> {v}
            </li>
          ))}
        </ul>
      )}
      {warnings && warnings.length > 0 && (
        <ul className="space-y-1">
          {warnings.map((w) => (
            <li key={w} className="flex gap-2 text-xs text-amber-400">
              <AlertCircle className="mt-0.5 h-3 w-3 shrink-0" /> {w}
            </li>
          ))}
        </ul>
      )}
      {recs && recs.length > 0 && (
        <ul className="space-y-1">
          {recs.map((r) => (
            <li key={r} className="flex gap-2 text-xs text-zinc-400">
              <Sparkles className="mt-0.5 h-3 w-3 shrink-0 text-indigo-400" /> {r}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function OptimizationSection({ data }: { data: Record<string, unknown> }) {
  const reasoning = data.reasoning as string | undefined;
  const confidence = data.confidence as number | undefined;
  const improvement = data.expected_improvement as number | undefined;

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-3">
        {typeof improvement === "number" && (
          <div className="rounded-lg border border-zinc-700/40 bg-zinc-800/40 px-3 py-2">
            <p className="text-[10px] font-medium uppercase tracking-wider text-zinc-500">
              Expected Improvement
            </p>
            <p className="text-sm font-semibold text-emerald-400">
              +{(improvement * 100).toFixed(1)}%
            </p>
          </div>
        )}
        {typeof confidence === "number" && (
          <div className="rounded-lg border border-zinc-700/40 bg-zinc-800/40 px-3 py-2">
            <p className="text-[10px] font-medium uppercase tracking-wider text-zinc-500">
              Confidence
            </p>
            <p className="text-sm font-semibold text-zinc-200">
              {(confidence * 100).toFixed(0)}%
            </p>
          </div>
        )}
      </div>
      {reasoning && (
        <div className="text-sm leading-relaxed text-zinc-300">
          <ReactMarkdown>{reasoning}</ReactMarkdown>
        </div>
      )}
      {!reasoning && <KeyValueTable data={data} exclude={["reasoning", "confidence", "expected_improvement"]} />}
    </div>
  );
}

function PolicySection({ data }: { data: Record<string, unknown> }) {
  const valid = data.valid as boolean | undefined;
  const errors = data.errors as string[] | undefined;
  const warnings = data.warnings as string[] | undefined;
  const suggestions = data.suggestions as string[] | undefined;

  const hasStructuredKeys =
    typeof valid === "boolean" ||
    (Array.isArray(errors) && errors.length > 0) ||
    (Array.isArray(warnings) && warnings.length > 0);

  if (!hasStructuredKeys) {
    return <KeyValueTable data={data} />;
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        {valid ? (
          <span className="flex items-center gap-1 text-xs font-medium text-emerald-400">
            <CheckCircle2 className="h-3.5 w-3.5" /> Valid
          </span>
        ) : (
          <span className="flex items-center gap-1 text-xs font-medium text-red-400">
            <XCircle className="h-3.5 w-3.5" /> Invalid
          </span>
        )}
      </div>
      {errors && errors.length > 0 && (
        <ul className="space-y-1">
          {errors.map((e) => (
            <li key={e} className="flex gap-2 text-xs text-red-400">
              <XCircle className="mt-0.5 h-3 w-3 shrink-0" /> {e}
            </li>
          ))}
        </ul>
      )}
      {warnings && warnings.length > 0 && (
        <ul className="space-y-1">
          {warnings.map((w) => (
            <li key={w} className="flex gap-2 text-xs text-amber-400">
              <AlertCircle className="mt-0.5 h-3 w-3 shrink-0" /> {w}
            </li>
          ))}
        </ul>
      )}
      {suggestions && suggestions.length > 0 && (
        <ul className="space-y-1">
          {suggestions.map((s) => (
            <li key={s} className="flex gap-2 text-xs text-zinc-400">
              <Sparkles className="mt-0.5 h-3 w-3 shrink-0 text-violet-400" /> {s}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function PlatformSection({ data }: { data: Record<string, unknown> }) {
  return <KeyValueTable data={data} />;
}

function VideoSection({ data }: { data: Record<string, unknown> }) {
  const videoUrl = data.video_url as string | undefined;
  const duration = data.duration as number | undefined;
  const modelUsed = data.model_used as string | undefined;
  const promptUsed = data.prompt_used as string | undefined;

  if (!videoUrl) {
    return (
      <div className="flex items-center gap-2 text-xs text-zinc-500">
        <Video className="h-3.5 w-3.5" />
        No video was generated (API key missing or generation failed).
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="overflow-hidden rounded-lg border border-zinc-700/50 bg-black">
        <video
          src={videoUrl}
          controls
          className="w-full"
          preload="metadata"
          style={{ maxHeight: "400px" }}
        />
      </div>
      <div className="flex flex-wrap gap-3">
        {typeof duration === "number" && duration > 0 && (
          <div className="rounded-lg border border-zinc-700/40 bg-zinc-800/40 px-3 py-1.5">
            <p className="text-[10px] font-medium uppercase tracking-wider text-zinc-500">Duration</p>
            <p className="text-sm font-semibold text-zinc-200">{duration}s</p>
          </div>
        )}
        {modelUsed && (
          <div className="rounded-lg border border-zinc-700/40 bg-zinc-800/40 px-3 py-1.5">
            <p className="text-[10px] font-medium uppercase tracking-wider text-zinc-500">Model</p>
            <p className="text-sm font-semibold text-zinc-200">{modelUsed.split("/").pop()}</p>
          </div>
        )}
      </div>
      {promptUsed && (
        <p className="text-xs italic text-zinc-500">Prompt: {promptUsed}</p>
      )}
    </div>
  );
}

function VideoComplianceSection({ data }: { data: Record<string, unknown> }) {
  const safe = data.safe as boolean | undefined;
  const violations = data.violations as Array<Record<string, unknown>> | undefined;
  const scannedFrames = data.scanned_frames as number | undefined;

  if (safe !== false) {
    return (
      <div className="flex items-center gap-2 text-xs font-medium text-emerald-400">
        <CheckCircle2 className="h-3.5 w-3.5" />
        Visual compliance check passed
        {typeof scannedFrames === "number" && (
          <span className="font-normal text-zinc-500">({scannedFrames} frames scanned)</span>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-950/30 px-3 py-2">
        <ShieldAlert className="h-5 w-5 shrink-0 text-red-400" />
        <div>
          <p className="text-sm font-semibold text-red-300">
            Video Blocked: Potential Copyright/IP Violation Detected
          </p>
          <p className="text-xs text-red-400/70">
            The generated video was blocked before delivery.
            {typeof scannedFrames === "number" && ` ${scannedFrames} keyframes were analyzed.`}
          </p>
        </div>
      </div>
      {violations && violations.length > 0 && (
        <ul className="space-y-2">
          {violations.map((v, i) => (
            <li
              key={i}
              className="flex gap-2 rounded-lg border border-red-800/30 bg-red-950/20 px-3 py-2"
            >
              <XCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-red-400" />
              <div>
                <span className="text-[10px] font-semibold uppercase tracking-wider text-red-400">
                  {(v.type as string) ?? "violation"}
                </span>
                {v.confidence != null && (
                  <span className="ml-2 text-[10px] text-zinc-500">
                    ({((v.confidence as number) * 100).toFixed(0)}% confidence)
                  </span>
                )}
                <p className="text-xs text-zinc-300">{(v.description as string) ?? ""}</p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function KeyValueTable({
  data,
  exclude = [],
}: {
  data: Record<string, unknown>;
  exclude?: string[];
}) {
  const entries = Object.entries(data).filter(
    ([k, v]) =>
      !exclude.includes(k) &&
      v !== null &&
      v !== undefined &&
      v !== "" &&
      !(Array.isArray(v) && v.length === 0) &&
      !(typeof v === "object" && !Array.isArray(v) && Object.keys(v as object).length === 0),
  );
  if (entries.length === 0) return null;

  return (
    <div className="space-y-1">
      {entries.map(([k, v]) => (
        <div key={k} className="flex gap-2 text-xs">
          <span className="shrink-0 font-medium capitalize text-zinc-500">
            {k.replace(/_/g, " ")}:
          </span>
          <span className="text-zinc-300">
            {typeof v === "object" ? JSON.stringify(v) : String(v)}
          </span>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section card renderer
// ---------------------------------------------------------------------------

function SectionCard({ section }: { section: SectionData }) {
  const meta = SECTION_META[section.kind] ?? SECTION_META.text;

  return (
    <div className={cn("mt-3 rounded-lg border p-3", meta.accent)}>
      <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-zinc-400">
        {meta.icon}
        {meta.label}
      </div>
      {section.kind === "content" && <ContentSection data={section.data} />}
      {section.kind === "analytics" && <AnalyticsSection data={section.data} />}
      {section.kind === "compliance" && <ComplianceSection data={section.data} />}
      {section.kind === "optimization" && <OptimizationSection data={section.data} />}
      {section.kind === "policy" && <PolicySection data={section.data} />}
      {section.kind === "platform" && <PlatformSection data={section.data} />}
      {section.kind === "video" && <VideoSection data={section.data} />}
      {section.kind === "video_compliance" && <VideoComplianceSection data={section.data} />}
      {section.kind === "text" && <KeyValueTable data={section.data} />}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Chat bubble
// ---------------------------------------------------------------------------

function IntentBadge({ intent }: { intent: string }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-md bg-indigo-500/20 px-2 py-0.5 text-xs font-medium text-indigo-300">
      <Sparkles className="h-3 w-3" />
      {intent.replace(/_/g, " ")}
    </span>
  );
}

function MessageBubble({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === "user";

  if (!isUser) {
    console.log("Raw Message Data:", msg);
  }

  return (
    <div className={cn("flex gap-3", isUser ? "flex-row-reverse" : "flex-row")}>
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
          isUser ? "bg-indigo-600" : "bg-zinc-800",
        )}
      >
        {isUser ? (
          <User className="h-4 w-4 text-white" />
        ) : (
          <BrainCircuit className="h-4 w-4 text-indigo-400" />
        )}
      </div>

      <div
        className={cn(
          "max-w-[85%] rounded-xl px-4 py-3",
          isUser
            ? "bg-indigo-600 text-white"
            : "border border-zinc-800 bg-zinc-900/80 text-zinc-200",
          msg.error && "border-red-800/50 bg-red-950/30",
        )}
      >
        {msg.intent && <IntentBadge intent={msg.intent} />}

        {msg.text && (
          <div
            className={cn(
              "prose prose-sm prose-invert max-w-none text-sm leading-relaxed",
              "prose-p:my-1 prose-ul:my-1 prose-li:my-0",
              msg.intent && "mt-2",
              msg.error && "text-red-400",
            )}
          >
            <ReactMarkdown>{msg.text}</ReactMarkdown>
          </div>
        )}

        {msg.sections?.map((s) => (
          <SectionCard key={s.kind} section={s} />
        ))}

        <p
          className={cn(
            "mt-2 text-[10px]",
            isUser ? "text-indigo-200/60" : "text-zinc-600",
          )}
        >
          {msg.timestamp.toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

const WELCOME_SUGGESTIONS = [
  "What campaigns are running right now?",
  "Analyze my Instagram performance",
  "Create a Twitter thread about AI trends",
  "Generate a video ad for our summer sale",
];

export default function OrchestratorPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [showPaywall, setShowPaywall] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => setMounted(true), []);

  const scrollToBottom = useCallback(() => {
    requestAnimationFrame(() => {
      if (scrollRef.current) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      }
    });
  }, []);

  useEffect(scrollToBottom, [messages, loading, scrollToBottom]);

  const send = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || loading) return;

      const userMsg: ChatMessage = {
        id: nextId(),
        role: "user",
        text: trimmed,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setInput("");
      setLoading(true);

      try {
        const res = await askOrchestrator(trimmed);
        setMessages((prev) => [...prev, buildAssistantMessage(res)]);
      } catch (err: unknown) {
        if (err instanceof ApiError && err.status === 402) {
          setShowPaywall(true);
        } else {
          setMessages((prev) => [
            ...prev,
            {
              id: nextId(),
              role: "assistant",
              text: err instanceof Error ? err.message : "Something went wrong.",
              error: true,
              timestamp: new Date(),
            },
          ]);
        }
      } finally {
        setLoading(false);
        setTimeout(() => inputRef.current?.focus(), 50);
      }
    },
    [loading],
  );

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    send(input);
  }

  const isEmpty = messages.length === 0;

  return (
    <div className="flex h-[calc(100vh-7rem)] flex-col">
      <div className="shrink-0 pb-4">
        <h1 className="text-2xl font-bold tracking-tight">AI Orchestrator</h1>
        <p className="text-sm text-zinc-500">
          Chat with your marketing AI -- create campaigns, get analytics, and
          optimize strategy using natural language.
        </p>
      </div>

      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto rounded-xl border border-zinc-800 bg-zinc-950/50 p-4"
      >
        {isEmpty && !loading ? (
          <div className="flex h-full flex-col items-center justify-center gap-6">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-zinc-800/80">
              <BrainCircuit className="h-8 w-8 text-indigo-400" />
            </div>
            <div className="text-center">
              <h2 className="text-lg font-semibold text-zinc-300">
                What can I help you with?
              </h2>
              <p className="mt-1 text-sm text-zinc-500">
                Ask me anything about your marketing campaigns.
              </p>
            </div>
            <div className="grid gap-2 sm:grid-cols-2">
              {WELCOME_SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="rounded-lg border border-zinc-800 bg-zinc-900/60 px-4 py-2.5 text-left text-sm text-zinc-300 transition-colors hover:border-indigo-500/50 hover:bg-zinc-800/80"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} msg={msg} />
            ))}
            {loading && (
              <div className="flex gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-zinc-800">
                  <BrainCircuit className="h-4 w-4 text-indigo-400" />
                </div>
                <div className="flex items-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900/80 px-4 py-3 text-sm text-zinc-400">
                  <Loader2 className="h-4 w-4 animate-spin text-indigo-400" />
                  Agents are thinking...
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <form
        onSubmit={handleSubmit}
        className="mt-3 flex shrink-0 items-center gap-2"
      >
        <div className="relative flex-1">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            placeholder="Ask OrchestraAI anything..."
            className="w-full rounded-xl border border-zinc-700 bg-zinc-900 py-3 pl-4 pr-12 text-sm text-zinc-100 placeholder-zinc-500 outline-none transition-colors focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="absolute right-2 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-lg bg-indigo-600 text-white transition-colors hover:bg-indigo-500 disabled:opacity-30"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </button>
        </div>
      </form>

      {mounted && !localStorage.getItem("orchestra_token") && (
        <div className="mt-2 flex items-center gap-2 text-xs text-amber-400/80">
          <AlertCircle className="h-3 w-3" />
          Sign in first to use the orchestrator.
        </div>
      )}

      {showPaywall && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-950/80 backdrop-blur-sm">
          <div className="mx-4 max-w-md rounded-2xl border border-indigo-500/30 bg-zinc-900 p-8 text-center shadow-2xl shadow-indigo-500/10">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-600/20">
              <Sparkles className="h-8 w-8 text-indigo-400" />
            </div>
            <h2 className="mt-5 text-xl font-bold text-zinc-100">
              Upgrade to Enterprise Cloud
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-zinc-400">
              AI Orchestration is available on the Starter and Agency plans.
              Upgrade now to unlock intelligent campaign management, real-time
              analytics, and multi-platform automation.
            </p>
            <div className="mt-6 flex flex-col gap-3">
              <Link
                href="/settings/billing"
                className="flex items-center justify-center gap-2 rounded-lg bg-indigo-600 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-500"
              >
                <Zap className="h-4 w-4" />
                View Plans & Upgrade
              </Link>
              <button
                onClick={() => setShowPaywall(false)}
                className="text-sm text-zinc-500 transition-colors hover:text-zinc-300"
              >
                Maybe later
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
