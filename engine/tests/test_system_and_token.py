from arca_engine.security.token import bearer_from_header, new_token, tokens_match
from arca_engine.system import info


def test_snapshot_has_real_numbers(app_paths):
    snap = info.snapshot(app_paths.data_dir)
    assert snap["memory"]["total_bytes"] > 0
    assert 0 <= snap["memory"]["percent"] <= 100
    assert snap["data_disk"]["free_bytes"] > 0
    gpu = snap["gpu"]
    # Either real devices or an explicit reason, never invented numbers.
    assert gpu["available"] is bool(gpu["devices"])
    if not gpu["available"]:
        assert gpu["reason"]


def test_parse_nvidia_smi_output():
    out = "NVIDIA GeForce RTX 5060 Laptop GPU, 8151, 5120\n"
    [gpu] = info.parse_nvidia_smi(out)
    assert gpu["name"].startswith("NVIDIA GeForce RTX 5060")
    assert gpu["total_bytes"] == 8151 * 1024 * 1024
    assert gpu["used_bytes"] == 5120 * 1024 * 1024


def test_tokens():
    t = new_token()
    assert len(t) >= 40
    assert tokens_match(t, t)
    assert not tokens_match(t, t[:-1] + ("A" if t[-1] != "A" else "B"))
    assert not tokens_match(t, None)
    assert bearer_from_header(f"Bearer {t}") == t
    assert bearer_from_header("Basic abc") is None
    assert bearer_from_header(None) is None
