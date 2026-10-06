import pytest
from PyQt6.QtCore import QEvent, QObject, QPointF, Qt
from PyQt6.QtGui import QGuiApplication, QMouseEvent
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


def test_shortcuts_declared_with_expected_sequences(qapp, tmp_path, run_engine):
    m = NotesModel(path=tmp_path / "n.json", debounce_ms=10)
    warnings = []
    run_engine(m, on_warnings=lambda ws: warnings.extend(w.toString() for w in ws))
    QTest.qWait(100)
    assert warnings == []

    win0 = _find_window_by_index(0)
    assert win0 is not None

    expected_shortcuts = {
        "shortcutNew": ("Ctrl+N",),
        "shortcutClose": ("Ctrl+W",),
        "shortcutDelete": ("Ctrl+Shift+D",),
        "shortcutCycleMode": ("Ctrl+T",),
        "shortcutEscape": ("Escape",),
        "shortcutChecklist": ("Ctrl+Shift+C",),
    }

    for obj_name, expected_seqs in expected_shortcuts.items():
        sc = win0.findChild(QObject, obj_name)
        assert sc is not None, f"Shortcut {obj_name} not found"
        seq = sc.property("sequence")
        assert seq in expected_seqs, f"Shortcut {obj_name} sequence {seq} not in {expected_seqs}"


def test_shortcut_new_adds_note(qapp, tmp_path, run_engine):
    m = NotesModel(path=tmp_path / "n.json", debounce_ms=10)
    run_engine(m)
    QTest.qWait(100)
    assert m.rowCount() == 1

    win0 = _find_window_by_index(0)
    sc = win0.findChild(QObject, "shortcutNew")
    assert sc is not None
    sc.activated.emit()
    QTest.qWait(50)

    assert m.rowCount() == 2
    assert len(QGuiApplication.allWindows()) == 2


def test_shortcut_close_hides_note(qapp, tmp_path, run_engine):
    m = NotesModel(path=tmp_path / "n.json", debounce_ms=10)
    m.addNote()
    run_engine(m)
    QTest.qWait(100)

    win0 = _find_window_by_index(0)
    sc = win0.findChild(QObject, "shortcutClose")
    assert sc is not None
    sc.activated.emit()
    QTest.qWait(50)

    assert win0.isVisible() is False
    assert win0.property("noteVisible") is False
    assert m.data(m.index(0), NOTE_VISIBLE) is False


def test_shortcut_delete_removes_note(qapp, tmp_path, run_engine):
    m = NotesModel(path=tmp_path / "n.json", debounce_ms=10)
    m.addNote()
    run_engine(m)
    QTest.qWait(100)
    assert m.rowCount() == 2

    win0 = _find_window_by_index(0)
    sc = win0.findChild(QObject, "shortcutDelete")
    assert sc is not None
    sc.activated.emit()
    QTest.qWait(50)

    assert m.rowCount() == 1
    assert len(QGuiApplication.allWindows()) == 1


def test_shortcut_cycle_mode(qapp, tmp_path, run_engine):
    m = NotesModel(path=tmp_path / "n.json", debounce_ms=10)
    run_engine(m)
    QTest.qWait(100)

    win0 = _find_window_by_index(0)
    sc = win0.findChild(QObject, "shortcutCycleMode")
    assert sc is not None

    assert win0.property("noteMode") == "normal"

    sc.activated.emit()
    QTest.qWait(50)
    assert win0.property("noteMode") == "top"

    sc.activated.emit()
    QTest.qWait(50)
    assert win0.property("noteMode") == "desktop"

    sc.activated.emit()
    QTest.qWait(50)
    assert win0.property("noteMode") == "normal"


def test_shortcut_escape_clears_focus(qapp, tmp_path, run_engine):
    m = NotesModel(path=tmp_path / "n.json", debounce_ms=10)
    run_engine(m)
    QTest.qWait(100)

    win0 = _find_window_by_index(0)
    win0.show()
    win0.requestActivate()
    QTest.qWait(50)

    ta = win0.findChild(QObject, "noteTextArea")
    assert ta is not None
    ta.forceActiveFocus(Qt.FocusReason.MouseFocusReason)
    QTest.qWait(50)
    assert ta.property("activeFocus") is True

    sc = win0.findChild(QObject, "shortcutEscape")
    assert sc is not None
    sc.activated.emit()
    QTest.qWait(50)

    assert ta.property("activeFocus") is False


def test_shortcut_checklist_toggles_and_inserts(qapp, tmp_path, run_engine):
    m = NotesModel(path=tmp_path / "n.json", debounce_ms=10)
    run_engine(m)
    QTest.qWait(100)

    win0 = _find_window_by_index(0)
    ta = win0.findChild(QObject, "noteTextArea")
    assert ta is not None

    sc = win0.findChild(QObject, "shortcutChecklist")
    assert sc is not None

    # Case 1: Empty note -> inserts "[ ] "
    sc.activated.emit()
    QTest.qWait(50)
    assert ta.property("text") == "[ ] "
    assert m.data(m.index(0), NOTE_TEXT) == "[ ] "

    # Case 2: [ ] -> toggles to [x]
    sc.activated.emit()
    QTest.qWait(50)
    assert ta.property("text") == "[x] "
    assert m.data(m.index(0), NOTE_TEXT) == "[x] "

    # Case 3: [x] -> toggles back to [ ]
    sc.activated.emit()
    QTest.qWait(50)
    assert ta.property("text") == "[ ] "
    assert m.data(m.index(0), NOTE_TEXT) == "[ ] "

    # Case 4: Line with content "Buy groceries" -> "[ ] Buy groceries"
    ta.setProperty("text", "Buy groceries")
    ta.setProperty("cursorPosition", 4)
    sc.activated.emit()
    QTest.qWait(50)
    assert ta.property("text") == "[ ] Buy groceries"
    assert m.data(m.index(0), NOTE_TEXT) == "[ ] Buy groceries"

    # Toggle to "[x] Buy groceries"
    sc.activated.emit()
    QTest.qWait(50)
    assert ta.property("text") == "[x] Buy groceries"
    assert m.data(m.index(0), NOTE_TEXT) == "[x] Buy groceries"

    # Case 5: Multi-line text, toggle on second line
    ta.setProperty("text", "Header\nItem 2")
    # Position cursor on "Item 2" (index 8)
    ta.setProperty("cursorPosition", 8)
    sc.activated.emit()
    QTest.qWait(50)
    assert ta.property("text") == "Header\n[ ] Item 2"
    assert m.data(m.index(0), NOTE_TEXT) == "Header\n[ ] Item 2"


def test_shortcuts_trigger_via_key_clicks(qapp, tmp_path, run_engine):
    m = NotesModel(path=tmp_path / "n.json", debounce_ms=10)
    run_engine(m)
    QTest.qWait(100)

    win0 = _find_window_by_index(0)
    assert win0 is not None
    win0.show()
    win0.requestActivate()
    QTest.qWait(50)

    # Test Ctrl+T via keyClick
    assert win0.property("noteMode") == "normal"
    QTest.keyClick(win0, Qt.Key.Key_T, Qt.KeyboardModifier.ControlModifier)
    QTest.qWait(50)
    assert win0.property("noteMode") == "top"

    # Test Ctrl+N via keyClick
    assert m.rowCount() == 1
    QTest.keyClick(win0, Qt.Key.Key_N, Qt.KeyboardModifier.ControlModifier)
    QTest.qWait(50)
    assert m.rowCount() == 2


def test_hover_reveal_toolbar(qapp, tmp_path, run_engine):
    m = NotesModel(path=tmp_path / "n.json", debounce_ms=10)
    run_engine(m)
    QTest.qWait(100)

    win0 = _find_window_by_index(0)
    assert win0 is not None
    win0.show()
    QTest.qWait(50)

    bar = win0.findChild(QObject, "headerBar")
    assert bar is not None
    assert bar.property("opacity") == pytest.approx(0.25, abs=0.02)

    # Hover inside window reveals toolbar
    pos_inside = QPointF(win0.width() / 2, win0.height() / 2)
    ev_in = QMouseEvent(
        QEvent.Type.MouseMove, pos_inside, pos_inside,
        Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier
    )
    qapp.sendEvent(win0, ev_in)
    QTest.qWait(200)
    assert bar.property("opacity") == pytest.approx(1.0, abs=0.02)

    # Move mouse outside hides toolbar
    pos_out = QPointF(-100, -100)
    ev_out = QMouseEvent(
        QEvent.Type.MouseMove, pos_out, pos_out,
        Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier
    )
    qapp.sendEvent(win0, ev_out)
    QTest.qWait(200)
    assert bar.property("opacity") == pytest.approx(0.25, abs=0.02)

    # Opening menu popup forces toolbar visible even without hover
    menu_popup = win0.findChild(QObject, "menuPopup")
    assert menu_popup is not None
    menu_popup.open()
    QTest.qWait(200)
    assert bar.property("opacity") == pytest.approx(1.0, abs=0.02)
    menu_popup.close()
    QTest.qWait(200)
    assert bar.property("opacity") == pytest.approx(0.25, abs=0.02)


def test_visual_resize_grip(qapp, tmp_path, run_engine):
    m = NotesModel(path=tmp_path / "n.json", debounce_ms=10)
    run_engine(m)
    QTest.qWait(100)

    win0 = _find_window_by_index(0)
    assert win0 is not None
    win0.show()
    QTest.qWait(50)

    grip = win0.findChild(QObject, "resizeGrip")
    assert grip is not None
    assert grip.property("opacity") == pytest.approx(0.35, abs=0.02)

    rma = win0.findChild(QObject, "resizeMouseArea")
    assert rma is not None
    assert rma.property("cursorShape") == Qt.CursorShape.SizeFDiagCursor

    # Hover over bottom-right resize grip
    pos_grip = QPointF(win0.width() - 5, win0.height() - 5)
    ev_grip = QMouseEvent(
        QEvent.Type.MouseMove, pos_grip, pos_grip,
        Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier
    )
    qapp.sendEvent(win0, ev_grip)
    QTest.qWait(200)
    assert grip.property("opacity") == pytest.approx(0.85, abs=0.02)

    # Move away from grip
    pos_inside = QPointF(win0.width() / 2, win0.height() / 2)
    ev_in = QMouseEvent(
        QEvent.Type.MouseMove, pos_inside, pos_inside,
        Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier
    )
    qapp.sendEvent(win0, ev_in)
    QTest.qWait(200)
    assert grip.property("opacity") == pytest.approx(0.35, abs=0.02)

    # Pressing on resize area
    ev_press = QMouseEvent(
        QEvent.Type.MouseButtonPress, pos_grip, pos_grip,
        Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier
    )
    qapp.sendEvent(win0, ev_press)
    QTest.qWait(50)
    ev_release = QMouseEvent(
        QEvent.Type.MouseButtonRelease, pos_grip, pos_grip,
        Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier
    )
    qapp.sendEvent(win0, ev_release)
    QTest.qWait(50)


def test_layer_mode_visual_feedback(qapp, tmp_path, run_engine):
    m = NotesModel(path=tmp_path / "n.json", debounce_ms=10)
    run_engine(m)
    QTest.qWait(100)

    win0 = _find_window_by_index(0)
    assert win0 is not None

    accent = win0.findChild(QObject, "topAccentLine")
    assert accent is not None

    # Normal mode (default)
    assert win0.property("noteMode") == "normal"
    assert win0.property("opacity") == pytest.approx(1.0, abs=0.01)
    assert accent.property("visible") is False

    # Top mode: accent line visible, opacity standard
    m.setMode(0, "top")
    QTest.qWait(50)
    assert win0.property("noteMode") == "top"
    assert win0.property("opacity") == pytest.approx(1.0, abs=0.01)
    assert accent.property("visible") is True
    assert accent.property("height") == 2

    # Desktop mode: accent line hidden, window opacity 0.92
    m.setMode(0, "desktop")
    QTest.qWait(50)
    assert win0.property("noteMode") == "desktop"
    assert win0.property("opacity") == pytest.approx(0.92, abs=0.01)
    assert accent.property("visible") is False

    # Return to normal mode
    m.setMode(0, "normal")
    QTest.qWait(50)
    assert win0.property("noteMode") == "normal"
    assert win0.property("opacity") == pytest.approx(1.0, abs=0.01)
    assert accent.property("visible") is False



