# Design: interface e experiência

Protótipos (canvas de design): https://claude.ai/artifact/MGfS4S3RNwQxQDDAX6YXai — telas **Início** e **Conversa com a IA**.

A ARCA navega como um serviço de streaming e conversa como os assistentes de IA mais conhecidos. A inspiração é de layout e navegação: nome, logotipo e cores de outras marcas não são usados.

## Identidade

| Token | Valor | Uso |
| --- | --- | --- |
| `bg` | `#0A0A0B` | Fundo |
| `surface-1` | `#111113` | Laterais, faixas |
| `surface-2` | `#141417` | Cards, destaque |
| `surface-3` | `#1F1F23` | Chips, hover |
| `border` | `#2A2A30` | Bordas |
| `text` | `#F2F2F3` | Texto principal |
| `text-muted` | `#B4B4BB` | Texto secundário |
| `accent` | `#F5A524` (âmbar) | Ações principais, destaque, citações |
| `ok` | `#3DDC84` / texto `#7EE2A8` | Disponível, local, offline funcionando |
| Fonte de títulos | Space Grotesk 600/700 | Empacotada no app |
| Fonte de texto | Inter 400–700 | Empacotada no app |

## Tela inicial (inspirada na Netflix)

- Barra superior: logo ARCA, Início, IA, Conhecimento, Sobrevivência, Mapas, Arquivos, Módulos, busca global, selo ONLINE/OFFLINE.
- Destaque (hero) com item em evidência e botões "Abrir" e "Perguntar à IA".
- Faixa discreta de estado do sistema: RAM, VRAM, disco, modelo carregado.
- Fileiras horizontais: Continuar lendo, Sobrevivência, Enciclopédias e bibliotecas, Conversas recentes (e, quando houver conteúdo, Artes e Jogos).
- Cards 2:3 para livros e enciclopédias, 16:9 para áreas, mapas, cursos e módulos. Hover: o card cresce e mostra formato, tamanho, confiabilidade e local (disco/nuvem).
- Conteúdo indisponível aparece esmaecido com selo "NA NUVEM" ou "SSD DESCONECTADO".

## Conversa com a IA (padrão ChatGPT)

- Lateral esquerda: "Nova conversa", busca, histórico por data, estado offline e uso de VRAM/RAM.
- Coluna central (~768 px): mensagem do usuário em balão à direita; resposta da IA sem balão, com Markdown, listas e código com copiar.
- Seletor de modelo no topo com selo LOCAL ou ONLINE.
- Caixa de mensagem arredondada fixa embaixo: anexar, enviar, parar. Enter envia, Shift+Enter quebra linha.
- Ações por resposta: copiar, gerar novamente, ler em voz alta.
- **Diferencial ARCA:** citações numeradas na resposta e painel lateral direito com a fonte aberta, trecho usado destacado, confiabilidade e local do arquivo. Confirmação explícita antes de enviar documento a modelo online.

## Implementação

Tailwind CSS com os tokens acima, componentes Radix/shadcn, Framer Motion para transições curtas, react-markdown para respostas. Nada carregado de CDN.
