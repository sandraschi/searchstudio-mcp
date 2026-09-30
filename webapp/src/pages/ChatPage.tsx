import { Download, Eraser, MessagesSquare, Send } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { apiGet } from "@/api/client";
import { cn } from "@/lib/cn";
import { type ChatMessage, chat, discoverLlm } from "@/lib/ollama";

const HIST_KEY = "searchstudio-chat-history";
const PERS_KEY = "searchstudio-chat-personality";

const PERSONALITIES = [
  {
    id: "researcher",
    label: "Research Assistant",
    prompt:
      "You are a research assistant. Answer concisely with sources when available.",
  },
  {
    id: "skeptic",
    label: "Expert Reviewer",
    prompt:
      "You are a skeptical expert reviewer. Challenge claims, demand evidence, flag weak sources.",
  },
  {
    id: "summarizer",
    label: "Quick Summarizer",
    prompt: "You summarize in 3 bullets or fewer. No preamble.",
  },
  { id: "custom", label: "Custom", prompt: "" },
];

const EXAMPLES = [
  "Which providers are healthy right now?",
  "Why did my search return nothing?",
  "How do I add a Tavily key?",
  "Explain receipts vs hits.",
  "What is the flakiness matrix?",
  "When should I use mode=any?",
];

function loadHistory(): ChatMessage[] {
  try {
    const raw = localStorage.getItem(HIST_KEY);
    const arr = raw ? (JSON.parse(raw) as ChatMessage[]) : [];
    return Array.isArray(arr) ? arr.slice(-100) : [];
  } catch {
    return [];
  }
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>(loadHistory);
  const [input, setInput] = useState("");
  const [personality, setPersonality] = useState(
    () => localStorage.getItem(PERS_KEY) ?? "researcher",
  );
  const [customPrompt, setCustomPrompt] = useState("");
  const [skill, setSkill] = useState("");
  const [model, setModel] = useState("");
  const [llmOk, setLlmOk] = useState<boolean | null>(null);
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    localStorage.setItem(HIST_KEY, JSON.stringify(messages.slice(-100)));
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    localStorage.setItem(PERS_KEY, personality);
  }, [personality]);

  useEffect(() => {
    apiGet<{ content: string }>("/skill/super-search")
      .then((d) => setSkill(d.content ?? ""))
      .catch(() =>
        setSkill("You help with web search across multiple providers."),
      );
    discoverLlm().then((s) => {
      setLlmOk(s.available);
      setModel(s.model);
    });
  }, []);

  function systemPrompt(): string {
    const base = skill || "You help with web search.";
    if (personality === "custom") return customPrompt || base;
    const p = PERSONALITIES.find((x) => x.id === personality);
    return `${base}\n\n---\n\n## Role\n${p?.prompt ?? ""}`;
  }

  async function send(text: string) {
    const content = text.trim();
    if (!content || sending) return;
    if (!llmOk || !model) {
      setMessages((m) => [
        ...m,
        { role: "user", content },
        {
          role: "assistant",
          content:
            "No local LLM detected (Ollama on :11434?). Start Ollama to chat.",
        },
      ]);
      return;
    }
    setInput("");
    setSending(true);
    const next = [...messages, { role: "user", content } as ChatMessage];
    setMessages(next);
    try {
      const reply = await chat(model, systemPrompt(), next);
      setMessages([
        ...next,
        { role: "assistant", content: reply, ts: new Date().toISOString() },
      ]);
    } catch (e) {
      setMessages([
        ...next,
        { role: "assistant", content: `Chat failed: ${String(e)}` },
      ]);
    } finally {
      setSending(false);
    }
  }

  function exportTxt() {
    const lines = messages.map(
      (m) => `[${m.ts ?? "?"}] ${m.role}: ${m.content}`,
    );
    const blob = new Blob([lines.join("\n")], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `searchstudio-chat-${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  return (
    <div
      className="flex h-[calc(100vh-3.5rem)] flex-col space-y-3"
      data-testid="chat-page"
    >
      <div className="flex items-center gap-2" data-testid="chat-controls">
        <MessagesSquare size={22} className="text-zinc-200" />
        <h1 className="text-2xl font-bold tracking-tight">Chat</h1>
        <select
          value={personality}
          onChange={(e) => setPersonality(e.target.value)}
          data-testid="personality-select"
          className="ml-2 rounded-lg border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-xs"
        >
          {PERSONALITIES.map((p) => (
            <option key={p.id} value={p.id}>
              {p.label}
            </option>
          ))}
        </select>
        <span className="text-[11px] text-zinc-500">
          skill:super-search · {model || "no model"} ·{" "}
          {llmOk ? "Ollama up" : llmOk === false ? "Ollama down" : "detecting…"}
        </span>
        <span className="flex-1" />
        <button
          type="button"
          onClick={exportTxt}
          disabled={messages.length === 0}
          data-testid="chat-export"
          className="rounded-lg border border-zinc-700 p-1.5 text-zinc-400 hover:text-zinc-100 disabled:opacity-40"
        >
          <Download size={15} />
        </button>
        <button
          type="button"
          onClick={() => setMessages([])}
          disabled={messages.length === 0}
          data-testid="chat-clear"
          className="rounded-lg border border-zinc-700 p-1.5 text-zinc-400 hover:text-zinc-100 disabled:opacity-40"
        >
          <Eraser size={15} />
        </button>
      </div>

      {personality === "custom" && (
        <textarea
          value={customPrompt}
          onChange={(e) => setCustomPrompt(e.target.value)}
          placeholder="Custom system prompt (replaces skill+role)…"
          rows={3}
          className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-xs"
        />
      )}

      <div
        className="flex-1 space-y-2 overflow-y-auto rounded-xl border border-zinc-800 bg-zinc-900/30 p-3"
        data-testid="chat-messages"
      >
        {messages.length === 0 && (
          <div>
            <p className="text-sm text-zinc-400">
              Ask about searching — providers, receipts, keys, flakiness.
            </p>
            <div
              className="mt-2 flex flex-wrap gap-1.5"
              data-testid="example-prompts"
            >
              {EXAMPLES.map((ex) => (
                <button
                  key={ex}
                  type="button"
                  onClick={() => setInput(ex)}
                  className="rounded-full border border-zinc-700 bg-zinc-900 px-2.5 py-1 text-[11px] text-zinc-300 hover:border-zinc-500"
                >
                  {ex}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m) => (
          <div
            key={`${m.ts ?? "no-ts"}-${m.content.slice(0, 24)}`}
            className={cn(
              "max-w-[85%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap",
              m.role === "user"
                ? "ml-auto bg-zinc-800 text-zinc-100"
                : "bg-zinc-900 text-zinc-300",
            )}
          >
            {m.content}
          </div>
        ))}
        {sending && (
          <p className="animate-pulse text-xs text-zinc-500">Thinking…</p>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send(input)}
          placeholder={llmOk ? "Message…" : "Start Ollama to enable chat…"}
          data-testid="chat-input"
          className="flex-1 rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm placeholder-zinc-600 focus:border-zinc-500 focus:outline-none"
        />
        <button
          type="button"
          onClick={() => send(input)}
          disabled={sending || !input.trim()}
          data-testid="chat-send"
          className="rounded-lg bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-950 hover:bg-white disabled:opacity-50"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}
