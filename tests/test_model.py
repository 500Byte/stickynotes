from PyQt6.QtTest import QTest

from stickynotes import model as M
from stickynotes import store


def make(tmp_path, ms=10):
    return M.NotesModel(path=tmp_path / "n.json", debounce_ms=ms)


def test_starts_with_one_note(qapp, tmp_path):
    assert make(tmp_path).rowCount() == 1


def test_add_and_remove(qapp, tmp_path):
    m = make(tmp_path)
    m.addNote()
    assert m.rowCount() == 2
    m.removeNote(0)
    assert m.rowCount() == 1


def test_remove_last_keeps_one(qapp, tmp_path):
    m = make(tmp_path)
    m.removeNote(0)
    assert m.rowCount() == 1


def test_setters_update_roles(qapp, tmp_path):
    m = make(tmp_path)
    m.setText(0, "hi")
    m.setColor(0, "#F48FB1")
    m.setSize(0, 300, 200)
    i = m.index(0)
    assert m.data(i, M.NOTE_TEXT) == "hi"
    assert m.data(i, M.NOTE_COLOR) == "#F48FB1"
    assert (m.data(i, M.NOTE_W), m.data(i, M.NOTE_H)) == (300, 200)


def test_invalid_row_is_ignored(qapp, tmp_path):
    m = make(tmp_path)
    m.setText(5, "x")
    m.removeNote(-1)
    assert m.rowCount() == 1


def test_debounce_saves_once_and_persists(qapp, tmp_path, monkeypatch):
    calls = []
    real = store.save
    monkeypatch.setattr(store, "save", lambda n, p: (calls.append(1), real(n, p))[1])
    m = make(tmp_path)
    for t in ("a", "ab", "abc"):
        m.setText(0, t)
    QTest.qWait(100)
    assert len(calls) == 1
    assert store.load(tmp_path / "n.json")[0]["text"] == "abc"


def test_reload_restores_notes(qapp, tmp_path):
    m = make(tmp_path)
    m.setText(0, "persist")
    m.flush()
    assert make(tmp_path).data(m.index(0), M.NOTE_TEXT) == "persist"


def test_data_changed_emits_expected_roles(qapp, tmp_path):
    m = make(tmp_path)
    emitted = []
    m.dataChanged.connect(lambda top_left, bottom_right, roles: emitted.append((top_left.row(), roles)))

    m.setText(0, "text update")
    assert emitted[-1] == (0, [M.NOTE_TEXT])

    m.setColor(0, "#80DEEA")
    assert emitted[-1] == (0, [M.NOTE_COLOR])

    m.setSize(0, 400, 350)
    _, roles = emitted[-1]
    assert M.NOTE_W in roles and M.NOTE_H in roles

