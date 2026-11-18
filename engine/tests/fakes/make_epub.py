"""Writes a small valid EPUB 3 for tests (chapters stored out of reading order on purpose)."""

from __future__ import annotations

import zipfile
from pathlib import Path

CONTAINER = """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>"""


def make_epub(path: Path, title: str, chapters: list[tuple[str, str]]) -> Path:
    """chapters: (heading, paragraph) in reading order."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    items = "\n".join(
        f'<item id="c{i}" href="texto/cap%20{i}.xhtml" media-type="application/xhtml+xml"/>'
        for i in range(len(chapters))
    )
    spine = "\n".join(f'<itemref idref="c{i}"/>' for i in range(len(chapters)))
    opf = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="id">arca-teste</dc:identifier><dc:title>{title}</dc:title><dc:language>pt-BR</dc:language>
  </metadata>
  <manifest>
    <item id="css" href="estilo.css" media-type="text/css"/>
    {items}
  </manifest>
  <spine>{spine}</spine>
</package>"""
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", CONTAINER)
        zf.writestr("OEBPS/content.opf", opf)
        zf.writestr("OEBPS/estilo.css", "p { color: red }")
        for i in reversed(range(len(chapters))):  # stored backwards: order must come from the spine
            heading, para = chapters[i]
            zf.writestr(
                f"OEBPS/texto/cap {i}.xhtml",
                f'<?xml version="1.0" encoding="utf-8"?><html xmlns="http://www.w3.org/1999/xhtml">'
                f"<head><title>{heading}</title><style>p{{}}</style></head>"
                f"<body><h1>{heading}</h1><p>{para}</p></body></html>",
            )
    return path
