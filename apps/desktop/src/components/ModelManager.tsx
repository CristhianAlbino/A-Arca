// Phase 2B: download (online mode only) and remove local models.
import { useRef, useState, type FormEvent } from "react";

import { ai, settings, type AiStatus } from "../api/engine";
import { gb, percent } from "../format";

interface Props {
  status: AiStatus;
  busy: boolean;
  onChanged: () => void | Promise<void>;
  onClose: () => void;
}

const IDLE_CHOICES = [1, 5, 15, 30, 60];

/** Fixed choices, plus the current value if it was set to something else. */
function idleOptions(current: number): number[] {
  return [...new Set([...IDLE_CHOICES, current])].sort((a, b) => a - b);
}

interface Progress {
  status: string;
  completed: number | null;
  total: number | null;
}

export function ModelManager({ status, busy, onChanged, onClose }: Props) {
  const [name, setName] = useState("");
  const [pulling, setPulling] = useState<string | null>(null);
  const [progress, setProgress] = useState<Progress | null>(null);
  const [message, setMessage] = useState<{ kind: "ok" | "error"; text: string } | null>(null);
  const [removing, setRemoving] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const online = status.network_mode === "online";

  async function goOnline() {
    try {
      await settings.setNetworkMode("online");
      await onChanged();
    } catch (err) {
      setMessage({ kind: "error", text: err instanceof Error ? err.message : String(err) });
    }
  }

  async function goOffline() {
    try {
      await settings.setNetworkMode("blocked");
      await onChanged();
    } catch (err) {
      setMessage({ kind: "error", text: err instanceof Error ? err.message : String(err) });
    }
  }

  async function setIdle(minutes: number) {
    try {
      await settings.setIdleUnloadMinutes(minutes);
      await onChanged();
    } catch (err) {
      setMessage({ kind: "error", text: err instanceof Error ? err.message : String(err) });
    }
  }

  async function pull(e: FormEvent) {
    e.preventDefault();
    const model = name.trim();
    if (!model || pulling) return;
    const controller = new AbortController();
    abortRef.current = controller;
    setPulling(model);
    setProgress({ status: "iniciando", completed: null, total: null });
    setMessage(null);
    try {
      await ai.pull(
        model,
        (ev) => {
          if (ev.type === "progress") setProgress(ev);
          else if (ev.type === "done") setMessage({ kind: "ok", text: `Modelo ${ev.model} instalado.` });
          else setMessage({ kind: "error", text: ev.message });
        },
        controller.signal,
      );
      setName("");
    } catch (err) {
      if (controller.signal.aborted) {
        setMessage({ kind: "error", text: "Download cancelado. O Ollama continua de onde parou se você baixar de novo." });
      } else {
        setMessage({ kind: "error", text: err instanceof Error ? err.message : String(err) });
      }
    } finally {
      abortRef.current = null;
      setPulling(null);
      setProgress(null);
      await onChanged();
    }
  }

  async function remove(model: string) {
    if (!window.confirm(`Remover o modelo ${model} deste computador? Para usar de novo será preciso baixar outra vez.`)) {
      return;
    }
    setRemoving(model);
    setMessage(null);
    try {
      await ai.deleteModel(model);
      setMessage({ kind: "ok", text: `Modelo ${model} removido.` });
    } catch (err) {
      setMessage({ kind: "error", text: err instanceof Error ? err.message : String(err) });
    } finally {
      setRemoving(null);
      await onChanged();
    }
  }

  const pct = progress?.total ? percent(progress.completed ?? 0, progress.total) : null;

  return (
    <section className="models-panel" aria-label="Gerenciar modelos">
      <div className="models-head">
        <h2>Modelos instalados</h2>
        <button type="button" className="btn btn-secondary btn-small" onClick={onClose}>
          Fechar
        </button>
      </div>

      {status.models.length === 0 ? (
        <p className="muted">Nenhum modelo instalado.</p>
      ) : (
        <ul className="models-list">
          {status.models.map((m) => (
            <li key={m.name}>
              <span className="models-name">{m.name}</span>
              <span className="muted">
                {[m.parameter_size, m.quantization, gb(m.size_bytes)].filter(Boolean).join(" · ")}
              </span>
              <button
                type="button"
                className="btn btn-outline btn-small"
                onClick={() => remove(m.name)}
                disabled={busy || removing !== null || pulling !== null}
                aria-label={`Remover modelo ${m.name}`}
              >
                {removing === m.name ? "Removendo…" : "Remover"}
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="models-idle">
        <label htmlFor="descarga">Tirar o modelo da memória depois de</label>
        <select
          id="descarga"
          className="model-select"
          value={status.idle_unload_minutes}
          onChange={(e) => setIdle(Number(e.target.value))}
        >
          {idleOptions(status.idle_unload_minutes).map((m) => (
            <option key={m} value={m}>
              {m < 60 ? `${m} min` : `${m / 60} h`} sem uso
            </option>
          ))}
        </select>
        <span className="muted">Vale a partir da próxima mensagem. Menos tempo libera RAM e VRAM mais cedo.</span>
      </div>

      <h2>Baixar modelo</h2>
      {!online ? (
        <div className="models-offline">
          <p>
            A ARCA está em modo offline, então nada é baixado da internet. Para baixar um modelo, ligue o modo
            online; depois do download você pode voltar ao offline.
          </p>
          <button type="button" className="btn btn-secondary btn-small" onClick={goOnline}>
            Ligar modo online
          </button>
        </div>
      ) : (
        <>
          <form className="models-form" onSubmit={pull}>
            <label className="sr-only" htmlFor="modelo-baixar">
              Nome do modelo
            </label>
            <input
              id="modelo-baixar"
              className="chat-search"
              placeholder="ex.: llama3.2:3b"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={pulling !== null}
              autoComplete="off"
              spellCheck={false}
            />
            {pulling ? (
              <button type="button" className="btn btn-outline btn-small" onClick={() => abortRef.current?.abort()}>
                Cancelar
              </button>
            ) : (
              <button type="submit" className="btn btn-primary btn-small" disabled={!name.trim()}>
                Baixar
              </button>
            )}
          </form>
          <p className="muted models-hint">
            Os nomes vêm da biblioteca do Ollama (ollama.com/library). Com 8 GB de RAM, prefira modelos de 3–4B.
          </p>
          <div className="models-online">
            <span className="pill pill-warn">ONLINE</span>
            <button type="button" className="link-button" onClick={goOffline} disabled={pulling !== null}>
              Voltar ao modo offline
            </button>
          </div>
        </>
      )}

      {pulling && progress && (
        <div className="models-progress" aria-live="polite">
          <span>
            {pulling}: {progress.status}
            {pct != null && ` · ${gb(progress.completed)} de ${gb(progress.total)}`}
          </span>
          {pct != null && (
            <div className="meter-bar">
              <div className="meter-fill" style={{ width: `${pct}%`, background: "var(--accent)" }} />
            </div>
          )}
        </div>
      )}

      {message && (
        <p className={message.kind === "error" ? "models-msg models-msg-error" : "models-msg"} role="status">
          {message.text}
        </p>
      )}
    </section>
  );
}
