from __future__ import annotations

from typing import Any

from src.utils import constants


class PlayerAnimator:
    """キャラクターアニメーションのパッチ処理を管理するクラス"""
    
    @staticmethod
    def actions_have_frame_clsns(actions: list[dict[str, Any]]) -> bool:
        """
        アクションリストにclsn1またはclsn2が含まれているかチェック
        
        Args:
            actions: AIRアクションのリスト
            
        Returns:
            clsn1またはclsn2が存在する場合True
        """
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
    
    @staticmethod
    def inject_special_actions(actions: list[dict[str, Any]]) -> None:
        """
        波動拳と真空波動拳のアクションを注入
        
        Args:
            actions: AIRアクションのリスト（in-place更新）
        """
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
    
    @staticmethod
    def inject_throw_actions(actions: list[dict[str, Any]]) -> None:
        """
        投げ技アニメーション（Action 800-804: 投げ技の各パターン）を注入
        
        800: 右向きで右に投げる（800-3→800-4→800-13）
        801: 右向きで左に投げる（800-3→800-12）
        802: 左向きで左に投げる（反転800-3→800-4→800-13）
        803: 左向きで右に投げる（反転800-3→800-12）
        
        Args:
            actions: AIRアクションのリスト（in-place更新）
        """
        # Action 800: 右向きで右に投げる（800-3, 800-4, 800-13）
        if not any(isinstance(a, dict) and int(a.get("action", -1)) == 800 for a in actions):
            frames: list[dict[str, Any]] = []
            # つかみモーション（800-3, 800-4）
            for idx in [3, 4]:
                frames.append({
                    "group": 800,
                    "index": idx,
                    "x": 0,
                    "y": 0,
                    "time": 2,
                    "flags": [],
                    "clsn1": [],
                    "clsn2": [[-20, -90, 20, 0]],
                })
            # 投げモーション（800-13: 左から右に投げる）
            frames.append({
                "group": 800,
                "index": 13,
                "x": 0,
                "y": 0,
                "time": 20,  # 投げアニメーションの持続時間
                "flags": [],
                "clsn1": [],
                "clsn2": [[-20, -90, 20, 0]],
            })
            actions.append({"action": 800, "frames": frames})
        
        # Action 801: 右向きで左に投げる（800-3→800-12）
        if not any(isinstance(a, dict) and int(a.get("action", -1)) == 801 for a in actions):
            frames: list[dict[str, Any]] = []
            # つかみモーション（800-3, 800-4）
            for idx in [3, 4]:
                frames.append({
                    "group": 800,
                    "index": idx,
                    "x": 0,
                    "y": 0,
                    "time": 2,
                    "flags": [],
                    "clsn1": [],
                    "clsn2": [[-20, -90, 20, 0]],
                })
            # 投げモーション（800-5から800-12: 右から左に投げる）
            for idx in range(5, 13):
                frames.append({
                    "group": 800,
                    "index": idx,
                    "x": 0,
                    "y": 0,
                    "time": 2,
                    "flags": [],
                    "clsn1": [],
                    "clsn2": [[-20, -90, 20, 0]],
                })
            actions.append({"action": 801, "frames": frames})
        
        # Action 802: 左向きで左に投げる（反転800-3→800-4→800-13）
        if not any(isinstance(a, dict) and int(a.get("action", -1)) == 802 for a in actions):
            frames: list[dict[str, Any]] = []
            # つかみモーション（反転800-3, 800-4）
            for idx in [3, 4]:
                frames.append({
                    "group": 800,
                    "index": idx,
                    "x": 0,
                    "y": 0,
                    "time": 2,
                    "flags": ["H"],  # 水平反転
                    "clsn1": [],
                    "clsn2": [[-20, -90, 20, 0]],
                })
            # 投げモーション（反転800-13）
            frames.append({
                "group": 800,
                "index": 13,
                "x": 0,
                "y": 0,
                "time": 20,
                "flags": ["H"],  # 水平反転
                "clsn1": [],
                "clsn2": [[-20, -90, 20, 0]],
            })
            actions.append({"action": 802, "frames": frames})
        
        # Action 803: 左向きで右に投げる（反転800-3→800-12）
        if not any(isinstance(a, dict) and int(a.get("action", -1)) == 803 for a in actions):
            frames: list[dict[str, Any]] = []
            # つかみモーション（反転800-3, 800-4）
            for idx in [3, 4]:
                frames.append({
                    "group": 800,
                    "index": idx,
                    "x": 0,
                    "y": 0,
                    "time": 2,
                    "flags": ["H"],  # 水平反転
                    "clsn1": [],
                    "clsn2": [[-20, -90, 20, 0]],
                })
            # 投げモーション（反転800-5から800-12）
            for idx in range(5, 13):
                frames.append({
                    "group": 800,
                    "index": idx,
                    "x": 0,
                    "y": 0,
                    "time": 2,
                    "flags": ["H"],  # 水平反転
                    "clsn1": [],
                    "clsn2": [[-20, -90, 20, 0]],
                })
            actions.append({"action": 803, "frames": frames})
    
    @staticmethod
    def inject_action_6000(actions: list[dict[str, Any]]) -> None:
        """
        Action 6000（Oキー: 足を振り上げる攻撃）を注入
        
        Args:
            actions: AIRアクションのリスト（in-place更新）
        """
        # Action 6000（Oキー: 足を振り上げる攻撃）を追加
        # スプライト6000-8から6000-18まで（11フレーム）
        if not any(isinstance(a, dict) and int(a.get("action", -1)) == 6000 for a in actions):
            frames: list[dict[str, Any]] = []
            # 準備モーション（3フレーム: 6000-8, 9, 10）
            for idx in [8, 9, 10]:
                frames.append({
                    "group": 6000,
                    "index": idx,
                    "x": 0,
                    "y": 0,
                    "time": 2,
                    "flags": [],
                    "clsn1": [],
                    "clsn2": [[-20, -90, 20, 0]],
                })
            # 攻撃判定あり（6フレーム: 6000-11, 12, 13, 14, 15, 16）
            for idx in [11, 12, 13, 14, 15, 16]:
                frames.append({
                    "group": 6000,
                    "index": idx,
                    "x": 0,
                    "y": 0,
                    "time": 2,
                    "flags": [],
                    "clsn1": [[10, -100, 55, -30]],
                    "clsn2": [[-20, -90, 20, 0]],
                })
            # 硬直モーション（2フレーム: 6000-17, 18）
            for idx in [17, 18]:
                frames.append({
                    "group": 6000,
                    "index": idx,
                    "x": 0,
                    "y": 0,
                    "time": 2,
                    "flags": [],
                    "clsn1": [],
                    "clsn2": [[-20, -90, 20, 0]],
                })
            actions.append({"action": 6000, "frames": frames})
    
    @staticmethod
    def patch_action400_startup(actions: list[dict[str, Any]]) -> None:
        """
        Action 400（Pキー）の発生フレームを調整
        
        Args:
            actions: AIRアクションのリスト（in-place更新）
        """
        # Action 400（Pキー）の発生を「入力から4フレーム目」に合わせるため、
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
    
    @staticmethod
    def patch_action1000_mp(actions: list[dict[str, Any]]) -> None:
        """
        Action 1000（Dキー）のフレームを調整
        
        Args:
            actions: AIRアクションのリスト（in-place更新）
        """
        # Dキー用（元々Oキーだったaction 1000）
        target = None
        for a in actions:
            if isinstance(a, dict) and int(a.get("action", -1)) == 1000:
                target = a
                break
        if target is None:
            return

        frames = target.get("frames")
        if not isinstance(frames, list) or not frames:
            return

        new_frames: list[dict[str, Any]] = []
        for fr in frames:
            if not isinstance(fr, dict):
                continue
            if int(fr.get("group", -1)) != 1000:
                continue
            idx = int(fr.get("index", -1))
            if 0 <= idx <= 7:
                fr = dict(fr)
                if idx < 4:
                    fr["clsn1"] = []
                new_frames.append(fr)

        if not new_frames:
            return

        target["frames"] = new_frames
    
    @staticmethod
    def patch_action209_mp(actions: list[dict[str, Any]]) -> None:
        """
        Action 209（Sキー）のフレームを調整
        
        Args:
            actions: AIRアクションのリスト（in-place更新）
        """
        # Sキー用（元々Iキーだったaction 209）
        target = None
        for a in actions:
            if isinstance(a, dict) and int(a.get("action", -1)) == 209:
                target = a
                break
        if target is None:
            return

        frames = target.get("frames")
        if not isinstance(frames, list) or not frames:
            return

        new_frames: list[dict[str, Any]] = []
        for fr in frames:
            if not isinstance(fr, dict):
                continue
            if int(fr.get("group", -1)) != 209:
                continue
            idx = int(fr.get("index", -1))
            if 0 <= idx <= 7:
                fr = dict(fr)
                if idx < 4:
                    fr["clsn1"] = []
                new_frames.append(fr)

        if not new_frames:
            return

        target["frames"] = new_frames
    
    @staticmethod
    def apply_all_patches(actions: list[dict[str, Any]]) -> None:
        """
        すべてのアニメーションパッチを一括適用
        
        Args:
            actions: AIRアクションのリスト（in-place更新）
        """
        PlayerAnimator.patch_action400_startup(actions)
        PlayerAnimator.patch_action1000_mp(actions)
        PlayerAnimator.patch_action209_mp(actions)
        PlayerAnimator.inject_special_actions(actions)
        PlayerAnimator.inject_action_6000(actions)
        PlayerAnimator.inject_throw_actions(actions)
