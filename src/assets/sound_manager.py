from __future__ import annotations

from pathlib import Path

import pygame

from src.engine.context import GameState
from src.utils.paths import resource_path


class SoundManager:
    """サウンドエフェクトとBGMの読み込み・管理を担当するクラス。"""

    def __init__(self) -> None:
        # SE読み込み
        self.start_se = self._load_sound_any(["start.wav", "start.ogg", "start.mp3"])
        self.menu_confirm_se = self._load_sound(Path("assets/sounds/SE/決定ボタンを押す15.mp3"))
        self.menu_move_se = self._load_sound(Path("assets/sounds/SE/カーソル移動8.mp3"))
        
        # カウントダウンSE
        self.countdown_se_3 = self._load_sound(Path("assets/sounds/SE/「3」.mp3"))
        self.countdown_se_2 = self._load_sound(Path("assets/sounds/SE/「2」.mp3"))
        self.countdown_se_1 = self._load_sound(Path("assets/sounds/SE/「1」.mp3"))
        self.countdown_se_go = self._load_sound(Path("assets/sounds/SE/「ゴー」.mp3"))
        
        # 戦闘SE
        self.beam_se = self._load_sound(Path("assets/sounds/SE/ビーム改.mp3"))
        self.hit_se = self._load_sound(Path("assets/sounds/SE/打撃1.mp3"))
        self.guard_se = self._load_sound(Path("assets/sounds/SE/ガード.wav"))
        
        # 瞬獄殺SE
        self.shungoku_ko_se = self._load_sound(Path("assets/sounds/SE/瞬獄殺.mp3"))
        self.shungoku_super_se = self._load_sound(Path("assets/sounds/SE/超必殺技.wav"))
        self.shungoku_asura_se = self._load_sound(Path("assets/sounds/SE/阿修羅.wav"))
        
        # BGMパス
        self.title_bgm_path = resource_path(Path("assets/sounds/BGM/Revenger.mp3"))
        self.battle_bgm_path = resource_path(Path("assets/sounds/BGM/Who_Is_the_Champion.mp3"))
        
        # BGM状態管理
        self.current_bgm: str | None = None
        self.bgm_suspended: bool = False
        
        # 音量レベル（0-100）
        self.se_volume_level: int = 60
        self.bgm_volume_level: int = 70

    @staticmethod
    def _load_sound(path: Path) -> pygame.mixer.Sound | None:
        """単一のサウンドファイルを読み込む。"""
        full_path = resource_path(path)
        if not full_path.exists():
            return None
        try:
            return pygame.mixer.Sound(str(full_path))
        except pygame.error:
            return None

    @staticmethod
    def _load_sound_any(candidates: list[str]) -> pygame.mixer.Sound | None:
        """複数の候補から最初に見つかったサウンドを読み込む。"""
        for rel in candidates:
            se_path = resource_path(Path("assets/sounds") / rel)
            if not se_path.exists():
                continue
            try:
                return pygame.mixer.Sound(str(se_path))
            except pygame.error:
                pass
        return None

    def apply_se_volume(self) -> None:
        """全SEに音量を適用する。"""
        vol = max(0.0, min(1.0, float(self.se_volume_level) / 100.0))
        try:
            if self.start_se is not None:
                self.start_se.set_volume(0.50 * vol)
            if self.menu_confirm_se is not None:
                self.menu_confirm_se.set_volume(0.55 * vol)
            if self.menu_move_se is not None:
                self.menu_move_se.set_volume(0.45 * vol)
            if self.countdown_se_3 is not None:
                self.countdown_se_3.set_volume(0.22 * vol)
            if self.countdown_se_2 is not None:
                self.countdown_se_2.set_volume(0.22 * vol)
            if self.countdown_se_1 is not None:
                self.countdown_se_1.set_volume(0.22 * vol)
            if self.countdown_se_go is not None:
                self.countdown_se_go.set_volume(0.25 * vol)
            if self.beam_se is not None:
                self.beam_se.set_volume(0.40 * vol)
            if self.hit_se is not None:
                self.hit_se.set_volume(0.18 * vol)
            if self.shungoku_ko_se is not None:
                self.shungoku_ko_se.set_volume(0.22 * vol)
            if self.shungoku_super_se is not None:
                self.shungoku_super_se.set_volume(0.25 * vol)
            if self.shungoku_asura_se is not None:
                self.shungoku_asura_se.set_volume(0.22 * vol)
            if self.guard_se is not None:
                self.guard_se.set_volume(0.18 * vol)
        except Exception:
            pass

    def apply_bgm_volume(self) -> None:
        """BGM音量を適用する。"""
        try:
            pygame.mixer.music.set_volume(float(self.bgm_volume_level) / 100.0)
        except Exception:
            pass

    def play_bgm(self, path: Path) -> None:
        """BGMを再生する。"""
        if not path.exists():
            return
        try:
            pygame.mixer.music.load(str(path))
            self.apply_bgm_volume()
            pygame.mixer.music.play(-1)
        except Exception:
            pass

    def ensure_bgm_for_state(self, state: GameState) -> None:
        """ゲーム状態に応じて適切なBGMを再生する。"""
        if self.bgm_suspended:
            return
        
        want: str | None = None
        if state == GameState.TITLE:
            want = str(self.title_bgm_path)
        elif state in {GameState.BATTLE, GameState.TRAINING}:
            want = str(self.battle_bgm_path)
        elif state == GameState.CHAR_SELECT:
            want = str(self.title_bgm_path)
        elif state == GameState.RESULT:
            want = str(self.title_bgm_path)
        
        if want is not None and self.current_bgm != want:
            path = self.title_bgm_path if "Revenger" in want else self.battle_bgm_path
            self.play_bgm(path)
            self.current_bgm = want

    def stop_bgm(self) -> None:
        """BGMを停止し、サスペンド状態にする。"""
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        self.bgm_suspended = True
        self.current_bgm = None

    def resume_bgm(self, state: GameState) -> None:
        """BGMサスペンドを解除し、再生を再開する。"""
        self.bgm_suspended = False
        self.ensure_bgm_for_state(state)
