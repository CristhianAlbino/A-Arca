# 0007 — Volumes por UUID e Google Drive como origem

- Status: Aceito (Drive com 5 TB confirmado pelo usuário em 2026-11-17)
- Data: 2026-11-17

## Contexto
O conteúdo começa na nuvem e migra para SSD interno e externo. Letras de unidade mudam, o SSD externo pode ser desconectado, e o app final não pode depender de login do Google.

## Opções consideradas
- Caminhos absolutos: quebram ao trocar de letra ou de disco.
- Integração direta com a API do Drive: exigiria OAuth dentro do app.
- **Volumes por UUID** + **Google Drive para computador** como ponte para a pasta local.

## Decisão
- Cada disco recebe `.arca-volume.json` com UUID; arquivos registrados como `vol://<uuid>/...`.
- O acervo da Etapa 1 fica no Drive (conta de 5 TB), pasta `ARCA/`, sincronizado pelo Google Drive para computador. O Importador lê a pasta local.
- Migrações copiam, verificam SHA-256 e só então atualizam o catálogo; nunca apagam.

## Consequências
- Nenhum token ou SDK do Google no app.
- Volume ausente = conteúdo marcado indisponível, resto funciona.
- Banco de dados sempre no SSD interno (ADR 0003).
