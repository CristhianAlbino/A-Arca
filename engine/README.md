# engine — motor local da ARCA

Python 3.12 + FastAPI. Roda só em `127.0.0.1`, com token por sessão. É o único componente que acessa banco, volumes, modelos e (quando permitido) a internet.

```
arca_engine/
  __main__.py       python -m arca_engine (imprime {"event":"ready","port","token"} no stdout)
  context.py        AppContext: pastas, banco, configurações, netguard, volumes
  service.py        lógica da API, testável sem FastAPI
  api/app.py        rotas HTTP (FastAPI) sobre o service
  config/           pastas por SO e settings.json
  storage/          SQLite + migrações; volumes por UUID (vol://<uuid>/...)
  netguard/         única porta para a rede
  system/           RAM, VRAM, disco
  security/         token de sessão
```

Desenvolvimento: `python -m venv .venv`, `pip install -e ".[dev,gpu]"`, `python -m pytest -q`.
Rodar para o navegador: `python -m arca_engine --port 8765 --token dev`.
