import json
import shutil

import pytest

from arca_engine.storage.volumes import (
    MARKER_NAME,
    InvalidVolumeUri,
    VolumeRegistry,
    VolumeUnavailable,
    create_marker,
    make_uri,
    parse_uri,
    read_marker,
)


@pytest.fixture
def ssd(tmp_path):
    root = tmp_path / "E"
    (root / "biblioteca").mkdir(parents=True)
    (root / "biblioteca" / "livro.pdf").write_bytes(b"%PDF-1.4 teste")
    return root


def registry(db, *paths):
    return VolumeRegistry(db, search_paths=lambda: list(paths), include_drive_roots=False)


def test_marker_is_created_once_and_never_overwritten(ssd):
    first = create_marker(ssd, "ARCA-EXT")
    second = create_marker(ssd, "OUTRO-NOME")
    assert first == second
    data = json.loads((ssd / MARKER_NAME).read_text(encoding="utf-8"))
    assert data["label"] == "ARCA-EXT"


def test_corrupted_marker_reads_as_none(ssd):
    (ssd / MARKER_NAME).write_text("{nao é json", encoding="utf-8")
    assert read_marker(ssd) is None


def test_register_and_resolve(db, ssd):
    reg = registry(db)
    marker = reg.register(ssd, "ARCA-EXT")
    uri = make_uri(marker.volume_id, "biblioteca/livro.pdf")
    assert reg.resolve(uri).read_bytes() == b"%PDF-1.4 teste"
    assert reg.to_uri(ssd / "biblioteca" / "livro.pdf") == uri


def test_uri_cannot_escape_the_volume(db, ssd):
    marker = registry(db).register(ssd, "ARCA-EXT")
    with pytest.raises(InvalidVolumeUri):
        parse_uri(f"vol://{marker.volume_id}/../segredo.txt")
    with pytest.raises(InvalidVolumeUri):
        parse_uri("vol://nao-e-uuid/arquivo")
    with pytest.raises(InvalidVolumeUri):
        make_uri(marker.volume_id, "/absoluto")


def test_unplugged_volume_is_unavailable_not_an_error(db, ssd, tmp_path):
    reg = registry(db, ssd)
    marker = reg.register(ssd, "ARCA-EXT")
    shutil.move(str(ssd), str(tmp_path / "gaveta"))  # "unplug"
    reg.scan()
    status = {v["id"]: v for v in reg.status()}
    assert status[marker.volume_id]["available"] is False
    with pytest.raises(VolumeUnavailable) as err:
        reg.resolve(make_uri(marker.volume_id, "biblioteca/livro.pdf"))
    assert "ARCA-EXT" in str(err.value)


def test_volume_is_found_again_under_a_new_letter(db, ssd, tmp_path):
    reg = registry(db)
    marker = reg.register(ssd, "ARCA-EXT")
    new_place = tmp_path / "F"
    shutil.move(str(ssd), str(new_place))  # the SSD came back as F:
    reg2 = registry(db, new_place)
    mounted = reg2.scan()
    assert mounted[marker.volume_id] == new_place
    uri = make_uri(marker.volume_id, "biblioteca/livro.pdf")
    assert reg2.resolve(uri) == (new_place / "biblioteca" / "livro.pdf").resolve()
    row = db.execute("SELECT last_root FROM volumes WHERE id = ?", (marker.volume_id,)).fetchone()
    assert row["last_root"] == str(new_place)


def test_status_reports_free_space(db, ssd):
    reg = registry(db)
    reg.register(ssd, "ARCA-EXT")
    [entry] = reg.status()
    assert entry["available"] is True
    assert entry["free_bytes"] > 0
