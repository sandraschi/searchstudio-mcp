import { Glasses } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  apiDelete,
  apiGet,
  apiPost,
  type GoggleEntry,
  type GogglesResponse,
  type ProviderInfo,
} from "@/api/client";

const DIY_TEMPLATE = `! name: My lens
! description: What this lens does.
! public: false
! author: Me

! Boost what you trust (strength 1-10, default 1):
/trusted-example/,$boost=2

! Downrank the noisy:
/noisy-example/,$downrank=2

! Discard the useless (use sparingly):
$discard,site=spam-example.com
`;

export default function GogglesPage() {
  const [entries, setEntries] = useState<GoggleEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [braveOn, setBraveOn] = useState<boolean | null>(null);
  const [newName, setNewName] = useState("");
  const [newUrl, setNewUrl] = useState("");
  const [newNotes, setNewNotes] = useState("");
  const [editor, setEditor] = useState(DIY_TEMPLATE);
  const [copied, setCopied] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [g, p] = await Promise.all([
        apiGet<GogglesResponse>("/api/goggles"),
        apiGet<{ providers: ProviderInfo[] }>("/api/providers"),
      ]);
      setEntries(g.entries);
      const brave = p.providers.find((x) => x.name === "brave");
      setBraveOn(brave ? brave.configured : false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Load failed.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const save = useCallback(
    async (body: Record<string, unknown>) => {
      const res = await apiPost<{ success: boolean; error?: string }>(
        "/api/goggles",
        body,
      );
      if (!res.success) throw new Error(res.error || "Save failed.");
      await load();
    },
    [load],
  );

  const toggle = async (entry: GoggleEntry) => {
    setError("");
    try {
      await save({ name: entry.name, enabled: !entry.enabled });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Toggle failed.");
    }
  };

  const saveUrl = async (entry: GoggleEntry, url: string, notes: string) => {
    setError("");
    try {
      await save({ name: entry.name, url, notes });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed.");
    }
  };

  const addCustom = async () => {
    setError("");
    try {
      await save({ name: newName, url: newUrl, notes: newNotes });
      setNewName("");
      setNewUrl("");
      setNewNotes("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Add failed.");
    }
  };

  const removeEntry = async (name: string) => {
    setError("");
    try {
      await apiDelete<{ success: boolean; error?: string }>("/api/goggles", {
        name,
      });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed.");
    }
  };

  const download = (filename: string, text: string, mime: string) => {
    const blob = new Blob([text], { type: mime });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  const exportAll = () => {
    download(
      "goggles.json",
      JSON.stringify({ entries }, null, 2),
      "application/json",
    );
  };

  const importFile = async (file: File) => {
    setError("");
    try {
      const parsed = JSON.parse(await file.text()) as {
        entries?: GoggleEntry[];
      };
      const list = Array.isArray(parsed) ? parsed : (parsed.entries ?? []);
      if (!Array.isArray(list) || list.length === 0) {
        throw new Error("No entries found in that file.");
      }
      for (const e of list.slice(0, 50)) {
        if (e && typeof e.name === "string") {
          await apiPost("/api/goggles", {
            name: e.name,
            url: typeof e.url === "string" ? e.url : "",
            notes: typeof e.notes === "string" ? e.notes : "",
          });
        }
      }
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Import failed.");
    }
  };

  const copyEditor = async () => {
    try {
      await navigator.clipboard.writeText(editor);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setError("Clipboard blocked by the browser.");
    }
  };

  const builtin = entries.filter((e) => e.builtin);
  const custom = entries.filter((e) => !e.builtin);

  return (
    <div className="space-y-4" data-testid="goggles-page">
      <div className="flex items-center gap-2">
        <Glasses size={22} className="text-zinc-200" />
        <h1 className="text-2xl font-bold tracking-tight">Goggles</h1>
      </div>
      <p className="text-sm leading-relaxed text-zinc-300">
        Brave lenses: custom ranking rules ($boost, $downrank, $discard) that
        Brave applies server-side on every Brave search. Enabled lenses ride
        along automatically and are named in the receipt, so a curated result
        never looks like a raw one.
      </p>

      {braveOn === false && (
        <p className="rounded-xl border border-amber-800 bg-amber-950/30 p-3 text-xs text-amber-200">
          No Brave key set: lenses are stored but do nothing until you add a key
          on the Settings page. Everything else keeps working.
        </p>
      )}
      {error && <p className="text-sm text-red-400">{error}</p>}
      {loading && <p className="text-xs text-zinc-500">Loading…</p>}

      <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-400">
        Prepared lenses
      </h2>
      <p className="text-xs text-zinc-500">
        Curated rule sets with ready-to-publish text. Paste a public URL
        (published at brave.com/goggles, a gist, any raw file URL) to activate
        one — enabling without a URL is refused on purpose.
      </p>
      <div className="space-y-2">
        {builtin.map((e) => (
          <GoggleCard
            key={e.name}
            entry={e}
            onToggle={() => toggle(e)}
            onSave={(url, notes) => saveUrl(e, url, notes)}
          />
        ))}
      </div>

      <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-400">
        Your lenses
      </h2>
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-3">
        <div className="flex flex-col gap-2">
          <input
            value={newName}
            onChange={(ev) => setNewName(ev.target.value)}
            placeholder="name (e.g. my-rss-lens)"
            className="rounded-lg border border-zinc-700 bg-zinc-950 px-2 py-1 text-sm"
          />
          <input
            value={newUrl}
            onChange={(ev) => setNewUrl(ev.target.value)}
            placeholder="public https:// URL of the .goggle file (optional until enabling)"
            className="rounded-lg border border-zinc-700 bg-zinc-950 px-2 py-1 text-sm"
          />
          <input
            value={newNotes}
            onChange={(ev) => setNewNotes(ev.target.value)}
            placeholder="notes (optional)"
            className="rounded-lg border border-zinc-700 bg-zinc-950 px-2 py-1 text-sm"
          />
          <button
            type="button"
            onClick={addCustom}
            data-testid="goggles-add"
            className="self-start rounded-lg bg-primary px-3 py-1 text-sm font-medium text-zinc-950"
          >
            Add lens
          </button>
        </div>
      </div>
      <div className="space-y-2">
        {custom.map((e) => (
          <GoggleCard
            key={e.name}
            entry={e}
            onToggle={() => toggle(e)}
            onSave={(url, notes) => saveUrl(e, url, notes)}
            onDelete={() => removeEntry(e.name)}
          />
        ))}
        {custom.length === 0 && (
          <p className="text-xs text-zinc-600">
            None yet. Add a public Goggle URL above, or compose one below.
          </p>
        )}
      </div>

      <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-400">
        Compose your own
      </h2>
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-3">
        <textarea
          value={editor}
          onChange={(ev) => setEditor(ev.target.value)}
          rows={14}
          spellCheck={false}
          data-testid="goggles-editor"
          className="w-full rounded-lg border border-zinc-700 bg-zinc-950 p-2 font-mono text-xs"
        />
        <div className="mt-2 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => download("my-lens.goggle", editor, "text/plain")}
            className="rounded-lg border border-zinc-700 px-3 py-1 text-xs"
          >
            Download .goggle
          </button>
          <button
            type="button"
            onClick={copyEditor}
            className="rounded-lg border border-zinc-700 px-3 py-1 text-xs"
          >
            {copied ? "Copied!" : "Copy"}
          </button>
        </div>
        <ol className="mt-2 list-decimal space-y-1 pl-5 text-xs text-zinc-400">
          <li>
            Publish the text: create a public gist (or any repo file) and copy
            its raw https:// URL — or submit at brave.com/goggles/create.
          </li>
          <li>Paste that URL into a custom lens above and enable it.</li>
          <li>
            Brave fetches the file per search. Keep it public; a private URL
            fails closed and the receipt will say the lens errored.
          </li>
        </ol>
      </div>

      <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-400">
        Backup
      </h2>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={exportAll}
          data-testid="goggles-export"
          className="rounded-lg border border-zinc-700 px-3 py-1 text-xs"
        >
          Export JSON
        </button>
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          data-testid="goggles-import"
          className="rounded-lg border border-zinc-700 px-3 py-1 text-xs"
        >
          Import JSON
        </button>
        <input
          ref={fileRef}
          type="file"
          accept="application/json,.json"
          className="hidden"
          onChange={(ev) => {
            const f = ev.target.files?.[0];
            ev.target.value = "";
            if (f) importFile(f);
          }}
        />
      </div>
    </div>
  );
}

function GoggleCard({
  entry,
  onToggle,
  onSave,
  onDelete,
}: {
  entry: GoggleEntry;
  onToggle: () => void;
  onSave: (url: string, notes: string) => void;
  onDelete?: () => void;
}) {
  const [url, setUrl] = useState(entry.url);
  const [notes, setNotes] = useState(entry.notes);
  const dirty = url !== entry.url || notes !== entry.notes;
  return (
    <div
      data-testid="goggle-item"
      className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-3"
    >
      <div className="flex items-center gap-2">
        <button
          type="button"
          role="switch"
          aria-checked={entry.enabled}
          onClick={onToggle}
          data-testid="goggle-toggle"
          className="rounded-lg border border-zinc-700 px-2 py-0.5 text-xs"
        >
          {entry.enabled ? "On" : "Off"}
        </button>
        <p className="font-mono text-sm text-zinc-100">{entry.name}</p>
        {entry.builtin && (
          <span className="text-[11px] text-zinc-500">prepared</span>
        )}
      </div>
      {entry.description && (
        <p className="mt-1 text-xs text-zinc-400">{entry.description}</p>
      )}
      {entry.dsl && (
        <details className="mt-1">
          <summary className="cursor-pointer text-[11px] text-zinc-500">
            Rule text
          </summary>
          <pre className="mt-1 max-h-48 overflow-auto whitespace-pre-wrap rounded-lg border border-zinc-800 bg-zinc-950 p-2 font-mono text-[11px] text-zinc-300">
            {entry.dsl}
          </pre>
        </details>
      )}
      <div className="mt-2 flex flex-col gap-1.5">
        <input
          value={url}
          onChange={(ev) => setUrl(ev.target.value)}
          placeholder="public https:// URL of the .goggle file"
          data-testid="goggle-url"
          className="rounded-lg border border-zinc-700 bg-zinc-950 px-2 py-1 font-mono text-xs"
        />
        <input
          value={notes}
          onChange={(ev) => setNotes(ev.target.value)}
          placeholder="notes (optional)"
          className="rounded-lg border border-zinc-700 bg-zinc-950 px-2 py-1 text-xs"
        />
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => onSave(url, notes)}
            disabled={!dirty}
            className="rounded-lg bg-primary px-3 py-1 text-xs font-medium text-zinc-950 disabled:opacity-40"
          >
            Save
          </button>
          {onDelete && (
            <button
              type="button"
              onClick={onDelete}
              className="rounded-lg border border-red-900 px-3 py-1 text-xs text-red-300"
            >
              Delete
            </button>
          )}
        </div>
      </div>
      {!entry.url && (
        <p className="mt-1 text-[11px] text-zinc-600">
          No public URL yet — enabling is refused until one is pasted above.
        </p>
      )}
    </div>
  );
}
