from __future__ import annotations

from src.characters.definition import CharacterDefinition, SpecialSpec
from src.utils import constants


RYUKO = CharacterDefinition(
    name="RYUKO",
    attack_action_map={
        "P1_U_LP": 400,
        "P1_I_MP": 200,
        "P1_O_HP": 210,
        "P1_J_LK": 229,
        "P1_K_MK": 430,
        "P1_L_HK": 410,
        "P2_L_PUNCH": 200,
    },
    punch_attack_ids={"P1_U_LP", "P1_I_MP", "P1_O_HP", "P2_L_PUNCH"},
    kick_attack_ids={"P1_J_LK", "P1_K_MK", "P1_L_HK"},
    rush_attack_ids={"P1_J_LK", "P1_K_MK", "P1_L_HK"},
    rush_action_id=6520,
    rush_sprite_key=(6520, 2),
    hadoken_action_candidates=[6040, 3000, 3050],
    shinku_action_candidates=[int(getattr(constants, "SHINKU_HADOKEN_ACTION_ID", 8000))],
    specials=[
        SpecialSpec(
            key="SHUNGOKUSATSU",
            sequences=[["BTN:P", "BTN:P", "DIR:F", "BTN:K", "BTN:P"]],
            immediate_attack_ids={"P1_U_LP", "P1_I_MP", "P1_O_HP", "P2_L_PUNCH", "P1_J_LK", "P1_K_MK", "P1_L_HK"},
            early_consume_key="punch_shinku",
            requires_power=False,
        ),

        # Priority: rush > shinku > hadoken (matches prior behavior where rush is checked early)
        SpecialSpec(
            key="RUSH",
            sequences=[["DIR:DB", "BTN:K"]],
            immediate_attack_ids={"P1_J_LK", "P1_K_MK", "P1_L_HK"},
            early_consume_key="kick_rush",
            requires_power=False,
        ),
        SpecialSpec(
            key="SHINKU_HADOKEN",
            sequences=[
                ["DIR:D", "DIR:DF", "DIR:F", "DIR:D", "DIR:DF", "DIR:F", "BTN:P"],
                ["DIR:D", "DIR:F", "DIR:D", "DIR:F", "BTN:P"],
            ],
            immediate_attack_ids={"P1_U_LP", "P1_I_MP", "P1_O_HP", "P2_L_PUNCH"},
            early_consume_key="punch_shinku",
            requires_power=True,
        ),
        SpecialSpec(
            key="HADOKEN",
            sequences=[["DIR:D", "DIR:DF", "DIR:F", "BTN:P"], ["DIR:D", "DIR:F", "BTN:P"]],
            immediate_attack_ids={"P1_U_LP", "P1_I_MP", "P1_O_HP", "P2_L_PUNCH"},
            early_consume_key="punch_hadoken",
            requires_power=False,
        ),
    ],
)
