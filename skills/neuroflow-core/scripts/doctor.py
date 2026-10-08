#!/usr/bin/env python3
"""neuroflow doctor — is this machine and project set up so neuroflow's work is safe and durable?

Checks the environment around a neuroflow project (not the project memory's internal consistency,
which is `nf_check.py` / `/sentinel`):

- Python and git are available; Claude Code's version against the mod's tested floor
- the project is a git repository with a remote; how many commits are not pushed; how old the last
  commit is; uncommitted changes under .neuroflow/ (durability: work that exists on one disk only)
- the project does not live on a network share or inside a cloud-synced folder
- project_config.md uses the current contract (frontmatter + nf_schema) — else /neuroflow:migrate
- .gitignore keeps the local-only paths out of git; .gitattributes merges append-only logs
- the person's flowie, when it is set up: commits in ~/.neuroflow/flowie not pushed to its upstream,
  uncommitted changes there (a count and up to three paths, never file contents), and auto-sync failures
  waiting in ~/.neuroflow/flowie-sync.log — /neuroflow:flowie --sync resolves all three

Usage:
    python doctor.py [--project PATH] [--json]

Exit codes: 0 = all good, 1 = warnings or failures found, 2 = usage or runtime error.
Standard library only.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


def _load_nf_check():
    """nf_check.py is the one home of the frontmatter reader and the known nf_schema (contract C10)."""
    spec = importlib.util.spec_from_file_location("nf_check_for_doctor", Path(__file__).with_name("nf_check.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # its dataclasses look the module up while they are built
    spec.loader.exec_module(module)
    return module


nfc = _load_nf_check()

VERSION_FLOOR = (2, 1, 292)
KNOWN_SCHEMA = nfc.SUPPORTED_NF_SCHEMA
LOCAL_ONLY = [".neuroflow/sessions/", ".neuroflow/review/", ".neuroflow/integrations.json", ".neuroflow/flowie/", ".neuroflow/paper/xray-*", ".neuroflow/wiki/.pending/"]
# One file under each local-only line, as git would see it there (git check-ignore answers for these).
PROBES = {
    ".neuroflow/sessions/": ".neuroflow/sessions/nf-probe.md",
    ".neuroflow/review/": ".neuroflow/review/nf-probe.md",
    ".neuroflow/integrations.json": ".neuroflow/integrations.json",
    ".neuroflow/flowie/": ".neuroflow/flowie/nf-probe.md",  # the legacy project-level folder the gitignore keeps out
    ".neuroflow/paper/xray-*": ".neuroflow/paper/xray-nf-probe.jsonl",
    ".neuroflow/wiki/.pending/": ".neuroflow/wiki/.pending/nf-probe.md",
}
# Without git: a .gitignore line that ignores the whole project memory covers every local-only path in it.
WHOLE_MEMORY = {".neuroflow", ".neuroflow/", ".neuroflow/*", ".neuroflow/**"}
UNION_FILES = [".neuroflow/reasoning/*.jsonl", ".neuroflow/sessions/*.md"]
SYNCED_MARKERS = ("onedrive", "dropbox", "icloud", "google drive", "googledrive", "my drive", "box sync", "nextcloud", "owncloud")
# A flowie-sync.log line for a sync that went through (`{time} synced: {paths} (mod)`): the log's one non-failure line.
SYNCED = re.compile(r"^\S+\s+synced:")


def check(checks: list[dict], cid: str, status: str, message: str) -> None:
    checks.append({"id": cid, "status": status, "message": message})


def run(argv: list[str], cwd: Path | None = None, timeout: int = 15) -> tuple[int, str]:
    try:
        done = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, str(exc)
    return done.returncode, (done.stdout or "") + (done.stderr or "")


def parse_version(text: str) -> tuple[int, ...] | None:
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", text)
    return tuple(int(part) for part in match.groups()) if match else None


def check_tools(checks: list[dict]) -> None:
    version = sys.version_info
    status = "ok" if version >= (3, 10) else "warn"
    check(checks, "python", status, f"Python {version.major}.{version.minor}.{version.micro}" + ("" if status == "ok" else " — neuroflow's scripts need 3.10+"))
    if shutil.which("git") is None:
        check(checks, "git", "warn", "git not found — project memory has no history and no backup")
    else:
        check(checks, "git", "ok", "git available")
    claude = shutil.which("claude")
    if claude is None:
        check(checks, "claude", "info", "the claude command is not on PATH (fine inside the desktop app)")
        return
    code, out = run([claude, "--version"])
    found = parse_version(out) if code == 0 else None
    if found is None:
        check(checks, "claude", "info", "could not read the Claude Code version")
    elif found >= VERSION_FLOOR:
        check(checks, "claude", "ok", f"Claude Code {'.'.join(map(str, found))}")
    else:
        floor = ".".join(map(str, VERSION_FLOOR))
        check(checks, "claude", "warn", f"Claude Code {'.'.join(map(str, found))} is older than {floor}, the version the neuroflow mod was tested on")


def check_git(checks: list[dict], project: Path, now: float) -> None:
    if shutil.which("git") is None:
        return
    code, out = run(["git", "rev-parse", "--show-toplevel"], cwd=project)
    if code != 0:
        check(checks, "repo", "warn", "the project is not a git repository — .neuroflow/ exists on this disk only")
        return
    code, out = run(["git", "remote"], cwd=project)
    if code == 0 and out.strip() == "":
        check(checks, "remote", "warn", "no git remote — nothing is backed up off this machine")
    code, out = run(["git", "rev-list", "--count", "@{u}..HEAD"], cwd=project)
    if code == 0 and out.strip().isdigit():
        ahead = int(out.strip())
        check(checks, "unpushed", "warn" if ahead > 0 else "ok", f"{ahead} commit(s) not pushed" if ahead > 0 else "everything committed is pushed")
    code, out = run(["git", "log", "-1", "--format=%ct"], cwd=project)
    if code == 0 and out.strip().isdigit():
        days = int((now - int(out.strip())) // 86400)
        check(checks, "last-commit", "warn" if days > 14 else "ok", f"last commit {days} day(s) ago")
    code, out = run(["git", "status", "--porcelain", "--", ".neuroflow"], cwd=project)
    if code == 0:
        changed = [line for line in out.splitlines() if line.strip()]
        if changed:
            check(checks, "uncommitted", "info", f"{len(changed)} uncommitted change(s) under .neuroflow/")


def check_location(checks: list[dict], project: Path) -> None:
    text = str(project)
    if text.startswith("\\\\") or text.startswith("//"):
        check(checks, "location", "warn", "the project is on a network share — file locks and change detection are unreliable; work on a local copy")
        return
    lowered = text.replace("\\", "/").lower()
    marker = next((m for m in SYNCED_MARKERS if m in lowered), None)
    if marker is not None:
        check(checks, "location", "warn", f"the project is inside a cloud-synced folder ({marker}) — sync can corrupt or duplicate files mid-write; prefer git for sharing")
    else:
        check(checks, "location", "ok", "the project is on a local disk")


def check_config(checks: list[dict], project: Path) -> None:
    config = project / ".neuroflow" / "project_config.md"
    if not config.exists():
        check(checks, "config", "info", "no .neuroflow/project_config.md — run /neuroflow to set the project up")
        return
    frontmatter, _, _ = nfc.split_frontmatter(config.read_text(encoding="utf-8", errors="replace"))
    if frontmatter is None:
        check(checks, "config", "warn", "project_config.md uses a legacy format — run /neuroflow:migrate")
        return
    schema = str(frontmatter.get("nf_schema") or "").strip()
    if not schema.isdigit():
        check(checks, "config", "warn", "project_config.md has no nf_schema — run /neuroflow:migrate")
    elif int(schema) > KNOWN_SCHEMA:
        check(checks, "config", "warn", f"project_config.md has nf_schema {schema}, newer than this plugin knows ({KNOWN_SCHEMA}) — update neuroflow")
    else:
        check(checks, "config", "ok", f"project_config.md uses the current contract (nf_schema {schema})")
    # The version notice (neuroflow-core -> Command lifecycle, step 3): plugin_version is raised only by /migrate.
    running = nfc.plugin_version(nfc.PLUGIN_ROOT)
    recorded = str(frontmatter.get("plugin_version") or "").strip()
    behind = nfc._vtuple(running) is not None and (nfc._vtuple(recorded) is None or nfc._vtuple(recorded) < nfc._vtuple(running))
    if behind:
        check(checks, "version", "warn", f"neuroflow {running} is installed; this project is on {recorded or 'an older version'} — "
              "run /neuroflow:migrate to bring the project, your flowie and the team hive up to date")


def git_ignored(project: Path, paths: list[str]) -> set[str] | None:
    """The paths git ignores in this project (`git check-ignore --no-index`); None when git cannot answer here."""
    if shutil.which("git") is None:
        return None
    try:
        proc = subprocess.run(["git", "-C", str(project), "check-ignore", "--no-index", "--stdin"],
                              input=("\n".join(paths) + "\n").encode("utf-8"), capture_output=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode not in (0, 1):
        return None  # not a git repository, or git failed
    return {line.strip() for line in proc.stdout.decode("utf-8", "replace").splitlines() if line.strip()}


def uncovered_local_only(project: Path, gitignore: str) -> list[str]:
    """The local-only lines the project's ignore rules leave uncovered: git decides when it can (anchored lines,
    `**`, negations, a folder above), else the .gitignore is read line by line."""
    ignored = git_ignored(project, list(PROBES.values()))
    if ignored is not None:
        return [line for line, probe in PROBES.items() if probe not in ignored]
    rules = [line.strip() for line in gitignore.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    plain = {rule.lstrip("/") for rule in rules if not rule.startswith("!")}
    brought_back = any(rule.lstrip("!/").startswith(".neuroflow") for rule in rules if rule.startswith("!"))
    if plain & WHOLE_MEMORY and not brought_back:
        return []
    return [line for line in LOCAL_ONLY if line not in plain and line.rstrip("/") not in plain
            and not any(rule.rstrip("*") == line for rule in plain if rule.endswith("/*") or rule.endswith("/**"))]


def check_git_files(checks: list[dict], project: Path) -> None:
    ignore = project / ".gitignore"
    ignored = ignore.read_text(encoding="utf-8", errors="replace") if ignore.exists() else ""
    missing = uncovered_local_only(project, ignored)
    if missing:
        check(checks, "gitignore", "warn", f".gitignore does not exclude {', '.join(missing)} — local-only files could be committed (/neuroflow:migrate adds them)")
    else:
        check(checks, "gitignore", "ok", ".gitignore keeps local-only files out of git")
    attributes = project / ".gitattributes"
    attrs = attributes.read_text(encoding="utf-8", errors="replace") if attributes.exists() else ""
    if all(f"{pattern} merge=union" in attrs for pattern in UNION_FILES):
        check(checks, "gitattributes", "ok", "append-only logs merge without conflicts (merge=union)")
    else:
        check(checks, "gitattributes", "info", "append-only logs are not set to merge=union — two people's log lines may conflict (/neuroflow:migrate adds it)")


def flowie_uncommitted(flowie: Path) -> list[str] | None:
    """One path per change `git status` lists in the flowie (paths only, never contents), integrations.json aside:
    it stays on this machine and is never committed. None when git cannot answer."""
    try:
        proc = subprocess.run(["git", "-C", str(flowie), "--no-optional-locks", "status", "--porcelain", "-z",
                               "--untracked-files=all"], capture_output=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    fields = proc.stdout.decode("utf-8", "replace").split("\0")
    paths: list[str] = []
    i = 0
    while i < len(fields):
        entry, i = fields[i], i + 1
        if len(entry) < 4:
            continue
        if "R" in entry[:2] or "C" in entry[:2]:
            i += 1  # the source path of a rename or copy follows
        if entry[3:] != "integrations.json":
            paths.append(entry[3:])
    return paths


def check_flowie(checks: list[dict], home: Path | None) -> None:
    """The person's flowie (optional): commits not pushed, uncommitted changes, and auto-sync failures waiting in the log.

    Says nothing when flowie is not set up. The unpushed count needs a git repository with an upstream
    and compares with the last fetched state of it (no network). Uncommitted changes are not backed up, and a pull
    with rebase refuses to run over them, so every pull of the flowie (and /neuroflow:migrate) passes it by."""
    if home is None:
        return
    flowie = home / ".neuroflow" / "flowie"
    if not flowie.is_dir():
        return
    if shutil.which("git") is not None and (flowie / ".git").exists():
        code, out = run(["git", "rev-list", "--count", "@{u}..HEAD"], cwd=flowie)
        if code == 0 and out.strip().isdigit():
            ahead = int(out.strip())
            if ahead > 0:
                check(checks, "flowie-unpushed", "warn", f"{ahead} flowie commit(s) not pushed to your private repo — run /neuroflow:flowie --sync")
            else:
                check(checks, "flowie-unpushed", "ok", "flowie: everything committed is pushed")
        changed = flowie_uncommitted(flowie)
        if changed:
            shown = ", ".join(changed[:3]) + (f" and {len(changed) - 3} more" if len(changed) > 3 else "")
            check(checks, "flowie-uncommitted", "warn", f"{len(changed)} uncommitted change(s) in your flowie ({shown}) — run /neuroflow:flowie --sync")
    log = home / ".neuroflow" / "flowie-sync.log"
    try:
        lines = [line.strip() for line in log.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]
    except OSError:
        return  # no log: nothing failed (or nothing to read)
    # The neuroflow mod logs each of its own sync attempts; a `synced` line is no failure.
    failures = [line for line in lines if not SYNCED.match(line)]
    if failures:
        first = failures[0].split()[0]
        since = f" since {first}" if re.match(r"\d{4}-\d{2}-\d{2}", first) else ""
        check(checks, "flowie-sync-log", "warn", f"{len(failures)} flowie auto-sync failure(s){since} in ~/.neuroflow/flowie-sync.log — run /neuroflow:flowie --sync to resolve")


def utf8_stdio() -> None:
    """Make stdout and stderr UTF-8, so a path in any script survives a Windows pipe."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", default=".", help="project root (the folder holding .neuroflow/)")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    parser.add_argument("--home", help=argparse.SUPPRESS)  # tests only: stands in for the home directory
    args = parser.parse_args(argv)
    project = Path(args.project).resolve()
    if not project.is_dir():
        print(f"not a folder: {project}", file=sys.stderr)
        return 2
    try:
        home: Path | None = Path(args.home) if args.home else Path.home()
    except RuntimeError:  # no home directory can be determined: the flowie checks are skipped
        home = None
    checks: list[dict] = []
    now = time.time()
    check_tools(checks)
    check_location(checks, project)
    check_config(checks, project)
    check_git(checks, project, now)
    check_git_files(checks, project)
    check_flowie(checks, home)
    if args.json:
        print(json.dumps({"project": str(project), "checks": checks}, indent=1))
    else:
        glyph = {"ok": "✔", "info": "·", "warn": "⚠", "fail": "✖"}
        for item in checks:
            print(f"{glyph[item['status']]} {item['message']}")
    return 1 if any(item["status"] in ("warn", "fail") for item in checks) else 0


if __name__ == "__main__":
    sys.exit(main())
