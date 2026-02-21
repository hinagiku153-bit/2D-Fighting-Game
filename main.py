from __future__ import annotations

from enum import Enum, auto
import math
import importlib.util
from pathlib import Path
from typing import Any

import pygame

from src.entities.effect import Effect
from src.entities.player import Player, PlayerInput
from src.utils import constants


class GameState(Enum):
    TITLE = auto()
    BATTLE = auto()


def _draw_hp_bar(
    surface: pygame.Surface,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    hp: float,
    chip_hp: float,
    max_hp: float,
    align_right: bool,
) -> None:
    bg_rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surface, constants.COLOR_HP_BG, bg_rect)

    hp_ratio = 0.0 if max_hp <= 0 else max(0.0, min(1.0, hp / max_hp))
    chip_ratio = 0.0 if max_hp <= 0 else max(0.0, min(1.0, chip_hp / max_hp))

    hp_w = int(w * hp_ratio)
    chip_w = int(w * chip_ratio)

    if align_right:
        chip_rect = pygame.Rect(x + (w - chip_w), y, chip_w, h)
        fill_rect = pygame.Rect(x + (w - hp_w), y, hp_w, h)
    else:
        chip_rect = pygame.Rect(x, y, chip_w, h)
        fill_rect = pygame.Rect(x, y, hp_w, h)

    pygame.draw.rect(surface, constants.COLOR_HP_CHIP, chip_rect)
    pygame.draw.rect(surface, constants.COLOR_HP_FILL, fill_rect)
    pygame.draw.rect(surface, (200, 200, 200), bg_rect, 2)


def main() -> None:
    # Pygame 初期化。
    pygame.init()

    project_root = Path(__file__).resolve().parent
    jp_font_path = project_root / "assets" / "fonts" / "TogeMaruGothic-700-Bold.ttf"
    mono_font_name = "consolas"
    if jp_font_path.exists():
        font = pygame.font.Font(str(jp_font_path), 28)
        title_font = pygame.font.Font(str(jp_font_path), 72)
        prompt_font = pygame.font.Font(str(jp_font_path), 32)
        menu_font = pygame.font.SysFont(mono_font_name, 34)
    else:
        font = pygame.font.SysFont(mono_font_name, 28)
        title_font = pygame.font.SysFont(mono_font_name, 72)
        prompt_font = pygame.font.SysFont(mono_font_name, 32)
        menu_font = font

    def _actions_have_frame_clsns(actions: list[dict[str, Any]]) -> bool:
        for action in actions:
            frames = action.get("frames", [])
            if not isinstance(frames, list):
                continue
            for frame in frames:
                if not isinstance(frame, dict):
                    continue
                clsn1 = frame.get("clsn1")
                clsn2 = frame.get("clsn2")
                if isinstance(clsn1, list) or isinstance(clsn2, list):
                    return True
        return False

    def _patch_action400_startup(actions: list[dict[str, Any]]) -> None:
        # Action 400（Jキー小キック）の発生を「入力から4フレーム目」に合わせるため、
        # 最初に clsn1 を持つフレーム以前の time 合計を 3 に調整する。
        # NOTE: 0 や負の time はアニメ進行が崩れやすいので、ここでは各フレーム time>=1 を前提にする。
        target = None
        for a in actions:
            if isinstance(a, dict) and int(a.get("action", -1)) == 400:
                target = a
                break
        if target is None:
            return

        frames = target.get("frames")
        if not isinstance(frames, list) or not frames:
            return

        first_active = None
        for i, fr in enumerate(frames):
            if not isinstance(fr, dict):
                continue
            clsn1 = fr.get("clsn1")
            if isinstance(clsn1, list) and len(clsn1) > 0:
                first_active = i
                break
        if first_active is None or first_active <= 0:
            return

        startup_frames = [fr for fr in frames[:first_active] if isinstance(fr, dict)]
        if not startup_frames:
            return

        # 予備動作フレーム数が 3 を超える場合、time>=1 のまま合計3にできないため、ここでは調整しない。
        if len(startup_frames) > 3:
            return

        # 合計3になるように 1,1,1(残りは最後へ加算) で配分する。
        remain = 3
        for idx, fr in enumerate(startup_frames):
            if idx < len(startup_frames) - 1:
                fr["time"] = 1
                remain -= 1
            else:
                fr["time"] = max(1, int(remain))

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
    p1 = Player(x=150, color=constants.COLOR_P1)
    p2 = Player(x=constants.STAGE_WIDTH - 200, color=constants.COLOR_P2)

    # MUGENの AIR（ACTIONS）と、整理済みPNG（organized）を読み込む。
    # 読み込みに失敗した場合でもゲームは起動でき、従来の矩形描画にフォールバックする。
    try:
        air_py = project_root / "assets" / "images" / "RYUKO2nd" / "ryuko_air_actions.py"
        sprites_root = project_root / "assets" / "images" / "RYUKO2nd" / "organized"

        spec = importlib.util.spec_from_file_location("ryuko_air_actions", str(air_py))
        if spec is not None and spec.loader is not None:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            actions = getattr(module, "ACTIONS", None)
            if isinstance(actions, list):
                _patch_action400_startup(actions)
                if not _actions_have_frame_clsns(actions):
                    air_parser_py = project_root / "scripts" / "organize_ryuko2nd_assets.py"
                    air_file = project_root / "assets" / "images" / "RYUKO2nd" / "RYUKO.AIR"
                    parser_spec = importlib.util.spec_from_file_location("ryuko_air_parser", str(air_parser_py))
                    if parser_spec is not None and parser_spec.loader is not None:
                        parser_module = importlib.util.module_from_spec(parser_spec)
                        parser_spec.loader.exec_module(parser_module)
                        parse_air_file = getattr(parser_module, "parse_air_file", None)
                        if callable(parse_air_file):
                            parsed_actions = parse_air_file(air_file)
                            if isinstance(parsed_actions, list):
                                actions = parsed_actions
                                _patch_action400_startup(actions)
                p1.set_mugen_animation(actions=actions, sprites_root=sprites_root)
                p2.set_mugen_animation(actions=actions, sprites_root=sprites_root)
    except Exception:
        pass

    # ヒットエフェクト（火花）読み込み。
    # 連番PNGを置いたフォルダをここで指定する。
    spark_folder_candidates = [
        project_root / "assets" / "images" / "RYUKO2nd" / "organized" / "other" / "hit_spark",
        project_root / "assets" / "effects" / "hit_spark",
    ]
    spark_frames: list[pygame.Surface] = []
    for folder in spark_folder_candidates:
        if not folder.exists() or not folder.is_dir():
            continue
        files = sorted([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == ".png"])
        if not files:
            continue
        frames: list[pygame.Surface] = []
        for p in files:
            try:
                frames.append(pygame.image.load(str(p)).convert_alpha())
            except pygame.error:
                continue
        if frames:
            spark_frames = frames
            break

    effects: list[Effect] = []

    # 判定枠線（Hurtbox/Pushbox/Hitbox）を描画するかどうか。
    # F3 で切り替える。
    debug_draw = constants.DEBUG_DRAW_DEFAULT

    # ESC で表示する簡易メニュー。
    menu_open = False
    menu_selection = 0

    # タイトル画面とバトル画面の状態管理。
    game_state = GameState.TITLE
    title_start_keys = {pygame.K_u, pygame.K_i, pygame.K_o, pygame.K_j, pygame.K_k, pygame.K_l}
    title_menu_items = ["BATTLE", "SETTING", "EXIT"]
    title_menu_selection = 0

    title_bg_img: pygame.Surface | None = None
    for pattern in (
        "assets/images/RYUKO2nd/organized/stand/*.png",
        "assets/images/RYUKO2nd/organized/**/*.png",
    ):
        candidates = sorted(project_root.glob(pattern))
        if not candidates:
            continue
        try:
            title_bg_img = pygame.image.load(str(candidates[0])).convert_alpha()
            break
        except pygame.error:
            title_bg_img = None
    start_se: pygame.mixer.Sound | None = None
    for rel in ("start.wav", "start.ogg", "start.mp3"):
        se_path = project_root / "assets" / "sounds" / rel
        if not se_path.exists():
            continue
        try:
            start_se = pygame.mixer.Sound(str(se_path))
            break
        except pygame.error:
            pass

    # “押した瞬間だけ True” にしたい入力は、KEYDOWN でトリガを立てて
    # フレームの先頭で False に戻す（エッジ入力）。
    p1_jump_pressed = False
    p2_jump_pressed = False
    p1_attack_id: str | None = None
    p2_attack_id: str | None = None

    # HPバー用の「赤チップ残り」値（見た目用）。
    p1_chip_hp: float = float(p1.max_hp)
    p2_chip_hp: float = float(p2.max_hp)

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
        nonlocal p1_chip_hp, p2_chip_hp

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

        p1.hp = p1.max_hp
        p2.hp = p2.max_hp
        p1_chip_hp = float(p1.max_hp)
        p2_chip_hp = float(p2.max_hp)

        p1.hitstop_frames_left = 0
        p2.hitstop_frames_left = 0
        p1._attack_frames_left = 0
        p2._attack_frames_left = 0
        p1._attack_has_hit = False
        p2._attack_has_hit = False
        p1._attack_id = None
        p2._attack_id = None

    _apply_resolution((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
    reset_match()

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
                if event.key == pygame.K_F3:
                    debug_draw = not debug_draw
                    continue

                if game_state == GameState.TITLE and menu_open:
                    if event.key == pygame.K_ESCAPE:
                        menu_open = False
                    elif event.key == pygame.K_UP:
                        menu_selection = (menu_selection - 1) % 2
                    elif event.key == pygame.K_DOWN:
                        menu_selection = (menu_selection + 1) % 2
                    elif event.key == pygame.K_LEFT:
                        if menu_selection == 0:
                            current_res_index = (current_res_index - 1) % len(resolutions)
                    elif event.key == pygame.K_RIGHT:
                        if menu_selection == 0:
                            current_res_index = (current_res_index + 1) % len(resolutions)
                    elif event.key == pygame.K_RETURN:
                        if menu_selection == 0:
                            _apply_resolution(resolutions[current_res_index])
                            reset_match()
                        elif menu_selection == 1:
                            menu_open = False
                    continue

                if game_state == GameState.TITLE:
                    if event.key == pygame.K_UP:
                        title_menu_selection = (title_menu_selection - 1) % len(title_menu_items)
                    elif event.key == pygame.K_DOWN:
                        title_menu_selection = (title_menu_selection + 1) % len(title_menu_items)
                    elif event.key == pygame.K_RETURN or event.key in title_start_keys:
                        selected = title_menu_items[title_menu_selection]
                        if selected == "BATTLE":
                            if start_se is not None:
                                start_se.play()
                            game_state = GameState.BATTLE
                            menu_open = False
                            reset_match()
                        elif selected == "SETTING":
                            menu_open = True
                            menu_selection = 0
                        elif selected == "EXIT":
                            running = False
                    continue

                if event.key == pygame.K_r:
                    reset_match()
                elif event.key == pygame.K_ESCAPE:
                    menu_open = not menu_open
                elif menu_open:
                    if event.key == pygame.K_UP:
                        menu_selection = (menu_selection - 1) % 2
                    elif event.key == pygame.K_DOWN:
                        menu_selection = (menu_selection + 1) % 2
                    elif event.key == pygame.K_LEFT:
                        if menu_selection == 0:
                            current_res_index = (current_res_index - 1) % len(resolutions)
                    elif event.key == pygame.K_RIGHT:
                        if menu_selection == 0:
                            current_res_index = (current_res_index + 1) % len(resolutions)
                    elif event.key == pygame.K_RETURN:
                        if menu_selection == 0:
                            _apply_resolution(resolutions[current_res_index])
                            reset_match()
                        elif menu_selection == 1:
                            menu_open = False
                elif event.key == pygame.K_w:
                    p1_jump_pressed = True
                elif event.key == pygame.K_UP:
                    p2_jump_pressed = True
                elif event.key == pygame.K_SEMICOLON:
                    p2_attack_id = "P2_L_PUNCH"
                elif event.key == pygame.K_u:
                    p1_attack_id = "P1_U_LP"
                elif event.key == pygame.K_i:
                    p1_attack_id = "P1_I_MP"
                elif event.key == pygame.K_o:
                    p1_attack_id = "P1_O_HP"
                elif event.key == pygame.K_j:
                    p1_attack_id = "P1_J_LK"
                elif event.key == pygame.K_k:
                    p1_attack_id = "P1_K_MK"
                elif event.key == pygame.K_l:
                    p1_attack_id = "P1_L_HK"

        if menu_open:
            stage_surface.fill(constants.COLOR_BG)

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

            title = font.render("メニュー (ESC)", True, (255, 255, 255))
            screen.blit(title, (40, 40))

            res_w, res_h = resolutions[current_res_index]
            items = [
                f"解像度: {res_w}x{res_h}  (←→ 変更 / Enter 適用)",
                "閉じる",
            ]
            y = 90
            for i, text in enumerate(items):
                color = (255, 255, 0) if i == menu_selection else (230, 230, 230)
                surf = font.render(text, True, color)
                screen.blit(surf, (60, y))
                y += 34

            pygame.display.flip()
            clock.tick(constants.FPS)
            continue

        if game_state == GameState.TITLE:
            stage_surface.fill((0, 0, 0))

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
            tick = pygame.time.get_ticks()
            for i, name in enumerate(title_menu_items):
                selected = i == title_menu_selection
                color = (80, 255, 220) if selected else (210, 210, 210)
                shake = int(3 * math.sin((tick / 120.0) + i)) if selected else 0
                text_surf = menu_font.render(name, True, color)
                text_rect = text_surf.get_rect(center=(cx + shake, base_y + i * 50))
                screen.blit(text_surf, text_rect)
                if selected:
                    arrow = menu_font.render(">", True, (80, 255, 220))
                    arrow_rect = arrow.get_rect(midright=(text_rect.left - 14, text_rect.centery))
                    screen.blit(arrow, arrow_rect)

            pygame.display.flip()
            clock.tick(constants.FPS)
            continue

        # 押しっぱなし入力（左右移動・しゃがみ）は get_pressed で取得。
        keys = pygame.key.get_pressed()

        # move_x は -1/0/+1 の3値にする。
        p1_move_x = int(keys[pygame.K_d]) - int(keys[pygame.K_a])
        p2_move_x = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])

        p1_crouch = bool(keys[pygame.K_s])
        p2_crouch = bool(keys[pygame.K_DOWN])

        # 向きは相手の位置から決める（Phase 1 の簡易仕様）。
        p1.facing = 1 if p2.rect.centerx >= p1.rect.centerx else -1
        p2.facing = 1 if p1.rect.centerx >= p2.rect.centerx else -1

        # 入力（intent）を Player に渡す。
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

        # 物理更新。
        p1.update()
        p2.update()

        # エフェクト更新。
        for e in effects:
            e.update()
        effects = [e for e in effects if not e.finished]

        # 押し合い（Pushbox）解決。
        # Pushbox が重なったら、x方向に左右へ押し戻して重なりを解消する。
        p1_push = p1.get_pushbox()
        p2_push = p2.get_pushbox()
        if p1_push.colliderect(p2_push):
            overlap_x = min(p1_push.right - p2_push.left, p2_push.right - p1_push.left)
            if overlap_x > 0:
                push = (overlap_x + 1) // 2
                if p1.rect.centerx < p2.rect.centerx:
                    p1.pos_x -= float(push)
                    p2.pos_x += float(push)
                else:
                    p1.pos_x += float(push)
                    p2.pos_x -= float(push)

                # 押し戻し後も画面外へ出ないように補正する。
                p1_half_w = p1.rect.width / 2.0
                p2_half_w = p2.rect.width / 2.0
                p1.pos_x = max(p1_half_w, min(constants.SCREEN_WIDTH - p1_half_w, p1.pos_x))
                p2.pos_x = max(p2_half_w, min(constants.SCREEN_WIDTH - p2_half_w, p2.pos_x))
                p1.rect.midbottom = (int(p1.pos_x), int(p1.pos_y))
                p2.rect.midbottom = (int(p2.pos_x), int(p2.pos_y))

        # ヒット判定（Hitbox vs Hurtbox）。
        # - 攻撃ごとにダメージ/ノックバック/ヒットストップを変える。
        # - 1回の攻撃で1回だけダメージを与える（多段ヒット防止）。
        def _apply_hit(attacker: Player, defender: Player) -> None:
            hitboxes = attacker.get_hitboxes()
            if not hitboxes:
                return

            hurtboxes = defender.get_hurtboxes()
            hit_point: tuple[int, int] | None = None
            for hitbox in hitboxes:
                for hurtbox in hurtboxes:
                    if not hitbox.colliderect(hurtbox):
                        continue
                    overlap = hitbox.clip(hurtbox)
                    if overlap.width > 0 and overlap.height > 0:
                        hit_point = overlap.center
                    else:
                        hit_point = hitbox.center
                    break
                if hit_point is not None:
                    break
            if hit_point is None:
                return

            # 多段ヒット対応：このフレームの clsn1 グループ（hit_id）が未登録なら当たりを許可。
            if not attacker.can_deal_damage():
                return

            attack_id = getattr(attacker, "_attack_id", None)
            spec = constants.ATTACK_SPECS.get(str(attack_id))
            if spec is None:
                damage = 50
                knockback_px = 12
                hitstop_frames = constants.HITSTOP_DEFAULT_FRAMES
                attacker_recoil_px = int(getattr(constants, "ATTACKER_RECOIL_PX_DEFAULT", 3))
            else:
                damage = int(spec["damage"])
                knockback_px = int(spec["knockback_px"])
                hitstop_frames = int(spec["hitstop_frames"])
                attacker_recoil_px = int(spec.get("attacker_recoil_px", getattr(constants, "ATTACKER_RECOIL_PX_DEFAULT", 3)))

            # ガード判定：後ろ入力中（defender.holding_back）ならガード成功。
            # まずは「後ろに下がっている間に攻撃を受けると、ダメージを受けずにガードモーション」を成立させる。
            # ガード受付は「衝突したそのフレーム」で判定する（アニメ遷移待ちなし）。
            # - 入力は Player 側でバッファされているため、のけぞり終了直前やヒットストップ中でも間に合う。
            # - blockstun 中は True blockstring として自動ガード継続する。
            is_guarding = bool(getattr(defender, "can_guard_now", lambda: False)()) and bool(
                getattr(defender, "is_guarding_intent", lambda: False)()
            )

            if is_guarding:
                chip_ratio = float(getattr(constants, "GUARD_CHIP_DAMAGE_RATIO", 0.0))
                chip_damage = int(max(0, round(damage * chip_ratio)))

                defender.take_damage(chip_damage)

                base_guard_kb = int(getattr(constants, "GUARD_KNOCKBACK_PX_DEFAULT", knockback_px))
                guard_mul = float(getattr(constants, "GUARD_KNOCKBACK_MULTIPLIER", 1.35))
                guard_knockback = int(max(0, round(base_guard_kb * guard_mul)))

                # 壁際なら、押せない分は攻撃側が倍引っ込む。
                half_w = defender.rect.width / 2.0
                at_left_wall = defender.pos_x <= (half_w + 0.01)
                at_right_wall = defender.pos_x >= ((constants.STAGE_WIDTH - half_w) - 0.01)
                toward_left = attacker.facing < 0
                toward_right = attacker.facing > 0
                defender_blocked_by_wall = (toward_left and at_left_wall) or (toward_right and at_right_wall)

                if defender_blocked_by_wall:
                    attacker.apply_knockback(dir_x=-attacker.facing, amount_px=guard_knockback * 2)
                else:
                    defender.apply_knockback(dir_x=attacker.facing, amount_px=guard_knockback)

                # ガード硬直＋ガードモーション。
                crouch_guard = bool(getattr(defender, "crouching", False))
                defender.enter_blockstun(crouching=crouch_guard)

                # セパレーション：攻撃側も少し後ろへ下がる。
                attacker.apply_knockback(dir_x=-attacker.facing, amount_px=attacker_recoil_px)
                # ガードではコンボ/ヒット登録は増やさない（多段ガードで無限にカウントされないようにする）。
                attacker.register_current_hit()

                extra_hitstop = int(getattr(constants, "HIT_EFFECT_EXTRA_HITSTOP_FRAMES", 4))
                hitstop_total = int(hitstop_frames) + max(0, extra_hitstop)
                attacker.hitstop_frames_left = max(attacker.hitstop_frames_left, hitstop_total)
                defender.hitstop_frames_left = max(defender.hitstop_frames_left, hitstop_total)
                return

            defender.take_damage(damage)
            half_w = defender.rect.width / 2.0
            at_left_wall = defender.pos_x <= (half_w + 0.01)
            at_right_wall = defender.pos_x >= ((constants.STAGE_WIDTH - half_w) - 0.01)
            toward_left = attacker.facing < 0
            toward_right = attacker.facing > 0
            defender_blocked_by_wall = (toward_left and at_left_wall) or (toward_right and at_right_wall)
            if defender_blocked_by_wall:
                attacker.apply_knockback(dir_x=-attacker.facing, amount_px=int(knockback_px) * 2)
            else:
                defender.apply_knockback(dir_x=attacker.facing, amount_px=knockback_px)
            defender.enter_hitstun()

            # セパレーション：攻撃側も少し後ろへ下がる。
            attacker.apply_knockback(dir_x=-attacker.facing, amount_px=attacker_recoil_px)
            attacker.mark_damage_dealt()

            # 衝突点に火花エフェクトを生成（画像がある場合）。
            if spark_frames:
                effects.append(Effect(frames=spark_frames, pos=hit_point, frames_per_image=2))

            extra_hitstop = int(getattr(constants, "HIT_EFFECT_EXTRA_HITSTOP_FRAMES", 4))
            hitstop_total = int(hitstop_frames) + max(0, extra_hitstop)

            attacker.hitstop_frames_left = max(attacker.hitstop_frames_left, hitstop_total)
            defender.hitstop_frames_left = max(defender.hitstop_frames_left, hitstop_total)

        _apply_hit(p1, p2)
        _apply_hit(p2, p1)

        # 描画（ステージに描いて、最後にウィンドウへ拡大）。
        stage_surface.fill(constants.COLOR_BG)

        # 地面ライン（目印）。
        pygame.draw.line(
            stage_surface,
            (80, 80, 80),
            (0, constants.GROUND_Y),
            (constants.STAGE_WIDTH, constants.GROUND_Y),
            2,
        )

        # キャラクター描画（内部でデバッグ枠線も描画）。
        p1.draw(stage_surface, debug_draw=debug_draw)
        p2.draw(stage_surface, debug_draw=debug_draw)

        # エフェクト描画（キャラより手前）。
        for e in effects:
            e.draw(stage_surface)

        if debug_draw:
            p1_info = p1.get_last_move_frame_info()
            if p1_info is not None:
                lines = [
                    f"P1 {p1_info.attack_id}",
                    f"Action: {p1.get_current_action_id()}  Frame: {p1.get_action_frame_counter()}f",
                    f"Combo: {p1.get_combo_count()}",
                    f"Total: {p1_info.total_frames}f",
                    f"Startup: {p1_info.startup_frames}f",
                    f"Active: {p1_info.active_frames}f",
                    f"Recovery: {p1_info.recovery_frames}f",
                ]
                x = 12
                y = 56
                for i, t in enumerate(lines):
                    surf = font.render(t, True, (240, 240, 240))
                    stage_surface.blit(surf, (x, y + i * 22))

            p2_info = p2.get_last_move_frame_info()
            if p2_info is not None:
                lines = [
                    f"P2 {p2_info.attack_id}",
                    f"Action: {p2.get_current_action_id()}  Frame: {p2.get_action_frame_counter()}f",
                    f"Combo: {p2.get_combo_count()}",
                    f"Total: {p2_info.total_frames}f",
                    f"Startup: {p2_info.startup_frames}f",
                    f"Active: {p2_info.active_frames}f",
                    f"Recovery: {p2_info.recovery_frames}f",
                ]
                x = constants.STAGE_WIDTH - 12
                y = 56
                for i, t in enumerate(lines):
                    surf = font.render(t, True, (240, 240, 240))
                    rect = surf.get_rect(topright=(x, y + i * 22))
                    stage_surface.blit(surf, rect)

        # HPバー描画（上部）。
        # 赤チップ（被ダメージの残り）を遅れて減らす。
        p1_hp = float(p1.hp)
        p2_hp = float(p2.hp)

        if p1_chip_hp < p1_hp:
            p1_chip_hp = p1_hp
        if p2_chip_hp < p2_hp:
            p2_chip_hp = p2_hp

        p1_chip_hp += (p1_hp - p1_chip_hp) * constants.HP_BAR_DAMAGE_LERP
        p2_chip_hp += (p2_hp - p2_chip_hp) * constants.HP_BAR_DAMAGE_LERP

        _draw_hp_bar(
            stage_surface,
            x=constants.HP_BAR_MARGIN_X,
            y=constants.HP_BAR_MARGIN_Y,
            w=constants.HP_BAR_WIDTH,
            h=constants.HP_BAR_HEIGHT,
            hp=p1_hp,
            chip_hp=p1_chip_hp,
            max_hp=float(p1.max_hp),
            align_right=False,
        )
        _draw_hp_bar(
            stage_surface,
            x=constants.STAGE_WIDTH - constants.HP_BAR_MARGIN_X - constants.HP_BAR_WIDTH,
            y=constants.HP_BAR_MARGIN_Y,
            w=constants.HP_BAR_WIDTH,
            h=constants.HP_BAR_HEIGHT,
            hp=p2_hp,
            chip_hp=p2_chip_hp,
            max_hp=float(p2.max_hp),
            align_right=True,
        )

        scaled = pygame.transform.smoothscale(stage_surface, (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
        screen.blit(scaled, (0, 0))

        pygame.display.flip()

        # FPS を固定し、1フレームあたりの挙動が安定するようにする。
        clock.tick(constants.FPS)

    # 終了処理。
    pygame.quit()


if __name__ == "__main__":
    main()
