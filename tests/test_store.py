import json

from stickynotes import store

NOTE = {"id": "a", "text": "hola", "color": "#FFF59D", "w": 280, "h": 280, "updated": "2026-01-01T00:00:00"}


def test_load_missing_returns_empty(tmp_path):
    assert store.load(tmp_path / "notes.json") == []


def test_roundtrip(tmp_path):
    p = tmp_path / "sub" / "notes.json"
    store.save([NOTE], p)
    assert store.load(p) == [NOTE]
    assert json.loads(p.read_text())["version"] == 1


def test_save_leaves_no_tmp_files(tmp_path):
    p = tmp_path / "notes.json"
    store.save([NOTE], p)
    assert [f.name for f in tmp_path.iterdir()] == ["notes.json"]


def test_corrupt_json_is_backed_up(tmp_path):
    p = tmp_path / "notes.json"
    p.write_text("{not json")
    assert store.load(p) == []
    assert (tmp_path / "notes.json.bak").read_text() == "{not json"
    assert not p.exists()
