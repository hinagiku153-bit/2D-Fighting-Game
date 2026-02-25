from __future__ import annotations

from typing import Any, TYPE_CHECKING

import pygame

from src.engine.context import FrameState, FrameSample, FrameDataTracker
from src.ui import hud
from src.utils import constants

if TYPE_CHECKING:
    from src.entities.player import Player


class HUDRenderer:
    """HPバー、パワーゲージ、コンボ表示、フレームメーター等のHUD描画を担当する。"""

    def __init__(
        self,
        *,
        title_font: pygame.font.Font,
        prompt_font: pygame.font.Font,
        debug_font: pygame.font.Font,
        frame_meter_adv_font: pygame.font.Font,
    ) -> None:
        self.title_font = title_font
        self.prompt_font = prompt_font
        self.debug_font = debug_font
        self.frame_meter_adv_font = frame_meter_adv_font

        # frame meter panel cache
        self._frame_meter_panel: pygame.Surface | None = None

    # ------------------------------------------------------------------
    # HP bars
    # ------------------------------------------------------------------

    @staticmethod
    def draw_hp_bars(
        surface: pygame.Surface,
        *,
        p1_hp: float,
        p1_chip_hp: float,
        p1_max_hp: float,
        p2_hp: float,
        p2_chip_hp: float,
        p2_max_hp: float,
    ) -> None:
        hud.draw_hp_bar(
            surface,
            x=constants.HP_BAR_MARGIN_X,
            y=constants.HP_BAR_MARGIN_Y,
            w=constants.HP_BAR_WIDTH,
            h=constants.HP_BAR_HEIGHT,
            hp=p1_hp,
            chip_hp=p1_chip_hp,
            max_hp=p1_max_hp,
            align_right=False,
        )
        hud.draw_hp_bar(
            surface,
            x=constants.STAGE_WIDTH - constants.HP_BAR_MARGIN_X - constants.HP_BAR_WIDTH,
            y=constants.HP_BAR_MARGIN_Y,
            w=constants.HP_BAR_WIDTH,
            h=constants.HP_BAR_HEIGHT,
            hp=p2_hp,
            chip_hp=p2_chip_hp,
            max_hp=p2_max_hp,
            align_right=True,
        )

    # ------------------------------------------------------------------
    # Round markers
    # ------------------------------------------------------------------

    @staticmethod
    def draw_round_markers(
        surface: pygame.Surface,
        *,
        p1_wins: int,
        p2_wins: int,
        tick_ms: int,
    ) -> None:
        cy = int(constants.HP_BAR_MARGIN_Y + (constants.HP_BAR_HEIGHT // 2))
        left_x = int(constants.HP_BAR_MARGIN_X + constants.HP_BAR_WIDTH + 18)
        right_x = int(constants.STAGE_WIDTH - constants.HP_BAR_MARGIN_X - constants.HP_BAR_WIDTH - 18)
        hud.draw_round_markers(
            surface,
            x=left_x,
            y=cy,
            wins=p1_wins,
            max_wins=2,
            align_right=False,
            tick_ms=int(tick_ms),
        )
        hud.draw_round_markers(
            surface,
            x=right_x,
            y=cy,
            wins=p2_wins,
            max_wins=2,
            align_right=True,
            tick_ms=int(tick_ms),
        )

    # ------------------------------------------------------------------
    # Round timer
    # ------------------------------------------------------------------

    def draw_timer(
        self,
        surface: pygame.Surface,
        *,
        timer_text: str,
    ) -> None:
        timer_surf = self.title_font.render(timer_text, True, (245, 245, 245))
        timer_rect = timer_surf.get_rect(midtop=(constants.STAGE_WIDTH // 2, int(constants.HP_BAR_MARGIN_Y)))
        surface.blit(timer_surf, timer_rect)

    # ------------------------------------------------------------------
    # Countdown
    # ------------------------------------------------------------------

    def draw_countdown(
        self,
        surface: pygame.Surface,
        *,
        number: int,
    ) -> None:
        cd_surf = self.title_font.render(str(number), True, (255, 240, 120))
        w = max(1, int(round(cd_surf.get_width() * 2.2)))
        h = max(1, int(round(cd_surf.get_height() * 2.2)))
        cd_surf = pygame.transform.smoothscale(cd_surf, (w, h))
        cd_rect = cd_surf.get_rect(center=(constants.STAGE_WIDTH // 2, constants.STAGE_HEIGHT // 2 - 40))
        surface.blit(cd_surf, cd_rect)

    # ------------------------------------------------------------------
    # KO text
    # ------------------------------------------------------------------

    def draw_ko(self, surface: pygame.Surface) -> None:
        ko_surf = self.title_font.render("KO", True, (255, 240, 120))
        w = max(1, int(round(ko_surf.get_width() * 1.8)))
        h = max(1, int(round(ko_surf.get_height() * 1.8)))
        ko_surf = pygame.transform.smoothscale(ko_surf, (w, h))
        rect = ko_surf.get_rect(center=(constants.STAGE_WIDTH // 2, constants.STAGE_HEIGHT // 2 - 30))
        surface.blit(ko_surf, rect)

    # ------------------------------------------------------------------
    # Power gauge
    # ------------------------------------------------------------------

    @staticmethod
    def draw_power_gauges(
        surface: pygame.Surface,
        *,
        p1_power: float,
        p2_power: float,
        max_power: float,
    ) -> None:
        gauge_h = 10
        gauge_gap = 6
        gauge_y = int(constants.HP_BAR_MARGIN_Y + constants.HP_BAR_HEIGHT + gauge_gap)
        hud.draw_power_gauge(
            surface,
            x=constants.HP_BAR_MARGIN_X,
            y=gauge_y,
            w=constants.HP_BAR_WIDTH,
            h=gauge_h,
            value=p1_power,
            max_value=max_power,
            align_right=False,
        )
        hud.draw_power_gauge(
            surface,
            x=constants.STAGE_WIDTH - constants.HP_BAR_MARGIN_X - constants.HP_BAR_WIDTH,
            y=gauge_y,
            w=constants.HP_BAR_WIDTH,
            h=gauge_h,
            value=p2_power,
            max_value=max_power,
            align_right=True,
        )

    # ------------------------------------------------------------------
    # Combo display
    # ------------------------------------------------------------------

    def draw_combo(
        self,
        surface: pygame.Surface,
        *,
        p1: Player,
        p2: Player,
    ) -> None:
        if int(getattr(p1, "combo_display_frames_left", 0)) > 0 and int(getattr(p1, "combo_display_count", 0)) >= 2:
            txt = f"{int(p1.combo_display_count)} Hits"
            surf = self.title_font.render(txt, True, (255, 240, 120))
            surface.blit(surf, (16, 110))

            dmg = int(getattr(p1, "combo_damage_display", 0))
            dmg_surf = self.prompt_font.render(f"{dmg}", True, (255, 240, 200))
            surface.blit(dmg_surf, (16, 110 + surf.get_height() - 6))

        if int(getattr(p2, "combo_display_frames_left", 0)) > 0 and int(getattr(p2, "combo_display_count", 0)) >= 2:
            txt = f"{int(p2.combo_display_count)} Hits"
            surf = self.title_font.render(txt, True, (255, 240, 120))
            rect = surf.get_rect(topright=(constants.STAGE_WIDTH - 16, 110))
            surface.blit(surf, rect)

            dmg = int(getattr(p2, "combo_damage_display", 0))
            dmg_surf = self.prompt_font.render(f"{dmg}", True, (255, 240, 200))
            dmg_rect = dmg_surf.get_rect(topright=(constants.STAGE_WIDTH - 16, 110 + surf.get_height() - 6))
            surface.blit(dmg_surf, dmg_rect)

    # ------------------------------------------------------------------
    # Frame meter (drawing only — state updates stay in main.py)
    # ------------------------------------------------------------------

    def draw_frame_meter(
        self,
        surface: pygame.Surface,
        *,
        tracker_p1: FrameDataTracker,
        tracker_p2: FrameDataTracker,
        adv_value: int | None,
        adv_frames_left: int,
        adv_attacker_side: int,
        combo_overlap_p1: bool,
        combo_overlap_p2: bool,
    ) -> None:
        block_w = 6
        history = 120
        bar_w = int(history * block_w)
        bar_h = 10
        gap = 6
        panel_pad = 10
        panel_w = int(bar_w + 90)
        panel_h = int((bar_h * 2) + gap + (panel_pad * 2))
        panel_x = int((constants.STAGE_WIDTH - panel_w) // 2)
        panel_y = int(constants.STAGE_HEIGHT - panel_h - 8)

        if self._frame_meter_panel is None:
            self._frame_meter_panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            self._frame_meter_panel.fill((0, 0, 0, 150))

        surface.blit(self._frame_meter_panel, (panel_x, panel_y))
        pygame.draw.rect(surface, (110, 110, 110), pygame.Rect(panel_x, panel_y, panel_w, panel_h), 2)

        colors = {
            FrameState.IDLE: (110, 110, 110),
            FrameState.STARTUP: (60, 220, 120),
            FrameState.ACTIVE: (240, 70, 70),
            FrameState.RECOVERY: (90, 140, 255),
            FrameState.STUN: (240, 210, 70),
            FrameState.SPECIAL: (170, 90, 255),
        }

        def _brighten(rgb: tuple[int, int, int], *, amount: int) -> tuple[int, int, int]:
            r, g, b = rgb
            return (min(255, int(r) + int(amount)), min(255, int(g) + int(amount)), min(255, int(b) + int(amount)))

        def _draw_bar(items: list[FrameSample], *, row_y: int) -> None:
            seg = items[-history:] if len(items) > history else items
            start_x = panel_x + panel_pad + (bar_w - (len(seg) * block_w))
            x = int(start_x)
            for smp in seg:
                st = smp.state
                base = colors.get(st, (110, 110, 110))
                col = _brighten(base, amount=35) if bool(smp.hitstop) else base
                r = pygame.Rect(x, row_y, block_w - 1, bar_h)
                pygame.draw.rect(surface, col, r)
                if bool(smp.hitstop):
                    pygame.draw.rect(surface, (245, 245, 245), r, 1)
                if bool(smp.combo):
                    pygame.draw.rect(surface, (255, 120, 255), r, 2)
                x += int(block_w)

        row1_y = int(panel_y + panel_pad)
        row2_y = int(panel_y + panel_pad + bar_h + gap)
        _draw_bar(tracker_p1.items(), row_y=row1_y)
        _draw_bar(tracker_p2.items(), row_y=row2_y)

        bar_left = int(panel_x + panel_pad)
        bar_right = int(bar_left + bar_w)
        grid_top = int(row1_y)
        grid_bottom = int(row2_y + bar_h)
        for i in range(0, history + 1):
            if i % 5 != 0:
                continue
            gx = int(bar_right - (i * block_w))
            if gx < bar_left or gx > bar_right:
                continue
            if i % 10 == 0:
                gc = (140, 140, 140)
                gw = 2
            else:
                gc = (120, 120, 120)
                gw = 1
            pygame.draw.line(surface, gc, (gx, grid_top), (gx, grid_bottom), gw)

        pygame.draw.line(surface, (235, 235, 235), (bar_right, grid_top - 2), (bar_right, grid_bottom + 2), 2)

        combo_now = bool(combo_overlap_p1 or combo_overlap_p2)
        if combo_now:
            combo_surf = self.debug_font.render("Combo!", True, (255, 170, 255))
            combo_x = int(bar_right - combo_surf.get_width() - 6)
            combo_y = int(panel_y - combo_surf.get_height() - 2)
            surface.blit(combo_surf, (combo_x, combo_y))

        tag1 = self.debug_font.render("P1", True, (240, 240, 240))
        tag2 = self.debug_font.render("P2", True, (240, 240, 240))
        surface.blit(tag1, (panel_x + 6, row1_y - 2))
        surface.blit(tag2, (panel_x + 6, row2_y - 2))

        if adv_value is not None and adv_attacker_side in {1, 2}:
            adv = int(adv_value)
            sign = "+" if adv >= 0 else ""
            txt = f"{sign}{adv}"
            ratio = 0.0
            if int(constants.FPS) > 0:
                ratio = float(adv_frames_left) / float(constants.FPS * 3)
            a = int(max(0, min(255, round(255 * ratio))))
            if adv >= 0:
                c = (90, 255, 220)
            else:
                c = (255, 90, 90)
            adv_surf = self.frame_meter_adv_font.render(txt, True, c)
            adv_surf.set_alpha(a)
            adv_x = int((panel_x + panel_pad + bar_w) - (adv_surf.get_width() // 2))
            adv_y = int(panel_y - adv_surf.get_height() - 6)
            surface.blit(adv_surf, (adv_x, adv_y))

    # ------------------------------------------------------------------
    # Grid display for hitbox visualization
    # ------------------------------------------------------------------

    def draw_grid(self, surface: pygame.Surface) -> None:
        """グリッド表示（ヒットボックス設定用）"""
        grid_color = (80, 80, 80)
        grid_spacing = 50  # 50pxごとにグリッド線
        
        # 縦線
        for x in range(0, constants.STAGE_WIDTH, grid_spacing):
            pygame.draw.line(surface, grid_color, (x, 0), (x, constants.STAGE_HEIGHT), 1)
        
        # 横線
        for y in range(0, constants.STAGE_HEIGHT, grid_spacing):
            pygame.draw.line(surface, grid_color, (0, y), (constants.STAGE_WIDTH, y), 1)
        
        # 中央線を強調
        center_x = constants.STAGE_WIDTH // 2
        pygame.draw.line(surface, (120, 120, 120), (center_x, 0), (center_x, constants.STAGE_HEIGHT), 2)
        
        # 地面線を強調
        ground_y = constants.STAGE_HEIGHT
        pygame.draw.line(surface, (120, 120, 120), (0, ground_y), (constants.STAGE_WIDTH, ground_y), 2)
        
        # グリッド数値表示（X軸）
        try:
            font = pygame.font.Font(None, 16)
            for x in range(0, constants.STAGE_WIDTH, grid_spacing * 2):
                text = font.render(str(x), True, (100, 100, 100))
                surface.blit(text, (x + 2, 2))
            
            # Y軸
            for y in range(0, constants.STAGE_HEIGHT, grid_spacing * 2):
                text = font.render(str(y), True, (100, 100, 100))
                surface.blit(text, (2, y + 2))
        except Exception:
            pass

    def draw_hitbox_info(self, surface: pygame.Surface, *, p1: Player, p2: Player) -> None:
        """ヒットボックス情報表示（サイズ・オフセット）"""
        try:
            font = pygame.font.Font(None, 20)
            
            for player, label in [(p1, "P1"), (p2, "P2")]:
                hitboxes = player.get_hitboxes()
                if not hitboxes:
                    continue
                
                # 攻撃ID取得
                attack_id = getattr(player, "_attack_id", None)
                if not attack_id:
                    continue
                
                # frame_data.py から情報取得
                frame_data_dict = getattr(player.character, "frame_data", None)
                if not frame_data_dict:
                    continue
                
                frame_data = frame_data_dict.get(str(attack_id))
                if not frame_data:
                    continue
                
                # ヒットボックスのパラメータ
                hitbox_w = int(getattr(frame_data, "hitbox_width", 0))
                hitbox_h = int(getattr(frame_data, "hitbox_height", 0))
                offset_x = int(getattr(frame_data, "hitbox_offset_x", 0))
                offset_y = int(getattr(frame_data, "hitbox_offset_y", 0))
                
                # 各ヒットボックスに情報を表示
                for hitbox in hitboxes:
                    # サイズ表示（ヒットボックスの上）
                    size_text = f"{hitbox_w}x{hitbox_h}"
                    size_surf = font.render(size_text, True, (255, 255, 0))
                    size_rect = size_surf.get_rect(midbottom=(hitbox.centerx, hitbox.top - 2))
                    
                    # 背景
                    bg = pygame.Surface((size_rect.width + 4, size_rect.height + 2))
                    bg.set_alpha(180)
                    bg.fill((0, 0, 0))
                    surface.blit(bg, (size_rect.x - 2, size_rect.y - 1))
                    surface.blit(size_surf, size_rect)
                    
                    # オフセット表示（ヒットボックスの下）
                    offset_text = f"X:{offset_x} Y:{offset_y}"
                    offset_surf = font.render(offset_text, True, (255, 200, 0))
                    offset_rect = offset_surf.get_rect(midtop=(hitbox.centerx, hitbox.bottom + 2))
                    
                    # 背景
                    bg2 = pygame.Surface((offset_rect.width + 4, offset_rect.height + 2))
                    bg2.set_alpha(180)
                    bg2.fill((0, 0, 0))
                    surface.blit(bg2, (offset_rect.x - 2, offset_rect.y - 1))
                    surface.blit(offset_surf, offset_rect)
                    
                    # プレイヤーラベル（ヒットボックスの中央）
                    label_text = f"{label}: {attack_id}"
                    label_surf = font.render(label_text, True, (255, 255, 255))
                    label_rect = label_surf.get_rect(center=hitbox.center)
                    
                    # 背景
                    bg3 = pygame.Surface((label_rect.width + 4, label_rect.height + 2))
                    bg3.set_alpha(200)
                    bg3.fill((50, 50, 50))
                    surface.blit(bg3, (label_rect.x - 2, label_rect.y - 1))
                    surface.blit(label_surf, label_rect)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Training debug info (key history + frame info)
    # ------------------------------------------------------------------

    def draw_training_debug(
        self,
        surface: pygame.Surface,
        *,
        p1: Player,
        p2: Player,
        show_key_history: bool,
        show_p1_frames: bool,
        show_p2_frames: bool,
        key_history: list[str],
    ) -> None:
        hud_top = 120
        line_h = int(self.debug_font.get_linesize())

        if bool(show_key_history) and key_history:
            x = 12
            y = hud_top
            for i, t in enumerate(key_history):
                surf = self.debug_font.render(t, True, (240, 240, 240))
                surface.blit(surf, (x, y + i * line_h))

        if bool(show_p1_frames):
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
                x = 96
                y = hud_top
                for i, t in enumerate(lines):
                    surf = self.debug_font.render(t, True, (240, 240, 240))
                    surface.blit(surf, (x, y + i * line_h))

        if bool(show_p2_frames):
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
                    surf = self.debug_font.render(t, True, (240, 240, 240))
                    rect = surf.get_rect(topright=(x, y + i * line_h))
                    surface.blit(surf, rect)
