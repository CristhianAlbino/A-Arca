interface Props {
  id: string;
  title: string;
  phase: number;
  message: string;
}

// A shelf that has no content yet. It says when it will, instead of showing fake items.
export function EmptyRow({ id, title, phase, message }: Props) {
  return (
    <section className="section" aria-labelledby={id}>
      <div className="section-head">
        <h2 id={id}>{title}</h2>
      </div>
      <div className="row">
        <div className="card card-empty">
          <span className="phase">CHEGA NA FASE {phase}</span>
          <strong>Nada aqui ainda</strong>
          <span>{message}</span>
        </div>
      </div>
    </section>
  );
}
