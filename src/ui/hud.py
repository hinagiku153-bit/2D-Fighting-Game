from __future__ import annotations

import math

import pygame

from src.utils import constants


def draw_hp_bar(
    surface: pygame.Surface,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    hp: float,
    chip_hp: float,
    max_hp: float,
    align_right: bool,
) -> None:
    bg_rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surface, constants.COLOR_HP_BG, bg_rect)

    hp_ratio = 0.0 if max_hp <= 0 else max(0.0, min(1.0, hp / max_hp))
    chip_ratio = 0.0 if max_hp <= 0 else max(0.0, min(1.0, chip_hp / max_hp))

    hp_w = int(w * hp_ratio)
    chip_w = int(w * chip_ratio)

    if align_right:
        chip_rect = pygame.Rect(x + (w - chip_w), y, chip_w, h)
        fill_rect = pygame.Rect(x + (w - hp_w), y, hp_w, h)
    else:
        chip_rect = pygame.Rect(x, y, chip_w, h)
        fill_rect = pygame.Rect(x, y, hp_w, h)

    pygame.draw.rect(surface, constants.COLOR_HP_CHIP, chip_rect)
    pygame.draw.rect(surface, constants.COLOR_HP_FILL, fill_rect)
    pygame.draw.rect(surface, (200, 200, 200), bg_rect, 2)


def draw_power_gauge(
    surface: pygame.Surface,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    value: float,
    max_value: float,
    align_right: bool,
) -> None:
    bg_rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surface, (30, 30, 45), bg_rect)

    ratio = 0.0 if max_value <= 0 else max(0.0, min(1.0, value / max_value))
    fill_w = int(w * ratio)
    if align_right:
        fill_rect = pygame.Rect(x + (w - fill_w), y, fill_w, h)
    else:
        fill_rect = pygame.Rect(x, y, fill_w, h)

    pygame.draw.rect(surface, (80, 160, 255), fill_rect)
    pygame.draw.rect(surface, (200, 200, 200), bg_rect, 2)

    segs = int(getattr(constants, "POWER_GAUGE_SEGMENTS", 10))
    segs = max(1, segs)
    for i in range(1, segs):
        xx = int(x + (w * i) / segs)
        pygame.draw.line(surface, (130, 130, 150), (xx, y + 1), (xx, y + h - 2), 1)


def draw_round_markers(
    surface: pygame.Surface,
    *,
    x: int,
    y: int,
    wins: int,
    max_wins: int,
    align_right: bool,
    tick_ms: int,
) -> None:
    r = 7
    gap = 6
    glow = 10
    a = int(90 + 60 * math.sin(tick_ms / 220.0))
    a = max(0, min(255, a))

    for i in range(max(0, int(max_wins))):
        filled = i < int(wins)
        dx = i * (r * 2 + gap)
        cx = int(x - dx if align_right else x + dx)
        cy = int(y)

        if filled:
            pygame.draw.circle(surface, (255, 255, 255, a), (cx, cy), glow)
            pygame.draw.circle(surface, (255, 235, 160), (cx, cy), r)
            pygame.draw.circle(surface, (255, 255, 255), (cx, cy), r, 2)
        else:
            pygame.draw.circle(surface, (120, 120, 120), (cx, cy), r, 2)
