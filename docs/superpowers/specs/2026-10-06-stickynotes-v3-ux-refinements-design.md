# StickyNotes v3 — UX/UI Refinement & Power-User Architecture Spec

Refinamiento integral de UX/UI para transformar StickyNotes en una herramienta fluida, elegante y orientada al teclado y al minimalismo en Wayland.

## Objetivos de Diseño

1. **Minimalismo Visual ("Paper First"):**
   - **Hover Reveal en Barra:** La barra de herramientas se atenúa a `opacity: 0.15` (o se mimetiza con el fondo de la nota) cuando el cursor no está sobre la ventana o sobre la barra. Al posar el mouse sobre los primeros 36px superiores, transiciona suavemente a `opacity: 1.0` en 150ms.
   - **Resize Grip Visual:** Indicador sutil de 3 puntos/marcas diagonales en la esquina inferior derecha con `opacity: 0.35` (hover `0.8`), eliminando la incertidumbre de dónde arrastrar para redimensionar en Wayland.
   - **Diferenciación Visual de Capas:**
     - `top` (Sobre todo): Borde superior o sutil resplandor con acento.
     - `desktop` (Fondo): Opacidad de ventana ajustada al 92% para fusionarse suavemente con el wallpaper.
     - `normal`: Opacidad al 100%, borde suave estándar.

2. **Atajos de Teclado Locales (Power-User):**
   - Dentro de la nota:
     - `Ctrl+N`: Nueva nota (`notesModel.addNote()`).
     - `Ctrl+W`: Cerrar nota actual (ocultar a bandeja).
     - `Ctrl+Shift+D`: Eliminar nota permanentemente.
     - `Ctrl+T`: Ciclar modo de ventana (`normal` ➔ `top` ➔ `desktop`).
     - `Escape`: Desenfocar el campo de texto (`activeFocus = false`).

3. **Checklists Rápidas en el Editor:**
   - Detección y atajo de lista de tareas: escribir `[] ` o `- [ ]` al inicio de una línea o presionar `Ctrl+Shift+C` inserta/alterna una casilla `[ ] ` / `[x] `.

4. **Buscador en el Tray Menu:**
   - La bandeja incluye una acción inicial "🔍 Buscar nota..." que permite filtrar notas guardadas rápidamente o un campo de búsqueda en la parte superior del submenú.

---

## Componentes y Arquitectura

- `stickynotes/qml/Note.qml`:
  - `Shortcut` items para `Ctrl+N`, `Ctrl+W`, `Ctrl+Shift+D`, `Ctrl+T`, `Escape`.
  - Animaciones de opacidad en la barra superior condicionadas a `containsMouse`.
  - Icono visual de resize grip en la esquina inferior derecha con `LucideIcon` o marcas diagonales.
  - Sutil tratamiento de opacidad según `noteMode === "desktop"`.
- `stickynotes/tray.py`:
  - Entrada de búsqueda o diálogo rápido para filtrar notas si la lista crece.
