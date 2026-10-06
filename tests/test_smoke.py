import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtTest import QTest

from stickynotes.main import build_engine
from stickynotes.model import NOTE_TEXT, NOTE_VISIBLE, NotesModel


@pytest.fixture
def run_engine():
    engines = []

    def _build(model, on_warnings=None):
        engine = build_engine(model, on_warnings=on_warnings)
        engines.append(engine)
        return engine

    yield _build

    for engine in engines:
        for obj in engine.rootObjects():
            obj.deleteLater()
        engine.deleteLater()
    QTest.qWait(50)


def _find_window_by_index(index):
    for win in QGuiApplication.allWindows():
        if win.property("index") == index:
            return win
    return None


def test_root_instantiator_loads_and_exposes_mode_and_visibility(qapp, tmp_path, run_engine):
    m = NotesModel(path=tmp_path / "n.json", debounce_ms=10)
    m.addNote()
    warnings = []
    engine = run_engine(m, on_warnings=lambda ws: warnings.extend(w.toString() for w in ws))
    QTest.qWait(100)
    assert warnings == []
    assert engine.rootObjects()

    wins = QGuiApplication.allWindows()
    assert len(wins) == 2
    for win in wins:
        assert win.property("noteVisible") is True
        assert win.property("noteMode") == "normal"
        assert win.isVisible() is True

    m.addNote()
    QTest.qWait(50)
    assert len(QGuiApplication.allWindows()) == 3

    # Hiding note 0 via removeNote sets noteVisible to False and hides that specific window
    m.removeNote(0)
    QTest.qWait(50)

    win0 = _find_window_by_index(0)
    assert win0 is not None
    assert win0.isVisible() is False
    assert win0.property("noteVisible") is False

    visible_wins = [w for w in QGuiApplication.allWindows() if w.isVisible()]
    assert len(visible_wins) == 2


def test_window_visibility_reacts_to_model_set_visible(qapp, tmp_path, run_engine):
    m = NotesModel(path=tmp_path / "n.json", debounce_ms=10)
    warnings = []
    run_engine(m, on_warnings=lambda ws: warnings.extend(w.toString() for w in ws))
    QTest.qWait(100)
    assert warnings == []

    win0 = _find_window_by_index(0)
    assert win0 is not None
    assert win0.isVisible() is True

    m.setVisible(0, False)
    QTest.qWait(50)
    assert win0.isVisible() is False
    assert win0.property("noteVisible") is False

    m.setVisible(0, True)
    QTest.qWait(50)
    assert win0.isVisible() is True
    assert win0.property("noteVisible") is True


def test_window_flags_update_with_mode(qapp, tmp_path, run_engine):
    m = NotesModel(path=tmp_path / "n.json", debounce_ms=10)
    warnings = []
    run_engine(m, on_warnings=lambda ws: warnings.extend(w.toString() for w in ws))
    QTest.qWait(100)
    assert warnings == []

    win0 = _find_window_by_index(0)
    assert win0 is not None
    assert win0.property("noteMode") == "normal"
    assert not (win0.flags() & Qt.WindowType.WindowStaysOnTopHint)
    assert not (win0.flags() & Qt.WindowType.WindowStaysOnBottomHint)

    m.setMode(0, "top")
    QTest.qWait(50)
    assert win0.property("noteMode") == "top"
    assert bool(win0.flags() & Qt.WindowType.WindowStaysOnTopHint) is True
    assert not (win0.flags() & Qt.WindowType.WindowStaysOnBottomHint)

    m.setMode(0, "desktop")
    QTest.qWait(50)
    assert win0.property("noteMode") == "desktop"
    assert bool(win0.flags() & Qt.WindowType.WindowStaysOnBottomHint) is True
    assert not (win0.flags() & Qt.WindowType.WindowStaysOnTopHint)

    m.setMode(0, "normal")
    QTest.qWait(50)
    assert win0.property("noteMode") == "normal"
    assert not (win0.flags() & Qt.WindowType.WindowStaysOnTopHint)
    assert not (win0.flags() & Qt.WindowType.WindowStaysOnBottomHint)


def test_cycle_mode_and_set_color(qapp, tmp_path, run_engine):
    m = NotesModel(path=tmp_path / "n.json", debounce_ms=10)
    warnings = []
    run_engine(m, on_warnings=lambda ws: warnings.extend(w.toString() for w in ws))
    QTest.qWait(100)
    assert warnings == []

    win0 = _find_window_by_index(0)
    assert win0 is not None

    m.setColor(0, "#80DEEA")
    QTest.qWait(50)
    assert win0.property("noteColor") == "#80DEEA"

    # Test mode cycle sequence: normal -> top -> desktop -> normal
    for expected in ["top", "desktop", "normal"]:
        current = win0.property("noteMode")
        next_mode = "top" if current == "normal" else ("desktop" if current == "top" else "normal")
        m.setMode(0, next_mode)
        QTest.qWait(50)
        assert win0.property("noteMode") == expected


def test_window_close_sets_visible_false_in_model(qapp, tmp_path, run_engine):
    m = NotesModel(path=tmp_path / "n.json", debounce_ms=10)
    m.addNote()
    warnings = []
    run_engine(m, on_warnings=lambda ws: warnings.extend(w.toString() for w in ws))
    QTest.qWait(100)
    assert warnings == []
    assert len(QGuiApplication.allWindows()) == 2
    assert m.rowCount() == 2

    win0 = _find_window_by_index(0)
    assert win0 is not None
    assert win0.isVisible() is True
    assert m.data(m.index(0), NOTE_VISIBLE) is True

    win0.close()
    QTest.qWait(100)

    # In v2, closing hides the note (sets visible=False in model) without deleting the row
    assert m.rowCount() == 2
    assert m.data(m.index(0), NOTE_VISIBLE) is False
    assert win0.isVisible() is False
    assert win0.property("noteVisible") is False


def test_delete_note_removes_from_model_or_resets_if_last(qapp, tmp_path, run_engine):
    m = NotesModel(path=tmp_path / "n.json", debounce_ms=10)
    m.addNote()
    warnings = []
    run_engine(m, on_warnings=lambda ws: warnings.extend(w.toString() for w in ws))
    QTest.qWait(100)
    assert warnings == []

    assert len(QGuiApplication.allWindows()) == 2
    assert m.rowCount() == 2

    m.deleteNote(0)
    QTest.qWait(50)
    assert m.rowCount() == 1
    assert len(QGuiApplication.allWindows()) == 1

    # Reset in place when deleting the last note
    m.setText(0, "Hola mundo")
    assert m.data(m.index(0), NOTE_TEXT) == "Hola mundo"
    m.deleteNote(0)
    QTest.qWait(50)
    assert m.rowCount() == 1
    assert len(QGuiApplication.allWindows()) == 1
    assert m.data(m.index(0), NOTE_TEXT) == ""
    assert m.data(m.index(0), NOTE_VISIBLE) is True
