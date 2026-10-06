"""Manejador del icono de bandeja del sistema (System Tray Icon)."""
from pathlib import Path

from PyQt6.QtCore import QObject, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from .model import NOTE_COLOR, NOTE_TEXT, NOTE_VISIBLE, NotesModel

ICONS_DIR = Path(__file__).resolve().parent / "qml" / "icons"


def _render_lucide(svg_name: str, color_hex: str = "#1c1b1f", size: int = 16) -> QIcon:
    svg_path = ICONS_DIR / svg_name
    if not svg_path.is_file():
        return QIcon()
    renderer = QSvgRenderer(str(svg_path))
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    renderer.render(painter)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pix.rect(), QColor(color_hex))
    painter.end()
    return QIcon(pix)


def _render_circle(color_hex: str, size: int = 12) -> QIcon:
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(color_hex))
    painter.setPen(QColor(color_hex).darker(130))
    painter.drawEllipse(1, 1, size - 2, size - 2)
    painter.end()
    return QIcon(pix)


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
        self.action_new_note = self.menu.addAction(_render_lucide("plus.svg"), "Nueva nota")
        self.action_new_note.triggered.connect(self._model.addNote)

        self.action_toggle_all = self.menu.addAction(_render_lucide("eye.svg"), "Mostrar todas")
        self.action_toggle_all.triggered.connect(self._model.toggleAllVisibility)

        self.menu.addSeparator()

        self.notes_menu = self.menu.addMenu(_render_lucide("file-text.svg"), "Notas")

        self.menu.addSeparator()

        self.action_quit = self.menu.addAction(_render_lucide("log-out.svg"), "Salir")
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
        count = self._model.rowCount()
        any_visible = any(
            bool(self._model.data(self._model.index(i), NOTE_VISIBLE))
            for i in range(count)
        )

        if any_visible:
            self.action_toggle_all.setIcon(_render_lucide("eye-off.svg"))
            self.action_toggle_all.setText("Ocultar todas")
        else:
            self.action_toggle_all.setIcon(_render_lucide("eye.svg"))
            self.action_toggle_all.setText("Mostrar todas")

        self.notes_menu.clear()
        for row in range(count):
            idx = self._model.index(row)
            text = self._model.data(idx, NOTE_TEXT) or ""
            color = self._model.data(idx, NOTE_COLOR) or "#FFF59D"
            is_visible = bool(self._model.data(idx, NOTE_VISIBLE))

            clean = text.strip()
            preview = clean[:20] if clean else "Nota vacía"

            action = self.notes_menu.addAction(_render_circle(color), preview)
            action.setCheckable(True)
            action.setChecked(is_visible)
            action.triggered.connect(
                lambda _checked=False, r=row, v=is_visible: self._model.setVisible(r, not v)
            )
