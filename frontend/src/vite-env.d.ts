/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly mode: string;
  readonly base: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}