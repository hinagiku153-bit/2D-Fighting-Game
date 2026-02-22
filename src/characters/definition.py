from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SpecialSpec:
    key: str

    # List of acceptable token sequences.
    # Each sequence is matched backwards against Player.input_buffer tokens.
    # Example: ["DIR:D", "DIR:DF", "DIR:F", "BTN:P"]
    sequences: list[list[str]]

    # If the player pressed an attack in this set on the current frame,
    # we try to trigger the special immediately.
    immediate_attack_ids: set[str]

    # Which buffered-button timestamp to consume for early-input triggering.
    # - "kick_rush": consume_recent_kick_for_rush
    # - "punch_hadoken": consume_recent_punch_for_hadoken
    # - "punch_shinku": consume_recent_punch_for_shinku
    early_consume_key: str

    # If True, this special requires power and should spend `super_cost`.
    requires_power: bool = False


@dataclass(frozen=True)
class CharacterDefinition:
    name: str

    # Normal attacks (input attack_id -> AIR action_id)
    attack_action_map: dict[str, int]

    # Input classification for command buffer (attack_id -> BTN token)
    punch_attack_ids: set[str]
    kick_attack_ids: set[str]

    # Rush special
    rush_attack_ids: set[str]
    rush_action_id: int
    rush_sprite_key: tuple[int, int]

    # Hadoken special
    hadoken_action_candidates: list[int]

    # Shinku Hadoken special
    shinku_action_candidates: list[int]

    # Special command table (character-specific)
    specials: list[SpecialSpec]
