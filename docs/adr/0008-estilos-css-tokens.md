# 0008 — Estilos com CSS próprio e tokens (sem Tailwind por enquanto)

- Status: Aceito
- Data: 2026-11-17
- Altera: a linha "UI" de ADR 0001 / AGENTS.md (Tailwind CSS)

## Contexto
O DESIGN.md define poucos tokens (cores, fontes, raios) e telas com layout próprio. A Fase 1 precisa ser construída e conferida visualmente mesmo em ambientes onde não é possível instalar pacotes (sessões de IA sem acesso ao npm).

## Opções consideradas
- **Tailwind CSS**: produtivo, mas adiciona pipeline de build (PostCSS) e classes longas no JSX; não pode ser compilado sem o pacote.
- **CSS próprio com variáveis (`tokens.css`) + um arquivo de estilos por área**: zero dependências, tokens idênticos ao DESIGN.md, legível por qualquer IA, funciona com Vite e com esbuild.

## Decisão
CSS próprio com variáveis CSS. Radix/shadcn e Framer Motion ficam para quando houver componentes complexos (diálogos, menus) ou animações que justifiquem, decididos em novo ADR.

## Consequências
- `apps/desktop/src/styles/tokens.css` é a fonte dos tokens visuais.
- A interface pode ser compilada com esbuild para pré-visualização e testes visuais.
- Migrar para Tailwind no futuro continua possível: os tokens viram tema do Tailwind.
