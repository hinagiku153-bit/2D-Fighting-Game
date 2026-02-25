from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.utils import constants

if TYPE_CHECKING:
    from src.entities.player import Player


class CollisionSystem:
    """衝突判定システム。Pushbox（押し合い）とHitbox vs Hurtbox判定を担当。"""

    @staticmethod
    def resolve_pushbox_overlap(
        p1: Player,
        p2: Player,
        *,
        shungoku_active: bool = False,
    ) -> None:
        """
        Pushbox が重なったら、x方向に左右へ押し戻して重なりを解消する。
        瞬獄殺中は押し合いを無効化。
        """
        if shungoku_active:
            return

        p1_push = p1.get_pushbox()
        p2_push = p2.get_pushbox()

        if not p1_push.colliderect(p2_push):
            return

        overlap_x = min(p1_push.right - p2_push.left, p2_push.right - p1_push.left)
        if overlap_x <= 0:
            return

        push = (overlap_x + 1) // 2
        if p1.rect.centerx < p2.rect.centerx:
            p1.pos_x -= float(push)
            p2.pos_x += float(push)
        else:
            p1.pos_x += float(push)
            p2.pos_x -= float(push)

        # 押し戻し後も画面外へ出ないように補正する。
        p1_half_w = p1.rect.width / 2.0
        p2_half_w = p2.rect.width / 2.0
        p1.pos_x = max(p1_half_w, min(constants.SCREEN_WIDTH - p1_half_w, p1.pos_x))
        p2.pos_x = max(p2_half_w, min(constants.SCREEN_WIDTH - p2_half_w, p2.pos_x))
        p1.rect.midbottom = (int(p1.pos_x), int(p1.pos_y))
        p2.rect.midbottom = (int(p2.pos_x), int(p2.pos_y))

    @staticmethod
    def check_hit_collision(attacker: Player, defender: Player) -> tuple[int, int] | None:
        """
        Hitbox vs Hurtbox の衝突判定を行い、衝突点を返す。
        衝突していない場合は None を返す。
        """
        hitboxes = attacker.get_hitboxes()
        if not hitboxes:
            return None

        hurtboxes = defender.get_hurtboxes()
        hit_point: tuple[int, int] | None = None

        for hitbox in hitboxes:
            for hurtbox in hurtboxes:
                if not hitbox.colliderect(hurtbox):
                    continue
                overlap = hitbox.clip(hurtbox)
                if overlap.width > 0 and overlap.height > 0:
                    hit_point = overlap.center
                else:
                    hit_point = hitbox.center
                break
            if hit_point is not None:
                break

        return hit_point
