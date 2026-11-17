import { useState, type FormEvent } from "react";
import { engine, type VolumeStatus } from "../api/engine";
import { gb } from "../format";
import { DiskIcon, PlusIcon, RefreshIcon } from "./Icons";

interface Props {
  volumes: VolumeStatus[];
  onChanged: () => void;
}

export function Volumes({ volumes, onChanged }: Props) {
  const [adding, setAdding] = useState(false);
  const [busy, setBusy] = useState(false);

  async function rescan() {
    setBusy(true);
    try {
      await engine.rescanVolumes();
      onChanged();
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="section" aria-labelledby="row-volumes">
      <div className="section-head">
        <h2 id="row-volumes">Armazenamento</h2>
        <span className="hint">Discos e pastas onde a ARCA guarda o acervo</span>
      </div>
      <div className="row">
        {volumes.map((v) => (
          <article key={v.id} className={`card card-volume${v.available ? "" : " unavailable"}`}>
            <DiskIcon color={v.available ? "var(--ok)" : "var(--text-faint)"} />
            <h3>{v.label}</h3>
            {v.available ? (
              <>
                <span>{gb(v.free_bytes, 0)} livres de {gb(v.total_bytes, 0)}</span>
                <span className="path">{v.root}</span>
              </>
            ) : (
              <>
                <span className="pill pill-warn" style={{ alignSelf: "flex-start" }}>DESCONECTADO</span>
                <span className="path">Último local: {v.last_root ?? "—"}</span>
              </>
            )}
          </article>
        ))}

        {adding ? (
          <AddVolumeForm
            onDone={() => {
              setAdding(false);
              onChanged();
            }}
            onCancel={() => setAdding(false)}
          />
        ) : (
          <div className="card card-empty">
            <strong>{volumes.length ? "Adicionar outro volume" : "Nenhum volume registrado ainda"}</strong>
            <span>
              Escolha uma pasta (no SSD interno ou externo). A ARCA cria nela um arquivo de identificação
              e a reconhece mesmo se a letra do disco mudar.
            </span>
            <div className="actions">
              <button type="button" className="btn btn-primary" onClick={() => setAdding(true)}>
                <PlusIcon /> Adicionar volume
              </button>
              {volumes.length > 0 && (
                <button type="button" className="btn btn-secondary" onClick={rescan} disabled={busy}>
                  <RefreshIcon /> Procurar discos
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

function AddVolumeForm({ onDone, onCancel }: { onDone: () => void; onCancel: () => void }) {
  const [path, setPath] = useState("");
  const [label, setLabel] = useState("ARCA-EXT");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await engine.registerVolume(path.trim(), label.trim());
      onDone();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="form" onSubmit={submit}>
      <label>
        Pasta do volume
        <input
          required
          value={path}
          onChange={(e) => setPath(e.target.value)}
          placeholder="Ex.: E:\ARCA"
          autoFocus
        />
      </label>
      <label>
        Nome
        <input required value={label} onChange={(e) => setLabel(e.target.value)} maxLength={40} />
      </label>
      {error && <p className="error" role="alert">{error}</p>}
      <div className="actions">
        <button type="submit" className="btn btn-primary" disabled={busy}>
          Registrar
        </button>
        <button type="button" className="btn btn-secondary" onClick={onCancel}>
          Cancelar
        </button>
      </div>
    </form>
  );
}
