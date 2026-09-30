const OLLAMA = "http://127.0.0.1:11434";

// Small preference stack for chat default. Resident-first: whatever is
// already loaded wins (no cold reload), else first installed match.
const PREFERENCE = ["qwen3", "gemma3", "llama3", "mistral", "phi"];

export interface LlmStatus {
  available: boolean;
  model: string;
  resident: boolean;
}

async function getJson(path: string): Promise<unknown> {
  const resp = await fetch(`${OLLAMA}${path}`);
  if (!resp.ok) throw new Error(`Ollama ${resp.status}`);
  return await resp.json();
}

export async function discoverLlm(): Promise<LlmStatus> {
  try {
    const ps = (await getJson("/api/ps")) as {
      models?: Array<{ name: string }>;
    };
    const loaded = (ps.models ?? []).map((m) => m.name);
    for (const want of PREFERENCE) {
      const hit = loaded.find((n) => n.toLowerCase().includes(want));
      if (hit) return { available: true, model: hit, resident: true };
    }
    if (loaded.length > 0)
      return { available: true, model: loaded[0], resident: true };
    const tags = (await getJson("/api/tags")) as {
      models?: Array<{ name: string }>;
    };
    const installed = (tags.models ?? []).map((m) => m.name);
    for (const want of PREFERENCE) {
      const hit = installed.find((n) => n.toLowerCase().includes(want));
      if (hit) return { available: true, model: hit, resident: false };
    }
    if (installed.length > 0)
      return { available: true, model: installed[0], resident: false };
    return { available: false, model: "", resident: false };
  } catch {
    return { available: false, model: "", resident: false };
  }
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  ts?: string;
}

export async function chat(
  model: string,
  system: string,
  messages: ChatMessage[],
): Promise<string> {
  const resp = await fetch(`${OLLAMA}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model,
      stream: false,
      messages: [
        { role: "system", content: system },
        ...messages.map((m) => ({ role: m.role, content: m.content })),
      ],
    }),
  });
  if (!resp.ok) throw new Error(`Ollama chat ${resp.status}`);
  const data = (await resp.json()) as {
    message?: { content?: string };
    error?: string;
  };
  if (data.error) throw new Error(data.error);
  return data.message?.content ?? "";
}
