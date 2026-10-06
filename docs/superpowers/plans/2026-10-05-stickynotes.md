# StickyNotes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** App de sticky notes flotantes para Wayland con Qt6/QML (PyQt6), una ventana sin bordes por nota, persistencia JSON y instancia única.

**Architecture:** Un solo proceso. `NotesModel` (QAbstractListModel) es la fuente de verdad, se persiste con `store` (JSON atómico, debounce 500 ms). QML crea una `Window` por fila con un `Instantiator`. Un segundo lanzamiento envía `new` por `QLocalSocket` a la instancia viva.

**Tech Stack:** Python 3.14, PyQt6 6.11 (sistema), QML (QtQuick/Controls), pytest (venv con `--system-site-packages`).

## Global Constraints

- Spec: `docs/superpowers/specs/2026-10-05-stickynotes-design.md`.
- Sin layer-shell: `FramelessWindowHint` + xdg-toplevel; mover con `startSystemMove()`, redimensionar con `startSystemResize()`.
- Wayland app-id / desktop-file-name: `stickynotes`.
- Datos: `~/.local/share/stickynotes/notes.json` (`XDG_DATA_HOME` respetado), formato `{"version":1,"notes":[...]}`.
- Paleta (8): `#FFF59D #FFCC80 #F48FB1 #CE93D8 #90CAF9 #80DEEA #A5D6A7 #E0E0E0`.
- Roles QML: `noteId, noteText, noteColor, noteW, noteH` (NO `color`/`text`: chocan con propiedades de `Window`).
- Invariante: el modelo siempre tiene ≥1 nota.
- Tests con `QT_QPA_PLATFORM=offscreen`.

---

### Task 1: Scaffold + store

**Files:**
- Create: `pyproject.toml`, `.gitignore`, `stickynotes/__init__.py`, `stickynotes/store.py`, `tests/conftest.py`, `tests/test_store.py`

**Interfaces:**
- Produces: `store.DEFAULT_PATH: Path`, `store.load(path=DEFAULT_PATH) -> list[dict]`, `store.save(notes: list[dict], path=DEFAULT_PATH) -> None`

- [ ] **Step 1: Scaffold y venv**

```bash
cd ~/Documents/GitHub/stickynotes
python -m venv --system-site-packages .venv
.venv/bin/pip install -q pytest
mkdir -p stickynotes/qml tests data scripts
touch stickynotes/__init__.py
printf '.venv/\n__pycache__/\n*.pyc\n.pytest_cache/\n' > .gitignore
cat > pyproject.toml <<'EOF'
[project]
name = "stickynotes"
version = "0.1.0"
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
EOF
cat > tests/conftest.py <<'EOF'
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtGui import QGuiApplication


@pytest.fixture(scope="session")
def qapp():
    app = QGuiApplication.instance() or QGuiApplication([])
    yield app
EOF
```

- [ ] **Step 2: Write the failing tests** — `tests/test_store.py`

```python
import json

from stickynotes import store

NOTE = {"id": "a", "text": "hola", "color": "#FFF59D", "w": 280, "h": 280, "updated": "2026-01-01T00:00:00"}


def test_load_missing_returns_empty(tmp_path):
    assert store.load(tmp_path / "notes.json") == []


def test_roundtrip(tmp_path):
    p = tmp_path / "sub" / "notes.json"
    store.save([NOTE], p)
    assert store.load(p) == [NOTE]
    assert json.loads(p.read_text())["version"] == 1


def test_save_leaves_no_tmp_files(tmp_path):
    p = tmp_path / "notes.json"
    store.save([NOTE], p)
    assert [f.name for f in tmp_path.iterdir()] == ["notes.json"]


def test_corrupt_json_is_backed_up(tmp_path):
    p = tmp_path / "notes.json"
    p.write_text("{not json")
    assert store.load(p) == []
    assert (tmp_path / "notes.json.bak").read_text() == "{not json"
    assert not p.exists()
```

- [ ] **Step 3: Run to verify failure**

Run: `.venv/bin/pytest tests/test_store.py -v`
Expected: FAIL — `ImportError: cannot import name 'store'`

- [ ] **Step 4: Implement** — `stickynotes/store.py`

```python
"""Persistencia JSON atómica de las notas."""
import json
import os
import sys
import tempfile
from pathlib import Path

DEFAULT_PATH = (
    Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    / "stickynotes"
    / "notes.json"
)


def load(path=DEFAULT_PATH) -> list:
    path = Path(path)
    if not path.exists():
        return []
    try:
        notes = json.loads(path.read_text(encoding="utf-8"))["notes"]
        if not isinstance(notes, list):
            raise ValueError("'notes' is not a list")
        return notes
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"stickynotes: store ilegible, respaldando como .bak ({exc})", file=sys.stderr)
        try:
            path.replace(path.with_name(path.name + ".bak"))
        except OSError:
            pass
        return []


def save(notes: list, path=DEFAULT_PATH) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".notes-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"version": 1, "notes": notes}, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
```

- [ ] **Step 5: Run to verify pass**

Run: `.venv/bin/pytest tests/test_store.py -v`
Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat: scaffold project and atomic JSON store"
```

---

### Task 2: NotesModel

**Files:**
- Create: `stickynotes/model.py`, `tests/test_model.py`

**Interfaces:**
- Consumes: `store.load/save/DEFAULT_PATH`
- Produces: `model.PALETTE: list[str]`; role constants `NOTE_ID, NOTE_TEXT, NOTE_COLOR, NOTE_W, NOTE_H`; `NotesModel(path=None, debounce_ms=500, parent=None)` con slots `addNote()`, `removeNote(row:int)`, `setText(row:int, text:str)`, `setColor(row:int, color:str)`, `setSize(row:int, w:int, h:int)`, `flush()`.

- [ ] **Step 1: Write the failing tests** — `tests/test_model.py`

```python
from PyQt6.QtTest import QTest

from stickynotes import model as M
from stickynotes import store


def make(tmp_path, ms=10):
    return M.NotesModel(path=tmp_path / "n.json", debounce_ms=ms)


def test_starts_with_one_note(qapp, tmp_path):
    assert make(tmp_path).rowCount() == 1


def test_add_and_remove(qapp, tmp_path):
    m = make(tmp_path)
    m.addNote()
    assert m.rowCount() == 2
    m.removeNote(0)
    assert m.rowCount() == 1


def test_remove_last_keeps_one(qapp, tmp_path):
    m = make(tmp_path)
    m.removeNote(0)
    assert m.rowCount() == 1


def test_setters_update_roles(qapp, tmp_path):
    m = make(tmp_path)
    m.setText(0, "hi")
    m.setColor(0, "#F48FB1")
    m.setSize(0, 300, 200)
    i = m.index(0)
    assert m.data(i, M.NOTE_TEXT) == "hi"
    assert m.data(i, M.NOTE_COLOR) == "#F48FB1"
    assert (m.data(i, M.NOTE_W), m.data(i, M.NOTE_H)) == (300, 200)


def test_invalid_row_is_ignored(qapp, tmp_path):
    m = make(tmp_path)
    m.setText(5, "x")
    m.removeNote(-1)
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
    m.flush()
    assert make(tmp_path).data(m.index(0), M.NOTE_TEXT) == "persist"
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/pytest tests/test_model.py -v`
Expected: FAIL — `ImportError` (no `model`)

- [ ] **Step 3: Implement** — `stickynotes/model.py`

```python
"""Modelo de notas expuesto a QML."""
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

_KEYS = {NOTE_ID: "id", NOTE_TEXT: "text", NOTE_COLOR: "color", NOTE_W: "w", NOTE_H: "h"}


def _now():
    return datetime.now().isoformat(timespec="seconds")


class NotesModel(QAbstractListModel):
    def __init__(self, path=None, debounce_ms=500, parent=None):
        super().__init__(parent)
        self._path = path or store.DEFAULT_PATH
        self._notes = store.load(self._path)
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
            "updated": _now(),
        }

    def roleNames(self):
        return {
            NOTE_ID: b"noteId",
            NOTE_TEXT: b"noteText",
            NOTE_COLOR: b"noteColor",
            NOTE_W: b"noteW",
            NOTE_H: b"noteH",
        }

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._notes)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._notes):
            return None
        key = _KEYS.get(role)
        return self._notes[index.row()][key] if key else None

    def _valid(self, row):
        return 0 <= row < len(self._notes)

    def _touch(self, row, role):
        self._notes[row]["updated"] = _now()
        i = self.index(row)
        self.dataChanged.emit(i, i, [role])
        self._timer.start()

    @pyqtSlot()
    def addNote(self):
        n = len(self._notes)
        self.beginInsertRows(QModelIndex(), n, n)
        self._notes.append(self._blank())
        self.endInsertRows()
        self._timer.start()

    @pyqtSlot(int)
    def removeNote(self, row):
        if not self._valid(row):
            return
        self.beginRemoveRows(QModelIndex(), row, row)
        del self._notes[row]
        self.endRemoveRows()
        if not self._notes:
            self.addNote()
        self._timer.start()

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
            self._touch(row, NOTE_W)

    @pyqtSlot()
    def flush(self):
        self._timer.stop()
        try:
            store.save(self._notes, self._path)
        except OSError as exc:
            import sys

            print(f"stickynotes: no se pudo guardar ({exc})", file=sys.stderr)
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/pytest tests/test_model.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: NotesModel with debounced autosave"
```

---

### Task 3: Single-instance IPC

**Files:**
- Create: `stickynotes/ipc.py`, `tests/test_ipc.py`

**Interfaces:**
- Produces: `ipc.SERVER_NAME: str`; `ipc.send_new(name=SERVER_NAME, timeout=300) -> bool`; `ipc.SingleInstance(name=SERVER_NAME, parent=None)` con `listen() -> bool` y señal `newRequested`.

- [ ] **Step 1: Write the failing test** — `tests/test_ipc.py`

```python
import uuid

from PyQt6.QtTest import QTest

from stickynotes import ipc


def test_send_new_without_server_returns_false(qapp):
    assert ipc.send_new(f"sn-test-{uuid.uuid4()}", timeout=50) is False


def test_second_client_delivers_new(qapp):
    name = f"sn-test-{uuid.uuid4()}"
    inst = ipc.SingleInstance(name)
    got = []
    inst.newRequested.connect(lambda: got.append(1))
    assert inst.listen()
    assert ipc.send_new(name) is True
    QTest.qWait(150)
    assert got == [1]
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/pytest tests/test_ipc.py -v`
Expected: FAIL — `ImportError` (no `ipc`)

- [ ] **Step 3: Implement** — `stickynotes/ipc.py`

```python
"""Instancia única: el segundo lanzamiento pide una nota nueva a la primera."""
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

SERVER_NAME = "stickynotes-ipc"


def send_new(name=SERVER_NAME, timeout=300) -> bool:
    sock = QLocalSocket()
    sock.connectToServer(name)
    if not sock.waitForConnected(timeout):
        return False
    sock.write(b"new\n")
    sock.waitForBytesWritten(timeout)
    sock.disconnectFromServer()
    return True


class SingleInstance(QObject):
    newRequested = pyqtSignal()

    def __init__(self, name=SERVER_NAME, parent=None):
        super().__init__(parent)
        self._name = name
        self._server = QLocalServer(self)
        self._server.newConnection.connect(self._on_connection)

    def listen(self) -> bool:
        QLocalServer.removeServer(self._name)  # elimina socket huérfano
        return self._server.listen(self._name)

    def _on_connection(self):
        sock = self._server.nextPendingConnection()
        if sock is None:
            return

        def read():
            while sock.canReadLine():
                if bytes(sock.readLine()).strip() == b"new":
                    self.newRequested.emit()

        sock.readyRead.connect(read)
        sock.disconnected.connect(sock.deleteLater)
        read()
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/pytest tests/test_ipc.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: single-instance IPC over QLocalSocket"
```

---

### Task 4: QML UI + entrypoint + smoke test

**Files:**
- Create: `stickynotes/qml/main.qml`, `stickynotes/qml/Note.qml`, `stickynotes/main.py`, `stickynotes/__main__.py`, `tests/test_smoke.py`

**Interfaces:**
- Consumes: `NotesModel` (contexto QML `notesModel`), `PALETTE` (contexto QML `noteColors`), `SingleInstance`, `send_new`.
- Produces: `main.build_engine(model) -> QQmlApplicationEngine`, `main.main(argv=None) -> int`.

- [ ] **Step 1: Write the failing smoke test** — `tests/test_smoke.py`

```python
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
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/pytest tests/test_smoke.py -v`
Expected: FAIL — `ImportError` (no `main`)

- [ ] **Step 3: Implement QML** — `stickynotes/qml/main.qml`

```qml
import QtQml

QtObject {
    property Instantiator notes: Instantiator {
        model: notesModel
        delegate: Note {}
    }
}
```

`stickynotes/qml/Note.qml`

```qml
import QtQuick
import QtQuick.Controls
import QtQuick.Window

Window {
    id: win

    required property int index
    required property string noteId
    required property string noteText
    required property string noteColor
    required property int noteW
    required property int noteH

    property bool ready: false

    visible: true
    title: "StickyNote"
    color: "transparent"
    flags: Qt.Window | Qt.FramelessWindowHint
    minimumWidth: 160
    minimumHeight: 120
    width: 280
    height: 280

    Component.onCompleted: {
        width = noteW
        height = noteH
        ready = true
    }
    onWidthChanged: if (ready) sizeTimer.restart()
    onHeightChanged: if (ready) sizeTimer.restart()

    Timer {
        id: sizeTimer
        interval: 300
        onTriggered: notesModel.setSize(win.index, win.width, win.height)
    }

    readonly property color ink: "#1c1b1f"

    Rectangle {
        anchors.fill: parent
        color: win.noteColor

        Rectangle {
            id: bar
            width: parent.width
            height: 32
            color: Qt.darker(win.noteColor, 1.08)

            DragHandler {
                target: null
                onActiveChanged: if (active) win.startSystemMove()
            }

            Row {
                anchors.left: parent.left
                anchors.leftMargin: 8
                anchors.verticalCenter: parent.verticalCenter
                spacing: 6

                Text {
                    text: "＋"
                    font.pixelSize: 18
                    color: win.ink
                    MouseArea {
                        anchors.fill: parent
                        anchors.margins: -4
                        cursorShape: Qt.PointingHandCursor
                        onClicked: notesModel.addNote()
                    }
                }

                Repeater {
                    model: noteColors
                    Rectangle {
                        required property string modelData
                        width: 14
                        height: 14
                        radius: 7
                        color: modelData
                        border.width: 1
                        border.color: Qt.darker(modelData, 1.3)
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: notesModel.setColor(win.index, parent.modelData)
                        }
                    }
                }
            }

            Text {
                anchors.right: parent.right
                anchors.rightMargin: 10
                anchors.verticalCenter: parent.verticalCenter
                text: "✕"
                font.pixelSize: 14
                color: win.ink
                MouseArea {
                    anchors.fill: parent
                    anchors.margins: -6
                    cursorShape: Qt.PointingHandCursor
                    onClicked: notesModel.removeNote(win.index)
                }
            }
        }

        ScrollView {
            anchors.top: bar.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.margins: 8

            TextArea {
                text: win.noteText
                color: win.ink
                selectionColor: Qt.darker(win.noteColor, 1.4)
                selectedTextColor: "white"
                wrapMode: TextEdit.Wrap
                font.pixelSize: 15
                background: null
                placeholderText: "Escribe una nota…"
                placeholderTextColor: Qt.rgba(0, 0, 0, 0.4)
                onTextChanged: if (activeFocus) notesModel.setText(win.index, text)
            }
        }

        MouseArea {
            width: 20
            height: 20
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            cursorShape: Qt.SizeFDiagCursor
            onPressed: win.startSystemResize(Qt.RightEdge | Qt.BottomEdge)
        }
    }
}
```

- [ ] **Step 4: Implement entrypoint** — `stickynotes/main.py`

```python
"""Punto de entrada de StickyNotes."""
import sys
from pathlib import Path

from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtCore import QUrl

from . import ipc
from .model import PALETTE, NotesModel

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
    app = QGuiApplication(args)
    app.setApplicationName("stickynotes")
    app.setDesktopFileName("stickynotes")  # app-id en Wayland → class en Hyprland

    if ipc.send_new():
        return 0  # ya hay una instancia: se encargó de crear la nota nueva

    instance = ipc.SingleInstance()
    instance.listen()
    model = NotesModel()
    instance.newRequested.connect(model.addNote)
    engine = build_engine(model)
    if not engine.rootObjects():
        return 1
    app.aboutToQuit.connect(model.flush)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
```

`stickynotes/__main__.py`

```python
import sys

from .main import main

sys.exit(main())
```

- [ ] **Step 5: Run full suite**

Run: `.venv/bin/pytest -v`
Expected: 14 passed (4 store + 7 model + 2 ipc + 1 smoke), sin warnings QML.

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat: QML note windows, entrypoint and smoke test"
```

---

### Task 5: Desktop integration + manual verification

**Files:**
- Create: `data/stickynotes.desktop`, `data/stickynotes.svg`, `scripts/install.sh`

- [ ] **Step 1: Desktop file** — `data/stickynotes.desktop`

```ini
[Desktop Entry]
Type=Application
Name=Sticky Notes
Comment=Notas adhesivas flotantes
Exec=stickynotes
Icon=stickynotes
Terminal=false
Categories=Utility;
StartupWMClass=stickynotes
Actions=new;

[Desktop Action new]
Name=Nueva nota
Exec=stickynotes --new
```

- [ ] **Step 2: Icon** — `data/stickynotes.svg`

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect x="6" y="6" width="52" height="52" rx="6" fill="#FFF59D"/><rect x="6" y="6" width="52" height="12" rx="6" fill="#F9E26B"/><path d="M16 30h32M16 38h32M16 46h20" stroke="#1c1b1f" stroke-width="3" stroke-linecap="round" opacity=".6"/></svg>
```

- [ ] **Step 3: Installer** — `scripts/install.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p ~/.local/bin ~/.local/share/applications ~/.local/share/icons/hicolor/scalable/apps
cat > ~/.local/bin/stickynotes <<EOF
#!/bin/sh
PYTHONPATH="$ROOT" exec /usr/bin/python3 -m stickynotes "\$@"
EOF
chmod +x ~/.local/bin/stickynotes
cp "$ROOT/data/stickynotes.desktop" ~/.local/share/applications/
cp "$ROOT/data/stickynotes.svg" ~/.local/share/icons/hicolor/scalable/apps/
update-desktop-database ~/.local/share/applications 2>/dev/null || true
echo "Instalado. Ejecuta: stickynotes   (nueva nota: stickynotes --new)"
```

- [ ] **Step 4: Install and manual check en Hyprland**

Run: `bash scripts/install.sh && stickynotes &` then `sleep 1; hyprctl clients -j | python3 -c "import sys,json; [print(c['class'],c['floating']) for c in json.load(sys.stdin) if c['class']=='stickynotes']"`
Expected: `stickynotes True`. Luego `stickynotes --new` crea una segunda ventana en el mismo proceso (`pgrep -fc 'stickynotes'` sigue en 1 proceso). Verificar a mano: arrastrar la barra, redimensionar la esquina, cambiar color, `Super+ñ` (pin), cerrar y reabrir conserva texto/tamaño/color.

- [ ] **Step 5: Commit**

```bash
chmod +x scripts/install.sh && git add -A && git commit -m "feat: desktop file, icon and installer"
```

---

## Self-Review

- **Spec coverage:** store (T1), model+debounce+invariante ≥1 (T2), IPC + `--new` (T3/T4), QML mover/redimensionar/colores/borrar (T4), app-id `stickynotes` (T4), `.desktop`/icono (T5), regla Hyprland (ya aplicada en `settings.lua`), `.bak`/errores de escritura/socket huérfano (T1/T2/T3). Smoke offscreen (T4).
- **Placeholders:** ninguno.
- **Consistencia de tipos:** roles `noteId/noteText/noteColor/noteW/noteH` coinciden entre `model.py` y `Note.qml`; `build_engine(model, on_warnings)` coincide entre test y `main.py`; `setSize(int,int,int)` coincide con QML.
