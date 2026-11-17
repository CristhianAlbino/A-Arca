import type { SystemSnapshot } from "../api/engine";
import { gb, percent } from "../format";

function Meter({ label, used, total, color, value }: {
  label: string;
  used: number;
  total: number;
  color: string;
  value: string;
}) {
  const pct = percent(used, total);
  return (
    <div className="meter">
      <span>{label}</span>
      <span
        className="meter-bar"
        role="meter"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(pct)}
      >
        <span className="meter-fill" style={{ display: "block", width: `${pct}%`, background: color }} />
      </span>
      <span className="meter-value">{value}</span>
    </div>
  );
}

export function SystemStrip({ snapshot }: { snapshot: SystemSnapshot }) {
  const { memory, gpu, data_disk: disk } = snapshot;
  const card = gpu.devices[0];
  const ramColor = memory.percent > 85 ? "var(--danger-text)" : "var(--ok)";
  return (
    <section className="system" aria-label="Estado do sistema">
      <Meter
        label="RAM"
        used={memory.used_bytes}
        total={memory.total_bytes}
        color={ramColor}
        value={`${gb(memory.used_bytes)} / ${gb(memory.total_bytes, 0)}`}
      />
      {card ? (
        <Meter
          label="VRAM"
          used={card.used_bytes}
          total={card.total_bytes}
          color="var(--accent)"
          value={`${gb(card.used_bytes)} / ${gb(card.total_bytes, 0)}`}
        />
      ) : (
        <div className="meter" title={gpu.reason ?? undefined}>
          <span>VRAM</span>
          <span className="muted">indisponível</span>
        </div>
      )}
      <Meter
        label="Disco"
        used={disk.used_bytes}
        total={disk.total_bytes}
        color="#8b8b94"
        value={`${gb(disk.free_bytes, 0)} livres`}
      />
      <div style={{ flex: "1 1 200px", color: "#e4e4e7" }}>
        IA local: <span className="muted">abra a aba IA</span>
      </div>
    </section>
  );
}
