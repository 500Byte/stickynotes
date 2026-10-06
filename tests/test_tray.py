import pytest
from PyQt6.QtWidgets import QSystemTrayIcon

from stickynotes.model import NOTE_VISIBLE, NotesModel
from stickynotes.tray import TrayManager


def test_tray_initialization(qapp, tmp_path):
    model = NotesModel(path=tmp_path / "notes.json")
    tray = TrayManager(model, qapp)

    assert tray.tray_icon is not None
    assert tray.tray_icon.isVisible()
    assert not tray.tray_icon.icon().isNull()
    assert tray.tray_icon.contextMenu() is tray.menu

    assert tray.action_new_note is not None
    assert "Nueva nota" in tray.action_new_note.text()

    assert tray.action_toggle_all is not None
    assert "Ocultar todas" in tray.action_toggle_all.text()

    assert tray.notes_menu is not None
    assert "Notas" in tray.notes_menu.title()

    assert tray.action_quit is not None
    assert "Salir" in tray.action_quit.text()

    # Initial blank note in menu
    actions = tray.notes_menu.actions()
    assert len(actions) == 1
    assert actions[0].text() == "Nota vacía"
    assert actions[0].isChecked() is True


def test_tray_left_click_toggles_all(qapp, tmp_path):
    model = NotesModel(path=tmp_path / "notes.json")
    tray = TrayManager(model, qapp)

    assert model.data(model.index(0), NOTE_VISIBLE) is True

    # Left click / Trigger
    tray.tray_icon.activated.emit(QSystemTrayIcon.ActivationReason.Trigger)
    assert model.data(model.index(0), NOTE_VISIBLE) is False
    assert "Mostrar todas" in tray.action_toggle_all.text()
    assert tray.notes_menu.actions()[0].isChecked() is False

    # Second click restores
    tray.tray_icon.activated.emit(QSystemTrayIcon.ActivationReason.Trigger)
    assert model.data(model.index(0), NOTE_VISIBLE) is True
    assert "Ocultar todas" in tray.action_toggle_all.text()
    assert tray.notes_menu.actions()[0].isChecked() is True


def test_tray_double_click_toggles_all(qapp, tmp_path):
    model = NotesModel(path=tmp_path / "notes.json")
    tray = TrayManager(model, qapp)

    tray.tray_icon.activated.emit(QSystemTrayIcon.ActivationReason.DoubleClick)
    assert model.data(model.index(0), NOTE_VISIBLE) is False


def test_tray_action_new_note(qapp, tmp_path):
    model = NotesModel(path=tmp_path / "notes.json")
    tray = TrayManager(model, qapp)

    assert model.rowCount() == 1
    tray.action_new_note.trigger()

    assert model.rowCount() == 2
    actions = tray.notes_menu.actions()
    assert len(actions) == 2
    assert actions[0].text() == "Nota vacía"
    assert actions[1].text() == "Nota vacía"
    assert actions[0].isChecked() is True
    assert actions[1].isChecked() is True


def test_tray_action_toggle_all(qapp, tmp_path):
    model = NotesModel(path=tmp_path / "notes.json")
    tray = TrayManager(model, qapp)
    model.addNote()

    assert "Ocultar todas" in tray.action_toggle_all.text()

    tray.action_toggle_all.trigger()
    assert model.data(model.index(0), NOTE_VISIBLE) is False
    assert model.data(model.index(1), NOTE_VISIBLE) is False
    assert "Mostrar todas" in tray.action_toggle_all.text()
    assert all(not a.isChecked() for a in tray.notes_menu.actions())

    tray.action_toggle_all.trigger()
    assert model.data(model.index(0), NOTE_VISIBLE) is True
    assert model.data(model.index(1), NOTE_VISIBLE) is True
    assert "Ocultar todas" in tray.action_toggle_all.text()
    assert all(a.isChecked() for a in tray.notes_menu.actions())


def test_tray_notes_submenu_item_click_toggles_individual(qapp, tmp_path):
    model = NotesModel(path=tmp_path / "notes.json")
    model.addNote()
    tray = TrayManager(model, qapp)

    actions = tray.notes_menu.actions()
    assert len(actions) == 2

    # Toggle first note off
    actions[0].trigger()
    assert model.data(model.index(0), NOTE_VISIBLE) is False
    assert model.data(model.index(1), NOTE_VISIBLE) is True

    # Re-fetch actions since menu updates on dataChanged
    actions = tray.notes_menu.actions()
    assert actions[0].isChecked() is False
    assert actions[1].isChecked() is True
    assert "Ocultar todas" in tray.action_toggle_all.text()

    # Toggle second note off -> all hidden
    actions[1].trigger()
    assert model.data(model.index(1), NOTE_VISIBLE) is False
    assert "Mostrar todas" in tray.action_toggle_all.text()

    # Toggle first note back on
    actions = tray.notes_menu.actions()
    actions[0].trigger()
    assert model.data(model.index(0), NOTE_VISIBLE) is True
    actions = tray.notes_menu.actions()
    assert actions[0].isChecked() is True
    assert "Ocultar todas" in tray.action_toggle_all.text()


def test_tray_notes_preview_and_reactive_updates(qapp, tmp_path):
    model = NotesModel(path=tmp_path / "notes.json")
    tray = TrayManager(model, qapp)

    model.setText(0, "Buy milk and bread")
    actions = tray.notes_menu.actions()
    assert actions[0].text() == "Buy milk and bread"

    long_text = "This is a very long note that exceeds twenty characters"
    model.setText(0, long_text)
    actions = tray.notes_menu.actions()
    assert actions[0].text() == long_text[:20]
    assert len(actions[0].text()) == 20

    model.setText(0, "")
    actions = tray.notes_menu.actions()
    assert actions[0].text() == "Nota vacía"

    model.setText(0, "    ")
    actions = tray.notes_menu.actions()
    assert actions[0].text() == "Nota vacía"

    model.addNote()
    assert len(tray.notes_menu.actions()) == 2

    model.deleteNote(1)
    assert len(tray.notes_menu.actions()) == 1


def test_tray_action_quit_calls_flush_and_app_quit(qapp, tmp_path, monkeypatch):
    model = NotesModel(path=tmp_path / "notes.json")
    tray = TrayManager(model, qapp)

    flush_called = []
    quit_called = []
    monkeypatch.setattr(model, "flush", lambda: flush_called.append(True))
    monkeypatch.setattr(qapp, "quit", lambda: quit_called.append(True))

    tray.action_quit.trigger()
    assert flush_called == [True]
    assert quit_called == [True]
