#!/usr/bin/env python3
"""Bump the neuroflow plugin version in the four places the release workflow lists.

    python scripts/automation/bump_version.py              # patch bump: 0.2.21 -> 0.2.22
    python scripts/automation/bump_version.py --set 0.3.0  # explicit version
    python scripts/automation/bump_version.py --sync       # copy plugin.json's version to the others
    python scripts/automation/bump_version.py --check      # report drift, change nothing
    add --dry-run to show what would change without writing

Sites (repo_checks.VERSION_SITES, also checked by validate_pr.py V2):
  .claude-plugin/plugin.json      version
  .claude-plugin/marketplace.json plugins[].version
  mkdocs.yml                      extra.version
  .neuroflow/project_config.md    plugin_version (skipped when the file is absent)

Only the version strings change; formatting and line endings stay as they are. The release
notes (README What's new, docs/changelog.md) are written by hand - this script prints them as
next steps.

Exit codes: 0 = done (or in sync), 1 = --check found drift, 2 = usage or runtime error.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repo_checks  # noqa: E402

_VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def next_patch(version: str) -> str:
    m = _VERSION_RE.match(version)
    if not m:
        raise ValueError(f"not a MAJOR.MINOR.PATCH version: {version!r}")
    major, minor, patch = (int(x) for x in m.groups())
    return f"{major}.{minor}.{patch + 1}"


def current_versions(root: Path) -> dict[str, list[str] | None]:
    return {rel: repo_checks.site_versions(root, rel) for rel in repo_checks.VERSION_SITES}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Bump or sync the plugin version in all four version sites.")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--set", metavar="X.Y.Z", help="write this version instead of the next patch")
    mode.add_argument("--sync", action="store_true", help="write plugin.json's current version to the other sites")
    mode.add_argument("--check", action="store_true", help="exit 1 if the sites disagree; write nothing")
    ap.add_argument("--dry-run", action="store_true", help="show the changes without writing")
    ap.add_argument("--root", type=Path, default=repo_checks.ROOT, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    root = args.root.resolve()

    found = current_versions(root)
    plugin = found[repo_checks.PLUGIN_JSON]
    if not plugin:
        print(f"bump_version: {repo_checks.PLUGIN_JSON} is missing or has no version", file=sys.stderr)
        return 2
    current = plugin[0]
    drift = {rel: vs for rel, vs in found.items() if vs is not None and any(v != current for v in vs)}

    if args.check:
        for rel, vs in found.items():
            state = "absent" if vs is None else ", ".join(vs) or "no version found"
            print(f"  {rel}: {state}")
        if drift:
            print(f"bump_version: {len(drift)} site(s) differ from plugin.json {current} (fix: --sync)")
            return 1
        print(f"bump_version: all sites at {current}")
        return 0

    try:
        target = current if args.sync else args.set or next_patch(current)
        if args.set and not _VERSION_RE.match(args.set):
            raise ValueError(f"not a MAJOR.MINOR.PATCH version: {args.set!r}")
    except ValueError as exc:
        print(f"bump_version: {exc}", file=sys.stderr)
        return 2

    changes = [(rel, vs) for rel, vs in found.items() if vs is not None and (not vs or any(v != target for v in vs))]
    missing = [rel for rel, vs in changes if not vs]
    if missing:
        print(f"bump_version: no version string found in {', '.join(missing)} - fix the file by hand", file=sys.stderr)
        return 2
    if not changes:
        print(f"bump_version: every site is already at {target}")
        return 0
    for rel, vs in changes:
        print(f"  {rel}: {', '.join(sorted(set(vs)))} -> {target}")
    if args.dry_run:
        print("bump_version: dry run, nothing written")
        return 0
    written = [rel for rel, _ in changes if repo_checks.set_site_version(root, rel, target)]
    failed = [rel for rel, _ in changes if rel not in written]
    if failed:
        print(f"bump_version: could not rewrite {', '.join(failed)}", file=sys.stderr)
        return 2
    print(f"bump_version: {len(written)} site(s) now at {target}")
    if not args.sync:
        print("Next (by hand): README.md `## What's new in " + target + "`, docs/changelog.md `## " + target + "`, "
              "then "
              "python scripts/automation/validate_pr.py --base origin/main")
    return 0


if __name__ == "__main__":
    sys.exit(main())
