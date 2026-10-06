# StickyNotes — Design

App de notas adhesivas flotantes para Wayland (Hyprland), escrita con Qt6/QML (PyQt6), portable entre escritorios Qt y GTK.

## Decisiones

- **Toolkit:** PyQt6 + QML. Sin layer-shell: cada nota es una ventana normal sin bordes (`FramelessWindowHint`, xdg-toplevel), portable a cualquier compositor (incl. GNOME).
- **Flotado/pin:** lo controla el usuario. En Hyprland `Super+ñ` cicla tiled → flotante → pin → tiled; `Super+clic` arrastra/redimensiona. Regla en `~/.config/hypr/config/settings.lua` (`float-stickynotes`, class `stickynotes|com.diego.StickyNotes`) hace que nazcan flotantes.
- **Alcance v1:** crear/borrar notas, texto plano, paleta de 8 colores, mover/redimensionar, persistencia JSON con autoguardado, tema oscuro por defecto.
- **Fuera de alcance:** Markdown, checklists, bandeja, sincronización, restauración de posición (Wayland no permite que el cliente fije posición).

## Arquitectura

Repo: `~/Documents/GitHub/stickynotes`.

| Archivo | Responsabilidad |
|---|---|
| `stickynotes/store.py` | Carga/guarda `~/.local/share/stickynotes/notes.json`. Escritura atómica (tmp + rename). JSON corrupto → renombrar a `notes.json.bak` y arrancar vacío. |
| `stickynotes/model.py` | `NotesModel(QAbstractListModel)`: roles `noteId, text, color, w, h`. Métodos invocables desde QML: `addNote()`, `removeNote(row)`, `setText(row, t)`, `setColor(row, c)`, `setSize(row, w, h)`. Autoguardado con debounce de 500 ms. |
| `stickynotes/ipc.py` | Instancia única vía `QLocalServer`/`QLocalSocket`. Segundo lanzamiento envía `new` y sale. |
| `stickynotes/main.py` | Entrada. Flag `--new`. App-id/desktop-file-name `stickynotes`. Expone el modelo a QML. |
| `stickynotes/qml/Note.qml` | Ventana de nota: barra superior (＋, colores, borrar), arrastre con `startSystemMove()`, esquina con `startSystemResize()`, `TextArea`. |
| `stickynotes/qml/main.qml` | `Instantiator` que crea una `Note` por fila del modelo. |
| `data/stickynotes.desktop`, `data/stickynotes.svg` | Integración de escritorio. |
| `tests/` | pytest para store, model e IPC; smoke test QML con `QT_QPA_PLATFORM=offscreen`. |

## Flujo de datos

QML → `model.setText/...` → marca sucio → debounce 500 ms → `store.save(notes)`. Al arrancar: `store.load()` → modelo → una ventana por nota. Si no hay notas, se crea una vacía. Al borrar la última nota, se crea otra vacía (la app siempre tiene ≥1 nota).

## Datos

```json
{"version": 1, "notes": [{"id": "uuid4", "text": "", "color": "#FFF59D", "w": 280, "h": 280, "updated": "ISO-8601"}]}
```

Paleta (8): `#FFF59D #FFCC80 #F48FB1 #CE93D8 #90CAF9 #80DEEA #A5D6A7 #E0E0E0`. Texto oscuro sobre cada color (contraste suficiente en claro y oscuro).

## Errores

- JSON ilegible → `.bak` + arranque vacío, aviso por stderr.
- Fallo de escritura → se conserva el estado en memoria, se reintenta en el siguiente cambio, aviso por stderr.
- Socket IPC huérfano → se elimina y se vuelve a escuchar.

## Pruebas

- `store`: roundtrip, escritura atómica, JSON corrupto → `.bak`.
- `model`: add/remove/setters, señal de cambios, invariante ≥1 nota, debounce guarda una sola vez.
- `ipc`: el segundo cliente entrega `new` al primero.
- Smoke QML offscreen: carga `main.qml` sin errores y crea N ventanas.
