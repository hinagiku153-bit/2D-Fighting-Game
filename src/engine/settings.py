from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pygame


def settings_path() -> Path:
    """設定ファイルのパスを返す。PyInstaller 時でも書き込みできるユーザー領域。"""
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "2D-Fighting-Game" / "settings.json"
    return Path.home() / ".2d_fighting_game_settings.json"


def load_settings() -> dict[str, Any]:
    p = settings_path()
    try:
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def save_settings(data: dict[str, Any]) -> None:
    p = settings_path()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Keybinds
# ---------------------------------------------------------------------------

DEFAULT_KEYBINDS: dict[str, int] = {
    "P1_LEFT": int(pygame.K_a),
    "P1_RIGHT": int(pygame.K_d),
    "P1_DOWN": int(pygame.K_s),
    "P1_JUMP": int(pygame.K_w),
    # Guilty Gear Strive button layout (5 buttons)
    "P1_P": int(pygame.K_u),    # Punch
    "P1_K": int(pygame.K_j),    # Kick
    "P1_S": int(pygame.K_i),    # Slash
    "P1_HS": int(pygame.K_k),   # Heavy Slash
    "P1_D": int(pygame.K_o),    # Dust Attack
    "P2_LEFT": int(pygame.K_LEFT),
    "P2_RIGHT": int(pygame.K_RIGHT),
    "P2_DOWN": int(pygame.K_DOWN),
    "P2_JUMP": int(pygame.K_UP),
    "P2_ATTACK": int(pygame.K_SEMICOLON),
    "FIELD_RESET": int(pygame.K_r),
    # backward-compat (old save key)
    "QUICK_RESET": int(pygame.K_r),
}


def load_keybinds(settings: dict[str, Any]) -> dict[str, int]:
    """settings dict からキーバインドを復元して返す。"""
    keybinds: dict[str, int] = dict(DEFAULT_KEYBINDS)
    try:
        raw = settings.get("keybinds", {})
        if isinstance(raw, dict):
            for k, v in raw.items():
                if k in DEFAULT_KEYBINDS:
                    try:
                        keybinds[str(k)] = int(v)
                    except (TypeError, ValueError):
                        continue
    except Exception:
        pass

    # backward-compat: if the config had QUICK_RESET only, map it to FIELD_RESET.
    try:
        if "FIELD_RESET" not in keybinds and "QUICK_RESET" in keybinds:
            keybinds["FIELD_RESET"] = int(keybinds.get("QUICK_RESET", pygame.K_r))
        if "FIELD_RESET" in keybinds and "QUICK_RESET" not in keybinds:
            keybinds["QUICK_RESET"] = int(keybinds.get("FIELD_RESET", pygame.K_r))
    except Exception:
        pass

    return keybinds


def save_keybinds(settings: dict[str, Any], keybinds: dict[str, int]) -> None:
    """キーバインドを settings dict に書き込みファイルへ保存する。"""
    settings["keybinds"] = dict(keybinds)
    save_settings(settings)


def key_name(code: int) -> str:
    try:
        return str(pygame.key.name(int(code)))
    except Exception:
        return str(code)
