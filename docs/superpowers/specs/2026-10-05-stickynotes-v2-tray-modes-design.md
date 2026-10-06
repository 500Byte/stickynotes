# StickyNotes v2 — UX/UI, Tray Icon & Window Modes Design

Actualización de StickyNotes para soportar cierre/ocultamiento no destructivo, Tray Icon con lista de notas, y modos de flotación (Top, Normal, Desktop).

## Decisiones de Diseño

1. **Ciclo de vida (Cerrar vs Eliminar):**
   - **Cerrar (`✕` o atajo de compositor):** Solo oculta la ventana (`visible = false`). La nota permanece persistida en `notes.json`. Se puede volver a abrir en cualquier momento desde el menú del tray icon.
   - **Eliminar (`🗑`):** Acción explícita desde el menú desplegable (`…`) de la nota. Remueve la nota permanentemente del JSON. Si es la última nota viva en el sistema, se resetea en blanco.

2. **System Tray Icon (Bandeja del sistema):**
   - Uso de `QSystemTrayIcon` con el icono SVG de StickyNotes.
   - **Clic izquierdo:** Toggle de visibilidad de todas las notas (si alguna está visible, las oculta todas; si todas están ocultas, las restaura).
   - **Menú contextual (Clic derecho):**
     - ➕ **Nueva nota**
     - 👁️ **Mostrar todas las notas** / **Ocultar todas**
     - 📑 **Notas (Submenú/Lista):** Muestra todas las notas guardadas (con vista previa del texto y punto de color). Cada una con checkbox o acción para abrir/ocultar individualmente.
     - ❌ **Salir completamente** (con guardado síncrono previo).

3. **Modos de Flotación (Botón de 3 estados en cada nota):**
   - Cicla entre:
     - 📌 **Top (Sobre todo):** `Qt.WindowStaysOnTopHint`.
     - 🪟 **Normal:** Sin hints especiales de nivel de ventana (nivel estándar del gestor de ventanas).
     - 🖥️ **Desktop (Fondo):** `Qt.WindowStaysOnBottomHint`.
   - Se guarda el estado del modo en el modelo y en `notes.json` (`mode: "top" | "normal" | "desktop"`).

4. **UX / UI de la barra superior:**
   - **Barra limpia:**
     - Izquierda: `＋` (crear nueva nota), botón de modo de flotación dinámico (📌 / 🪟 / 🖥️).
     - Derecha: Botón de menú `…` (despliega paleta de colores y botón `🗑 Eliminar`) y botón `✕` (cerrar/ocultar a bandeja).
   - Área de arrastre fluida en el centro mediante `DragHandler` y `startSystemMove()`.

## Esquema de Datos Actualizado

```json
{
  "version": 2,
  "notes": [
    {
      "id": "uuid4",
      "text": "Contenido...",
      "color": "#FFF59D",
      "w": 280,
      "h": 280,
      "visible": true,
      "mode": "normal",
      "updated": "ISO-8601"
    }
  ]
}
```
Retrocompatible: Si `visible` o `mode` no están en el JSON, se asumen `visible: true` y `mode: "normal"`.
