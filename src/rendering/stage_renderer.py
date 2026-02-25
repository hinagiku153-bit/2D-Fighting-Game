from __future__ import annotations

import random
from pathlib import Path

import pygame

from src.utils import constants
from src.utils.paths import resource_path


class StageRenderer:
    """ステージ背景・雨エフェクトの描画を担当するクラス。"""

    def __init__(self, *, rain_count: int = 90) -> None:
        self.stage_bg_frames: list[pygame.Surface] = self._load_stage_frames()
        self.rain_drops: list[dict[str, float]] = self._init_rain_drops(rain_count)

    # ------------------------------------------------------------------
    # Stage background frames
    # ------------------------------------------------------------------

    @staticmethod
    def _load_stage_frames() -> list[pygame.Surface]:
        frames: list[pygame.Surface] = []
        for name in ("01.png", "02.png", "03.png", "04.png"):
            p = resource_path(Path("assets/images/stage") / name)
            if not p.exists():
                return []
            try:
                frames.append(pygame.image.load(str(p)).convert_alpha())
            except pygame.error:
                return []
        return frames

    # ------------------------------------------------------------------
    # Rain
    # ------------------------------------------------------------------

    @staticmethod
    def _init_rain_drops(count: int) -> list[dict[str, float]]:
        drops: list[dict[str, float]] = []
        for _ in range(max(0, int(count))):
            drops.append(
                {
                    "x": float(random.randrange(0, constants.STAGE_WIDTH)),
                    "y": float(random.randrange(-constants.STAGE_HEIGHT, constants.STAGE_HEIGHT)),
                    "vy": float(random.uniform(9.0, 15.0)),
                    "vx": float(random.uniform(-1.0, 0.8)),
                    "len": float(random.uniform(10.0, 18.0)),
                    "a": float(random.uniform(90.0, 150.0)),
                }
            )
        return drops

    def update_rain(self) -> None:
        for d in self.rain_drops:
            d["x"] = float(d.get("x", 0.0)) + float(d.get("vx", 0.0))
            d["y"] = float(d.get("y", 0.0)) + float(d.get("vy", 0.0))

            if d["y"] > float(constants.STAGE_HEIGHT + 30):
                d["y"] = float(random.uniform(-120.0, -20.0))
                d["x"] = float(random.randrange(-20, constants.STAGE_WIDTH + 20))
            if d["x"] < -40:
                d["x"] = float(constants.STAGE_WIDTH + 40)
            if d["x"] > float(constants.STAGE_WIDTH + 40):
                d["x"] = float(-40)

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def draw_background(
        surface: pygame.Surface,
        *,
        tick_ms: int,
        stage_bg_frames: list[pygame.Surface],
        stage_bg_img: pygame.Surface | None,
    ) -> None:
        bg_img: pygame.Surface | None = None
        if stage_bg_frames:
            bg_img = stage_bg_frames[0]
        else:
            bg_img = stage_bg_img

        if bg_img is not None:
            bg = pygame.transform.smoothscale(bg_img, (constants.STAGE_WIDTH, constants.STAGE_HEIGHT))
            surface.blit(bg, (0, 0))

            dark = pygame.Surface((constants.STAGE_WIDTH, constants.STAGE_HEIGHT), pygame.SRCALPHA)
            dark.fill((20, 40, 70, 95))
            surface.blit(dark, (0, 0))

    def draw_rain(self, surface: pygame.Surface) -> None:
        if not self.rain_drops:
            return
        rain = pygame.Surface((constants.STAGE_WIDTH, constants.STAGE_HEIGHT), pygame.SRCALPHA)
        for d in self.rain_drops:
            x = int(d.get("x", 0.0))
            y = int(d.get("y", 0.0))
            ln = int(d.get("len", 14.0))
            a = int(max(0, min(255, int(d.get("a", 120.0)))))
            pygame.draw.line(rain, (170, 210, 255, a), (x, y), (x - 2, y + ln), 1)
        surface.blit(rain, (0, 0))
