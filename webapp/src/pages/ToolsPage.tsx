import { Wrench } from "lucide-react";

const OPS = [
  {
    name: "super_search",
    desc: "Parallel fan-out across fleet-local, knowledge, and serp providers. Merged hits + per-provider receipts.",
    params: "query*, kinds, providers, limit (1-50), mode balanced|any",
  },
  {
    name: "provider_health",
    desc: "Rolling scoreboard: success rate, p50 latency, blocks per provider.",
    params: "window_hours (default 24)",
  },
  {
    name: "self_test",
    desc: "Flakiness matrix: 3 canonical probes across all providers.",
    params: "none",
  },
  {
    name: "provider_health_app",
    desc: "Prefab card twin of provider_health for in-chat display.",
    params: "window_hours (default 24)",
  },
];

export default function ToolsPage() {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Wrench size={22} className="text-zinc-200" />
        <h1 className="text-2xl font-bold tracking-tight">Tools</h1>
      </div>
      <p className="text-xs text-zinc-500">
        MCP surface: one portmanteau{" "}
        <span className="font-mono">searchops</span> plus one Prefab card. All
        tools read-only; all reach external networks (openWorldHint).
      </p>
      <div className="space-y-2" data-testid="tools-list">
        {OPS.map((op) => (
          <div
            key={op.name}
            className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4"
          >
            <p className="font-mono text-sm text-zinc-100">{op.name}</p>
            <p className="mt-1 text-xs text-zinc-400">{op.desc}</p>
            <p className="mt-1 font-mono text-[11px] text-zinc-500">
              {op.params}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
