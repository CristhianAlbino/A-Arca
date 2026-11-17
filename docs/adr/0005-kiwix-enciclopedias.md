# 0005 — Kiwix para enciclopédias, sem vetorizar a Wikipédia

- Status: Aceito
- Data: 2026-11-17

## Contexto
O usuário quer a Wikipédia em português e inglês offline, além de outros ZIMs (WikiMed, Wikibooks, Wikivoyage, Gutenberg).

## Opções consideradas
- **Kiwix**: formato ZIM padrão, já com índice de busca; `kiwix-serve` para navegar e `python-libzim` para ler artigos.
- Converter dumps da Wikipédia para banco próprio: enorme e sem ganho.
- Vetorizar a Wikipédia inteira: milhões de artigos, dias de GPU e dezenas de GB de vetores neste hardware.

## Decisão
Kiwix. A IA consulta a Wikipédia por busca textual (índice do ZIM) e lê os melhores artigos ("buscar e depois ler"). Vetorização fica para a biblioteca própria e o acervo de Sobrevivência.

## Consequências
- `kiwix-serve` roda como serviço local gerenciado pelo motor.
- Respostas citam o artigo da Wikipédia usado.
- Variantes `maxi`, `nopic` e `mini` escolhidas por espaço disponível.
