# 2026-11-18 — ChatGPT — relevância de fontes na Fase 3C

- **Fase:** 3C — busca e respostas com fontes (RAG inicial, sem embeddings)
- **Branch / PR:** `fix/rag-filtrar-fontes-fracas-chatgpt`, derivada de `feat/fase-3-biblioteca` · [PR #2 (draft)](https://github.com/CristhianAlbino/A-Arca/pull/2)
- **Papel:** revisão de qualidade de busca, pequena implementação isolada e testes de regressão

## Feito

- Análise do CI: 33/33 execuções com falha; a última tem três jobs terminados sem steps. Causa raiz **não identificada**; possível problema de provisionamento/bloqueio externo. Issue [#1](https://github.com/CristhianAlbino/A-Arca/issues/1).
- Em `knowledge/retrieve.py`: `relevant_excerpt` descarta fontes com apenas uma palavra de perguntas com vários termos; exige ao menos um termo no trecho e dois termos distintos no título + trecho. Perguntas com uma única palavra exigem um termo.
- Busca até quatro candidatos documentais para preencher até duas fontes aceitas; fontes remanescentes são numeradas sem lacunas.
- Adicionado `engine/tests/test_rag_relevance.py` com casos de documento irrelevante, evidência no título + trecho, consulta de um termo e renumeração após descarte.

## Pendente

- Revisar o [PR #2 (draft)](https://github.com/CristhianAlbino/A-Arca/pull/2) contra `feat/fase-3-biblioteca` e validar antes do merge.
- Medir precisão e recuperação com acervo real (especialmente Salmo 23, tratamento de queimadura e Prim).
- Investigar causa exata do CI no painel do GitHub. Não alterar workflow às cegas.
- Implementar busca semântica e melhores escores na etapa seguinte; este filtro não resolve respostas inventadas.

## Não testado (e por quê)

- **Não rodei a suíte `pytest` nem `ruff` do repositório**: este ambiente não possui checkout local do GitHub e a execução no GitHub Actions está bloqueada antes dos steps.
- Foi executada somente uma verificação isolada da lógica de correspondência (sem importar o código versionado): casos de fonte com um termo, dois termos e título sem evidência. Isso **não** equivale a passar os testes adicionados.

## Decisões

- Alteração conservadora e pequena na 3C: sem mudar esquema de banco, APIs, modelos ou interface.
- Branch própria, sem modificar `main`, sem merge automático.
- Em saúde/sobrevivência, correspondência textual **não** comprova confiabilidade. A regra de fontes A/B da Fase 4 continua pendente.
