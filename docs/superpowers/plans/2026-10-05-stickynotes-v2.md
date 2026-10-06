# StickyNotes v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Incorporar soporte para bandeja del sistema (System Tray Icon), ocultar vs eliminar permanentemente, y botón selector de 3 modos de flotación (Top / Normal / Desktop).

**Architecture:**
- `QApplication` en lugar de `QGuiApplication` para soporte completo de `QSystemTrayIcon` y `QMenu`.
- `NotesModel` extiende soporte para roles `noteVisible` y `noteMode` ("normal", "top", "desktop"). Incorpora slots `setVisible(row, bool)`, `setMode(row, str)`, `toggleAllVisibility()`, y `deleteNote(row)`. `removeNote(row)` ahora actúa como ocultar (`setVisible(row, False)`), mientras que `deleteNote(row)` elimina permanentemente.
- `TrayManager`: controlador en Python con `QSystemTrayIcon`, maneja menú contextual con lista reactiva de notas, toggle general, nueva nota y salir.
- `Note.qml`: barra superior con botones `＋`, botón de ciclo de modo (📌 / 🪟 / 🖥️), menú desplegable (`…`) con paleta de colores y `🗑 Eliminar`, y botón `✕` (ocultar). Bandera de ventana `flags` reactiva al modo.

**Tech Stack:** Python 3.14, PyQt6 6.11 (QtWidgets + QtQuick/QML), pytest.

## Global Constraints
- Spec: `docs/superpowers/specs/2026-10-05-stickynotes-v2-tray-modes-design.md`.
- `QApplication` para habilitar widgets de bandeja en Linux.
- Retrocompatibilidad en `store.py` / `model.py`: si una nota guardada no tiene `visible` o `mode`, defaults: `visible = True`, `mode = "normal"`.
- Roles QML: `noteId, noteText, noteColor, noteW, noteH, noteVisible, noteMode`.
- Tests con `QT_QPA_PLATFORM=offscreen`.

---

### Task 1: Model & Store Updates (Visible, Mode, Delete vs Hide)

**Files:**
- Modify: `stickynotes/model.py`
- Modify: `tests/test_model.py`

**Interfaces:**
- Produces: Roles `NOTE_VISIBLE`, `NOTE_MODE`; slots: `setVisible(row: int, visible: bool)`, `setMode(row: int, mode: str)`, `deleteNote(row: int)`, `toggleAllVisibility()`. `removeNote(row: int)` oculta la nota (`setVisible(row, False)`).

- [ ] **Step 1: Write failing tests in `tests/test_model.py`**
- [ ] **Step 2: Run tests to verify failure**
- [ ] **Step 3: Update `NotesModel` in `stickynotes/model.py`**
- [ ] **Step 4: Run tests to verify pass**
- [ ] **Step 5: Commit**

---

### Task 2: System Tray Icon Manager

**Files:**
- Create: `stickynotes/tray.py`
- Modify: `stickynotes/main.py`
- Create: `tests/test_tray.py`

**Interfaces:**
- Produces: `TrayManager(model: NotesModel, app: QApplication, parent=None)` que gestiona `QSystemTrayIcon`, menu con Toggle All, New Note, submenú de notas sincronizado con el modelo, y Quit.

- [ ] **Step 1: Write failing tests in `tests/test_tray.py`**
- [ ] **Step 2: Run tests to verify failure**
- [ ] **Step 3: Implement `stickynotes/tray.py` y actualizar `main.py` para usar `QApplication`**
- [ ] **Step 4: Run tests to verify pass**
- [ ] **Step 5: Commit**

---

### Task 3: QML UI Update (Top/Normal/Desktop Mode Toggle & Menu)

**Files:**
- Modify: `stickynotes/qml/Note.qml`
- Modify: `tests/test_smoke.py`

**Interfaces:**
- Ventana reactiva a `noteVisible` y `noteMode` (ajustando `flags` con `WindowStaysOnTopHint` o `WindowStaysOnBottomHint`).
- Barra de herramientas con:
  - Botón de modo flotante con icono dinámico (📌, 🪟, 🖥️) que llama a `notesModel.setMode(...)`.
  - Botón `…` que abre popup para seleccionar colores o eliminar (`🗑`).
  - Botón `✕` que llama a `notesModel.removeNote(win.index)` (oculta a bandeja).

- [ ] **Step 1: Update smoke test to verify visibility and modes**
- [ ] **Step 2: Update `stickynotes/qml/Note.qml`**
- [ ] **Step 3: Run tests to verify pass**
- [ ] **Step 4: Commit**
