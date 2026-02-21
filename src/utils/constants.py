from __future__ import annotations

# このファイルは、ゲーム内の数値設定を1か所に集約するための定数定義です。
# Phase 1 では「60FPS固定」を前提に、速度や重力は “1フレームあたり” の値として扱います。

# Window（画面・ウィンドウ関連）
# ステージ（論理解像度）は固定。ウィンドウ解像度を変えてもステージの広さは変えない。
STAGE_WIDTH: int = 820
STAGE_HEIGHT: int = 540

# 実際のウィンドウ解像度（初期値）。
SCREEN_WIDTH: int = 1220
SCREEN_HEIGHT: int = 720
GAME_TITLE: str = "SCRIPT FIGHTERS"
CAPTION: str = GAME_TITLE

# Timing（フレームレート）
FPS: int = 60

# Physics（簡易物理）
# y軸は下方向が + なので、ジャンプ初速は負の値になります。
GRAVITY: float = 0.8
WALK_SPEED: float = 4.0
JUMP_VELOCITY: float = -14.0
# 地面ライン（足元のY座標）。
# ステージ（論理解像度）に対して固定。
GROUND_Y: int = 470

# Player（プレイヤー矩形の見た目サイズ）
PLAYER_WIDTH: int = 50
PLAYER_HEIGHT: int = 90

# Combat (Phase 1 prototype)
# 攻撃は「キーを押した瞬間に一定時間だけ攻撃状態になる」簡易実装です。
# Phase 1.5: 1P は複数の攻撃タイプ（U/J/I/K/O）を持つ。

PLAYER_MAX_HP: int = 1000

# 共通（フォールバック）
ATTACK_DURATION_SECONDS: float = 0.20
HITBOX_WIDTH: int = 35
HITBOX_HEIGHT: int = 25
HITBOX_OFFSET_X: int = 30
HITBOX_OFFSET_Y: int = 20

# ヒットストップ（両者停止）
HITSTOP_DEFAULT_FRAMES: int = 6

# ヒットエフェクト発生時の追加ヒットストップ（手応え調整用）
HIT_EFFECT_EXTRA_HITSTOP_FRAMES: int = 4

# ヒット時に攻撃側も少し後ろへ下がる（セパレーション）距離（px）
ATTACKER_RECOIL_PX_DEFAULT: int = 3

# Knockback (velocity + decay)
KNOCKBACK_DECAY: float = 0.70
KNOCKBACK_STOP_EPS: float = 0.50
KNOCKBACK_VX_MAX: float = 12.0

# Guard (Phase 1.5)
GUARD_CHIP_DAMAGE_RATIO: float = 0.0
BLOCKSTUN_DEFAULT_FRAMES: int = 12
GUARD_KNOCKBACK_PX_DEFAULT: int = 10
GUARD_KNOCKBACK_MULTIPLIER: float = 1.20

# ガード入力バッファ（フレーム）。後ろ入力がこのフレーム数だけ保持される。
GUARD_BUFFER_FRAMES: int = 2

# のけぞり終了直前は、少し早めにガード入力を受け付ける（フレーム）。
HITSTUN_GUARD_EARLY_ACCEPT_FRAMES: int = 2

# 攻撃仕様（最初はお任せ調整の暫定値）
# - damage: 与えるダメージ
# - duration_frames: Hitbox を表示・判定するフレーム数
# - hitbox_*: 判定矩形のサイズ/オフセット
# - knockback_px: ヒット時に食らった側を後方へ押す距離（px）
# - hitstop_frames: ヒット時の停止フレーム数
ATTACK_SPECS: dict[str, dict[str, int]] = {
    # 1P attacks
    "P1_U_LP": {
        "damage": 40,
        "duration_frames": 8,
        "hitbox_width": 30,
        "hitbox_height": 20,
        "hitbox_offset_x": 22,
        "hitbox_offset_y": 18,
        "knockback_px": 8,
        "hitstop_frames": 5,
        "recovery_bonus_frames": 6,
        "attacker_recoil_px": 4,
    },
    "P1_I_MP": {
        "damage": 65,
        "duration_frames": 12,
        "hitbox_width": 38,
        "hitbox_height": 22,
        "hitbox_offset_x": 26,
        "hitbox_offset_y": 18,
        "knockback_px": 10,
        "hitstop_frames": 6,
    },
    "P1_O_HP": {
        "damage": 110,
        "duration_frames": 16,
        "hitbox_width": 48,
        "hitbox_height": 28,
        "hitbox_offset_x": 30,
        "hitbox_offset_y": 18,
        "knockback_px": 16,
        "hitstop_frames": 8,
    },
    "P1_J_LK": {
        "damage": 55,
        "duration_frames": 12,
        "hitbox_width": 38,
        "hitbox_height": 22,
        "hitbox_offset_x": 26,
        "hitbox_offset_y": 28,
        "knockback_px": 10,
        "hitstop_frames": 6,
    },
    "P1_K_MK": {
        "damage": 75,
        "duration_frames": 14,
        "hitbox_width": 46,
        "hitbox_height": 22,
        "hitbox_offset_x": 30,
        "hitbox_offset_y": 26,
        "knockback_px": 12,
        "hitstop_frames": 7,
    },
    "P1_L_HK": {
        "damage": 95,
        "duration_frames": 16,
        "hitbox_width": 58,
        "hitbox_height": 24,
        "hitbox_offset_x": 34,
        "hitbox_offset_y": 24,
        "knockback_px": 16,
        "hitstop_frames": 8,
    },
    # P2 default attack (temporary)
    "P2_L_PUNCH": {
        "damage": 50,
        "duration_frames": 10,
        "hitbox_width": HITBOX_WIDTH,
        "hitbox_height": HITBOX_HEIGHT,
        "hitbox_offset_x": HITBOX_OFFSET_X,
        "hitbox_offset_y": HITBOX_OFFSET_Y,
        "knockback_px": 12,
        "hitstop_frames": HITSTOP_DEFAULT_FRAMES,
    },
}

# HP Bar
HP_BAR_WIDTH: int = 300
HP_BAR_HEIGHT: int = 18
HP_BAR_MARGIN_X: int = 20
HP_BAR_MARGIN_Y: int = 15
HP_BAR_CHIP_LERP: float = 0.15
HP_BAR_DAMAGE_LERP: float = 0.08
COLOR_HP_BG = (60, 60, 60)
COLOR_HP_FILL = (80, 220, 120)
COLOR_HP_CHIP = (220, 70, 70)

# Debug
# 判定枠線（Hurtbox/Pushbox/Hitbox）を最初から表示するかどうか。
DEBUG_DRAW_DEFAULT: bool = True

HITSTUN_DEFAULT_FRAMES: int = 20

# Colors (RGB)
# ここでは見やすさを優先した暫定色を使います。
COLOR_BG = (25, 25, 25)
COLOR_P1 = (40, 90, 220)
COLOR_P2 = (220, 60, 60)

COLOR_HURTBOX = (60, 200, 255)
COLOR_PUSHBOX = (80, 160, 255)
COLOR_HITBOX = (255, 50, 50)
