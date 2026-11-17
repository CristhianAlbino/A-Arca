# Armazenamento, migração e backup

## Volumes

A ARCA nunca guarda caminhos fixos (`E:\ARCA\mapas`). Cada disco usado recebe na raiz um `.arca-volume.json`:

```json
{ "volume_id": "7b1c…-uuid", "label": "ARCA-EXT", "created_at": "2026-11-17T00:00:00Z", "arca_schema": 1 }
```

Arquivos são registrados como `vol://<uuid>/<caminho relativo>`. Se o SSD externo mudar de letra, a ARCA o reencontra pelo UUID. Conteúdo de volume ausente aparece como indisponível, nunca some.

| Classe de dado | Local padrão |
| --- | --- |
| Aplicativo | `C:\Program Files\ARCA` |
| Configuração | `%APPDATA%\ARCA\config` |
| Banco SQLite | `%LOCALAPPDATA%\ARCA\data` (sempre SSD interno) |
| Modelos essenciais | SSD interno, pasta configurável (`OLLAMA_MODELS`) |
| Modelos extras, bibliotecas, mapas | SSD externo |
| Backups | SSD externo + cópia opcional no Drive (`ARCA/99_BACKUPS`) |

## Origem do conteúdo (Etapa 1)

O acervo fica no Google Drive (conta de 5 TB), pasta `ARCA/`, sincronizado pelo **Google Drive para computador**. O app nunca fala com o Drive: o **Importador** lê a pasta local, copia para o volume de destino, calcula SHA-256 e atualiza o catálogo (`so-nuvem → baixado → verificado → indexado`). Arquivos públicos também registram URL oficial e checksum publicado, para poderem ser baixados de novo da fonte.

Estrutura do Drive:

```
ARCA/
├─ LEIA-ME — Como usar a pasta ARCA
├─ 00_CATALOGO/catalogo_arca (planilha)
├─ 01_ENTRADA  02_ENCICLOPEDIAS  03_LIVROS  04_MANUAIS
├─ 05_SOBREVIVENCIA/ 01_Agua … 18_Seguranca_Emergencias
├─ 06_MAPAS  07_CURSOS  08_DOC_TECNICA  09_PESQUISAS  10_IMAGENS
├─ 11_ARTES  13_MODELOS_IA  14_INSTALADORES
├─ 12_ENTRETENIMENTO/ 01_Biblia  02_Livros_Literatura  03_Jogos  04_Quadrinhos  05_Musica
├─ 90_PESSOAL   (nunca enviado a IA online)
└─ 99_BACKUPS
```

Campos do catálogo: `id, nome, categoria, subcategoria, origem, autor, data, idioma, formato, tamanho, licenca, confiabilidade (A–D), sha256, armazenamento, status_local, caminho_drive, observacoes`.

## Regras de integridade

- Toda cópia é verificada por SHA-256 antes de atualizar o catálogo.
- Nenhuma rotina apaga a origem; remover é ação separada e explícita do usuário.
- Verificação periódica recalcula hashes e aponta arquivos ausentes ou alterados.

## Backup

`arca-backup-AAAAMMDD.zip`: banco (backup online do SQLite), configuração, documentos pessoais e manifesto com hashes. Conteúdo público rebaixável e chaves de API não entram.

## Estimativa de espaço (aproximada)

| Item | Mínimo | Recomendado | Completo |
| --- | --- | --- | --- |
| App, motor, runtimes | 0,5 GB | 0,5 GB | 0,5 GB |
| Banco e índices | 1 GB | 5 GB | 20 GB |
| Modelos de IA | 8 GB | 20 GB | 40 GB |
| Wikipédia PT + EN | 10 GB | 85 GB | 145 GB |
| Outros ZIMs | 5 GB | 30 GB | 100 GB |
| Mapas | 1 GB | 6 GB | 10 GB |
| Biblioteca própria e Sobrevivência | 5 GB | 50 GB | 200 GB |
| Backups | 2 GB | 20 GB | 50 GB |
| **Total** | **~33 GB** | **~217 GB** | **~566 GB** |

Artes e Entretenimento (livros, jogos, quadrinhos, música) não estão nessa conta e dependem do que for adicionado.

## Teste de isolamento de rede

Obrigatório na Fase 9, executado a partir da Fase 1:

- Suíte automatizada com `netguard` em modo "falhar em qualquer conexão externa".
- Teste real: Wi-Fi desligado + regra no Firewall do Windows bloqueando `ARCA.exe`, motor, Ollama e kiwix-serve.
- Roteiro manual (chat local, busca na Wikipédia, RAG com referências, mapa, importação, backup e restauração).
- Resultado registrado em `docs/testes/` com data e evidência.
