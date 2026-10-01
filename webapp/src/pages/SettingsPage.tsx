import { Settings } from "lucide-react";
import { useEffect, useState } from "react";
import { apiGet, type ProviderInfo } from "@/api/client";
import { discoverLlm } from "@/lib/ollama";

export default function SettingsPage() {
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [llm, setLlm] = useState({
    available: false as boolean | null,
    model: "",
  });

  useEffect(() => {
    apiGet<{ providers: ProviderInfo[] }>("/api/health")
      .then((h) => setProviders(h.providers ?? []))
      .catch(() => setProviders([]));
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
          work with zero setup. Keys unlock SaaS providers and are read from
          process env - never pasted here, never committed.
        </p>
        <div className="mt-2 space-y-1.5">
          {[
            {
              key: "TAVILY_API_KEY",
              desc: "Tavily AI-native search (free 1k/mo at tavily.com)",
            },
            { key: "EXA_API_KEY", desc: "Exa neural search (Phase 2 adapter)" },
            {
              key: "BRAVE_API_KEY",
              desc: "Brave grounding search (Phase 2 adapter)",
            },
          ].map((row) => {
            const live = providers.find(
              (p) => p.name === row.key.split("_")[0].toLowerCase(),
            );
            return (
              <div
                key={row.key}
                className="flex items-center gap-2 font-mono text-xs"
              >
                <span className="text-zinc-200">{row.key}</span>
                <span
                  className={
                    live?.configured ? "text-green-400" : "text-amber-400"
                  }
                >
                  {live?.configured ? "set" : "unset"}
                </span>
                <span className="font-sans text-zinc-500">{row.desc}</span>
              </div>
            );
          })}
        </div>
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
