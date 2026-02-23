from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import pygame

from src.characters.definition import CharacterDefinition
from src.utils import constants
from src.utils.paths import resource_path


@dataclass
class PlayerInput:
    # Player に渡す入力の「意図（intent）」をまとめたデータ。
    # - move_x: 左(-1) / 停止(0) / 右(+1)
    # - jump_pressed: 押した瞬間だけ True（ジャンプ開始トリガ）
    # - crouch: 押している間 True（しゃがみ保持）
    # - attack_id: 押した瞬間の攻撃ID（攻撃していないなら None）
    move_x: int
    jump_pressed: bool
    crouch: bool
    # attack_id は「今回のフレームで押された攻撃」を表す（押されていなければ None）。
    attack_id: str | None


@dataclass(frozen=True)
class MoveFrameInfo:
    attack_id: str
    total_frames: int
    startup_frames: int
    active_frames: int
    recovery_frames: int


class Player:
    def __init__(
        self,
        *,
        x: int,
        color: tuple[int, int, int],
        character: CharacterDefinition,
    ) -> None:
        self.color = color
        self.character = character

        # pos_x / pos_y は「キャラクターの足元（接地中点）」を表す。
        # AIR のオフセット適用や、描画の基準点として使う。
        self.pos_x: float = float(x + (constants.PLAYER_WIDTH // 2))
        self.pos_y: float = float(constants.GROUND_Y)

        # rect はプレイヤー本体の当たり判定（Hurtbox）兼、描画矩形として使う。
        # 位置は「左上座標」基準（pygame.Rect の仕様）。
        self.rect = pygame.Rect(0, 0, constants.PLAYER_WIDTH, constants.PLAYER_HEIGHT)
        self.rect.midbottom = (int(self.pos_x), int(self.pos_y))

        # 速度は float で管理し、rect へ反映する時に int 化する（簡易物理）。
        self.vel_x: float = 0.0
        self.vel_y: float = 0.0

        # ノックバック速度（滑り）。衝突時に加算し、毎フレーム減衰させる。
        self.knockback_vx: float = 0.0

        # 地上判定（ジャンプ/重力の適用に使用）。
        self.on_ground: bool = True
        # しゃがみ状態。Hitbox の出る高さを変えるために使う。
        self.crouching: bool = False

        # 向き（右:+1 / 左:-1）。main 側で「相手の位置」を見て更新する。
        self.facing: int = 1

        # 攻撃は「一定フレームだけ攻撃状態」にする簡易タイマー。
        self._attack_frames_left: int = 0
        # 将来のダメージ判定用（多段ヒット防止）。Phase 1 ではまだ未使用。
        self._attack_has_hit: bool = False

        self._hit_id_counter: int = 0
        self._current_hit_id: int = 0
        self._registered_hit_ids: set[int] = set()
        self._last_clsn1_signature: tuple[tuple[int, int, int, int], ...] | None = None
        self.combo_count: int = 0

        # 現在の攻撃ID（ATTACK_SPECS のキー）。攻撃していない時は None。
        self._attack_id: str | None = None

        # デバッグ用：最後に入力された攻撃のフレーム情報（全体/発生/硬直）。
        self._last_move_frame_info: MoveFrameInfo | None = None

        # HP
        self.max_hp: int = constants.PLAYER_MAX_HP
        self.hp: int = constants.PLAYER_MAX_HP

        # ヒットストップ（フレーム）。0 の時は通常。
        self.hitstop_frames_left: int = 0

        # ヒット硬直（操作不能）。0 の時は通常。
        self.hitstun_frames_left: int = 0

        self.hitstun_timer: int = 0

        self.is_in_combo: bool = False

        self._combo_attacker_side: int | None = None
        self._combo_end_side_pending: int | None = None

        self.combo_display_frames_left: int = 0
        self.combo_display_count: int = 0

        self.combo_damage_total: int = 0
        self.combo_damage_display: int = 0

        self._input_frame_counter: int = 0
        # 入力履歴（コマンド検知用）。直近10〜15F程度の「方向/ボタン」履歴を保持する。
        # entry の例:
        # - "DIR:D" / "DIR:DF" / "DIR:F" / "DIR:N"
        # - "BTN:P" / "BTN:K"
        self.input_buffer: list[tuple[int, str]] = []
        # 先行入力（硬直明けに自動で技を出す）用の攻撃バッファ。
        self.attack_buffer: list[tuple[int, str]] = []

        self.hadoken_flash_frames_left: int = 0

        self._hadoken_action_id: int | None = None
        self._hadoken_spawned: bool = False
        self._hadoken_spawn_pending: bool = False
        self._hadoken_spawn_delay_frames_left: int = 0

        self.power_gauge: int = 0

        self._shinku_action_id: int | None = None
        self._shinku_spawned: bool = False
        self._shinku_spawn_pending: bool = False
        self._shinku_lockout_frames_left: int = 0

        self._last_punch_pressed_frame: int | None = None
        self._last_kick_pressed_frame: int | None = None
        self._punch_consumed_for_hadoken_frame: int | None = None
        self._punch_consumed_for_shinku_frame: int | None = None

        self._rush_frames_left: int = 0
        self._rush_startup_frames_left: int = 0
        self._rush_effect_pending: bool = False
        self._rush_effect_pos: tuple[int, int] | None = None
        self._rush_recovery_frames_left: int = 0
        self._rush_recovery_total_frames: int = 0
        self._rush_has_hit: bool = False

        # ガード硬直（操作不能）。0 の時は通常。
        self.blockstun_frames_left: int = 0

        # ガード入力（後ろ入力）を保持しているか。
        self.holding_back: bool = False

        # ガード入力バッファ（後ろ入力を数フレーム保持する）。
        self._guard_buffer_frames_left: int = 0

        # --- Animation (MUGEN AIR + extracted PNGs) ---
        # action_id -> action_dict (from ACTIONS)
        self._air_actions: dict[int, dict[str, Any]] = {}
        # (group, index) -> loaded Surface
        self._sprites: dict[tuple[int, int], pygame.Surface] = {}
        # (group, index) -> (crop_left, crop_top) for trimmed images
        self._sprite_crop_offsets: dict[tuple[int, int], tuple[int, int]] = {}
        self._current_action_id: int | None = None
        self._frame_index: int = 0
        self._frame_time_left: int = 0

        # デバッグ用：現在のアクション開始からの経過フレーム（ヒットストップ除外）。
        self._action_frame_counter: int = 0

        # アニメーション制御用。
        # - oneshot: 攻撃など「最後まで再生したらIdleへ戻る」
        # - loop: Idle/Walkなど「ループして再生し続ける」
        self._action_mode: str = "loop"
        self._action_finished: bool = False

        self._knocked_down: bool = False

    @property
    def attacking(self) -> bool:
        # 攻撃タイマーが残っている間だけ攻撃中。
        return self._attack_frames_left > 0

    @property
    def in_hitstun(self) -> bool:
        return self.hitstun_frames_left > 0

    @property
    def in_blockstun(self) -> bool:
        return self.blockstun_frames_left > 0

    def can_guard_now(self) -> bool:
        # True blockstring: blockstun 中は次の攻撃も自動でガード継続できる。
        if self.in_blockstun:
            return True

        # ヒット硬直中は基本ガード不可だが、終了直前だけ先行入力を受け付ける。
        if self.in_hitstun:
            early = int(getattr(constants, "HITSTUN_GUARD_EARLY_ACCEPT_FRAMES", 2))
            return self.hitstun_frames_left <= max(0, early)

        return True

    def is_guarding_intent(self) -> bool:
        # 「今ガードするつもりか？」を返す。
        # - 後ろ入力バッファが残っていれば True
        if self.in_blockstun:
            return True
        return self._guard_buffer_frames_left > 0

    def enter_hitstun(self, *, frames: int | None = None) -> None:
        # HIT（のけぞり）状態へ遷移し、AIR Action 5000 を oneshot 再生する。
        if frames is None:
            frames = int(getattr(constants, "HITSTUN_DEFAULT_FRAMES", 20))
        self.hitstun_frames_left = max(0, int(frames))
        self.hitstun_timer = max(0, int(frames))

        # 攻撃中の相殺など最小限の整合性として、攻撃状態は解除する。
        self._attack_frames_left = 0
        self._attack_has_hit = False
        self._attack_id = None

        # Action 5000（地上ダメージ）へ。
        self._set_action(self._best_action_id([5000]), mode="oneshot")

    def enter_knockdown(self) -> None:
        # KO 用：ダウンモーションへ。
        # 5040番台が無ければ 5000 などへフォールバック。
        self.hitstop_frames_left = 0
        self.hitstun_frames_left = 0
        self.hitstun_timer = 0
        self.blockstun_frames_left = 0

        self._attack_frames_left = 0
        self._attack_has_hit = False
        self._attack_id = None
        self.attack_buffer.clear()

        self.vel_x = 0.0
        self.vel_y = 0.0
        self.knockback_vx = 0.0
        self.on_ground = True
        self.crouching = False

        self._knocked_down = True

        action_id = self._best_action_id([5041, 5040, 5042, 5043, 5044, 5000])
        self._set_action(int(action_id), mode="oneshot")

    def reset_round_state(self) -> None:
        # Round start reset: clear transient state that should not carry over.
        self.hitstop_frames_left = 0
        self.hitstun_frames_left = 0
        self.hitstun_timer = 0
        self.blockstun_frames_left = 0

        self._attack_frames_left = 0
        self._attack_has_hit = False
        self._attack_id = None
        self._registered_hit_ids.clear()
        self._last_clsn1_signature = None
        self._current_hit_id = 0

        self.is_in_combo = False
        self._combo_attacker_side = None
        self._combo_end_side_pending = None
        self.combo_display_frames_left = 0
        self.combo_display_count = 0
        self.combo_damage_total = 0
        self.combo_damage_display = 0

        self.knockback_vx = 0.0

        self.input_buffer.clear()
        self.attack_buffer.clear()
        self._last_punch_pressed_frame = None
        self._last_kick_pressed_frame = None
        self._punch_consumed_for_hadoken_frame = None
        self._punch_consumed_for_shinku_frame = None
        self._kick_consumed_for_rush_frame = -1

        self._hadoken_action_id = None
        self._hadoken_spawned = False
        self._hadoken_spawn_pending = False
        self._hadoken_spawn_delay_frames_left = 0
        self.hadoken_flash_frames_left = 0

        self._shinku_action_id = None
        self._shinku_spawned = False
        self._shinku_spawn_pending = False
        self._shinku_lockout_frames_left = 0

        self._rush_frames_left = 0
        self._rush_startup_frames_left = 0
        self._rush_recovery_frames_left = 0
        self._rush_recovery_total_frames = 0
        self._rush_has_hit = False
        self._rush_effect_pending = False
        self._rush_effect_pos = None

        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = True
        self.crouching = False

        self._action_finished = False
        self._action_mode = "loop"
        self._knocked_down = False
        if self._air_actions:
            self._set_action(self._best_action_id([0]), mode="loop")

    def enter_blockstun(self, *, frames: int | None = None, crouching: bool = False) -> None:
        if frames is None:
            frames = int(getattr(constants, "BLOCKSTUN_DEFAULT_FRAMES", 12))
        self.blockstun_frames_left = max(self.blockstun_frames_left, int(frames))

        if self.is_in_combo:
            self._combo_end_side_pending = self._combo_attacker_side
            self.is_in_combo = False
            self._combo_attacker_side = None

        # ガード中は攻撃状態を解除する。
        self._attack_frames_left = 0
        self._attack_has_hit = False
        self._attack_id = None

        if crouching:
            self._set_action(self._best_action_id([150]), mode="oneshot")
        else:
            # 120: guard start / 130: guard hold
            self._set_action(self._best_action_id([120, 130]), mode="oneshot")

    def start_attack(self, attack_id: str) -> None:
        # すでに攻撃中なら再発動しない（連打で伸びないようにする）。
        if self.attacking:
            return

        # のけぞり中は攻撃できない。
        if self.in_hitstun:
            return

        if self.in_blockstun:
            return

        self._registered_hit_ids.clear()
        self._last_clsn1_signature = None
        self._current_hit_id = 0

        info = self._infer_move_frame_info(attack_id)
        if info is None:
            self._attack_id = None
            self._attack_frames_left = max(1, int(constants.ATTACK_DURATION_SECONDS * constants.FPS))
        else:
            self._attack_id = attack_id
            self._attack_frames_left = max(1, int(info.total_frames))
        self._attack_has_hit = False

        # 攻撃開始時に、AIRの攻撃アクションへ切り替える（存在する場合）。
        action_id = self._attack_to_action_id(attack_id)
        if action_id is not None:
            self._set_action(action_id, mode="oneshot")

    def apply_input(self, inp: PlayerInput) -> None:
        self._input_frame_counter += 1

        self._push_direction_history(move_x=inp.move_x, crouch=inp.crouch)

        if inp.attack_id is not None:
            # 突進（RUSH）は「方向コマンド + キック」で成立するため、
            # 通常キック攻撃を start_attack する前に判定して優先的に発動する。
            atk = str(inp.attack_id)
            if atk in set(getattr(self.character, "rush_attack_ids", set())):
                self._push_button_history(atk)
                if (
                    (not self.is_rushing())
                    and int(self._rush_recovery_frames_left) <= 0
                    and self.check_command_rush()
                    and self._can_start_buffered_attack_now()
                ):
                    self.attack_buffer.clear()
                    self.start_rush()
                    return

            # 先行入力：今すぐ出せるなら即発動、出せないならバッファへ。
            if self._can_start_buffered_attack_now():
                self.attack_buffer.clear()
                info = self._infer_move_frame_info(inp.attack_id)
                if info is not None:
                    self._last_move_frame_info = info
                self.start_attack(inp.attack_id)
            else:
                self._push_attack_buffer(inp.attack_id)

            self._push_button_history(inp.attack_id)

        # 「後ろ入力」を保持しているか（相手側は main が facing を更新済みであることが前提）。
        # move_x は -1/0/+1 なので、自分の向きと逆が「後ろ」。
        self.holding_back = (inp.move_x != 0) and ((inp.move_x * self.facing) < 0)
        if self.holding_back:
            self._guard_buffer_frames_left = int(getattr(constants, "GUARD_BUFFER_FRAMES", 2))

        if self.in_hitstun:
            self.vel_x = 0.0
            return

        if self.in_blockstun:
            self.vel_x = 0.0
            return

        # 攻撃中（全体フレーム中）は移動できない。
        # これにより、前入力で押し込みながら連打しても永久に繋がりにくくする。
        if self.attacking:
            self.vel_x = 0.0
        

        # しゃがみは地上にいる間だけ成立。
        self.crouching = inp.crouch and self.on_ground

        # 攻撃モーション中は、基本的に移動入力を無効化する。
        if self.attacking or (self._action_mode == "oneshot" and self._current_action_id is not None):
            self.vel_x = 0.0
            if inp.jump_pressed:
                pass
        else:
            # 左右移動は入力をそのまま速度に変換する（慣性なし）。
            if self.crouching and self.on_ground:
                self.vel_x = 0.0
            else:
                self.vel_x = float(inp.move_x) * constants.WALK_SPEED

        # ジャンプは押した瞬間だけ成立。
        if inp.jump_pressed and self.on_ground:
            self.vel_y = constants.JUMP_VELOCITY
            self.on_ground = False

        self._try_consume_buffered_attack()

    def process_special_inputs(
        self,
        *,
        attack_id: str | None,
        early_frames: int,
        super_cost: int,
    ) -> dict[str, Any]:
        now = int(self.get_input_frame_counter())
        early = max(0, int(early_frames))

        did_rush = False
        did_hadoken = False
        did_shinku = False
        clear_attack_id = False

        tokens = [t for (_f, t) in self.input_buffer]

        def _match_sequence(seq: list[str]) -> bool:
            # Match as an ordered subsequence in the buffer tail.
            # This keeps the command system lenient (allows extra tokens between inputs),
            # similar to the previous dedicated command checks.
            if not seq:
                return False

            i = len(tokens) - 1
            for want in reversed(seq):
                found = False
                for j in range(i, -1, -1):
                    if tokens[j] == want:
                        i = j - 1
                        found = True
                        break
                if not found:
                    return False
            return True

        def _any_match(seqs: list[list[str]]) -> bool:
            for s in seqs:
                if _match_sequence(s):
                    return True
            return False

        def _consume_early(key: str) -> int | None:
            if key == "kick_rush":
                return self.consume_recent_kick_for_rush()
            if key == "punch_hadoken":
                return self.consume_recent_punch_for_hadoken()
            if key == "punch_shinku":
                return self.consume_recent_punch_for_shinku()
            return None

        def _can_trigger_special(spec_key: str) -> bool:
            if spec_key == "RUSH":
                return (not self.is_rushing()) and int(self._rush_recovery_frames_left) <= 0
            if spec_key == "SHINKU_HADOKEN":
                if int(getattr(self, "_shinku_lockout_frames_left", 0)) > 0:
                    return False
                # Prevent double-trigger while the super's oneshot action is still running.
                if (
                    self._action_mode == "oneshot"
                    and (self._current_action_id is not None)
                    and (not bool(getattr(self, "_action_finished", False)))
                ):
                    if self._shinku_action_id is not None and int(self._current_action_id) == int(self._shinku_action_id):
                        return False
                if getattr(self, "_shinku_spawned", False) and (
                    self._shinku_action_id is not None
                    and int(self._current_action_id or -1) == int(self._shinku_action_id)
                ):
                    return False
            if spec_key == "HADOKEN":
                # If Shinku command was just used, 236236 can remain in the buffer and be re-read as 236.
                # Suppress hadoken while shinku is in lockout to avoid unintended hadoken after a shinku input.
                if int(getattr(self, "_shinku_lockout_frames_left", 0)) > 0:
                    return False
            return True

        def _trigger(spec_key: str) -> None:
            nonlocal did_rush, did_hadoken, did_shinku
            if spec_key == "RUSH":
                self.start_rush()
                did_rush = True
                return
            if spec_key == "HADOKEN":
                self.start_hadoken()
                did_hadoken = True
                return
            if spec_key == "SHINKU_HADOKEN":
                self.start_shinku_hadoken()
                did_shinku = True
                return

        specials = list(getattr(self.character, "specials", []) or [])

        for sp in specials:
            if not _can_trigger_special(str(getattr(sp, "key", ""))):
                continue

            sp_key = str(getattr(sp, "key", ""))
            seqs = list(getattr(sp, "sequences", []) or [])
            immediate_ids = set(getattr(sp, "immediate_attack_ids", set()) or set())
            consume_key = str(getattr(sp, "early_consume_key", ""))
            requires_power = bool(getattr(sp, "requires_power", False))

            # 1) Immediate trigger: button pressed this frame
            if attack_id is not None and str(attack_id) in immediate_ids:
                if _any_match(seqs):
                    if requires_power and (not self.spend_power(int(super_cost))):
                        continue
                    _trigger(sp_key)
                    if sp_key == "RUSH":
                        clear_attack_id = True
                    return {
                        "did_rush": did_rush,
                        "did_hadoken": did_hadoken,
                        "did_shinku": did_shinku,
                        "clear_attack_id": clear_attack_id,
                    }

            # 2) Early input: button within early window
            if _any_match(seqs):
                f = _consume_early(consume_key)
                if f is not None and (now - int(f)) <= early:
                    if requires_power and (not self.spend_power(int(super_cost))):
                        continue
                    _trigger(sp_key)
                    if sp_key == "RUSH":
                        clear_attack_id = True
                    return {
                        "did_rush": did_rush,
                        "did_hadoken": did_hadoken,
                        "did_shinku": did_shinku,
                        "clear_attack_id": clear_attack_id,
                    }

        return {
            "did_rush": did_rush,
            "did_hadoken": did_hadoken,
            "did_shinku": did_shinku,
            "clear_attack_id": clear_attack_id,
        }

    def _push_attack_buffer(self, attack_id: str) -> None:
        buf_frames = int(getattr(constants, "INPUT_BUFFER_FRAMES", 10))
        now = int(self._input_frame_counter)
        self.attack_buffer.append((now, str(attack_id)))
        cutoff = now - max(1, buf_frames)
        self.attack_buffer = [(f, a) for (f, a) in self.attack_buffer if f > cutoff]

    def _try_consume_buffered_attack(self) -> None:
        if not self.attack_buffer:
            return
        if not self._can_start_buffered_attack_now():
            return

        _f, attack_id = self.attack_buffer[-1]
        self.attack_buffer.clear()
        info = self._infer_move_frame_info(attack_id)
        if info is not None:
            self._last_move_frame_info = info
        self.start_attack(attack_id)

    def _push_direction_history(self, *, move_x: int, crouch: bool) -> None:
        # 相対方向（自分の向き基準）で履歴化する。
        # 236は「下, 下前, 前」なので forward=+1 になるよう facing を掛ける。
        rel_x = int(move_x) * int(self.facing)
        down = bool(crouch and self.on_ground)
        if down and rel_x > 0:
            token = "DIR:DF"
        elif down and rel_x < 0:
            token = "DIR:DB"
        elif down:
            token = "DIR:D"
        elif rel_x > 0:
            token = "DIR:F"
        elif rel_x < 0:
            token = "DIR:B"
        else:
            token = "DIR:N"

        now = int(self._input_frame_counter)
        if self.input_buffer and self.input_buffer[-1][1] == token:
            return
        self._push_command_token(token)

    def _push_button_history(self, attack_id: str) -> None:
        atk = str(attack_id)
        is_punch = atk in set(getattr(self.character, "punch_attack_ids", set()))
        is_kick = atk in set(getattr(self.character, "kick_attack_ids", set()))
        if is_punch:
            self._push_command_token("BTN:P")
            self._last_punch_pressed_frame = int(self._input_frame_counter)
        elif is_kick:
            self._push_command_token("BTN:K")
            self._last_kick_pressed_frame = int(self._input_frame_counter)

    def get_input_frame_counter(self) -> int:
        return int(self._input_frame_counter)

    def consume_recent_punch_for_hadoken(self) -> int | None:
        f = self._last_punch_pressed_frame
        if f is None:
            return None
        if self._punch_consumed_for_shinku_frame == f:
            return None
        if self._punch_consumed_for_hadoken_frame == f:
            return None
        self._punch_consumed_for_hadoken_frame = f
        return int(f)

    def consume_recent_punch_for_shinku(self) -> int | None:
        f = self._last_punch_pressed_frame
        if f is None:
            return None
        if self._punch_consumed_for_shinku_frame == f:
            return None
        self._punch_consumed_for_shinku_frame = f
        return int(f)

    def consume_recent_kick_for_rush(self) -> int | None:
        f = self._last_kick_pressed_frame
        if f is None:
            return None
        if int(getattr(self, "_kick_consumed_for_rush_frame", -1)) == int(f):
            return None
        self._kick_consumed_for_rush_frame = int(f)
        return int(f)

    def check_command_rush(self) -> bool:
        # 簡易：下後ろ（DB）→ キック で成立。
        # レベル緩和：DB が無ければ、D→B の順でもOK。
        if not self.input_buffer:
            return False
        tokens = [t for (_f, t) in self.input_buffer]
        frames = [int(f) for (f, _t) in self.input_buffer]
        if "BTN:K" not in tokens:
            return False

        i_btn = None
        for i in range(len(tokens) - 1, -1, -1):
            if tokens[i] == "BTN:K":
                i_btn = i
                break
        if i_btn is None:
            return False

        def _find_prev(start_i: int, wants: set[str]) -> int | None:
            for j in range(start_i, -1, -1):
                if tokens[j] in wants:
                    return j
            return None

        i_db = _find_prev(i_btn - 1, {"DIR:DB"})
        if i_db is None:
            i_b = _find_prev(i_btn - 1, {"DIR:B"})
            if i_b is None:
                return False
            i_d = _find_prev(i_b - 1, {"DIR:D", "DIR:DB"})
            if i_d is None:
                return False
            i_db = i_d

        win = int(getattr(constants, "INPUT_BUFFER_FRAMES", 25))
        earliest = int(frames[i_db])
        latest = int(frames[i_btn])
        return (latest - earliest) <= max(1, win)

    @staticmethod
    def _find_236_start(tokens: list[str], *, start: int) -> int | None:
        # 236: D -> (DF optional) -> F
        def _find_prev(start_i: int, wants: set[str]) -> int | None:
            for j in range(start_i, -1, -1):
                if tokens[j] in wants:
                    return j
            return None

        i_f = _find_prev(start, {"DIR:F"})
        if i_f is None:
            return None
        i_mid = _find_prev(i_f - 1, {"DIR:DF", "DIR:D"})
        if i_mid is None:
            return None
        if tokens[i_mid] == "DIR:DF":
            i_d = _find_prev(i_mid - 1, {"DIR:D"})
            return i_d
        return i_mid

    def _push_command_token(self, token: str) -> None:
        buf_frames = int(getattr(constants, "INPUT_BUFFER_FRAMES", 10))
        now = int(self._input_frame_counter)
        self.input_buffer.append((now, str(token)))
        cutoff = now - max(1, buf_frames)
        self.input_buffer = [(f, t) for (f, t) in self.input_buffer if f > cutoff]

    def check_command_hadoken(self) -> bool:
        # 236 + Punch (相対方向: D -> DF -> F) + BTN:P
        if not self.input_buffer:
            return False

        tokens = [t for (_f, t) in self.input_buffer]
        if "BTN:P" not in tokens:
            return False

        # 最新の BTN:P を起点に遡って成立判定する。
        i_btn = None
        for i in range(len(tokens) - 1, -1, -1):
            if tokens[i] == "BTN:P":
                i_btn = i
                break
        if i_btn is None:
            return False

        def _find_prev(start: int, want: str) -> int | None:
            for j in range(start, -1, -1):
                if tokens[j] == want:
                    return j
            return None

        i_d = self._find_236_start(tokens, start=i_btn)
        return i_d is not None

    def check_command_shinku_hadoken(self) -> bool:
        if not self.input_buffer:
            return False

        tokens = [t for (_f, t) in self.input_buffer]
        frames = [int(f) for (f, _t) in self.input_buffer]
        if "BTN:P" not in tokens:
            return False

        i_btn = None
        for i in range(len(tokens) - 1, -1, -1):
            if tokens[i] == "BTN:P":
                i_btn = i
                break
        if i_btn is None:
            return False

        def _find_prev(start: int, want: str) -> int | None:
            for j in range(start, -1, -1):
                if tokens[j] == want:
                    return j
            return None

        i_d2 = self._find_236_start(tokens, start=i_btn)
        if i_d2 is None:
            return False
        i_d1 = self._find_236_start(tokens, start=i_d2 - 1)
        if i_d1 is None:
            return False

        win = int(getattr(constants, "INPUT_BUFFER_FRAMES", 25))
        earliest = int(frames[i_d1])
        latest = int(frames[i_btn])
        return (latest - earliest) <= max(1, win)

    def start_hadoken(self) -> None:
        # HADOKEN専用アクションへ（存在しなければ現状維持）。
        action_id = self._best_action_id(list(getattr(self.character, "hadoken_action_candidates", [6040, 3000, 3050])))
        self._hadoken_action_id = int(action_id) if action_id in self._air_actions else None
        if self._hadoken_action_id is not None:
            self._set_action(self._hadoken_action_id, mode="oneshot")

        self.attack_buffer.clear()

        # 波動拳中は本体の攻撃判定（clsn1）を使わない。
        self._attack_frames_left = 0
        self._attack_has_hit = False
        self._attack_id = None

        self._hadoken_spawned = False
        self._hadoken_spawn_pending = False
        self._hadoken_spawn_delay_frames_left = 0
        self.hadoken_flash_frames_left = max(self.hadoken_flash_frames_left, int(0.75 * constants.FPS))

        self.add_power(int(getattr(constants, "POWER_GAIN_ON_SPECIAL_USE", 10)))

        # デバッグ表示用：波動拳のフレーム情報（全体/発生/硬直）。
        try:
            a = self._air_actions.get(int(self._hadoken_action_id or 0))
            frames = [] if not a else a.get("frames", [])
            if isinstance(frames, list) and frames:
                times = [max(0, int(fr.get("time", 0))) for fr in frames if isinstance(fr, dict)]
                total = int(sum(times))

                # 6040-1..3 の3枚モーション想定。
                base_before_last = int(sum(times[:2])) if len(times) >= 2 else 0
                delay = int(getattr(constants, "HADOKEN_SPAWN_DELAY_FRAMES", 20))
                startup = max(0, base_before_last + delay)
                active = 1
                recovery = max(0, total - startup - active)
                self._last_move_frame_info = MoveFrameInfo(
                    attack_id="HADOKEN",
                    total_frames=max(1, int(startup + active + recovery)),
                    startup_frames=int(startup),
                    active_frames=int(active),
                    recovery_frames=int(recovery),
                )
        except Exception:
            pass

    def start_rush(self) -> None:
        if self.is_rushing() or int(self._rush_recovery_frames_left) > 0:
            return
        if self.attacking:
            return
        if self.in_hitstun or self.in_blockstun:
            return

        # 突進開始：短い初期モーション（6520-1/2）→ 突進中は6520-2を固定表示。
        rush_action = int(getattr(self.character, "rush_action_id", 6520))
        if rush_action in self._air_actions:
            self._set_action(rush_action, mode="oneshot")
        else:
            # アクションが無い場合でも、描画はスプライト固定で行うため続行。
            self._current_action_id = None

        self.attack_buffer.clear()
        self._attack_frames_left = 0
        self._attack_has_hit = False
        self._attack_id = "RUSH"
        self._rush_has_hit = False

        self._rush_startup_frames_left = int(getattr(constants, "RUSH_STARTUP_FRAMES", 6))
        self._rush_frames_left = int(getattr(constants, "RUSH_FRAMES", 18))

        self._rush_effect_pending = True
        self._rush_effect_pos = (int(self.rect.centerx), int(self.rect.bottom) - 12)

    def is_rushing(self) -> bool:
        return int(self._rush_frames_left) > 0 or int(self._rush_startup_frames_left) > 0

    def is_rush_attack_active(self) -> bool:
        return int(self._rush_frames_left) > 0

    def _get_rush_hitbox(self) -> pygame.Rect:
        # 突進中は、表示している 6520-2 のスプライトに合わせて当たり判定を作る。
        key = tuple(getattr(self.character, "rush_sprite_key", (6520, 2)))
        img = self._sprites.get((int(key[0]), int(key[1])))
        if img is None:
            return self._fallback_attack_hitbox(self.rect, facing=self.facing, crouching=False, attack_id="RUSH")

        w = max(18, int(round(img.get_width() * 0.38)))
        h = max(18, int(round(img.get_height() * 0.24)))

        # スプライトの前方に寄せて、足元基準で配置。
        cx = int(self.rect.centerx + (self.facing * int(round(img.get_width() * 0.25))))
        by = int(self.rect.bottom - int(round(img.get_height() * 0.10)))
        r = pygame.Rect(0, 0, int(w), int(h))
        r.midbottom = (int(cx), int(by))
        return r

    def consume_rush_effect_spawn(self) -> tuple[int, int] | None:
        if not self._rush_effect_pending:
            return None
        self._rush_effect_pending = False
        return self._rush_effect_pos

    def start_shinku_hadoken(self) -> None:
        action_id = self._best_action_id(list(getattr(self.character, "shinku_action_candidates", [int(getattr(constants, "SHINKU_HADOKEN_ACTION_ID", 8000))])))
        self._shinku_action_id = int(action_id) if action_id in self._air_actions else None
        if self._shinku_action_id is not None:
            self._set_action(self._shinku_action_id, mode="oneshot")

        self.attack_buffer.clear()

        self._attack_frames_left = 0
        self._attack_has_hit = False
        self._attack_id = None

        self._shinku_spawned = False
        self._shinku_spawn_pending = False

        self.add_power(int(getattr(constants, "POWER_GAIN_ON_SPECIAL_USE", 10)))

        try:
            a = self._air_actions.get(int(self._shinku_action_id or 0))
            frames = [] if not a else a.get("frames", [])
            if isinstance(frames, list) and frames:
                times = [max(0, int(fr.get("time", 0))) for fr in frames if isinstance(fr, dict)]
                total = int(sum(times))
                spawn_i = int(getattr(constants, "SHINKU_HADOKEN_SPAWN_FRAME_INDEX", 3))
                startup = int(sum(times[: max(0, spawn_i)]))
                active = 1
                recovery = max(0, total - startup - active)
                self._last_move_frame_info = MoveFrameInfo(
                    attack_id="SHINKU_HADOKEN",
                    total_frames=max(1, int(startup + active + recovery)),
                    startup_frames=int(startup),
                    active_frames=int(active),
                    recovery_frames=int(recovery),
                )
        except Exception:
            pass

        # Lockout to avoid retriggering while command remains in the input buffer.
        lockout = int(constants.FPS * 1.0)
        try:
            info = getattr(self, "_last_move_frame_info", None)
            if info is not None and str(getattr(info, "attack_id", "")) == "SHINKU_HADOKEN":
                lockout = int(max(1, getattr(info, "total_frames", lockout)))
        except Exception:
            pass
        self._shinku_lockout_frames_left = max(int(self._shinku_lockout_frames_left), int(lockout))

    def consume_hadoken_spawn(self) -> bool:
        if not self._hadoken_spawn_pending:
            return False
        self._hadoken_spawn_pending = False
        return True

    def consume_shinku_spawn(self) -> bool:
        if not self._shinku_spawn_pending:
            return False
        self._shinku_spawn_pending = False
        return True

    def can_spend_power(self, cost: int) -> bool:
        return int(self.power_gauge) >= max(0, int(cost))

    def spend_power(self, cost: int) -> bool:
        c = max(0, int(cost))
        if not self.can_spend_power(c):
            return False
        self.power_gauge = max(0, int(self.power_gauge) - c)
        return True

    def add_power(self, amount: int) -> None:
        mx = int(getattr(constants, "POWER_GAUGE_MAX", 1000))
        self.power_gauge = max(0, min(mx, int(self.power_gauge) + max(0, int(amount))))

    def _can_start_buffered_attack_now(self) -> bool:
        if self.attacking:
            return False
        if self.in_hitstun or self.in_blockstun:
            return False
        # oneshot action is still running (recovery)
        if self._action_mode == "oneshot" and (self._current_action_id is not None) and (not self._action_finished):
            return False
        return True

    def get_last_move_frame_info(self) -> MoveFrameInfo | None:
        return self._last_move_frame_info

    def get_current_action_id(self) -> int | None:
        return self._current_action_id

    def get_action_frame_counter(self) -> int:
        return int(self._action_frame_counter)

    def set_mugen_animation(self, *, actions: list[dict[str, Any]], sprites_root: Path) -> None:
        # AIR の ACTIONS を取り込み、PNG を (group,index) で引けるようにロードする。
        # まずは Action 0 のループ再生を最優先とする。
        self._air_actions = {int(a.get("action")): a for a in actions if "action" in a}
        resolved_root = sprites_root
        try:
            if not resolved_root.is_absolute():
                resolved_root = resource_path(resolved_root)
        except Exception:
            resolved_root = resource_path(sprites_root)

        sprites, crop_offsets = self._load_sprites_from_organized(resolved_root)
        self._sprites = sprites
        self._sprite_crop_offsets = crop_offsets
        self._set_action(self._best_action_id([0]), mode="loop")

    def _set_action(self, action_id: int, *, mode: str) -> None:
        if action_id not in self._air_actions:
            # AIR に Action 0 が無い等のケースでも、何か描画できるアクションへフォールバックする。
            if self._air_actions:
                fallback = self._best_action_id([0])
                action_id = int(fallback)
            else:
                self._current_action_id = None
                self._frame_index = 0
                self._frame_time_left = 0
                self._action_mode = "loop"
                self._action_finished = False
                return

        if self._current_action_id == action_id and self._action_mode == mode:
            return

        self._current_action_id = action_id
        self._frame_index = 0
        self._frame_time_left = 0
        self._action_mode = mode
        self._action_finished = False
        self._action_frame_counter = 0

        frames = self._air_actions[action_id].get("frames", [])
        if frames:
            t = int(frames[0].get("time", 0))
            if int(action_id) in {5000, 5040, 5041, 5042, 5043, 5044}:
                t = 10
            self._frame_time_left = max(1, t)

    @staticmethod
    def _load_sprites_from_organized(
        sprites_root: Path,
    ) -> tuple[dict[tuple[int, int], pygame.Surface], dict[tuple[int, int], tuple[int, int]]]:
        # organized/ 以下を再帰的に走査して、ファイル名から group/index を抽出する。
        # 例：Nova pasta_0-0.png / Nova pasta_0_0.png
        sprites: dict[tuple[int, int], pygame.Surface] = {}
        crop_offsets: dict[tuple[int, int], tuple[int, int]] = {}

        if not sprites_root.exists():
            return sprites, crop_offsets

        filename_re = re.compile(r"_(?P<group>\d+)[_-](?P<index>\d+)\.png$", re.IGNORECASE)

        for p in sorted(sprites_root.rglob("*.png")):
            m = filename_re.search(p.name)
            if not m:
                continue
            key = (int(m.group("group")), int(m.group("index")))
            if key in sprites:
                continue
            try:
                img = pygame.image.load(str(p)).convert_alpha()

                # Fighter Factory の出力は「透明余白が大きい」ケースがあるため、
                # 実際の絵がある領域だけにトリミングして見た目の高さを適正化する。
                bbox = img.get_bounding_rect(min_alpha=1)
                if bbox.width > 0 and bbox.height > 0:
                    trimmed = img.subsurface(bbox).copy()
                    sprites[key] = trimmed
                    crop_offsets[key] = (bbox.left, bbox.top)
                else:
                    sprites[key] = img
                    crop_offsets[key] = (0, 0)
            except pygame.error:
                continue

        return sprites, crop_offsets

    def _update_animation(self) -> None:
        # 最小実装：Action 0 の frames を time で進めてループ。
        if self._current_action_id is None:
            return

        action = self._air_actions.get(self._current_action_id)
        if not action:
            return

        frames: list[dict[str, Any]] = action.get("frames", [])
        if not frames:
            return

        frame = frames[self._frame_index]
        t = int(frame.get("time", 0))
        if int(self._current_action_id or 0) in {5000, 5040, 5041, 5042, 5043, 5044}:
            t = 10
        if t < 0:
            # -1 はそのフレームで停止（またはループ）扱い。
            # oneshot の場合は「終了扱い」にして Idle 復帰させる。
            if self._action_mode == "oneshot":
                self._action_finished = True
            return

        if self._frame_time_left <= 0:
            self._frame_time_left = max(1, t)

        self._frame_time_left -= 1
        if self._frame_time_left > 0:
            return

        # 次フレームへ。
        self._frame_index += 1
        if self._frame_index >= len(frames):
            if self._action_mode == "oneshot":
                if bool(self._knocked_down) and int(self._current_action_id or 0) == 5041:
                    target = min(9, max(0, len(frames) - 1))
                    self._frame_index = int(target)
                else:
                    self._frame_index = len(frames) - 1
                self._action_finished = True
                return
            self._frame_index = 0

        next_t = int(frames[self._frame_index].get("time", 0))
        if int(self._current_action_id or 0) in {5000, 5040, 5041, 5042, 5043, 5044}:
            next_t = 10
        self._frame_time_left = max(1, int(next_t))

    def update(self) -> None:
        # ヒットストップ中は「動作もタイマーも止める」。
        if self.hitstop_frames_left > 0:
            self.hitstop_frames_left -= 1
            return

        if int(self._shinku_lockout_frames_left) > 0:
            self._shinku_lockout_frames_left -= 1

        if self.combo_display_frames_left > 0:
            self.combo_display_frames_left -= 1

        self._action_frame_counter += 1

        if self._guard_buffer_frames_left > 0 and (not self.holding_back):
            self._guard_buffer_frames_left -= 1

        if self.hitstun_frames_left > 0:
            self.hitstun_frames_left -= 1

        prev_hitstun_timer = int(self.hitstun_timer)
        if self.hitstun_timer > 0:
            self.hitstun_timer -= 1
            if self.hitstun_timer < 0:
                self.hitstun_timer = 0

        # 突進技：初期モーション後、一定フレーム前進して終了。
        if self._rush_startup_frames_left > 0:
            self._rush_startup_frames_left -= 1
            self.vel_x = 0.0
        elif self._rush_frames_left > 0:
            self._rush_frames_left -= 1
            speed = float(getattr(constants, "RUSH_SPEED", 10.0))
            self.pos_x += float(self.facing) * speed
            self.vel_x = 0.0
            if self._rush_frames_left <= 0:
                rec_action = int(getattr(constants, "RUSH_RECOVERY_ACTION_ID", 6760))
                self._rush_recovery_frames_left = int(getattr(constants, "RUSH_RECOVERY_FRAMES", 12))
                self._rush_recovery_total_frames = int(self._rush_recovery_frames_left)
                if rec_action in self._air_actions:
                    self._set_action(rec_action, mode="oneshot")
                else:
                    self._set_action(self._best_action_id([0]), mode="loop")
                self._attack_id = None
        elif self._rush_recovery_frames_left > 0:
            self._rush_recovery_frames_left -= 1
            self.vel_x = 0.0
            if self._rush_recovery_frames_left <= 0 and (not self.in_hitstun):
                self._set_action(self._best_action_id([0]), mode="loop")

        prev_frame_index = int(self._frame_index)
        if prev_hitstun_timer > 0 and self.hitstun_timer == 0 and self.is_in_combo:
            self._combo_end_side_pending = self._combo_attacker_side
            self.is_in_combo = False
            self._combo_attacker_side = None

        if self.blockstun_frames_left > 0:
            self.blockstun_frames_left -= 1

        decay = float(getattr(constants, "KNOCKBACK_DECAY", 0.82))
        stop_eps = float(getattr(constants, "KNOCKBACK_STOP_EPS", 0.05))
        self.knockback_vx *= decay
        if abs(self.knockback_vx) < stop_eps:
            self.knockback_vx = 0.0

        self._update_animation()

        if (
            self._hadoken_action_id is not None
            and int(self._current_action_id or -1) == int(self._hadoken_action_id)
            and (not self._hadoken_spawned)
        ):
            # 最後のモーション（6040-3 / frame_index==2）へ切り替わった瞬間に弾を出す。
            if int(self._frame_index) == 2 and prev_frame_index != 2:
                delay = int(getattr(constants, "HADOKEN_SPAWN_DELAY_FRAMES", 20))
                self._hadoken_spawn_delay_frames_left = max(self._hadoken_spawn_delay_frames_left, max(0, delay))

            if self._hadoken_spawn_delay_frames_left > 0:
                self._hadoken_spawn_delay_frames_left -= 1
                if self._hadoken_spawn_delay_frames_left <= 0:
                    self._hadoken_spawned = True
                    self._hadoken_spawn_pending = True

        if (
            self._shinku_action_id is not None
            and int(self._current_action_id or -1) == int(self._shinku_action_id)
            and (not self._shinku_spawned)
        ):
            spawn_i = int(getattr(constants, "SHINKU_HADOKEN_SPAWN_FRAME_INDEX", 3))
            should_spawn = False
            if int(self._frame_index) >= spawn_i and int(prev_frame_index) < spawn_i:
                should_spawn = True
            if self._action_mode == "oneshot" and bool(getattr(self, "_action_finished", False)):
                should_spawn = True
            if should_spawn:
                self._shinku_spawned = True
                self._shinku_spawn_pending = True

        self._update_multihit_state()

        # oneshot 終了（攻撃など）→ Idle へ戻す。
        if self._action_mode == "oneshot" and self._action_finished and (not self.in_hitstun) and (not self._knocked_down):
            self._set_action(0, mode="loop")

        if self.is_in_combo and (not self.in_hitstun) and (not self.in_blockstun) and self.on_ground:
            if int(self._current_action_id or 0) == 0:
                self._combo_end_side_pending = self._combo_attacker_side
                self.is_in_combo = False
                self._combo_attacker_side = None

        # 攻撃タイマーを進める。
        if self._attack_frames_left > 0:
            self._attack_frames_left -= 1
            if self._attack_frames_left == 0:
                self._attack_id = None
                self._registered_hit_ids.clear()
                self._last_clsn1_signature = None
                self._current_hit_id = 0

        # 空中にいる間だけ重力を加える。
        if not self.on_ground:
            self.vel_y += constants.GRAVITY

        # 位置更新。
        self.pos_x += float(self.vel_x) + float(self.knockback_vx)
        self.pos_y += float(self.vel_y)

        # 地面より下に落ちないように補正。
        if self.pos_y >= constants.GROUND_Y:
            self.pos_y = float(constants.GROUND_Y)
            self.vel_y = 0.0
            self.on_ground = True

        # 画面外に出ないように補正。
        half_w = self.rect.width / 2.0
        min_x = half_w
        max_x = constants.STAGE_WIDTH - half_w
        self.pos_x = max(min_x, min(max_x, self.pos_x))

        # 壁に当たっている間は、壁方向へ押すノックバック速度を打ち消す。
        # これにより、クランプと減衰がぶつかって「押し付け続ける」挙動になりにくくする。
        if self.pos_x <= (min_x + 0.01) and self.knockback_vx < 0:
            self.knockback_vx = 0.0
        if self.pos_x >= (max_x - 0.01) and self.knockback_vx > 0:
            self.knockback_vx = 0.0

        # pos -> rect を同期。
        self.rect.midbottom = (int(self.pos_x), int(self.pos_y))

        # 攻撃モーション中以外は、状態に応じてアクションを切り替える。
        if self._action_mode != "oneshot" and (not self.in_hitstun):
            self._update_state_action()

    def _update_state_action(self) -> None:
        # まず空中判定（ジャンプ）。
        if not self.on_ground:
            if self.vel_y < 0:
                self._set_action(self._best_action_id([41, 40]), mode="loop")
            else:
                self._set_action(self._best_action_id([47, 40]), mode="loop")
            return

        # しゃがみ。
        if self.crouching:
            self._set_action(self._best_action_id([11, 10]), mode="loop")
            return

        # 歩き（前/後）。
        if abs(self.vel_x) > 0.01:
            move_dir = 1 if self.vel_x > 0 else -1
            forward = (move_dir == self.facing)
            if forward:
                self._set_action(self._best_action_id([20]), mode="loop")
            else:
                self._set_action(self._best_action_id([21]), mode="loop")
            return

        # 待機。
        self._set_action(self._best_action_id([0]), mode="loop")

    def _best_action_id(self, candidates: list[int]) -> int:
        # 候補のうち存在するものを優先的に返す。すべて無ければ 0。
        for a in candidates:
            if a in self._air_actions:
                return a
        if self._air_actions:
            # Idle(0) が無いキャラでも、最低限描画できるものを返す。
            return int(sorted(self._air_actions.keys())[0])
        return 0

    def _attack_to_action_id(self, attack_id: str) -> int | None:
        mapping = getattr(self.character, "attack_action_map", {})
        if not isinstance(mapping, dict):
            return None
        v = mapping.get(str(attack_id))
        if v is None:
            return None
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    def _infer_move_frame_info(self, attack_id: str) -> MoveFrameInfo | None:
        action_id = self._attack_to_action_id(attack_id)
        if action_id is None:
            return None
        if action_id not in self._air_actions:
            return None

        action = self._air_actions.get(action_id)
        if not action:
            return None
        frames = action.get("frames", [])
        if not isinstance(frames, list) or not frames:
            return None

        total = 0
        startup = 0
        active = 0
        first_active_seen = False

        for fr in frames:
            if not isinstance(fr, dict):
                continue

            t = int(fr.get("time", 0))
            if t < 0:
                # -1 は停止扱いなので、フレーム数には加算しない。
                t = 0

            clsn1 = fr.get("clsn1")
            has_active = isinstance(clsn1, list) and len(clsn1) > 0

            total += t
            if has_active:
                active += t
                first_active_seen = True
            else:
                if not first_active_seen:
                    startup += t

        total = max(1, int(total))
        startup = max(0, min(int(startup), total))
        active = max(0, min(int(active), total))
        recovery = max(0, total - startup - active)

        spec = constants.ATTACK_SPECS.get(str(attack_id))
        if isinstance(spec, dict):
            bonus = int(spec.get("recovery_bonus_frames", 0))
            if bonus > 0:
                total += bonus
                recovery += bonus

        return MoveFrameInfo(
            attack_id=str(attack_id),
            total_frames=total,
            startup_frames=startup,
            active_frames=active,
            recovery_frames=recovery,
        )

    def _get_current_frame(self) -> dict[str, Any] | None:
        if self._current_action_id is None:
            return None
        action = self._air_actions.get(self._current_action_id)
        if not action:
            return None
        frames = action.get("frames", [])
        if not isinstance(frames, list) or not frames:
            return None
        if self._frame_index < 0 or self._frame_index >= len(frames):
            return None
        frame = frames[self._frame_index]
        if not isinstance(frame, dict):
            return None
        return frame

    def _update_multihit_state(self) -> None:
        if not self.attacking:
            self._last_clsn1_signature = None
            self._current_hit_id = 0
            return

        frame = self._get_current_frame()
        if frame is None:
            self._last_clsn1_signature = None
            self._current_hit_id = 0
            return

        raw = frame.get("clsn1")
        if not isinstance(raw, list) or not raw:
            self._last_clsn1_signature = None
            return

        sig: list[tuple[int, int, int, int]] = []
        for item in raw:
            if not isinstance(item, (tuple, list)) or len(item) != 4:
                continue
            try:
                sig.append((int(item[0]), int(item[1]), int(item[2]), int(item[3])))
            except (TypeError, ValueError):
                continue

        signature = tuple(sig)
        if not signature:
            self._last_clsn1_signature = None
            return

        if signature != self._last_clsn1_signature:
            self._hit_id_counter += 1
            self._current_hit_id = self._hit_id_counter
            self._last_clsn1_signature = signature

    def _get_axis_world_position(self, frame: dict[str, Any]) -> tuple[int, int]:
        off_x = int(frame.get("x", 0))
        off_y = int(frame.get("y", 0))
        if self.facing < 0:
            off_x = -off_x
        axis_x = self.rect.centerx + off_x
        axis_y = self.rect.bottom + off_y
        return axis_x, axis_y

    def _build_air_rect(self, *, axis_x: int, axis_y: int, raw: tuple[int, int, int, int]) -> pygame.Rect:
        x1, y1, x2, y2 = raw

        if self.facing < 0:
            world_x1 = axis_x - x2
            world_x2 = axis_x - x1
        else:
            world_x1 = axis_x + x1
            world_x2 = axis_x + x2

        world_y1 = axis_y + y1
        world_y2 = axis_y + y2

        left = min(world_x1, world_x2)
        top = min(world_y1, world_y2)
        right = max(world_x1, world_x2)
        bottom = max(world_y1, world_y2)
        return pygame.Rect(left, top, max(1, right - left), max(1, bottom - top))

    def _get_air_clsn_boxes(self, kind: str) -> list[pygame.Rect]:
        frame = self._get_current_frame()
        if frame is None:
            return []

        raw_rects = frame.get(kind)
        if not isinstance(raw_rects, list) or not raw_rects:
            return []

        axis_x, axis_y = self._get_axis_world_position(frame)
        out: list[pygame.Rect] = []
        for item in raw_rects:
            if not isinstance(item, (tuple, list)) or len(item) != 4:
                continue
            try:
                rect = self._build_air_rect(
                    axis_x=axis_x,
                    axis_y=axis_y,
                    raw=(int(item[0]), int(item[1]), int(item[2]), int(item[3])),
                )
            except (TypeError, ValueError):
                continue
            out.append(rect)
        return out

    @staticmethod
    def _fallback_attack_hitbox(base: pygame.Rect, *, facing: int, crouching: bool, attack_id: str | None) -> pygame.Rect:
        spec = constants.ATTACK_SPECS.get(attack_id or "")
        if spec is None:
            hitbox_w = constants.HITBOX_WIDTH
            hitbox_h = constants.HITBOX_HEIGHT
            offset_x = constants.HITBOX_OFFSET_X
            offset_y = constants.HITBOX_OFFSET_Y
        else:
            hitbox_w = int(spec["hitbox_width"])
            hitbox_h = int(spec["hitbox_height"])
            offset_x = int(spec["hitbox_offset_x"])
            offset_y = int(spec["hitbox_offset_y"])

        if crouching:
            y = base.top + offset_y + 20
        else:
            y = base.top + offset_y

        if facing >= 0:
            x = base.right + offset_x
        else:
            x = base.left - offset_x - hitbox_w

        return pygame.Rect(x, y, hitbox_w, hitbox_h)

    @staticmethod
    def _union_rects(rects: list[pygame.Rect]) -> pygame.Rect:
        merged = rects[0].copy()
        for r in rects[1:]:
            merged.union_ip(r)
        return merged

    def get_hurtbox(self) -> pygame.Rect:
        # 互換API（単一Rect）。
        # 内部では AIR の複数clsn2 を扱うため、描画/判定には get_hurtboxes() を優先する。
        hurtboxes = self.get_hurtboxes()
        return self._union_rects(hurtboxes)

    def get_hurtboxes(self) -> list[pygame.Rect]:
        # AIRフレームに紐づく食らい判定（clsn2）を優先。
        # データがない場合は従来どおり本体rectを使う。
        air_boxes = self._get_air_clsn_boxes("clsn2")
        if air_boxes:
            return air_boxes
        return [self.rect.copy()]

    def get_pushbox(self) -> pygame.Rect:
        # 押し合い判定。
        # Hurtbox より少し細くして「見た目の重なり」と「押し合い」のバランスを取りやすくする。
        push = self.rect.copy()
        push.width = int(self.rect.width * 0.90)
        push.centerx = self.rect.centerx
        return push

    def get_hitbox(self) -> pygame.Rect | None:
        hitboxes = self.get_hitboxes()
        if not hitboxes:
            return None
        return self._union_rects(hitboxes)

    def get_hitboxes(self) -> list[pygame.Rect]:
        # 攻撃判定は「攻撃中」かつ「そのフレームのclsn1がある時のみ」有効。
        if self.is_rush_attack_active():
            return [self._get_rush_hitbox()]
        if not self.attacking:
            return []

        air_boxes = self._get_air_clsn_boxes("clsn1")
        if air_boxes:
            return air_boxes

        # AIRのフレーム判定データが無い場合の従来フォールバック。
        if self._current_action_id is None:
            return [
                self._fallback_attack_hitbox(
                    self.rect,
                    facing=self.facing,
                    crouching=self.crouching,
                    attack_id=self._attack_id,
                )
            ]

        # AIR再生中でclsn1が無いフレームは、攻撃判定なし。
        return []

    def can_deal_damage(self) -> bool:
        if self.is_rush_attack_active():
            return (not bool(self._rush_has_hit))
        if not self.attacking:
            return False
        if not self.get_hitboxes():
            return False
        hit_id = int(self._current_hit_id)
        if hit_id <= 0:
            return False
        return hit_id not in self._registered_hit_ids

    def register_current_hit(self) -> None:
        if self.is_rush_attack_active():
            self._rush_has_hit = True
            return
        hit_id = int(self._current_hit_id)
        if hit_id > 0:
            self._registered_hit_ids.add(hit_id)

    def mark_damage_dealt(self) -> None:
        self.register_current_hit()

    def start_combo_on_opponent(self, *, opponent_side: int) -> None:
        self.combo_count = 1
        self.combo_display_count = 1
        self.combo_display_frames_left = 0
        self.combo_damage_total = 0
        self.combo_damage_display = 0

    def extend_combo_on_opponent(self) -> None:
        self.combo_count += 1
        self.combo_display_count = int(self.combo_count)
        show_frames = int(getattr(constants, "COMBO_DISPLAY_FRAMES", int(2.5 * constants.FPS)))
        self.combo_display_frames_left = max(self.combo_display_frames_left, show_frames)

    def add_combo_damage(self, amount: int) -> None:
        self.combo_damage_total += max(0, int(amount))
        self.combo_damage_display = int(self.combo_damage_total)
        if self.combo_display_count >= 2:
            show_frames = int(getattr(constants, "COMBO_DISPLAY_FRAMES", int(2.5 * constants.FPS)))
            self.combo_display_frames_left = max(self.combo_display_frames_left, show_frames)

    def reset_combo_count(self) -> None:
        self.combo_count = 0
        self.combo_damage_total = 0
        self.combo_damage_display = 0

    def set_combo_victim_state(self, *, attacker_side: int, hitstun_frames: int) -> None:
        self.is_in_combo = True
        self._combo_attacker_side = int(attacker_side)
        self.hitstun_timer = max(0, int(hitstun_frames))

    def consume_combo_end_side(self) -> int | None:
        side = self._combo_end_side_pending
        self._combo_end_side_pending = None
        return side

    def get_combo_count(self) -> int:
        return int(self.combo_count)

    def take_damage(self, damage: int) -> None:
        d = max(0, int(damage))
        self.hp = max(0, self.hp - d)
        ratio = float(getattr(constants, "POWER_GAIN_ON_TAKE_DAMAGE_RATIO", 0.20))
        gain = int(round(float(d) * max(0.0, ratio)))
        if gain > 0:
            self.add_power(gain)

    def apply_knockback(self, *, dir_x: int, amount_px: int) -> None:
        # dir_x はノックバック方向（+1:右 / -1:左）。
        impulse = float(int(dir_x) * int(amount_px))
        self.knockback_vx += impulse
        vx_max = float(getattr(constants, "KNOCKBACK_VX_MAX", 12.0))
        if self.knockback_vx > vx_max:
            self.knockback_vx = vx_max
        elif self.knockback_vx < -vx_max:
            self.knockback_vx = -vx_max

    def draw(self, surface: pygame.Surface, *, debug_draw: bool) -> None:
        # Sprite がロードできているなら、AIR の (group,index) を使って描画する。
        drawn_sprite = False

        # 突進中は 6520-2 を固定表示（アニメーションのpngのまま突進）。
        if self.is_rushing():
            key = (6520, 2)
            img = self._sprites.get(key)
            if img is not None:
                x = int(self.rect.centerx) - (img.get_width() // 2)
                y = int(self.rect.bottom) - img.get_height()
                if int(self.facing) < 0:
                    img = pygame.transform.flip(img, True, False)
                surface.blit(img, (x, y))
                drawn_sprite = True

        # 突進後の硬直は 6760-1..3 を固定で順番表示する。
        if (not drawn_sprite) and int(self._rush_recovery_frames_left) > 0:
            total = max(1, int(getattr(self, "_rush_recovery_total_frames", 0)) or 1)
            left = int(self._rush_recovery_frames_left)
            elapsed = max(0, total - left)
            phase = elapsed / float(total)
            idx = 1
            if phase >= (2.0 / 3.0):
                idx = 3
            elif phase >= (1.0 / 3.0):
                idx = 2

            key = (int(getattr(constants, "RUSH_RECOVERY_ACTION_ID", 6760)), int(idx))
            img = self._sprites.get(key)
            if img is not None:
                x = int(self.rect.centerx) - (img.get_width() // 2)
                y = int(self.rect.bottom) - img.get_height()
                if int(self.facing) < 0:
                    img = pygame.transform.flip(img, True, False)
                surface.blit(img, (x, y))
                drawn_sprite = True

        if (not drawn_sprite) and self._current_action_id is not None:
            frame = self._get_current_frame()
            if frame is not None:
                group = frame.get("group")
                index = frame.get("index")
                sprite = frame.get("sprite")
                key: tuple[int, int] | None = None
                if isinstance(group, (int, str)) and isinstance(index, (int, str)):
                    try:
                        key = (int(group), int(index))
                    except (TypeError, ValueError):
                        key = None
                elif isinstance(sprite, (tuple, list)) and len(sprite) >= 2:
                    try:
                        key = (int(sprite[0]), int(sprite[1]))
                    except (TypeError, ValueError):
                        key = None

                if key is not None:
                    img = self._sprites.get(key)
                    if img is not None:
                        off_x = int(frame.get("x", 0))
                        off_y = int(frame.get("y", 0))

                        x = int(self.rect.centerx) - (img.get_width() // 2)
                        y = int(self.rect.bottom) - img.get_height()

                        # facing が左向きの場合は左右反転し、xオフセットも反転させる。
                        if self.facing < 0:
                            img = pygame.transform.flip(img, True, False)
                            off_x = -off_x

                        surface.blit(img, (x + off_x, y + off_y))
                        drawn_sprite = True

        if not drawn_sprite:
            # フォールバック：攻撃中は見た目を少し明るくして、状態が分かるようにする。
            if self.attacking:
                body_color = tuple(min(255, int(c * 1.35)) for c in self.color)
            else:
                body_color = self.color
            pygame.draw.rect(surface, body_color, self.rect)

        # F3 でデバッグ描画自体をまとめてON/OFFする。
        if not debug_draw:
            return

        # 足元基準点（pos_x,pos_y）を可視化する（ズレ確認用）。
        cx = int(self.pos_x)
        cy = int(self.pos_y)
        pygame.draw.line(surface, (255, 255, 0), (cx - 4, cy), (cx + 4, cy), 2)
        pygame.draw.line(surface, (255, 255, 0), (cx, cy - 4), (cx, cy + 4), 2)

        # Hurtbox（AIR clsn2）と Pushbox（押し合い枠）を描画。
        for hurtbox in self.get_hurtboxes():
            pygame.draw.rect(surface, constants.COLOR_HURTBOX, hurtbox, 2)
        pygame.draw.rect(surface, constants.COLOR_PUSHBOX, self.get_pushbox(), 2)

        # Hitbox（AIR clsn1）はフレームに存在する時だけ描画。
        for hitbox in self.get_hitboxes():
            pygame.draw.rect(surface, constants.COLOR_HITBOX, hitbox, 2)
