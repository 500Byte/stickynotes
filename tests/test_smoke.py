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
