from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

import pygame

from src.entities.effect import Effect, StaticImageBurstEffect
from src.engine.context import GameState
from src.utils import constants
from src.utils.constants import AttackAttribute

if TYPE_CHECKING:
    from src.entities.player import Player


class CombatSystem:
    """コンバットシステム。ヒット/ガード処理、ダメージ計算、エフェクト生成を担当。"""

    def __init__(
        self,
        *,
        spark_frames: list[pygame.Surface],
        hit_fx_img: pygame.Surface | None,
        guard_fx_img: pygame.Surface | None,
        hit_se: pygame.mixer.Sound | None,
        guard_se: pygame.mixer.Sound | None,
    ) -> None:
        self.spark_frames = spark_frames
        self.hit_fx_img = hit_fx_img
        self.guard_fx_img = guard_fx_img
        self.hit_se = hit_se
        self.guard_se = guard_se

    def apply_hit(
        self,
        attacker: Player,
        defender: Player,
        hit_point: tuple[int, int],
        *,
        game_state: GameState,
        training_p2_all_guard: bool,
        effects: list[Effect],
        p1: Player,
        p2: Player,
    ) -> dict[str, Any]:
        """
        ヒット/ガード処理を実行し、フレームメーターアドバンテージ情報を返す。
        
        Returns:
            dict with keys:
            - "frame_meter_adv_value": int | None
            - "frame_meter_adv_frames_left": int
            - "frame_meter_adv_attacker_side": int
        """
        # 瞬獄殺中は通常ヒット判定を無効化
        if bool(getattr(attacker, "_shungoku_active", False)) or bool(getattr(defender, "_shungoku_active", False)):
            return {
                "frame_meter_adv_value": None,
                "frame_meter_adv_frames_left": 0,
                "frame_meter_adv_attacker_side": 0,
            }
        
        # ダウン中は無敵（攻撃を食らわない）
        if bool(getattr(defender, "_down_anim_active", False)) or bool(getattr(defender, "_ko_down_anim_active", False)):
            return {
                "frame_meter_adv_value": None,
                "frame_meter_adv_frames_left": 0,
                "frame_meter_adv_attacker_side": 0,
            }

        # 多段ヒット対応：このフレームの clsn1 グループ（hit_id）が未登録なら当たりを許可。
        if not attacker.can_deal_damage():
            return {
                "frame_meter_adv_value": None,
                "frame_meter_adv_frames_left": 0,
                "frame_meter_adv_attacker_side": 0,
            }

        attack_id = getattr(attacker, "_attack_id", None)
        
        # まず frame_data.py からデータを取得（優先）
        frame_data_dict = getattr(attacker.character, "frame_data", None)
        frame_data = None
        if frame_data_dict and attack_id:
            frame_data = frame_data_dict.get(str(attack_id))
        
        if frame_data:
            # frame_data.py のデータを使用
            damage = int(getattr(frame_data, "damage", 50))
            knockback_px = int(getattr(frame_data, "knockback_px", 12))
            hitstop_frames = int(getattr(frame_data, "hitstop_frames", constants.HITSTOP_DEFAULT_FRAMES))
            attacker_recoil_px = int(getattr(frame_data, "attacker_recoil_px", 3))
            hit_pause = int(getattr(frame_data, "hitstun_frames", 20))
        else:
            # frame_data.py にない場合は constants.ATTACK_SPECS を使用（フォールバック）
            spec = constants.ATTACK_SPECS.get(str(attack_id))
            if spec is None:
                damage = 50
                knockback_px = 12
                hitstop_frames = constants.HITSTOP_DEFAULT_FRAMES
                attacker_recoil_px = int(getattr(constants, "ATTACKER_RECOIL_PX_DEFAULT", 3))
                hit_pause = int(getattr(constants, "HITSTUN_DEFAULT_FRAMES", 20))
            else:
                damage = int(spec["damage"])
                knockback_px = int(spec["knockback_px"])
                hitstop_frames = int(spec["hitstop_frames"])
                attacker_recoil_px = int(spec.get("attacker_recoil_px", getattr(constants, "ATTACKER_RECOIL_PX_DEFAULT", 3)))
                hit_pause = int(spec.get("hit_pause", getattr(constants, "HITSTUN_DEFAULT_FRAMES", 20)))

        # 攻撃属性を取得（デフォルトはMID）
        attack_attribute = AttackAttribute.MID
        if frame_data:
            attack_attribute = getattr(frame_data, "attack_attribute", AttackAttribute.MID)
        
        # ガード判定：後ろ入力中（defender.holding_back）ならガード成功。
        # ただし、攻撃属性とガード姿勢の組み合わせをチェック
        can_guard_basic = bool(getattr(defender, "can_guard_now", lambda: False)()) and bool(
            getattr(defender, "is_guarding_intent", lambda: False)()
        )
        
        # 攻撃属性に応じたガード判定
        is_guarding = False
        if can_guard_basic:
            if attack_attribute == AttackAttribute.OVERHEAD:
                # 中段攻撃：立ちガードでのみガード可能
                is_guarding = bool(getattr(defender, "is_standing_guard", lambda: False)())
            elif attack_attribute == AttackAttribute.LOW:
                # 下段攻撃：しゃがみガードでのみガード可能
                is_guarding = bool(getattr(defender, "is_crouching_guard", lambda: False)())
            else:  # AttackAttribute.MID
                # 通常攻撃：立ち・しゃがみ両方でガード可能
                is_guarding = True
        
        # トレーニングモードの全ガード設定（攻撃属性に関わらず全てガード）
        if game_state == GameState.TRAINING and training_p2_all_guard and (defender is p2):
            is_guarding = True

        attacker_side = 1 if attacker is p1 else 2

        if is_guarding:
            return self._apply_guard(
                attacker=attacker,
                defender=defender,
                hit_point=hit_point,
                damage=damage,
                knockback_px=knockback_px,
                hitstop_frames=hitstop_frames,
                attacker_recoil_px=attacker_recoil_px,
                effects=effects,
                attacker_side=attacker_side,
            )
        else:
            return self._apply_damage(
                attacker=attacker,
                defender=defender,
                hit_point=hit_point,
                damage=damage,
                knockback_px=knockback_px,
                hitstop_frames=hitstop_frames,
                attacker_recoil_px=attacker_recoil_px,
                hit_pause=hit_pause,
                effects=effects,
                attacker_side=attacker_side,
            )

    def _apply_guard(
        self,
        *,
        attacker: Player,
        defender: Player,
        hit_point: tuple[int, int],
        damage: int,
        knockback_px: int,
        hitstop_frames: int,
        attacker_recoil_px: int,
        effects: list[Effect],
        attacker_side: int,
    ) -> dict[str, Any]:
        """ガード処理を実行。"""
        was_in_blockstun = bool(getattr(defender, "in_blockstun", False))
        info = attacker.get_last_move_frame_info()
        attacker_recovery = int(getattr(info, "recovery_frames", 0)) if info is not None else 0
        
        # frame_data.py からブロックスタンとチップダメージを取得
        attack_id = getattr(attacker, "_attack_id", None)
        frame_data_dict = getattr(attacker.character, "frame_data", None)
        frame_data = None
        if frame_data_dict and attack_id:
            frame_data = frame_data_dict.get(str(attack_id))
        
        if frame_data:
            defender_stun = int(getattr(frame_data, "blockstun_frames", 12))
            chip_ratio = float(getattr(frame_data, "chip_damage_ratio", 0.0))
        else:
            defender_stun = int(getattr(constants, "BLOCKSTUN_DEFAULT_FRAMES", 12))
            chip_ratio = float(getattr(constants, "GUARD_CHIP_DAMAGE_RATIO", 0.0))
        
        chip_damage = int(max(0, round(damage * chip_ratio)))

        defender.take_damage(chip_damage)

        gain_guard = int(getattr(constants, "POWER_GAIN_ON_GUARD", 20))
        attacker.add_power(gain_guard)

        base_guard_kb = int(getattr(constants, "GUARD_KNOCKBACK_PX_DEFAULT", knockback_px))
        guard_mul = float(getattr(constants, "GUARD_KNOCKBACK_MULTIPLIER", 1.35))
        guard_knockback = int(max(0, round(base_guard_kb * guard_mul)))

        # 壁際なら、押せない分は攻撃側が倍引っ込む。
        half_w = defender.rect.width / 2.0
        at_left_wall = defender.pos_x <= (half_w + 0.01)
        at_right_wall = defender.pos_x >= ((constants.STAGE_WIDTH - half_w) - 0.01)
        toward_left = attacker.facing < 0
        toward_right = attacker.facing > 0
        defender_blocked_by_wall = (toward_left and at_left_wall) or (toward_right and at_right_wall)

        if defender_blocked_by_wall:
            attacker.apply_knockback(dir_x=-attacker.facing, amount_px=guard_knockback * 2)
        else:
            defender.apply_knockback(dir_x=attacker.facing, amount_px=guard_knockback)

        # ガード硬直＋ガードモーション。
        crouch_guard = bool(getattr(defender, "crouching", False))
        defender.enter_blockstun(crouching=crouch_guard)

        if (not was_in_blockstun) and self.guard_se is not None:
            self.guard_se.play()

        if (not was_in_blockstun) and (self.guard_fx_img is not None):
            try:
                effects.append(
                    StaticImageBurstEffect(
                        image=self.guard_fx_img,
                        pos=hit_point,
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

        # セパレーション：攻撃側も少し後ろへ下がる。
        attacker.apply_knockback(dir_x=-attacker.facing, amount_px=attacker_recoil_px)
        # ガードではコンボ/ヒット登録は増やさない（多段ガードで無限にカウントされないようにする）。
        attacker.register_current_hit()

        extra_hitstop = int(getattr(constants, "HIT_EFFECT_EXTRA_HITSTOP_FRAMES", 4))
        hitstop_total = int(hitstop_frames) + max(0, extra_hitstop)

        attacker.hitstop_frames_left = max(attacker.hitstop_frames_left, hitstop_total)
        defender.hitstop_frames_left = max(defender.hitstop_frames_left, hitstop_total)

        return {
            "frame_meter_adv_value": int(defender_stun) - int(attacker_recovery),
            "frame_meter_adv_frames_left": int(constants.FPS * 3),
            "frame_meter_adv_attacker_side": attacker_side,
        }

    def _apply_damage(
        self,
        *,
        attacker: Player,
        defender: Player,
        hit_point: tuple[int, int],
        damage: int,
        knockback_px: int,
        hitstop_frames: int,
        attacker_recoil_px: int,
        hit_pause: int,
        effects: list[Effect],
        attacker_side: int,
    ) -> dict[str, Any]:
        """ダメージ処理を実行。"""
        # コンボ判定：相手がコンボ中（is_in_combo）かつ、攻撃側が同じならコンボ継続
        if bool(getattr(defender, "is_in_combo", False)) and int(getattr(defender, "_combo_attacker_side", 0)) == attacker_side:
            attacker.extend_combo_on_opponent()
        else:
            attacker.start_combo_on_opponent(opponent_side=(2 if attacker_side == 1 else 1))

        dmg_mul = float(getattr(constants, "get_damage_multiplier", lambda _c: 1.0)(attacker.get_combo_count()))
        scaled_damage = int(max(0, round(float(damage) * dmg_mul)))

        defender.take_damage(scaled_damage)
        if self.hit_se is not None:
            self.hit_se.play()

        info = attacker.get_last_move_frame_info()
        attacker_recovery = int(getattr(info, "recovery_frames", 0)) if info is not None else 0
        defender_stun = int(hit_pause)

        gain_hit = int(getattr(constants, "POWER_GAIN_ON_HIT", 50))
        attacker.add_power(gain_hit)

        half_w = defender.rect.width / 2.0
        at_left_wall = defender.pos_x <= (half_w + 0.01)
        at_right_wall = defender.pos_x >= ((constants.STAGE_WIDTH - half_w) - 0.01)
        toward_left = attacker.facing < 0
        toward_right = attacker.facing > 0
        defender_blocked_by_wall = (toward_left and at_left_wall) or (toward_right and at_right_wall)

        if defender_blocked_by_wall:
            attacker.apply_knockback(dir_x=-attacker.facing, amount_px=int(knockback_px) * 2)
        else:
            defender.apply_knockback(dir_x=attacker.facing, amount_px=knockback_px)

        defender.set_combo_victim_state(attacker_side=attacker_side, hitstun_frames=hit_pause)
        defender.enter_hitstun(frames=hit_pause)

        # セパレーション：攻撃側も少し後ろへ下がる。
        attacker.apply_knockback(dir_x=-attacker.facing, amount_px=attacker_recoil_px)
        attacker.mark_damage_dealt()

        attacker.add_combo_damage(scaled_damage)

        # ヒットキャンセルウィンドウを設定
        # コマンド技（波動拳、突進、真空波動拳）とIキー（P1_S）がヒットキャンセル可能
        attack_id = getattr(attacker, "_attack_id", None)
        is_command_move = attack_id in {"HADOKEN", "RUSH", "SHINKU_HADOKEN", "SHUNGOKUSATSU"}
        is_i_key = attack_id == "P1_S"
        
        if is_command_move:
            hit_cancel_frames = int(getattr(constants, "HIT_CANCEL_WINDOW_FRAMES", 8))
            attacker._hit_cancel_window_frames_left = max(attacker._hit_cancel_window_frames_left, hit_cancel_frames)
        elif is_i_key:
            # Iキーは全体フレーム分のキャンセル猶予を与える
            info = attacker.get_last_move_frame_info()
            if info is not None:
                # 全体フレーム = startup + active + recovery
                total_frames = int(getattr(info, "total_frames", 0))
                # 現在の経過フレーム数を取得
                elapsed = int(getattr(attacker, "_attack_elapsed_frames", 0))
                # 残りフレーム数をキャンセル猶予として設定
                remaining_frames = max(0, total_frames - elapsed)
                attacker._hit_cancel_window_frames_left = max(attacker._hit_cancel_window_frames_left, remaining_frames)
        
        # ダウン判定：特定の技（突進攻撃の根元ヒット）はダウンさせる
        should_knockdown = False
        if attack_id == "RUSH":
            # 突進攻撃は根元（発動直後）でヒットした場合のみダウンさせる
            should_knockdown = bool(getattr(attacker, "is_rush_early_hit", lambda: False)())
        else:
            # その他の技はフレームデータのcauses_knockdownフラグを参照
            frame_data_dict = getattr(attacker.character, "frame_data", None)
            if frame_data_dict and attack_id:
                frame_data = frame_data_dict.get(str(attack_id))
                if frame_data:
                    should_knockdown = bool(getattr(frame_data, "causes_knockdown", False))
        
        if should_knockdown:
            # ダウン状態にする（瞬獄殺と同じアニメーション）
            defender.enter_knockdown()

        # 衝突点に火花エフェクトを生成（画像がある場合）。
        if self.spark_frames:
            effects.append(Effect(frames=self.spark_frames, pos=hit_point, frames_per_image=2))

        if self.hit_fx_img is not None:
            try:
                effects.append(
                    StaticImageBurstEffect(
                        image=self.hit_fx_img,
                        pos=hit_point,
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
        hitstop_total = int(hitstop_frames) + max(0, extra_hitstop)

        attacker.hitstop_frames_left = max(attacker.hitstop_frames_left, hitstop_total)
        defender.hitstop_frames_left = max(defender.hitstop_frames_left, hitstop_total)

        return {
            "frame_meter_adv_value": int(defender_stun) - int(attacker_recovery),
            "frame_meter_adv_frames_left": int(constants.FPS * 3),
            "frame_meter_adv_attacker_side": attacker_side,
        }
