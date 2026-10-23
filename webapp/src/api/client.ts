export interface Hit {
  title: string;
  url: string;
  snippet: string;
  provider: string;
  kind: string;
  published?: string | null;
  score?: number | null;
  // Paper extras (arxiv-mcp hits only; absent elsewhere).
  server?: string;
  authors?: string[];
  pdf_url?: string | null;
  categories?: string[];
  paper_id?: string;
}

export interface PaperText {
  success: boolean;
  paper_id?: string;
  markdown?: string;
  truncated?: boolean;
  error?: string;
}

export interface GoggleEntry {
  name: string;
  url: string;
  notes: string;
  enabled: boolean;
  builtin: boolean;
  description: string;
  dsl: string;
}

export interface GogglesResponse {
  success: boolean;
  entries: GoggleEntry[];
  error?: string;
}

export interface Receipt {
  provider: string;
  kind: string;
  ok: boolean;
  latency_ms: number;
  count: number;
  error: string;
  blocked: boolean;
  configured: boolean;
  time_filter_applied: boolean;
  goggles_applied?: string[];
}

export interface ProviderInfo {
  name: string;
  kind: string;
  configured: boolean;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!resp.ok) {
    throw new Error(`HTTP ${resp.status}: ${path}`);
  }
  return (await resp.json()) as T;
}

export const apiGet = <T>(path: string): Promise<T> => request<T>(path);

export const apiPost = <T>(path: string, body: unknown): Promise<T> =>
  request<T>(path, { method: "POST", body: JSON.stringify(body) });

export const apiDelete = <T>(path: string, body?: unknown): Promise<T> =>
  request<T>(path, {
    method: "DELETE",
    body: body === undefined ? undefined : JSON.stringify(body),
  });
