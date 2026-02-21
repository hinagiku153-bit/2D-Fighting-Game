from __future__ import annotations

import argparse
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# ============================
# Image organization
# ============================


@dataclass(frozen=True)
class ImageRecord:
    path: Path
    char_name: str
    group: int
    index: int


_FILENAME_RE = re.compile(
    r"^(?P<name>.+)_(?P<group>\d+)(?:[_-])(?P<index>\d+)\.png$",
    re.IGNORECASE,
)


def parse_image_filename(path: Path) -> ImageRecord | None:
    m = _FILENAME_RE.match(path.name)
    if not m:
        return None

    return ImageRecord(
        path=path,
        char_name=m.group("name"),
        group=int(m.group("group")),
        index=int(m.group("index")),
    )


def category_from_group(group: int) -> str:
    # User-provided mapping rules.
    if group == 0:
        return "idle"
    if group in (10, 11):
        return "walk"
    if group in (20, 40):
        return "jump"
    if 200 <= group <= 499:
        return "attack"
    if group >= 5000:
        return "hit"
    return "other"


def organize_images(
    *,
    src_dir: Path,
    dst_dir: Path,
    apply: bool,
) -> dict[str, int]:
    if not src_dir.exists():
        raise FileNotFoundError(f"Source images directory not found: {src_dir}")

    dst_dir.mkdir(parents=True, exist_ok=True)

    stats: dict[str, int] = {
        "idle": 0,
        "walk": 0,
        "jump": 0,
        "attack": 0,
        "hit": 0,
        "other": 0,
        "skipped": 0,
    }

    for item in sorted(src_dir.iterdir()):
        if not item.is_file():
            continue
        if item.suffix.lower() != ".png":
            continue

        rec = parse_image_filename(item)
        if rec is None:
            stats["skipped"] += 1
            continue

        category = category_from_group(rec.group)
        target_dir = dst_dir / category
        target_dir.mkdir(parents=True, exist_ok=True)

        target_path = target_dir / item.name

        if target_path.exists():
            # Avoid overwriting; treat as skipped.
            stats["skipped"] += 1
            continue

        if apply:
            shutil.move(str(item), str(target_path))
        else:
            # dry-run: no filesystem changes.
            pass

        stats[category] += 1

    return stats


# ============================
# AIR parsing
# ============================


_BEGIN_ACTION_RE = re.compile(r"^\[\s*Begin\s+Action\s+(?P<id>-?\d+)\s*\]$", re.IGNORECASE)
_CLSN_RE = re.compile(r"^(?P<kind>Clsn1|Clsn2)\s*:\s*(?P<count>\d+)\s*$", re.IGNORECASE)
_CLSN_ITEM_RE = re.compile(
    r"^(?P<kind>Clsn1|Clsn2)\s*\[\s*(?P<idx>\d+)\s*\]\s*=\s*(?P<x1>-?\d+)\s*,\s*(?P<y1>-?\d+)\s*,\s*(?P<x2>-?\d+)\s*,\s*(?P<y2>-?\d+)\s*$",
    re.IGNORECASE,
)


def _strip_comment(line: str) -> str:
    # AIR comment usually begins with ';'
    if ";" in line:
        line = line.split(";", 1)[0]
    return line.strip()


def parse_air_file(air_path: Path) -> list[dict[str, Any]]:
    if not air_path.exists():
        raise FileNotFoundError(f"AIR file not found: {air_path}")

    actions: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    pending_clsn1: list[tuple[int, int, int, int]] = []
    pending_clsn2: list[tuple[int, int, int, int]] = []

    with air_path.open("r", encoding="cp932", errors="ignore") as f:
        for raw_line in f:
            line = _strip_comment(raw_line)
            if not line:
                continue

            m = _BEGIN_ACTION_RE.match(line)
            if m:
                if current is not None:
                    actions.append(current)
                current = {
                    "action": int(m.group("id")),
                    "frames": [],
                    "clsn1": [],
                    "clsn2": [],
                }
                pending_clsn1 = []
                pending_clsn2 = []
                continue

            if current is None:
                continue

            m = _CLSN_RE.match(line)
            if m:
                # Clsn定義開始。個数はバリデーションには使わず、以降の Clsn[n] 行を収集する。
                continue

            m = _CLSN_ITEM_RE.match(line)
            if m:
                kind = m.group("kind").lower()
                rect = (int(m.group("x1")), int(m.group("y1")), int(m.group("x2")), int(m.group("y2")))
                if kind == "clsn1":
                    pending_clsn1.append(rect)
                else:
                    pending_clsn2.append(rect)
                continue

            # Frame line examples:
            # 0, 0, 0, 0, 8
            # 5, 0, 0, 0, 3, H
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 5 and all(re.fullmatch(r"-?\d+", p) for p in parts[:5]):
                group, index, x, y, time = (int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4]))
                flags = [p for p in parts[5:] if p]
                frame_clsn1 = list(pending_clsn1)
                frame_clsn2 = list(pending_clsn2)
                current["frames"].append(
                    {
                        "group": group,
                        "index": index,
                        "x": x,
                        "y": y,
                        "time": time,
                        "flags": flags,
                        "clsn1": frame_clsn1,
                        "clsn2": frame_clsn2,
                    }
                )
                current["clsn1"].extend(frame_clsn1)
                current["clsn2"].extend(frame_clsn2)
                pending_clsn1 = []
                pending_clsn2 = []
                continue

    if current is not None:
        actions.append(current)

    return actions


def write_air_as_python(actions: list[dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        f.write("from __future__ import annotations\n\n")
        f.write("# Generated from MUGEN AIR file.\n")
        f.write("ACTIONS = ")
        f.write(repr(actions))
        f.write("\n")


# ============================
# CLI
# ============================


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Organize Fighter Factory exported PNGs by MUGEN group number and parse AIR into a Python list.",
    )
    parser.add_argument(
        "--src-images",
        type=Path,
        default=Path(r"assets/images/RYUKO2nd/SFF出力画像"),
        help="Source directory containing exported PNG images.",
    )
    parser.add_argument(
        "--dst-images",
        type=Path,
        default=Path(r"assets/images/RYUKO2nd/organized"),
        help="Destination directory to create category folders under.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually move files. Without this flag, does a dry-run.",
    )
    parser.add_argument(
        "--air",
        type=Path,
        default=Path(r"assets/images/RYUKO2nd/RYUKO.AIR"),
        help="Path to AIR file.",
    )
    parser.add_argument(
        "--write-air-out",
        type=Path,
        default=Path(r"assets/images/RYUKO2nd/ryuko_air_actions.py"),
        help="Output .py file to write parsed AIR actions.",
    )
    parser.add_argument(
        "--no-air",
        action="store_true",
        help="Skip AIR parsing/export.",
    )

    args = parser.parse_args()

    project_root = Path(os.getcwd())
    src_images = (project_root / args.src_images).resolve()
    dst_images = (project_root / args.dst_images).resolve()

    stats = organize_images(src_dir=src_images, dst_dir=dst_images, apply=bool(args.apply))

    print("=== Image organization ===")
    print(f"mode: {'APPLY (move)' if args.apply else 'DRY-RUN (no changes)'}")
    print(f"src:  {src_images}")
    print(f"dst:  {dst_images}")
    for k in ("idle", "walk", "jump", "attack", "hit", "other", "skipped"):
        print(f"{k:>7}: {stats.get(k, 0)}")

    if not args.no_air:
        air_path = (project_root / args.air).resolve()
        out_path = (project_root / args.write_air_out).resolve()

        actions = parse_air_file(air_path)
        write_air_as_python(actions, out_path)

        print("=== AIR parse/export ===")
        print(f"air:   {air_path}")
        print(f"out:   {out_path}")
        print(f"actions: {len(actions)}")


if __name__ == "__main__":
    main()
