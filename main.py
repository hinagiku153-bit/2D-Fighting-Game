from __future__ import annotations

from enum import Enum, auto
import json
import math
import importlib.util
import os
import random
import re
from pathlib import Path
from typing import Any

import pygame

from src.entities.effect import Effect
from src.entities.effect import Projectile
from src.entities.effect import SuperProjectile
from src.entities.player import Player, PlayerInput
from src.characters.ryuko import RYUKO
from src.ui import hud
from src.utils import constants
from src.utils.paths import resource_path


class GameState(Enum):
    TITLE = auto()
    BATTLE = auto()
    TRAINING = auto()
    CHAR_SELECT = auto()
    RESULT = auto()


def _load_stage_frames() -> list[pygame.Surface]:
    frames: list[pygame.Surface] = []
    for name in ("01.png", "02.png", "03.png", "04.png"):
        p = resource_path(Path("assets/images/stage") / name)
        if not p.exists():
            return []
        try:
            frames.append(pygame.image.load(str(p)).convert_alpha())
        except pygame.error:
            return []
    return frames


def _draw_stage_background(
    surface: pygame.Surface,
    *,
    tick_ms: int,
    stage_bg_frames: list[pygame.Surface],
    stage_bg_img: pygame.Surface | None,
) -> None:
    bg_img: pygame.Surface | None = None
    if stage_bg_frames:
        bg_img = stage_bg_frames[0]
    else:
        bg_img = stage_bg_img

    if bg_img is not None:
        bg = pygame.transform.smoothscale(bg_img, (constants.STAGE_WIDTH, constants.STAGE_HEIGHT))
        surface.blit(bg, (0, 0))

        dark = pygame.Surface((constants.STAGE_WIDTH, constants.STAGE_HEIGHT), pygame.SRCALPHA)
        dark.fill((20, 40, 70, 95))
        surface.blit(dark, (0, 0))


def _init_rain_drops(count: int) -> list[dict[str, float]]:
    drops: list[dict[str, float]] = []
    for _ in range(max(0, int(count))):
        drops.append(
            {
                "x": float(random.randrange(0, constants.STAGE_WIDTH)),
                "y": float(random.randrange(-constants.STAGE_HEIGHT, constants.STAGE_HEIGHT)),
                "vy": float(random.uniform(9.0, 15.0)),
                "vx": float(random.uniform(-1.0, 0.8)),
                "len": float(random.uniform(10.0, 18.0)),
                "a": float(random.uniform(90.0, 150.0)),
            }
        )
    return drops


def _update_rain_drops(drops: list[dict[str, float]]) -> None:
    for d in drops:
        d["x"] = float(d.get("x", 0.0)) + float(d.get("vx", 0.0))
        d["y"] = float(d.get("y", 0.0)) + float(d.get("vy", 0.0))

        if d["y"] > float(constants.STAGE_HEIGHT + 30):
            d["y"] = float(random.uniform(-120.0, -20.0))
            d["x"] = float(random.randrange(-20, constants.STAGE_WIDTH + 20))
        if d["x"] < -40:
            d["x"] = float(constants.STAGE_WIDTH + 40)
        if d["x"] > float(constants.STAGE_WIDTH + 40):
            d["x"] = float(-40)


def _draw_rain(surface: pygame.Surface, *, drops: list[dict[str, float]]) -> None:
    if not drops:
        return
    rain = pygame.Surface((constants.STAGE_WIDTH, constants.STAGE_HEIGHT), pygame.SRCALPHA)
    for d in drops:
        x = int(d.get("x", 0.0))
        y = int(d.get("y", 0.0))
        ln = int(d.get("len", 14.0))
        a = int(max(0, min(255, int(d.get("a", 120.0)))))
        pygame.draw.line(rain, (170, 210, 255, a), (x, y), (x - 2, y + ln), 1)
    surface.blit(rain, (0, 0))


def _draw_power_gauge(
    surface: pygame.Surface,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    value: float,
    max_value: float,
    align_right: bool,
) -> None:
    hud.draw_power_gauge(surface, x=x, y=y, w=w, h=h, value=value, max_value=max_value, align_right=align_right)


def main() -> None:
    # Pygame 初期化。
    pygame.init()

    def _settings_path() -> Path:
        # 実行ファイル化（PyInstaller）時でも書き込みできるように、ユーザー領域へ保存する。
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "2D-Fighting-Game" / "settings.json"
        return Path.home() / ".2d_fighting_game_settings.json"

    def _load_settings() -> dict[str, Any]:
        p = _settings_path()
        try:
            if p.exists():
                return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    def _save_settings(data: dict[str, Any]) -> None:
        p = _settings_path()
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    settings = _load_settings()
    bgm_volume_level = int(settings.get("bgm_volume_level", 70))
    bgm_volume_level = max(0, min(100, bgm_volume_level))

    se_volume_level = int(settings.get("se_volume_level", 60))
    se_volume_level = max(0, min(100, se_volume_level))

    default_keybinds: dict[str, int] = {
        "P1_LEFT": int(pygame.K_a),
        "P1_RIGHT": int(pygame.K_d),
        "P1_DOWN": int(pygame.K_s),
        "P1_JUMP": int(pygame.K_w),
        "P1_LP": int(pygame.K_u),
        "P1_MP": int(pygame.K_i),
        "P1_HP": int(pygame.K_o),
        "P1_LK": int(pygame.K_j),
        "P1_MK": int(pygame.K_k),
        "P1_HK": int(pygame.K_l),
        "P2_LEFT": int(pygame.K_LEFT),
        "P2_RIGHT": int(pygame.K_RIGHT),
        "P2_DOWN": int(pygame.K_DOWN),
        "P2_JUMP": int(pygame.K_UP),
        "P2_ATTACK": int(pygame.K_SEMICOLON),
        "QUICK_RESET": int(pygame.K_r),
    }

    keybinds: dict[str, int] = dict(default_keybinds)
    try:
        raw = settings.get("keybinds", {})
        if isinstance(raw, dict):
            for k, v in raw.items():
                if k in default_keybinds:
                    try:
                        keybinds[str(k)] = int(v)
                    except (TypeError, ValueError):
                        pass
    except Exception:
        pass

    def _save_keybinds() -> None:
        settings["keybinds"] = dict(keybinds)
        _save_settings(settings)

    def _key_name(code: int) -> str:
        try:
            return str(pygame.key.name(int(code)))
        except Exception:
            return str(code)

    project_root = resource_path(".")
    jp_font_path = resource_path("assets/fonts/TogeMaruGothic-700-Bold.ttf")
    mono_font_name = "consolas"
    if jp_font_path.exists():
        font = pygame.font.Font(str(jp_font_path), 28)
        title_font = pygame.font.Font(str(jp_font_path), 72)
        prompt_font = pygame.font.Font(str(jp_font_path), 32)
        keycfg_font = pygame.font.Font(str(jp_font_path), 26)
        debug_font = pygame.font.Font(str(jp_font_path), 22)
        menu_font = pygame.font.SysFont(mono_font_name, 34)
    else:
        font = pygame.font.SysFont(mono_font_name, 28)
        title_font = pygame.font.SysFont(mono_font_name, 72)
        prompt_font = pygame.font.SysFont(mono_font_name, 32)
        keycfg_font = pygame.font.SysFont(mono_font_name, 26)
        debug_font = pygame.font.SysFont(mono_font_name, 22)
        menu_font = pygame.font.SysFont(mono_font_name, 34)

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

    def _inject_special_actions(actions: list[dict[str, Any]]) -> None:
        # 波動拳（6040）/真空波動拳（6050）を、PNG連番を再生できるように補助的に注入する。
        hadoken_action_id = int(getattr(constants, "HADOKEN_ACTION_ID", 6040))
        last_time = int(getattr(constants, "HADOKEN_ACTION_LAST_FRAME_TIME", 40))
        if not any(isinstance(a, dict) and int(a.get("action", -1)) == hadoken_action_id for a in actions):
            actions.append(
                {
                    "action": hadoken_action_id,
                    "frames": [
                        {"group": hadoken_action_id, "index": 1, "x": 0, "y": 0, "time": 3, "flags": [], "clsn1": [], "clsn2": []},
                        {"group": hadoken_action_id, "index": 2, "x": 0, "y": 0, "time": 3, "flags": [], "clsn1": [], "clsn2": []},
                        {"group": hadoken_action_id, "index": 3, "x": 0, "y": 0, "time": last_time, "flags": [], "clsn1": [], "clsn2": []},
                    ],
                }
            )

        shinku_action_id = int(getattr(constants, "SHINKU_HADOKEN_ACTION_ID", 8000))
        start_i = int(getattr(constants, "SHINKU_HADOKEN_MOTION_START_INDEX", 1))
        end_i = int(getattr(constants, "SHINKU_HADOKEN_MOTION_END_INDEX", 6))
        if not any(isinstance(a, dict) and int(a.get("action", -1)) == shinku_action_id for a in actions):
            frames: list[dict[str, Any]] = []
            for idx in range(start_i, end_i + 1):
                frames.append(
                    {
                        "group": shinku_action_id,
                        "index": idx,
                        "x": 0,
                        "y": 0,
                        "time": 3,
                        "flags": [],
                        "clsn1": [],
                        "clsn2": [],
                    }
                )
            if frames:
                frames[-1]["time"] = 12
            actions.append({"action": shinku_action_id, "frames": frames})

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
    p1 = Player(x=150, color=constants.COLOR_P1, character=RYUKO)
    p2 = Player(x=constants.STAGE_WIDTH - 200, color=constants.COLOR_P2, character=RYUKO)

    loaded_actions: list[dict[str, Any]] | None = None
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
                _patch_action400_startup(actions)

                _inject_special_actions(actions)
                if not _actions_have_frame_clsns(actions):
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
                                _patch_action400_startup(actions)
                                _inject_special_actions(actions)
                loaded_actions = actions
                actions_by_id = {int(a.get("action")): a for a in actions if isinstance(a, dict) and "action" in a}
                p1.set_mugen_animation(actions=actions, sprites_root=sprites_root)
                p2.set_mugen_animation(actions=actions, sprites_root=sprites_root)
    except Exception:
        pass

    # ヒットエフェクト（火花）読み込み。
    # 連番PNGを置いたフォルダをここで指定する。
    spark_folder_candidates = [
        resource_path("assets/images/RYUKO2nd/organized/other/hit_spark"),
        resource_path("assets/effects/hit_spark"),
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
    projectiles: list[Projectile] = []

    hadoken_proj_frames: list[pygame.Surface] | None = None
    try:
        hadoken_proj_frames = []
        for idx in range(4, 10):
            key = (6040, idx)
            img = getattr(p1, "_sprites", {}).get(key)
            if img is None:
                img = getattr(p2, "_sprites", {}).get(key)
            if img is not None:
                hadoken_proj_frames.append(img)
        if not hadoken_proj_frames:
            hadoken_proj_frames = None
    except Exception:
        hadoken_proj_frames = None

    if hadoken_proj_frames is None:
        hadoken_proj_frames = Projectile.load_frames_any(
            png_path=Path("assets/images/hadoken.png"),
            folder=Path("assets/images/hadoken"),
        )
    if hadoken_proj_frames is None and spark_frames:
        hadoken_proj_frames = spark_frames

    def _scale_frames(frames: list[pygame.Surface] | None, *, scale: float) -> list[pygame.Surface] | None:
        if frames is None:
            return None
        out: list[pygame.Surface] = []
        s = float(scale)
        for img in frames:
            w = max(1, int(round(img.get_width() * s)))
            h = max(1, int(round(img.get_height() * s)))
            out.append(pygame.transform.smoothscale(img, (w, h)))
        return out

    hadoken_proj_frames = _scale_frames(hadoken_proj_frames, scale=0.85)

    shinku_proj_frames: list[pygame.Surface] | None = None
    try:
        proj_group = int(getattr(constants, "SHINKU_HADOKEN_PROJECTILE_GROUP_ID", 8001))
        proj_start = int(getattr(constants, "SHINKU_HADOKEN_PROJECTILE_START_INDEX", 1))
        proj_end = int(getattr(constants, "SHINKU_HADOKEN_PROJECTILE_END_INDEX", 7))
        shinku_proj_frames = []
        for idx in range(proj_start, proj_end + 1):
            key = (proj_group, idx)
            img = getattr(p1, "_sprites", {}).get(key)
            if img is None:
                img = getattr(p2, "_sprites", {}).get(key)
            if img is not None:
                shinku_proj_frames.append(img)
        if not shinku_proj_frames:
            shinku_proj_frames = None
    except Exception:
        shinku_proj_frames = None

    if shinku_proj_frames is None and spark_frames:
        shinku_proj_frames = spark_frames

    shinku_proj_frames = _scale_frames(shinku_proj_frames, scale=0.80)

    rush_dust_frames: list[pygame.Surface] = []
    try:
        rush_dust_frames = []
        for idx in range(1, 9):
            key = (6521, idx)
            img = getattr(p1, "_sprites", {}).get(key)
            if img is None:
                img = getattr(p2, "_sprites", {}).get(key)
            if img is not None:
                rush_dust_frames.append(img)
        if not rush_dust_frames:
            base = resource_path("assets/images/RYUKO2nd/organized/hit")
            candidates = sorted(base.glob("*_6521-*.png"))

            def _suffix(p: Path) -> int:
                m = re.search(r"6521-(\d+)", p.name)
                if m:
                    try:
                        return int(m.group(1))
                    except ValueError:
                        return 0
                return 0

            candidates = sorted(candidates, key=_suffix)
            for p in candidates:
                try:
                    rush_dust_frames.append(pygame.image.load(str(p)).convert_alpha())
                except pygame.error:
                    continue
    except Exception:
        rush_dust_frames = []

    def _spawn_hadoken(attacker: Player) -> None:
        side = 1 if attacker is p1 else 2
        x = float(attacker.rect.centerx + attacker.facing * 34)
        y = float(attacker.rect.centery - 10)
        vx = float(attacker.facing * 8)
        projectiles.append(
            Projectile(
                pos=pygame.Vector2(x, y),
                vel=pygame.Vector2(vx, 0.0),
                owner_side=side,
                radius=8,
                frames_left=90,
                damage=55,
                hitstun_frames=20,
                frames=hadoken_proj_frames,
                frames_per_image=3,
            )
        )

    def _spawn_shinku(attacker: Player) -> None:
        side = 1 if attacker is p1 else 2
        x = float(attacker.rect.centerx + attacker.facing * 44)
        y = float(attacker.rect.centery - 18)
        vx = float(attacker.facing * 6)
        projectiles.append(
            SuperProjectile(
                pos=pygame.Vector2(x, y),
                vel=pygame.Vector2(vx, 0.0),
                owner_side=side,
                radius=12,
                frames_left=120,
                damage=35,
                hitstun_frames=12,
                frames=shinku_proj_frames,
                frames_per_image=2,
                hit_interval_frames=4,
                max_hits=5,
                push_on_hit_px=3,
            )
        )

    # 判定枠線（Hurtbox/Pushbox/Hitbox）を描画するかどうか。
    # F3 で切り替える。
    debug_draw = constants.DEBUG_DRAW_DEFAULT

    debugmenu_open = False
    debugmenu_selection = 0
    debug_ui_show_key_history = True
    debug_ui_show_p1_frames = True
    debug_ui_show_p2_frames = True

    # ESC で表示する簡易メニュー。
    menu_open = False
    menu_selection = 0
    cmdlist_open = False
    cmdlist_selection = 0
    cmdlist_preview_start_ms = 0
    cmdlist_closing = False
    cmdlist_close_start_ms = 0

    keyconfig_open = False
    keyconfig_selection = 0
    keyconfig_waiting_action: str | None = None

    training_settings_open = False
    training_settings_selection = 0
    training_hp_percent_p1 = 100
    training_hp_percent_p2 = 100
    training_sp_percent_p1 = 100
    training_sp_percent_p2 = 100
    training_p2_all_guard = False

    training_p2_state_lock = 0
    training_start_position = 0

    keyconfig_actions: list[tuple[str, str]] = [
        ("P1 左", "P1_LEFT"),
        ("P1 右", "P1_RIGHT"),
        ("P1 下", "P1_DOWN"),
        ("P1 ジャンプ", "P1_JUMP"),
        ("P1 弱P", "P1_LP"),
        ("P1 中P", "P1_MP"),
        ("P1 強P", "P1_HP"),
        ("P1 弱K", "P1_LK"),
        ("P1 中K", "P1_MK"),
        ("P1 強K", "P1_HK"),
        ("P2 左", "P2_LEFT"),
        ("P2 右", "P2_RIGHT"),
        ("P2 下", "P2_DOWN"),
        ("P2 ジャンプ", "P2_JUMP"),
        ("P2 攻撃", "P2_ATTACK"),
        ("クイックリセット", "QUICK_RESET"),
    ]

    cmdlist_items: list[tuple[str, int]] = [
        ("U: 弱パンチ", 400),
        ("I: 中パンチ", 200),
        ("O: 強パンチ", 210),
        ("J: 弱キック", 229),
        ("K: 中キック", 430),
        ("L: 強キック", 410),
        ("↓↘→+P: 波動拳", 6040),
        ("↓↘→↓↘→+P: 真空波動拳", int(getattr(constants, "SHINKU_HADOKEN_ACTION_ID", 8000))),
        ("←↙↓+K: 突進", 6520),
        ("メニューに戻る", -1),
    ]

    def _get_preview_sprite_key(action_id: int, *, elapsed_frames: int) -> tuple[int, int] | None:
        # 突進(6520)はゲーム中もスプライト固定描画なので、プレビューも確実に出す。
        if int(action_id) == 6520:
            startup = int(getattr(constants, "RUSH_STARTUP_FRAMES", 6))
            if int(elapsed_frames) < max(1, startup):
                return (6520, 1)
            return (6520, 2)

        a = actions_by_id.get(int(action_id))
        if not a:
            return None
        frames = a.get("frames", [])
        if not isinstance(frames, list) or not frames:
            return None

        total = 0
        for fr in frames:
            if not isinstance(fr, dict):
                continue
            t = int(fr.get("time", 0))
            if t <= 0:
                continue
            total += t
        if total <= 0:
            fr0 = frames[0] if isinstance(frames[0], dict) else None
            if not fr0:
                return None
            try:
                return (int(fr0.get("group", 0)), int(fr0.get("index", 0)))
            except (TypeError, ValueError):
                return None

        f = int(elapsed_frames) % int(total)
        acc = 0
        for fr in frames:
            if not isinstance(fr, dict):
                continue
            t = int(fr.get("time", 0))
            if t <= 0:
                continue
            acc += t
            if f < acc:
                group = fr.get("group")
                index = fr.get("index")
                sprite = fr.get("sprite")
                if group is not None and index is not None:
                    try:
                        return (int(group), int(index))
                    except (TypeError, ValueError):
                        return None
                if isinstance(sprite, (tuple, list)) and len(sprite) >= 2:
                    try:
                        return (int(sprite[0]), int(sprite[1]))
                    except (TypeError, ValueError):
                        return None
                return None
        return None

    def _start_cmdlist_close() -> None:
        nonlocal cmdlist_closing, cmdlist_close_start_ms, cmdlist_preview_start_ms
        if cmdlist_closing:
            return
        cmdlist_closing = True
        cmdlist_close_start_ms = pygame.time.get_ticks()
        cmdlist_preview_start_ms = cmdlist_close_start_ms

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

    stage_bg_img: pygame.Surface | None = None
    stage_bg_path = resource_path("assets/images/stage/01.png")
    if stage_bg_path.exists():
        try:
            stage_bg_img = pygame.image.load(str(stage_bg_path)).convert_alpha()
        except pygame.error:
            stage_bg_img = None

    stage_bg_frames: list[pygame.Surface] = []
    rain_drops = _init_rain_drops(90)

    title_bg_img: pygame.Surface | None = None
    preferred_title_bg = resource_path("assets/images/Gemini_Generated_Image_897hvv897hvv897h.png")
    if preferred_title_bg.exists():
        try:
            title_bg_img = pygame.image.load(str(preferred_title_bg)).convert_alpha()
        except pygame.error:
            title_bg_img = None

    if title_bg_img is None:
        for pattern in (
            "assets/images/RYUKO2nd/organized/stand/*.png",
            "assets/images/RYUKO2nd/organized/**/*.png",
        ):
            candidates = sorted(resource_path(".").glob(pattern))
            if not candidates:
                continue
            try:
                title_bg_img = pygame.image.load(str(candidates[0])).convert_alpha()
                break
            except pygame.error:
                title_bg_img = None
    start_se: pygame.mixer.Sound | None = None
    for rel in ("start.wav", "start.ogg", "start.mp3"):
        se_path = resource_path(Path("assets/sounds") / rel)
        if not se_path.exists():
            continue
        try:
            start_se = pygame.mixer.Sound(str(se_path))
            break
        except pygame.error:
            pass

    menu_confirm_se: pygame.mixer.Sound | None = None
    menu_confirm_path = resource_path(Path("assets/sounds/SE/決定ボタンを押す15.mp3"))
    if menu_confirm_path.exists():
        try:
            menu_confirm_se = pygame.mixer.Sound(str(menu_confirm_path))
        except pygame.error:
            menu_confirm_se = None

    menu_move_se: pygame.mixer.Sound | None = None
    menu_move_path = resource_path(Path("assets/sounds/SE/カーソル移動8.mp3"))
    if menu_move_path.exists():
        try:
            menu_move_se = pygame.mixer.Sound(str(menu_move_path))
        except pygame.error:
            menu_move_se = None

    countdown_se_3: pygame.mixer.Sound | None = None
    countdown_se_2: pygame.mixer.Sound | None = None
    countdown_se_1: pygame.mixer.Sound | None = None
    countdown_se_go: pygame.mixer.Sound | None = None
    for _var, _name in (
        ("countdown_se_3", "「3」.mp3"),
        ("countdown_se_2", "「2」.mp3"),
        ("countdown_se_1", "「1」.mp3"),
        ("countdown_se_go", "「ゴー」.mp3"),
    ):
        p = resource_path(Path("assets/sounds/SE") / _name)
        if not p.exists():
            continue
        try:
            s = pygame.mixer.Sound(str(p))
        except pygame.error:
            s = None
        if _var == "countdown_se_3":
            countdown_se_3 = s
        elif _var == "countdown_se_2":
            countdown_se_2 = s
        elif _var == "countdown_se_1":
            countdown_se_1 = s
        elif _var == "countdown_se_go":
            countdown_se_go = s

    beam_se: pygame.mixer.Sound | None = None
    beam_se_path = resource_path(Path("assets/sounds/SE/ビーム改.mp3"))
    if beam_se_path.exists():
        try:
            beam_se = pygame.mixer.Sound(str(beam_se_path))
        except pygame.error:
            beam_se = None

    hit_se: pygame.mixer.Sound | None = None
    hit_se_path = resource_path(Path("assets/sounds/SE/打撃1.mp3"))
    if hit_se_path.exists():
        try:
            hit_se = pygame.mixer.Sound(str(hit_se_path))
        except pygame.error:
            hit_se = None

    def _apply_se_volume() -> None:
        vol = max(0.0, min(1.0, float(se_volume_level) / 100.0))
        try:
            if start_se is not None:
                start_se.set_volume(0.50 * vol)
            if menu_confirm_se is not None:
                menu_confirm_se.set_volume(0.55 * vol)
            if menu_move_se is not None:
                menu_move_se.set_volume(0.45 * vol)
            if countdown_se_3 is not None:
                countdown_se_3.set_volume(0.22 * vol)
            if countdown_se_2 is not None:
                countdown_se_2.set_volume(0.22 * vol)
            if countdown_se_1 is not None:
                countdown_se_1.set_volume(0.22 * vol)
            if countdown_se_go is not None:
                countdown_se_go.set_volume(0.25 * vol)
            if beam_se is not None:
                beam_se.set_volume(0.40 * vol)
            if hit_se is not None:
                hit_se.set_volume(0.18 * vol)
        except Exception:
            pass

    title_bgm_path = resource_path(Path("assets/sounds/BGM/Revenger.mp3"))
    battle_bgm_path = resource_path(Path("assets/sounds/BGM/Who_Is_the_Champion.mp3"))

    def _apply_bgm_volume() -> None:
        try:
            pygame.mixer.music.set_volume(float(bgm_volume_level) / 100.0)
        except Exception:
            pass

    _apply_se_volume()

    def _play_bgm(path: Path) -> None:
        if not path.exists():
            return
        try:
            pygame.mixer.music.load(str(path))
            _apply_bgm_volume()
            pygame.mixer.music.play(-1)
        except Exception:
            pass

    current_bgm: str | None = None

    def _ensure_bgm_for_state(state: GameState) -> None:
        nonlocal current_bgm
        if state == GameState.TITLE:
            want = str(title_bgm_path)
            if current_bgm != want:
                _play_bgm(title_bgm_path)
                current_bgm = want
        elif state in {GameState.BATTLE, GameState.TRAINING}:
            want = str(battle_bgm_path)
            if current_bgm != want:
                _play_bgm(battle_bgm_path)
                current_bgm = want
        elif state == GameState.CHAR_SELECT:
            want = str(title_bgm_path)
            if current_bgm != want:
                _play_bgm(title_bgm_path)
                current_bgm = want
        elif state == GameState.RESULT:
            want = str(title_bgm_path)
            if current_bgm != want:
                _play_bgm(title_bgm_path)
                current_bgm = want

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

    _apply_resolution((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
    reset_match()

    _ensure_bgm_for_state(game_state)

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

                if (
                    game_state == GameState.TRAINING
                    and (not bool(menu_open))
                    and event.key == int(keybinds.get("QUICK_RESET", pygame.K_r))
                ):
                    reset_match()
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
                        projectiles.clear()
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
                                _cycle_p2_lock(-1)
                                if menu_move_se is not None:
                                    menu_move_se.play()
                            elif idx == 5:
                                _cycle_start_pos(-1)
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
                                _cycle_p2_lock(+1)
                                if menu_move_se is not None:
                                    menu_move_se.play()
                            elif idx == 5:
                                _cycle_start_pos(+1)
                                if menu_move_se is not None:
                                    menu_move_se.play()
                        elif event.key == pygame.K_RETURN or event.key == pygame.K_u:
                            idx = int(training_settings_selection)
                            if idx == 4:
                                training_p2_state_lock = (int(training_p2_state_lock) + 1) % 4
                                if menu_confirm_se is not None:
                                    menu_confirm_se.play()
                            elif idx == 5:
                                training_start_position = (int(training_start_position) + 1) % 3
                                if menu_confirm_se is not None:
                                    menu_confirm_se.play()
                            elif idx == 6:
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
                                if menu_confirm_se is not None:
                                    menu_confirm_se.play()
                            elif idx == 1:
                                debug_ui_show_p1_frames = not bool(debug_ui_show_p1_frames)
                                if menu_confirm_se is not None:
                                    menu_confirm_se.play()
                            elif idx == 2:
                                debug_ui_show_p2_frames = not bool(debug_ui_show_p2_frames)
                                if menu_confirm_se is not None:
                                    menu_confirm_se.play()
                            elif idx == 3:
                                debug_draw = not bool(debug_draw)
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

                    if game_state in {GameState.BATTLE, GameState.TRAINING} and cmdlist_open:
                        if cmdlist_closing:
                            continue
                        if event.key in {pygame.K_UP, pygame.K_w}:
                            cmdlist_selection = (cmdlist_selection - 1) % max(1, len(cmdlist_items))
                            cmdlist_preview_start_ms = pygame.time.get_ticks()
                            if menu_move_se is not None:
                                menu_move_se.play()
                        elif event.key in {pygame.K_DOWN, pygame.K_s}:
                            cmdlist_selection = (cmdlist_selection + 1) % max(1, len(cmdlist_items))
                            cmdlist_preview_start_ms = pygame.time.get_ticks()
                            if menu_move_se is not None:
                                menu_move_se.play()
                        elif event.key == pygame.K_RETURN or event.key == pygame.K_u:
                            _label, aid = cmdlist_items[cmdlist_selection]
                            if int(aid) < 0:
                                _start_cmdlist_close()
                            else:
                                cmdlist_preview_start_ms = pygame.time.get_ticks()
                            if menu_confirm_se is not None:
                                menu_confirm_se.play()
                        elif event.key in {pygame.K_ESCAPE, pygame.K_o}:
                            _start_cmdlist_close()
                            if event.key == pygame.K_o and menu_move_se is not None:
                                menu_move_se.play()
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
                            cmdlist_open = True
                            cmdlist_selection = 0
                            cmdlist_preview_start_ms = pygame.time.get_ticks()
                            cmdlist_closing = False
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
                    p2_attack_id = "P2_L_PUNCH"
                elif event.key == int(keybinds.get("P1_LP", pygame.K_u)):
                    p1_attack_id = "P1_U_LP"
                elif event.key == int(keybinds.get("P1_MP", pygame.K_i)):
                    p1_attack_id = "P1_I_MP"
                elif event.key == int(keybinds.get("P1_HP", pygame.K_o)):
                    p1_attack_id = "P1_O_HP"
                elif event.key == int(keybinds.get("P1_LK", pygame.K_j)):
                    p1_attack_id = "P1_J_LK"
                elif event.key == int(keybinds.get("P1_MK", pygame.K_k)):
                    p1_attack_id = "P1_K_MK"
                elif event.key == int(keybinds.get("P1_HK", pygame.K_l)):
                    p1_attack_id = "P1_L_HK"

        tick_ms = pygame.time.get_ticks()

        if super_freeze_frames_left > 0:
            super_freeze_frames_left -= 1

            # 描画（ステージに描いて、最後にウィンドウへ拡大）。
            stage_surface.fill(constants.COLOR_BG)

            _draw_stage_background(
                stage_surface,
                tick_ms=int(tick_ms),
                stage_bg_frames=stage_bg_frames,
                stage_bg_img=stage_bg_img,
            )

            _draw_rain(stage_surface, drops=rain_drops)

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
                color = (80, 255, 220) if selected else (210, 210, 210)
                local_shake = int(3 * math.sin((tick / 120.0) + i)) if selected else 0

                if item == "P2":
                    mode = "CPU" if bool(char_select_p2_cpu) else "PLAYER"
                    label = f"P2: {mode}  (←→ 切替)"
                elif item == "START":
                    label = "START"
                else:
                    label = "BACK"

                text_surf = menu_font.render(label, True, color)
                if selected:
                    tw = max(1, int(round(text_surf.get_width() * 1.15)))
                    th = max(1, int(round(text_surf.get_height() * 1.15)))
                    text_surf = pygame.transform.smoothscale(text_surf, (tw, th))

                text_rect = text_surf.get_rect(topleft=(right_x + local_shake, base_y + i * 54))
                screen.blit(text_surf, text_rect)

            hint = font.render("ESC: 戻る / Enter: 決定", True, (235, 235, 235))
            screen.blit(hint, hint.get_rect(midbottom=(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT - 22)))

            pygame.display.flip()
            clock.tick(constants.FPS)
            continue

        if menu_open:
            stage_surface.fill(constants.COLOR_BG)

            _draw_stage_background(
                stage_surface,
                tick_ms=int(tick_ms),
                stage_bg_frames=stage_bg_frames,
                stage_bg_img=stage_bg_img,
            )

            _draw_rain(stage_surface, drops=rain_drops)

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
                    ("P2状態固定", lock_label),
                    ("開始位置", pos_label),
                    ("P2全ガード", "ON" if bool(training_p2_all_guard) else "OFF"),
                    ("戻る", ""),
                ]
                y = panel_y + 110
                for i, (label, value) in enumerate(rows):
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
                    y += 44

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

                left_rows = [r for r in rows if r[1].startswith("P1_")]
                right_rows = [r for r in rows if r[1].startswith("P2_")]

                def _draw_rows(rows_in: list[tuple[str, str, int]], *, x: int) -> None:
                    y = int(inner_y)
                    line_h = 44
                    for label, act, idx in rows_in:
                        selected = (idx == int(keyconfig_selection)) and (keyconfig_waiting_action is None)
                        if selected:
                            pygame.draw.rect(screen, (90, 255, 220, 28), pygame.Rect(x, y - 6, col_w, line_h), 0)
                            pygame.draw.rect(screen, (90, 255, 220), pygame.Rect(x, y - 6, col_w, line_h), 1)

                        key_code = int(keybinds.get(str(act), default_keybinds.get(str(act), 0)))
                        key_text = _key_name(key_code)

                        name_c = (245, 245, 245) if selected else (220, 220, 220)
                        key_c = (255, 240, 120) if selected else (200, 200, 200)

                        left = keycfg_font.render(str(label), True, name_c)
                        right = keycfg_font.render(str(key_text), True, key_c)
                        screen.blit(left, (x + 8, y))
                        screen.blit(right, right.get_rect(midright=(x + col_w - 10, y + (left.get_height() // 2) + 2)))

                        y += line_h

                _draw_rows(left_rows, x=left_x)
                _draw_rows(right_rows, x=right_x)

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

            if game_state in {GameState.BATTLE, GameState.TRAINING} and cmdlist_open:
                overlay2 = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay2.fill((0, 0, 0, 210))
                screen.blit(overlay2, (0, 0))

                w = int(constants.SCREEN_WIDTH)
                h = int(constants.SCREEN_HEIGHT)

                panel_w = int(min(920, w - 80))
                panel_h = int(min(600, h - 140))
                panel_x = (w - panel_w) // 2
                panel_y = (h - panel_h) // 2

                panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
                panel.fill((18, 18, 22, 235))
                screen.blit(panel, (panel_x, panel_y))
                pygame.draw.rect(screen, (90, 255, 220), pygame.Rect(panel_x, panel_y, panel_w, panel_h), 2)

                header_txt = "COMMAND LIST"
                header = title_font.render(header_txt, True, (245, 245, 245))
                header_scale_w = max(1, int(round(header.get_width() * 0.38)))
                header_scale_h = max(1, int(round(header.get_height() * 0.38)))
                header = pygame.transform.smoothscale(header, (header_scale_w, header_scale_h))
                screen.blit(header, (panel_x + 26, panel_y + 18))

                sub = keycfg_font.render("↑↓: 選択 / Enter: プレビュー / ESC or O: 戻る", True, (220, 220, 220))
                screen.blit(sub, (panel_x + 28, panel_y + 58))

                inner_x = panel_x + 26
                inner_y = panel_y + 98
                inner_w = panel_w - 52
                inner_h = panel_h - 128

                list_w = int(inner_w * 0.58)
                prev_w = int(inner_w - list_w - 26)
                prev_h = int(min(300, inner_h - 10))

                list_x = inner_x
                list_y0 = inner_y

                preview_x = inner_x + list_w + 26
                preview_y = inner_y + 18
                preview_w = max(220, int(prev_w))
                preview_h = max(200, int(prev_h))

                pygame.draw.rect(screen, (25, 25, 35), pygame.Rect(list_x, list_y0 - 8, list_w, inner_h), 0)
                pygame.draw.rect(screen, (80, 80, 110), pygame.Rect(list_x, list_y0 - 8, list_w, inner_h), 1)
                pygame.draw.rect(screen, (20, 20, 20), pygame.Rect(preview_x, preview_y, preview_w, preview_h), 0)
                pygame.draw.rect(screen, (80, 80, 80), pygame.Rect(preview_x, preview_y, preview_w, preview_h), 2)

                list_y = int(list_y0)
                row_h = 42
                for i, (label, _aid) in enumerate(cmdlist_items):
                    selected = (i == int(cmdlist_selection))
                    if selected:
                        pygame.draw.rect(screen, (90, 255, 220, 28), pygame.Rect(list_x + 10, list_y - 6, list_w - 20, row_h), 0)
                        pygame.draw.rect(screen, (90, 255, 220), pygame.Rect(list_x + 10, list_y - 6, list_w - 20, row_h), 1)
                    c = (255, 240, 120) if selected else (230, 230, 230)
                    s = keycfg_font.render(label, True, c)
                    screen.blit(s, (list_x + 18, list_y))
                    list_y += row_h

                if cmdlist_items:
                    _label, aid = cmdlist_items[cmdlist_selection]
                    if int(aid) < 0:
                        aid = 0
                    elapsed = pygame.time.get_ticks() - int(cmdlist_preview_start_ms)
                    elapsed_frames = int(elapsed // max(1, int(1000 / constants.FPS)))

                    if cmdlist_closing:
                        close_elapsed = pygame.time.get_ticks() - int(cmdlist_close_start_ms)
                        close_frames = int(close_elapsed // max(1, int(1000 / constants.FPS)))
                        pause = 20
                        idx = min(7, int(close_frames))
                        if close_frames >= 8:
                            idx = 7
                        img = getattr(p1, "_sprites", {}).get((181, idx))
                        if img is not None:
                            show = img
                            max_w = preview_w - 24
                            max_h = preview_h - 24
                            scale = min(1.0, float(max_w) / float(show.get_width()), float(max_h) / float(show.get_height()))
                            if scale < 1.0:
                                w = max(1, int(round(show.get_width() * scale)))
                                h = max(1, int(round(show.get_height() * scale)))
                                show = pygame.transform.smoothscale(show, (w, h))
                            cx = preview_x + (preview_w // 2)
                            cy = preview_y + (preview_h // 2) + 30
                            screen.blit(show, (cx - (show.get_width() // 2), cy - (show.get_height() // 2)))

                        if close_frames >= (8 + pause):
                            cmdlist_open = False
                            cmdlist_closing = False
                    else:
                        key = _get_preview_sprite_key(int(aid), elapsed_frames=elapsed_frames)
                        if key is not None:
                            img = getattr(p1, "_sprites", {}).get(key)
                            if img is not None:
                                show = img
                                if int(getattr(p1, "facing", 1)) < 0:
                                    show = pygame.transform.flip(img, True, False)
                                max_w = preview_w - 24
                                max_h = preview_h - 24
                                scale = min(1.0, float(max_w) / float(show.get_width()), float(max_h) / float(show.get_height()))
                                if scale < 1.0:
                                    w = max(1, int(round(show.get_width() * scale)))
                                    h = max(1, int(round(show.get_height() * scale)))
                                    show = pygame.transform.smoothscale(show, (w, h))
                                cx = preview_x + (preview_w // 2)
                                cy = preview_y + (preview_h // 2) + 30
                                screen.blit(show, (cx - (show.get_width() // 2), cy - (show.get_height() // 2)))

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

        # 物理更新（KO中/カウント中でもアニメは進める）。
        p1.update()
        p2.update()

        # Rush wind/dust effect spawn (ポーリングで確実に発生させる)。
        if rush_dust_frames:
            pos = p1.consume_rush_effect_spawn()
            if pos is not None:
                effects.append(Effect(frames=rush_dust_frames, pos=pos, frames_per_image=2))
            pos = p2.consume_rush_effect_spawn()
            if pos is not None:
                effects.append(Effect(frames=rush_dust_frames, pos=pos, frames_per_image=2))

        if p1.consume_hadoken_spawn():
            _spawn_hadoken(p1)
        if p2.consume_hadoken_spawn():
            _spawn_hadoken(p2)

        if p1.consume_shinku_spawn():
            _spawn_shinku(p1)
        if p2.consume_shinku_spawn():
            _spawn_shinku(p2)

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
            _update_rain_drops(rain_drops)

        stage_bounds = pygame.Rect(0, 0, constants.STAGE_WIDTH, constants.STAGE_HEIGHT)
        for pr in projectiles:
            pr.update(bounds=stage_bounds)
        projectiles = [pr for pr in projectiles if not pr.finished]

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
                hit_pause = int(getattr(constants, "HITSTUN_DEFAULT_FRAMES", 20))
            else:
                damage = int(spec["damage"])
                knockback_px = int(spec["knockback_px"])
                hitstop_frames = int(spec["hitstop_frames"])
                attacker_recoil_px = int(spec.get("attacker_recoil_px", getattr(constants, "ATTACKER_RECOIL_PX_DEFAULT", 3)))
                hit_pause = int(spec.get("hit_pause", getattr(constants, "HITSTUN_DEFAULT_FRAMES", 20)))

            # ガード判定：後ろ入力中（defender.holding_back）ならガード成功。
            # まずは「後ろに下がっている間に攻撃を受けると、ダメージを受けずにガードモーション」を成立させる。
            # ガード受付は「衝突したそのフレーム」で判定する（アニメ遷移待ちなし）。
            # - 入力は Player 側でバッファされているため、のけぞり終了直前やヒットストップ中でも間に合う。
            # - blockstun 中は True blockstring として自動ガード継続する。
            is_guarding = bool(getattr(defender, "can_guard_now", lambda: False)()) and bool(
                getattr(defender, "is_guarding_intent", lambda: False)()
            )
            if game_state == GameState.TRAINING and training_p2_all_guard and (defender is p2):
                is_guarding = True

            if is_guarding:
                chip_ratio = float(getattr(constants, "GUARD_CHIP_DAMAGE_RATIO", 0.0))
                chip_damage = int(max(0, round(damage * chip_ratio)))

                defender.take_damage(chip_damage)

                gain_guard = int(getattr(constants, "POWER_GAIN_ON_GUARD", 20))
                attacker.add_power(gain_guard)

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

            attacker_side = 1 if attacker is p1 else 2
            if int(getattr(defender, "hitstun_timer", 0)) > 0:
                attacker.extend_combo_on_opponent()
            else:
                attacker.start_combo_on_opponent(opponent_side=(2 if attacker_side == 1 else 1))

            dmg_mul = float(getattr(constants, "get_damage_multiplier", lambda _c: 1.0)(attacker.get_combo_count()))
            scaled_damage = int(max(0, round(float(damage) * dmg_mul)))

            defender.take_damage(scaled_damage)
            if hit_se is not None:
                hit_se.play()
            gain_hit = int(getattr(constants, "POWER_GAIN_ON_HIT", 50))
            attacker.add_power(gain_hit)
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

            defender.set_combo_victim_state(attacker_side=attacker_side, hitstun_frames=hit_pause)
            defender.enter_hitstun(frames=hit_pause)

            # セパレーション：攻撃側も少し後ろへ下がる。
            attacker.apply_knockback(dir_x=-attacker.facing, amount_px=attacker_recoil_px)
            attacker.mark_damage_dealt()

            attacker.add_combo_damage(scaled_damage)

            # 衝突点に火花エフェクトを生成（画像がある場合）。
            if spark_frames:
                effects.append(Effect(frames=spark_frames, pos=hit_point, frames_per_image=2))

            extra_hitstop = int(getattr(constants, "HIT_EFFECT_EXTRA_HITSTOP_FRAMES", 4))
            hitstop_total = int(hitstop_frames) + max(0, extra_hitstop)

            attacker.hitstop_frames_left = max(attacker.hitstop_frames_left, hitstop_total)
            defender.hitstop_frames_left = max(defender.hitstop_frames_left, hitstop_total)

        _apply_hit(p1, p2)
        _apply_hit(p2, p1)

        for pr in projectiles:
            if pr.finished:
                continue

            if int(getattr(pr, "owner_side", 0)) == 1:
                target = p2
                attacker = p1
            elif int(getattr(pr, "owner_side", 0)) == 2:
                target = p1
                attacker = p2
            else:
                continue

            if pr.get_rect().colliderect(target.get_hurtbox()):
                is_guarding = bool(getattr(target, "can_guard_now", lambda: False)()) and bool(
                    getattr(target, "is_guarding_intent", lambda: False)()
                )
                if game_state == GameState.TRAINING and training_p2_all_guard and (target is p2):
                    is_guarding = True

                if is_guarding:
                    damage = int(getattr(pr, "damage", 0))

                    chip_ratio = float(getattr(constants, "GUARD_CHIP_DAMAGE_RATIO", 0.0))
                    chip_damage = int(max(0, round(damage * chip_ratio)))
                    target.take_damage(chip_damage)

                    gain_guard = int(getattr(constants, "POWER_GAIN_ON_GUARD", 20))
                    attacker.add_power(gain_guard)

                    base_guard_kb = int(getattr(constants, "GUARD_KNOCKBACK_PX_DEFAULT", 10))
                    guard_mul = float(getattr(constants, "GUARD_KNOCKBACK_MULTIPLIER", 1.35))
                    guard_knockback = int(max(0, round(base_guard_kb * guard_mul)))

                    # Guard knockback: push defender away from projectile direction
                    dir_x = 1 if float(getattr(pr, "vel", pygame.Vector2(1, 0)).x) > 0 else -1
                    target.apply_knockback(dir_x=dir_x, amount_px=guard_knockback)
                    crouch_guard = bool(getattr(target, "crouching", False))
                    target.enter_blockstun(crouching=crouch_guard)

                    extra_hitstop = int(getattr(constants, "HIT_EFFECT_EXTRA_HITSTOP_FRAMES", 4))
                    hitstop_total = int(getattr(constants, "HITSTOP_DEFAULT_FRAMES", 6)) + max(0, extra_hitstop)
                    attacker.hitstop_frames_left = max(attacker.hitstop_frames_left, hitstop_total)
                    target.hitstop_frames_left = max(target.hitstop_frames_left, hitstop_total)

                    if isinstance(pr, SuperProjectile):
                        if pr.can_hit_now():
                            pr.register_hit()
                    else:
                        pr._finished = True
                    continue

                if isinstance(pr, SuperProjectile):
                    if pr.can_hit_now():
                        pr.register_hit()

                        attacker_side = 1 if attacker is p1 else 2
                        if int(getattr(target, "hitstun_timer", 0)) > 0:
                            attacker.extend_combo_on_opponent()
                        else:
                            attacker.start_combo_on_opponent(opponent_side=(2 if attacker_side == 1 else 1))

                        target.take_damage(pr.damage)
                        if hit_se is not None:
                            hit_se.play()
                        attacker.add_combo_damage(int(getattr(pr, "damage", 0)))
                        target.set_combo_victim_state(attacker_side=attacker_side, hitstun_frames=pr.hitstun_frames)
                        target.enter_hitstun(frames=pr.hitstun_frames)
                        target.apply_knockback(dir_x=(1 if pr.vel.x > 0 else -1), amount_px=int(pr.push_on_hit_px))
                        if int(getattr(pr, "owner_side", 0)) == 1:
                            p1.add_power(30)
                        elif int(getattr(pr, "owner_side", 0)) == 2:
                            p2.add_power(30)
                else:
                    pr._finished = True

                    attacker_side = 1 if attacker is p1 else 2
                    if int(getattr(target, "hitstun_timer", 0)) > 0:
                        attacker.extend_combo_on_opponent()
                    else:
                        attacker.start_combo_on_opponent(opponent_side=(2 if attacker_side == 1 else 1))

                    target.take_damage(pr.damage)
                    if hit_se is not None:
                        hit_se.play()
                    attacker.add_combo_damage(int(getattr(pr, "damage", 0)))
                    target.set_combo_victim_state(attacker_side=attacker_side, hitstun_frames=pr.hitstun_frames)
                    target.enter_hitstun(frames=pr.hitstun_frames)

        # 描画（ステージに描いて、最後にウィンドウへ拡大）。
        stage_surface.fill(constants.COLOR_BG)

        _draw_stage_background(
            stage_surface,
            tick_ms=int(tick_ms),
            stage_bg_frames=stage_bg_frames,
            stage_bg_img=stage_bg_img,
        )

        _draw_rain(stage_surface, drops=rain_drops)

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

        for pr in projectiles:
            pr.draw(stage_surface)

        if game_state == GameState.TRAINING:
            hud_top = 120
            line_h = int(debug_font.get_linesize())
            if bool(debug_ui_show_key_history) and p1_key_history:
                # 左端は入力（コマンド）表示欄として確保する。
                x = 12
                y = hud_top
                for i, t in enumerate(p1_key_history):
                    surf = debug_font.render(t, True, (240, 240, 240))
                    stage_surface.blit(surf, (x, y + i * line_h))

            if bool(debug_ui_show_p1_frames):
                p1_info = p1.get_last_move_frame_info()
                if p1_info is not None:
                    lines = [
                        f"P1 {p1_info.attack_id}",
                        f"アクション: {p1.get_current_action_id()}  フレーム: {p1.get_action_frame_counter()}f",
                        f"コンボ: {p1.get_combo_count()}",
                        f"全体: {p1_info.total_frames}f",
                        f"発生: {p1_info.startup_frames}f",
                        f"持続: {p1_info.active_frames}f",
                        f"硬直: {p1_info.recovery_frames}f",
                    ]
                    # フレーム表示などのデバッグ文字は右へ寄せ、左端は入力欄にする。
                    x = 96
                    y = hud_top
                    for i, t in enumerate(lines):
                        surf = debug_font.render(t, True, (240, 240, 240))
                        stage_surface.blit(surf, (x, y + i * line_h))

            if bool(debug_ui_show_p2_frames):
                p2_info = p2.get_last_move_frame_info()
                if p2_info is not None:
                    lines = [
                        f"P2 {p2_info.attack_id}",
                        f"アクション: {p2.get_current_action_id()}  フレーム: {p2.get_action_frame_counter()}f",
                        f"コンボ: {p2.get_combo_count()}",
                        f"全体: {p2_info.total_frames}f",
                        f"発生: {p2_info.startup_frames}f",
                        f"持続: {p2_info.active_frames}f",
                        f"硬直: {p2_info.recovery_frames}f",
                    ]
                    x = constants.STAGE_WIDTH - 12
                    y = hud_top
                    for i, t in enumerate(lines):
                        surf = debug_font.render(t, True, (240, 240, 240))
                        rect = surf.get_rect(topright=(x, y + i * line_h))
                        stage_surface.blit(surf, rect)

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

        hud.draw_hp_bar(
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
        hud.draw_hp_bar(
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

        if game_state in {GameState.BATTLE, GameState.TRAINING}:
            cy = int(constants.HP_BAR_MARGIN_Y + (constants.HP_BAR_HEIGHT // 2))
            left_x = int(constants.HP_BAR_MARGIN_X + constants.HP_BAR_WIDTH + 18)
            right_x = int(constants.STAGE_WIDTH - constants.HP_BAR_MARGIN_X - constants.HP_BAR_WIDTH - 18)
            hud.draw_round_markers(
                stage_surface,
                x=left_x,
                y=cy,
                wins=p1_round_wins,
                max_wins=2,
                align_right=False,
                tick_ms=int(tick_ms),
            )
            hud.draw_round_markers(
                stage_surface,
                x=right_x,
                y=cy,
                wins=p2_round_wins,
                max_wins=2,
                align_right=True,
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

            timer_surf = title_font.render(timer_text, True, (245, 245, 245))
            timer_rect = timer_surf.get_rect(midtop=(constants.STAGE_WIDTH // 2, int(constants.HP_BAR_MARGIN_Y)))
            stage_surface.blit(timer_surf, timer_rect)

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

            cd_surf = title_font.render(str(show), True, (255, 240, 120))
            w = max(1, int(round(cd_surf.get_width() * 2.2)))
            h = max(1, int(round(cd_surf.get_height() * 2.2)))
            cd_surf = pygame.transform.smoothscale(cd_surf, (w, h))
            cd_rect = cd_surf.get_rect(center=(constants.STAGE_WIDTH // 2, constants.STAGE_HEIGHT // 2 - 40))
            stage_surface.blit(cd_surf, cd_rect)
        elif game_state == GameState.BATTLE and int(round_over_frames_left) <= 0 and int(battle_countdown_frames_left) == 0:
            if battle_countdown_last_announce is not None:
                battle_countdown_last_announce = None
                if countdown_se_go is not None:
                    countdown_se_go.play()

        if int(round_over_frames_left) > 0:
            round_over_frames_left = max(0, int(round_over_frames_left) - 1)
            ko_surf = title_font.render("KO", True, (255, 240, 120))
            w = max(1, int(round(ko_surf.get_width() * 1.8)))
            h = max(1, int(round(ko_surf.get_height() * 1.8)))
            ko_surf = pygame.transform.smoothscale(ko_surf, (w, h))
            rect = ko_surf.get_rect(center=(constants.STAGE_WIDTH // 2, constants.STAGE_HEIGHT // 2 - 30))
            stage_surface.blit(ko_surf, rect)

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
        gauge_h = 10
        gauge_gap = 6
        gauge_y = int(constants.HP_BAR_MARGIN_Y + constants.HP_BAR_HEIGHT + gauge_gap)
        mx = float(getattr(constants, "POWER_GAUGE_MAX", 1000))
        _draw_power_gauge(
            stage_surface,
            x=constants.HP_BAR_MARGIN_X,
            y=gauge_y,
            w=constants.HP_BAR_WIDTH,
            h=gauge_h,
            value=float(getattr(p1, "power_gauge", 0)),
            max_value=mx,
            align_right=False,
        )
        _draw_power_gauge(
            stage_surface,
            x=constants.STAGE_WIDTH - constants.HP_BAR_MARGIN_X - constants.HP_BAR_WIDTH,
            y=gauge_y,
            w=constants.HP_BAR_WIDTH,
            h=gauge_h,
            value=float(getattr(p2, "power_gauge", 0)),
            max_value=mx,
            align_right=True,
        )

        if int(getattr(p1, "combo_display_frames_left", 0)) > 0 and int(getattr(p1, "combo_display_count", 0)) >= 2:
            txt = f"{int(p1.combo_display_count)} Hits"
            surf = title_font.render(txt, True, (255, 240, 120))
            stage_surface.blit(surf, (16, 110))

            dmg = int(getattr(p1, "combo_damage_display", 0))
            dmg_surf = prompt_font.render(f"{dmg}", True, (255, 240, 200))
            stage_surface.blit(dmg_surf, (16, 110 + surf.get_height() - 6))

        if int(getattr(p2, "combo_display_frames_left", 0)) > 0 and int(getattr(p2, "combo_display_count", 0)) >= 2:
            txt = f"{int(p2.combo_display_count)} Hits"
            surf = title_font.render(txt, True, (255, 240, 120))
            rect = surf.get_rect(topright=(constants.STAGE_WIDTH - 16, 110))
            stage_surface.blit(surf, rect)

            dmg = int(getattr(p2, "combo_damage_display", 0))
            dmg_surf = prompt_font.render(f"{dmg}", True, (255, 240, 200))
            dmg_rect = dmg_surf.get_rect(topright=(constants.STAGE_WIDTH - 16, 110 + surf.get_height() - 6))
            stage_surface.blit(dmg_surf, dmg_rect)

        scaled = pygame.transform.smoothscale(stage_surface, (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
        screen.blit(scaled, (0, 0))

        pygame.display.flip()

        # FPS を固定し、1フレームあたりの挙動が安定するようにする。
        clock.tick(constants.FPS)

    # 終了処理。
    pygame.quit()


if __name__ == "__main__":
    main()
