#!/usr/bin/env python3
"""neuroflow pre-push version check.

Rejects a push if substantive files changed between the remote branch and
the local commits being pushed, but .claude-plugin/plugin.json version was
NOT bumped.

Invoked automatically by .githooks/pre-push.
Installed via: uv run python scripts/automation/install_hooks.py
"""

import json
import subprocess
import sys

EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
VERSION_FILE = ".claude-plugin/plugin.json"

# These files are expected to change as part of a version bump itself —
# a push that only touches these is allowed without a further bump.
BUMP_FILES = {
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    "mkdocs.yml",
    "README.md",
    "docs/changelog.md",
}


def git(*args: str) -> str:
    r = subprocess.run(
        ["git"] + list(args),
        capture_output=True,
        text=True,
        check=True,
    )
    return r.stdout.strip()


def get_version_at(sha: str) -> str | None:
    try:
        raw = subprocess.run(
            ["git", "show", f"{sha}:{VERSION_FILE}"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        return json.loads(raw).get("version")
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
        return None


def changed_files(base: str, head: str) -> list[str]:
    """Return paths changed between base and head, excluding version-bump files."""
    try:
        out = git("diff", "--name-only", base, head)
    except subprocess.CalledProcessError:
        return []
    return [f for f in out.splitlines() if f.strip() and f not in BUMP_FILES]


def main() -> int:
    failed = False

    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 4:
            continue

        local_ref, local_sha, remote_ref, remote_sha = parts[:4]

        # Deletion push — nothing to check
        if local_sha == "0" * 40:
            continue

        # New branch / no remote history — first push, skip check
        if remote_sha == "0" * 40:
            continue

        local_version = get_version_at(local_sha)
        remote_version = get_version_at(remote_sha)

        # Can't read versions from git objects — skip silently
        if local_version is None or remote_version is None:
            continue

        if local_version == remote_version:
            substantive = changed_files(remote_sha, local_sha)
            if substantive:
                sample = substantive[:10]
                overflow = len(substantive) - 10
                print(
                    f"\n\033[31m[neuroflow pre-push] Version not bumped!\033[0m\n"
                    f"  plugin.json is still at v{local_version} "
                    f"but {len(substantive)} file(s) changed:\n"
                    + "".join(f"    · {f}\n" for f in sample)
                    + (f"    … and {overflow} more\n" if overflow > 0 else "")
                    + f"\n  Bump the version in .claude-plugin/plugin.json (and marketplace.json),\n"
                    f"  update README.md, docs/changelog.md, and mkdocs.yml, then re-push.\n"
                    f"  See: .github/agents/neuroflow-developer.md § Release workflow\n"
                    f"  To skip (use sparingly): git push --no-verify\n",
                    file=sys.stderr,
                )
                failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
