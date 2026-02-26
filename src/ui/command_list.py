from __future__ import annotations

from typing import Any

import pygame

from src.utils import constants


class CommandListMenu:
    """コマンドリスト表示を管理するクラス"""
    
    def __init__(self, *, actions_by_id: dict[int, dict[str, Any]]):
        """
        Args:
            actions_by_id: AIRアクションIDをキーとしたアクション辞書
        """
        self.actions_by_id = actions_by_id
        
        # Guilty Gear Strive方式のボタン名称
        self.items: list[tuple[str, int]] = [
            ("U: P (Punch)", 400),
            ("I: S (Slash)", 209),
            ("O: D (Dust)", 6000),
            ("J: K (Kick)", 229),
            ("K: HS (Heavy Slash)", 6570),
            ("↓↘→+P: 波動拳", 6040),
            ("↓↘→↓↘→+P: 真空波動拳", int(getattr(constants, "SHINKU_HADOKEN_ACTION_ID", 8000))),
            ("←↙↓+K: 突進", 6520),
            ("メニューに戻る", -1),
        ]
        
        self.selection = 0
        self.scroll = 0
        self.closing = False
        self.close_start_ms = 0
        self.preview_start_ms = 0
        self.is_open = False
    
    def get_preview_sprite_key(self, action_id: int, *, elapsed_frames: int) -> tuple[int, int] | None:
        """
        指定されたアクションIDとフレーム数から、プレビュー表示すべきスプライトキーを取得
        
        Args:
            action_id: AIRアクションID
            elapsed_frames: 経過フレーム数
            
        Returns:
            (group, index)のタプル、または取得できない場合はNone
        """
        # 突進(6520)はゲーム中もスプライト固定描画なので、プレビューも確実に出す
        if int(action_id) == 6520:
            startup = int(getattr(constants, "RUSH_STARTUP_FRAMES", 6))
            if int(elapsed_frames) < max(1, startup):
                return (6520, 1)
            return (6520, 2)
        
        a = self.actions_by_id.get(int(action_id))
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
    
    def start_close(self, current_time_ms: int) -> None:
        """
        コマンドリストのクローズアニメーションを開始
        
        Args:
            current_time_ms: 現在時刻（ミリ秒）
        """
        if self.closing:
            return
        self.closing = True
        self.close_start_ms = current_time_ms
        self.preview_start_ms = current_time_ms
    
    def reset_preview_timer(self, current_time_ms: int) -> None:
        """
        プレビュータイマーをリセット
        
        Args:
            current_time_ms: 現在時刻（ミリ秒）
        """
        self.preview_start_ms = current_time_ms
    
    def open(self) -> None:
        """コマンドリストを開く"""
        self.is_open = True
        self.selection = 0
        self.preview_start_ms = pygame.time.get_ticks()
        self.closing = False
    
    def handle_input(self, event: pygame.event.Event, *, menu_move_se: Any = None, menu_confirm_se: Any = None) -> bool:
        """
        入力イベントを処理
        
        Args:
            event: pygameイベント
            menu_move_se: メニュー移動SE
            menu_confirm_se: メニュー確定SE
            
        Returns:
            イベントが処理された場合True
        """
        if not self.is_open or self.closing:
            return False
        
        if event.type != pygame.KEYDOWN:
            return False
        
        if event.key in {pygame.K_UP, pygame.K_w}:
            self.selection = (self.selection - 1) % max(1, len(self.items))
            self.preview_start_ms = pygame.time.get_ticks()
            if menu_move_se is not None:
                menu_move_se.play()
            return True
        elif event.key in {pygame.K_DOWN, pygame.K_s}:
            self.selection = (self.selection + 1) % max(1, len(self.items))
            self.preview_start_ms = pygame.time.get_ticks()
            if menu_move_se is not None:
                menu_move_se.play()
            return True
        elif event.key == pygame.K_RETURN or event.key == pygame.K_u:
            _label, aid = self.items[self.selection]
            if int(aid) < 0:
                self.start_close(pygame.time.get_ticks())
            else:
                self.preview_start_ms = pygame.time.get_ticks()
            if menu_confirm_se is not None:
                menu_confirm_se.play()
            return True
        elif event.key in {pygame.K_ESCAPE, pygame.K_o}:
            self.start_close(pygame.time.get_ticks())
            if event.key == pygame.K_o and menu_move_se is not None:
                menu_move_se.play()
            return True
        
        return False
    
    def draw(self, screen: pygame.Surface, player: Any, *, title_font: pygame.font.Font, keycfg_font: pygame.font.Font) -> None:
        """
        コマンドリストを描画
        
        Args:
            screen: 描画先サーフェス
            player: プレイヤーオブジェクト（スプライト取得用）
            title_font: タイトルフォント
            keycfg_font: キー設定フォント
        """
        if not self.is_open:
            return
        
        # オーバーレイ
        overlay2 = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay2.fill((0, 0, 0, 210))
        screen.blit(overlay2, (0, 0))
        
        w = int(constants.SCREEN_WIDTH)
        h = int(constants.SCREEN_HEIGHT)
        
        panel_w = int(min(920, w - 80))
        panel_h = int(min(600, h - 140))
        panel_x = (w - panel_w) // 2
        panel_y = (h - panel_h) // 2
        
        # パネル背景
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((18, 18, 22, 235))
        screen.blit(panel, (panel_x, panel_y))
        pygame.draw.rect(screen, (90, 255, 220), pygame.Rect(panel_x, panel_y, panel_w, panel_h), 2)
        
        # ヘッダー
        header_txt = "COMMAND LIST"
        header = title_font.render(header_txt, True, (245, 245, 245))
        header_scale_w = max(1, int(round(header.get_width() * 0.38)))
        header_scale_h = max(1, int(round(header.get_height() * 0.38)))
        header = pygame.transform.smoothscale(header, (header_scale_w, header_scale_h))
        screen.blit(header, (panel_x + 26, panel_y + 18))
        
        # サブテキスト
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
        
        # リスト背景
        pygame.draw.rect(screen, (25, 25, 35), pygame.Rect(list_x, list_y0 - 8, list_w, inner_h), 0)
        pygame.draw.rect(screen, (80, 80, 110), pygame.Rect(list_x, list_y0 - 8, list_w, inner_h), 1)
        
        # プレビュー背景
        pygame.draw.rect(screen, (20, 20, 20), pygame.Rect(preview_x, preview_y, preview_w, preview_h), 0)
        pygame.draw.rect(screen, (80, 80, 80), pygame.Rect(preview_x, preview_y, preview_w, preview_h), 2)
        
        # アイテムリスト描画
        list_y = int(list_y0)
        row_h = 42
        for i, (label, _aid) in enumerate(self.items):
            selected = (i == int(self.selection))
            if selected:
                pygame.draw.rect(screen, (90, 255, 220, 28), pygame.Rect(list_x + 10, list_y - 6, list_w - 20, row_h), 0)
                pygame.draw.rect(screen, (90, 255, 220), pygame.Rect(list_x + 10, list_y - 6, list_w - 20, row_h), 1)
            c = (255, 240, 120) if selected else (230, 230, 230)
            s = keycfg_font.render(label, True, c)
            screen.blit(s, (list_x + 18, list_y))
            list_y += row_h
        
        # スクロールバー
        max_visible_items = max(1, int(inner_h // row_h))
        if int(len(self.items)) > int(max_visible_items):
            max_scroll_items = max(1, int(len(self.items)) - int(max_visible_items))
            thumb_height = max(20, int(round(float(inner_h) * (float(max_visible_items) / float(len(self.items))))))
            thumb_y = inner_y + int(round(float(self.scroll) * (float(inner_h - thumb_height) / float(max_scroll_items))))
            pygame.draw.rect(screen, (60, 60, 60), pygame.Rect(panel_x + panel_w - 18, inner_y, 12, inner_h))
            pygame.draw.rect(screen, (180, 180, 180), pygame.Rect(panel_x + panel_w - 17, thumb_y, 10, thumb_height))
        
        # プレビュー描画
        if self.items:
            _label, aid = self.items[self.selection]
            if int(aid) < 0:
                aid = 0
            elapsed = pygame.time.get_ticks() - int(self.preview_start_ms)
            elapsed_frames = int(elapsed // max(1, int(1000 / constants.FPS)))
            
            if self.closing:
                close_elapsed = pygame.time.get_ticks() - int(self.close_start_ms)
                close_frames = int(close_elapsed // max(1, int(1000 / constants.FPS)))
                pause = 20
                idx = min(7, int(close_frames))
                if close_frames >= 8:
                    idx = 7
                img = getattr(player, "_sprites", {}).get((181, idx))
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
                    self.is_open = False
                    self.closing = False
            else:
                key = self.get_preview_sprite_key(int(aid), elapsed_frames=elapsed_frames)
                if key is not None:
                    img = getattr(player, "_sprites", {}).get(key)
                    if img is not None:
                        show = img
                        if int(getattr(player, "facing", 1)) < 0:
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
