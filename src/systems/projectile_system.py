from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

import pygame

from src.engine.context import GameState
from src.entities.effect import Effect, StaticImageBurstEffect, Projectile, SuperProjectile
from src.utils import constants

if TYPE_CHECKING:
    from src.entities.player import Player


class ProjectileSystem:
    """波動拳・真空波動拳の生成とヒット判定を管理するシステム。"""

    def __init__(
        self,
        *,
        hadoken_frames: list[pygame.Surface] | None,
        shinku_frames: list[pygame.Surface] | None,
        hit_fx_img: pygame.Surface | None,
        guard_fx_img: pygame.Surface | None,
        hit_se: pygame.mixer.Sound | None,
        guard_se: pygame.mixer.Sound | None,
    ) -> None:
        self.hadoken_frames = hadoken_frames
        self.shinku_frames = shinku_frames
        self.hit_fx_img = hit_fx_img
        self.guard_fx_img = guard_fx_img
        self.hit_se = hit_se
        self.guard_se = guard_se
        self.projectiles: list[Projectile] = []

    def spawn_hadoken(self, attacker: Player, *, p1: Player, p2: Player) -> None:
        """波動拳を生成する。"""
        side = 1 if attacker is p1 else 2
        x = float(attacker.rect.centerx + attacker.facing * 34)
        y = float(attacker.rect.centery - 10)
        vx = float(attacker.facing * 8)
        self.projectiles.append(
            Projectile(
                pos=pygame.Vector2(x, y),
                vel=pygame.Vector2(vx, 0.0),
                owner_side=side,
                radius=8,
                frames_left=90,
                damage=55,
                hitstun_frames=20,
                frames=self.hadoken_frames,
                frames_per_image=3,
            )
        )

    def spawn_shinku(self, attacker: Player, *, p1: Player, p2: Player) -> None:
        """真空波動拳を生成する。"""
        side = 1 if attacker is p1 else 2
        x = float(attacker.rect.centerx + attacker.facing * 44)
        y = float(attacker.rect.centery - 18)
        vx = float(attacker.facing * 6)
        self.projectiles.append(
            SuperProjectile(
                pos=pygame.Vector2(x, y),
                vel=pygame.Vector2(vx, 0.0),
                owner_side=side,
                radius=12,
                frames_left=120,
                damage=35,
                hitstun_frames=12,
                frames=self.shinku_frames,
                frames_per_image=2,
                hit_interval_frames=4,
                max_hits=5,
                push_on_hit_px=3,
            )
        )

    def update(self) -> None:
        """全弾を更新し、画面外の弾を削除する。"""
        stage_bounds = pygame.Rect(0, 0, constants.STAGE_WIDTH, constants.STAGE_HEIGHT)
        for pr in self.projectiles:
            pr.update(bounds=stage_bounds)
        self.projectiles = [pr for pr in self.projectiles if not pr.finished]

    def check_hits(
        self,
        *,
        p1: Player,
        p2: Player,
        game_state: GameState,
        training_p2_all_guard: bool,
        effects: list[Effect],
    ) -> dict[str, Any]:
        """
        弾のヒット判定を行い、フレームメーターアドバンテージ情報を返す。
        
        Returns:
            dict with keys:
            - "frame_meter_adv_value": int | None
            - "frame_meter_adv_frames_left": int
            - "frame_meter_adv_attacker_side": int
        """
        result = {
            "frame_meter_adv_value": None,
            "frame_meter_adv_frames_left": 0,
            "frame_meter_adv_attacker_side": 0,
        }

        for pr in self.projectiles:
            if pr.finished:
                continue

            if int(getattr(pr, "owner_side", 0)) == 1:
                target = p2
                attacker = p1
            elif int(getattr(pr, "owner_side", 0)) == 2:
                target = p1
                attacker = p2
            else:
                continue

            if not pr.get_rect().colliderect(target.get_hurtbox()):
                continue

            # ガード判定
            is_guarding = bool(getattr(target, "can_guard_now", lambda: False)()) and bool(
                getattr(target, "is_guarding_intent", lambda: False)()
            )
            if game_state == GameState.TRAINING and training_p2_all_guard and (target is p2):
                is_guarding = True

            if is_guarding:
                hit_result = self._apply_projectile_guard(pr, attacker, target, effects, p1, p2)
                if hit_result["frame_meter_adv_value"] is not None:
                    result = hit_result
            else:
                hit_result = self._apply_projectile_hit(pr, attacker, target, effects, p1, p2)
                if hit_result["frame_meter_adv_value"] is not None:
                    result = hit_result

        return result

    def _apply_projectile_guard(
        self,
        pr: Projectile,
        attacker: Player,
        target: Player,
        effects: list[Effect],
        p1: Player,
        p2: Player,
    ) -> dict[str, Any]:
        """弾のガード処理。"""
        was_in_blockstun = bool(getattr(target, "in_blockstun", False))
        info = attacker.get_last_move_frame_info()
        attacker_recovery = int(getattr(info, "recovery_frames", 0)) if info is not None else 0
        defender_stun = int(getattr(constants, "BLOCKSTUN_DEFAULT_FRAMES", 12))

        damage = int(getattr(pr, "damage", 0))
        chip_ratio = float(getattr(constants, "GUARD_CHIP_DAMAGE_RATIO", 0.0))
        chip_damage = int(max(0, round(damage * chip_ratio)))
        target.take_damage(chip_damage)

        gain_guard = int(getattr(constants, "POWER_GAIN_ON_GUARD", 20))
        attacker.add_power(gain_guard)

        base_guard_kb = int(getattr(constants, "GUARD_KNOCKBACK_PX_DEFAULT", 10))
        guard_mul = float(getattr(constants, "GUARD_KNOCKBACK_MULTIPLIER", 1.35))
        guard_knockback = int(max(0, round(base_guard_kb * guard_mul)))

        dir_x = 1 if float(getattr(pr, "vel", pygame.Vector2(1, 0)).x) > 0 else -1
        target.apply_knockback(dir_x=dir_x, amount_px=guard_knockback)
        crouch_guard = bool(getattr(target, "crouching", False))
        target.enter_blockstun(crouching=crouch_guard)

        if (not was_in_blockstun) and self.guard_se is not None:
            self.guard_se.play()

        if (not was_in_blockstun) and (self.guard_fx_img is not None):
            try:
                effects.append(
                    StaticImageBurstEffect(
                        image=self.guard_fx_img,
                        pos=pr.get_rect().center,
                        total_frames=random.randint(3, 5),
                        start_scale=1.2,
                        end_scale=0.8,
                        fadeout_frames=2,
                        angle_deg=float(random.uniform(0.0, 360.0)),
                        flip_x=bool(random.random() < 0.5),
                    )
                )
            except Exception:
                pass

        extra_hitstop = int(getattr(constants, "HIT_EFFECT_EXTRA_HITSTOP_FRAMES", 4))
        hitstop_total = int(getattr(constants, "HITSTOP_DEFAULT_FRAMES", 6)) + max(0, extra_hitstop)
        attacker.hitstop_frames_left = max(attacker.hitstop_frames_left, hitstop_total)
        target.hitstop_frames_left = max(target.hitstop_frames_left, hitstop_total)

        if isinstance(pr, SuperProjectile):
            if pr.can_hit_now():
                pr.register_hit()
        else:
            pr._finished = True

        return {
            "frame_meter_adv_value": int(defender_stun) - int(attacker_recovery),
            "frame_meter_adv_frames_left": int(constants.FPS * 3),
            "frame_meter_adv_attacker_side": 1 if attacker is p1 else 2,
        }

    def _apply_projectile_hit(
        self,
        pr: Projectile,
        attacker: Player,
        target: Player,
        effects: list[Effect],
        p1: Player,
        p2: Player,
    ) -> dict[str, Any]:
        """弾のヒット処理。"""
        attacker_side = 1 if attacker is p1 else 2

        if isinstance(pr, SuperProjectile):
            if pr.can_hit_now():
                pr.register_hit()

                if int(getattr(target, "hitstun_timer", 0)) > 0:
                    attacker.extend_combo_on_opponent()
                else:
                    attacker.start_combo_on_opponent(opponent_side=(2 if attacker_side == 1 else 1))

                target.take_damage(pr.damage)
                if self.hit_se is not None:
                    self.hit_se.play()

                info = attacker.get_last_move_frame_info()
                attacker_recovery = int(getattr(info, "recovery_frames", 0)) if info is not None else 0
                defender_stun = int(getattr(pr, "hitstun_frames", 0))

                attacker.add_combo_damage(int(getattr(pr, "damage", 0)))
                target.set_combo_victim_state(attacker_side=attacker_side, hitstun_frames=pr.hitstun_frames)
                target.enter_hitstun(frames=pr.hitstun_frames)
                target.apply_knockback(dir_x=(1 if pr.vel.x > 0 else -1), amount_px=int(pr.push_on_hit_px))
                
                if int(getattr(pr, "owner_side", 0)) == 1:
                    p1.add_power(30)
                elif int(getattr(pr, "owner_side", 0)) == 2:
                    p2.add_power(30)

                return {
                    "frame_meter_adv_value": int(defender_stun) - int(attacker_recovery),
                    "frame_meter_adv_frames_left": int(constants.FPS * 3),
                    "frame_meter_adv_attacker_side": attacker_side,
                }
        else:
            pr._finished = True

            if int(getattr(target, "hitstun_timer", 0)) > 0:
                attacker.extend_combo_on_opponent()
            else:
                attacker.start_combo_on_opponent(opponent_side=(2 if attacker_side == 1 else 1))

            target.take_damage(pr.damage)
            if self.hit_se is not None:
                self.hit_se.play()

            if self.hit_fx_img is not None:
                try:
                    effects.append(
                        StaticImageBurstEffect(
                            image=self.hit_fx_img,
                            pos=pr.get_rect().center,
                            total_frames=random.randint(3, 5),
                            start_scale=1.2,
                            end_scale=0.8,
                            fadeout_frames=2,
                            angle_deg=float(random.uniform(0.0, 360.0)),
                            flip_x=bool(random.random() < 0.5),
                        )
                    )
                except Exception:
                    pass

            attacker.add_combo_damage(int(getattr(pr, "damage", 0)))
            target.set_combo_victim_state(attacker_side=attacker_side, hitstun_frames=pr.hitstun_frames)
            target.enter_hitstun(frames=pr.hitstun_frames)

        return {
            "frame_meter_adv_value": None,
            "frame_meter_adv_frames_left": 0,
            "frame_meter_adv_attacker_side": 0,
        }

    def draw_all(self, surface: pygame.Surface) -> None:
        """全弾を描画する。"""
        for pr in self.projectiles:
            pr.draw(surface)
