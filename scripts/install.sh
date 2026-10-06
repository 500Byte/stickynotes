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
