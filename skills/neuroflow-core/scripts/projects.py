#!/usr/bin/env python3
"""One research project across the flowie, the team hives and its repositories (neuroflow-core → Project registry).

A project has one card: a team project's in the hive its team works in, a personal project's in the flowie. The other
level holds at most a pointer ({"id": …, "ref": "hive:{org}/{repo}"}) with personal notes, never a copy of the card's
fields. Tasks stay on three boards (project repo, flowie, hive: /tasks → Levels); this script reads them together.

subcommands:
  list                       every card and pointer, where it lives
  check                      two cards for one project, pointers that lead nowhere or carry copies, a local path in
                             a card's repos, blocked_by entries that name no task at their level, open tasks whose
                             project: names no registered project
  view --project ID          the project's open tasks at every level: the flowie, each hive, this repository's board
                             and the boards of the card's other repositories — read from a machine-local cache
                             (~/.neuroflow/boards/) that is refreshed from their remotes first (--no-remote: cache only)
  refresh --project ID       refresh that cache only (--root: this repository, which needs no cache)
  fold [--project ID ...] [--hive NAME ...] [--no-hive] [--keep ID.FIELD=flowie|hive|both ...] [--apply]
                             two cards of one project (one in the flowie, one in a hive) become the hive card and a
                             flowie pointer. A field that differs: a list (repos, visited_phases) keeps both by
                             default, a value keeps the hive's unless only the flowie has one. --hive limits the
                             hives that may be written (by folder name), --no-hive skips every project whose hive card
                             would change. Writes files only with --apply; stages nothing, never commits or pushes.
  add --json for a machine-readable result; --home DIR stands in for the home folder (tests)

The cache in ~/.neuroflow/boards/ holds shallow, sparse clones with only .neuroflow/tasks/; git runs there with hooks
off, no credential prompt and ssh in batch mode. Nothing outside that folder is ever deleted or checked out.

exit codes: 0 clean (check), nothing to do (fold) or done · 1 findings (check), planned or applied changes (fold),
a repository that could not be read (view/refresh) · 2 usage or runtime error
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CARD_FIELDS = ("description", "repos", "current_phase", "visited_phases", "status")
LIST_FIELDS = ("repos", "visited_phases")
CLOSED = {"done", "archive", "archived"}
NO_PROJECT = {"", "-", "—", "none", "personal", "null", "~"}
DEFAULT_COLUMNS = ["inbox", "ready", "active", "review", "meeting", "done", "archive"]
CARD_SECTIONS = {"repos", "phase timeline", "linked repos"}  # a card's fields, written out in a flowie note
BOARD_MARK = ".neuroflow-board"  # written into every cache folder this script creates: only those are ever replaced
SAFE_PART = re.compile(r"^[a-z0-9](?:[a-z0-9._-]*[a-z0-9_-])?$")


class UsageError(Exception):
    pass


def utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


# ── reading ─────────────────────────────────────────────────────────────────────────────────────

def read_text(path: Path) -> str | None:
    try:
        return path.read_bytes().decode("utf-8-sig", errors="replace")
    except OSError:
        return None


def read_json(path: Path):
    text = read_text(path)
    if text is None:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def entry_id(entry: dict) -> str:
    value = entry.get("id") or entry.get("name") or ""
    return str(value).strip()


def registry_entries(path: Path) -> tuple[list[dict], bool]:
    """A projects.json's entries, as both shapes are written ({"projects": [...]} or a bare list); False if unreadable."""
    if not path.exists():
        return [], True
    data = read_json(path)
    if isinstance(data, dict):
        data = data.get("projects")
        data = [] if data is None else data
    if not isinstance(data, list):
        return [], False
    return [entry for entry in data if isinstance(entry, dict) and entry_id(entry)], True


def _scalar(value: str):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        return [_scalar(item) for item in value[1:-1].split(",") if item.strip()]
    return value


def frontmatter(text: str) -> dict:
    """The keys of a task file's frontmatter this script needs: scalars, inline lists and block lists."""
    lines = text.replace("\r\n", "\n").split("\n")
    if not lines or lines[0].strip() != "---":
        return {}
    out: dict = {}
    key = None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = re.match(r"^([A-Za-z_][\w-]*):\s*(.*?)\s*(?:#.*)?$", line)
        if match:
            key, value = match.group(1), match.group(2)
            out[key] = _scalar(value) if value != "" else []
            continue
        item = re.match(r"^\s+-\s+(.*?)\s*$", line)
        if item and key is not None:
            current = out.get(key)
            out[key] = (current if isinstance(current, list) else []) + [_scalar(item.group(1))]
    return out


def as_list(value) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def parse_repo(url: str) -> tuple[str, str] | None:
    """(`host/owner/repo` in lower case, the URL to clone) for an https, http, ssh or scp-style git URL or a bare
    host/owner/repo; None for anything else — a local folder, a file:// URL, an option, or a path that is not exactly
    host, owner and repository of safe characters (no `..`, nothing that could leave the cache folder)."""
    url = str(url).strip()
    if not url or url.startswith("-") or any(char.isspace() for char in url):
        return None
    match = re.match(r"^(https?|ssh|git)://(?:[^@/]+@)?([^/:]+)(?::\d+)?/(.+)$", url, re.I)
    scp = None if match else re.match(r"^[^@/:]+@([^:/]+):(.+)$", url)
    bare = None if match or scp else re.match(r"^([^/:]+\.[^/:]+)/(.+)$", url)
    if match:
        host, path = match.group(2), match.group(3)
    elif scp:
        host, path = scp.group(1), scp.group(2)
    elif bare:
        host, path = bare.group(1), bare.group(2)
    else:
        return None
    path = re.sub(r"\.git$", "", path.strip("/"), flags=re.I)
    parts = [host.lower(), *[part.lower() for part in path.split("/")]]
    if len(parts) != 3 or "." not in parts[0] or any(part in (".", "..") or not SAFE_PART.match(part) for part in parts):
        return None
    return "/".join(parts), (url if match or scp else f"https://{host}/{path}")


def repo_key(url: str) -> str | None:
    parsed = parse_repo(url)
    return parsed[0] if parsed else None


def origin_url(repo: Path) -> str | None:
    """The `origin` URL in a clone's git config (a worktree's .git file is followed)."""
    git_dir = repo / ".git"
    if git_dir.is_file():
        match = re.search(r"gitdir:\s*(.+)", read_text(git_dir) or "")
        if not match:
            return None
        gitdir = Path(match.group(1).strip())
        gitdir = gitdir if gitdir.is_absolute() else repo / gitdir
        common = read_text(gitdir / "commondir")
        git_dir = (gitdir / common.strip()).resolve() if common else gitdir
    config = read_text(git_dir / "config") or ""
    section = re.search(r'\[remote "origin"\]([^\[]*)', config)
    url = re.search(r"^\s*url\s*=\s*(.+?)\s*$", section.group(1), re.M) if section else None
    return url.group(1) if url else None


# ── the registry ────────────────────────────────────────────────────────────────────────────────

class Level:
    """The flowie or one hive clone: its registry and its task board."""

    def __init__(self, kind: str, root: Path, name: str, repo: str | None) -> None:
        self.kind, self.root, self.name, self.repo = kind, root, name, repo  # repo: org/repo of a hive
        self.is_clone = (root / ".git" / "HEAD").is_file() or (root / ".git").is_file()
        self.entries, self.registry_ok = registry_entries(root / "projects" / "projects.json")

    @property
    def label(self) -> str:
        return "flowie" if self.kind == "flowie" else f"hive {self.repo or self.name}"

    def entry(self, project_id: str) -> dict | None:
        return next((entry for entry in self.entries if entry_id(entry) == project_id), None)


def is_pointer(entry: dict) -> bool:
    return isinstance(entry.get("ref"), str) and entry["ref"].startswith("hive:")


def hive_levels(home: Path) -> list[Level]:
    hives = home / ".neuroflow" / "hives"
    levels = []
    for folder in sorted(hives.iterdir() if hives.is_dir() else [], key=lambda p: p.name.lower()):
        if not folder.is_dir():
            continue
        key = repo_key(origin_url(folder) or "")
        levels.append(Level("hive", folder, folder.name, "/".join(key.split("/")[1:]) if key else None))
    return levels


def all_levels(home: Path) -> list[Level]:
    flowie = home / ".neuroflow" / "flowie"
    levels = [Level("flowie", flowie, "flowie", None)] if flowie.is_dir() else []
    return levels + hive_levels(home)


def hive_for_ref(levels: list[Level], ref: str) -> Level | None:
    """The hive a pointer names (`hive:{org}/{repo}`): by its clone's origin, else a folder named {org}-{repo} or {repo}."""
    target = ref[len("hive:"):].strip().strip("/").lower()
    hives = [level for level in levels if level.kind == "hive"]
    for level in hives:
        if level.repo and level.repo.lower() == target:
            return level
    names = {target.replace("/", "-"), target.split("/")[-1]}
    return next((level for level in hives if level.name.lower() in names), None)


def find_card(levels: list[Level], project_id: str) -> tuple[Level | None, dict | None, list[str]]:
    """The project's card: in a hive, or in the flowie; followed through a flowie pointer. Problems found on the way."""
    problems = []
    cards = [(level, level.entry(project_id)) for level in levels]
    cards = [(level, entry) for level, entry in cards if entry is not None and not is_pointer(entry)]
    if len(cards) > 1:
        problems.append(f"{project_id} has {len(cards)} cards ({', '.join(level.label for level, _ in cards)})")
    hive_cards = [pair for pair in cards if pair[0].kind == "hive"]
    if hive_cards:
        return hive_cards[0][0], hive_cards[0][1], problems
    if cards:
        return cards[0][0], cards[0][1], problems
    flowie = next((level for level in levels if level.kind == "flowie"), None)
    pointer = flowie.entry(project_id) if flowie else None
    if pointer is not None and is_pointer(pointer):
        hive = hive_for_ref(levels, pointer["ref"])
        if hive is None:
            problems.append(f"{project_id} points at {pointer['ref']}, which is not cloned here (/hive --init)")
        else:
            card = hive.entry(project_id)
            if card is not None and not is_pointer(card):
                return hive, card, problems
            problems.append(f"{project_id} points at {pointer['ref']}, which has no card for it")
    return None, None, problems


def repo_values(entry: dict) -> list[str]:
    values = []
    for repo in as_items(entry.get("repos")):
        value = repo.get("url") if isinstance(repo, dict) else repo
        if isinstance(value, str) and value.strip():
            values.append(value.strip())
    return values


def is_remote(value: str) -> bool:
    """A remote a repository can be cloned from: a URL with a scheme other than file://, an scp-style address
    (user@host:path), or a bare host.domain/owner/repo."""
    value = value.strip()
    if re.match(r"^[a-z][a-z0-9+.-]*://", value, re.I):
        return not value.lower().startswith("file:")
    return bool(re.match(r"^[^@/\\:\s]+@[^:/\s]+:\S", value)) or parse_repo(value) is not None


def is_local_path(value: str) -> bool:
    """Anything in `repos` that is no remote: a folder on some machine (C:\\…, /…, ~/…, $HOME/…, ../…, a relative
    path, file://…). neuroflow-core: repos holds remote URLs only."""
    return value.strip() != "" and not is_remote(value)


def card_repos(card: dict) -> list[str]:
    return [url for url in repo_values(card) if parse_repo(url)]


# ── tasks ───────────────────────────────────────────────────────────────────────────────────────

def read_board(tasks: Path) -> list[dict]:
    """Every task file of a board: one per `{column}/{slug}.md`; a legacy flat file counts in its `status` column."""
    out: list[dict] = []
    if not tasks.is_dir():
        return out
    for path in sorted(tasks.rglob("*.md")):
        rel = path.relative_to(tasks)
        if path.name.lower() in ("readme.md", "index.md", "flow.md") or len(rel.parts) > 2:
            continue
        fm = frontmatter(read_text(path) or "")
        if not fm:
            continue
        column = rel.parts[0] if len(rel.parts) == 2 else str(fm.get("status") or "inbox")
        slug = path.stem if len(rel.parts) == 2 else re.sub(r"^[A-Za-z]*-?\d+-", "", path.stem)
        out.append({
            "slug": slug,
            "file": rel.as_posix(),
            "column": column,
            "title": str(fm.get("title") or slug),
            "owner": (as_list(fm.get("owner")) or as_list(fm.get("assignee")) or as_list(fm.get("responsible")) or [None])[0],
            "due": str(fm.get("due")) if fm.get("due") not in (None, [], "") else None,
            "project": str(fm.get("project")).strip() if fm.get("project") not in (None, []) else None,
            "blocked_by": as_list(fm.get("blocked_by")),
            "open": column.lower() not in CLOSED,
        })
    return out


def safe_board(tasks: Path) -> tuple[list[dict], str | None]:
    try:
        return read_board(tasks), None
    except OSError as error:
        return [], f"could not read the board: {error.strerror or error}"


# ── machine-local cache of the boards of repositories not checked out here ─────────────────────

def remove_tree(path: Path) -> None:
    """Deletes a cache folder, git's read-only object files included (Windows refuses those otherwise)."""
    def retry(func, name, _info) -> None:
        os.chmod(name, stat.S_IWRITE)
        func(name)
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=retry)
    else:
        shutil.rmtree(path, onerror=retry)


def boards_root(home: Path) -> Path:
    return home / ".neuroflow" / "boards"


def git(args: list[str], cwd: Path | None, home: Path, timeout: int = 60) -> subprocess.CompletedProcess:
    """git for the cache: hooks off (an empty hooks folder), no credential prompt, ssh in batch mode, no stdin."""
    no_hooks = boards_root(home) / ".nohooks"
    no_hooks.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
    if not (os.environ.get("GIT_SSH_COMMAND") or os.environ.get("GIT_SSH") or own_ssh(home)):
        env["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes"  # no passphrase or host-key question can hold it
    try:
        return subprocess.run(["git", "-c", f"core.hooksPath={no_hooks.as_posix()}", "-c", "core.symlinks=false", *args], cwd=cwd,
                              capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
                              stdin=subprocess.DEVNULL, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as error:
        return subprocess.CompletedProcess(args, 1, "", str(error))


_OWN_SSH: dict[str, bool] = {}


def own_ssh(home: Path) -> bool:
    """Whether git is set up with the person's own ssh command (core.sshCommand): then it is used as it is."""
    key = str(home)
    if key not in _OWN_SSH:
        try:
            proc = subprocess.run(["git", "config", "--global", "--get", "core.sshCommand"], capture_output=True,
                                  text=True, stdin=subprocess.DEVNULL, timeout=10, cwd=str(home) if home.is_dir() else None)
            _OWN_SSH[key] = proc.returncode == 0 and proc.stdout.strip() != ""
        except (OSError, subprocess.TimeoutExpired):
            _OWN_SSH[key] = False
    return _OWN_SSH[key]


def cache_dir(home: Path, key: str) -> Path:
    """The cache folder of `host/owner/repo` — always inside ~/.neuroflow/boards/, or an error."""
    root = boards_root(home).resolve()
    parts = key.split("/")
    if len(parts) != 3 or any(part in (".", "..") or not SAFE_PART.match(part) for part in parts):
        raise UsageError(f"not a repository key: {key!r}")
    target = root.joinpath(*parts)
    if root not in target.resolve().parents:
        raise UsageError(f"{key!r} leads outside {root}")
    return target


def refresh_cache(home: Path, url: str, key: str) -> tuple[bool, str]:
    """A shallow, sparse clone that holds only the repository's `.neuroflow/tasks/`: cloned once, refreshed after.
    Only a folder this script created (it holds BOARD_MARK) is ever replaced; anything else in the way is left alone."""
    if shutil.which("git") is None:
        return False, "git is not installed"
    target = cache_dir(home, key)
    if target.exists() and not (target / BOARD_MARK).is_file():
        return False, f"{target} is not a board cache this script made; left alone"
    if (target / BOARD_MARK).is_file() and not (target / ".git").is_dir():
        remove_tree(target)  # a cache of ours that broke: clone it again
    fresh = not target.exists()
    if fresh:
        # Cloned beside the target and moved into place once marked, so a clone cut off half-way (a killed process)
        # leaves only a `.neuroflow-partial` folder, which the next refresh removes: that name is this script's own.
        partial = target.with_name(target.name + ".neuroflow-partial")
        if partial.exists():
            remove_tree(partial)
        target.parent.mkdir(parents=True, exist_ok=True)
        proc = git(["clone", "--depth", "1", "--filter=blob:none", "--no-checkout", "--quiet", "--", url, str(partial)], None, home)
        if proc.returncode != 0:
            if partial.exists():
                remove_tree(partial)
            return False, first_line(proc)
        (partial / BOARD_MARK).write_text("a cache of this repository's .neuroflow/tasks/ (projects.py)\n", encoding="utf-8")
        partial.rename(target)
    steps = [["sparse-checkout", "set", "--no-cone", "/.neuroflow/tasks/"]]
    steps += [["checkout", "--quiet"]] if fresh else [["fetch", "--depth", "1", "--quiet", "origin", "HEAD"],
                                                      ["checkout", "--quiet", "--force", "FETCH_HEAD"]]
    for args in steps:
        proc = git(args, target, home)
        if proc.returncode != 0:
            return False, first_line(proc)
    (target / ".neuroflow-fetched").write_text(datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") + "\n",
                                               encoding="utf-8")
    return True, ""


def first_line(proc: subprocess.CompletedProcess) -> str:
    lines = [line.strip() for line in (proc.stderr + "\n" + proc.stdout).splitlines() if line.strip()]
    reason = next((line for line in lines if re.match(r"^(fatal|error):", line, re.I)), lines[0] if lines else "git failed")
    return reason[:200]


def local_projects(home: Path) -> list[dict]:
    entries, _ = registry_entries(home / ".neuroflow" / "local-projects.json")
    return entries


def find_root(start: Path) -> Path | None:
    for folder in [start, *start.parents]:
        if (folder / ".neuroflow" / "project_config.md").is_file():
            return folder
    return None


def linked_id(home: Path, levels: list[Level], root: Path) -> str | None:
    """The project this repository is: its local-projects.json entry, else a card or pointer listing its origin."""
    for entry in local_projects(home):
        path = str(entry.get("path") or "")
        try:
            if path and Path(path).expanduser().resolve() == root.resolve():
                return entry_id(entry) or None
        except OSError:
            continue
    key = repo_key(origin_url(root) or "")
    for level in levels:
        for entry in level.entries:
            if key and any(repo_key(url) == key for url in repo_values(entry)):
                return entry_id(entry)
    return None


def cached_level(home: Path, key: str) -> dict:
    entry: dict = {"level": "project", "name": key, "source": "remote", "tasks": []}
    cached = cache_dir(home, key)
    stamp = read_text(cached / ".neuroflow-fetched")
    entry["fetched"] = stamp.strip() if stamp else None
    if (cached / ".git").exists():
        entry["tasks"], error = safe_board(cached / ".neuroflow" / "tasks")
        if error:
            entry["error"] = error
    return entry


def remote_repos(home: Path, card: dict | None, here: Path | None) -> list[tuple[str, str, Path | None]]:
    """The card's repositories other than this one: (key, clone URL, the local copy when it is checked out here)."""
    seen = {repo_key(origin_url(here) or "")} if here is not None else set()
    checked_out = {}
    for entry in local_projects(home):
        key = repo_key(str(entry.get("remote") or ""))
        if key and entry.get("path"):
            checked_out[key] = Path(str(entry["path"])).expanduser()
    out = []
    for value in repo_values(card or {}):
        parsed = parse_repo(value)
        if parsed is None or parsed[0] in seen:
            continue
        seen.add(parsed[0])
        out.append((parsed[0], parsed[1], checked_out.get(parsed[0])))
    return out


def view(home: Path, project_id: str, root: Path | None, remote: bool) -> dict:
    levels = all_levels(home)
    where, card, problems = find_card(levels, project_id)
    result: dict = {"project": project_id, "card": None, "problems": problems, "levels": []}
    if card is not None:
        result["card"] = {"where": where.label, **{field: card.get(field) for field in CARD_FIELDS if field in card}}
    for level in levels:
        tasks, error = safe_board(level.root / "tasks")
        tasks = [task for task in tasks if task["project"] == project_id]
        if tasks or error or level.kind == "flowie" or level is where:
            result["levels"].append({"level": level.kind, "name": level.label, "source": "local", "tasks": tasks,
                                     **({"error": error} if error else {})})
    here = find_root(root) if root is not None else None
    if here is not None and linked_id(home, levels, here) == project_id:
        tasks, error = safe_board(here / ".neuroflow" / "tasks")
        result["levels"].append({"level": "project", "name": "this repository", "source": "local", "tasks": tasks,
                                 **({"error": error} if error else {})})
    for key, url, local in remote_repos(home, card, here):
        if local is not None and (local / ".neuroflow").is_dir():
            tasks, error = safe_board(local / ".neuroflow" / "tasks")
            result["levels"].append({"level": "project", "name": key, "source": f"local copy ({local.as_posix()})",
                                     "tasks": tasks, **({"error": error} if error else {})})
            continue
        reason = refresh_cache(home, url, key)[1] if remote else ""
        entry = cached_level(home, key)
        if reason:
            entry["error"] = reason
        elif "error" not in entry and not (cache_dir(home, key) / ".git").exists():
            entry["error"] = "not fetched yet (run without --no-remote)"
        result["levels"].append(entry)
    return result


def refresh(home: Path, project_id: str, root: Path | None) -> dict:
    levels = all_levels(home)
    _, card, problems = find_card(levels, project_id)
    here = find_root(root) if root is not None else None
    out = {"project": project_id, "problems": problems, "repos": []}
    for key, url, local in remote_repos(home, card, here):
        if local is not None and (local / ".neuroflow").is_dir():
            continue
        ok, reason = refresh_cache(home, url, key)
        out["repos"].append({"repo": key, "ok": ok, **({"error": reason} if not ok else {})})
    return out


# ── checks ──────────────────────────────────────────────────────────────────────────────────────

def check(home: Path) -> list[dict]:
    levels = all_levels(home)
    findings: list[dict] = []
    for level in levels:
        if not level.registry_ok:
            findings.append({"kind": "registry", "where": level.label, "message": f"projects/projects.json in the {level.label} is not a list of projects (not valid JSON?)"})
    ids = {entry_id(entry) for level in levels for entry in level.entries}
    for project_id in sorted(ids):
        cards = [(level, level.entry(project_id)) for level in levels]
        cards = [(level, entry) for level, entry in cards if entry is not None]
        full = [(level, entry) for level, entry in cards if not is_pointer(entry)]
        if len(full) > 1:
            differ = [field for field in CARD_FIELDS
                      if len({json.dumps(entry.get(field), sort_keys=True) for _, entry in full}) > 1]
            findings.append({"kind": "two-cards", "project": project_id, "where": [level.label for level, _ in full],
                             "differ": differ,
                             "message": f"{project_id} has {len(full)} cards ({', '.join(level.label for level, _ in full)})"
                                        + (f"; they differ in {', '.join(differ)}" if differ else "")
                                        + (" — /neuroflow:migrate folds them into one card and a pointer" if len(full) == 2 and full[0][0].kind == "flowie"
                                           else " — keep one: a project has one card")})
        for level, entry in full:
            local = [value for value in repo_values(entry) if is_local_path(value)]
            if local:
                findings.append({"kind": "local-repo", "project": project_id, "where": level.label,
                                 "message": f"the card of {project_id} in the {level.label} lists a local folder in repos ({local[0]}); "
                                            "repos holds remote URLs, a folder belongs in ~/.neuroflow/local-projects.json"})
        for level, entry in cards:
            if not is_pointer(entry):
                continue
            copies = [field for field in CARD_FIELDS if field in entry]
            if copies:
                findings.append({"kind": "pointer-copies", "project": project_id, "where": level.label,
                                 "message": f"the pointer for {project_id} in the {level.label} copies {', '.join(copies)} "
                                            "from the card; those fields live only on the card"})
            hive = hive_for_ref(levels, entry["ref"])
            card = hive.entry(project_id) if hive else None
            if hive is None:
                findings.append({"kind": "pointer-target", "project": project_id, "where": level.label,
                                 "message": f"{project_id} points at {entry['ref']}, which is not cloned here (/hive --init)"})
            elif card is None or is_pointer(card):
                findings.append({"kind": "pointer-target", "project": project_id, "where": level.label,
                                 "message": f"{project_id} points at {entry['ref']}, which has no card for it"})
    # A task's project: is the card's id at every level (/tasks): a flowie task may name a team card with no pointer.
    known = {entry_id(entry) for level in levels for entry in level.entries}
    for level in levels:
        tasks, error = safe_board(level.root / "tasks")
        if error:
            findings.append({"kind": "board", "where": level.label, "message": f"the {level.label} board: {error}"})
        slugs = {task["slug"] for task in tasks}
        for task in tasks:
            for slug in task["blocked_by"]:
                if slug not in slugs:
                    findings.append({"kind": "blocked-by", "where": level.label, "file": task["file"],
                                     "message": f"{task['file']}: blocked_by {slug} names no task on the {level.label} board"})
            project = task["project"]
            if task["open"] and project and project.lower() not in NO_PROJECT and known and project not in known:
                findings.append({"kind": "unknown-project", "where": level.label, "file": task["file"],
                                 "message": f"{task['file']}: project {project} is not a registered project"})
    return findings


# ── fold: two cards of one project become the hive card and a flowie pointer ───────────────────

def same(a, b) -> bool:
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def as_items(value) -> list:
    """A field as a list: a single value (a repos string, say) is one item, never its characters."""
    if value in (None, "", []):
        return []
    return list(value) if isinstance(value, list) else [value]


def union(a, b) -> list:
    out = as_items(a)
    for item in as_items(b):
        if not any(same(item, kept) for kept in out):
            out.append(item)
    return out


def note_sections(text: str) -> tuple[list[str], str]:
    """A flowie project note: what its repository sections list (URLs, and local folders, which the caller keeps off
    the card), and everything else, kept."""
    text = text.replace("\r\n", "\n")
    urls: list[str] = []
    for heading, body in re.findall(r"^## +(.+?)\s*\n(.*?)(?=^## |\Z)", text, re.M | re.S):
        if heading.strip().lower() not in ("repos", "linked repos"):
            continue
        for line in body.splitlines():
            line = line.strip()
            if not line or re.match(r"^\|?\s*:?-{3,}", line):
                continue
            cell = line.strip("|").split("|")[0].strip() if line.startswith("|") else re.sub(r"^[-*+]\s+", "", line)
            cell = cell.strip("`<> ")
            if not cell or cell.lower() in ("url", "repo", "repository", "path"):
                continue
            found = re.findall(r"(?:https?|ssh|git)://\S+|[\w.-]+@[\w.-]+:[\w./-]+", cell)
            urls += found or ([cell.split()[0]] if is_local_path(cell.split()[0]) and re.search(r"[\\/]", cell) else [])
    kept = re.sub(r"^## +(.+?)\s*\n.*?(?=^## |\Z)",
                  lambda match: "" if match.group(1).strip().lower() in CARD_SECTIONS else match.group(0), text,
                  flags=re.M | re.S)
    kept = re.sub(r"\A# .*\n", "", kept).strip()
    return [url.rstrip("|).,`") for url in urls], kept


def dirty(level: Level, paths: list[str]) -> bool:
    """Whether a rebase or merge is in progress in the level's clone, or one of `paths` has uncommitted changes."""
    git_dir = level.root / ".git"
    if any((git_dir / marker).exists() for marker in ("rebase-merge", "rebase-apply", "MERGE_HEAD")):
        return True
    if shutil.which("git") is None or not level.is_clone:
        return False
    proc = subprocess.run(["git", "-C", str(level.root), "--no-optional-locks", "status", "--porcelain", "--", *paths],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    return proc.returncode == 0 and proc.stdout.strip() != ""  # git cannot answer: nothing to protect it from


def fold_plan(home: Path, keep: dict[str, str], projects: set[str], hives: set[str] | None, no_hive: bool) -> list[dict]:
    levels = all_levels(home)
    flowie = next((level for level in levels if level.kind == "flowie"), None)
    if flowie is None:
        return []
    plan = []
    for entry in flowie.entries:
        project_id = entry_id(entry)
        if is_pointer(entry) or (projects and project_id not in projects):
            continue
        holders = [level for level in levels if level.kind == "hive" and level.entry(project_id) is not None
                   and not is_pointer(level.entry(project_id))]
        if len(holders) != 1:
            continue  # a personal project, or cards in two hives (check reports it): nothing to fold here
        hive = holders[0]
        card = hive.entry(project_id)
        item: dict = {"project": project_id, "hive": hive.repo or hive.name, "hive_folder": hive.name, "differ": [],
                      "extra": {key: value for key, value in entry.items() if key not in (*CARD_FIELDS, "id", "ref")}}
        note = flowie.root / "projects" / f"{project_id}.md"
        note_urls, _ = note_sections(read_text(note) or "") if note.exists() else ([], "")
        flowie_repos = union(entry.get("repos"), [url for url in note_urls if not any(url in str(r) for r in as_items(entry.get("repos")))])
        # A folder on some machine never goes on the team's card: it is listed for ~/.neuroflow/local-projects.json.
        item["local_repos"] = [repo for repo in flowie_repos if is_local_path(repo.get("url", "") if isinstance(repo, dict) else str(repo))]
        mine_repos = [repo for repo in flowie_repos if repo not in item["local_repos"]]
        hive_writes = {}
        for field in CARD_FIELDS:
            mine = mine_repos if field == "repos" else entry.get(field)
            theirs = card.get(field)
            if mine in (None, "", []) or same(mine, theirs):
                continue
            default = "both" if field in LIST_FIELDS and theirs not in (None, []) else ("flowie" if theirs in (None, "", []) else "hive")
            side = keep.get(f"{project_id}.{field}", default)
            if side == "both" and field not in LIST_FIELDS:
                side = default
            item["differ"].append({"field": field, "flowie": mine, "hive": theirs, "keep": side})
            value = union(theirs, mine) if side == "both" else mine if side == "flowie" else theirs
            if not same(value, theirs):
                hive_writes[field] = value
        item["hive_writes"] = hive_writes
        if not hive.is_clone:
            item["blocked"] = "that hive is a copy of files, not a git clone: /hive --init replaces it first"
        elif hives is not None and hive.name not in hives and (hive.repo or "") not in hives:
            item["blocked"] = "that hive is not part of this run (its pull did not go through)"
        elif no_hive and hive_writes:
            item["blocked"] = "its hive card would change; fold it together with the hive"
        elif dirty(flowie, ["projects/projects.json", f"projects/{project_id}.md"]):
            item["blocked"] = "the flowie has a rebase in progress or uncommitted changes in its projects/ files"
        elif hive_writes and dirty(hive, ["projects/projects.json"]):
            item["blocked"] = "that hive has a rebase in progress or uncommitted changes in projects/projects.json"
        plan.append(item)
    return plan


def apply_fold(home: Path, plan: list[dict]) -> dict[str, list[str]]:
    flowie_root = home / ".neuroflow" / "flowie"
    flowie_json = flowie_root / "projects" / "projects.json"
    changed: dict[str, list[str]] = {"flowie": []}
    plan = [item for item in plan if not item.get("blocked")]
    if not plan:
        return changed
    flowie_data = read_json(flowie_json)
    for item in plan:
        project_id = item["project"]
        if item["hive_writes"]:
            hive_json = home / ".neuroflow" / "hives" / item["hive_folder"] / "projects" / "projects.json"
            hive_data = read_json(hive_json)
            for entry in hive_data["projects"] if isinstance(hive_data, dict) else hive_data:
                if isinstance(entry, dict) and entry_id(entry) == project_id:
                    entry.update(item["hive_writes"])
            write_json(hive_json, hive_data)
            if "projects/projects.json" not in changed.setdefault(item["hive_folder"], []):
                changed[item["hive_folder"]].append("projects/projects.json")
        pointer = {"id": project_id, "ref": f"hive:{item['hive']}", **item["extra"]}
        entries = flowie_data["projects"] if isinstance(flowie_data, dict) else flowie_data
        entries[:] = [pointer if isinstance(entry, dict) and entry_id(entry) == project_id else entry for entry in entries]
        note = flowie_root / "projects" / f"{project_id}.md"
        if note.exists():
            raw = read_text(note) or ""
            _, kept = note_sections(raw)
            body = kept if re.search(r"^## ", kept, re.M) or not kept else f"## Notes\n\n{kept}"
            text = (f"# {project_id}\n\nCard: hive {item['hive']} → projects/{project_id}.md (status, phase, description "
                    f"and repos live there).\n\n{body or '## Notes'}\n")
            note.write_bytes(text.replace("\n", "\r\n" if "\r\n" in raw else "\n").encode("utf-8"))
            changed["flowie"].append(f"projects/{project_id}.md")
    write_json(flowie_json, flowie_data)
    changed["flowie"].append("projects/projects.json")
    return changed


def write_json(path: Path, data) -> None:
    raw = read_text(path) or ""
    newline = "\r\n" if "\r\n" in raw else "\n"
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.replace("\n", newline).encode("utf-8"))


# ── command line ────────────────────────────────────────────────────────────────────────────────

def print_view(result: dict) -> None:
    card = result["card"]
    head = result["project"]
    if card:
        head += f" — card in the {card['where']}" + (f", {card.get('status')}" if card.get("status") else "")
        head += f", phase {card.get('current_phase')}" if card.get("current_phase") else ""
    print(head if card else f"{head} — no card")
    for problem in result["problems"]:
        print(f"  ! {problem}")
    for level in result["levels"]:
        open_tasks = [task for task in level["tasks"] if task["open"]]
        source = level["source"] + (f", fetched {level['fetched']}" if level.get("fetched") else "")
        print(f"  [{level['name']}] {len(open_tasks)} open ({source})" + (f" — {level['error']}" if level.get("error") else ""))
        for task in open_tasks:
            extra = "".join([f" @{task['owner']}" if task["owner"] else "", f" due {task['due']}" if task["due"] else "",
                             f" blocked by {', '.join(task['blocked_by'])}" if task["blocked_by"] else ""])
            print(f"    {task['column']}: {task['title']}{extra}")


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["list", "check", "view", "refresh", "fold"])
    parser.add_argument("--project", action="append", default=[], help="the project id (view, refresh; fold: limit to it)")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="a folder inside this repository (view, refresh)")
    parser.add_argument("--no-remote", action="store_true", help="view: read the cache only, no network")
    parser.add_argument("--hive", action="append", default=None, metavar="NAME", help="fold: a hive that may be written")
    parser.add_argument("--no-hive", action="store_true", help="fold: write no hive; skip projects whose card would change")
    parser.add_argument("--apply", action="store_true", help="fold: write the planned changes")
    parser.add_argument("--keep", action="append", default=[], metavar="ID.FIELD=SIDE",
                        help="fold: which value a differing field keeps (flowie, hive, or both for repos/visited_phases)")
    parser.add_argument("--home", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--json", action="store_true", help="print the result as JSON")
    args = parser.parse_args(argv)
    home = args.home or Path.home()
    try:
        if args.command in ("view", "refresh") and len(args.project) != 1:
            raise UsageError(f"{args.command} needs one --project ID")
        keep = {}
        for item in args.keep:
            match = re.match(r"^(.+)\.([a-z_]+)=(flowie|hive|both)$", item)
            if not match or match.group(2) not in CARD_FIELDS:
                raise UsageError(f"--keep {item}: expected ID.FIELD=flowie|hive|both with FIELD one of {', '.join(CARD_FIELDS)}")
            keep[f"{match.group(1)}.{match.group(2)}"] = match.group(3)
        if args.command == "list":
            rows = [{"project": entry_id(entry), "where": level.label,
                     "kind": "pointer" if is_pointer(entry) else "card", **({"ref": entry["ref"]} if is_pointer(entry) else {})}
                    for level in all_levels(home) for entry in level.entries]
            if args.json:
                print(json.dumps({"projects": rows}, ensure_ascii=False, indent=2))
            else:
                for row in rows:
                    print(f"{row['project']}: {row['kind']} in the {row['where']}" + (f" → {row['ref']}" if row.get("ref") else ""))
            return 0
        if args.command == "check":
            findings = check(home)
            if args.json:
                print(json.dumps({"findings": findings}, ensure_ascii=False, indent=2))
            else:
                for finding in findings:
                    print(f"{finding['kind']}: {finding['message']}")
                print(f"{len(findings)} finding(s)" if findings else "projects: no findings")
            return 1 if findings else 0
        if args.command == "view":
            result = view(home, args.project[0], args.root, remote=not args.no_remote)
            print(json.dumps(result, ensure_ascii=False, indent=2)) if args.json else print_view(result)
            return 1 if any(level.get("error") for level in result["levels"]) else 0
        if args.command == "refresh":
            result = refresh(home, args.project[0], args.root)
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                for repo in result["repos"]:
                    print(f"{repo['repo']}: {'refreshed' if repo['ok'] else 'not refreshed — ' + repo['error']}")
            return 1 if any(not repo["ok"] for repo in result["repos"]) else 0
        hives = set(args.hive) if args.hive is not None else None
        plan = fold_plan(home, keep, set(args.project), hives, args.no_hive)
        changed = apply_fold(home, plan) if args.apply else {}
        if args.json:
            print(json.dumps({"applied": bool(args.apply and any(not item.get("blocked") for item in plan)), "plan": plan,
                              "changed": changed}, ensure_ascii=False, indent=2))
        else:
            for item in plan:
                if item.get("blocked"):
                    print(f"{item['project']}: not folded — {item['blocked']}")
                    continue
                print(f"{item['project']}: one card in hive {item['hive']}, a pointer in the flowie")
                for change in item["differ"]:
                    print(f"    {change['field']}: flowie {json.dumps(change['flowie'], ensure_ascii=False)} · hive "
                          f"{json.dumps(change['hive'], ensure_ascii=False)} → keeps {change['keep']}")
            if not plan:
                print("projects: nothing to fold")
            elif not args.apply:
                print("run again with --apply to write these changes (nothing is staged, committed or pushed)")
        return 1 if plan else 0
    except UsageError as error:
        print(f"projects: {error}", file=sys.stderr)
        return 2
    except Exception as error:  # a registry shape nobody foresaw is a runtime error, never "findings"
        print(f"projects: {type(error).__name__}: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
