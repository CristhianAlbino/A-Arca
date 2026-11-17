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
