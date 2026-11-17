import type { ActivityItem, SystemSnapshot } from "../api/engine";
import { Activity } from "../components/Activity";
import { EmptyRow } from "../components/EmptyRow";
import { SystemStrip } from "../components/SystemStrip";
import { Volumes } from "../components/Volumes";
import type { ModuleId } from "../modules";

interface Props {
  snapshot: SystemSnapshot;
  activity: ActivityItem[];
  onRefresh: () => void;
  onNavigate: (id: ModuleId) => void;
}

export function Home({ snapshot, activity, onRefresh, onNavigate }: Props) {
  const hasVolume = snapshot.volumes.length > 0;
  return (
    <main className="page">
      <section className="hero" aria-label="Boas-vindas">
        <div className="hero-text">
          <p className="eyebrow">ARCA · FASE 1</p>
          <h1>Seu acervo começa aqui</h1>
          <p className="lead">
            A ARCA já roda neste computador sem internet. Agora ela precisa de um lugar para guardar o
            acervo e de conteúdo para ler.
          </p>
          <ol className="hero-steps">
            <li>{hasVolume ? "Volume de armazenamento registrado." : "Registre um volume de armazenamento logo abaixo."}</li>
            <li>
              Coloque livros e materiais no Drive em <code>ARCA/01_ENTRADA</code> ou na categoria certa.
            </li>
            <li>A importação e a leitura chegam nas próximas fases.</li>
          </ol>
          <div className="actions">
            <a className="btn btn-primary" href="#row-volumes">
              {hasVolume ? "Ver armazenamento" : "Registrar volume"}
            </a>
            <button type="button" className="btn btn-secondary" onClick={() => onNavigate("ia")}>
              Conversar com a IA
            </button>
          </div>
        </div>
        <div className="hero-art" aria-hidden="true">
          <svg width="260" height="260" viewBox="0 0 300 300" fill="none">
            <circle cx="150" cy="150" r="140" stroke="#1f1f23" strokeWidth="1.5" />
            <circle cx="150" cy="150" r="104" stroke="#26262b" strokeWidth="1.5" />
            <circle cx="150" cy="150" r="68" stroke="#2e2e34" strokeWidth="1.5" />
            <path
              d="M70 150h160l-22 62H92z M108 150v-46h84v46 M150 104V76"
              stroke="var(--accent)"
              strokeWidth="6"
              strokeLinejoin="round"
              strokeLinecap="round"
            />
          </svg>
        </div>
      </section>

      <SystemStrip snapshot={snapshot} />

      <Volumes volumes={snapshot.volumes} onChanged={onRefresh} />

      <EmptyRow
        id="row-continuar"
        title="Continuar lendo"
        phase={3}
        message="Livros e documentos que você abrir aparecem aqui, com o ponto onde parou."
      />
      <EmptyRow
        id="row-sobrevivencia"
        title="Sobrevivência"
        phase={4}
        message="As 18 áreas (água, saúde, energia, rádio...) com fontes confiáveis."
      />
      <EmptyRow
        id="row-entretenimento"
        title="Entretenimento"
        phase={6}
        message="Bíblia, literatura, quadrinhos e música. Jogos leves chegam com os módulos (Fase 7)."
      />
      <EmptyRow
        id="row-enciclopedias"
        title="Enciclopédias"
        phase={3}
        message="Wikipédia em português e inglês, WikiMed, Wikibooks e outras, sem internet."
      />

      <Activity items={activity} />
    </main>
  );
}
