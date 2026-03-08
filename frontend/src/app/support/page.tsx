"use client";

import {
  type ChatMessageResponse,
  type ChatSessionResponse,
  type FAQGroupResponse,
  ApiError,
  createSupportSession,
  getSessionMessages,
  listFAQs,
  listSupportSessions,
  resolveSession,
  sendSupportMessage,
} from "@/lib/apiClient";
import { cn } from "@/lib/utils";
import {
  CheckCircle2,
  ChevronDown,
  HelpCircle,
  Loader2,
  MessageCircle,
  Plus,
  Search,
  Send,
  User,
  X,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import {
  type FormEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type Tab = "chat" | "faq";

// ---------------------------------------------------------------------------
// FAQ Accordion
// ---------------------------------------------------------------------------

function FAQAccordionItem({
  question,
  answer,
}: {
  question: string;
  answer: string;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border-b border-zinc-800 last:border-0">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between gap-3 py-3.5 text-left text-sm font-medium text-zinc-200 transition-colors hover:text-indigo-300"
      >
        <span>{question}</span>
        <ChevronDown
          className={cn(
            "h-4 w-4 shrink-0 text-zinc-500 transition-transform duration-200",
            open && "rotate-180 text-indigo-400",
          )}
        />
      </button>
      {open && (
        <div className="pb-3.5 text-sm leading-relaxed text-zinc-400">
          <ReactMarkdown>{answer}</ReactMarkdown>
        </div>
      )}
    </div>
  );
}

function FAQPanel({
  groups,
  loading,
}: {
  groups: FAQGroupResponse[];
  loading: boolean;
}) {
  const [search, setSearch] = useState("");

  const filtered = groups
    .map((g) => ({
      ...g,
      entries: g.entries.filter(
        (e) =>
          !search ||
          e.question.toLowerCase().includes(search.toLowerCase()) ||
          e.answer.toLowerCase().includes(search.toLowerCase()),
      ),
    }))
    .filter((g) => g.entries.length > 0);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center text-zinc-500">
        <Loader2 className="h-5 w-5 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search FAQs..."
          className="w-full rounded-lg border border-zinc-700 bg-zinc-900 py-2.5 pl-9 pr-4 text-sm text-zinc-100 placeholder-zinc-500 outline-none focus:border-indigo-500"
        />
      </div>

      {filtered.length === 0 ? (
        <p className="py-8 text-center text-sm text-zinc-500">
          No FAQs found. Try a different search term.
        </p>
      ) : (
        filtered.map((group) => (
          <div key={group.category}>
            <h3 className="mb-1 text-xs font-semibold uppercase tracking-wider text-indigo-400/80">
              {group.category}
            </h3>
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 px-4">
              {group.entries.map((entry) => (
                <FAQAccordionItem
                  key={entry.id}
                  question={entry.question}
                  answer={entry.answer}
                />
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Session sidebar
// ---------------------------------------------------------------------------

function SessionList({
  sessions,
  activeId,
  onSelect,
  onCreate,
}: {
  sessions: ChatSessionResponse[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onCreate: () => void;
}) {
  return (
    <div className="flex h-full flex-col">
      <button
        onClick={onCreate}
        className="mb-3 flex w-full items-center justify-center gap-2 rounded-lg border border-dashed border-zinc-700 py-2 text-sm font-medium text-zinc-400 transition-colors hover:border-indigo-500/50 hover:text-indigo-300"
      >
        <Plus className="h-4 w-4" />
        New conversation
      </button>

      <div className="flex-1 space-y-1 overflow-y-auto">
        {sessions.map((s) => (
          <button
            key={s.id}
            onClick={() => onSelect(s.id)}
            className={cn(
              "flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm transition-colors",
              s.id === activeId
                ? "bg-indigo-600/15 text-indigo-300"
                : "text-zinc-400 hover:bg-zinc-800/60 hover:text-zinc-200",
            )}
          >
            <MessageCircle className="h-3.5 w-3.5 shrink-0" />
            <span className="truncate">{s.title}</span>
            {s.status === "resolved" && (
              <CheckCircle2 className="ml-auto h-3.5 w-3.5 shrink-0 text-emerald-500" />
            )}
          </button>
        ))}
        {sessions.length === 0 && (
          <p className="py-4 text-center text-xs text-zinc-600">
            No conversations yet
          </p>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Chat panel
// ---------------------------------------------------------------------------

function ChatBubble({ msg }: { msg: ChatMessageResponse }) {
  const isUser = msg.role === "user";

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
          <HelpCircle className="h-4 w-4 text-indigo-400" />
        )}
      </div>

      <div
        className={cn(
          "max-w-[80%] rounded-xl px-4 py-3",
          isUser
            ? "bg-indigo-600 text-white"
            : "border border-zinc-800 bg-zinc-900/80 text-zinc-200",
        )}
      >
        <div className="prose prose-sm prose-invert max-w-none text-sm leading-relaxed prose-p:my-1 prose-ul:my-1 prose-li:my-0">
          <ReactMarkdown>{msg.content}</ReactMarkdown>
        </div>
        <p
          className={cn(
            "mt-2 text-[10px]",
            isUser ? "text-indigo-200/60" : "text-zinc-600",
          )}
        >
          {new Date(msg.created_at).toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
}

function ChatPanel({
  sessionId,
  messages,
  loading,
  onSend,
  onResolve,
  sessionStatus,
}: {
  sessionId: string | null;
  messages: ChatMessageResponse[];
  loading: boolean;
  onSend: (msg: string) => void;
  onResolve: () => void;
  sessionStatus: string;
}) {
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = useCallback(() => {
    requestAnimationFrame(() => {
      if (scrollRef.current) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      }
    });
  }, []);

  useEffect(scrollToBottom, [messages, loading, scrollToBottom]);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || loading) return;
    setInput("");
    onSend(trimmed);
  }

  if (!sessionId) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 text-zinc-500">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-zinc-800/80">
          <HelpCircle className="h-8 w-8 text-indigo-400" />
        </div>
        <div className="text-center">
          <h2 className="text-lg font-semibold text-zinc-300">
            OrchestraAI Support
          </h2>
          <p className="mt-1 text-sm text-zinc-500">
            Start a new conversation or select one from the sidebar.
          </p>
        </div>
      </div>
    );
  }

  const isClosed = sessionStatus === "closed";

  return (
    <div className="flex h-full flex-col">
      {sessionStatus === "open" && messages.length > 0 && (
        <div className="mb-2 flex justify-end">
          <button
            onClick={onResolve}
            className="flex items-center gap-1.5 rounded-lg border border-emerald-600/40 bg-emerald-600/10 px-3 py-1.5 text-xs font-medium text-emerald-400 transition-colors hover:bg-emerald-600/20"
          >
            <CheckCircle2 className="h-3.5 w-3.5" />
            Mark resolved
          </button>
        </div>
      )}
      {sessionStatus === "resolved" && (
        <div className="mb-2 flex items-center gap-2 rounded-lg border border-emerald-600/30 bg-emerald-950/30 px-3 py-2 text-xs text-emerald-400">
          <CheckCircle2 className="h-3.5 w-3.5" />
          This conversation has been resolved. You can still send follow-up
          messages.
        </div>
      )}

      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto rounded-xl border border-zinc-800 bg-zinc-950/50 p-4"
      >
        {messages.length === 0 && !loading ? (
          <div className="flex h-full flex-col items-center justify-center gap-3">
            <HelpCircle className="h-10 w-10 text-zinc-700" />
            <p className="text-sm text-zinc-500">
              Ask anything about OrchestraAI -- we&apos;re here to help.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((msg) => (
              <ChatBubble key={msg.id} msg={msg} />
            ))}
            {loading && (
              <div className="flex gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-zinc-800">
                  <HelpCircle className="h-4 w-4 text-indigo-400" />
                </div>
                <div className="flex items-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900/80 px-4 py-3 text-sm text-zinc-400">
                  <Loader2 className="h-4 w-4 animate-spin text-indigo-400" />
                  Typing...
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {!isClosed && (
        <form onSubmit={handleSubmit} className="mt-3 flex items-center gap-2">
          <div className="relative flex-1">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
              placeholder="Type your question..."
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
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function SupportPage() {
  const [tab, setTab] = useState<Tab>("chat");
  const [sessions, setSessions] = useState<ChatSessionResponse[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessageResponse[]>([]);
  const [faqGroups, setFaqGroups] = useState<FAQGroupResponse[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [loadingFaqs, setLoadingFaqs] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sending, setSending] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);

  const activeSession = sessions.find((s) => s.id === activeSessionId);

  const fetchSessions = useCallback(async () => {
    try {
      const data = await listSupportSessions();
      setSessions(data);
    } catch {
      /* auth redirect handled by apiClient */
    } finally {
      setLoadingSessions(false);
    }
  }, []);

  const fetchFaqs = useCallback(async () => {
    try {
      const data = await listFAQs();
      setFaqGroups(data);
    } catch {
      /* handled */
    } finally {
      setLoadingFaqs(false);
    }
  }, []);

  useEffect(() => {
    fetchSessions();
    fetchFaqs();
  }, [fetchSessions, fetchFaqs]);

  const selectSession = useCallback(async (id: string) => {
    setActiveSessionId(id);
    setLoadingMessages(true);
    try {
      const msgs = await getSessionMessages(id);
      setMessages(msgs);
    } catch {
      setMessages([]);
    } finally {
      setLoadingMessages(false);
    }
  }, []);

  const handleCreateSession = useCallback(async () => {
    try {
      const session = await createSupportSession();
      setSessions((prev) => [session, ...prev]);
      setActiveSessionId(session.id);
      setMessages([]);
    } catch {
      /* handled */
    }
  }, []);

  const handleSend = useCallback(
    async (text: string) => {
      if (!activeSessionId || sending) return;
      setSending(true);

      const optimisticUser: ChatMessageResponse = {
        id: `temp-${Date.now()}`,
        role: "user",
        content: text,
        metadata: {},
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, optimisticUser]);

      try {
        const res = await sendSupportMessage(activeSessionId, text);
        setMessages((prev) => {
          const without = prev.filter((m) => m.id !== optimisticUser.id);
          return [...without, res.user_message, res.assistant_message];
        });

        setSessions((prev) =>
          prev.map((s) =>
            s.id === activeSessionId
              ? {
                  ...s,
                  title:
                    s.title === "New conversation"
                      ? text.slice(0, 80)
                      : s.title,
                  message_count: s.message_count + 2,
                  updated_at: new Date().toISOString(),
                }
              : s,
          ),
        );
      } catch (err) {
        setMessages((prev) => prev.filter((m) => m.id !== optimisticUser.id));
      } finally {
        setSending(false);
      }
    },
    [activeSessionId, sending],
  );

  const handleResolve = useCallback(async () => {
    if (!activeSessionId) return;
    try {
      const updated = await resolveSession(activeSessionId);
      setSessions((prev) =>
        prev.map((s) => (s.id === updated.id ? updated : s)),
      );
    } catch {
      /* handled */
    }
  }, [activeSessionId]);

  return (
    <div className="flex h-[calc(100vh-7rem)] flex-col">
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Support</h1>
          <p className="text-sm text-zinc-500">
            Get help from our AI support assistant or browse the FAQ.
          </p>
        </div>
        <div className="flex rounded-lg border border-zinc-800 bg-zinc-900/60 p-0.5">
          <button
            onClick={() => setTab("chat")}
            className={cn(
              "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
              tab === "chat"
                ? "bg-indigo-600/20 text-indigo-300"
                : "text-zinc-400 hover:text-zinc-200",
            )}
          >
            <MessageCircle className="h-3.5 w-3.5" />
            Chat
          </button>
          <button
            onClick={() => setTab("faq")}
            className={cn(
              "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
              tab === "faq"
                ? "bg-indigo-600/20 text-indigo-300"
                : "text-zinc-400 hover:text-zinc-200",
            )}
          >
            <HelpCircle className="h-3.5 w-3.5" />
            FAQ
          </button>
        </div>
      </div>

      {/* Body */}
      {tab === "faq" ? (
        <div className="flex-1 overflow-y-auto rounded-xl border border-zinc-800 bg-zinc-950/50 p-6">
          <FAQPanel groups={faqGroups} loading={loadingFaqs} />
        </div>
      ) : (
        <div className="flex flex-1 gap-4 overflow-hidden">
          {/* Session sidebar */}
          {showSidebar && (
            <div className="hidden w-64 shrink-0 rounded-xl border border-zinc-800 bg-zinc-950/50 p-3 lg:block">
              {loadingSessions ? (
                <div className="flex h-32 items-center justify-center">
                  <Loader2 className="h-5 w-5 animate-spin text-zinc-500" />
                </div>
              ) : (
                <SessionList
                  sessions={sessions}
                  activeId={activeSessionId}
                  onSelect={selectSession}
                  onCreate={handleCreateSession}
                />
              )}
            </div>
          )}

          {/* Chat area */}
          <div className="flex-1">
            {/* Mobile new chat button */}
            <div className="mb-2 flex items-center gap-2 lg:hidden">
              <button
                onClick={handleCreateSession}
                className="flex items-center gap-1.5 rounded-lg border border-zinc-700 px-3 py-1.5 text-xs font-medium text-zinc-400 hover:border-indigo-500/50 hover:text-indigo-300"
              >
                <Plus className="h-3.5 w-3.5" />
                New chat
              </button>
              {sessions.length > 0 && !activeSessionId && (
                <button
                  onClick={() => selectSession(sessions[0].id)}
                  className="text-xs text-zinc-500 underline hover:text-zinc-300"
                >
                  or load latest
                </button>
              )}
            </div>

            <ChatPanel
              sessionId={activeSessionId}
              messages={messages}
              loading={sending || loadingMessages}
              onSend={handleSend}
              onResolve={handleResolve}
              sessionStatus={activeSession?.status ?? ""}
            />
          </div>
        </div>
      )}
    </div>
  );
}
