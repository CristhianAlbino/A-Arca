"""Phase 3B regression: catalog and private files are not searchable knowledge."""

from arca_engine.knowledge.library import find_documents


def test_arca_volume_skips_private_staging_catalog_and_backups(tmp_path):
    expected = tmp_path / "05_SOBREVIVENCIA" / "01_Agua" / "01_Agua__GUIA_BASE.txt"
    expected.parent.mkdir(parents=True)
    expected.write_text("Água e meio ambiente.", encoding="utf-8")

    # Bibliographic metadata lists URLs; it must not be cited as original evidence.
    (expected.parent / "01_Agua__FONTES_E_PRIORIDADES.txt").write_text(
        "CDC https://www.cdc.gov/ — PDF ainda não baixado.", encoding="utf-8"
    )

    forbidden = {
        "90_PESSOAL": "dados-pessoais.pdf",
        "00_CATALOGO": "pesquisa.txt",
        "01_ENTRADA": "rascunho.md",
        "99_BACKUPS": "backup.html",
    }
    for folder, filename in forbidden.items():
        target = tmp_path / folder / filename
        target.parent.mkdir()
        target.write_text("Não deve entrar na busca.", encoding="utf-8")

    assert find_documents(tmp_path) == [expected]


def test_arca_skip_is_case_insensitive_and_preserves_other_documents(tmp_path):
    hidden = tmp_path / "90_pessoal" / "sigilo.epub"
    hidden.parent.mkdir()
    hidden.write_text("Confidencial.", encoding="utf-8")

    usable = tmp_path / "08_DOC_TECNICA" / "manual.PDF"
    usable.parent.mkdir()
    usable.write_text("Conteúdo público de teste.", encoding="utf-8")

    meta = tmp_path / "08_DOC_TECNICA" / "Rede__Fontes_e_Prioridades.TXT"
    meta.write_text("Metadados, não conteúdo técnico.", encoding="utf-8")

    assert find_documents(tmp_path) == [usable]
