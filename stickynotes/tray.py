"""Manejador del icono de bandeja del sistema (System Tray Icon)."""
from pathlib import Path

from PyQt6.QtCore import QObject
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from .model import NOTE_TEXT, NOTE_VISIBLE, NotesModel


def _load_tray_icon() -> QIcon:
    icon = QIcon.fromTheme("stickynotes")
    if not icon.isNull():
        return icon

    pkg_dir = Path(__file__).resolve().parent
    candidates = [
        pkg_dir.parent / "data" / "stickynotes.svg",
        pkg_dir / "data" / "stickynotes.svg",
        Path("/usr/share/icons/hicolor/scalable/apps/stickynotes.svg"),
        Path("data/stickynotes.svg"),
    ]
    for c in candidates:
        if c.is_file():
            return QIcon(str(c))
    return QIcon()


class TrayManager(QObject):
    def __init__(self, model: NotesModel, app: QApplication, parent=None):
        super().__init__(parent or app)
        self._model = model
        self._app = app

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(_load_tray_icon())
        self.tray_icon.setToolTip("StickyNotes")
        self.tray_icon.activated.connect(self._on_tray_activated)

        self.menu = QMenu()
        self.action_new_note = self.menu.addAction("➕ Nueva nota")
        self.action_new_note.triggered.connect(self._model.addNote)

        self.action_toggle_all = self.menu.addAction("👁️ Mostrar todas")
        self.action_toggle_all.triggered.connect(self._model.toggleAllVisibility)

        self.menu.addSeparator()

        self.notes_menu = self.menu.addMenu("Notas")

        self.menu.addSeparator()

        self.action_quit = self.menu.addAction("❌ Salir")
        self.action_quit.triggered.connect(self._on_quit)

        self.tray_icon.setContextMenu(self.menu)

        self._model.dataChanged.connect(self._on_model_changed)
        self._model.rowsInserted.connect(self._on_model_changed)
        self._model.rowsRemoved.connect(self._on_model_changed)
        self._model.modelReset.connect(self._on_model_changed)

        self._on_model_changed()
        self.tray_icon.show()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self._model.toggleAllVisibility()

    def _on_quit(self):
        self._model.flush()
        self._app.quit()

    def _on_model_changed(self, *args):
        # Actualizar texto de mostrar/ocultar todas
        count = self._model.rowCount()
        any_visible = any(
            bool(self._model.data(self._model.index(i), NOTE_VISIBLE))
            for i in range(count)
        )

        if any_visible:
            self.action_toggle_all.setText("👁️ Ocultar todas")
        else:
            self.action_toggle_all.setText("👁️ Mostrar todas")

        # Sincronizar submenú de notas
        self.notes_menu.clear()
        for row in range(count):
            idx = self._model.index(row)
            text = self._model.data(idx, NOTE_TEXT) or ""
            is_visible = bool(self._model.data(idx, NOTE_VISIBLE))

            clean = text.strip()
            preview = clean[:20] if clean else "Nota vacía"

            action = self.notes_menu.addAction(preview)
            action.setCheckable(True)
            action.setChecked(is_visible)
            action.triggered.connect(
                lambda _checked=False, r=row, v=is_visible: self._model.setVisible(r, not v)
            )
