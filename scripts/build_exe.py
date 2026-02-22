from __future__ import annotations

import subprocess
from pathlib import Path
import sys


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    dist = project_root / "build"
    work = project_root / "build" / "temp"

    dist.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--log-level",
        "WARN",
        "--distpath",
        str(dist),
        "--workpath",
        str(work),
        "main.spec",
    ]

    print(" ".join(cmd))
    subprocess.check_call(cmd, cwd=str(project_root))
    print(f"Built: {dist / 'main.exe'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
