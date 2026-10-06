"""Modelo de notas expuesto a QML."""
import sys
import uuid
from datetime import datetime

from PyQt6.QtCore import QAbstractListModel, QModelIndex, Qt, QTimer, pyqtSlot

from . import store

PALETTE = ["#FFF59D", "#FFCC80", "#F48FB1", "#CE93D8", "#90CAF9", "#80DEEA", "#A5D6A7", "#E0E0E0"]

NOTE_ID = Qt.ItemDataRole.UserRole + 1
NOTE_TEXT = NOTE_ID + 1
NOTE_COLOR = NOTE_ID + 2
NOTE_W = NOTE_ID + 3
NOTE_H = NOTE_ID + 4
NOTE_VISIBLE = NOTE_ID + 5
NOTE_MODE = NOTE_ID + 6

_KEYS = {
    NOTE_ID: "id",
    NOTE_TEXT: "text",
    NOTE_COLOR: "color",
    NOTE_W: "w",
    NOTE_H: "h",
    NOTE_VISIBLE: "visible",
    NOTE_MODE: "mode",
}


def _now():
    return datetime.now().isoformat(timespec="seconds")


class NotesModel(QAbstractListModel):
    def __init__(self, path=None, debounce_ms=500, parent=None):
        super().__init__(parent)
        self._path = path or store.DEFAULT_PATH
        self._notes = store.load(self._path)
        for note in self._notes:
            if "visible" not in note:
                note["visible"] = True
            if "mode" not in note:
                note["mode"] = "normal"
        if not self._notes:
            self._notes = [self._blank()]
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(debounce_ms)
        self._timer.timeout.connect(self.flush)

    def _blank(self):
        n = len(self._notes) if hasattr(self, "_notes") else 0
        return {
            "id": str(uuid.uuid4()),
            "text": "",
            "color": PALETTE[n % len(PALETTE)],
            "w": 280,
            "h": 280,
            "visible": True,
            "mode": "normal",
            "updated": _now(),
        }

    def roleNames(self):
        return {
            NOTE_ID: b"noteId",
            NOTE_TEXT: b"noteText",
            NOTE_COLOR: b"noteColor",
            NOTE_W: b"noteW",
            NOTE_H: b"noteH",
            NOTE_VISIBLE: b"noteVisible",
            NOTE_MODE: b"noteMode",
        }

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._notes)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._notes):
            return None
        key = _KEYS.get(role)
        if not key:
            return None
        val = self._notes[index.row()].get(key)
        if key == "visible" and val is None:
            return True
        if key == "mode" and val is None:
            return "normal"
        return val

    def _valid(self, row):
        return 0 <= row < len(self._notes)

    def _touch(self, row, *roles):
        self._notes[row]["updated"] = _now()
        i = self.index(row)
        self.dataChanged.emit(i, i, list(roles))
        self._timer.start()

    @pyqtSlot()
    def addNote(self):
        n = len(self._notes)
        self.beginInsertRows(QModelIndex(), n, n)
        self._notes.append(self._blank())
        self.endInsertRows()
        self._timer.start()

    @pyqtSlot(int, bool)
    def setVisible(self, row, visible):
        if self._valid(row):
            self._notes[row]["visible"] = bool(visible)
            self._touch(row, NOTE_VISIBLE)

    @pyqtSlot(int, str)
    def setMode(self, row, mode):
        if self._valid(row):
            self._notes[row]["mode"] = mode
            self._touch(row, NOTE_MODE)

    @pyqtSlot(int)
    def removeNote(self, row):
        self.setVisible(row, False)

    @pyqtSlot(int)
    def deleteNote(self, row):
        if not self._valid(row):
            return
        if len(self._notes) <= 1:
            note = self._notes[0]
            note["text"] = ""
            note["color"] = PALETTE[0]
            note["mode"] = "normal"
            note["visible"] = True
            note["updated"] = _now()
            idx = self.index(0)
            self.dataChanged.emit(idx, idx, [NOTE_TEXT, NOTE_COLOR, NOTE_MODE, NOTE_VISIBLE])
            self._timer.start()
            return
        self.beginRemoveRows(QModelIndex(), row, row)
        del self._notes[row]
        self.endRemoveRows()
        self._timer.start()

    @pyqtSlot()
    def toggleAllVisibility(self):
        target = not any(n.get("visible", True) for n in self._notes)
        for i in range(len(self._notes)):
            self.setVisible(i, target)

    @pyqtSlot(int, str)
    def setText(self, row, text):
        if self._valid(row):
            self._notes[row]["text"] = text
            self._touch(row, NOTE_TEXT)

    @pyqtSlot(int, str)
    def setColor(self, row, color):
        if self._valid(row):
            self._notes[row]["color"] = color
            self._touch(row, NOTE_COLOR)

    @pyqtSlot(int, int, int)
    def setSize(self, row, w, h):
        if self._valid(row):
            self._notes[row]["w"], self._notes[row]["h"] = w, h
            self._touch(row, NOTE_W, NOTE_H)

    @pyqtSlot()
    def flush(self):
        self._timer.stop()
        try:
            store.save(self._notes, self._path)
        except OSError as exc:
            print(f"stickynotes: no se pudo guardar ({exc})", file=sys.stderr)
