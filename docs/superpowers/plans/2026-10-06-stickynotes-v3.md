# StickyNotes v3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar el paquete completo de mejoras UX/UI: barra minimalista con hover reveal, feedback visual de modo (top/desktop/normal), grip visual de redimensión, atajos de teclado locales (`Ctrl+N`, `Ctrl+W`, `Ctrl+T`, `Ctrl+Shift+D`, `Escape`), y checklist rápida con `Ctrl+Shift+C`.

**Architecture:**
- `Note.qml`:
  - Declaración de `Shortcut` para comandos de teclado.
  - Hover Handler / MouseArea para revelar la barra superior (`opacity: 0.2` cuando idle, `1.0` en hover, con animación fluida).
  - Componente de grip de redimensión con puntos o líneas diagonales visibles.
  - Ajuste de opacidad general y borde sutil según `noteMode`.
- `tests/test_smoke.py`:
  - Validar atajos y comportamientos en QML.

## Global Constraints
- Spec: `docs/superpowers/specs/2026-10-06-stickynotes-v3-ux-refinements-design.md`.
- Mantener compatibilidad con Wayland / Hyprland.
- Iconos vectoriales Lucide sin emojis.
- Tests ejecutables headless con `QT_QPA_PLATFORM=offscreen`.

---

### Task 1: Shortcuts & Power-User Keyboard Navigation in QML

**Files:**
- Modify: `stickynotes/qml/Note.qml`
- Modify: `tests/test_smoke.py`

**Interfaces:**
- `Shortcut { sequence: "Ctrl+N"; onActivated: notesModel.addNote() }`
- `Shortcut { sequence: "Ctrl+W"; onActivated: notesModel.removeNote(win.index) }`
- `Shortcut { sequence: "Ctrl+Shift+D"; onActivated: notesModel.deleteNote(win.index) }`
- `Shortcut { sequence: "Ctrl+T"; onActivated: cycleMode() }`
- `Shortcut { sequence: "Escape"; onActivated: textArea.focus = false }`
- `Shortcut { sequence: "Ctrl+Shift+C"; onActivated: toggleChecklist() }`

- [ ] **Step 1: Write failing smoke tests in `tests/test_smoke.py`**
- [ ] **Step 2: Add shortcuts and checklist logic to `Note.qml`**
- [ ] **Step 3: Run pytest to verify pass**
- [ ] **Step 4: Commit**

---

### Task 2: Visual Polish (Hover Reveal Bar, Resize Grip & Layer Mode Feedback)

**Files:**
- Modify: `stickynotes/qml/Note.qml`
- Modify: `tests/test_smoke.py`

**Interfaces:**
- Barra superior con opacidad reactiva al hover (`Behavior on opacity { NumberAnimation { duration: 150 } }`).
- Grip visual en esquina inferior derecha (`opacity: 0.35` idle, `0.8` hover).
- Modo `desktop` aplica `opacity: 0.92`, modo `top` aplica un borde de acento en la parte superior.

- [ ] **Step 1: Implement visual polish in `Note.qml`**
- [ ] **Step 2: Verify smoke tests and run pytest**
- [ ] **Step 3: Commit and install**
