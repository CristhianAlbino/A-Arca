import { MODULES, type ModuleId } from "../modules";
import { ArcaMark } from "./Icons";

interface Props {
  current: ModuleId;
  onNavigate: (id: ModuleId) => void;
  networkMode: "blocked" | "online" | null;
}

export function TopBar({ current, onNavigate, networkMode }: Props) {
  return (
    <header className="topbar">
      <button type="button" className="brand" onClick={() => onNavigate("inicio")} aria-label="ARCA — Início">
        <span className="brand-mark">
          <ArcaMark color="var(--accent-ink)" />
        </span>
        <span className="brand-name">ARCA</span>
      </button>

      <nav className="nav" aria-label="Principal">
        {MODULES.map((m) => (
          <button
            key={m.id}
            type="button"
            aria-current={m.id === current ? "page" : undefined}
            onClick={() => onNavigate(m.id)}
          >
            {m.label}
          </button>
        ))}
      </nav>

      <NetworkPill mode={networkMode} />
    </header>
  );
}

function NetworkPill({ mode }: { mode: "blocked" | "online" | null }) {
  if (mode === null) {
    return <span className="pill pill-warn">Conectando ao motor…</span>;
  }
  if (mode === "online") {
    return (
      <span className="pill pill-warn" title="Recursos online permitidos pela lista de hosts autorizados">
        <span className="dot" />
        ONLINE · com permissão
      </span>
    );
  }
  return (
    <span className="pill pill-ok" title="Nenhuma conexão externa é feita">
      <span className="dot" />
      OFFLINE · tudo local
    </span>
  );
}
