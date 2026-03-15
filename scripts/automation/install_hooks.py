#!/usr/bin/env python3
"""One-time setup: point git's core.hooksPath at .githooks/ for this repo.

Run this once after cloning:
    uv run python scripts/automation/install_hooks.py
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent


def main() -> int:
    subprocess.run(
        ["git", "-C", str(ROOT), "config", "core.hooksPath", ".githooks"],
        check=True,
    )
    hook = ROOT / ".githooks" / "pre-push"
    print("✓ Git hooks installed  (core.hooksPath = .githooks)")
    print(f"  pre-push hook: {hook}")
    print()
    print("  Effect: pushing is blocked if tracked files changed")
    print("  but plugin.json version was not bumped.")
    print()
    print("  To skip the check on a specific push: git push --no-verify")
    return 0


if __name__ == "__main__":
    sys.exit(main())
