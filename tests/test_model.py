from PyQt6.QtTest import QTest

from stickynotes import model as M
from stickynotes import store


def make(tmp_path, ms=10):
    return M.NotesModel(path=tmp_path / "n.json", debounce_ms=ms)


def test_starts_with_one_note(qapp, tmp_path):
    m = make(tmp_path)
    assert m.rowCount() == 1
    assert m.data(m.index(0), M.NOTE_VISIBLE) is True
    assert m.data(m.index(0), M.NOTE_MODE) == "normal"


def test_add_and_remove_hides_in_model(qapp, tmp_path):
    m = make(tmp_path)
    m.addNote()
    assert m.rowCount() == 2
    m.removeNote(0)
    assert m.rowCount() == 2
    assert m.data(m.index(0), M.NOTE_VISIBLE) is False
    assert m.data(m.index(1), M.NOTE_VISIBLE) is True


def test_add_and_delete(qapp, tmp_path):
    m = make(tmp_path)
    m.addNote()
    assert m.rowCount() == 2
    note1_id = m.data(m.index(1), M.NOTE_ID)
    m.deleteNote(0)
    assert m.rowCount() == 1
    assert m.data(m.index(0), M.NOTE_ID) == note1_id


def test_remove_last_keeps_one(qapp, tmp_path):
    m = make(tmp_path)
    m.removeNote(0)
    assert m.rowCount() == 1
    assert m.data(m.index(0), M.NOTE_VISIBLE) is False


def test_delete_last_keeps_one(qapp, tmp_path):
    m = make(tmp_path)
    m.deleteNote(0)
    assert m.rowCount() == 1


def test_delete_last_resets_in_place(qapp, tmp_path):
    m = make(tmp_path)
    m.setText(0, "note content")
    m.setColor(0, "#F48FB1")
    m.setMode(0, "top")
    m.setVisible(0, False)
    note_id = m.data(m.index(0), M.NOTE_ID)
    assert note_id is not None

    emitted = []
    m.dataChanged.connect(lambda top_left, bottom_right, roles: emitted.append((top_left.row(), roles)))

    m.deleteNote(0)

    assert m.rowCount() == 1
    assert m.data(m.index(0), M.NOTE_ID) == note_id
    assert m.data(m.index(0), M.NOTE_TEXT) == ""
    assert m.data(m.index(0), M.NOTE_COLOR) == M.PALETTE[0]
    assert m.data(m.index(0), M.NOTE_MODE) == "normal"
    assert m.data(m.index(0), M.NOTE_VISIBLE) is True
    _, roles = emitted[-1]
    assert M.NOTE_TEXT in roles and M.NOTE_COLOR in roles
    assert M.NOTE_MODE in roles and M.NOTE_VISIBLE in roles


def test_setters_update_roles(qapp, tmp_path):
    m = make(tmp_path)
    m.setText(0, "hi")
    m.setColor(0, "#F48FB1")
    m.setSize(0, 300, 200)
    m.setVisible(0, False)
    m.setMode(0, "top")
    i = m.index(0)
    assert m.data(i, M.NOTE_TEXT) == "hi"
    assert m.data(i, M.NOTE_COLOR) == "#F48FB1"
    assert (m.data(i, M.NOTE_W), m.data(i, M.NOTE_H)) == (300, 200)
    assert m.data(i, M.NOTE_VISIBLE) is False
    assert m.data(i, M.NOTE_MODE) == "top"


def test_invalid_row_is_ignored(qapp, tmp_path):
    m = make(tmp_path)
    m.setText(5, "x")
    m.setColor(-1, "#FFF")
    m.setSize(5, 100, 100)
    m.setVisible(5, False)
    m.setMode(-1, "top")
    m.removeNote(-1)
    m.deleteNote(-1)
    m.deleteNote(5)
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
    m.setMode(0, "desktop")
    m.setVisible(0, False)
    m.flush()

    reloaded = make(tmp_path)
    i = reloaded.index(0)
    assert reloaded.data(i, M.NOTE_TEXT) == "persist"
    assert reloaded.data(i, M.NOTE_MODE) == "desktop"
    assert reloaded.data(i, M.NOTE_VISIBLE) is False


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

    m.setVisible(0, False)
    assert emitted[-1] == (0, [M.NOTE_VISIBLE])

    m.setMode(0, "top")
    assert emitted[-1] == (0, [M.NOTE_MODE])


def test_toggle_all_visibility(qapp, tmp_path):
    m = make(tmp_path)
    m.addNote()
    assert m.data(m.index(0), M.NOTE_VISIBLE) is True
    assert m.data(m.index(1), M.NOTE_VISIBLE) is True

    # If any is visible -> all set to False
    m.toggleAllVisibility()
    assert m.data(m.index(0), M.NOTE_VISIBLE) is False
    assert m.data(m.index(1), M.NOTE_VISIBLE) is False

    # If all hidden -> all set to True
    m.toggleAllVisibility()
    assert m.data(m.index(0), M.NOTE_VISIBLE) is True
    assert m.data(m.index(1), M.NOTE_VISIBLE) is True

    # If mixed -> all set to False
    m.setVisible(0, False)
    assert m.data(m.index(0), M.NOTE_VISIBLE) is False
    assert m.data(m.index(1), M.NOTE_VISIBLE) is True
    m.toggleAllVisibility()
    assert m.data(m.index(0), M.NOTE_VISIBLE) is False
    assert m.data(m.index(1), M.NOTE_VISIBLE) is False


def test_backwards_compatibility_defaults(qapp, tmp_path):
    p = tmp_path / "legacy.json"
    p.write_text(
        '{"version": 1, "notes": [{"id": "old1", "text": "legacy", "color": "#FFF59D", "w": 280, "h": 280, "updated": "2026-01-01T00:00:00"}]}'
    )
    m = M.NotesModel(path=p, debounce_ms=10)
    assert m.rowCount() == 1
    assert m.data(m.index(0), M.NOTE_ID) == "old1"
    assert m.data(m.index(0), M.NOTE_TEXT) == "legacy"
    assert m.data(m.index(0), M.NOTE_VISIBLE) is True
    assert m.data(m.index(0), M.NOTE_MODE) == "normal"


def test_role_names(qapp):
    m = M.NotesModel(debounce_ms=10)
    roles = m.roleNames()
    assert roles[M.NOTE_VISIBLE] == b"noteVisible"
    assert roles[M.NOTE_MODE] == b"noteMode"

