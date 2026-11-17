// Sections in the top bar. `phase` says when each one gets real content.
export type ModuleId =
  | "inicio"
  | "ia"
  | "conhecimento"
  | "sobrevivencia"
  | "entretenimento"
  | "mapas"
  | "arquivos"
  | "modulos";

export interface ModuleInfo {
  id: ModuleId;
  label: string;
  phase: number;
  summary: string;
}

export const MODULES: ModuleInfo[] = [
  { id: "inicio", label: "Início", phase: 1, summary: "Painel central da ARCA." },
  {
    id: "ia",
    label: "IA",
    phase: 2,
    summary: "Conversa com modelos locais (Ollama) e, se você ligar, modelos online, sempre com referências às fontes.",
  },
  {
    id: "conhecimento",
    label: "Conhecimento",
    phase: 3,
    summary: "Wikipédia em português e inglês, livros e documentos, com busca textual e semântica sem internet.",
  },
  {
    id: "sobrevivencia",
    label: "Sobrevivência",
    phase: 4,
    summary: "Acervo das 18 áreas (água, saúde, energia, rádio...). Respostas só com fontes confiáveis citadas.",
  },
  {
    id: "entretenimento",
    label: "Entretenimento",
    phase: 6,
    summary:
      "Bíblia, literatura, quadrinhos e música do seu acervo (Fase 6). Jogos leves chegam com o sistema de módulos (Fase 7).",
  },
  {
    id: "mapas",
    label: "Mapas",
    phase: 5,
    summary: "Mapas offline do OpenStreetMap, busca de cidades e pontos salvos.",
  },
  {
    id: "arquivos",
    label: "Arquivos",
    phase: 6,
    summary: "Importar, organizar, indexar e consultar seus documentos pela IA.",
  },
  {
    id: "modulos",
    label: "Módulos",
    phase: 7,
    summary: "Extensões com permissões declaradas: instalar, atualizar, desativar e remover.",
  },
];

export const CURRENT_PHASE = 2;
