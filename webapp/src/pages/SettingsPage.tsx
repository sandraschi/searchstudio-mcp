import { Settings } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { apiGet } from "@/api/client";
import { discoverLlm } from "@/lib/ollama";

interface KeyStatus {
  name: string;
  set: boolean;
  source: string;
}

const MANAGED_KEYS = [
  {
    key: "TAVILY_API_KEY",
    desc: "Tavily AI-native search: ranked results plus page content, built for LLM agents",
    url: "https://tavily.com",
    urlLabel: "free 1k/mo, no card",
  },
  {
    key: "EXA_API_KEY",
    desc: "Exa neural search: finds by meaning, not just keywords",
    url: "https://dashboard.exa.ai/api-keys",
    urlLabel: "exa.ai dashboard",
  },
  {
    key: "BRAVE_API_KEY",
    desc: "Brave grounding search: clean snippets (adapter Phase 2)",
    url: "https://brave.com/search/api",
    urlLabel: "brave.com/search/api",
  },
];

function KeyForm() {
  const [status, setStatus] = useState<KeyStatus[]>([]);
  const [inputs, setInputs] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    try {
      const data = await apiGet<{ keys: KeyStatus[] }>("/api/provider-keys");
      setStatus(data.keys ?? []);
    } catch (e) {
      setError(String(e));
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function save(name: string) {
    const value = (inputs[name] ?? "").trim();
    if (!value) {
      setError("Paste a key first.");
      return;
    }
    setError("");
    setMsg("");
    try {
      const resp = await fetch("/api/provider-keys", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, key: value }),
      });
      const data = (await resp.json()) as { success: boolean; error?: string };
      if (!data.success) throw new Error(data.error ?? "save failed");
      setInputs((prev) => ({ ...prev, [name]: "" }));
      setMsg(`${name} saved (server-side file, active immediately).`);
      refresh();
    } catch (e) {
      setError(String(e));
    }
  }

  async function testKey(name: string) {
    setError("");
    setMsg(`Testing ${name}…`);
    try {
      const resp = await fetch("/api/provider-keys/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      const data = (await resp.json()) as {
        success: boolean;
        valid?: boolean;
        latency_ms?: number;
        source?: string;
        error?: string;
        detail?: string;
      };
      if (!data.success) throw new Error(data.error ?? "test failed");
      setMsg(
        data.valid
          ? `${name} valid (${data.source}, ${data.latency_ms}ms).`
          : `${name} INVALID (${data.source}): ${data.detail ?? data.error ?? "rejected"}`,
      );
      refresh();
    } catch (e) {
      setError(String(e));
    }
  }

  async function clear(name: string) {
    setError("");
    setMsg("");
    try {
      const resp = await fetch(
        `/api/provider-keys?name=${encodeURIComponent(name)}`,
        {
          method: "DELETE",
        },
      );
      const data = (await resp.json()) as {
        success: boolean;
        removed?: boolean;
        error?: string;
      };
      if (!data.success) throw new Error(data.error ?? "delete failed");
      setMsg(
        data.removed
          ? `${name} removed from server file.`
          : `${name} was not stored (env-set keys are unaffected).`,
      );
      refresh();
    } catch (e) {
      setError(String(e));
    }
  }

  function stateOf(name: string): KeyStatus | undefined {
    return status.find((k) => k.name === name);
  }

  return (
    <div className="mt-2 space-y-2.5">
      {MANAGED_KEYS.map((row) => {
        const st = stateOf(row.key);
        return (
          <div
            key={row.key}
            className="rounded-lg border border-zinc-800 bg-zinc-950 p-3"
          >
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-xs text-zinc-200">{row.key}</span>
              <span
                className={
                  st?.set ? "text-xs text-green-400" : "text-xs text-amber-400"
                }
              >
                {st ? (st.set ? `set (${st.source})` : "unset") : "…"}
              </span>
              <span className="text-[11px] text-zinc-500">{row.desc}</span>
              <a
                href={row.url}
                target="_blank"
                rel="noreferrer"
                className="text-[11px] text-primary hover:underline"
              >
                Get a key: {row.urlLabel}
              </a>
            </div>
            <div className="mt-2 flex gap-2">
              <input
                type="password"
                value={inputs[row.key] ?? ""}
                onChange={(e) =>
                  setInputs((prev) => ({ ...prev, [row.key]: e.target.value }))
                }
                onKeyDown={(e) => e.key === "Enter" && save(row.key)}
                placeholder={
                  st?.source === "env"
                    ? "Set via env (file entry optional)"
                    : "Paste key…"
                }
                data-testid={`key-input-${row.key}`}
                autoComplete="off"
                className="flex-1 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-1.5 font-mono text-xs placeholder-zinc-600 focus:border-zinc-500 focus:outline-none"
              />
              <button
                type="button"
                onClick={() => save(row.key)}
                data-testid={`key-save-${row.key}`}
                className="rounded-lg bg-zinc-100 px-3 py-1.5 text-xs font-medium text-zinc-950 hover:bg-white"
              >
                Save
              </button>
              <button
                type="button"
                onClick={() => testKey(row.key)}
                data-testid={`key-test-${row.key}`}
                className="rounded-lg border border-zinc-700 px-3 py-1.5 text-xs text-zinc-300 hover:border-zinc-500"
              >
                Test
              </button>
              <button
                type="button"
                onClick={() => clear(row.key)}
                data-testid={`key-clear-${row.key}`}
                className="rounded-lg border border-zinc-700 px-3 py-1.5 text-xs text-zinc-300 hover:border-zinc-500"
              >
                Clear
              </button>
            </div>
          </div>
        );
      })}
      {msg && <p className="text-xs text-green-400">{msg}</p>}
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  );
}

interface FallbackStatus {
  browser_fallback: boolean;
  source: "env" | "file" | "default";
}

function FallbackToggle() {
  const [status, setStatus] = useState<FallbackStatus | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    apiGet<FallbackStatus>("/api/settings/fallbacks")
      .then(setStatus)
      .catch((e) => setError(String(e)));
  }, []);

  async function toggle(next: boolean) {
    setError("");
    try {
      const resp = await fetch("/api/settings/fallbacks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ browser_fallback: next }),
      });
      const data = (await resp.json()) as FallbackStatus & {
        success: boolean;
        error?: string;
      };
      if (!data.success) throw new Error(data.error ?? "save failed");
      setStatus(data);
    } catch (e) {
      setError(String(e));
    }
  }

  const locked = status?.source === "env";
  return (
    <div className="mt-2 space-y-1.5">
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={status?.browser_fallback ?? false}
          disabled={status === null || locked}
          onChange={(e) => toggle(e.target.checked)}
          data-testid="browser-fallback-toggle"
          className="h-4 w-4 accent-zinc-100"
        />
        Allow browser fallback (Camoufox) when a provider blocks us
      </label>
      <p className="text-xs text-zinc-400">
        When DuckDuckGo shows a bot challenge, SearchStudio retries once in a
        Camoufox browser via browser-mcp. This gets around the provider's bot
        check, which the provider may not want. Every rescued result is marked
        "via camoufox after block" in its receipt.
      </p>
      <p
        className="text-xs text-zinc-500"
        data-testid="browser-fallback-source"
      >
        {status === null
          ? "Loading..."
          : locked
            ? "Locked off by the operator (BROWSER_MCP_URL is empty)."
            : status.source === "file"
              ? "Your choice, saved on the server."
              : "Default (on). Uncheck to turn it off."}
      </p>
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  );
}

export default function SettingsPage() {
  const [llm, setLlm] = useState({
    available: false as boolean | null,
    model: "",
  });

  useEffect(() => {
    discoverLlm().then((s) =>
      setLlm({ available: s.available, model: s.model }),
    );
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Settings size={22} className="text-zinc-200" />
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
      </div>

      <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
        <p className="text-sm font-medium">Local LLM (chat)</p>
        <p className="mt-1 text-xs text-zinc-400">
          {llm.available === null
            ? "Detecting Ollama on :11434…"
            : llm.available
              ? `Ollama up - default model ${llm.model || "(none loaded)"}`
              : "Ollama not detected. Install from ollama.com and pull any chat model to enable Chat."}
        </p>
      </div>

      <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
        <p className="text-sm font-medium">Provider keys (all optional)</p>
        <p className="mt-1 text-xs text-zinc-400">
          Keyless providers (OpenSERP-local, DuckDuckGo, Wikipedia, arxiv-mcp)
          work with zero setup. Keys unlock SaaS providers: paste below or set
          process env (env wins when both exist). Stored keys live in a
          gitignored server-side file, take effect immediately, and are never
          shown back.
        </p>
        <KeyForm />
      </div>

      <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
        <p className="text-sm font-medium">Blocked providers</p>
        <FallbackToggle />
      </div>

      <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
        <p className="text-sm font-medium">Onboarding</p>
        <p className="mt-1 text-xs text-zinc-400">
          No account needed. Optional: Docker Desktop + openserp container for
          the OpenSERP-local provider, arxiv-mcp backend for fleet-local
          results. Details in docs/ONBOARDING.md.
        </p>
      </div>
    </div>
  );
}
