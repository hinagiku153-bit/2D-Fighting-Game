from __future__ import annotations

from pathlib import Path
import sys


def get_base_path() -> Path:
    # PyInstaller onefile/onedir builds set sys._MEIPASS to the temporary extraction directory.
    mei = getattr(sys, "_MEIPASS", None)
    if mei:
        return Path(mei)

    # Source run: main.py lives at project root.
    # src/utils/paths.py -> src/utils -> src -> project_root
    return Path(__file__).resolve().parents[2]


def resource_path(relative_path: str | Path) -> Path:
    rel = Path(relative_path)
    return get_base_path() / rel
