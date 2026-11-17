import { useCallback, useEffect, useState } from "react";
import { engine, type ActivityItem, type SystemSnapshot } from "./api/engine";
import { TopBar } from "./components/TopBar";
import { MODULES, type ModuleId } from "./modules";
import { Chat } from "./screens/Chat";
import { Home } from "./screens/Home";
import { Knowledge } from "./screens/Knowledge";
import { Placeholder } from "./screens/Placeholder";

const REFRESH_MS = 5000;

export function App() {
  const [current, setCurrent] = useState<ModuleId>("inicio");
  const [snapshot, setSnapshot] = useState<SystemSnapshot | null>(null);
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [snap, acts] = await Promise.all([engine.system(), engine.activity(8)]);
      setSnapshot(snap);
      setActivity(acts);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, []);

  useEffect(() => {
    refresh();
    const timer = window.setInterval(refresh, REFRESH_MS);
    return () => window.clearInterval(timer);
  }, [refresh]);

  const module = MODULES.find((m) => m.id === current)!;

  return (
    <>
      <TopBar current={current} onNavigate={setCurrent} networkMode={snapshot?.network_mode ?? null} />
      {error && (
        <div className="banner" role="alert">
          {error} Tentando de novo a cada {REFRESH_MS / 1000} segundos.
        </div>
      )}
      {current === "ia" ? (
        <Chat />
      ) : current === "conhecimento" ? (
        <Knowledge />
      ) : current === "inicio" ? (
        snapshot ? (
          <Home snapshot={snapshot} activity={activity} onRefresh={refresh} onNavigate={setCurrent} />
        ) : (
          !error && <p className="placeholder muted">Iniciando o motor local…</p>
        )
      ) : (
        <Placeholder module={module} />
      )}
    </>
  );
}
