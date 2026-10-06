from PyQt6.QtGui import QGuiApplication
from PyQt6.QtTest import QTest

from stickynotes.main import build_engine
from stickynotes.model import NotesModel


def test_qml_loads_and_one_window_per_note(qapp, tmp_path):
    m = NotesModel(path=tmp_path / "n.json", debounce_ms=10)
    m.addNote()
    warnings = []
    engine = build_engine(m, on_warnings=lambda ws: warnings.extend(w.toString() for w in ws))
    QTest.qWait(100)
    assert warnings == []
    assert engine.rootObjects()
    assert len(QGuiApplication.allWindows()) == 2
    m.addNote()
    QTest.qWait(50)
    assert len(QGuiApplication.allWindows()) == 3
    m.removeNote(0)
    QTest.qWait(50)
    assert len(QGuiApplication.allWindows()) == 2


def test_window_close_removes_from_model(qapp, tmp_path):
    m = NotesModel(path=tmp_path / "n.json", debounce_ms=10)
    m.addNote()
    warnings = []
    engine = build_engine(m, on_warnings=lambda ws: warnings.extend(w.toString() for w in ws))
    QTest.qWait(100)
    assert warnings == []
    assert len(QGuiApplication.allWindows()) == 2
    assert m.rowCount() == 2

    wins = [w for w in QGuiApplication.allWindows() if w.isVisible()]
    assert len(wins) == 2
    wins[0].close()
    QTest.qWait(100)
    assert m.rowCount() == 1
