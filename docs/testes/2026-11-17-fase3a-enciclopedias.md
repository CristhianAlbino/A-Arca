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

## Adendo — empacotamento e catálogo (mesma data e máquina)

**Empacotamento:** o motor gerado pelo PyInstaller (`build.ps1` como estava) respondia `{"detail":"Leitor de ZIM (python-libzim) não instalado no motor."}` em `/knowledge/zims`: o pacote não tinha `libzim.cp312-win_amd64.pyd` nem `zim-9.dll`. Com `--collect-all libzim`:

```
> dist\arca-engine\arca-engine.exe --check-deps
ok       fastapi
ok       uvicorn
ok       psutil
ok       libzim.reader
ok       libzim.search
ok       libzim.suggestion
```

O motor empacotado, com um volume temporário contendo o ZIM de teste, listou `Enciclopédia de teste (3 itens)`, achou `Rádio amador` na busca e leu `Agua` → `Água potável`.

**build.ps1:** com `$ErrorActionPreference = "Stop"`, o Windows PowerShell 5.1 abortava o build na primeira linha `INFO` que o PyInstaller escreve no stderr quando a saída é redirecionada. Trocado por checagem de `$LASTEXITCODE` em cada etapa.

**Motor:** `88 passed, 1 warning in 34.47s`. Novos: enciclopédia de disco desconectado continua listada (`available: false`, nome do disco), a busca a ignora, ler dá 404 citando o disco; o catálogo sobrevive a reiniciar o motor e volta a ficar disponível ao reconectar.

**Navegador:** volume "SSD-TESTE" registrado com o ZIM de teste e depois "desconectado" (marcador renomeado). Primeira tentativa: a lista só marcava "desconectado" depois de clicar em "Procurar" (usava o resultado guardado da última procura). Corrigido: a lista confere na hora se o disco de cada enciclopédia continua conectado (teste `test_unplug_seen_without_rescan`, 13 testes de enciclopédia passando). Depois de "Procurar", a tela mostrou "Enciclopédia de teste · por · 3 itens · 59 KB · Disco “SSD-TESTE” desconectado", botão desativado e campo de busca desativado.

**Lint:** `ruff check arca_engine tests` → `All checks passed!` (havia 28 avisos, a maioria anterior a esta sessão; a sugestão SIM118 em `ai/chat.py` foi recusada porque `sqlite3.Row` itera valores, não chaves).

## Instalador — `scripts\build.ps1` (com a correção acima)

```
    Finished `release` profile [optimized] target(s) in 6m 35s
    Finished 1 bundle at:
        ...\apps\desktop\src-tauri\target\release\bundle\nsis\ARCA_0.1.0_x64-setup.exe (24.17 MiB)
```

- O Tauri baixou as ferramentas do NSIS do GitHub na primeira vez (só no build, nunca no app).
- O motor junto do app (`target\release\engine`) tem `zim-9.dll` e `libzim.cp312-win_amd64.pyd`; `--check-deps` passou.
- `target\release\arca.exe` (versão final, sem instalar): iniciou `arca-engine.exe` como processo filho, escutando só em `127.0.0.1`; fechar a janela encerrou os dois.
- Instalação silenciosa (`ARCA_0.1.0_x64-setup.exe /S`, a pedido do usuário): saída 0, entrada "ARCA 0.1.0" em Programas instalados, atalho no menu Iniciar, `engine\arca-engine.exe --check-deps` ok; o app instalado abriu, subiu o motor em `127.0.0.1:51097` e fechou sem deixar processo.
- **Mas** a instalação foi feita de dentro do app Claude Desktop, que é um pacote MSIX: o Windows redirecionou tudo para `AppData\Local\Packages\Claude_…\LocalCache\Local\ARCA` (área virtual que só o Claude enxerga). Para o usuário, nada foi instalado. Essa cópia foi desinstalada (`uninstall.exe /S`, saída 0) e o instalador foi aberto pelo `explorer.exe`, fora da área virtual, para o usuário concluir.
- Lição para outras sessões de IA: não instalar programas a partir do Claude Desktop; abrir o instalador pelo Explorer ou pedir ao usuário.

### App instalado pelo usuário (instalador aberto pelo Explorer)

- Instalado de verdade em `%LOCALAPPDATA%\ARCA` (arca.exe, engine, uninstall.exe), atalhos no menu Iniciar e na Área de Trabalho.
- Aberto pelo Explorer: `arca.exe` → filho `engine\arca-engine.exe` escutando em `127.0.0.1:57580`. A tela Início levou alguns segundos em "Conectando ao motor…" (partida do motor empacotado com a RAM em ~95% de uso) e depois carregou com RAM, VRAM e disco reais.
- **Falha 1 — tela Conhecimento:** "Sem conexão com o motor local da ARCA". Reproduzido rodando o motor instalado à parte: `GET /knowledge/zims` → 500, `AttributeError: 'ZimLibrary' object has no attribute 'catalog'`. Causa: o instalador foi gerado enquanto o código ainda era editado (o PyInstaller pegou o `service.py` novo com o `kiwix.py` antigo). O código commitado estava certo; o instalador foi gerado de novo a partir do commit `bf93877`, sem edições durante o build, e o motor empacotado novo respondeu `GET /knowledge/zims` → `[] [200]`, `db_schema: 3`.
- **Falha 2 — erro aparecia como "sem conexão":** um erro não tratado saía sem cabeçalhos CORS e a janela não conseguia ler a resposta. Corrigido: o motor responde JSON 500 "Erro interno no motor da ARCA" com CORS e registra o erro no log (teste `test_internal_error_is_json_with_cors`).
- **Falha 3 — duas ARCAs ao mesmo tempo:** abrir o app de novo iniciava uma segunda janela e um segundo motor usando o mesmo banco. Corrigido com `tauri-plugin-single-instance` (a segunda abertura traz a janela existente para frente).
- Motor: `90 passed, 1 warning in 40.94s`; `ruff`: `All checks passed!`; `cargo build` sem avisos.

### Reinstalação com o instalador do commit `bf93877` (usuário, pelo Explorer)

- `arca.exe` atualizado (23:16); o instalador abriu a ARCA ao concluir: um `arca.exe` e um `engine\arca-engine.exe` filho, ambos em `%LOCALAPPDATA%\ARCA`.
- Pedir para abrir a ARCA de novo (atalho/`open_application`) só trouxe a janela existente para frente; continuaram 1 app e 1 motor. → instância única **passou**.
- Tela Início carregou com dados reais (RAM 6,9/8 GB, VRAM 0,5/8 GB, 199 GB livres, OFFLINE).
- Tela Conhecimento: sem erro; mostra as instruções de "Nenhuma enciclopédia encontrada"; "Procurar" respondeu normalmente (nenhum volume registrado ainda). → falha 1 **corrigida** no app instalado.

## Não testado

- ZIMs reais grandes (Wikipédia PT/EN): desempenho da busca e da listagem.
- Rodar o instalador e usar o app instalado.
