import type { ActivityItem } from "../api/engine";
import { when } from "../format";

export function Activity({ items }: { items: ActivityItem[] }) {
  return (
    <section className="section" aria-labelledby="row-activity">
      <div className="section-head">
        <h2 id="row-activity">Atividade recente</h2>
        <span className="hint">Fica só neste computador</span>
      </div>
      {items.length === 0 ? (
        <p className="muted" style={{ margin: 0 }}>Nenhuma atividade registrada.</p>
      ) : (
        <ul className="activity">
          {items.map((a) => (
            <li key={a.id}>
              <time dateTime={a.at}>{when(a.at)}</time>
              <span>{a.message}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
