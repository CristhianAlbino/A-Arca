# 2026-11-17 — Fase 3A (enciclopédias ZIM) — testes

- **Máquina:** notebook do Cris (Windows 11 Pro 10.0.26300), Python 3.12.10, libzim 3.13.1, Node 20.20.2
- **Branch:** `feat/fase-3-kiwix`
- **Dados de teste:** ZIM real pequeno gerado por `engine/tests/fakes/make_zim.py` (3 artigos, 1 imagem, 1 redirecionamento, índice de texto completo em português). Nenhum ZIM baixado.

## 1. Motor — `cd engine; .\.venv\Scripts\python -m pytest -q`

```
87 passed, 1 warning in 37.60s
```

11 testes novos em `tests/test_kiwix.py`:

- pastas ocultas e "System Volume Information" são ignoradas;
- o ZIM aparece com URI `vol://…/03_ENCICLOPEDIAS/teste.zim` (sem letra de unidade);
- disco desconectado: a enciclopédia some da lista e ler artigo dá 404;
- busca por texto completo ("ferver") acha o artigo, com trecho sem HTML e sem espaço antes de pontuação;
- ZIM sem índice de texto usa busca por título;
- redirecionamento "Agua" → "Água potável"; página inicial quando não se informa artigo;
- HTML limpo: sem `<script>`, `onclick`, `style=`; link interno vira `data-zim-path`, externo vira `data-external` sem `href`; imagem embutida como `data:image/png`;
- links relativos de subpastas (`../B/Outro#sec`) e imagens externas (viram "[imagem: foto]");
- artigo inexistente e enciclopédia desconhecida → 404;
- rotas HTTP: 401 sem token, lista, busca, artigo, busca longa demais → 400.

## 2. Interface — `npx tsc --noEmit` e `npx vite build`

Sem erros (`index-DmP-WGBi.js 426.52 kB`).

## 3. Ponta a ponta no navegador (motor + Vite, volume temporário com o ZIM de teste)

1. Conhecimento → "Procurar": lista "Enciclopédia de teste · por · 3 itens".
2. Buscar "ferver": 2 resultados ("Filtro de água", "Água potável") com trechos.
3. Abrir "Filtro de água": título certo, 0 `<script>`, sem `onclick`.
4. Clicar no link interno "ferver": abre "Água potável", aparece "← Voltar".
5. Em "Água potável": imagem embutida (`data:image/png;base64,…`), nenhum `href` externo; clicar no link da Wikipédia online só mostra "Link para fora da ARCA (não abre offline): https://pt.wikipedia.org/wiki/Agua" e a página não sai do app.
6. "← Voltar" retorna a "Filtro de água".

Conferido pelo DOM (captura de tela indisponível com a janela do app minimizada).

## Não testado

- ZIMs reais grandes (Wikipédia PT/EN): desempenho da busca e da listagem.
- Empacotamento do `libzim` no instalador (PyInstaller).
