from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pygame

from src.entities.effect import Projectile
from src.utils import constants
from src.utils.paths import resource_path


@dataclass
class GameAssets:
    """ゲームで使用するすべてのアセットを保持するデータクラス"""
    
    # エフェクト画像
    spark_frames: list[pygame.Surface]
    hit_fx_img: pygame.Surface | None
    guard_fx_img: pygame.Surface | None
    
    # 弾のフレーム
    hadoken_proj_frames: list[pygame.Surface] | None
    shinku_proj_frames: list[pygame.Surface] | None
    
    # ダストエフェクト
    rush_dust_frames: list[pygame.Surface]
    k_attack_dust_frames: list[pygame.Surface]
    
    # 背景画像
    title_bg_img: pygame.Surface | None
    stage_bg_img: pygame.Surface | None
    shungoku_stage_bg_img: pygame.Surface | None


class AssetManager:
    """ゲームアセットの読み込みと管理を行うクラス"""
    
    @staticmethod
    def _scale_frames(frames: list[pygame.Surface] | None, *, scale: float) -> list[pygame.Surface] | None:
        """
        フレームリストをスケーリング
        
        Args:
            frames: スケーリングするフレームリスト
            scale: スケール倍率
            
        Returns:
            スケーリングされたフレームリスト
        """
        if frames is None:
            return None
        out: list[pygame.Surface] = []
        s = float(scale)
        for img in frames:
            w = max(1, int(round(img.get_width() * s)))
            h = max(1, int(round(img.get_height() * s)))
            out.append(pygame.transform.smoothscale(img, (w, h)))
        return out
    
    @staticmethod
    def _load_spark_frames() -> list[pygame.Surface]:
        """ヒット火花エフェクトを読み込み"""
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
        return spark_frames
    
    @staticmethod
    def _load_hit_guard_fx() -> tuple[pygame.Surface | None, pygame.Surface | None]:
        """ヒット・ガードエフェクト画像を読み込み"""
        hit_fx_img: pygame.Surface | None = None
        guard_fx_img: pygame.Surface | None = None
        
        try:
            hit_fx_path = resource_path(Path("assets/images/effect/hit.png"))
            if hit_fx_path.exists() and hit_fx_path.is_file():
                hit_img = pygame.image.load(str(hit_fx_path)).convert_alpha()
                try:
                    s = 0.10
                    w = max(1, int(round(hit_img.get_width() * s)))
                    h = max(1, int(round(hit_img.get_height() * s)))
                    hit_img = pygame.transform.smoothscale(hit_img, (w, h))
                except Exception:
                    pass
                hit_fx_img = hit_img
        except Exception:
            hit_fx_img = None
        
        try:
            guard_fx_path = resource_path(Path("assets/images/effect/guard.png"))
            if guard_fx_path.exists() and guard_fx_path.is_file():
                guard_img = pygame.image.load(str(guard_fx_path)).convert_alpha()
                try:
                    s = 0.10
                    w = max(1, int(round(guard_img.get_width() * s)))
                    h = max(1, int(round(guard_img.get_height() * s)))
                    guard_img = pygame.transform.smoothscale(guard_img, (w, h))
                except Exception:
                    pass
                guard_fx_img = guard_img
        except Exception:
            guard_fx_img = None
        
        return hit_fx_img, guard_fx_img
    
    @staticmethod
    def _load_hadoken_frames(p1: Any, p2: Any, spark_frames: list[pygame.Surface]) -> list[pygame.Surface] | None:
        """波動拳の弾フレームを読み込み"""
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

        return AssetManager._scale_frames(hadoken_proj_frames, scale=0.85)
    
    @staticmethod
    def _load_shinku_frames(p1: Any, p2: Any, spark_frames: list[pygame.Surface]) -> list[pygame.Surface] | None:
        """真空波動拳の弾フレームを読み込み"""
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

        return AssetManager._scale_frames(shinku_proj_frames, scale=0.80)
    
    @staticmethod
    def _load_rush_dust_frames(p1: Any, p2: Any) -> list[pygame.Surface]:
        """突進のダストエフェクトを読み込み"""
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
        
        return rush_dust_frames
    
    @staticmethod
    def _load_k_attack_dust_frames(p1: Any, p2: Any) -> list[pygame.Surface]:
        """Kキー攻撃の砂ぼこりエフェクトを読み込み"""
        k_attack_dust_frames: list[pygame.Surface] = []
        try:
            k_attack_dust_frames = []
            for idx in range(1, 18):  # 1から17まで
                key = (6540, idx)
                img = getattr(p1, "_sprites", {}).get(key)
                if img is None:
                    img = getattr(p2, "_sprites", {}).get(key)
                if img is not None:
                    k_attack_dust_frames.append(img)
            if not k_attack_dust_frames:
                base = resource_path("assets/images/RYUKO2nd/organized/hit")
                candidates = sorted(base.glob("*_6540-*.png"))

                def _k_suffix(p: Path) -> int:
                    m = re.search(r"6540-(\d+)", p.name)
                    if m:
                        try:
                            return int(m.group(1))
                        except ValueError:
                            return 0
                    return 0

                candidates = sorted(candidates, key=_k_suffix)
                for p in candidates:
                    try:
                        k_attack_dust_frames.append(pygame.image.load(str(p)).convert_alpha())
                    except pygame.error:
                        continue
        except Exception:
            k_attack_dust_frames = []
        
        return k_attack_dust_frames
    
    @staticmethod
    def _load_title_bg() -> pygame.Surface | None:
        """タイトル画面の背景を読み込み"""
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
        
        return title_bg_img
    
    @staticmethod
    def _load_stage_bg() -> pygame.Surface | None:
        """ステージ背景を読み込み"""
        stage_bg_img: pygame.Surface | None = None
        stage_bg_path = resource_path("assets/images/stage/01.png")
        if stage_bg_path.exists():
            try:
                stage_bg_img = pygame.image.load(str(stage_bg_path)).convert_alpha()
            except pygame.error:
                stage_bg_img = None
        return stage_bg_img
    
    @staticmethod
    def _load_shungoku_stage_bg() -> pygame.Surface | None:
        """瞬獄殺ステージ背景を読み込み"""
        shungoku_stage_bg_img: pygame.Surface | None = None
        shungoku_stage_path = resource_path(Path("assets/images/stage/瞬獄殺.png"))
        if shungoku_stage_path.exists():
            try:
                shungoku_stage_bg_img = pygame.image.load(str(shungoku_stage_path)).convert_alpha()
            except pygame.error:
                shungoku_stage_bg_img = None
        return shungoku_stage_bg_img
    
    @staticmethod
    def load_all_assets(p1: Any, p2: Any) -> GameAssets:
        """
        すべてのゲームアセットを一括読み込み
        
        Args:
            p1: プレイヤー1オブジェクト（スプライト取得用）
            p2: プレイヤー2オブジェクト（スプライト取得用）
            
        Returns:
            GameAssets: すべてのアセットを含むデータクラス
        """
        # エフェクト画像
        spark_frames = AssetManager._load_spark_frames()
        hit_fx_img, guard_fx_img = AssetManager._load_hit_guard_fx()
        
        # 弾のフレーム
        hadoken_proj_frames = AssetManager._load_hadoken_frames(p1, p2, spark_frames)
        shinku_proj_frames = AssetManager._load_shinku_frames(p1, p2, spark_frames)
        
        # ダストエフェクト
        rush_dust_frames = AssetManager._load_rush_dust_frames(p1, p2)
        k_attack_dust_frames = AssetManager._load_k_attack_dust_frames(p1, p2)
        
        # 背景画像
        title_bg_img = AssetManager._load_title_bg()
        stage_bg_img = AssetManager._load_stage_bg()
        shungoku_stage_bg_img = AssetManager._load_shungoku_stage_bg()
        
        return GameAssets(
            spark_frames=spark_frames,
            hit_fx_img=hit_fx_img,
            guard_fx_img=guard_fx_img,
            hadoken_proj_frames=hadoken_proj_frames,
            shinku_proj_frames=shinku_proj_frames,
            rush_dust_frames=rush_dust_frames,
            k_attack_dust_frames=k_attack_dust_frames,
            title_bg_img=title_bg_img,
            stage_bg_img=stage_bg_img,
            shungoku_stage_bg_img=shungoku_stage_bg_img,
        )
