# 0006 — Mapas offline com PMTiles + MapLibre

- Status: Aceito
- Data: 2026-11-17

## Contexto
ARCA MAPS precisa mostrar estradas e cidades, buscar lugares, consultar coordenadas e salvar pontos sem internet.

## Opções consideradas
- **PMTiles** (um arquivo por região, servido localmente por range requests) + **MapLibre GL JS** na interface.
- Servidor de tiles completo (TileServer, OpenMapTiles): mais peças para manter.
- Nominatim para busca: pesado demais para o notebook.

## Decisão
PMTiles + MapLibre. Busca de lugares em tabela FTS5 extraída de dados OpenStreetMap (`.osm.pbf`). Estilo, glyphs (fontes) e sprites empacotados no app.

## Consequências
- Mapa da região do usuário fica no SSD interno; demais regiões no externo.
- Roteamento (rotas de carro/a pé) fica fora do escopo inicial.
- Dados OSM sob licença ODbL: atribuição exibida no mapa.
