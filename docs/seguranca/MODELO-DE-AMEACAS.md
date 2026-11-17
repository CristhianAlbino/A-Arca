# Modelo de ameaças (versão inicial)

| Ameaça | Mitigação |
| --- | --- |
| Outro programa local chamando a API do motor | Escuta só em `127.0.0.1`, porta aleatória, token por sessão |
| Vazamento de documento pessoal para API online | Online desligado por padrão; confirmação por envio; `90_PESSOAL` bloqueada |
| Chave de API exposta | Cofre do Windows via `keyring`; nunca em arquivo, log ou Git |
| Conteúdo malicioso em página ZIM ou documento | Renderização em contexto isolado, CSP restritiva, sem execução de scripts de documentos |
| Módulo de terceiros malicioso | Manifesto com permissões, UI em iframe isolado, sem código nativo na primeira versão, hash/assinatura |
| Atualização adulterada | Updater do Tauri com assinatura; pacotes offline verificados por assinatura |
| Arquivo corrompido ou alterado | SHA-256 no catálogo e verificação periódica |
| Corrupção do banco ao desconectar disco | Banco sempre no SSD interno, modo WAL, backups |
