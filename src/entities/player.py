from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import pygame

from src.utils import constants


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
    ) -> None:
        self.color = color

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
        self.hitstun_frames_left = max(self.hitstun_frames_left, int(frames))

        # 攻撃中の相殺など最小限の整合性として、攻撃状態は解除する。
        self._attack_frames_left = 0
        self._attack_has_hit = False
        self._attack_id = None

        # Action 5000（地上ダメージ）へ。
        self._set_action(self._best_action_id([5000]), mode="oneshot")

    def enter_blockstun(self, *, frames: int | None = None, crouching: bool = False) -> None:
        if frames is None:
            frames = int(getattr(constants, "BLOCKSTUN_DEFAULT_FRAMES", 12))
        self.blockstun_frames_left = max(self.blockstun_frames_left, int(frames))

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
        self.combo_count = 0

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

        # 攻撃は押した瞬間だけ開始。
        if inp.attack_id is not None:
            # デバッグ表示用に、攻撃が成立しなくても「押した技」のフレーム情報は更新する。
            info = self._infer_move_frame_info(inp.attack_id)
            if info is not None:
                self._last_move_frame_info = info
            self.start_attack(inp.attack_id)

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
        sprites, crop_offsets = self._load_sprites_from_organized(sprites_root)
        self._sprites = sprites
        self._sprite_crop_offsets = crop_offsets
        self._set_action(0, mode="loop")

    def _set_action(self, action_id: int, *, mode: str) -> None:
        if action_id not in self._air_actions:
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
            self._frame_time_left = max(0, t)

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
        if t == -1:
            # -1 はそのフレームで停止（またはループ）扱い。
            # oneshot の場合は「終了扱い」にして Idle 復帰させる。
            if self._action_mode == "oneshot":
                self._action_finished = True
            return

        if self._frame_time_left <= 0:
            self._frame_time_left = max(0, t)

        self._frame_time_left -= 1
        if self._frame_time_left > 0:
            return

        # 次フレームへ。
        self._frame_index += 1
        if self._frame_index >= len(frames):
            if self._action_mode == "oneshot":
                self._frame_index = len(frames) - 1
                self._action_finished = True
                return
            self._frame_index = 0

        next_t = int(frames[self._frame_index].get("time", 0))
        self._frame_time_left = max(0, next_t)

    def update(self) -> None:
        # ヒットストップ中は「動作もタイマーも止める」。
        if self.hitstop_frames_left > 0:
            self.hitstop_frames_left -= 1
            return

        self._action_frame_counter += 1

        if self._guard_buffer_frames_left > 0 and (not self.holding_back):
            self._guard_buffer_frames_left -= 1

        if self.hitstun_frames_left > 0:
            self.hitstun_frames_left -= 1

        if self.blockstun_frames_left > 0:
            self.blockstun_frames_left -= 1

        decay = float(getattr(constants, "KNOCKBACK_DECAY", 0.82))
        stop_eps = float(getattr(constants, "KNOCKBACK_STOP_EPS", 0.05))
        self.knockback_vx *= decay
        if abs(self.knockback_vx) < stop_eps:
            self.knockback_vx = 0.0

        self._update_animation()

        self._update_multihit_state()

        # oneshot 終了（攻撃など）→ Idle へ戻す。
        if self._action_mode == "oneshot" and self._action_finished and (not self.in_hitstun):
            self._set_action(0, mode="loop")

        # 攻撃タイマーを進める。
        if self._attack_frames_left > 0:
            self._attack_frames_left -= 1
            if self._attack_frames_left == 0:
                self._attack_id = None
                self._registered_hit_ids.clear()
                self._last_clsn1_signature = None
                self._current_hit_id = 0
                self.combo_count = 0

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
        return 0

    @staticmethod
    def _attack_to_action_id(attack_id: str) -> int | None:
        # キーコンフィグ/攻撃ID → AIR Action番号
        mapping: dict[str, int] = {
            "P1_U_LP": 200,
            "P1_I_MP": 210,
            "P1_O_HP": 229,
            "P1_J_LK": 400,
            "P1_K_MK": 410,
            "P1_L_HK": 430,
            "P2_L_PUNCH": 200,
        }
        return mapping.get(attack_id)

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
        if not self.attacking:
            return False
        if not self.get_hitboxes():
            return False
        hit_id = int(self._current_hit_id)
        if hit_id <= 0:
            return False
        return hit_id not in self._registered_hit_ids

    def register_current_hit(self) -> None:
        hit_id = int(self._current_hit_id)
        if hit_id > 0:
            self._registered_hit_ids.add(hit_id)

    def mark_damage_dealt(self) -> None:
        self.register_current_hit()
        self.combo_count += 1

    def get_combo_count(self) -> int:
        return int(self.combo_count)

    def take_damage(self, damage: int) -> None:
        self.hp = max(0, self.hp - int(damage))

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
        if self._current_action_id is not None:
            action = self._air_actions.get(self._current_action_id)
            frames: list[dict[str, Any]] = [] if not action else action.get("frames", [])
            if frames:
                frame = frames[self._frame_index]
                key = (int(frame.get("group", -1)), int(frame.get("index", -1)))
                img = self._sprites.get(key)
                if img is not None:
                    off_x = int(frame.get("x", 0))
                    off_y = int(frame.get("y", 0))

                    # facing が左向きの場合は左右反転し、xオフセットも反転させる。
                    if self.facing < 0:
                        img = pygame.transform.flip(img, True, False)
                        off_x = -off_x

                    # 描画基準点は pos_x / pos_y（足元の接地中点）。
                    # 以前の最小実装の描画方式：
                    # - 画像の中心xを rect.centerx に合わせる
                    # - yは rect.bottom から画像高さ分だけ上へ
                    # - AIRの x/y は、その描画位置に加算する（補正値扱い）
                    draw_x = self.rect.centerx - (img.get_width() // 2) + off_x
                    draw_y = self.rect.bottom - img.get_height() + off_y
                    surface.blit(img, (draw_x, draw_y))
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
