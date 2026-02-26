from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import Enum, auto
import math
import importlib.util
import os
import random
from typing import Any

import pygame

from src.engine.context import GameState, FrameState, FrameSample, FrameDataTracker, ShungokuState
from src.engine.settings import (
    load_settings,
    save_settings,
    load_keybinds,
    save_keybinds,
    key_name as _key_name,
    DEFAULT_KEYBINDS,
)
from src.rendering.stage_renderer import StageRenderer
from src.rendering.hud_renderer import HUDRenderer
from src.systems.collision import CollisionSystem
from src.systems.combat import CombatSystem
from src.systems.projectile_system import ProjectileSystem
from src.systems.shungoku import ShungokuManager
from src.assets.sound_manager import SoundManager
from src.assets.asset_manager import AssetManager
from src.entities.effect import Effect
from src.entities.effect import StaticImageBurstEffect
from src.entities.effect import Projectile
from src.entities.effect import SuperProjectile
from src.entities.player import Player, PlayerInput
from src.entities.player_animator import PlayerAnimator
from src.characters.ryuko import RYUKO
from src.ui.command_list import CommandListMenu
from src.utils import constants
from src.utils.paths import resource_path



def main() -> None:
    # Pygame 初期化。
    pygame.init()
    # メニュー操作でキー長押しリピートを有効化（初回300ms、以降50ms間隔）。
    pygame.key.set_repeat(300, 50)

    settings = load_settings()
    bgm_volume_level = int(settings.get("bgm_volume_level", 70))
    bgm_volume_level = max(0, min(100, bgm_volume_level))

    se_volume_level = int(settings.get("se_volume_level", 60))
    se_volume_level = max(0, min(100, se_volume_level))

    frame_meter_enabled = bool(settings.get("frame_meter_enabled", True))

    keybinds: dict[str, int] = load_keybinds(settings)

    def _save_keybinds() -> None:
        save_keybinds(settings, keybinds)

    def _save_settings(data: dict[str, Any]) -> None:
        save_settings(data)

    jp_font_path = resource_path("assets/fonts/TogeMaruGothic-700-Bold.ttf")
    mono_font_name = "consolas"
    if jp_font_path.exists():
        font = pygame.font.Font(str(jp_font_path), 28)
        title_font = pygame.font.Font(str(jp_font_path), 72)
        prompt_font = pygame.font.Font(str(jp_font_path), 32)
        keycfg_font = pygame.font.Font(str(jp_font_path), 26)
        debug_font = pygame.font.Font(str(jp_font_path), 22)
        frame_meter_adv_font = pygame.font.Font(str(jp_font_path), 36)
        menu_font = pygame.font.SysFont(mono_font_name, 34)
    else:
        font = pygame.font.SysFont("meiryo", 28)
        title_font = pygame.font.SysFont("meiryo", 72)
        prompt_font = pygame.font.SysFont("meiryo", 32)
        keycfg_font = pygame.font.SysFont("meiryo", 26)
        debug_font = pygame.font.SysFont("meiryo", 22)
        frame_meter_adv_font = pygame.font.SysFont("meiryo", 36)
        menu_font = pygame.font.SysFont(mono_font_name, 34)

    stage_renderer = StageRenderer(rain_count=90)
    hud_renderer = HUDRenderer(
        title_font=title_font,
        prompt_font=prompt_font,
        debug_font=debug_font,
        frame_meter_adv_font=frame_meter_adv_font,
    )

    # 画面作成とフレーム管理用の Clock。
    # 画面（ウィンドウ）サイズは可変だが、ステージ（論理解像度）は固定にする。
    screen = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
    pygame.display.set_caption(constants.GAME_TITLE)
    clock = pygame.time.Clock()

    # ステージ（論理解像度）への描画先。ここにゲームを描いて、最後にウィンドウへ拡大して表示する。
    stage_surface = pygame.Surface((constants.STAGE_WIDTH, constants.STAGE_HEIGHT)).convert()

    # 解像度候補（ゲーム内で切り替え可能）。
    resolutions: list[tuple[int, int]] = [
        (800, 450),
        (1280, 720),
        (1600, 900),
        (1920, 1080),
    ]
    try:
        current_res_index = resolutions.index((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
    except ValueError:
        current_res_index = 0

    # プレイヤー生成。
    # Phase 1 は「塗りつぶし矩形」だけでキャラクターを表現する。
    p1 = Player(x=150, color=constants.COLOR_P1, character=RYUKO)
    p2 = Player(x=constants.STAGE_WIDTH - 200, color=constants.COLOR_P2, character=RYUKO)

    actions_by_id: dict[int, dict[str, Any]] = {}

    # MUGENの AIR（ACTIONS）と、整理済みPNG（organized）を読み込む。
    # 読み込みに失敗した場合でもゲームは起動でき、従来の矩形描画にフォールバックする。
    try:
        air_py = resource_path("assets/images/RYUKO2nd/ryuko_air_actions.py")
        sprites_root = resource_path("assets/images/RYUKO2nd/organized")

        spec = importlib.util.spec_from_file_location("ryuko_air_actions", str(air_py))
        if spec is not None and spec.loader is not None:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            actions = getattr(module, "ACTIONS", None)
            if isinstance(actions, list):
                PlayerAnimator.apply_all_patches(actions)
                if not PlayerAnimator.actions_have_frame_clsns(actions):
                    air_parser_py = resource_path("scripts/organize_ryuko2nd_assets.py")
                    air_file = resource_path("assets/images/RYUKO2nd/RYUKO.AIR")
                    parser_spec = importlib.util.spec_from_file_location("ryuko_air_parser", str(air_parser_py))
                    if parser_spec is not None and parser_spec.loader is not None:
                        parser_module = importlib.util.module_from_spec(parser_spec)
                        parser_spec.loader.exec_module(parser_module)
                        parse_air_file = getattr(parser_module, "parse_air_file", None)
                        if callable(parse_air_file):
                            parsed_actions = parse_air_file(air_file)
                            if isinstance(parsed_actions, list):
                                actions = parsed_actions
                                PlayerAnimator.apply_all_patches(actions)
                actions_by_id = {int(a.get("action")): a for a in actions if isinstance(a, dict) and "action" in a}
                p1.set_mugen_animation(actions=actions, sprites_root=sprites_root)
                p2.set_mugen_animation(actions=actions, sprites_root=sprites_root)
    except Exception:
        pass
    
    # CommandListMenuを初期化
    if actions_by_id:
        command_list_menu = CommandListMenu(actions_by_id=actions_by_id)
    else:
        command_list_menu = CommandListMenu(actions_by_id={})

    # すべてのゲームアセットを一括読み込み
    assets = AssetManager.load_all_assets(p1, p2)
    
    effects: list[Effect] = []
    projectiles: list[Projectile] = []

    # 判定枠線（Hurtbox/Pushbox/Hitbox）を描画するかどうか。
    # F3 で切り替える。
    debug_draw = bool(settings.get("debug_draw", constants.DEBUG_DRAW_DEFAULT))
    debug_show_grid = bool(settings.get("debug_show_grid", False))

    debugmenu_open = False
    debugmenu_selection = 0
    debug_ui_show_key_history = bool(settings.get("debug_ui_show_key_history", True))
    debug_ui_show_p1_frames = bool(settings.get("debug_ui_show_p1_frames", True))
    debug_ui_show_p2_frames = bool(settings.get("debug_ui_show_p2_frames", True))

    # ESC で表示する簡易メニュー。
    menu_open = False
    menu_selection = 0

    keyconfig_open = False
    keyconfig_selection = 0
    keyconfig_waiting_action: str | None = None
    keyconfig_scroll_left = 0
    keyconfig_scroll_right = 0

    training_settings_open = False
    training_settings_selection = 0
    training_settings_scroll = 0
    training_hp_percent_p1 = 100
    training_hp_percent_p2 = 100
    training_sp_percent_p1 = 100
    training_sp_percent_p2 = 100
    training_p2_all_guard = False
    training_auto_recover_hp = False
    training_auto_recover_sp = False

    training_p2_state_lock = 0
    training_start_position = 0

    frame_meter_p1 = FrameDataTracker(max_frames=120)
    frame_meter_p2 = FrameDataTracker(max_frames=120)
    frame_meter_adv_value: int | None = None
    frame_meter_adv_frames_left: int = 0
    frame_meter_adv_attacker_side: int = 0
    frame_meter_paused: bool = False
    frame_meter_idle_run: int = 0

    frame_meter_last_action_id_p1: int | None = None
    frame_meter_last_action_id_p2: int | None = None
    frame_meter_last_action_fc_p1: int = 0
    frame_meter_last_action_fc_p2: int = 0
    frame_meter_synth_action_fc_p1: int = 0
    frame_meter_synth_action_fc_p2: int = 0

    shungoku_state = ShungokuState()
    stage_bg_override_img: pygame.Surface | None = None
    bgm_suspended: bool = False
    shungoku_start_queued_side: int = 0
    shungoku_posthit_lock_side: int = 0
    shungoku_posthit_lock_defender_side: int = 0
    
    # Compatibility aliases for shungoku state
    shungoku_cine_frames_left = shungoku_state.cine_frames_left
    shungoku_attacker_side = shungoku_state.attacker_side
    shungoku_defender_side = shungoku_state.defender_side
    shungoku_ko_anim_side = shungoku_state.ko_anim_side
    shungoku_ko_anim_idx = shungoku_state.ko_anim_idx
    shungoku_ko_anim_tick = shungoku_state.ko_anim_tick
    shungoku_pending_apply = shungoku_state.pending_apply
    shungoku_pending_damage = shungoku_state.pending_damage
    shungoku_pending_ko = shungoku_state.pending_ko
    shungoku_pan_frames_left = shungoku_state.pan_frames_left
    shungoku_pan_target_px = shungoku_state.pan_target_px
    shungoku_hit_se_cooldown = shungoku_state.hit_se_cooldown
    shungoku_flash_frames_left = shungoku_state.flash_frames_left
    shungoku_finish_frames_left = shungoku_state.finish_frames_left
    shungoku_super_se_cooldown = shungoku_state.super_se_cooldown
    shungoku_ko_anim_frames_per_image = shungoku_state.ko_anim_frames_per_image
    shungoku_pan_total_frames = shungoku_state.pan_total_frames

    keyconfig_actions: list[tuple[str, str]] = [
        ("P1 左", "P1_LEFT"),
        ("P1 右", "P1_RIGHT"),
        ("P1 下", "P1_DOWN"),
        ("P1 ジャンプ", "P1_JUMP"),
        ("P1 P (Punch)", "P1_P"),
        ("P1 K (Kick)", "P1_K"),
        ("P1 S (Slash)", "P1_S"),
        ("P1 HS (Heavy Slash)", "P1_HS"),
        ("P1 D (Dust)", "P1_D"),
        ("P2 左", "P2_LEFT"),
        ("P2 右", "P2_RIGHT"),
        ("P2 下", "P2_DOWN"),
        ("P2 ジャンプ", "P2_JUMP"),
        ("P2 攻撃", "P2_ATTACK"),
        ("フィールドリセット(トレモ専用)", "FIELD_RESET"),
    ]

    # CommandListMenuインスタンスを作成（actions_by_id読み込み後に初期化）
    command_list_menu: CommandListMenu | None = None

    # タイトル画面とバトル画面の状態管理。
    game_state = GameState.TITLE
    title_start_keys = {pygame.K_u, pygame.K_i, pygame.K_o, pygame.K_j, pygame.K_k, pygame.K_l}
    title_menu_items = ["BATTLE", "TRAINING", "SETTING", "EXIT"]
    title_menu_selection = 0

    char_select_items = ["P2", "START", "BACK"]
    char_select_selection = 0
    char_select_p2_cpu: bool = True
    char_select_next_state: GameState = GameState.BATTLE
    char_select_thumb: pygame.Surface | None = None

    result_menu_items = ["rematch", "back_to_title", "exit"]
    result_menu_selection = 0
    result_winner_side: int | None = None
    result_bg_frames: list[pygame.Surface] = []
    result_anim_counter: int = 0

    round_timer_frames_left: int | None = None

    p1_round_wins: int = 0
    p2_round_wins: int = 0
    round_over_frames_left: int = 0
    round_over_winner_side: int | None = None

    battle_countdown_frames_left: int = 0
    battle_countdown_last_announce: int | None = None

    # 背景画像はassetsから取得
    stage_bg_img = assets.stage_bg_img
    stage_bg_frames: list[pygame.Surface] = stage_renderer.stage_bg_frames
    rain_drops = stage_renderer.rain_drops

    sound_manager = SoundManager()
    sound_manager.se_volume_level = se_volume_level
    sound_manager.bgm_volume_level = bgm_volume_level
    sound_manager.apply_se_volume()
    sound_manager.apply_bgm_volume()

    # SE/BGM aliases for compatibility
    start_se = sound_manager.start_se
    menu_confirm_se = sound_manager.menu_confirm_se
    menu_move_se = sound_manager.menu_move_se
    countdown_se_3 = sound_manager.countdown_se_3
    countdown_se_2 = sound_manager.countdown_se_2
    countdown_se_1 = sound_manager.countdown_se_1
    countdown_se_go = sound_manager.countdown_se_go
    beam_se = sound_manager.beam_se
    hit_se = sound_manager.hit_se
    guard_se = sound_manager.guard_se

    combat_system = CombatSystem(
        spark_frames=assets.spark_frames,
        hit_fx_img=assets.hit_fx_img,
        guard_fx_img=assets.guard_fx_img,
        hit_se=hit_se,
        guard_se=guard_se,
    )

    projectile_system = ProjectileSystem(
        hadoken_frames=assets.hadoken_proj_frames,
        shinku_frames=assets.shinku_proj_frames,
        hit_fx_img=assets.hit_fx_img,
        guard_fx_img=assets.guard_fx_img,
        hit_se=hit_se,
        guard_se=guard_se,
    )

    shungoku_manager = ShungokuManager(
        shungoku_state=shungoku_state,
        shungoku_stage_bg_img=assets.shungoku_stage_bg_img,
        shungoku_asura_se=sound_manager.shungoku_asura_se,
        shungoku_super_se=sound_manager.shungoku_super_se,
        shungoku_ko_se=sound_manager.shungoku_ko_se,
        hit_se=hit_se,
        hit_fx_img=assets.hit_fx_img,
    )

    def _apply_se_volume() -> None:
        sound_manager.se_volume_level = se_volume_level
        sound_manager.apply_se_volume()

    def _apply_bgm_volume() -> None:
        sound_manager.bgm_volume_level = bgm_volume_level
        sound_manager.apply_bgm_volume()

    def _ensure_bgm_for_state(state: GameState) -> None:
        sound_manager.ensure_bgm_for_state(state)

    # タイトル背景はassetsから取得
    title_bg_img = assets.title_bg_img

    # “押した瞬間だけ True” にしたい入力は、KEYDOWN でトリガを立てて
    # フレームの先頭で False に戻す（エッジ入力）。
    p1_jump_pressed = False
    p2_jump_pressed = False
    p1_attack_id: str | None = None
    p2_attack_id: str | None = None

    p1_key_history: list[str] = []

    # HPバー用の「赤チップ残り」値（見た目用）。
    p1_chip_hp: float = float(p1.max_hp)
    p2_chip_hp: float = float(p2.max_hp)

    super_freeze_frames_left: int = 0
    super_freeze_attacker_side: int = 0

    shungoku_start_queued_side: int = 0

    cpu_enabled_battle: bool = True
    cpu_enabled_training: bool = False
    cpu_decision_frames_left: int = 0
    cpu_attack_cooldown: int = 0
    cpu_jump_cooldown: int = 0
    cpu_special_cooldown: int = 0

    def _apply_resolution(size: tuple[int, int]) -> None:
        nonlocal screen
        w, h = size

        # 画面（ウィンドウ）サイズだけを変更する。
        # ステージの広さ（constants.STAGE_*）や地面位置（constants.GROUND_Y）は固定。
        constants.SCREEN_WIDTH = int(w)
        constants.SCREEN_HEIGHT = int(h)

        screen = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))

    def reset_match() -> None:
        # デバッグ用の「試合リセット」。
        # - 位置、速度、HP、攻撃/ヒットストップ等を初期化する。
        # - debug_draw（F3 のON/OFF）は維持する。
        nonlocal p1_chip_hp, p2_chip_hp, round_timer_frames_left, battle_countdown_frames_left, battle_countdown_last_announce

        if game_state == GameState.TRAINING:
            preset = int(training_start_position)
            if preset == 1:
                p1.pos_x = float(140 + (p1.rect.width // 2))
                p2.pos_x = float(260 + (p2.rect.width // 2))
            elif preset == 2:
                p2.pos_x = float((constants.STAGE_WIDTH - 140) + (p2.rect.width // 2))
                p1.pos_x = float((constants.STAGE_WIDTH - 260) + (p1.rect.width // 2))
            else:
                center = float(constants.STAGE_WIDTH / 2)
                p1.pos_x = float(center - 90)
                p2.pos_x = float(center + 90)
        else:
            p1.pos_x = float(150 + (p1.rect.width // 2))
            p2.pos_x = float((constants.STAGE_WIDTH - 200) + (p2.rect.width // 2))
        p1.pos_y = float(constants.GROUND_Y)
        p2.pos_y = float(constants.GROUND_Y)
        p1.rect.midbottom = (int(p1.pos_x), int(p1.pos_y))
        p2.rect.midbottom = (int(p2.pos_x), int(p2.pos_y))

        p1.vel_x = 0.0
        p1.vel_y = 0.0
        p2.vel_x = 0.0
        p2.vel_y = 0.0
        p1.on_ground = True
        p2.on_ground = True
        p1.crouching = False
        p2.crouching = False

        p1.reset_round_state()
        p2.reset_round_state()

        if game_state == GameState.TRAINING:
            p1.hp = int(round(p1.max_hp * (float(training_hp_percent_p1) / 100.0)))
            p2.hp = int(round(p2.max_hp * (float(training_hp_percent_p2) / 100.0)))
        else:
            p1.hp = p1.max_hp
            p2.hp = p2.max_hp
        p1_chip_hp = float(p1.hp)
        p2_chip_hp = float(p2.hp)

        if game_state == GameState.TRAINING:
            max_sp = int(getattr(constants, "POWER_GAUGE_MAX", 1000))
            p1.power_gauge = int(round(max_sp * (float(training_sp_percent_p1) / 100.0)))
            p2.power_gauge = int(round(max_sp * (float(training_sp_percent_p2) / 100.0)))

        if game_state == GameState.BATTLE:
            round_timer_frames_left = int(constants.FPS * 99)
            battle_countdown_frames_left = int(constants.FPS * 3)
            battle_countdown_last_announce = None
        elif game_state == GameState.TRAINING:
            round_timer_frames_left = None
            battle_countdown_frames_left = 0
            battle_countdown_last_announce = None

        round_over_frames_left = 0
        round_over_winner_side = None

        p1.hitstop_frames_left = 0
        p2.hitstop_frames_left = 0
        p1._attack_frames_left = 0
        p2._attack_frames_left = 0
        p1._attack_has_hit = False
        p2._attack_has_hit = False
        p1._attack_id = None
        p2._attack_id = None

        nonlocal stage_bg_override_img, bgm_suspended, shungoku_cine_frames_left
        stage_bg_override_img = None
        bgm_suspended = False
        shungoku_cine_frames_left = 0

        # 阿修羅SEの停止はShungokuManagerが管理
        try:
            if shungoku_manager.asura_channel is not None:
                shungoku_manager.asura_channel.stop()
                shungoku_manager.asura_channel = None
        except Exception:
            pass

        nonlocal shungoku_ko_anim_side, shungoku_ko_anim_idx, shungoku_ko_anim_tick
        shungoku_ko_anim_side = 0
        shungoku_ko_anim_idx = 1
        shungoku_ko_anim_tick = 0

        nonlocal shungoku_pending_damage, shungoku_pending_apply, shungoku_pending_ko
        shungoku_pending_damage = 0
        shungoku_pending_apply = False
        shungoku_pending_ko = False

        nonlocal shungoku_posthit_lock_side, shungoku_posthit_lock_defender_side
        shungoku_posthit_lock_side = 0
        shungoku_posthit_lock_defender_side = 0

        nonlocal shungoku_pan_frames_left, shungoku_pan_target_px
        shungoku_pan_frames_left = 0
        shungoku_pan_target_px = 0

        nonlocal shungoku_start_queued_side
        shungoku_start_queued_side = 0

        nonlocal shungoku_super_se_cooldown
        shungoku_super_se_cooldown = 0

    _apply_resolution((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
    reset_match()

    _ensure_bgm_for_state(game_state)

    # フレームごとの時間制御
    frame_paused = False
    frame_advance = False

    running = True
    while running:
        # 毎フレーム、エッジ入力をリセット。
        p1_jump_pressed = False
        p2_jump_pressed = False
        p1_attack_id = None
        p2_attack_id = None

        # イベント処理：終了、デバッグ切り替え、ジャンプ/攻撃の押下（瞬間）入力。
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if bool(menu_open) and bool(keyconfig_open) and (keyconfig_waiting_action is not None):
                    if event.key == pygame.K_ESCAPE:
                        keyconfig_waiting_action = None
                        continue
                    keybinds[str(keyconfig_waiting_action)] = int(event.key)
                    _save_keybinds()
                    keyconfig_waiting_action = None
                    continue

                if event.key == pygame.K_F3:
                    if game_state == GameState.TRAINING:
                        debug_draw = not debug_draw
                    continue

                # Mキー: フレームポーズのトグル
                if event.key == pygame.K_m:
                    if game_state in {GameState.BATTLE, GameState.TRAINING}:
                        frame_paused = not frame_paused
                    continue

                # >キー: ポーズ中に1フレーム進める
                if event.key == pygame.K_PERIOD:  # >キー（Shiftなし）
                    if game_state in {GameState.BATTLE, GameState.TRAINING} and frame_paused:
                        frame_advance = True
                    continue

                if (
                    game_state == GameState.TRAINING
                    and (not bool(menu_open))
                    and event.key == int(keybinds.get("FIELD_RESET", keybinds.get("QUICK_RESET", pygame.K_r)))
                ):
                    reset_match()
                    continue

                if (
                    game_state in {GameState.BATTLE, GameState.TRAINING}
                    and (not bool(menu_open))
                    and event.key == pygame.K_h
                ):
                    mx = int(getattr(constants, "POWER_GAUGE_MAX", 1000))
                    p1.power_gauge = int(mx)
                    p1.start_shungokusatsu()
                    continue

                if game_state == GameState.RESULT:
                    if event.key == pygame.K_ESCAPE:
                        game_state = GameState.TITLE
                        menu_open = False
                        cmdlist_open = False
                        p1_round_wins = 0
                        p2_round_wins = 0
                        result_winner_side = None
                        result_anim_counter = 0
                        reset_match()
                        effects.clear()
                        projectile_system.projectiles.clear()
                        _ensure_bgm_for_state(game_state)
                        continue

                    if event.key in {pygame.K_UP, pygame.K_w}:
                        result_menu_selection = (result_menu_selection - 1) % len(result_menu_items)
                        if menu_move_se is not None:
                            menu_move_se.play()
                        continue
                    if event.key in {pygame.K_DOWN, pygame.K_s}:
                        result_menu_selection = (result_menu_selection + 1) % len(result_menu_items)
                        if menu_move_se is not None:
                            menu_move_se.play()
                        continue

                    if event.key == pygame.K_RETURN or event.key == pygame.K_u:
                        if menu_confirm_se is not None:
                            menu_confirm_se.play()

                        selected = result_menu_items[result_menu_selection]
                        if selected == "rematch":
                            game_state = GameState.BATTLE
                            debug_draw = False
                            menu_open = False
                            cmdlist_open = False
                            p1_round_wins = 0
                            p2_round_wins = 0
                            result_winner_side = None
                            result_anim_counter = 0
                            reset_match()
                            effects.clear()
                            projectiles.clear()
                            _ensure_bgm_for_state(game_state)
                        elif selected == "back_to_title":
                            game_state = GameState.TITLE
                            menu_open = False
                            cmdlist_open = False
                            p1_round_wins = 0
                            p2_round_wins = 0
                            result_winner_side = None
                            result_anim_counter = 0
                            reset_match()
                            effects.clear()
                            projectiles.clear()
                            _ensure_bgm_for_state(game_state)
                        elif selected == "exit":
                            running = False
                        continue

                if event.key == pygame.K_n and game_state in {GameState.BATTLE, GameState.TRAINING}:
                    super_cost = int(getattr(constants, "POWER_GAUGE_SUPER_COST", 500))
                    p1.power_gauge = int(getattr(constants, "POWER_GAUGE_MAX", 1000))
                    if p1.spend_power(super_cost):
                        p1.start_shinku_hadoken()
                        if beam_se is not None:
                            beam_se.play()
                        super_freeze_frames_left = int(getattr(constants, "SUPER_FREEZE_FRAMES", 30))
                        super_freeze_attacker_side = 1
                    continue

                if event.key in {
                    int(keybinds.get("P1_LEFT", pygame.K_a)),
                    int(keybinds.get("P1_DOWN", pygame.K_s)),
                    int(keybinds.get("P1_RIGHT", pygame.K_d)),
                    int(keybinds.get("P1_JUMP", pygame.K_w)),
                    int(keybinds.get("P1_LP", pygame.K_u)),
                    int(keybinds.get("P1_MP", pygame.K_i)),
                    int(keybinds.get("P1_HP", pygame.K_o)),
                    int(keybinds.get("P1_LK", pygame.K_j)),
                    int(keybinds.get("P1_MK", pygame.K_k)),
                    int(keybinds.get("P1_HK", pygame.K_l)),
                }:
                    name_map = {
                        int(keybinds.get("P1_LEFT", pygame.K_a)): "←",
                        int(keybinds.get("P1_DOWN", pygame.K_s)): "↓",
                        int(keybinds.get("P1_RIGHT", pygame.K_d)): "→",
                        int(keybinds.get("P1_JUMP", pygame.K_w)): "↑",
                        int(keybinds.get("P1_LP", pygame.K_u)): "U",
                        int(keybinds.get("P1_MP", pygame.K_i)): "I",
                        int(keybinds.get("P1_HP", pygame.K_o)): "O",
                        int(keybinds.get("P1_LK", pygame.K_j)): "J",
                        int(keybinds.get("P1_MK", pygame.K_k)): "K",
                        int(keybinds.get("P1_HK", pygame.K_l)): "L",
                    }
                    p1_key_history.insert(0, name_map.get(int(event.key), str(event.key)))
                    p1_key_history = p1_key_history[:16]

                if game_state == GameState.TITLE and menu_open:
                    if event.key == pygame.K_ESCAPE:
                        menu_open = False
                        keyconfig_open = False
                        keyconfig_waiting_action = None
                    elif event.key in {pygame.K_UP, pygame.K_w}:
                        menu_selection = (menu_selection - 1) % 5
                        if menu_move_se is not None:
                            menu_move_se.play()
                    elif event.key in {pygame.K_DOWN, pygame.K_s}:
                        menu_selection = (menu_selection + 1) % 5
                        if menu_move_se is not None:
                            menu_move_se.play()
                    elif event.key in {pygame.K_LEFT, pygame.K_a}:
                        if menu_selection == 0:
                            current_res_index = (current_res_index - 1) % len(resolutions)
                        elif menu_selection == 1:
                            bgm_volume_level = max(0, bgm_volume_level - 1)
                            settings["bgm_volume_level"] = int(bgm_volume_level)
                            _save_settings(settings)
                            _apply_bgm_volume()
                        elif menu_selection == 2:
                            se_volume_level = max(0, se_volume_level - 1)
                            settings["se_volume_level"] = int(se_volume_level)
                            _save_settings(settings)
                            _apply_se_volume()
                    elif event.key in {pygame.K_RIGHT, pygame.K_d}:
                        if menu_selection == 0:
                            current_res_index = (current_res_index + 1) % len(resolutions)
                        elif menu_selection == 1:
                            bgm_volume_level = min(100, bgm_volume_level + 1)
                            settings["bgm_volume_level"] = int(bgm_volume_level)
                            _save_settings(settings)
                            _apply_bgm_volume()
                        elif menu_selection == 2:
                            se_volume_level = min(100, se_volume_level + 1)
                            settings["se_volume_level"] = int(se_volume_level)
                            _save_settings(settings)
                            _apply_se_volume()
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_u:
                        if menu_confirm_se is not None:
                            menu_confirm_se.play()
                        if menu_selection == 0:
                            _apply_resolution(resolutions[current_res_index])
                            reset_match()
                        elif menu_selection == 3:
                            keyconfig_open = True
                            keyconfig_selection = 0
                            keyconfig_waiting_action = None
                        elif menu_selection == 4:
                            menu_open = False
                    continue

                if game_state == GameState.TITLE:
                    if event.key in {pygame.K_UP, pygame.K_w}:
                        title_menu_selection = (title_menu_selection - 1) % len(title_menu_items)
                        if menu_move_se is not None:
                            menu_move_se.play()
                    elif event.key in {pygame.K_DOWN, pygame.K_s}:
                        title_menu_selection = (title_menu_selection + 1) % len(title_menu_items)
                        if menu_move_se is not None:
                            menu_move_se.play()
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_u or event.key in title_start_keys:
                        if menu_confirm_se is not None:
                            menu_confirm_se.play()
                        selected = title_menu_items[title_menu_selection]
                        if selected == "BATTLE":
                            if start_se is not None:
                                start_se.play()
                            game_state = GameState.CHAR_SELECT
                            debug_draw = False
                            menu_open = False
                            cmdlist_open = False
                            char_select_selection = 0
                            char_select_p2_cpu = True
                            char_select_next_state = GameState.BATTLE
                            _ensure_bgm_for_state(game_state)
                        elif selected == "TRAINING":
                            if start_se is not None:
                                start_se.play()
                            game_state = GameState.CHAR_SELECT
                            debug_draw = True
                            menu_open = False
                            cmdlist_open = False
                            char_select_selection = 0
                            char_select_p2_cpu = False
                            char_select_next_state = GameState.TRAINING
                            _ensure_bgm_for_state(game_state)
                        elif selected == "SETTING":
                            menu_open = True
                        elif selected == "EXIT":
                            running = False
                    continue

                if game_state == GameState.CHAR_SELECT:
                    if event.key == pygame.K_ESCAPE:
                        game_state = GameState.TITLE
                        menu_open = False
                        cmdlist_open = False
                        _ensure_bgm_for_state(game_state)
                        continue

                    if event.key in {pygame.K_UP, pygame.K_w}:
                        char_select_selection = (char_select_selection - 1) % len(char_select_items)
                        if menu_move_se is not None:
                            menu_move_se.play()
                        continue
                    if event.key in {pygame.K_DOWN, pygame.K_s}:
                        char_select_selection = (char_select_selection + 1) % len(char_select_items)
                        if menu_move_se is not None:
                            menu_move_se.play()
                        continue

                    if event.key in {pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d}:
                        if char_select_items[char_select_selection] == "P2":
                            char_select_p2_cpu = not bool(char_select_p2_cpu)
                            if menu_move_se is not None:
                                menu_move_se.play()
                        continue

                    if event.key == pygame.K_RETURN or event.key == pygame.K_u:
                        if menu_confirm_se is not None:
                            menu_confirm_se.play()

                        sel = char_select_items[char_select_selection]
                        if sel == "START":
                            if char_select_next_state == GameState.BATTLE:
                                cpu_enabled_battle = bool(char_select_p2_cpu)
                            elif char_select_next_state == GameState.TRAINING:
                                cpu_enabled_training = bool(char_select_p2_cpu)
                            game_state = char_select_next_state
                            menu_open = False
                            cmdlist_open = False
                            p1_round_wins = 0
                            p2_round_wins = 0
                            result_winner_side = None
                            result_menu_selection = 0
                            reset_match()
                            _ensure_bgm_for_state(game_state)
                        elif sel == "BACK":
                            game_state = GameState.TITLE
                            menu_open = False
                            cmdlist_open = False
                            _ensure_bgm_for_state(game_state)
                        elif sel == "P2":
                            char_select_p2_cpu = not bool(char_select_p2_cpu)
                        continue

                if event.key == pygame.K_r:
                    reset_match()
                elif event.key == pygame.K_ESCAPE:
                    menu_open = not menu_open
                    if not menu_open:
                        cmdlist_open = False
                        keyconfig_open = False
                        keyconfig_waiting_action = None
                        debugmenu_open = False
                        training_settings_open = False
                elif menu_open and event.key == pygame.K_o:
                    # Back/close shortcut (menu-only) to avoid conflicting with gameplay attack key.
                    if keyconfig_open:
                        keyconfig_open = False
                        keyconfig_waiting_action = None
                        if menu_move_se is not None:
                            menu_move_se.play()
                    elif cmdlist_open:
                        _start_cmdlist_close()
                        if menu_move_se is not None:
                            menu_move_se.play()
                    elif debugmenu_open:
                        debugmenu_open = False
                        if menu_move_se is not None:
                            menu_move_se.play()
                    elif training_settings_open:
                        training_settings_open = False
                        if menu_move_se is not None:
                            menu_move_se.play()
                    else:
                        menu_open = False
                        if menu_move_se is not None:
                            menu_move_se.play()
                elif menu_open:
                    if training_settings_open and game_state == GameState.TRAINING:
                        items = [
                            "P1 HP残量",
                            "P2 HP残量",
                            "P1 SPゲージ",
                            "P2 SPゲージ",
                            "HP自動回復",
                            "SP自動回復",
                            "P2状態固定",
                            "開始位置",
                            "P2全ガード",
                            "戻る",
                        ]
                        item_count = len(items)

                        def _apply_training_hp(*, side: int, percent: int) -> None:
                            nonlocal p1_chip_hp, p2_chip_hp
                            if side == 1:
                                p1.hp = int(round(p1.max_hp * (float(percent) / 100.0)))
                                p1_chip_hp = float(p1.hp)
                            else:
                                p2.hp = int(round(p2.max_hp * (float(percent) / 100.0)))
                                p2_chip_hp = float(p2.hp)

                        def _apply_training_sp(*, side: int, percent: int) -> None:
                            max_sp = int(getattr(constants, "POWER_GAUGE_MAX", 1000))
                            sp = int(round(max_sp * (float(percent) / 100.0)))
                            if side == 1:
                                p1.power_gauge = sp
                            else:
                                p2.power_gauge = sp

                        def _cycle_p2_lock(delta: int) -> None:
                            nonlocal training_p2_state_lock
                            training_p2_state_lock = (int(training_p2_state_lock) + int(delta)) % 4

                        def _cycle_start_pos(delta: int) -> None:
                            nonlocal training_start_position
                            training_start_position = (int(training_start_position) + int(delta)) % 3

                        if event.key in {pygame.K_UP, pygame.K_w}:
                            training_settings_selection = (training_settings_selection - 1) % item_count
                            if menu_move_se is not None:
                                menu_move_se.play()
                        elif event.key in {pygame.K_DOWN, pygame.K_s}:
                            training_settings_selection = (training_settings_selection + 1) % item_count
                            if menu_move_se is not None:
                                menu_move_se.play()
                        elif event.key in {pygame.K_LEFT, pygame.K_a}:
                            idx = int(training_settings_selection)
                            if idx == 0:
                                training_hp_percent_p1 = max(0, int(training_hp_percent_p1) - 10)
                                _apply_training_hp(side=1, percent=int(training_hp_percent_p1))
                                if menu_move_se is not None:
                                    menu_move_se.play()
                            elif idx == 1:
                                training_hp_percent_p2 = max(0, int(training_hp_percent_p2) - 10)
                                _apply_training_hp(side=2, percent=int(training_hp_percent_p2))
                                if menu_move_se is not None:
                                    menu_move_se.play()
                            elif idx == 2:
                                training_sp_percent_p1 = max(0, int(training_sp_percent_p1) - 10)
                                _apply_training_sp(side=1, percent=int(training_sp_percent_p1))
                                if menu_move_se is not None:
                                    menu_move_se.play()
                            elif idx == 3:
                                training_sp_percent_p2 = max(0, int(training_sp_percent_p2) - 10)
                                _apply_training_sp(side=2, percent=int(training_sp_percent_p2))
                                if menu_move_se is not None:
                                    menu_move_se.play()
                            elif idx == 4:
                                training_auto_recover_hp = not bool(training_auto_recover_hp)
                                if menu_move_se is not None:
                                    menu_move_se.play()
                            elif idx == 5:
                                training_auto_recover_sp = not bool(training_auto_recover_sp)
                                if menu_move_se is not None:
                                    menu_move_se.play()
                            elif idx == 6:
                                _cycle_p2_lock(-1)
                                if menu_move_se is not None:
                                    menu_move_se.play()
                            elif idx == 7:
                                _cycle_start_pos(-1)
                                if menu_move_se is not None:
                                    menu_move_se.play()
                            elif idx == 8:
                                training_p2_all_guard = not bool(training_p2_all_guard)
                                if menu_move_se is not None:
                                    menu_move_se.play()
                        elif event.key in {pygame.K_RIGHT, pygame.K_d}:
                            idx = int(training_settings_selection)
                            if idx == 0:
                                training_hp_percent_p1 = min(100, int(training_hp_percent_p1) + 10)
                                _apply_training_hp(side=1, percent=int(training_hp_percent_p1))
                                if menu_move_se is not None:
                                    menu_move_se.play()
                            elif idx == 1:
                                training_hp_percent_p2 = min(100, int(training_hp_percent_p2) + 10)
                                _apply_training_hp(side=2, percent=int(training_hp_percent_p2))
                                if menu_move_se is not None:
                                    menu_move_se.play()
                            elif idx == 2:
                                training_sp_percent_p1 = min(100, int(training_sp_percent_p1) + 10)
                                _apply_training_sp(side=1, percent=int(training_sp_percent_p1))
                                if menu_move_se is not None:
                                    menu_move_se.play()
                            elif idx == 3:
                                training_sp_percent_p2 = min(100, int(training_sp_percent_p2) + 10)
                                _apply_training_sp(side=2, percent=int(training_sp_percent_p2))
                                if menu_move_se is not None:
                                    menu_move_se.play()
                            elif idx == 4:
                                training_auto_recover_hp = not bool(training_auto_recover_hp)
                                if menu_move_se is not None:
                                    menu_move_se.play()
                            elif idx == 5:
                                training_auto_recover_sp = not bool(training_auto_recover_sp)
                                if menu_move_se is not None:
                                    menu_move_se.play()
                            elif idx == 6:
                                _cycle_p2_lock(+1)
                                if menu_move_se is not None:
                                    menu_move_se.play()
                            elif idx == 7:
                                _cycle_start_pos(+1)
                                if menu_move_se is not None:
                                    menu_move_se.play()
                            elif idx == 8:
                                training_p2_all_guard = not bool(training_p2_all_guard)
                                if menu_move_se is not None:
                                    menu_move_se.play()
                        elif event.key == pygame.K_RETURN or event.key == pygame.K_u:
                            idx = int(training_settings_selection)
                            if idx == 4:
                                training_auto_recover_hp = not bool(training_auto_recover_hp)
                                if menu_confirm_se is not None:
                                    menu_confirm_se.play()
                            elif idx == 5:
                                training_auto_recover_sp = not bool(training_auto_recover_sp)
                                if menu_confirm_se is not None:
                                    menu_confirm_se.play()
                            elif idx == 6:
                                training_p2_state_lock = (int(training_p2_state_lock) + 1) % 4
                                if menu_confirm_se is not None:
                                    menu_confirm_se.play()
                            elif idx == 7:
                                training_start_position = (int(training_start_position) + 1) % 3
                                if menu_confirm_se is not None:
                                    menu_confirm_se.play()
                            elif idx == 8:
                                training_p2_all_guard = not bool(training_p2_all_guard)
                                if menu_confirm_se is not None:
                                    menu_confirm_se.play()
                            else:
                                training_settings_open = False
                                if menu_move_se is not None:
                                    menu_move_se.play()
                        elif event.key in {pygame.K_ESCAPE, pygame.K_o}:
                            training_settings_open = False
                            if menu_move_se is not None:
                                menu_move_se.play()
                        continue

                    if debugmenu_open and game_state == GameState.TRAINING:
                        debug_items = [
                            "キー履歴: ",
                            "P1フレーム情報: ",
                            "P2フレーム情報: ",
                            "判定表示: ",
                            "フレームメーター: ",
                            "グリッド表示: ",
                            "戻る",
                        ]
                        debug_item_count = len(debug_items)
                        if event.key in {pygame.K_UP, pygame.K_w}:
                            debugmenu_selection = (debugmenu_selection - 1) % debug_item_count
                            if menu_move_se is not None:
                                menu_move_se.play()
                        elif event.key in {pygame.K_DOWN, pygame.K_s}:
                            debugmenu_selection = (debugmenu_selection + 1) % debug_item_count
                            if menu_move_se is not None:
                                menu_move_se.play()
                        elif event.key in {pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d, pygame.K_RETURN, pygame.K_u}:
                            idx = int(debugmenu_selection)
                            if idx == 0:
                                debug_ui_show_key_history = not bool(debug_ui_show_key_history)
                                settings["debug_ui_show_key_history"] = bool(debug_ui_show_key_history)
                                _save_settings(settings)
                                if menu_confirm_se is not None:
                                    menu_confirm_se.play()
                            elif idx == 1:
                                debug_ui_show_p1_frames = not bool(debug_ui_show_p1_frames)
                                settings["debug_ui_show_p1_frames"] = bool(debug_ui_show_p1_frames)
                                _save_settings(settings)
                                if menu_confirm_se is not None:
                                    menu_confirm_se.play()
                            elif idx == 2:
                                debug_ui_show_p2_frames = not bool(debug_ui_show_p2_frames)
                                settings["debug_ui_show_p2_frames"] = bool(debug_ui_show_p2_frames)
                                _save_settings(settings)
                                if menu_confirm_se is not None:
                                    menu_confirm_se.play()
                            elif idx == 3:
                                debug_draw = not bool(debug_draw)
                                settings["debug_draw"] = bool(debug_draw)
                                _save_settings(settings)
                                if menu_confirm_se is not None:
                                    menu_confirm_se.play()
                            elif idx == 4:
                                frame_meter_enabled = not bool(frame_meter_enabled)
                                settings["frame_meter_enabled"] = bool(frame_meter_enabled)
                                _save_settings(settings)
                                if menu_confirm_se is not None:
                                    menu_confirm_se.play()
                            elif idx == 5:
                                debug_show_grid = not bool(debug_show_grid)
                                settings["debug_show_grid"] = bool(debug_show_grid)
                                _save_settings(settings)
                                if menu_confirm_se is not None:
                                    menu_confirm_se.play()
                            else:
                                debugmenu_open = False
                                if menu_move_se is not None:
                                    menu_move_se.play()
                        elif event.key in {pygame.K_ESCAPE, pygame.K_o}:
                            debugmenu_open = False
                            if menu_move_se is not None:
                                menu_move_se.play()
                        continue

                    if keyconfig_open:
                        if event.key in {pygame.K_UP, pygame.K_w}:
                            keyconfig_selection = (keyconfig_selection - 1) % max(1, len(keyconfig_actions))
                            if menu_move_se is not None:
                                menu_move_se.play()
                        elif event.key in {pygame.K_DOWN, pygame.K_s}:
                            keyconfig_selection = (keyconfig_selection + 1) % max(1, len(keyconfig_actions))
                            if menu_move_se is not None:
                                menu_move_se.play()
                        elif event.key in {pygame.K_RIGHT, pygame.K_d}:
                            if keyconfig_waiting_action is None and keyconfig_actions:
                                cur_act = str(keyconfig_actions[int(keyconfig_selection)][1])
                                p1_idx = [i for i, (_l, a) in enumerate(keyconfig_actions) if str(a).startswith("P1_")]
                                p2_idx = [i for i, (_l, a) in enumerate(keyconfig_actions) if str(a).startswith("P2_")]
                                if cur_act.startswith("P1_") and p1_idx and p2_idx:
                                    pos = p1_idx.index(int(keyconfig_selection)) if int(keyconfig_selection) in p1_idx else 0
                                    keyconfig_selection = int(p2_idx[min(pos, len(p2_idx) - 1)])
                                    if menu_move_se is not None:
                                        menu_move_se.play()
                        elif event.key in {pygame.K_LEFT, pygame.K_a}:
                            if keyconfig_waiting_action is None and keyconfig_actions:
                                cur_act = str(keyconfig_actions[int(keyconfig_selection)][1])
                                p1_idx = [i for i, (_l, a) in enumerate(keyconfig_actions) if str(a).startswith("P1_")]
                                p2_idx = [i for i, (_l, a) in enumerate(keyconfig_actions) if str(a).startswith("P2_")]
                                if cur_act.startswith("P2_") and p1_idx and p2_idx:
                                    pos = p2_idx.index(int(keyconfig_selection)) if int(keyconfig_selection) in p2_idx else 0
                                    keyconfig_selection = int(p1_idx[min(pos, len(p1_idx) - 1)])
                                    if menu_move_se is not None:
                                        menu_move_se.play()
                        elif event.key == pygame.K_RETURN or event.key == pygame.K_u:
                            _label, act = keyconfig_actions[keyconfig_selection]
                            keyconfig_waiting_action = str(act)
                            if menu_confirm_se is not None:
                                menu_confirm_se.play()
                        elif event.key in {pygame.K_ESCAPE, pygame.K_o}:
                            keyconfig_open = False
                            keyconfig_waiting_action = None
                            if event.key == pygame.K_o and menu_move_se is not None:
                                menu_move_se.play()
                        continue

                    # CommandListMenuの入力処理
                    if game_state in {GameState.BATTLE, GameState.TRAINING} and command_list_menu is not None:
                        if command_list_menu.handle_input(event, menu_move_se=menu_move_se, menu_confirm_se=menu_confirm_se):
                            continue

                    if game_state in {GameState.BATTLE, GameState.TRAINING}:
                        _items = ["res", "bgm", "se", "cmdlist", "keyconfig", "debug", "back", "close"]
                        if game_state == GameState.TRAINING:
                            _items = ["res", "bgm", "se", "cmdlist", "keyconfig", "debug", "training", "back", "close"]
                    else:
                        _items = [
                            "res",
                            "bgm",
                            "se",
                            "keyconfig",
                            "close",
                        ]
                    menu_item_count = len(_items)
                    if event.key in {pygame.K_UP, pygame.K_w}:
                        menu_selection = (menu_selection - 1) % menu_item_count
                        if menu_move_se is not None:
                            menu_move_se.play()
                    elif event.key in {pygame.K_DOWN, pygame.K_s}:
                        menu_selection = (menu_selection + 1) % menu_item_count
                        if menu_move_se is not None:
                            menu_move_se.play()
                    elif event.key in {pygame.K_LEFT, pygame.K_a}:
                        if menu_selection == 0:
                            current_res_index = (current_res_index - 1) % len(resolutions)
                        elif menu_selection == 1:
                            bgm_volume_level = max(0, bgm_volume_level - 1)
                            settings["bgm_volume_level"] = int(bgm_volume_level)
                            _save_settings(settings)
                            _apply_bgm_volume()
                        elif menu_selection == 2:
                            se_volume_level = max(0, se_volume_level - 1)
                            settings["se_volume_level"] = int(se_volume_level)
                            _save_settings(settings)
                            _apply_se_volume()
                    elif event.key in {pygame.K_RIGHT, pygame.K_d}:
                        if menu_selection == 0:
                            current_res_index = (current_res_index + 1) % len(resolutions)
                        elif menu_selection == 1:
                            bgm_volume_level = min(100, bgm_volume_level + 1)
                            settings["bgm_volume_level"] = int(bgm_volume_level)
                            _save_settings(settings)
                            _apply_bgm_volume()
                        elif menu_selection == 2:
                            se_volume_level = min(100, se_volume_level + 1)
                            settings["se_volume_level"] = int(se_volume_level)
                            _save_settings(settings)
                            _apply_se_volume()
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_u:
                        if menu_confirm_se is not None:
                            menu_confirm_se.play()
                        selected_key = _items[int(menu_selection)] if _items else ""
                        if selected_key == "res":
                            _apply_resolution(resolutions[current_res_index])
                            reset_match()
                        elif selected_key == "cmdlist":
                            if command_list_menu is not None:
                                command_list_menu.open()
                        elif selected_key == "keyconfig":
                            keyconfig_open = True
                            keyconfig_selection = 0
                            keyconfig_waiting_action = None
                        elif selected_key == "debug" and game_state == GameState.TRAINING:
                            debugmenu_open = True
                            debugmenu_selection = 0
                        elif selected_key == "training" and game_state == GameState.TRAINING:
                            training_settings_open = True
                            training_settings_selection = 0
                        elif selected_key == "back" and game_state in {GameState.BATTLE, GameState.TRAINING}:
                            game_state = GameState.TITLE
                            menu_open = False
                            reset_match()
                            effects.clear()
                            projectiles.clear()
                            _ensure_bgm_for_state(game_state)
                        elif selected_key == "close":
                            menu_open = False
                elif event.key == int(keybinds.get("P1_JUMP", pygame.K_w)):
                    p1_jump_pressed = True
                elif event.key == int(keybinds.get("P2_JUMP", pygame.K_UP)):
                    p2_jump_pressed = True
                elif event.key == int(keybinds.get("P2_ATTACK", pygame.K_SEMICOLON)):
                    p2_attack_id = "P2_ATTACK"
                # Guilty Gear Strive button layout (5 buttons)
                elif event.key == int(keybinds.get("P1_P", pygame.K_u)):
                    p1_attack_id = "P1_P"
                elif event.key == int(keybinds.get("P1_K", pygame.K_j)):
                    p1_attack_id = "P1_K"
                elif event.key == int(keybinds.get("P1_S", pygame.K_i)):
                    p1_attack_id = "P1_S"
                elif event.key == int(keybinds.get("P1_HS", pygame.K_k)):
                    p1_attack_id = "P1_HS"
                elif event.key == int(keybinds.get("P1_D", pygame.K_o)):
                    p1_attack_id = "P1_D"

        tick_ms = pygame.time.get_ticks()

        if int(shungoku_start_queued_side) in {1, 2} and int(super_freeze_frames_left) <= 0:
            starter = p1 if int(shungoku_start_queued_side) == 1 else p2
            if bool(getattr(starter, "_shungoku_pending_start", False)):
                try:
                    starter.start_shungokusatsu()
                except Exception:
                    pass
            shungoku_start_queued_side = 0

        if super_freeze_frames_left > 0:
            super_freeze_frames_left -= 1

            # 描画（ステージに描いて、最後にウィンドウへ拡大）。
            stage_surface.fill(constants.COLOR_BG)

            stage_renderer.draw_background(
                stage_surface,
                tick_ms=int(tick_ms),
                stage_bg_frames=stage_bg_frames,
                stage_bg_img=stage_bg_img,
            )

            stage_renderer.draw_rain(stage_surface)

            pygame.draw.line(
                stage_surface,
                (80, 80, 80),
                (0, constants.GROUND_Y),
                (constants.STAGE_WIDTH, constants.GROUND_Y),
                2,
            )

            flash = pygame.Surface((constants.STAGE_WIDTH, constants.STAGE_HEIGHT), pygame.SRCALPHA)
            phase = int(super_freeze_frames_left)
            if (phase // 2) % 2 == 0:
                flash.fill((255, 255, 255, 170))
            else:
                flash.fill((0, 0, 0, 160))
            stage_surface.blit(flash, (0, 0))

            p1.draw(stage_surface, debug_draw=debug_draw)
            p2.draw(stage_surface, debug_draw=debug_draw)

            scaled = pygame.transform.smoothscale(stage_surface, (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
            shake = 2 if (phase % 2 == 0) else -2
            screen.blit(scaled, (shake, 0))
            pygame.display.flip()
            clock.tick(constants.FPS)
            continue

        if game_state == GameState.RESULT:
            if not result_bg_frames:
                # 9003-1..11 の背景をロード（convert_alpha のため display 初期化後に行う）。
                base = resource_path("assets/images/RYUKO2nd/organized/hit")
                for i in range(1, 12):
                    matches = sorted(base.glob(f"*_9003-{i}.png"))
                    if not matches:
                        continue
                    p = matches[0]
                    try:
                        img = pygame.image.load(str(p)).convert_alpha()
                        bbox = img.get_bounding_rect(min_alpha=1)
                        if bbox.width > 0 and bbox.height > 0:
                            img = img.subsurface(bbox).copy()
                        result_bg_frames.append(img)
                    except pygame.error:
                        pass

            if result_bg_frames:
                result_anim_counter = int(result_anim_counter) + 1
                idx = min((int(result_anim_counter) // 10), len(result_bg_frames) - 1)
                img = result_bg_frames[idx]
                if img.get_size() != (constants.STAGE_WIDTH, constants.STAGE_HEIGHT):
                    img = pygame.transform.smoothscale(img, (constants.STAGE_WIDTH, constants.STAGE_HEIGHT))
                stage_surface.blit(img, (0, 0))
            else:
                stage_surface.fill((0, 0, 0))

            overlay = pygame.Surface((constants.STAGE_WIDTH, constants.STAGE_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            stage_surface.blit(overlay, (0, 0))

            title = title_font.render("RESULT", True, (245, 245, 245))
            stage_surface.blit(title, title.get_rect(midtop=(constants.STAGE_WIDTH // 2, 60)))

            winner_text = "DRAW" if result_winner_side is None else ("P1 WIN" if int(result_winner_side) == 1 else "P2 WIN")
            w_surf = font.render(winner_text, True, (255, 240, 120))
            stage_surface.blit(w_surf, w_surf.get_rect(midtop=(constants.STAGE_WIDTH // 2, 120)))

            y = 220
            for i, item in enumerate(result_menu_items):
                selected = i == int(result_menu_selection)
                color = (255, 240, 120) if selected else (240, 240, 240)
                label = item
                surf = font.render(label, True, color)
                stage_surface.blit(surf, surf.get_rect(midtop=(constants.STAGE_WIDTH // 2, y)))
                y += 40

            scaled = pygame.transform.smoothscale(stage_surface, (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
            screen.blit(scaled, (0, 0))
            pygame.display.flip()
            clock.tick(constants.FPS)
            continue

        if game_state == GameState.CHAR_SELECT:
            stage_surface.fill((0, 0, 0))

            tick = pygame.time.get_ticks()
            if title_bg_img is not None:
                bg = pygame.transform.smoothscale(title_bg_img, (constants.STAGE_WIDTH, constants.STAGE_HEIGHT))
                bg.set_alpha(60)
                stage_surface.blit(bg, (0, 0))

            if char_select_thumb is None:
                p = resource_path("assets/images/RYUKO2nd/キャラサムネ.png")
                if p.exists():
                    try:
                        char_select_thumb = pygame.image.load(str(p)).convert_alpha()
                    except pygame.error:
                        char_select_thumb = None

            if char_select_thumb is not None:
                max_w = int(constants.STAGE_WIDTH * 0.45)
                scale = max_w / max(1, char_select_thumb.get_width())
                w = max(1, int(round(char_select_thumb.get_width() * scale)))
                h = max(1, int(round(char_select_thumb.get_height() * scale)))
                thumb = pygame.transform.smoothscale(char_select_thumb, (w, h))
                stage_surface.blit(thumb, (int(constants.STAGE_WIDTH * 0.08), int(constants.STAGE_HEIGHT * 0.22)))

            overlay = pygame.Surface((constants.STAGE_WIDTH, constants.STAGE_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            stage_surface.blit(overlay, (0, 0))

            scaled = pygame.transform.smoothscale(stage_surface, (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
            screen.blit(scaled, (0, 0))

            title_surface = title_font.render("CHARACTER SELECT", True, (245, 245, 245))
            if char_select_next_state == GameState.TRAINING:
                title_surface = title_font.render("TRAINING SETUP", True, (245, 245, 245))
            title_rect = title_surface.get_rect(center=(constants.SCREEN_WIDTH // 2, 110))
            screen.blit(title_surface, title_rect)

            right_x = int(constants.SCREEN_WIDTH * 0.65)
            base_y = int(constants.SCREEN_HEIGHT * 0.34)
            for i, item in enumerate(char_select_items):
                selected = i == int(char_select_selection)
                local_shake = int(3 * math.sin((tick / 120.0) + i)) if selected else 0

                text_color = (255, 240, 120) if selected else (210, 210, 210)
                text_surf = menu_font.render(item, True, text_color)

                text_rect = text_surf.get_rect(midtop=(right_x + local_shake, base_y + i * 54))
                screen.blit(text_surf, text_rect)

                if selected and (tick // 250) % 2 == 0:
                    arrow = menu_font.render("▶", True, (90, 255, 220))
                    arrow_rect = arrow.get_rect(midright=(text_rect.left - 14, text_rect.centery))
                    screen.blit(arrow, arrow_rect)

            hint = font.render("ESC: 戻る / Enter: 決定", True, (235, 235, 235))
            screen.blit(hint, hint.get_rect(midbottom=(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT - 22)))

            pygame.display.flip()
            clock.tick(constants.FPS)
            continue

        if menu_open:
            stage_surface.fill(constants.COLOR_BG)

            stage_renderer.draw_background(
                stage_surface,
                tick_ms=int(tick_ms),
                stage_bg_frames=stage_bg_frames,
                stage_bg_img=stage_bg_img,
            )

            stage_renderer.draw_rain(stage_surface)

            pygame.draw.line(
                stage_surface,
                (80, 80, 80),
                (0, constants.GROUND_Y),
                (constants.STAGE_WIDTH, constants.GROUND_Y),
                2,
            )

            p1.draw(stage_surface, debug_draw=debug_draw)
            p2.draw(stage_surface, debug_draw=debug_draw)

            scaled = pygame.transform.smoothscale(stage_surface, (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
            screen.blit(scaled, (0, 0))

            overlay = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))

            w = int(constants.SCREEN_WIDTH)
            h = int(constants.SCREEN_HEIGHT)
            panel_w = int(min(760, w - 80))
            panel_h = int(min(520, h - 140))
            panel_x = (w - panel_w) // 2
            panel_y = (h - panel_h) // 2

            panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            panel.fill((18, 18, 22, 235))
            screen.blit(panel, (panel_x, panel_y))
            pygame.draw.rect(screen, (90, 255, 220), pygame.Rect(panel_x, panel_y, panel_w, panel_h), 2)

            title = font.render("MENU", True, (245, 245, 245))
            screen.blit(title, (panel_x + 26, panel_y + 18))

            res_w, res_h = resolutions[current_res_index]
            if game_state in {GameState.BATTLE, GameState.TRAINING}:
                if game_state == GameState.TRAINING:
                    items = [
                        f"解像度: {res_w}x{res_h}  (←→ 変更 / Enter 適用)",
                        f"BGM音量: {bgm_volume_level}  (←→ 変更)",
                        f"効果音音量: {se_volume_level}  (←→ 変更)",
                        "コマンドリスト",
                        "キーコンフィグ",
                        "デバッグ表示",
                        "トレーニング設定",
                        "メニューに戻る",
                        "閉じる",
                    ]
                else:
                    items = [
                        f"解像度: {res_w}x{res_h}  (←→ 変更 / Enter 適用)",
                        f"BGM音量: {bgm_volume_level}  (←→ 変更)",
                        f"効果音音量: {se_volume_level}  (←→ 変更)",
                        "コマンドリスト",
                        "キーコンフィグ",
                        "デバッグ表示",
                        "メニューに戻る",
                        "閉じる",
                    ]
            else:
                items = [
                    f"解像度: {res_w}x{res_h}  (←→ 変更 / Enter 適用)",
                    f"BGM音量: {bgm_volume_level}  (←→ 変更)",
                    f"効果音音量: {se_volume_level}  (←→ 変更)",
                    "キーコンフィグ",
                    "閉じる",
                ]
            y = panel_y + 74
            if not cmdlist_open:
                for i, text in enumerate(items):
                    selected = (i == int(menu_selection))
                    if selected:
                        pygame.draw.rect(
                            screen,
                            (90, 255, 220, 28),
                            pygame.Rect(panel_x + 22, y - 6, panel_w - 44, 40),
                            0,
                        )
                        pygame.draw.rect(
                            screen,
                            (90, 255, 220),
                            pygame.Rect(panel_x + 22, y - 6, panel_w - 44, 40),
                            1,
                        )
                    color = (255, 240, 120) if selected else (230, 230, 230)
                    surf = font.render(text, True, color)
                    screen.blit(surf, (panel_x + 36, y))
                    y += 44

            if game_state == GameState.TRAINING and training_settings_open:
                overlay5 = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay5.fill((0, 0, 0, 210))
                screen.blit(overlay5, (0, 0))

                w = int(constants.SCREEN_WIDTH)
                h = int(constants.SCREEN_HEIGHT)
                panel_w = int(min(760, w - 80))
                panel_h = int(min(520, h - 140))
                panel_x = (w - panel_w) // 2
                panel_y = (h - panel_h) // 2

                panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
                panel.fill((18, 18, 22, 235))
                screen.blit(panel, (panel_x, panel_y))
                pygame.draw.rect(screen, (90, 255, 220), pygame.Rect(panel_x, panel_y, panel_w, panel_h), 2)

                header = title_font.render("TRAINING", True, (245, 245, 245))
                header_scale_w = max(1, int(round(header.get_width() * 0.38)))
                header_scale_h = max(1, int(round(header.get_height() * 0.38)))
                header = pygame.transform.smoothscale(header, (header_scale_w, header_scale_h))
                screen.blit(header, (panel_x + 26, panel_y + 18))

                sub = keycfg_font.render("←→: 調整 / Enter: 切替 / ESC or O: 戻る", True, (220, 220, 220))
                screen.blit(sub, (panel_x + 28, panel_y + 58))

                lock_label = "なし"
                if int(training_p2_state_lock) == 1:
                    lock_label = "立ち"
                elif int(training_p2_state_lock) == 2:
                    lock_label = "しゃがみ"
                elif int(training_p2_state_lock) == 3:
                    lock_label = "ジャンプ"

                pos_label = "画面中央"
                if int(training_start_position) == 1:
                    pos_label = "左端"
                elif int(training_start_position) == 2:
                    pos_label = "右端"

                rows = [
                    ("P1 HP残量", f"{int(training_hp_percent_p1)}%"),
                    ("P2 HP残量", f"{int(training_hp_percent_p2)}%"),
                    ("P1 SPゲージ", f"{int(training_sp_percent_p1)}%"),
                    ("P2 SPゲージ", f"{int(training_sp_percent_p2)}%"),
                    ("HP自動回復", "ON" if bool(training_auto_recover_hp) else "OFF"),
                    ("SP自動回復", "ON" if bool(training_auto_recover_sp) else "OFF"),
                    ("P2状態固定", lock_label),
                    ("開始位置", pos_label),
                    ("P2全ガード", "ON" if bool(training_p2_all_guard) else "OFF"),
                    ("戻る", ""),
                ]
                y0 = panel_y + 110
                line_h = 44
                y_max = panel_y + panel_h - 56
                visible = max(1, int((y_max - y0) // line_h))
                max_scroll = max(0, len(rows) - visible)
                try:
                    target_scroll = int(training_settings_scroll)
                    sel = int(training_settings_selection)
                    if sel < target_scroll:
                        target_scroll = sel
                    if sel >= target_scroll + visible:
                        target_scroll = sel - visible + 1
                    training_settings_scroll = max(0, min(max_scroll, int(target_scroll)))
                except Exception:
                    training_settings_scroll = 0

                y = int(y0)
                for i in range(int(training_settings_scroll), min(len(rows), int(training_settings_scroll) + visible)):
                    label, value = rows[i]
                    selected = i == int(training_settings_selection)
                    if selected:
                        pygame.draw.rect(
                            screen,
                            (90, 255, 220, 28),
                            pygame.Rect(panel_x + 22, y - 6, panel_w - 44, 40),
                            0,
                        )
                        pygame.draw.rect(
                            screen,
                            (90, 255, 220),
                            pygame.Rect(panel_x + 22, y - 6, panel_w - 44, 40),
                            1,
                        )
                    color = (255, 240, 120) if selected else (230, 230, 230)
                    text = label if not value else f"{label}: {value}"
                    surf = font.render(text, True, color)
                    screen.blit(surf, (panel_x + 36, y))
                    y += int(line_h)

                # スクロールバー（必要な場合のみ描画）
                if int(len(rows)) > int(visible):
                    track_h = int(y_max - y0)
                    thumb_height = max(20, int(round(float(track_h) * (float(visible) / float(len(rows))))))
                    thumb_y = y0 + int(round(float(training_settings_scroll) * (float(track_h - thumb_height) / max(1, float(max_scroll)))))
                    # トラック
                    pygame.draw.rect(screen, (60, 60, 60), pygame.Rect(panel_x + panel_w - 18, y0, 12, track_h))
                    # サム
                    pygame.draw.rect(screen, (180, 180, 180), pygame.Rect(panel_x + panel_w - 17, thumb_y, 10, thumb_height))

            if keyconfig_open:
                overlay3 = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay3.fill((0, 0, 0, 210))
                screen.blit(overlay3, (0, 0))

                w = int(constants.SCREEN_WIDTH)
                h = int(constants.SCREEN_HEIGHT)

                panel_w = int(min(860, w - 80))
                panel_h = int(min(560, h - 140))
                panel_x = (w - panel_w) // 2
                panel_y = (h - panel_h) // 2

                panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
                panel.fill((18, 18, 22, 235))
                screen.blit(panel, (panel_x, panel_y))
                pygame.draw.rect(screen, (90, 255, 220), pygame.Rect(panel_x, panel_y, panel_w, panel_h), 2)

                header_txt = "KEY CONFIG"
                sub_txt = "ESC: 戻る"
                if keyconfig_waiting_action is not None:
                    sub_txt = "設定したいキーを押してください (ESCでキャンセル)"

                header = title_font.render(header_txt, True, (245, 245, 245))
                header_scale_w = max(1, int(round(header.get_width() * 0.42)))
                header_scale_h = max(1, int(round(header.get_height() * 0.42)))
                header = pygame.transform.smoothscale(header, (header_scale_w, header_scale_h))
                screen.blit(header, (panel_x + 26, panel_y + 18))

                sub = font.render(sub_txt, True, (220, 220, 220))
                screen.blit(sub, (panel_x + 28, panel_y + 58))

                inner_x = panel_x + 26
                inner_y = panel_y + 98
                inner_w = panel_w - 52
                inner_h = panel_h - 140

                col_gap = 26
                col_w = (inner_w - col_gap) // 2
                left_x = inner_x
                right_x = inner_x + col_w + col_gap

                tag_h = 34
                pygame.draw.rect(screen, (25, 25, 35), pygame.Rect(left_x, inner_y - 44, col_w, tag_h), 0)
                pygame.draw.rect(screen, (25, 25, 35), pygame.Rect(right_x, inner_y - 44, col_w, tag_h), 0)
                pygame.draw.rect(screen, (80, 80, 110), pygame.Rect(left_x, inner_y - 44, col_w, tag_h), 1)
                pygame.draw.rect(screen, (80, 80, 110), pygame.Rect(right_x, inner_y - 44, col_w, tag_h), 1)

                p1_tag = font.render("P1", True, (90, 255, 220))
                p2_tag = font.render("P2", True, (90, 255, 220))
                screen.blit(p1_tag, p1_tag.get_rect(midleft=(left_x + 14, inner_y - 27)))
                screen.blit(p2_tag, p2_tag.get_rect(midleft=(right_x + 14, inner_y - 27)))

                rows: list[tuple[str, str, int]] = []
                for idx, (label, act) in enumerate(keyconfig_actions):
                    rows.append((str(label), str(act), int(idx)))

                left_rows = [r for r in rows if (r[1].startswith("P1_") or (not r[1].startswith("P2_")))]
                right_rows = [r for r in rows if r[1].startswith("P2_")]

                line_h = 44
                visible = max(1, int(inner_h // line_h))
                left_idxs = [int(idx) for _l, _a, idx in left_rows]
                right_idxs = [int(idx) for _l, _a, idx in right_rows]

                try:
                    sel = int(keyconfig_selection)
                    if sel in left_idxs:
                        pos = left_idxs.index(sel)
                        target = int(keyconfig_scroll_left)
                        if pos < target:
                            target = pos
                        if pos >= target + visible:
                            target = pos - visible + 1
                        keyconfig_scroll_left = max(0, min(max(0, len(left_rows) - visible), int(target)))
                    if sel in right_idxs:
                        pos = right_idxs.index(sel)
                        target = int(keyconfig_scroll_right)
                        if pos < target:
                            target = pos
                        if pos >= target + visible:
                            target = pos - visible + 1
                        keyconfig_scroll_right = max(0, min(max(0, len(right_rows) - visible), int(target)))
                except Exception:
                    keyconfig_scroll_left = 0
                    keyconfig_scroll_right = 0

                def _draw_rows(rows_in: list[tuple[str, str, int]], *, x: int, scroll: int) -> None:
                    y = int(inner_y)
                    for label, act, idx in rows_in[int(scroll) : int(scroll) + visible]:
                        selected = (idx == int(keyconfig_selection)) and (keyconfig_waiting_action is None)
                        if selected:
                            pygame.draw.rect(screen, (90, 255, 220, 28), pygame.Rect(x, y - 6, col_w, line_h), 0)
                            pygame.draw.rect(screen, (90, 255, 220), pygame.Rect(x, y - 6, col_w, line_h), 1)

                        key_code = int(keybinds.get(str(act), DEFAULT_KEYBINDS.get(str(act), 0)))
                        key_text = _key_name(key_code)

                        name_c = (245, 245, 245) if selected else (220, 220, 220)
                        key_c = (255, 240, 120) if selected else (200, 200, 200)

                        # Long labels (e.g. FIELD_RESET) can overlap with key name, so clamp to fit.
                        label_txt = str(label)
                        max_label_w = int(max(40, col_w - 10 - 170))
                        try:
                            while label_txt and int(keycfg_font.size(label_txt)[0]) > int(max_label_w):
                                if len(label_txt) <= 1:
                                    break
                                label_txt = label_txt[:-1]
                                if len(label_txt) >= 2:
                                    label_txt = label_txt[:-1] + "…"
                        except Exception:
                            pass
                        left = keycfg_font.render(str(label_txt), True, name_c)
                        right = keycfg_font.render(str(key_text), True, key_c)
                        screen.blit(left, (x + 8, y))
                        screen.blit(right, right.get_rect(midright=(x + col_w - 10, y + (left.get_height() // 2) + 2)))

                        y += line_h

                _draw_rows(left_rows, x=left_x, scroll=int(keyconfig_scroll_left))
                _draw_rows(right_rows, x=right_x, scroll=int(keyconfig_scroll_right))

                # スクロールバー（P1側とP2側で別々に描画）
                max_visible_rows = max(1, int(inner_h // line_h))
                
                # P1側（左）のスクロールバー
                if int(len(left_rows)) > int(max_visible_rows):
                    max_scroll_left = max(1, int(len(left_rows)) - int(max_visible_rows))
                    thumb_height_left = max(20, int(round(float(inner_h) * (float(max_visible_rows) / float(len(left_rows))))))
                    thumb_y_left = inner_y + int(round(float(keyconfig_scroll_left) * (float(inner_h - thumb_height_left) / float(max_scroll_left))))
                    # トラック
                    pygame.draw.rect(screen, (60, 60, 60), pygame.Rect(left_x + col_w - 14, inner_y, 10, inner_h))
                    # サム
                    pygame.draw.rect(screen, (180, 180, 180), pygame.Rect(left_x + col_w - 13, thumb_y_left, 8, thumb_height_left))
                
                # P2側（右）のスクロールバー
                if int(len(right_rows)) > int(max_visible_rows):
                    max_scroll_right = max(1, int(len(right_rows)) - int(max_visible_rows))
                    thumb_height_right = max(20, int(round(float(inner_h) * (float(max_visible_rows) / float(len(right_rows))))))
                    thumb_y_right = inner_y + int(round(float(keyconfig_scroll_right) * (float(inner_h - thumb_height_right) / float(max_scroll_right))))
                    # トラック
                    pygame.draw.rect(screen, (60, 60, 60), pygame.Rect(right_x + col_w - 14, inner_y, 10, inner_h))
                    # サム
                    pygame.draw.rect(screen, (180, 180, 180), pygame.Rect(right_x + col_w - 13, thumb_y_right, 8, thumb_height_right))

                footer = keycfg_font.render("↑↓: 選択 / A← D→: 列移動 / Enter: 変更 / ESC: 戻る", True, (220, 220, 220))
                screen.blit(footer, footer.get_rect(midbottom=(w // 2, panel_y + panel_h - 18)))

            if game_state == GameState.TRAINING and debugmenu_open:
                overlay4 = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay4.fill((0, 0, 0, 210))
                screen.blit(overlay4, (0, 0))

                w = int(constants.SCREEN_WIDTH)
                h = int(constants.SCREEN_HEIGHT)
                panel_w = int(min(760, w - 80))
                panel_h = int(min(520, h - 140))
                panel_x = (w - panel_w) // 2
                panel_y = (h - panel_h) // 2

                panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
                panel.fill((18, 18, 22, 235))
                screen.blit(panel, (panel_x, panel_y))
                pygame.draw.rect(screen, (90, 255, 220), pygame.Rect(panel_x, panel_y, panel_w, panel_h), 2)

                header = title_font.render("DEBUG", True, (245, 245, 245))
                header_scale_w = max(1, int(round(header.get_width() * 0.42)))
                header_scale_h = max(1, int(round(header.get_height() * 0.42)))
                header = pygame.transform.smoothscale(header, (header_scale_w, header_scale_h))
                screen.blit(header, (panel_x + 26, panel_y + 18))

                sub = keycfg_font.render("Enter: 切替 / ESC or O: 戻る", True, (220, 220, 220))
                screen.blit(sub, (panel_x + 28, panel_y + 58))

                dbg_rows = [
                    ("キー履歴", bool(debug_ui_show_key_history)),
                    ("P1フレーム情報", bool(debug_ui_show_p1_frames)),
                    ("P2フレーム情報", bool(debug_ui_show_p2_frames)),
                    ("判定表示", bool(debug_draw)),
                    ("フレームメーター", bool(frame_meter_enabled)),
                    ("グリッド表示", bool(debug_show_grid)),
                    ("戻る", True),
                ]
                y = panel_y + 110
                for i, (label, enabled) in enumerate(dbg_rows):
                    selected = i == int(debugmenu_selection)
                    if selected:
                        pygame.draw.rect(
                            screen,
                            (90, 255, 220, 28),
                            pygame.Rect(panel_x + 22, y - 6, panel_w - 44, 40),
                            0,
                        )
                        pygame.draw.rect(
                            screen,
                            (90, 255, 220),
                            pygame.Rect(panel_x + 22, y - 6, panel_w - 44, 40),
                            1,
                        )
                    color = (255, 240, 120) if selected else (230, 230, 230)
                    suffix = "" if label == "戻る" else ("ON" if enabled else "OFF")
                    text = f"{label}: {suffix}" if suffix else label
                    surf = font.render(text, True, color)
                    screen.blit(surf, (panel_x + 36, y))
                    y += 44

            # CommandListMenuの描画
            if game_state in {GameState.BATTLE, GameState.TRAINING} and command_list_menu is not None:
                command_list_menu.draw(screen, p1, title_font=title_font, keycfg_font=keycfg_font)

            pygame.display.flip()
            clock.tick(constants.FPS)
            continue

        if game_state == GameState.TITLE:
            stage_surface.fill((0, 0, 0))

            tick = pygame.time.get_ticks()

            if title_bg_img is not None:
                bg = pygame.transform.smoothscale(title_bg_img, (constants.STAGE_WIDTH, constants.STAGE_HEIGHT))
                bg.set_alpha(60)
                stage_surface.blit(bg, (0, 0))

            title_bg_overlay = pygame.Surface((constants.STAGE_WIDTH, constants.STAGE_HEIGHT), pygame.SRCALPHA)
            title_bg_overlay.fill((0, 0, 0, 140))
            stage_surface.blit(title_bg_overlay, (0, 0))

            scaled = pygame.transform.smoothscale(stage_surface, (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
            screen.blit(scaled, (0, 0))

            title_surface = title_font.render(constants.GAME_TITLE, True, (245, 245, 245))
            title_rect = title_surface.get_rect(center=(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2 - 150))
            screen.blit(title_surface, title_rect)

            cx = constants.SCREEN_WIDTH // 2
            base_y = constants.SCREEN_HEIGHT // 2 - 20
            for i, name in enumerate(title_menu_items):
                selected = i == title_menu_selection
                local_shake = int(3 * math.sin((tick / 120.0) + i)) if selected else 0

                text_color = (255, 240, 120) if selected else (210, 210, 210)
                text_surf = menu_font.render(name, True, text_color)

                text_rect = text_surf.get_rect(center=(cx + local_shake, base_y + i * 50))
                screen.blit(text_surf, text_rect)

                if selected and (tick // 250) % 2 == 0:
                    arrow = menu_font.render("▶", True, (90, 255, 220))
                    arrow_rect = arrow.get_rect(midright=(text_rect.left - 14, text_rect.centery))
                    screen.blit(arrow, arrow_rect)

            pygame.display.flip()
            clock.tick(constants.FPS)
            continue

        # 押しっぱなし入力（左右移動・しゃがみ）は get_pressed で取得。
        keys = pygame.key.get_pressed()

        # move_x は -1/0/+1 の3値にする。
        p1_move_x = int(keys[int(keybinds.get("P1_RIGHT", pygame.K_d))]) - int(keys[int(keybinds.get("P1_LEFT", pygame.K_a))])
        p2_move_x = int(keys[int(keybinds.get("P2_RIGHT", pygame.K_RIGHT))]) - int(keys[int(keybinds.get("P2_LEFT", pygame.K_LEFT))])

        p1_crouch = bool(keys[int(keybinds.get("P1_DOWN", pygame.K_s))])
        p2_crouch = bool(keys[int(keybinds.get("P2_DOWN", pygame.K_DOWN))])

        # 向きは相手の位置から決める（Phase 1 の簡易仕様）。
        p1.facing = 1 if p2.rect.centerx >= p1.rect.centerx else -1
        p2.facing = 1 if p1.rect.centerx >= p2.rect.centerx else -1

        # 入力（intent）を Player に渡す。
        can_play_round = (int(round_over_frames_left) <= 0) and (
            (game_state != GameState.BATTLE) or (int(battle_countdown_frames_left) <= 0)
        )

        # CPU control (P2)
        cpu_enabled_now = (game_state == GameState.BATTLE and cpu_enabled_battle) or (
            game_state == GameState.TRAINING and cpu_enabled_training
        )
        if cpu_enabled_now and can_play_round:
            cpu_decision_frames_left = max(0, int(cpu_decision_frames_left) - 1)
            cpu_attack_cooldown = max(0, int(cpu_attack_cooldown) - 1)
            cpu_jump_cooldown = max(0, int(cpu_jump_cooldown) - 1)
            cpu_special_cooldown = max(0, int(cpu_special_cooldown) - 1)

            dx = float(p1.rect.centerx - p2.rect.centerx)
            adx = abs(dx)

            # Default: approach if far, hold if mid, back off a bit if too close.
            move_dir = 0
            if adx > 230:
                move_dir = 1 if dx > 0 else -1
            elif adx < 90:
                move_dir = -1 if dx > 0 else 1

            p2_move_x = int(move_dir)
            p2_crouch = False

            # Simple decision cadence to avoid spamming.
            if cpu_decision_frames_left <= 0:
                cpu_decision_frames_left = int(constants.FPS * 0.20)

                # 1) Close-range normal attack
                if adx < 115 and cpu_attack_cooldown <= 0 and (not p2.attacking) and (not p2.in_hitstun) and (not p2.in_blockstun):
                    p2.start_attack("P2_L_PUNCH")
                    cpu_attack_cooldown = int(constants.FPS * 0.45)

                # 2) Mid-range specials
                if cpu_special_cooldown <= 0 and (not p2.in_hitstun) and (not p2.in_blockstun):
                    # Prefer shinku if power is enough and distance is good.
                    super_cost = int(getattr(constants, "POWER_GAUGE_SUPER_COST", 500))
                    if adx > 170 and p2.can_spend_power(super_cost) and (random.random() < 0.12):
                        if p2.spend_power(super_cost):
                            p2.start_shinku_hadoken()
                            if beam_se is not None:
                                beam_se.play()
                            super_freeze_frames_left = int(getattr(constants, "SUPER_FREEZE_FRAMES", 30))
                            super_freeze_attacker_side = 2
                            cpu_special_cooldown = int(constants.FPS * 1.2)
                    elif adx > 150 and (random.random() < 0.22):
                        p2.start_hadoken()
                        cpu_special_cooldown = int(constants.FPS * 0.9)

                # 3) Occasional jump to vary behavior
                if cpu_jump_cooldown <= 0 and adx > 140 and (random.random() < 0.06):
                    p2_jump_pressed = True
                    cpu_jump_cooldown = int(constants.FPS * 1.0)

        if game_state == GameState.TRAINING and can_play_round:
            lock = int(training_p2_state_lock)
            if lock == 1:
                p2_move_x = 0
                p2_crouch = False
                p2_jump_pressed = False
            elif lock == 2:
                p2_move_x = 0
                p2_crouch = True
                p2_jump_pressed = False
            elif lock == 3:
                p2_move_x = 0
                p2_crouch = False
                if bool(getattr(p2, "on_ground", False)):
                    p2_jump_pressed = True

        if can_play_round and int(shungoku_posthit_lock_side) in {1, 2}:
            defender = p1 if int(shungoku_posthit_lock_defender_side) == 1 else p2
            defender_down = bool(getattr(defender, "_down_anim_active", False))
            if not defender_down:
                attacker = p1 if int(shungoku_posthit_lock_side) == 1 else p2
                try:
                    attacker._set_action(attacker._best_action_id([0]), mode="loop")
                except Exception:
                    pass
                shungoku_posthit_lock_side = 0
                shungoku_posthit_lock_defender_side = 0

                # 瞬獄殺ヒット後：相手が起き上がった瞬間に BGM を再開する。
                if bool(bgm_suspended):
                    bgm_suspended = False
                    _ensure_bgm_for_state(game_state)
            else:
                if int(shungoku_posthit_lock_side) == 1:
                    p1_move_x = 0
                    p1_crouch = False
                    p1_jump_pressed = False
                    p1_attack_id = None
                else:
                    p2_move_x = 0
                    p2_crouch = False
                    p2_jump_pressed = False
                    p2_attack_id = None

        if can_play_round:
            p1.apply_input(
                PlayerInput(
                    move_x=p1_move_x,
                    jump_pressed=p1_jump_pressed,
                    crouch=p1_crouch,
                    attack_id=p1_attack_id,
                )
            )
            p2.apply_input(
                PlayerInput(
                    move_x=p2_move_x,
                    jump_pressed=p2_jump_pressed,
                    crouch=p2_crouch,
                    attack_id=p2_attack_id,
                )
            )

        def _apply_special_results(res: dict[str, Any], *, side: int, player: Player) -> None:
            nonlocal super_freeze_frames_left, super_freeze_attacker_side
            if bool(res.get("did_shinku")):
                if beam_se is not None:
                    beam_se.play()
                super_freeze_frames_left = int(getattr(constants, "SUPER_FREEZE_FRAMES", 30))
                super_freeze_attacker_side = int(side)
            if bool(res.get("did_shungoku")):
                nonlocal shungoku_start_queued_side
                if int(shungoku_start_queued_side) != 0:
                    return
                nonlocal shungoku_super_se_cooldown
                if int(shungoku_super_se_cooldown) <= 0:
                    if sound_manager.shungoku_super_se is not None:
                        sound_manager.shungoku_super_se.play()
                    shungoku_super_se_cooldown = 12
                super_freeze_frames_left = max(int(super_freeze_frames_left), 10)
                super_freeze_attacker_side = int(side)
                shungoku_start_queued_side = int(side)
                nonlocal shungoku_pan_frames_left, shungoku_pan_target_px
                shungoku_pan_frames_left = int(shungoku_pan_total_frames)
                try:
                    dx = int(player.rect.centerx) - int(constants.STAGE_WIDTH // 2)
                except Exception:
                    dx = 0
                shungoku_pan_target_px = int(max(-18, min(18, round(dx * 0.35))))

        if can_play_round:
            early = int(getattr(constants, "COMMAND_BUTTON_EARLY_FRAMES", 2))
            super_cost = int(getattr(constants, "POWER_GAUGE_SUPER_COST", 500))

            res1 = p1.process_special_inputs(attack_id=p1_attack_id, early_frames=early, super_cost=super_cost)
            _apply_special_results(res1, side=1, player=p1)
            if bool(res1.get("clear_attack_id")):
                p1_attack_id = None

            res2 = p2.process_special_inputs(attack_id=p2_attack_id, early_frames=early, super_cost=super_cost)
            _apply_special_results(res2, side=2, player=p2)
            if bool(res2.get("clear_attack_id")):
                p2_attack_id = None

        if int(shungoku_super_se_cooldown) > 0:
            shungoku_super_se_cooldown = max(0, int(shungoku_super_se_cooldown) - 1)

        # フレームポーズ中は更新をスキップ（フレーム進行時は例外）
        should_update = not frame_paused or frame_advance
        if frame_advance:
            frame_advance = False  # 1フレーム進めたらリセット

        # 物理更新（KO中/カウント中でもアニメは進める）。
        if shungoku_cine_frames_left <= 0 and should_update:
            p1.update()
            p2.update()

        # ポーズ中は以下の更新をスキップ
        if should_update:
            # Rush wind/dust effect spawn (ポーリングで確実に発生させる)。
            if assets.rush_dust_frames:
                pos = p1.consume_rush_effect_spawn()
                if pos is not None:
                    effects.append(Effect(frames=assets.rush_dust_frames, pos=pos, frames_per_image=2))
                pos = p2.consume_rush_effect_spawn()
                if pos is not None:
                    effects.append(Effect(frames=assets.rush_dust_frames, pos=pos, frames_per_image=2))

            # Kキー攻撃の砂ぼこりエフェクト（6540）スポーン（攻撃判定あり）
            if assets.k_attack_dust_frames:
                from src.entities.effect import AttackEffect
                k_info = p1.consume_k_attack_effect_spawn()
                if k_info is not None:
                    effects.append(AttackEffect(
                        frames=assets.k_attack_dust_frames,
                        pos=k_info["pos"],
                        frames_per_image=2,
                        owner_side=k_info["owner_side"],
                        damage=80,
                        hitbox_width=100,
                        hitbox_height=60,
                        hitbox_offset_x=0,
                        hitbox_offset_y=30,  # 地面に接地（ヒットボックスの下半分を地面に配置）
                        startup_frames=2,
                        active_frames=10,
                        hitstop_frames=8,
                        hitstun_frames=15,
                        blockstun_frames=8,
                        knockback_px=20,
                        attacker_recoil_px=2,
                    ))
                k_info = p2.consume_k_attack_effect_spawn()
                if k_info is not None:
                    effects.append(AttackEffect(
                        frames=assets.k_attack_dust_frames,
                        pos=k_info["pos"],
                        frames_per_image=2,
                        owner_side=k_info["owner_side"],
                        damage=80,
                        hitbox_width=100,
                        hitbox_height=60,
                        hitbox_offset_x=0,
                        hitbox_offset_y=30,  # 地面に接地（ヒットボックスの下半分を地面に配置）
                        startup_frames=2,
                        active_frames=10,
                        hitstop_frames=8,
                        hitstun_frames=15,
                        blockstun_frames=8,
                        knockback_px=20,
                        attacker_recoil_px=2,
                    ))

            if p1.consume_hadoken_spawn():
                projectile_system.spawn_hadoken(p1, p1=p1, p2=p2)
            if p2.consume_hadoken_spawn():
                projectile_system.spawn_hadoken(p2, p1=p1, p2=p2)

            if p1.consume_shinku_spawn():
                projectile_system.spawn_shinku(p1, p1=p1, p2=p2)
            if p2.consume_shinku_spawn():
                projectile_system.spawn_shinku(p2, p1=p1, p2=p2)

            end_side_1 = p1.consume_combo_end_side()
            end_side_2 = p2.consume_combo_end_side()
            if end_side_1 == 1:
                p1.reset_combo_count()
            if end_side_1 == 2:
                p2.reset_combo_count()
            if end_side_2 == 1:
                p1.reset_combo_count()
            if end_side_2 == 2:
                p2.reset_combo_count()

            # エフェクト更新。
            for e in effects:
                e.update()
            effects = [e for e in effects if not e.finished]

            if game_state in {GameState.BATTLE, GameState.TRAINING}:
                stage_renderer.update_rain()

            projectile_system.update()

            # 押し合い（Pushbox）解決。
            shungoku_active = (
                shungoku_cine_frames_left > 0
                or bool(getattr(p1, "_shungoku_active", False))
                or bool(getattr(p2, "_shungoku_active", False))
            )
            CollisionSystem.resolve_pushbox_overlap(p1, p2, shungoku_active=shungoku_active)

        # ポーズ中は以下の判定もスキップ
        if should_update:
            # 投げ技のヒット判定（通常攻撃より優先）
            for attacker, defender in ((p1, p2), (p2, p1)):
                if attacker.is_throw_active():
                    throw_hitbox = attacker.get_throw_hitbox()
                    defender_hurtbox = defender.get_hurtbox()
                    if throw_hitbox.colliderect(defender_hurtbox):
                        # 投げ成功：相手をつかんだ瞬間にやられアニメーション
                        attacker._throw_active = False
                        defender._being_thrown = True
                        
                        # 投げアニメーションの持続時間を設定（800-3, 800-4で4F + 800-13で20F or 800-5～800-12で16F）
                        # つかみ: 4F, 投げモーション: 20F（action 800/802）or 16F（action 801/803）
                        if attacker.facing == 1:
                            if attacker._throw_direction == 1:  # 右向きで右に投げる
                                throw_anim_frames = 24  # 4F + 20F
                            else:  # 右向きで左に投げる
                                throw_anim_frames = 20  # 4F + 16F
                        else:
                            if attacker._throw_direction == 1:  # 左向きで左に投げる
                                throw_anim_frames = 24  # 4F + 20F
                            else:  # 左向きで右に投げる
                                throw_anim_frames = 20  # 4F + 16F
                        
                        defender._throw_anim_frames_left = throw_anim_frames
                        
                        # 後ろ投げの場合、投げ終了時の位置を設定（相手の反対側に移動）
                        if attacker._throw_direction == -1:
                            # 後ろ投げ：攻撃側の反対側に移動
                            move_distance = 100  # 移動距離
                            defender._throw_end_pos_x = attacker.pos_x - (attacker.facing * move_distance)
                        else:
                            # 前投げ：位置は変わらない
                            defender._throw_end_pos_x = None
                        
                        # やられアニメーション（hitstun）を設定
                        defender.hitstun_frames_left = throw_anim_frames
                        defender.hitstun_timer = throw_anim_frames
                        
                        # ダメージを与える
                        throw_damage = int(getattr(constants, "THROW_DAMAGE", 100))
                        defender.hp = max(0, defender.hp - throw_damage)
                        
                        # ヒットストップ
                        hitstop = 10
                        attacker.hitstop_frames_left = hitstop
                        defender.hitstop_frames_left = hitstop
                        
                        # SE再生
                        if hit_se is not None:
                            hit_se.play()
                        
                        # 投げ成功後は通常のヒット判定をスキップ
                        break
            
            # ヒット判定（Hitbox vs Hurtbox）。
            for attacker, defender in ((p1, p2), (p2, p1)):
                hit_point = CollisionSystem.check_hit_collision(attacker, defender)
                if hit_point is not None:
                    result = combat_system.apply_hit(
                        attacker,
                        defender,
                        hit_point,
                        game_state=game_state,
                        training_p2_all_guard=training_p2_all_guard,
                        effects=effects,
                        p1=p1,
                        p2=p2,
                    )
                    if result["frame_meter_adv_value"] is not None:
                        frame_meter_adv_value = result["frame_meter_adv_value"]
                        frame_meter_adv_frames_left = result["frame_meter_adv_frames_left"]
                        frame_meter_adv_attacker_side = result["frame_meter_adv_attacker_side"]

            # 弾のヒット判定
            projectile_hit_result = projectile_system.check_hits(
                p1=p1,
                p2=p2,
                game_state=game_state,
                training_p2_all_guard=training_p2_all_guard,
                effects=effects,
            )
            if projectile_hit_result["frame_meter_adv_value"] is not None:
                frame_meter_adv_value = projectile_hit_result["frame_meter_adv_value"]
                frame_meter_adv_frames_left = projectile_hit_result["frame_meter_adv_frames_left"]
                frame_meter_adv_attacker_side = projectile_hit_result["frame_meter_adv_attacker_side"]

            # AttackEffectのヒット判定（砂ぼこりエフェクトなど）
            from src.entities.effect import AttackEffect
            for effect in effects:
                if not isinstance(effect, AttackEffect):
                    continue
                if not effect.can_deal_damage():
                    continue
                
                # エフェクトの所有者と防御側を判定
                attacker = p1 if effect.owner_side == 1 else p2
                defender = p2 if effect.owner_side == 1 else p1
                
                # ダウン中は無敵
                if bool(getattr(defender, "_down_anim_active", False)) or bool(getattr(defender, "_ko_down_anim_active", False)):
                    continue
                
                effect_hitbox = effect.get_hitbox()
                if effect_hitbox is None:
                    continue
                
                # 防御側のハートボックスと衝突判定
                defender_hurtboxes = defender.get_hurtboxes()
                hit_detected = False
                for hurtbox in defender_hurtboxes:
                    if effect_hitbox.colliderect(hurtbox):
                        hit_detected = True
                        break
                
                if not hit_detected:
                    continue
                
                # ヒット処理
                effect.register_hit()
                
                # ガード判定
                is_guarding = bool(getattr(defender, "can_guard_now", lambda: False)()) and bool(
                    getattr(defender, "is_guarding_intent", lambda: False)()
                )
                if game_state == GameState.TRAINING and training_p2_all_guard and (defender is p2):
                    is_guarding = True
                
                hit_point = (effect_hitbox.centerx, effect_hitbox.centery)
                
                if is_guarding:
                    # ガード処理
                    defender.enter_blockstun(frames=effect.blockstun_frames, crouching=defender.crouching)
                    knockback = effect.knockback_px
                    defender.knockback_vx = -float(defender.facing) * float(knockback) * 0.3
                    
                    # ガードエフェクト
                    from src.entities.effect import StaticImageBurstEffect
                    guard_img = getattr(constants, "GUARD_EFFECT_IMAGE", None)
                    if guard_img is not None:
                        effects.append(StaticImageBurstEffect(
                            image=guard_img,
                            pos=hit_point,
                            total_frames=8,
                            start_scale=1.0,
                            end_scale=0.6,
                            fadeout_frames=3,
                        ))
                else:
                    # ダメージ処理
                    defender.take_damage(effect.damage)
                    defender.enter_hitstun(frames=effect.hitstun_frames)
                    defender.hitstop_frames_left = max(defender.hitstop_frames_left, effect.hitstop_frames)
                    attacker.hitstop_frames_left = max(attacker.hitstop_frames_left, effect.hitstop_frames)
                    
                    knockback = effect.knockback_px
                    defender.knockback_vx = -float(defender.facing) * float(knockback)
                    
                    # ヒットエフェクト
                    from src.entities.effect import StaticImageBurstEffect
                    hit_img = getattr(constants, "HIT_EFFECT_IMAGE", None)
                    if hit_img is not None:
                        effects.append(StaticImageBurstEffect(
                            image=hit_img,
                            pos=hit_point,
                            total_frames=10,
                            start_scale=1.2,
                            end_scale=0.8,
                            fadeout_frames=3,
                        ))

        if shungoku_cine_frames_left <= 0 and should_update:
            # ShungokuManagerでダッシュシーケンスを更新
            dash_result = shungoku_manager.update_dash_sequence(p1, p2)
            if dash_result["hit_occurred"]:
                try:
                    pygame.mixer.music.stop()
                except Exception:
                    pass
                bgm_suspended = True
                
                # 互換性のためにローカル変数を更新
                shungoku_cine_frames_left = shungoku_state.cine_frames_left
                shungoku_attacker_side = shungoku_state.attacker_side
                shungoku_defender_side = shungoku_state.defender_side
                shungoku_hit_se_cooldown = shungoku_state.hit_se_cooldown
                shungoku_pending_damage = shungoku_state.pending_damage
                shungoku_pending_apply = shungoku_state.pending_apply
                shungoku_pending_ko = shungoku_state.pending_ko

        # 描画（ステージに描いて、最後にウィンドウへ拡大）。
        if shungoku_cine_frames_left > 0:
            # ShungokuManagerでシネマティック演出を更新
            cine_result = shungoku_manager.update_cinematic(p1, p2, effects)
            
            if cine_result["stage_bg_override"] is not None:
                stage_bg_override_img = cine_result["stage_bg_override"]
            
            # 互換性のためにローカル変数を更新
            shungoku_cine_frames_left = shungoku_state.cine_frames_left
            shungoku_ko_anim_side = shungoku_state.ko_anim_side
            shungoku_ko_anim_idx = shungoku_state.ko_anim_idx
            shungoku_ko_anim_tick = shungoku_state.ko_anim_tick
            shungoku_finish_frames_left = shungoku_state.finish_frames_left

            stage_surface.fill((0, 0, 0))
        else:
            stage_surface.fill(constants.COLOR_BG)

            stage_renderer.draw_background(
                stage_surface,
                tick_ms=int(tick_ms),
                stage_bg_frames=stage_bg_frames,
                stage_bg_img=(stage_bg_override_img or stage_bg_img),
            )

            stage_renderer.draw_rain(stage_surface)

            # グリッド表示（トレーニングモード専用）
            if game_state == GameState.TRAINING and debug_show_grid:
                hud_renderer.draw_grid(stage_surface)

            # 地面ライン（目印）。
            pygame.draw.line(
                stage_surface,
                (80, 80, 80),
                (0, constants.GROUND_Y),
                (constants.STAGE_WIDTH, constants.GROUND_Y),
                2,
            )

        # キャラクター描画（内部でデバッグ枠線も描画）。
        if shungoku_cine_frames_left <= 0:
            shungoku_bg_active = (stage_bg_override_img is not None) and (stage_bg_override_img is assets.shungoku_stage_bg_img)
            if shungoku_bg_active and int(shungoku_ko_anim_side) in {1, 2}:
                shungoku_ko_anim_tick += 1
                if int(shungoku_ko_anim_tick) >= int(shungoku_ko_anim_frames_per_image):
                    shungoku_ko_anim_tick = 0
                    if int(shungoku_ko_anim_idx) < 16:
                        shungoku_ko_anim_idx += 1
                    else:
                        shungoku_ko_anim_idx = 10

            def _draw_shungoku_ko_anim(pl: Player) -> bool:
                if not (shungoku_bg_active and int(shungoku_ko_anim_side) in {1, 2}):
                    return False
                if (int(shungoku_ko_anim_side) == 1 and pl is not p1) or (int(shungoku_ko_anim_side) == 2 and pl is not p2):
                    return False
                idx = max(1, min(16, int(shungoku_ko_anim_idx)))
                key = (5400, int(idx))
                img = getattr(pl, "_sprites", {}).get(key)
                if img is None:
                    return False
                x = int(pl.rect.centerx) - (img.get_width() // 2)
                y = int(pl.rect.bottom) - img.get_height()
                if int(getattr(pl, "facing", 1)) < 0:
                    img = pygame.transform.flip(img, True, False)
                stage_surface.blit(img, (x, y))
                return True

            drew_p1 = _draw_shungoku_ko_anim(p1)
            drew_p2 = _draw_shungoku_ko_anim(p2)
            if not drew_p1:
                p1.draw(stage_surface, debug_draw=debug_draw)
            if not drew_p2:
                p2.draw(stage_surface, debug_draw=debug_draw)

        # ヒットボックス情報表示（トレーニングモード専用、プレイヤーの後）
        if game_state == GameState.TRAINING and debug_show_grid and debug_draw:
            hud_renderer.draw_hitbox_info(stage_surface, p1=p1, p2=p2)

        # エフェクト描画（キャラより手前）。
        for e in effects:
            # AttackEffectの場合はdebug_drawフラグを渡す
            from src.entities.effect import AttackEffect
            if isinstance(e, AttackEffect):
                e.draw(stage_surface, debug_draw=debug_draw)
            else:
                e.draw(stage_surface)

        projectile_system.draw_all(stage_surface)

        if game_state == GameState.TRAINING:
            if bool(training_auto_recover_hp):
                p1_target = int(round(p1.max_hp * (float(training_hp_percent_p1) / 100.0)))
                p2_target = int(round(p2.max_hp * (float(training_hp_percent_p2) / 100.0)))
                if int(getattr(p1, "hp", 0)) < int(p1_target):
                    p1.hp = int(p1_target)
                if int(getattr(p2, "hp", 0)) < int(p2_target):
                    p2.hp = int(p2_target)
            if bool(training_auto_recover_sp):
                max_sp = int(getattr(constants, "POWER_GAUGE_MAX", 1000))
                p1_target_sp = int(round(max_sp * (float(training_sp_percent_p1) / 100.0)))
                p2_target_sp = int(round(max_sp * (float(training_sp_percent_p2) / 100.0)))
                if int(getattr(p1, "power_gauge", 0)) < int(p1_target_sp):
                    p1.power_gauge = int(p1_target_sp)
                if int(getattr(p2, "power_gauge", 0)) < int(p2_target_sp):
                    p2.power_gauge = int(p2_target_sp)

        if game_state == GameState.TRAINING and bool(frame_meter_enabled):
            def _classify(pl: Player, *, synth_fc: int) -> FrameState:
                if shungoku_cine_frames_left > 0 and (
                    (shungoku_attacker_side == 1 and pl is p1)
                    or (shungoku_attacker_side == 2 and pl is p2)
                ):
                    return FrameState.SPECIAL
                if int(getattr(pl, "hitstun_frames_left", 0)) > 0 or int(getattr(pl, "blockstun_frames_left", 0)) > 0:
                    return FrameState.STUN
                if bool(getattr(pl, "in_hitstun", False)) or bool(getattr(pl, "in_blockstun", False)):
                    return FrameState.STUN

                info = pl.get_last_move_frame_info()
                oneshot_playing = (
                    (pl.get_current_action_id() is not None)
                    and (str(getattr(pl, "_action_mode", "")) == "oneshot")
                    and (not bool(getattr(pl, "_action_finished", False)))
                )
                is_rushing = bool(getattr(pl, "is_rushing", lambda: False)())
                is_attack_like = bool(getattr(pl, "attacking", False)) or bool(oneshot_playing) or bool(is_rushing)
                if is_attack_like and (info is not None):
                    f0 = max(0, int(synth_fc) - 1)
                    if f0 < int(getattr(info, "startup_frames", 0)):
                        return FrameState.STARTUP
                    if f0 < (int(getattr(info, "startup_frames", 0)) + int(getattr(info, "active_frames", 0))):
                        return FrameState.ACTIVE
                    if f0 < int(getattr(info, "total_frames", 0)):
                        return FrameState.RECOVERY
                return FrameState.IDLE

            def _update_synth_counter(
                *,
                pl: Player,
                last_action_id: int | None,
                last_fc: int,
                synth_fc: int,
            ) -> tuple[int | None, int, int]:
                now_aid = pl.get_current_action_id()
                now_fc = int(pl.get_action_frame_counter())
                hitstop = int(getattr(pl, "hitstop_frames_left", 0)) > 0
                if now_aid is None:
                    return None, int(now_fc), int(now_fc)
                if last_action_id is None or int(now_aid) != int(last_action_id):
                    return int(now_aid), int(now_fc), int(now_fc)
                if hitstop and int(now_fc) == int(last_fc):
                    return int(last_action_id), int(now_fc), int(synth_fc) + 1
                return int(last_action_id), int(now_fc), int(now_fc)

            frame_meter_last_action_id_p1, frame_meter_last_action_fc_p1, frame_meter_synth_action_fc_p1 = _update_synth_counter(
                pl=p1,
                last_action_id=frame_meter_last_action_id_p1,
                last_fc=frame_meter_last_action_fc_p1,
                synth_fc=frame_meter_synth_action_fc_p1,
            )
            frame_meter_last_action_id_p2, frame_meter_last_action_fc_p2, frame_meter_synth_action_fc_p2 = _update_synth_counter(
                pl=p2,
                last_action_id=frame_meter_last_action_id_p2,
                last_fc=frame_meter_last_action_fc_p2,
                synth_fc=frame_meter_synth_action_fc_p2,
            )

            s1 = _classify(p1, synth_fc=frame_meter_synth_action_fc_p1)
            s2 = _classify(p2, synth_fc=frame_meter_synth_action_fc_p2)
            hs1 = int(getattr(p1, "hitstop_frames_left", 0)) > 0
            hs2 = int(getattr(p2, "hitstop_frames_left", 0)) > 0

            p1_combo = bool(getattr(p1, "is_in_combo", False))
            p2_combo = bool(getattr(p2, "is_in_combo", False))
            combo_overlap_p1 = (s1 == FrameState.ACTIVE) and (s2 == FrameState.STUN) and p2_combo
            combo_overlap_p2 = (s2 == FrameState.ACTIVE) and (s1 == FrameState.STUN) and p1_combo

            any_non_idle = (s1 != FrameState.IDLE) or (s2 != FrameState.IDLE)
            any_hitstop = bool(hs1 or hs2)
            if any_non_idle:
                frame_meter_paused = False
                frame_meter_idle_run = 0
            else:
                frame_meter_idle_run = int(frame_meter_idle_run) + 1
                if int(frame_meter_idle_run) >= 20:
                    frame_meter_paused = True

            if any_hitstop:
                frame_meter_paused = False

            if not frame_meter_paused:
                frame_meter_p1.push(FrameSample(state=s1, hitstop=bool(hs1), combo=bool(combo_overlap_p1)))
                frame_meter_p2.push(FrameSample(state=s2, hitstop=bool(hs2), combo=bool(combo_overlap_p2)))

            frame_meter_adv_frames_left = max(0, int(frame_meter_adv_frames_left) - 1)
            if frame_meter_adv_frames_left <= 0:
                frame_meter_adv_value = None
                frame_meter_adv_attacker_side = 0

            hud_renderer.draw_frame_meter(
                stage_surface,
                tracker_p1=frame_meter_p1,
                tracker_p2=frame_meter_p2,
                adv_value=frame_meter_adv_value,
                adv_frames_left=frame_meter_adv_frames_left,
                adv_attacker_side=frame_meter_adv_attacker_side,
                combo_overlap_p1=bool(combo_overlap_p1),
                combo_overlap_p2=bool(combo_overlap_p2),
            )

        if game_state == GameState.TRAINING:
            hud_renderer.draw_training_debug(
                stage_surface,
                p1=p1,
                p2=p2,
                show_key_history=bool(debug_ui_show_key_history),
                show_p1_frames=bool(debug_ui_show_p1_frames),
                show_p2_frames=bool(debug_ui_show_p2_frames),
                key_history=p1_key_history,
            )

        # HPバー描画（上部）。
        # 赤チップ（被ダメージの残り）を遅れて減らす。
        p1_hp = float(p1.hp)
        p2_hp = float(p2.hp)

        if game_state == GameState.BATTLE and int(round_over_frames_left) <= 0:
            if p1_hp <= 0 and p2_hp > 0:
                round_over_frames_left = int(constants.FPS * 2)
                round_over_winner_side = 2
                p1.enter_knockdown()
            elif p2_hp <= 0 and p1_hp > 0:
                round_over_frames_left = int(constants.FPS * 2)
                round_over_winner_side = 1
                p2.enter_knockdown()
            elif p1_hp <= 0 and p2_hp <= 0:
                round_over_frames_left = int(constants.FPS * 2)
                round_over_winner_side = None
                p1.enter_knockdown()
                p2.enter_knockdown()

        if p1_chip_hp < p1_hp:
            p1_chip_hp = p1_hp
        if p2_chip_hp < p2_hp:
            p2_chip_hp = p2_hp

        p1_chip_hp += (p1_hp - p1_chip_hp) * constants.HP_BAR_DAMAGE_LERP
        p2_chip_hp += (p2_hp - p2_chip_hp) * constants.HP_BAR_DAMAGE_LERP

        hud_renderer.draw_hp_bars(
            stage_surface,
            p1_hp=p1_hp,
            p1_chip_hp=p1_chip_hp,
            p1_max_hp=float(p1.max_hp),
            p2_hp=p2_hp,
            p2_chip_hp=p2_chip_hp,
            p2_max_hp=float(p2.max_hp),
        )

        if game_state in {GameState.BATTLE, GameState.TRAINING}:
            hud_renderer.draw_round_markers(
                stage_surface,
                p1_wins=p1_round_wins,
                p2_wins=p2_round_wins,
                tick_ms=int(tick_ms),
            )

        # Round timer (top center)
        if game_state in {GameState.BATTLE, GameState.TRAINING}:
            if (
                game_state == GameState.BATTLE
                and round_timer_frames_left is not None
                and int(round_over_frames_left) <= 0
                and int(battle_countdown_frames_left) <= 0
            ):
                round_timer_frames_left = max(0, int(round_timer_frames_left) - 1)

            if game_state == GameState.TRAINING:
                timer_text = "∞"
            else:
                left = 0 if round_timer_frames_left is None else int(round_timer_frames_left)
                sec = int(math.ceil(left / max(1, int(constants.FPS))))
                timer_text = "TIME UP" if sec <= 0 else f"{sec:02d}"

            hud_renderer.draw_timer(stage_surface, timer_text=timer_text)

        # Pre-round countdown (Battle only)
        if game_state == GameState.BATTLE and int(round_over_frames_left) <= 0 and int(battle_countdown_frames_left) > 0:
            battle_countdown_frames_left = max(0, int(battle_countdown_frames_left) - 1)
            sec_left = int(math.ceil(int(battle_countdown_frames_left) / max(1, int(constants.FPS))))
            show = max(1, sec_left)

            if battle_countdown_last_announce != int(show):
                battle_countdown_last_announce = int(show)
                if int(show) == 3 and countdown_se_3 is not None:
                    countdown_se_3.play()
                elif int(show) == 2 and countdown_se_2 is not None:
                    countdown_se_2.play()
                elif int(show) == 1 and countdown_se_1 is not None:
                    countdown_se_1.play()

            hud_renderer.draw_countdown(stage_surface, number=show)
        elif game_state == GameState.BATTLE and int(round_over_frames_left) <= 0 and int(battle_countdown_frames_left) == 0:
            if battle_countdown_last_announce is not None:
                battle_countdown_last_announce = None
                if countdown_se_go is not None:
                    countdown_se_go.play()

        if int(round_over_frames_left) > 0:
            round_over_frames_left = max(0, int(round_over_frames_left) - 1)
            hud_renderer.draw_ko(stage_surface)

            if int(round_over_frames_left) == 0 and game_state == GameState.BATTLE:
                if int(round_over_winner_side or 0) == 1:
                    p1_round_wins += 1
                elif int(round_over_winner_side or 0) == 2:
                    p2_round_wins += 1

                if int(p1_round_wins) >= 2 or int(p2_round_wins) >= 2:
                    game_state = GameState.RESULT
                    menu_open = False
                    cmdlist_open = False
                    result_menu_selection = 0
                    result_winner_side = 1 if int(p1_round_wins) >= 2 and int(p2_round_wins) < 2 else (2 if int(p2_round_wins) >= 2 and int(p1_round_wins) < 2 else None)
                    result_anim_counter = 0
                    _ensure_bgm_for_state(game_state)
                else:
                    reset_match()

        # Power gauge (super meter)
        mx = float(getattr(constants, "POWER_GAUGE_MAX", 1000))
        hud_renderer.draw_power_gauges(
            stage_surface,
            p1_power=float(getattr(p1, "power_gauge", 0)),
            p2_power=float(getattr(p2, "power_gauge", 0)),
            max_power=mx,
        )

        hud_renderer.draw_combo(stage_surface, p1=p1, p2=p2)

        scaled = pygame.transform.smoothscale(stage_surface, (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))

        pan_x = 0
        if int(shungoku_pan_frames_left) > 0:
            shungoku_pan_frames_left = max(0, int(shungoku_pan_frames_left) - 1)
            t = float(int(shungoku_pan_total_frames) - int(shungoku_pan_frames_left)) / float(max(1, int(shungoku_pan_total_frames)))
            if t < 0.5:
                ease = t / 0.5
            else:
                ease = (1.0 - t) / 0.5
            ease = max(0.0, min(1.0, float(ease)))
            pan_x = int(round(-float(shungoku_pan_target_px) * float(ease)))
        screen.blit(scaled, (int(pan_x), 0))

        # ポーズ中の表示
        if frame_paused and game_state in {GameState.BATTLE, GameState.TRAINING}:
            try:
                pause_font = pygame.font.Font(None, 48)
                pause_text = pause_font.render("PAUSED (M: Resume / >: Frame Advance)", True, (255, 255, 0))
                pause_rect = pause_text.get_rect(center=(constants.SCREEN_WIDTH // 2, 50))
                # 半透明の背景
                bg_surf = pygame.Surface((pause_rect.width + 20, pause_rect.height + 10))
                bg_surf.set_alpha(180)
                bg_surf.fill((0, 0, 0))
                screen.blit(bg_surf, (pause_rect.x - 10, pause_rect.y - 5))
                screen.blit(pause_text, pause_rect)
            except Exception:
                pass

        pygame.display.flip()

        # FPS を固定し、1フレームあたりの挙動が安定するようにする。
        clock.tick(constants.FPS)

    # 終了処理。
    pygame.quit()


if __name__ == "__main__":
    main()
