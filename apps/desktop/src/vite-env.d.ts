/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_ARCA_ENGINE_URL?: string;
  readonly VITE_ARCA_TOKEN?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
