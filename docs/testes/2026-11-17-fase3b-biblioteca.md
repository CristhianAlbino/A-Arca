# 2026-11-17 — Fase 3B (biblioteca própria, busca textual) — testes

- **Máquina:** notebook do Cris (Windows 11 Pro 10.0.26300), Python 3.12.10, SQLite 3.49.1 (FTS5), pypdf 6.21.4, Node 20.20.2
- **Branch:** `feat/fase-3-biblioteca`
- **Dados de teste:** arquivos criados na hora: `.txt`, `.md`, `.html` e um PDF real mínimo gerado por `engine/tests/fakes/make_pdf.py` (texto em WinAnsi, com acentos). Nenhum documento pessoal usado.

## 1. Motor — `cd engine; .\.venv\Scripts\python -m pytest -q`

```
98 passed, 1 warning in 34.54s
```

`ruff check arca_engine tests` → `All checks passed!`

8 testes novos em `tests/test_library.py`:

- consulta FTS5 segura: palavras do usuário entre aspas (`NEAR`, `OR`, `*`, `"` viram texto comum), prefixo só na última;
- títulos: primeira linha curta do `.txt`, primeiro `#` do Markdown, `<title>` do HTML (sem o conteúdo de `<script>`), título do PDF;
- indexa 4 arquivos; ignora pasta oculta e `.jpg`; "agua" (sem acento) acha o `.txt` e o PDF; trecho com `[[queimadura]]`; todas as palavras exigidas;
- reindexar: 4 inalterados; arquivo alterado é atualizado, arquivo apagado sai do índice;
- disco desconectado: nada é removido, resultados marcados `available: false`;
- arquivo vazio → `sem-texto`; PDF quebrado → `erro` sem parar a indexação;
- HTTP: 401 sem token, indexação em segundo plano (202) até `running: false`, busca, documento, busca longa → 400.

## 2. Interface — `npx tsc --noEmit` e `npx vite build`

Sem erros (`index-A_c2v6A8.js 430.87 kB`).

## 3. Navegador (motor + Vite, volume temporário com ZIM de teste, .txt, .md e PDF)

1. Conhecimento → Biblioteca: "0 documentos" e a explicação; "Indexar" → "3 documentos · Última indexação: 3 novos, 0 atualizados, 0 removidos".
2. Buscar `agua`: "4 resultados", seções **Biblioteca** (agua.txt, "Manual de primeiros socorros") e **Enciclopédias** ("Água potável", "Filtro de água"); "água" destacado nos trechos.
3. Abrir o PDF: título "Manual de primeiros socorros", "PDF · SSD-TESTE", texto "Primeiros socorros / Em caso de queimadura, resfrie com água corrente por 20 minutos."
4. O título do `.txt` aparecia como "agua" (nome do arquivo); passou a usar a primeira linha ("Purificação de água") — coberto em `test_extracts_titles_and_text`.

Conferido pelo DOM.

## Não testado

- Acervo real (milhares de PDFs do Drive): tempo de indexação e tamanho do banco.
- PDFs escaneados reais (devem aparecer como "sem texto" até o OCR da Fase 6).

## 4. Instalador (`scripts\build.ps1` a partir do commit `c579040`, sem edições durante o build)

- `--check-deps`: `ok` para fastapi, uvicorn, psutil, libzim (3 módulos) e `pypdf`.
- `ARCA_0.1.0_x64-setup.exe` gerado (24.97 MiB).
- Motor empacotado com volume temporário contendo um PDF: indexação `{'added': 1, ... 'failed': 0}`; busca `queimadura` → `('Manual', 'pdf')`.
- Instalada pelo usuário (instalador aberto pelo Explorer). `arca.exe` de 23:32; `--check-deps` do motor instalado: tudo `ok`, inclusive `pypdf`.
- O instalador abriu a ARCA ao concluir; motor escutando em `127.0.0.1:57807`. A tela ficou ~40 s em "Conectando ao motor…" com ~700 MB de RAM livre (de 8 GB) e depois carregou normalmente.
- Conhecimento: seções Enciclopédias e Biblioteca presentes; "Indexar" sem volume registrado → "0 documentos · Última indexação: 0 novos, 0 atualizados, 0 removidos", sem erro.
- Observação: a partida do motor empacotado fica lenta com pouca RAM livre; reavaliar depois do upgrade para 24 GB (se continuar lento, mostrar na tela que o motor está iniciando há X segundos).

## Adendo — EPUB e livros reais

**Motor:** `101 passed, 1 warning in 39.47s`; `ruff`: `All checks passed!`. Novos: EPUB lido na ordem do `content.opf` (capítulos guardados fora de ordem no zip), título do livro, sem CSS/tags; EPUB quebrado conta como erro sem parar a indexação; volume com caminho relativo é recusado.

**Livros reais de `G:\Meu Drive\ARCA\03_LIVROS` (só leitura, `extract()` direto, sem indexar):**

| Arquivo | Formato | Texto | Tempo |
| --- | --- | --- | --- |
| Amanhecer na Colheita - Suzanne Collins.pdf | pdf | 657.803 caracteres | 24,0 s |
| Amanhecer na Colheita .epub | epub | 672.941 caracteres | 1,8 s |
| Amanhecer na Colheita PDF.pdf | pdf | 657.803 caracteres (mesmo texto do outro PDF: duplicado) | 18,9 s |
| Jogos_Vorazes_#0_5_….pdf | pdf | 890.039 caracteres | 26,3 s |
| Trilogia Jogos Vorazes - Suzanne Collins.pdf | pdf | 1.857.859 caracteres | 53,5 s |

Todos com título correto. **Ponto de atenção:** `pypdf` leva ~20–50 s por livro neste notebook (8 GB de RAM, quase toda em uso). Um acervo de milhares de PDFs levaria horas na primeira indexação. Opção a avaliar: `pypdfium2` (licença Apache/BSD, bem mais rápido); `PyMuPDF` foi descartado pela licença AGPL.

**Instalador** do commit `652a41f`: `--check-deps` ok (inclui `pypdf`), 25.04 MiB. Ainda não instalado.

**Registro da pasta do Drive pelo app instalado (automação de tela):** o primeiro texto digitado foi colado da área de transferência ("ollama") e revelou o defeito do caminho relativo (corrigido no commit `6a7a9c9`, ainda fora do instalador). Na segunda tentativa as teclas não chegaram à ARCA (provavelmente foram para outra janela em primeiro plano); a automação foi interrompida e o registro ficou para o usuário fazer.

## App instalado com conteúdo real (2026-11-18, usuário + conferência)

- Instalador do commit `652a41f` instalado pelo usuário (`arca.exe` de 23:57); um `arca.exe` e um `arca-engine.exe`.
- O usuário registrou `G:\Meu Drive\ARCA` como volume "DRIVE" (marcador `.arca-volume.json` criado na pasta) e indexou: **"5 documentos · Última indexação: 5 novos, 0 atualizados, 0 removidos"**.
- Busca `katniss`: **5 resultados** na seção Biblioteca (Trilogia, A Cantiga dos Pássaros e das Serpentes, Amanhecer na Colheita em EPUB e nos dois PDFs), formato e disco certos, palavra destacada nos trechos.
- Abrir a Trilogia (1,86 milhão de caracteres): o texto inteiro aparece no leitor, com rolagem, sem travar.

### Melhorias anotadas a partir do uso real

1. **Duplicatas:** o mesmo livro aparecia 3 vezes (EPUB + 2 PDFs iguais). **Feito** (ver abaixo).
2. **Leitor abria no início.** **Feito** (ver abaixo).
3. **PDF lento** (~20–50 s por livro com `pypdf`): avaliar `pypdfium2`.
4. **Caminho relativo** ao registrar volume: corrigido no commit `6a7a9c9` (entra no próximo instalador).

## Correções a partir do uso real (2026-11-18, commit `9ed6c76`)

**Motor:** `102 passed, 1 warning in 33.06s`; `ruff`: `All checks passed!`. Novo teste: EPUB e TXT do mesmo livro viram um resultado com `copies`; um livro de mesmo título e texto muito maior continua separado.

- **Duplicatas agrupadas:** mesmo título (sem acentos, maiúsculas e pontuação) e texto até 10% diferente. Nos livros reais, EPUB (672.941 caracteres) e PDFs (657.803) diferem 2,2% → um resultado só.
- **Leitor vai ao trecho:** palavras buscadas marcadas no texto (sem diferenciar acentos/maiúsculas, só no começo de palavra, até 300 marcas), rolagem até a primeira, botões Anterior/Próxima e contador fixo no topo.

**Navegador** (volume temporário com o mesmo livro em EPUB e TXT, viewport 1280×800): busca `katniss` → "1 resultado", "Também em: Texto"; leitor "1 de 2 ocorrências", primeira marca visível no meio da tela (390/800 px); "Próxima" → "2 de 2", também visível; barra fixa no topo.

**Instalador** do commit `9ed6c76`: 7 dependências `ok`, 25.04 MiB. Inclui também a correção do caminho relativo (`6a7a9c9`). Ainda não instalado.

### App instalado (instalador do `9ed6c76`, 2026-11-18)

- Busca `katniss` nos livros reais: **3 resultados** (antes 5); "Amanhecer na Colheita" uma vez só (EPUB), com "Também em: PDF, PDF".
- Leitor da Trilogia: "1 de 300+ ocorrências", palavra atual destacada e a tela já posicionada nela.
- **Defeito visto só no app:** ao rolar, a barra "Anterior/Próxima" ficava escondida atrás do cabeçalho da ARCA (os dois fixos no topo; no teste do navegador a página não rolava o suficiente para aparecer). Corrigido no commit seguinte: a barra fica logo abaixo do cabeçalho, medindo a altura real dele. **Ainda não testado no app instalado.**
