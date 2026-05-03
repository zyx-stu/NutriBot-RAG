"use client";

import { useState, useRef, useEffect, FormEvent } from "react";

/* ── Types ─────────────────────────────────────────────────────────────────── */
interface Source {
  content: string;
  page?: number;
  source?: string;
  similarity: number;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  model?: string;
  timestamp: Date;
}

/* ── Quick-prompt suggestions ───────────────────────────────────────────────── */
const SUGGESTIONS = [
  "What are the best protein sources for muscle building?",
  "How does vitamin D deficiency affect the body?",
  "Explain the Mediterranean diet and its benefits",
  "What is the role of fiber in digestive health?",
  "How many calories do I need per day?",
  "What foods are high in omega-3 fatty acids?",
];

/* ── Helpers ────────────────────────────────────────────────────────────────── */
function generateId() {
  return Math.random().toString(36).slice(2, 10);
}

function formatTime(d: Date) {
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

/* ── Typing indicator ───────────────────────────────────────────────────────── */
function TypingDots() {
  return (
    <span className="typing-dots" aria-label="Assistant is thinking">
      <span /><span /><span />
    </span>
  );
}

/* ── Source card ────────────────────────────────────────────────────────────── */
function SourceCard({ source, index }: { source: Source; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const pct = Math.round(source.similarity * 100);
  return (
    <div className="source-card">
      <button
        className="source-header"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
      >
        <span className="source-badge">{index + 1}</span>
        <span className="source-meta">
          {source.source ?? "human-nutrition-text.pdf"}
          {source.page && <span className="source-page"> · p.{source.page}</span>}
        </span>
        <span className="source-sim" title="Relevance score">
          {pct}%
        </span>
        <span className="source-chevron">{expanded ? "▲" : "▼"}</span>
      </button>
      {expanded && (
        <p className="source-content">{source.content}</p>
      )}
    </div>
  );
}

/* ── Message bubble ─────────────────────────────────────────────────────────── */
function ChatBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === "user";
  const [showSources, setShowSources] = useState(false);

  return (
    <div className={`bubble-row ${isUser ? "bubble-row--user" : "bubble-row--bot"}`}>
      {!isUser && (
        <div className="avatar avatar--bot" aria-hidden>🥦</div>
      )}
      <div className="bubble-col">
        <div className={`bubble ${isUser ? "bubble--user" : "bubble--bot"}`}>
          <p className="bubble-text">{msg.content}</p>
          <span className="bubble-time">{formatTime(msg.timestamp)}</span>
        </div>

        {/* Sources accordion */}
        {!isUser && msg.sources && msg.sources.length > 0 && (
          <div className="sources-section">
            <button
              className="sources-toggle"
              onClick={() => setShowSources((v) => !v)}
            >
              📚 {msg.sources.length} source{msg.sources.length > 1 ? "s" : ""}
              {msg.model && (
                <span className="model-badge">via {msg.model.split("-").slice(0, 2).join("-")}</span>
              )}
              <span className="toggle-icon">{showSources ? "▲" : "▼"}</span>
            </button>
            {showSources && (
              <div className="sources-list">
                {msg.sources.map((s, i) => (
                  <SourceCard key={i} source={s} index={i} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
      {isUser && (
        <div className="avatar avatar--user" aria-hidden>👤</div>
      )}
    </div>
  );
}

/* ── Main page ──────────────────────────────────────────────────────────────── */
export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  // Auto-resize textarea
  useEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  }, [input]);

  async function sendMessage(text: string) {
    const query = text.trim();
    if (!query || busy) return;

    setError(null);
    const userMsg: Message = {
      id: generateId(),
      role: "user",
      content: query,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setBusy(true);

    try {
      const history = messages.slice(-6).map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: query, history }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error ?? `HTTP ${res.status}`);
      }

      const botMsg: Message = {
        id: generateId(),
        role: "assistant",
        content: data.answer ?? "I couldn't generate a response. Please try again.",
        sources: data.sources ?? [],
        model: data.model,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      setError(msg);
    } finally {
      setBusy(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    sendMessage(input);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  }

  const isEmpty = messages.length === 0;

  return (
    <div className="app">
      {/* ── Sidebar ──────────────────────────────────────────────────────── */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <span className="logo-icon">🥗</span>
          <span className="logo-text">NutriBot</span>
        </div>
        <p className="sidebar-tagline">AI-powered nutrition advisor</p>

        <div className="sidebar-section">
          <p className="sidebar-label">Powered by</p>
          <div className="tech-pills">
            <span className="pill pill--green">HuggingFace API</span>
            <span className="pill pill--blue">Supabase pgvector</span>
            <span className="pill pill--purple">Groq Llama 3.1</span>
            <span className="pill pill--orange">RAG Pipeline</span>
          </div>
        </div>

        <div className="sidebar-section">
          <p className="sidebar-label">Quick Questions</p>
          <div className="suggestions">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                className="suggestion-btn"
                onClick={() => sendMessage(s)}
                disabled={busy}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        <div className="sidebar-footer">
          <p className="sidebar-source">
            📖 Source: <em>Human Nutrition Textbook</em>
          </p>
          <p className="sidebar-note">Consult a dietitian for personal advice.</p>
        </div>
      </aside>

      {/* ── Main chat area ───────────────────────────────────────────────── */}
      <div className="chat-area">
        {/* Header */}
        <header className="chat-header">
          <div className="chat-header-left">
            <span className="header-icon">🥦</span>
            <div>
              <h1 className="header-title">NutriBot</h1>
              <p className="header-subtitle">Nutrition &amp; Diet Expert · RAG-powered</p>
            </div>
          </div>
          <div className="status-dot" title="Online" />
        </header>

        {/* Messages */}
        <main className="messages-area" aria-live="polite" aria-label="Chat messages">
          {isEmpty ? (
            <div className="welcome">
              <div className="welcome-icon">🥗</div>
              <h2 className="welcome-title">Welcome to NutriBot!</h2>
              <p className="welcome-sub">
                Ask me anything about nutrition, diet plans, vitamins, macros, or healthy eating.
                I answer from a curated nutrition knowledge base.
              </p>
              <div className="welcome-chips">
                {SUGGESTIONS.slice(0, 3).map((s) => (
                  <button
                    key={s}
                    className="welcome-chip"
                    onClick={() => sendMessage(s)}
                    disabled={busy}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <ChatBubble key={msg.id} msg={msg} />
              ))}
              {busy && (
                <div className="bubble-row bubble-row--bot">
                  <div className="avatar avatar--bot">🥦</div>
                  <div className="bubble bubble--bot bubble--loading">
                    <TypingDots />
                  </div>
                </div>
              )}
            </>
          )}
          {error && (
            <div className="error-banner" role="alert">
              ⚠️ {error}
              <button className="error-dismiss" onClick={() => setError(null)}>✕</button>
            </div>
          )}
          <div ref={bottomRef} />
        </main>

        {/* Input */}
        <footer className="input-area">
          <form className="input-form" onSubmit={handleSubmit}>
            <textarea
              ref={inputRef}
              className="input-box"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about nutrition, diet plans, vitamins, macros…"
              disabled={busy}
              rows={1}
              aria-label="Chat input"
            />
            <button
              type="submit"
              className="send-btn"
              disabled={busy || !input.trim()}
              aria-label="Send message"
            >
              {busy ? (
                <span className="send-spinner" />
              ) : (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13" />
                  <polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
              )}
            </button>
          </form>
          <p className="input-hint">Press Enter to send · Shift+Enter for new line</p>
        </footer>
      </div>
    </div>
  );
}
