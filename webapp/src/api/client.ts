export interface Hit {
  title: string;
  url: string;
  snippet: string;
  provider: string;
  kind: string;
  published?: string | null;
  score?: number | null;
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
