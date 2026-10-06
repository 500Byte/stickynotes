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


def load(path=DEFAULT_PATH) -> list[dict]:
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


def save(notes: list[dict], path=DEFAULT_PATH) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".notes-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"version": 1, "notes": notes}, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
