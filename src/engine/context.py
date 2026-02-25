from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    import pygame
    from src.entities.effect import Effect, Projectile
    from src.entities.player import Player


# ---------------------------------------------------------------------------
# Game State (moved from main.py top-level)
# ---------------------------------------------------------------------------

class GameState(Enum):
    TITLE = auto()
    BATTLE = auto()
    TRAINING = auto()
    CHAR_SELECT = auto()
    RESULT = auto()


# ---------------------------------------------------------------------------
# Frame Meter types (moved from main.py top-level)
# ---------------------------------------------------------------------------

class FrameState(Enum):
    IDLE = auto()
    STARTUP = auto()
    ACTIVE = auto()
    RECOVERY = auto()
    STUN = auto()
    SPECIAL = auto()


@dataclass(frozen=True)
class FrameSample:
    state: FrameState
    hitstop: bool = False
    combo: bool = False


class FrameDataTracker:
    def __init__(self, *, max_frames: int) -> None:
        self._buf: deque[FrameSample] = deque(maxlen=max(1, int(max_frames)))

    def push(self, sample: FrameSample) -> None:
        self._buf.append(sample)

    def items(self) -> list[FrameSample]:
        return list(self._buf)


# ---------------------------------------------------------------------------
# Shungoku cinematic state
# ---------------------------------------------------------------------------

@dataclass
class ShungokuState:
    cine_frames_left: int = 0
    flash_frames_left: int = 0
    finish_frames_left: int = 0
    attacker_side: int = 0
    defender_side: int = 0
    hit_se_cooldown: int = 0

    ko_anim_side: int = 0
    ko_anim_idx: int = 1
    ko_anim_tick: int = 0
    ko_anim_frames_per_image: int = 4

    pending_damage: int = 0
    pending_apply: bool = False
    pending_ko: bool = False

    posthit_lock_side: int = 0
    posthit_lock_defender_side: int = 0

    pan_frames_left: int = 0
    pan_total_frames: int = 12
    pan_target_px: int = 0

    start_queued_side: int = 0
    super_se_cooldown: int = 0

    def reset(self) -> None:
        """試合リセット時にシネマ状態を初期化する。"""
        self.cine_frames_left = 0
        self.flash_frames_left = 0
        self.finish_frames_left = 0
        self.attacker_side = 0
        self.defender_side = 0
        self.hit_se_cooldown = 0
        self.ko_anim_side = 0
        self.ko_anim_idx = 1
        self.ko_anim_tick = 0
        self.pending_damage = 0
        self.pending_apply = False
        self.pending_ko = False
        self.posthit_lock_side = 0
        self.posthit_lock_defender_side = 0
        self.pan_frames_left = 0
        self.pan_target_px = 0
        self.start_queued_side = 0
        self.super_se_cooldown = 0
