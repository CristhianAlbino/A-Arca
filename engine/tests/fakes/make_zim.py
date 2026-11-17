"""Builds a tiny real ZIM file for tests and UI previews (no download needed).

    python engine/tests/fakes/make_zim.py <output.zim>
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

from libzim.writer import Creator, Hint, Item, StringProvider

# 1x1 transparent PNG
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)

ARTICLES = {
    "Agua_potavel": (
        "Água potável",
        "<p>A <b>água potável</b> é própria para o consumo humano. Ferver a água por um minuto "
        'elimina a maioria dos microrganismos. Veja também <a href="Filtro_de_agua">filtro de água</a> '
        'e <a href="https://pt.wikipedia.org/wiki/Agua">a versão online</a>.</p>'
        '<img src="I/gota.png" alt="Gota de água">'
        '<script>alert("não deveria rodar")</script>'
        '<p onclick="roubar()" style="color:red">Parágrafo com atributos perigosos.</p>',
    ),
    "Filtro_de_agua": (
        "Filtro de água",
        "<p>Um <b>filtro de água</b> remove partículas e parte dos microrganismos. "
        'Depois de filtrar, ainda é recomendável <a href="Agua_potavel#ferver">ferver</a>.</p>',
    ),
    "Radio_amador": (
        "Rádio amador",
        "<p>O <b>radioamadorismo</b> permite comunicação de longa distância sem internet.</p>",
    ),
}


class _Page(Item):
    def __init__(self, path: str, title: str, body: str):
        super().__init__()
        self._path, self._title = path, title
        self._html = f"<html><head><title>{title}</title></head><body><h1>{title}</h1>{body}</body></html>"

    def get_path(self) -> str:
        return self._path

    def get_title(self) -> str:
        return self._title

    def get_mimetype(self) -> str:
        return "text/html"

    def get_contentprovider(self):
        return StringProvider(self._html)

    def get_hints(self):
        return {Hint.FRONT_ARTICLE: True}


class _Image(Item):
    def get_path(self) -> str:
        return "I/gota.png"

    def get_title(self) -> str:
        return ""

    def get_mimetype(self) -> str:
        return "image/png"

    def get_contentprovider(self):
        return StringProvider(PNG)

    def get_hints(self):
        return {Hint.FRONT_ARTICLE: False}


def make_zim(path: Path, title: str = "Enciclopédia de teste", fulltext: bool = True) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    creator = Creator(str(path))
    creator.config_indexing(fulltext, "por")
    with creator as c:
        c.set_mainpath("Agua_potavel")
        for p, (t, body) in ARTICLES.items():
            c.add_item(_Page(p, t, body))
        c.add_item(_Image())
        c.add_redirection("Agua", "Água", "Agua_potavel", {Hint.FRONT_ARTICLE: False})
        for key, value in {
            "Title": title,
            "Description": "ZIM pequeno gerado para os testes da ARCA",
            "Language": "por",
            "Creator": "ARCA",
            "Publisher": "ARCA",
            "Name": "arca_teste",
        }.items():
            c.add_metadata(key, value)
    return path


if __name__ == "__main__":
    print(make_zim(Path(sys.argv[1] if len(sys.argv) > 1 else "teste.zim")))
