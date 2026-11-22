#!/usr/bin/env python3
"""Build the standalone game executable with PyInstaller.

Usage:
    python scripts/build_exe.py

The build uses ``tetris.spec`` and writes ``dist/tetris.exe`` on Windows
(``dist/tetris`` elsewhere). The executable bundles Python, Pygame and the
``tetris`` package, so it runs on a machine without Python installed.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPEC_FILE = PROJECT_ROOT / "tetris.spec"
DIST_DIR = PROJECT_ROOT / "dist"
EXE_NAME = "tetris.exe" if os.name == "nt" else "tetris"


def main() -> int:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print(
            "PyInstaller is required to build the executable.\n"
            "Install it with: python -m pip install -r requirements-build.txt",
            file=sys.stderr,
        )
        return 1

    if not SPEC_FILE.is_file():
        print(f"Missing build definition: {SPEC_FILE}", file=sys.stderr)
        return 1

    shutil.rmtree(DIST_DIR, ignore_errors=True)
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        str(SPEC_FILE),
    ]
    result = subprocess.run(command, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print("PyInstaller failed; see the output above.", file=sys.stderr)
        return result.returncode

    executable = DIST_DIR / EXE_NAME
    if not executable.is_file():
        print(f"Expected build output was not produced: {executable}", file=sys.stderr)
        return 1

    print(f"Built {executable}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
