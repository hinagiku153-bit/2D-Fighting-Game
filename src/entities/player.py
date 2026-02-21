from __future__ import annotations

from dataclasses import dataclass

import pygame

from src.utils import constants


@dataclass
class PlayerInput:
    # Player に渡す入力の「意図（intent）」をまとめたデータ。
    # - move_x: 左(-1) / 停止(0) / 右(+1)
    # - jump_pressed: 押した瞬間だけ True（ジャンプ開始トリガ）
    # - crouch: 押している間 True（しゃがみ保持）
    # - attack_pressed: 押した瞬間だけ True（攻撃開始トリガ）
    move_x: int
    jump_pressed: bool
    crouch: bool
    attack_pressed: bool


class Player:
    def __init__(
        self,
        *,
        x: int,
        color: tuple[int, int, int],
    ) -> None:
        self.color = color

        # rect はプレイヤー本体の当たり判定（Hurtbox）兼、描画矩形として使う。
        # 位置は「左上座標」基準（pygame.Rect の仕様）。
        self.rect = pygame.Rect(
            x,
            constants.GROUND_Y - constants.PLAYER_HEIGHT,
            constants.PLAYER_WIDTH,
            constants.PLAYER_HEIGHT,
        )

        # 速度は float で管理し、rect へ反映する時に int 化する（簡易物理）。
        self.vel_x: float = 0.0
        self.vel_y: float = 0.0

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

    @property
    def attacking(self) -> bool:
        # 攻撃タイマーが残っている間だけ攻撃中。
        return self._attack_frames_left > 0

    def start_attack(self) -> None:
        # すでに攻撃中なら再発動しない（連打で伸びないようにする）。
        if self.attacking:
            return
        # 秒→フレームに変換して管理する。
        self._attack_frames_left = max(1, int(constants.ATTACK_DURATION_SECONDS * constants.FPS))
        self._attack_has_hit = False

    def apply_input(self, inp: PlayerInput) -> None:
        # しゃがみは地上にいる間だけ成立。
        self.crouching = inp.crouch and self.on_ground

        # 左右移動は入力をそのまま速度に変換する（慣性なし）。
        self.vel_x = float(inp.move_x) * constants.WALK_SPEED

        # ジャンプは押した瞬間だけ成立。
        if inp.jump_pressed and self.on_ground:
            self.vel_y = constants.JUMP_VELOCITY
            self.on_ground = False

        # 攻撃は押した瞬間だけ開始。
        if inp.attack_pressed:
            self.start_attack()

    def update(self) -> None:
        # 攻撃タイマーを進める。
        if self._attack_frames_left > 0:
            self._attack_frames_left -= 1

        # 空中にいる間だけ重力を加える。
        if not self.on_ground:
            self.vel_y += constants.GRAVITY

        # 位置更新。
        self.rect.x += int(self.vel_x)
        self.rect.y += int(self.vel_y)

        # 地面より下に落ちないように補正。
        if self.rect.bottom >= constants.GROUND_Y:
            self.rect.bottom = constants.GROUND_Y
            self.vel_y = 0.0
            self.on_ground = True

        # 画面外に出ないように補正。
        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(constants.SCREEN_WIDTH, self.rect.right)

    def get_hurtbox(self) -> pygame.Rect:
        # 食らい判定（本体）。rect をそのまま使う。
        return self.rect.copy()

    def get_pushbox(self) -> pygame.Rect:
        # 押し合い判定。
        # Hurtbox より少し細くして「見た目の重なり」と「押し合い」のバランスを取りやすくする。
        push = self.rect.copy()
        push.width = int(self.rect.width * 0.90)
        push.centerx = self.rect.centerx
        return push

    def get_hitbox(self) -> pygame.Rect | None:
        # 攻撃判定（攻撃中のみ前方へ出す）。
        if not self.attacking:
            return None

        # しゃがみ中は少し低い位置に判定を出す。
        if self.crouching:
            h = constants.HITBOX_HEIGHT
            y = self.rect.top + constants.HITBOX_OFFSET_Y + 20
        else:
            h = constants.HITBOX_HEIGHT
            y = self.rect.top + constants.HITBOX_OFFSET_Y

        # facing に応じて「前方」に出す。
        if self.facing >= 0:
            x = self.rect.right + constants.HITBOX_OFFSET_X
        else:
            x = self.rect.left - constants.HITBOX_OFFSET_X - constants.HITBOX_WIDTH

        return pygame.Rect(x, y, constants.HITBOX_WIDTH, h)

    def draw(self, surface: pygame.Surface, *, debug_draw: bool) -> None:
        # 攻撃中は見た目を少し明るくして、状態が分かるようにする。
        if self.attacking:
            body_color = tuple(min(255, int(c * 1.35)) for c in self.color)
        else:
            body_color = self.color

        pygame.draw.rect(surface, body_color, self.rect)

        # F3 でデバッグ描画自体をまとめてON/OFFする。
        if not debug_draw:
            return

        # Hurtbox（本体枠）と Pushbox（押し合い枠）を描画。
        pygame.draw.rect(surface, constants.COLOR_HURTBOX, self.get_hurtbox(), 2)
        pygame.draw.rect(surface, constants.COLOR_PUSHBOX, self.get_pushbox(), 2)

        # Hitbox（攻撃枠）は攻撃中だけ描画。
        hitbox = self.get_hitbox()
        if hitbox is not None:
            pygame.draw.rect(surface, constants.COLOR_HITBOX, hitbox, 2)
