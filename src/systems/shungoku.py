from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

import pygame

from src.engine.context import ShungokuState
from src.entities.effect import Effect, StaticImageBurstEffect
from src.utils import constants

if TYPE_CHECKING:
    from src.entities.player import Player


class ShungokuManager:
    """瞬獄殺の演出シーケンスを管理するクラス。"""

    def __init__(
        self,
        *,
        shungoku_state: ShungokuState,
        shungoku_stage_bg_img: pygame.Surface | None,
        shungoku_asura_se: pygame.mixer.Sound | None,
        shungoku_super_se: pygame.mixer.Sound | None,
        shungoku_ko_se: pygame.mixer.Sound | None,
        hit_se: pygame.mixer.Sound | None,
        hit_fx_img: pygame.Surface | None,
    ) -> None:
        self.state = shungoku_state
        self.stage_bg_img = shungoku_stage_bg_img
        self.asura_se = shungoku_asura_se
        self.super_se = shungoku_super_se
        self.ko_se = shungoku_ko_se
        self.hit_se = hit_se
        self.hit_fx_img = hit_fx_img
        
        # 阿修羅SEのチャンネル
        self.asura_channel: pygame.mixer.Channel | None = None

    def handle_special_results(
        self,
        res: dict[str, Any],
        *,
        side: int,
        player: Player,
        super_freeze_frames_left: int,
    ) -> tuple[int, int]:
        """
        必殺技の結果を処理し、スーパーフリーズ情報を返す。
        
        Returns:
            (super_freeze_frames_left, super_freeze_attacker_side)
        """
        new_freeze = super_freeze_frames_left
        new_attacker_side = 0

        if bool(res.get("did_shungoku")):
            if self.state.start_queued_side != 0:
                return new_freeze, new_attacker_side
            
            if self.state.super_se_cooldown <= 0:
                if self.super_se is not None:
                    self.super_se.play()
                self.state.super_se_cooldown = 12
            
            new_freeze = max(super_freeze_frames_left, 10)
            new_attacker_side = side
            self.state.start_queued_side = side
            self.state.pan_frames_left = self.state.pan_total_frames
            
            try:
                dx = int(player.rect.centerx) - int(constants.STAGE_WIDTH // 2)
            except Exception:
                dx = 0
            self.state.pan_target_px = int(max(-18, min(18, round(dx * 0.35))))

        return new_freeze, new_attacker_side

    def update_super_se_cooldown(self) -> None:
        """超必殺技SEのクールダウンを更新。"""
        if self.state.super_se_cooldown > 0:
            self.state.super_se_cooldown = max(0, self.state.super_se_cooldown - 1)

    def start_queued_shungoku(self, p1: Player, p2: Player) -> None:
        """キューされた瞬獄殺を開始する。"""
        if self.state.start_queued_side not in {1, 2}:
            return
        
        starter = p1 if self.state.start_queued_side == 1 else p2
        if bool(getattr(starter, "_shungoku_pending_start", False)):
            try:
                starter.start_shungokusatsu()
            except Exception:
                pass
        self.state.start_queued_side = 0

    def update_dash_sequence(
        self,
        p1: Player,
        p2: Player,
    ) -> dict[str, Any]:
        """
        瞬獄殺のダッシュシーケンスを更新。
        
        Returns:
            dict with keys:
            - "hit_occurred": bool
            - "attacker_side": int
            - "defender_side": int
            - "damage": int
            - "is_ko": bool
        """
        result = {
            "hit_occurred": False,
            "attacker_side": 0,
            "defender_side": 0,
            "damage": 0,
            "is_ko": False,
        }

        if self.state.cine_frames_left > 0:
            return result

        for side, atk, dfd in ((1, p1, p2), (2, p2, p1)):
            if not bool(getattr(atk, "_shungoku_active", False)):
                continue
            
            startup_left = int(getattr(atk, "_shungoku_startup_frames_left", 0))
            if startup_left > 0:
                setattr(atk, "_shungoku_startup_frames_left", startup_left - 1)
                continue
            
            dash_left = int(getattr(atk, "_shungoku_dash_frames_left", 0))
            if dash_left <= 0:
                setattr(atk, "_shungoku_active", False)
                try:
                    if self.asura_channel is not None:
                        self.asura_channel.stop()
                except Exception:
                    pass
                self.asura_channel = None
                continue

            # 阿修羅SEの再生
            if self.asura_se is not None:
                dash_total = int(constants.FPS * 1.2)
                if dash_left == dash_total and self.asura_channel is None:
                    try:
                        self.asura_channel = self.asura_se.play(loops=-1)
                    except Exception:
                        self.asura_channel = None

            # ダッシュ移動
            speed = 9.0
            dir_x = int(getattr(atk, "_shungoku_dash_dir", 1))
            try:
                atk.push_shungoku_afterimage()
            except Exception:
                pass
            atk.pos_x += float(dir_x) * float(speed)
            atk.rect.midbottom = (int(atk.pos_x), int(atk.pos_y))
            setattr(atk, "facing", dir_x)
            setattr(atk, "_shungoku_dash_frames_left", dash_left - 1)

            # ヒット検出
            if atk.rect.colliderect(dfd.get_hurtbox()):
                setattr(atk, "_shungoku_active", False)
                setattr(atk, "_shungoku_dash_frames_left", 0)
                
                self.state.cine_frames_left = int(constants.FPS * 2.5)
                self.state.flash_frames_left = 0
                self.state.finish_frames_left = int(constants.FPS * 1.2)
                self.state.attacker_side = side
                self.state.defender_side = 2 if side == 1 else 1
                self.state.hit_se_cooldown = 0

                try:
                    if self.asura_channel is not None:
                        self.asura_channel.stop()
                except Exception:
                    pass
                self.asura_channel = None

                dmg = int(getattr(constants, "SHUNGOKUSATSU_DAMAGE", 450))
                self.state.pending_damage = dmg
                self.state.pending_apply = True
                self.state.pending_ko = (int(getattr(dfd, "hp", 0)) - dmg) <= 0

                # 攻撃者を防御者の後ろに配置
                behind = -dir_x
                atk.pos_x = float(dfd.pos_x + (behind * 48))
                atk.rect.midbottom = (int(atk.pos_x), int(atk.pos_y))

                result = {
                    "hit_occurred": True,
                    "attacker_side": side,
                    "defender_side": 2 if side == 1 else 1,
                    "damage": dmg,
                    "is_ko": self.state.pending_ko,
                }
                break

        return result

    def update_cinematic(
        self,
        p1: Player,
        p2: Player,
        effects: list[Effect],
    ) -> dict[str, Any]:
        """
        瞬獄殺のシネマティック演出を更新。
        
        Returns:
            dict with keys:
            - "should_stop_bgm": bool
            - "damage_applied": bool
            - "ko_occurred": bool
            - "stage_bg_override": pygame.Surface | None
        """
        result = {
            "should_stop_bgm": False,
            "damage_applied": False,
            "ko_occurred": False,
            "stage_bg_override": None,
        }

        if self.state.cine_frames_left <= 0:
            return result

        self.state.cine_frames_left = max(0, self.state.cine_frames_left - 1)
        
        # ヒットSE演出
        if self.state.hit_se_cooldown > 0:
            self.state.hit_se_cooldown -= 1
        if self.state.hit_se_cooldown <= 0:
            if self.hit_se is not None:
                self.hit_se.play()
            self.state.hit_se_cooldown = max(1, int(constants.FPS // 10))
            
            if self.hit_fx_img is not None:
                try:
                    for _i in range(random.randint(6, 10)):
                        hx = int(random.randint(0, max(0, int(constants.STAGE_WIDTH) - 1)))
                        hy = int(random.randint(0, max(0, int(constants.STAGE_HEIGHT) - 1)))
                        effects.append(
                            StaticImageBurstEffect(
                                image=self.hit_fx_img,
                                pos=(hx, hy),
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

        # ダメージ適用
        if self.state.cine_frames_left <= 0 and self.state.pending_apply:
            atk = p1 if self.state.attacker_side == 1 else p2
            dfd = p2 if self.state.defender_side == 2 else p1
            dfd.take_damage(self.state.pending_damage)
            dfd.enter_knockdown()
            
            if self.state.pending_ko:
                if self.ko_se is not None:
                    self.ko_se.play()
                if self.stage_bg_img is not None:
                    result["stage_bg_override"] = self.stage_bg_img
                    self.state.ko_anim_side = self.state.attacker_side
                    self.state.ko_anim_idx = 1
                    self.state.ko_anim_tick = 0
                    result["ko_occurred"] = True
            else:
                self.state.posthit_lock_side = self.state.attacker_side
                self.state.posthit_lock_defender_side = self.state.defender_side
            
            self.state.pending_damage = 0
            self.state.pending_apply = False
            self.state.pending_ko = False
            result["damage_applied"] = True

        if self.state.cine_frames_left <= 0:
            self.state.finish_frames_left = max(0, self.state.finish_frames_left)

        return result

    def update_ko_animation(self) -> None:
        """瞬獄殺KOアニメーションを更新。"""
        if self.state.ko_anim_side not in {1, 2}:
            return
        
        self.state.ko_anim_tick += 1
        if self.state.ko_anim_tick >= self.state.ko_anim_frames_per_image:
            self.state.ko_anim_tick = 0
            if self.state.ko_anim_idx < 16:
                self.state.ko_anim_idx += 1
            else:
                self.state.ko_anim_idx = 10

    def draw_ko_animation(
        self,
        surface: pygame.Surface,
        player: Player,
        *,
        is_correct_side: bool,
    ) -> bool:
        """
        瞬獄殺KOアニメーションを描画。
        
        Returns:
            True if animation was drawn, False otherwise
        """
        if not is_correct_side or self.state.ko_anim_side not in {1, 2}:
            return False
        
        idx = max(1, min(16, self.state.ko_anim_idx))
        key = (5400, idx)
        img = getattr(player, "_sprites", {}).get(key)
        if img is None:
            return False
        
        x = int(player.rect.centerx) - (img.get_width() // 2)
        y = int(player.rect.bottom) - img.get_height()
        if int(getattr(player, "facing", 1)) < 0:
            img = pygame.transform.flip(img, True, False)
        surface.blit(img, (x, y))
        return True

    def calculate_pan_offset(self) -> int:
        """画面パンのオフセットを計算。"""
        if self.state.pan_frames_left <= 0:
            return 0
        
        self.state.pan_frames_left = max(0, self.state.pan_frames_left - 1)
        t = float(self.state.pan_total_frames - self.state.pan_frames_left) / float(max(1, self.state.pan_total_frames))
        if t < 0.5:
            ease = t / 0.5
        else:
            ease = (1.0 - t) / 0.5
        ease = max(0.0, min(1.0, ease))
        return int(round(-float(self.state.pan_target_px) * ease))
