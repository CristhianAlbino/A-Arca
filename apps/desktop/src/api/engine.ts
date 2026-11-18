// Connection to the local ARCA engine.
// Inside the app (Tauri) the shell tells us the port and token.
// In the browser (npm run dev) they come from .env (see .env.example).

export interface EngineConfig {
  baseUrl: string;
  token: string;
}

export interface MemoryInfo {
  total_bytes: number;
  available_bytes: number;
  used_bytes: number;
  percent: number;
}

export interface GpuDevice {
  name: string;
  total_bytes: number;
  used_bytes: number;
  source: string;
}

export interface VolumeStatus {
  id: string;
  label: string;
  available: boolean;
  root: string | null;
  last_root: string | null;
  last_seen_at: string | null;
  total_bytes: number | null;
  free_bytes: number | null;
}

export interface SystemSnapshot {
  platform: { system: string; release: string; machine: string; python: string };
  cpu: { logical_cores: number; percent: number };
  memory: MemoryInfo;
  gpu: { available: boolean; devices: GpuDevice[]; reason: string | null };
  data_disk: { path: string; total_bytes: number; used_bytes: number; free_bytes: number; percent: number | null };
  volumes: VolumeStatus[];
  network_mode: "blocked" | "online";
}

export interface ActivityItem {
  id: number;
  at: string;
  kind: string;
  message: string;
  data: Record<string, unknown> | null;
}

declare global {
  interface Window {
    __TAURI_INTERNALS__?: unknown;
  }
}

let configPromise: Promise<EngineConfig> | null = null;

async function loadConfig(): Promise<EngineConfig> {
  if (window.__TAURI_INTERNALS__) {
    const { invoke } = await import("@tauri-apps/api/core");
    // The shell answers once the engine printed its ready line.
    for (let attempt = 0; attempt < 60; attempt++) {
      const info = await invoke<{ port: number | null; token: string | null; error: string | null }>(
        "engine_info",
      );
      if (info.error) throw new Error(info.error);
      if (info.port && info.token) {
        return { baseUrl: `http://127.0.0.1:${info.port}`, token: info.token };
      }
      await new Promise((r) => setTimeout(r, 250));
    }
    throw new Error("O motor da ARCA não respondeu ao iniciar.");
  }
  const baseUrl = import.meta.env.VITE_ARCA_ENGINE_URL;
  const token = import.meta.env.VITE_ARCA_TOKEN;
  if (!baseUrl || !token) {
    throw new Error("Configure VITE_ARCA_ENGINE_URL e VITE_ARCA_TOKEN (veja apps/desktop/.env.example).");
  }
  return { baseUrl, token };
}

export function engineConfig(): Promise<EngineConfig> {
  configPromise ??= loadConfig().catch((err) => {
    configPromise = null;
    throw err;
  });
  return configPromise;
}

export class EngineError extends Error {
  constructor(message: string, readonly status?: number) {
    super(message);
  }
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const { baseUrl, token } = await engineConfig();
  let response: Response;
  try {
    response = await fetch(baseUrl + path, {
      ...init,
      headers: {
        Authorization: `Bearer ${token}`,
        ...(init.body ? { "Content-Type": "application/json" } : {}),
        ...init.headers,
      },
    });
  } catch {
    throw new EngineError("Sem conexão com o motor local da ARCA.");
  }
  if (!response.ok) {
    let detail = `Erro ${response.status}`;
    try {
      detail = (await response.json()).detail ?? detail;
    } catch {
      /* body was not JSON */
    }
    throw new EngineError(detail, response.status);
  }
  return response.json() as Promise<T>;
}

export const engine = {
  system: () => api<SystemSnapshot>("/system"),
  activity: (limit = 8) => api<ActivityItem[]>(`/activity?limit=${limit}`),
  registerVolume: (path: string, label: string) =>
    api<{ id: string; label: string }>("/volumes", { method: "POST", body: JSON.stringify({ path, label }) }),
  rescanVolumes: () => api<VolumeStatus[]>("/volumes?rescan=true"),
};

// ---------- AI (Phase 2) ----------

export interface AiModel {
  name: string;
  size_bytes: number;
  family: string | null;
  parameter_size: string | null;
  quantization: string | null;
  local: boolean;
}

export interface AiStatus {
  provider: string;
  url: string;
  available: boolean;
  version: string | null;
  reason: string | null;
  models: AiModel[];
  loaded: { name: string; size_bytes: number; vram_bytes: number; expires_at: string | null }[];
  default_model: string | null;
  network_mode: "blocked" | "online";
  idle_unload_minutes: number;
}

export interface ConversationSummary {
  id: string;
  title: string;
  provider: string;
  model: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface StoredMessage {
  id: number;
  role: "user" | "assistant" | "system";
  content: string;
  model: string | null;
  status: "ok" | "interrupted" | "error";
  stats: Record<string, number | null> | null;
  created_at: string;
}

export interface ConversationDetail extends ConversationSummary {
  messages: StoredMessage[];
}

export type ChatEvent =
  | { type: "meta"; conversation_id: string; model: string }
  | { type: "notice"; message: string }
  | { type: "delta"; text: string }
  | { type: "done"; stats: Record<string, number | null> }
  | { type: "error"; message: string };

export const ai = {
  status: () => api<AiStatus>("/ai/status"),
  conversations: () => api<ConversationSummary[]>("/ai/conversations"),
  conversation: (id: string) => api<ConversationDetail>(`/ai/conversations/${encodeURIComponent(id)}`),
  deleteConversation: (id: string) =>
    api<{ deleted: string }>(`/ai/conversations/${encodeURIComponent(id)}`, { method: "DELETE" }),

  /** Streams one answer. Resolves when the stream ends; abort with `signal` to stop. */
  async chat(
    body: { text: string; model: string; conversation_id?: string | null },
    onEvent: (event: ChatEvent) => void,
    signal?: AbortSignal,
  ): Promise<void> {
    const { baseUrl, token } = await engineConfig();
    const response = await fetch(baseUrl + "/ai/chat", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal,
    });
    if (!response.ok || !response.body) {
      throw new EngineError(`Erro ${response.status} ao conversar com a IA.`, response.status);
    }
    await readNdjson(response.body, onEvent);
  },

  deleteModel: (name: string) =>
    api<{ deleted: string }>(`/ai/models/${name.split("/").map(encodeURIComponent).join("/")}`, {
      method: "DELETE",
    }),

  /** Downloads a model through Ollama (needs online mode). Abort with `signal` to stop. */
  async pull(model: string, onEvent: (event: PullEvent) => void, signal?: AbortSignal): Promise<void> {
    const { baseUrl, token } = await engineConfig();
    const response = await fetch(baseUrl + "/ai/models/pull", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ model }),
      signal,
    });
    if (!response.ok || !response.body) {
      let detail = `Erro ${response.status} ao baixar o modelo.`;
      try {
        detail = (await response.json()).detail ?? detail;
      } catch {
        /* body was not JSON */
      }
      throw new EngineError(detail, response.status);
    }
    await readNdjson(response.body, onEvent);
  },
};

export type PullEvent =
  | { type: "progress"; status: string; completed: number | null; total: number | null }
  | { type: "done"; model: string }
  | { type: "error"; message: string };

export const settings = {
  setNetworkMode: (mode: "blocked" | "online") =>
    api<Record<string, unknown>>("/settings", { method: "PUT", body: JSON.stringify({ network_mode: mode }) }),
  setIdleUnloadMinutes: (minutes: number) =>
    api<Record<string, unknown>>("/settings", {
      method: "PUT",
      body: JSON.stringify({ model_idle_unload_minutes: minutes }),
    }),
};

async function readNdjson<T>(body: ReadableStream<Uint8Array>, onEvent: (event: T) => void): Promise<void> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let newline: number;
    while ((newline = buffer.indexOf("\n")) >= 0) {
      const line = buffer.slice(0, newline).trim();
      buffer = buffer.slice(newline + 1);
      if (line) onEvent(JSON.parse(line) as T);
    }
  }
  if (buffer.trim()) onEvent(JSON.parse(buffer) as T);
}

// ---------- Knowledge (Phase 3) ----------

export interface ZimInfo {
  id: string;
  uri: string;
  title: string;
  description: string;
  language: string;
  article_count: number;
  size_bytes: number;
  has_fulltext: boolean;
  /** false when the volume holding it is not connected (kept in the catalog). */
  available: boolean;
  volume_label: string | null;
}

export interface SearchHit {
  zim_id: string;
  zim_title: string;
  path: string;
  title: string;
  snippet: string;
}

export interface Article {
  zim_id: string;
  zim_title: string;
  path: string;
  title: string;
  html: string;
}

export const knowledge = {
  zims: (rescan = false) => api<ZimInfo[]>(`/knowledge/zims${rescan ? "?rescan=true" : ""}`),
  search: (q: string, zim?: string | null) => {
    const params = new URLSearchParams({ q });
    if (zim) params.set("zim", zim);
    return api<SearchHit[]>(`/knowledge/search?${params}`);
  },
  article: (zim: string, path?: string | null) => {
    const params = new URLSearchParams({ zim });
    if (path) params.set("path", path);
    return api<Article>(`/knowledge/article?${params}`);
  },
};

export interface LibraryStatus {
  documents: number;
  searchable: number;
  running: boolean;
  done?: number;
  total?: number;
  current?: string | null;
  last_result?: { added: number; updated: number; unchanged: number; removed: number; failed: number };
  error?: string;
}

export interface LibraryHit {
  id: number;
  uri: string;
  title: string;
  format: "txt" | "md" | "html" | "pdf";
  size_bytes: number;
  volume_label: string;
  available: boolean;
  /** Matched words are wrapped in [[ ]]. */
  snippet: string;
}

export interface LibraryDoc extends Omit<LibraryHit, "snippet"> {
  status: "ok" | "sem-texto" | "erro";
  text: string;
}

export const library = {
  status: () => api<LibraryStatus>("/library/status"),
  index: () => api<LibraryStatus>("/library/index", { method: "POST" }),
  search: (q: string) => api<LibraryHit[]>(`/library/search?${new URLSearchParams({ q })}`),
  doc: (id: number) => api<LibraryDoc>(`/library/docs/${id}`),
};
