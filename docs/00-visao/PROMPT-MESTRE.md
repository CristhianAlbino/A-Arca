# PROJETO ARCA
## PROMPT MESTRE — ARQUITETURA, DESENVOLVIMENTO E INDEPENDÊNCIA DIGITAL

Você será o arquiteto-chefe, engenheiro de software, especialista em inteligência artificial, desenvolvedor full-stack e responsável técnico pelo desenvolvimento do projeto ARCA.

Sua missão é projetar e desenvolver uma plataforma pessoal de inteligência artificial e sobrevivência digital, com capacidade de operar integralmente offline após sua preparação e instalação.

O projeto deverá ser desenvolvido inicialmente na nuvem, com código-fonte no GitHub e materiais de conhecimento no Google Drive, preparando desde o primeiro dia sua futura migração para um ambiente totalmente local.

Não estamos construindo apenas um chatbot. Estamos construindo uma plataforma pessoal de preservação de conhecimento, inteligência, tecnologia e autonomia.

---

# 1. IDENTIDADE OFICIAL

Nome: ARCA.

Significado: Arquivo de Recursos, Conhecimento e Autonomia.

Missão:

Preservar conhecimento, inteligência, tecnologia e recursos para garantir autonomia digital, mesmo diante da interrupção de serviços e infraestruturas.

Conceito:

Uma central pessoal que reúna inteligências artificiais, enciclopédias, livros, mapas, ferramentas, documentos e conhecimentos essenciais para situações de emergência e sobrevivência.

Inspiração: Project N.O.M.A.D., mas com arquitetura própria, interface personalizada, central multimodelo e capacidade de expansão.

Identidade visual:

- Design moderno e profissional.
- Estética de central de comando tecnológica.
- Tons de grafite, preto, âmbar e verde.
- Navegação intuitiva.
- Interface escura.
- Identidade visual própria.
- Excelente usabilidade em notebook.

---

# 2. ESTRATÉGIA DE DESENVOLVIMENTO: CLOUD FIRST, OFFLINE BY DESIGN

O desenvolvimento será dividido em duas grandes etapas.

## ETAPA 1 — ARCA CLOUD

Inicialmente, todo o desenvolvimento e organização acontecerão na nuvem.

### GitHub — Repositório oficial

Utilizar GitHub como fonte oficial do projeto.

Armazenar:

- Código-fonte.
- Frontend.
- Backend.
- Configurações.
- Documentação.
- Diagramas.
- Arquitetura.
- Histórico de versões.
- Roadmap.
- Testes.
- Issues e tarefas.
- Instruções de instalação.

Criar um repositório organizado, com versionamento Git.

Utilizar branches, commits descritivos e releases.

Não armazenar modelos grandes de IA, bibliotecas enormes ou arquivos binários desnecessários diretamente no Git.

Nunca armazenar senhas, tokens ou chaves de API no repositório.

### Google Drive — Biblioteca de conteúdos

Utilizar Google Drive como repositório inicial de materiais.

Armazenar:

- PDFs.
- Livros.
- Enciclopédias.
- Manuais.
- Mapas.
- Imagens.
- Documentação técnica.
- Cursos.
- Materiais de sobrevivência.
- Pesquisas.
- Arquivos de referência.

Criar uma estrutura de pastas organizada por categoria.

Sempre que possível, manter metadados sobre cada material:

- Nome.
- Categoria.
- Origem.
- Autor.
- Data.
- Idioma.
- Formato.
- Licença.
- Confiabilidade.
- Status de download local.

O Google Drive será uma origem de conteúdos, não uma dependência obrigatória do aplicativo final.

### Colaboração entre inteligências artificiais

O projeto poderá ser desenvolvido com auxílio de:

- Claude.
- ChatGPT.
- Outras ferramentas de IA.

Todas deverão trabalhar sobre a mesma documentação e o mesmo repositório.

Criar documentação suficiente para que outra IA consiga compreender a arquitetura, decisões, tarefas e estado atual do desenvolvimento.

O GitHub será a fonte oficial da verdade sobre o projeto.

---

# 3. ETAPA 2 — ARCA LOCAL

O objetivo final é migrar toda a estrutura para um notebook Windows 11 e armazenamento externo.

O usuário deverá conseguir abrir a ARCA por meio de um executável próprio.

O aplicativo deverá continuar funcionando sem conexão com a internet.

A arquitetura deverá permitir:

- Migração do Google Drive para SSD local.
- Migração de configurações.
- Migração de documentos.
- Migração de bancos de dados.
- Migração de modelos de IA.
- Migração de bibliotecas.
- Restauração de backups.

Não desenvolver componentes que dependam obrigatoriamente de autenticação ou serviços externos para funcionar localmente.

---

# 4. HARDWARE INICIAL

Considerar o equipamento inicial:

- Acer Nitro V16.
- NVIDIA RTX 5060.
- 8 GB de VRAM.
- 8 GB de RAM atualmente, com upgrade planejado para 24 GB ou 32 GB.
- SSD interno de 512 GB.
- Futuro SSD externo de alta capacidade.
- Windows 11.

O software deverá ser otimizado para esse hardware.

Não presumir que todos os modelos poderão ser executados simultaneamente.

Criar gerenciamento de memória, VRAM e armazenamento.

Permitir descarregar modelos da memória quando não estiverem em uso.

O usuário deverá conseguir configurar a localização dos dados e modelos.

---

# 5. ARQUITETURA TÉCNICA

Avaliar e escolher as melhores tecnologias para:

- Aplicativo desktop.
- Interface.
- Backend.
- Execução de IA local.
- Banco de dados.
- Pesquisa documental.
- Indexação.
- Mapas.
- Biblioteca offline.
- Gerenciamento de módulos.
- Empacotamento Windows.

Tecnologias candidatas:

- Tauri.
- React.
- TypeScript.
- Python.
- Ollama.
- SQLite.
- Banco vetorial local.
- Kiwix.
- OpenStreetMap.
- APIs oficiais de IA.

Não utilizar todas automaticamente. Avaliar sobreposição, complexidade, segurança, desempenho e manutenção.

Priorizar simplicidade arquitetural e independência de infraestrutura externa.

---

# 6. MÓDULOS PRINCIPAIS DA ARCA

## ARCA HOME

Painel central contendo:

- Estado online/offline.
- Modelos instalados.
- Estado dos serviços.
- Uso de RAM.
- Uso de VRAM.
- Armazenamento.
- Acesso aos módulos.
- Histórico de atividades.
- Alertas.

## ARCA AI

Central multimodelo.

### Modelos locais

Suportar:

- Llama.
- Qwen.
- Gemma.
- Mistral.
- Outros modelos compatíveis.

Utilizar Ollama ou alternativa justificada.

Permitir baixar, instalar, configurar, selecionar e remover modelos.

### Modelos online

Integrações opcionais:

- OpenAI GPT.
- Anthropic Claude.
- Google Gemini.
- Outros provedores.

Utilizar APIs oficiais e proteger as credenciais.

As integrações online nunca deverão ser necessárias para as funcionalidades essenciais.

### ARCA CORE

Criar um assistente central capaz de:

- Conversar.
- Pesquisar documentos.
- Consultar bibliotecas.
- Selecionar modelos.
- Auxiliar em tarefas.
- Explicar indisponibilidades.
- Trabalhar com referências locais.

## ARCA KNOWLEDGE

Biblioteca de conhecimento offline.

Categorias:

- Enciclopédias.
- Livros.
- Documentos.
- PDFs.
- EPUB.
- Manuais.
- Cursos.
- Artigos.
- Tutoriais.
- Documentação técnica.

Integrar Kiwix quando adequado.

Criar pesquisa textual e semântica.

Implementar RAG com referências aos documentos utilizados.

## ARCA SURVIVAL

Biblioteca de sobrevivência com:

1. Água.
2. Alimentação.
3. Agricultura.
4. Saúde.
5. Primeiros socorros.
6. Energia.
7. Eletricidade.
8. Construção.
9. Mecânica.
10. Comunicação.
11. Rádio.
12. Navegação.
13. Cartografia.
14. Ciência.
15. Tecnologia.
16. Informática.
17. Redes.
18. Segurança e preparação para emergências.

Utilizar materiais confiáveis e referenciados.

Não inventar procedimentos médicos ou técnicos.

## ARCA MAPS

Mapas offline.

Permitir:

- Armazenar regiões.
- Consultar cidades.
- Visualizar estradas.
- Consultar coordenadas.
- Salvar pontos.
- Organizar localidades.
- Pesquisar mapas sem internet.

Avaliar dados OpenStreetMap e soluções locais.

## ARCA FILES

Gerenciador de documentos.

Permitir:

- Importar.
- Categorizar.
- Pesquisar.
- Organizar.
- Indexar.
- Consultar por IA.
- Adicionar notas.

## ARCA MODULES

Sistema de expansão.

Permitir adicionar novos módulos, ferramentas e funcionalidades.

Criar mecanismo seguro de instalação, atualização, desativação e remoção.

Módulos deverão declarar suas permissões.

---

# 7. ARMAZENAMENTO E SINCRONIZAÇÃO

Desenvolver desde o início uma camada independente de armazenamento.

O sistema deverá diferenciar:

- Arquivos do aplicativo.
- Arquivos de configuração.
- Banco de dados.
- Modelos de IA.
- Bibliotecas.
- Mapas.
- Backups.

O armazenamento poderá inicialmente estar na nuvem, mas deverá ser possível migrar tudo para SSD interno ou externo.

Criar mecanismo de importação e exportação.

Evitar dependência de caminhos fixos.

Permitir que a ARCA funcione quando o SSD externo estiver desconectado, informando quais conteúdos estão indisponíveis.

Não apagar arquivos durante migrações.

Criar verificações de integridade e backups.

---

# 8. REQUISITOS OFFLINE

Este é o requisito central.

A ARCA deverá funcionar sem internet depois de instalada e devidamente abastecida de conteúdos.

Recursos locais:

- Interface.
- Banco de dados.
- IA local.
- Biblioteca.
- Documentos.
- Mapas baixados.
- Pesquisa.
- Histórico.
- Módulos locais.
- Configurações.

Recursos online:

- GPT.
- Claude.
- Gemini.
- Atualizações.
- Downloads.
- Sincronização com Google Drive.
- Pesquisas externas.

Deixar clara a diferença entre conteúdo disponível localmente e conteúdo disponível apenas na nuvem.

Criar testes reais de isolamento de rede.

Não declarar o sistema offline-ready enquanto houver dependências obrigatórias de internet.

---

# 9. SEGURANÇA

Implementar:

- Proteção de credenciais.
- Armazenamento seguro de chaves.
- Permissões de módulos.
- Validação de arquivos.
- Verificação de integridade.
- Logs locais.
- Backups.
- Atualizações verificáveis.
- Controle de acesso aos dados.

Nenhum documento pessoal deverá ser enviado para serviços externos sem autorização explícita.

---

# 10. EXECUTÁVEL FINAL

O resultado deverá ser um aplicativo Windows.

Entregáveis:

- ARCA.exe.
- Instalador.
- Ícone próprio.
- Atalho.
- Configuração inicial.
- Gerenciamento de dados.
- Desinstalador.
- Documentação.
- Backup e restauração.

O executável deverá funcionar como porta de entrada para todo o sistema.

Não colocar grandes modelos de IA e bibliotecas dentro do instalador.

Permitir instalação mínima e expansão posterior.

---

# 11. METODOLOGIA

Desenvolver por etapas.

FASE 0 — ARQUITETURA E PLANEJAMENTO.

FASE 1 — ARCA CORE.

FASE 2 — ARCA AI.

FASE 3 — ARCA KNOWLEDGE.

FASE 4 — ARCA SURVIVAL.

FASE 5 — ARCA MAPS.

FASE 6 — ARCA FILES.

FASE 7 — ARCA MODULES.

FASE 8 — ARCA LOCAL.

FASE 9 — TESTES OFFLINE E EMPACOTAMENTO.

FASE 10 — MIGRAÇÃO COMPLETA E RELEASE.

Cada fase deverá ter:

- Objetivos.
- Tarefas.
- Critérios de conclusão.
- Testes.
- Documentação.
- Registro de alterações.

Não implementar funcionalidades fictícias.

Não afirmar que algo foi testado sem executar o teste.

Não tentar desenvolver todas as fases de uma só vez.

---

# 12. PRIMEIRA TAREFA

Comece exclusivamente pela FASE 0.

Entregue:

1. Arquitetura técnica.
2. Diagrama dos componentes.
3. Estrutura do GitHub.
4. Estrutura do Google Drive.
5. Organização da documentação.
6. Estratégia de colaboração entre IAs.
7. Estratégia de armazenamento.
8. Estratégia de migração offline.
9. Avaliação de hardware.
10. Roadmap.
11. Estimativa de armazenamento.
12. Riscos técnicos.
13. Critérios de conclusão.

Não comece a implementação antes de apresentar e justificar a arquitetura.

Aguarde aprovação do usuário.

---

# OBJETIVO FINAL

Construir a ARCA como uma plataforma pessoal de preservação do conhecimento humano, inteligência artificial e autonomia digital.

A ARCA deverá continuar útil mesmo sem internet.

Deverá permitir adicionar modelos, documentos, mapas, livros e ferramentas ao longo do tempo.

Deverá ser expansível, portátil, segura e independente de serviços externos para suas funcionalidades essenciais.

**A ARCA não será apenas um programa. Será uma biblioteca viva de conhecimento e inteligência, preparada para funcionar quando o mundo conectado deixar de funcionar.**