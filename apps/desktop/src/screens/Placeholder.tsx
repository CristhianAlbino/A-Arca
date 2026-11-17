import type { ModuleInfo } from "../modules";

// Shown for sections that are not built yet. Clearly labelled: no fake features.
export function Placeholder({ module }: { module: ModuleInfo }) {
  return (
    <main className="placeholder">
      <p className="eyebrow">EM CONSTRUÇÃO · CHEGA NA FASE {module.phase}</p>
      <h1>{module.label}</h1>
      <p>{module.summary}</p>
      <p className="muted">
        O roadmap completo está em docs/fases/README.md no repositório do projeto.
      </p>
    </main>
  );
}
