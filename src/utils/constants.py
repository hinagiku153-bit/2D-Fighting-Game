from __future__ import annotations

# このファイルは、ゲーム内の数値設定を1か所に集約するための定数定義です。
# Phase 1 では「60FPS固定」を前提に、速度や重力は “1フレームあたり” の値として扱います。

# Window（画面・ウィンドウ関連）
SCREEN_WIDTH: int = 800
SCREEN_HEIGHT: int = 450
CAPTION: str = "PyFight Online"

# Timing（フレームレート）
FPS: int = 60

# Physics（簡易物理）
# y軸は下方向が + なので、ジャンプ初速は負の値になります。
GRAVITY: float = 0.8
WALK_SPEED: float = 4.0
JUMP_VELOCITY: float = -14.0
GROUND_Y: int = 400

# Player（プレイヤー矩形の見た目サイズ）
PLAYER_WIDTH: int = 50
PLAYER_HEIGHT: int = 90

# Combat (Phase 1 prototype)
# 攻撃は「キーを押した瞬間に一定時間だけ攻撃状態になる」簡易実装です。
ATTACK_DURATION_SECONDS: float = 0.20
HITBOX_WIDTH: int = 35
HITBOX_HEIGHT: int = 25
HITBOX_OFFSET_X: int = 30
HITBOX_OFFSET_Y: int = 20

# Debug
# 判定枠線（Hurtbox/Pushbox/Hitbox）を最初から表示するかどうか。
DEBUG_DRAW_DEFAULT: bool = True

# Colors (RGB)
# ここでは見やすさを優先した暫定色を使います。
COLOR_BG = (25, 25, 25)
COLOR_P1 = (40, 90, 220)
COLOR_P2 = (220, 60, 60)

COLOR_HURTBOX = (230, 230, 230)
COLOR_PUSHBOX = (80, 160, 255)
COLOR_HITBOX = (255, 50, 50)
