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

# Input
# コマンド（236236 など）検知用に、方向/ボタン履歴を保持するフレーム数。
INPUT_BUFFER_FRAMES: int = 25

# Command leniency
COMMAND_BUTTON_EARLY_FRAMES: int = 2

# Hit cancel window (frames after hit where you can cancel into another attack)
HIT_CANCEL_WINDOW_FRAMES: int = 8

# Dash (double-tap)
DASH_DOUBLE_TAP_WINDOW_FRAMES: int = 12
DASH_FRAMES: int = 14
DASH_SPEED: float = 8.0

# Step (double-tap) - dashの代わりに短距離の前ステップ/バックステップを行う
STEP_FORWARD_FRAMES: int = 10
STEP_BACK_FRAMES: int = 12
STEP_FORWARD_SPEED: float = 7.0
STEP_BACK_SPEED: float = 7.5

# Physics（簡易物理）
# y軸は下方向が + なので、ジャンプ初速は負の値になります。
GRAVITY: float = 0.8
WALK_SPEED: float = 4.0
JUMP_VELOCITY: float = -14.0

# Rush (突進技)
RUSH_STARTUP_FRAMES: int = 6
RUSH_FRAMES: int = 18
RUSH_SPEED: float = 10.0
RUSH_RECOVERY_ACTION_ID: int = 6760
RUSH_RECOVERY_FRAMES: int = 12
# 地面ライン（足元のY座標）。
# ステージ（論理解像度）に対して固定。
GROUND_Y: int = 470

# Super (Shinku Hadoken)
SHINKU_HADOKEN_ACTION_ID: int = 8000
SHINKU_HADOKEN_MOTION_START_INDEX: int = 1
SHINKU_HADOKEN_MOTION_END_INDEX: int = 6
SHINKU_HADOKEN_PROJECTILE_GROUP_ID: int = 8001
SHINKU_HADOKEN_PROJECTILE_START_INDEX: int = 1
SHINKU_HADOKEN_PROJECTILE_END_INDEX: int = 7
SHINKU_HADOKEN_SPAWN_FRAME_INDEX: int = 5
SUPER_FREEZE_FRAMES: int = 30

# Power Gauge
POWER_GAUGE_MAX: int = 1000
POWER_GAUGE_SEGMENTS: int = 10
POWER_GAUGE_SHINKU_COST_SEGMENTS: int = 5
POWER_GAUGE_SUPER_COST: int = int((POWER_GAUGE_MAX / max(1, POWER_GAUGE_SEGMENTS)) * POWER_GAUGE_SHINKU_COST_SEGMENTS)
POWER_GAIN_ON_HIT: int = 50
POWER_GAIN_ON_GUARD: int = 20
POWER_GAIN_ON_SPECIAL_USE: int = 10
POWER_GAIN_ON_TAKE_DAMAGE_RATIO: float = 0.20

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
        "damage": 55,
        "duration_frames": 12,
        "hitbox_width": 38,
        "hitbox_height": 22,
        "hitbox_offset_x": 26,
        "hitbox_offset_y": 28,
        "knockback_px": 10,
        "hitstop_frames": 6,
    },
    "P1_I_MP": {
        "damage": 65,
        "duration_frames": 12,
        "hitbox_width": 38,
        "hitbox_height": 22,
        "hitbox_offset_x": 26,
        "hitbox_offset_y": 12,  # 中パンチ: 当たり判定を上に挙げる（18→12）
        "knockback_px": 10,
        "hitstop_frames": 6,
    },
    "P1_O_HP": {
        "damage": 40,
        "duration_frames": 17,
        "hitbox_width": 50,
        "hitbox_height": 25,
        "hitbox_offset_x": 25,
        "hitbox_offset_y": 10,  # 大パンチ: 当たり判定を上に挙げる（15→10）
        "knockback_px": 8,
        "hitstop_frames": 5,
        "recovery_bonus_frames": 6,
        "attacker_recoil_px": 4,
    },
    "P1_J_LK": {
        "damage": 110,
        "duration_frames": 16,
        "hitbox_width": 48,
        "hitbox_height": 28,
        "hitbox_offset_x": 30,
        "hitbox_offset_y": 18,
        "knockback_px": 16,
        "hitstop_frames": 8,
    },
    "P1_K_MK": {
        "damage": 95,
        "duration_frames": 16,
        "hitbox_width": 58,
        "hitbox_height": 24,
        "hitbox_offset_x": 34,
        "hitbox_offset_y": 24,
        "knockback_px": 16,
        "hitstop_frames": 8,
    },
    "P1_L_HK": {
        "damage": 75,
        "duration_frames": 14,
        "hitbox_width": 46,
        "hitbox_height": 22,
        "hitbox_offset_x": 30,
        "hitbox_offset_y": 26,
        "knockback_px": 12,
        "hitstop_frames": 7,
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

    "RUSH": {
        "damage": 90,
        "duration_frames": 18,
        "hitbox_width": 64,
        "hitbox_height": 28,
        "hitbox_offset_x": 42,
        "hitbox_offset_y": 30,
        "knockback_px": 18,
        "hitstop_frames": 8,
        "recovery_bonus_frames": 10,
        "attacker_recoil_px": 0,
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

COMBO_DISPLAY_SECONDS: float = 2.5
COMBO_DISPLAY_FRAMES: int = int(2.5 * FPS)

HADOKEN_ACTION_ID: int = 6040
HADOKEN_SPAWN_DELAY_FRAMES: int = 20
HADOKEN_ACTION_LAST_FRAME_TIME: int = 40


def get_damage_multiplier(combo_count: int) -> float:
    c = max(1, int(combo_count))
    # 1 hit: 100%, 2+ hits: -10% each, min 10%
    mul = 1.0 - 0.1 * float(c - 1)
    return max(0.1, mul)

# Colors (RGB)
# ここでは見やすさを優先した暫定色を使います。
COLOR_BG = (25, 25, 25)
COLOR_P1 = (40, 90, 220)
COLOR_P2 = (220, 60, 60)

COLOR_HURTBOX = (60, 200, 255)
COLOR_PUSHBOX = (80, 160, 255)
COLOR_HITBOX = (255, 50, 50)
