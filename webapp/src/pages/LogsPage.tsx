import { ScrollText } from "lucide-react";

export default function LogsPage() {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <ScrollText size={22} className="text-zinc-200" />
        <h1 className="text-2xl font-bold tracking-tight">Logs</h1>
      </div>
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
        <p className="text-sm text-zinc-300">Backend log locations</p>
        <ul className="mt-1 list-inside list-disc text-xs text-zinc-400">
          <li>
            Console output of the backend process (start.ps1 window, or NSSM
            service log when service-managed).
          </li>
          <li>
            Every tool failure auto-logs a full traceback server-side (shared
            error helper) — ask for the backend window, not the chat transcript.
          </li>
          <li>
            Provider attempt history lives in the SQLite ledger (
            <span className="font-mono">data/searchstudio.sqlite3</span>) — see
            the Activity page for the 7-day view.
          </li>
        </ul>
      </div>
    </div>
  );
}
