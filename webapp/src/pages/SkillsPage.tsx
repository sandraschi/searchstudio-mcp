import { GraduationCap } from "lucide-react";
import { useEffect, useState } from "react";
import { apiGet } from "@/api/client";

export default function SkillsPage() {
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let live = true;
    apiGet<{ content: string }>("/skill/super-search")
      .then((d) => {
        if (live) setContent(d.content ?? "");
      })
      .catch((e) => {
        if (live) setError(String(e));
      })
      .finally(() => {
        if (live) setLoading(false);
      });
    return () => {
      live = false;
    };
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <GraduationCap size={22} className="text-zinc-200" />
        <h1 className="text-2xl font-bold tracking-tight">Skills</h1>
      </div>
      {loading ? (
        <div className="animate-pulse rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
          <div className="h-4 w-40 rounded bg-zinc-800" />
        </div>
      ) : error ? (
        <p className="text-sm text-red-400">{error}</p>
      ) : (
        <div className="grid gap-3 lg:grid-cols-3" data-testid="skills-list">
          <div className="rounded-xl border border-zinc-500 bg-zinc-900 p-3 text-left text-sm">
            <code className="text-xs text-zinc-100">super-search</code>
            <p className="mt-1 text-xs text-zinc-400">
              SearchStudio search expert
            </p>
          </div>
          <pre className="rounded-xl border border-zinc-800 bg-zinc-950 p-4 font-mono text-xs text-zinc-300 whitespace-pre-wrap max-h-[60vh] overflow-y-auto lg:col-span-2">
            {content || "(empty)"}
          </pre>
        </div>
      )}
      <p className="text-xs text-zinc-600">
        Also exposed to agents as MCP resource{" "}
        <span className="font-mono">skill://super-search</span>.
      </p>
    </div>
  );
}
