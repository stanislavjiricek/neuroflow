#!/usr/bin/env python3
"""neuroflow pre-push version check.

Rejects a push if substantive files changed but .claude-plugin/plugin.json version was
NOT bumped. Like CI (validate_pr.py V7), it compares the pushed commits with their merge
base on origin's default branch, and it uses the same exempt list (repo_checks.py), so the
hook and CI agree. Without an origin default branch it falls back to the remote branch tip.

Invoked automatically by .githooks/pre-push.
Installed via: uv run python scripts/automation/install_hooks.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repo_checks import substantive_changes  # noqa: E402

ZERO = "0" * 40
VERSION_FILE = ".claude-plugin/plugin.json"


def git(*args: str, cwd: str | None = None) -> str:
    r = subprocess.run(
        ["git"] + list(args),
        capture_output=True,
        text=True,
        check=True,
        cwd=cwd,
    )
    return r.stdout.strip()


def get_version_at(sha: str, cwd: str | None = None) -> str | None:
    try:
        return json.loads(git("show", f"{sha}:{VERSION_FILE}", cwd=cwd)).get("version")
    except (subprocess.CalledProcessError, json.JSONDecodeError, AttributeError):
        return None


def changed_files(base: str, head: str, cwd: str | None = None) -> list[str]:
    """Return paths changed between base and head that need a version bump."""
    try:
        out = git("diff", "--name-only", base, head, cwd=cwd)
    except subprocess.CalledProcessError:
        return []
    return substantive_changes(out.splitlines())


def default_branch_ref(cwd: str | None = None) -> str | None:
    """origin's default branch (origin/HEAD, else origin/main), or None if unknown."""
    for args in (("symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"),
                 ("rev-parse", "--verify", "--quiet", "--abbrev-ref", "origin/main")):
        try:
            ref = git(*args, cwd=cwd)
        except subprocess.CalledProcessError:
            continue
        if ref:
            return ref
    return None


def comparison_base(local_sha: str, remote_sha: str, cwd: str | None = None) -> str | None:
    """Merge base with origin's default branch (CI's base...HEAD); else the remote tip."""
    ref = default_branch_ref(cwd)
    if ref:
        try:
            return git("merge-base", ref, local_sha, cwd=cwd)
        except subprocess.CalledProcessError:
            pass
    return None if remote_sha == ZERO else remote_sha


def main(stdin=None, cwd: str | None = None) -> int:
    failed = False

    for raw_line in stdin or sys.stdin:
        parts = raw_line.split()
        if len(parts) < 4:
            continue

        local_ref, local_sha, remote_ref, remote_sha = parts[:4]

        # Deletion push — nothing to check
        if local_sha == ZERO:
            continue

        base = comparison_base(local_sha, remote_sha, cwd)
        # No default branch and no remote history: nothing to compare against
        if base is None or base == local_sha:
            continue

        local_version = get_version_at(local_sha, cwd)
        base_version = get_version_at(base, cwd)

        # Can't read versions from git objects — skip silently
        if local_version is None or base_version is None:
            continue

        if local_version == base_version:
            substantive = changed_files(base, local_sha, cwd)
            if substantive:
                sample = substantive[:10]
                overflow = len(substantive) - 10
                print(
                    f"\n\033[31m[neuroflow pre-push] Version not bumped!\033[0m\n"
                    f"  plugin.json is still at v{local_version} "
                    f"but {len(substantive)} file(s) changed since {base[:10]}:\n"
                    + "".join(f"    · {f}\n" for f in sample)
                    + (f"    … and {overflow} more\n" if overflow > 0 else "")
                    + "\n  Bump with: python scripts/automation/bump_version.py\n"
                    "  then update README.md, docs/changelog.md and docs/index.md, and re-push.\n"
                    "  See: skills/neuroflow-develop/SKILL.md § Release workflow\n"
                    "  (Compared with origin's default branch — run git fetch if it is stale.)\n"
                    "  To skip (use sparingly): git push --no-verify\n",
                    file=sys.stderr,
                )
                failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
