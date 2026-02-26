from __future__ import annotations

from src.characters.definition import CharacterDefinition, SpecialSpec
from src.characters.frame_data import RYUKO_FRAME_DATA
from src.utils import constants


RYUKO = CharacterDefinition(
    name="RYUKO",
    
    # ============================================================
    # 通常技のアニメーション設定（キー入力 → AIR アクションID）
    # ============================================================
    # Guilty Gear Strive方式: P/K/S/HS/D の5ボタン
    # 形式: "攻撃ID": アニメーションID(AIR action番号)
    attack_action_map={
        # --- GG Strive ボタン配置 ---
        "P1_P": 400,    # Uキー: P (Punch) → AIR action 400
        "P1_K": 229,    # Jキー: K (Kick) → AIR action 229
        "P1_S": 209,    # Iキー: S (Slash) → AIR action 209
        "P1_HS": 6570,  # Kキー: HS (Heavy Slash) 砂ぼこり攻撃 → AIR action 6570 (frames 6430-23~28) + エフェクト 6540 (frames 1-17)
        "P1_D": 6000,   # Oキー: D (Dust Attack) 足を振り上げる攻撃 → AIR action 6000 (frames 6000-8~18)
        
        # --- P2デフォルト ---
        "P2_ATTACK": 200,  # P2デフォルト攻撃 → AIR action 200
    },
    
    # ============================================================
    # 入力分類（コマンド技の判定用）
    # ============================================================
    # GG Strive方式: P/S/D系とK/HS系に分類
    punch_attack_ids={"P1_P", "P1_S", "P1_D", "P2_ATTACK"},  # パンチ系ボタン（P, S, D）
    kick_attack_ids={"P1_K", "P1_HS"},  # キック系ボタン（K, HS）
    
    # ============================================================
    # 特殊技: 突進（RUSH）
    # ============================================================
    # コマンド: ↙ + キック
    rush_attack_ids={"P1_K", "P1_HS"},  # 突進技の入力判定に使うキック（K, HS）
    rush_action_id=6520,          # 突進アニメーション: AIR action 6520
    rush_sprite_key=(6520, 2),    # 突進スプライト: group 6520, index 2
    
    # ============================================================
    # 特殊技: 波動拳（HADOKEN）
    # ============================================================
    # コマンド: ↓↘→ + パンチ
    hadoken_action_candidates=[6040, 3000, 3050],  # 波動拳アニメーション候補: AIR action 6040/3000/3050
    
    # ============================================================
    # 特殊技: 真空波動拳（SHINKU HADOKEN）
    # ============================================================
    # コマンド: ↓↘→↓↘→ + パンチ（ゲージ消費）
    shinku_action_candidates=[int(getattr(constants, "SHINKU_HADOKEN_ACTION_ID", 8000))],  # 真空波動拳: AIR action 8000
    
    # ============================================================
    # 特殊技コマンド定義
    # ============================================================
    # 優先順位: 瞬獄殺 > 突進 > 真空波動拳 > 波動拳
    specials=[
        # --------------------------------------------------------
        # 瞬獄殺（SHUNGOKUSATSU）
        # --------------------------------------------------------
        # コマンド: P・P・→・K・P (GG Strive方式)
        # アニメーション: constants.SHUNGOKU_ACTION_ID で定義
        SpecialSpec(
            key="SHUNGOKUSATSU",
            sequences=[["BTN:P", "BTN:P", "DIR:F", "BTN:K", "BTN:P"]],
            immediate_attack_ids={"P1_P", "P1_S", "P1_D", "P2_ATTACK", "P1_K", "P1_HS"},
            early_consume_key="punch_shinku",
            requires_power=False,  # ゲージ不要（HP 20%以下で発動可能）
        ),

        # --------------------------------------------------------
        # 突進（RUSH）
        # --------------------------------------------------------
        # コマンド: ↙ + キック
        # アニメーション: AIR action 6520（上記 rush_action_id で定義）
        SpecialSpec(
            key="RUSH",
            sequences=[["DIR:DB", "BTN:K"]],
            immediate_attack_ids={"P1_K", "P1_HS"},
            early_consume_key="kick_rush",
            requires_power=False,
        ),
        
        # --------------------------------------------------------
        # 真空波動拳（SHINKU HADOKEN）
        # --------------------------------------------------------
        # コマンド: ↓↘→↓↘→ + パンチ または ↓→↓→ + パンチ
        # アニメーション: AIR action 8000（上記 shinku_action_candidates で定義）
        SpecialSpec(
            key="SHINKU_HADOKEN",
            sequences=[
                ["DIR:D", "DIR:DF", "DIR:F", "DIR:D", "DIR:DF", "DIR:F", "BTN:P"],  # ↓↘→↓↘→P
                ["DIR:D", "DIR:F", "DIR:D", "DIR:F", "BTN:P"],                      # ↓→↓→P（簡易版）
            ],
            immediate_attack_ids={"P1_P", "P1_S", "P1_D", "P2_ATTACK"},
            early_consume_key="punch_shinku",
            requires_power=True,  # ゲージ消費あり
        ),
        
        # --------------------------------------------------------
        # 波動拳（HADOKEN）
        # --------------------------------------------------------
        # コマンド: ↓↘→ + パンチ または ↓→ + パンチ
        # アニメーション: AIR action 6040/3000/3050（上記 hadoken_action_candidates で定義）
        SpecialSpec(
            key="HADOKEN",
            sequences=[
                ["DIR:D", "DIR:DF", "DIR:F", "BTN:P"],  # ↓↘→P
                ["DIR:D", "DIR:F", "BTN:P"],            # ↓→P（簡易版）
            ],
            immediate_attack_ids={"P1_P", "P1_S", "P1_D", "P2_ATTACK"},
            early_consume_key="punch_hadoken",
            requires_power=False,
        ),
    ],
    
    # ============================================================
    # フレームデータ参照
    # ============================================================
    # 各技の詳細なフレームデータは frame_data.py で定義
    frame_data=RYUKO_FRAME_DATA,
)
