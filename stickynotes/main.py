"""Punto de entrada de StickyNotes."""
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtCore import QUrl

from . import ipc
from .model import PALETTE, NotesModel
from .tray import TrayManager

QML_MAIN = Path(__file__).parent / "qml" / "main.qml"


def build_engine(model, on_warnings=None):
    engine = QQmlApplicationEngine()
    if on_warnings:
        engine.warnings.connect(on_warnings)
    ctx = engine.rootContext()
    ctx.setContextProperty("notesModel", model)
    ctx.setContextProperty("noteColors", PALETTE)
    engine.load(QUrl.fromLocalFile(str(QML_MAIN)))
    return engine


def main(argv=None) -> int:
    argv = list(sys.argv if argv is None else argv)
    args = [a for a in argv if a != "--new"]
    app = QApplication(args)
    app.setApplicationName("stickynotes")
    app.setDesktopFileName("stickynotes")  # app-id en Wayland → class en Hyprland
    app.setQuitOnLastWindowClosed(False)

    if ipc.send_new():
        return 0  # ya hay una instancia: se encargó de crear la nota nueva

    instance = ipc.SingleInstance()
    instance.listen()
    model = NotesModel()
    instance.newRequested.connect(model.addNote)
    tray = TrayManager(model, app)
    engine = build_engine(model)
    if not engine.rootObjects():
        return 1
    app.aboutToQuit.connect(model.flush)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
