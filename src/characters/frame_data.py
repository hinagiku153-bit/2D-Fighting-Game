from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AttackFrameData:
    """
    攻撃のフレームデータ定義。
    
    各攻撃の詳細なフレーム情報とヒット/ガード時の有利フレームを定義します。
    """
    # 攻撃ID（例: "P1_U_LP", "P1_I_MP"）
    attack_id: str
    
    # ダメージ
    damage: int
    
    # === フレーム情報 ===
    # 発生フレーム: 攻撃開始から当たり判定が出るまでのフレーム数
    startup_frames: int
    
    # 持続フレーム: 当たり判定が出ている期間のフレーム数
    active_frames: int
    
    # 硬直フレーム: 攻撃後の隙（recovery）のフレーム数
    recovery_frames: int
    
    # === ヒット/ガード時の有利フレーム ===
    # ヒット時有利フレーム: 正の値なら攻撃側が有利、負の値なら不利
    # 例: +3 なら攻撃側が3フレーム先に動ける、-2なら防御側が2フレーム先に動ける
    hit_advantage: int
    
    # ガード時有利フレーム: 正の値なら攻撃側が有利、負の値なら不利
    # 通常、ガード時は攻撃側が不利になることが多い（例: -2, -5など）
    guard_advantage: int
    
    # === ヒット時の挙動 ===
    # ノックバック距離（px）
    knockback_px: int
    
    # ヒットストップフレーム数
    hitstop_frames: int
    
    # ヒットストン（のけぞり）フレーム数
    # hit_advantage と連動: hitstun_frames - recovery_frames = hit_advantage
    hitstun_frames: int
    
    # ガードストン（ガード硬直）フレーム数
    # guard_advantage と連動: blockstun_frames - recovery_frames = guard_advantage
    blockstun_frames: int
    
    # === その他 ===
    # 攻撃側の反動（押し戻し）距離（px）
    attacker_recoil_px: int = 1
    
    # 追加の硬直フレーム（特定の技で使用）
    recovery_bonus_frames: int = 0
    
    # ガード時のチップダメージ比率（0.0-1.0）
    chip_damage_ratio: float = 0.0
    
    # ヒット時にダウンさせるか
    causes_knockdown: bool = False
    
    # === 当たり判定（Hitbox）の形状と位置 ===
    # 当たり判定の幅（px）
    hitbox_width: int = 40
    
    # 当たり判定の高さ（px）
    hitbox_height: int = 25
    
    # 当たり判定のX方向オフセット（キャラクターの中心からの距離、px）
    hitbox_offset_x: int = 30
    
    # 当たり判定のY方向オフセット（キャラクターの上端からの距離、px）
    hitbox_offset_y: int = 20
    
    # === 入力視覚インジケーター ===
    # 入力から何フレーム後に視覚的な赤枠を表示するか（0なら即座、Nなら入力後Nフレーム）
    # これは実際のヒット判定とは別で、入力受付を視覚的に示すためのもの
    input_visual_frame: int = 0
    
    # === アニメーション速度 ===
    # アニメーション再生速度の倍率（1.0 = 通常速度、0.5 = 半分の速度、2.0 = 2倍速）
    # 小数点第一位まで設定可能（例: 0.8, 1.2, 1.5など）
    animation_speed: float = 1.0


# RYUKOキャラクターのフレームデータ定義
RYUKO_FRAME_DATA: dict[str, AttackFrameData] = {
    # 小パンチ（Uキー）
    "P1_U_LP": AttackFrameData(
        attack_id="P1_U_LP",
        damage=55,
        startup_frames=4,      # 小パンチ: 発生フレーム
        active_frames=4,       # 小パンチ: 持続フレーム
        recovery_frames=7,     # 小パンチ: 硬直フレーム
        hit_advantage=+4,      # 小パンチ: ヒット時
        guard_advantage=-1,    # 小パンチ: ガード時
        knockback_px=10,
        hitstop_frames=6,
        hitstun_frames=10,     # recovery(6) + hit_advantage(+4) = 10
        blockstun_frames=5,    # recovery(6) + guard_advantage(-1) = 5
        attacker_recoil_px=0,
        hitbox_width=15,
        hitbox_height=22,
        hitbox_offset_x=0,
        hitbox_offset_y=28,
        input_visual_frame=0,  # 入力直後に視覚インジケーター表示
        animation_speed=1.0,
    ),
    
    # 中パンチ（Iキー）
    "P1_I_MP": AttackFrameData(
        attack_id="P1_I_MP",
        damage=65,
        startup_frames=9,      # 中パンチ: 発生フレーム
        active_frames=6,       # 中パンチ: 持続フレーム
        recovery_frames=5,     # 中パンチ: 硬直フレーム
        hit_advantage=+7,      # 中パンチ: ヒット時
        guard_advantage=-1,    # 中パンチ: ガード時
        knockback_px=10,
        hitstop_frames=6,
        hitstun_frames=15,     # recovery(8) + hit_advantage(+7) = 15
        blockstun_frames=7,    # recovery(8) + guard_advantage(-1) = 7
        attacker_recoil_px=1,
        hitbox_width=50,
        hitbox_height=22,
        hitbox_offset_x=0,
        hitbox_offset_y=5,
        input_visual_frame=0,  # 入力直後に視覚インジケーター表示
        animation_speed=1.3,
    ),
    
    # 大パンチ（Oキー）
    "P1_O_HP": AttackFrameData(
        attack_id="P1_O_HP",
        damage=40,
        startup_frames=8,      # 大パンチ: 発生フレーム（8F発生）
        active_frames=5,       # 大パンチ: 持続フレーム
        recovery_frames=8,    # 大パンチ: 硬直フレーム
        hit_advantage=+2,      # 大パンチ: ヒット時+2F有利
        guard_advantage=-4,    # 大パンチ: ガード時-5F不利
        knockback_px=8,
        hitstop_frames=5,
        hitstun_frames=12,     # recovery(10) + hit_advantage(+2) = 12
        blockstun_frames=5,    # recovery(10) + guard_advantage(-5) = 5
        attacker_recoil_px=1,
        recovery_bonus_frames=6,
        hitbox_width=58,
        hitbox_height=32,
        hitbox_offset_x=36,
        hitbox_offset_y=46,
        causes_knockdown=True,
        input_visual_frame=0,
        animation_speed=1.0,
    ),
    
    # 小キック（Jキー）
    "P1_J_LK": AttackFrameData(
        attack_id="P1_J_LK",
        damage=110,
        startup_frames=5,      # 小キック: 発生フレーム
        active_frames=2,       # 小キック: 持続フレーム
        recovery_frames=8,     # 小キック: 硬直フレーム
        hit_advantage=+2,      # 小キック: ヒット時+F有利
        guard_advantage=-2,    # 小キック: ガード時-F不利
        knockback_px=16,
        hitstop_frames=8,
        hitstun_frames=13,     # recovery(8) + hit_advantage(+5) = 13
        blockstun_frames=6,    # recovery(8) + guard_advantage(-2) = 6
        attacker_recoil_px=3,
        hitbox_width=48,
        hitbox_height=28,
        hitbox_offset_x=32,
        hitbox_offset_y=50,
        input_visual_frame=0,
        animation_speed=1.0,
    ),
    
    # 中キック（Kキー）
    "P1_K_MK": AttackFrameData(
        attack_id="P1_K_MK",
        damage=95,
        startup_frames=6,      # 中キック: 発生フレーム
        active_frames=5,       # 中キック: 持続フレーム
        recovery_frames=10,    # 中キック: 硬直フレーム
        hit_advantage=+4,      # 中キック: ヒット時+4F有利
        guard_advantage=-3,    # 中キック: ガード時-3F不利
        knockback_px=16,
        hitstop_frames=8,
        hitstun_frames=14,     # recovery(10) + hit_advantage(+4) = 14
        blockstun_frames=7,    # recovery(10) + guard_advantage(-3) = 7
        attacker_recoil_px=3,
        hitbox_width=52,
        hitbox_height=30,
        hitbox_offset_x=34,
        hitbox_offset_y=48,
        input_visual_frame=0,
        animation_speed=1.0,
    ),
    
    # 大キック（Lキー）
    "P1_L_HK": AttackFrameData(
        attack_id="P1_L_HK",
        damage=75,
        startup_frames=5,      # 大キック: 発生フレーム
        active_frames=4,       # 大キック: 持続フレーム
        recovery_frames=9,     # 大キック: 硬直フレーム
        hit_advantage=+3,      # 大キック: ヒット時+3F有利
        guard_advantage=-4,    # 大キック: ガード時-4F不利
        knockback_px=12,
        hitstop_frames=7,
        hitstun_frames=12,     # recovery(9) + hit_advantage(+3) = 12
        blockstun_frames=5,    # recovery(9) + guard_advantage(-4) = 5
        attacker_recoil_px=3,
        hitbox_width=35,
        hitbox_height=25,
        hitbox_offset_x=30,
        hitbox_offset_y=20,
        input_visual_frame=0,
        animation_speed=1.0,
    ),
    
    # P2デフォルト攻撃（仮）
    "P2_L_PUNCH": AttackFrameData(
        attack_id="P2_L_PUNCH",
        damage=50,
        startup_frames=3,
        active_frames=3,
        recovery_frames=6,
        hit_advantage=+2,
        guard_advantage=-2,
        knockback_px=12,
        hitstop_frames=6,
        hitstun_frames=8,
        blockstun_frames=4,
        attacker_recoil_px=3,
        hitbox_width=35,
        hitbox_height=25,
        hitbox_offset_x=30,
        hitbox_offset_y=20,
        input_visual_frame=0,  # 入力直後に視覚インジケーター表示
        animation_speed=1.0,
    ),
    
    # 突進技
    "RUSH": AttackFrameData(
        attack_id="RUSH",
        damage=90,
        startup_frames=6,
        active_frames=18,
        recovery_frames=12,
        hit_advantage=+10,
        guard_advantage=-6,
        knockback_px=18,
        hitstop_frames=8,
        hitstun_frames=22,
        blockstun_frames=6,
        attacker_recoil_px=0,
        recovery_bonus_frames=10,
        causes_knockdown=True,  # 突進攻撃はヒット時にダウンさせる
        hitbox_width=60,
        hitbox_height=40,
        hitbox_offset_x=40,
        hitbox_offset_y=30,
        input_visual_frame=0,
        animation_speed=1.0,
    ),
}
