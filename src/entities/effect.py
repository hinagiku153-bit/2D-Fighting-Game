from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pygame

from src.utils.paths import resource_path


@dataclass
class Effect:
    frames: list[pygame.Surface]
    pos: tuple[int, int]
    frames_per_image: int = 2

    _frame_index: int = 0
    _frame_tick: int = 0
    _finished: bool = False

    @classmethod
    def load_sequence_from_folder(
        cls,
        *,
        folder: Path,
        pos: tuple[int, int],
        frames_per_image: int = 2,
    ) -> Effect | None:
        folder = resource_path(folder)
        if not folder.exists() or not folder.is_dir():
            return None

        files = sorted([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == ".png"])
        if not files:
            return None

        frames: list[pygame.Surface] = []
        for p in files:
            try:
                frames.append(pygame.image.load(str(p)).convert_alpha())
            except pygame.error:
                continue

        if not frames:
            return None

        return cls(frames=frames, pos=pos, frames_per_image=max(1, int(frames_per_image)))

    @property
    def finished(self) -> bool:
        return self._finished

    def update(self) -> None:
        if self._finished:
            return

        self._frame_tick += 1
        if self._frame_tick < self.frames_per_image:
            return

        self._frame_tick = 0
        self._frame_index += 1
        if self._frame_index >= len(self.frames):
            self._finished = True

    def draw(self, surface: pygame.Surface) -> None:
        if self._finished:
            return
        if self._frame_index < 0 or self._frame_index >= len(self.frames):
            return

        img = self.frames[self._frame_index]
        x, y = self.pos
        surface.blit(img, (x - (img.get_width() // 2), y - (img.get_height() // 2)))


@dataclass
class Projectile:
    pos: pygame.Vector2
    vel: pygame.Vector2
    owner_side: int = 0
    radius: int = 10
    color: tuple[int, int, int] = (120, 200, 255)
    frames_left: int = 90
    damage: int = 40
    hitstun_frames: int = 18
    frames: list[pygame.Surface] | None = None
    frames_per_image: int = 3
    _frame_index: int = 0
    _frame_tick: int = 0
    _finished: bool = False

    @classmethod
    def load_frames_any(
        cls,
        *,
        png_path: Path | None = None,
        folder: Path | None = None,
    ) -> list[pygame.Surface] | None:
        if png_path is not None:
            p = resource_path(png_path)
            if p.exists() and p.is_file():
                try:
                    return [pygame.image.load(str(p)).convert_alpha()]
                except pygame.error:
                    pass

        if folder is not None:
            f = resource_path(folder)
            if f.exists() and f.is_dir():
                files = sorted([p for p in f.iterdir() if p.is_file() and p.suffix.lower() == ".png"])
                if files:
                    frames: list[pygame.Surface] = []
                    for p in files:
                        try:
                            frames.append(pygame.image.load(str(p)).convert_alpha())
                        except pygame.error:
                            continue
                    if frames:
                        return frames

        return None

    @property
    def finished(self) -> bool:
        return self._finished

    def get_rect(self) -> pygame.Rect:
        if self.frames and 0 <= self._frame_index < len(self.frames):
            img = self.frames[self._frame_index]
            w = int(img.get_width())
            h = int(img.get_height())
            return pygame.Rect(int(self.pos.x) - (w // 2), int(self.pos.y) - (h // 2), w, h)

        r = int(self.radius)
        return pygame.Rect(int(self.pos.x) - r, int(self.pos.y) - r, r * 2, r * 2)

    def update(self, *, bounds: pygame.Rect | None = None) -> None:
        if self._finished:
            return

        if self.frames:
            self._frame_tick += 1
            if self._frame_tick >= max(1, int(self.frames_per_image)):
                self._frame_tick = 0
                self._frame_index = (self._frame_index + 1) % max(1, len(self.frames))

        self.pos += self.vel
        self.frames_left -= 1
        if self.frames_left <= 0:
            self._finished = True
            return

        if bounds is not None:
            if not self.get_rect().colliderect(bounds):
                self._finished = True

    def draw(self, surface: pygame.Surface) -> None:
        if self._finished:
            return
        if self.frames and 0 <= self._frame_index < len(self.frames):
            img = self.frames[self._frame_index]
            if float(self.vel.x) < 0:
                img = pygame.transform.flip(img, True, False)
            surface.blit(img, (int(self.pos.x) - (img.get_width() // 2), int(self.pos.y) - (img.get_height() // 2)))
            return

        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), int(self.radius))


@dataclass
class SuperProjectile(Projectile):
    hit_interval_frames: int = 4
    max_hits: int = 5
    push_on_hit_px: int = 2
    _hit_cooldown: int = 0
    _hits_done: int = 0

    def update(self, *, bounds: pygame.Rect | None = None) -> None:
        if self._hit_cooldown > 0:
            self._hit_cooldown -= 1
        super().update(bounds=bounds)

    def can_hit_now(self) -> bool:
        if self._hits_done >= int(self.max_hits):
            return False
        return int(self._hit_cooldown) <= 0

    def register_hit(self) -> None:
        self._hits_done += 1
        self._hit_cooldown = max(0, int(self.hit_interval_frames))
