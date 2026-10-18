#!/usr/bin/env python3
"""One research project across the flowie, the team hives and its repositories (neuroflow-core → Project registry).

A project has one card: a team project's in the hive its team works in, a personal project's in the flowie. The other
level holds at most a pointer ({"id": …, "ref": "hive:{org}/{repo}"}) with personal notes, never a copy of the card's
fields. Tasks stay on three boards (project repo, flowie, hive: /tasks → Levels); this script reads them together.

subcommands:
  list                       every card and pointer, where it lives
  check                      two cards for one project, pointers that lead nowhere or carry copies, blocked_by
                             entries that name no task at their level, tasks whose project: names no registered project
  view --project ID          the project's open tasks at every level: the flowie, each hive, this repository's board
                             and the boards of the card's other repositories — read from a machine-local cache
                             (~/.neuroflow/boards/) that is refreshed from their remotes first (--no-remote: cache only)
  refresh --project ID       refresh that cache only
  fold [--apply] [--keep ID.FIELD=flowie|hive ...]
                             two cards of one project (one in the flowie, one in a hive) become the hive card and a
                             flowie pointer; a field that differs keeps the hive's value unless --keep says flowie.
                             Writes files only with --apply, stages nothing, never commits or pushes.
  add --json for a machine-readable result; --home DIR stands in for the home folder (tests)

exit codes: 0 clean (check), nothing to do (fold) or done · 1 findings (check), planned or applied changes (fold),
a repository that could not be read (view/refresh) · 2 usage or runtime error
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CARD_FIELDS = ("description", "repos", "current_phase", "visited_phases", "status")
CLOSED = {"done", "archive", "archived"}
NO_PROJECT = {"", "-", "—", "none", "personal", "null", "~"}
DEFAULT_COLUMNS = ["inbox", "ready", "active", "review", "meeting", "done", "archive"]
GIT_ENV = {"GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never"}


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
        return path.read_bytes().decode("utf-8", errors="replace")
    except OSError:
        return None


def read_json(path: Path) -> dict | None:
    text = read_text(path)
    if text is None:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


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


def repo_key(url: str) -> str | None:
    """`host/owner/repo`, lower case, for a git URL in any spelling (https, ssh, scp form, no scheme); None if not a URL."""
    url = url.strip()
    match = re.match(r"^(?:[a-z][a-z0-9+.-]*://)?(?:[^@/]+@)?([A-Za-z0-9.-]+\.[A-Za-z]{2,})[:/]+(.+?)(?:\.git)?/*$", url)
    if not match or re.match(r"^[A-Za-z]:[\\/]", url):
        return None
    return f"{match.group(1)}/{match.group(2)}".lower()


def clone_url(url: str) -> str:
    url = url.strip()
    if re.match(r"^[a-z][a-z0-9+.-]*://", url) or re.match(r"^[^@/]+@[^:]+:", url):
        return url
    return "https://" + url


def origin_url(repo: Path) -> str | None:
    """The `origin` URL in a clone's git config (a worktree's .git file is followed)."""
    git = repo / ".git"
    if git.is_file():
        match = re.search(r"gitdir:\s*(.+)", read_text(git) or "")
        if not match:
            return None
        gitdir = Path(match.group(1).strip())
        gitdir = gitdir if gitdir.is_absolute() else repo / gitdir
        common = read_text(gitdir / "commondir")
        git = (gitdir / common.strip()).resolve() if common else gitdir
    config = read_text(git / "config") or ""
    section = re.search(r'\[remote "origin"\]([^\[]*)', config)
    url = re.search(r"^\s*url\s*=\s*(.+?)\s*$", section.group(1), re.M) if section else None
    return url.group(1) if url else None


# ── the registry ────────────────────────────────────────────────────────────────────────────────

class Level:
    """The flowie or one hive clone: its registry and its task board."""

    def __init__(self, kind: str, root: Path, name: str, repo: str | None) -> None:
        self.kind, self.root, self.name, self.repo = kind, root, name, repo  # repo: org/repo of a hive
        self.is_clone = (root / ".git" / "HEAD").is_file() or (root / ".git").is_file()
        data = read_json(root / "projects" / "projects.json")
        self.registry_ok = data is not None or not (root / "projects" / "projects.json").exists()
        entries = data.get("projects", []) if data else []
        self.entries: list[dict] = [entry for entry in entries if isinstance(entry, dict) and entry.get("id")]

    @property
    def label(self) -> str:
        return "flowie" if self.kind == "flowie" else f"hive {self.repo or self.name}"

    def entry(self, project_id: str) -> dict | None:
        return next((entry for entry in self.entries if str(entry["id"]) == project_id), None)


def is_pointer(entry: dict) -> bool:
    return isinstance(entry.get("ref"), str) and entry["ref"].startswith("hive:")


def hive_levels(home: Path) -> list[Level]:
    hives = home / ".neuroflow" / "hives"
    levels = []
    for folder in sorted(hives.iterdir() if hives.is_dir() else [], key=lambda p: p.name.lower()):
        if not folder.is_dir():
            continue
        key = repo_key(origin_url(folder) or "")
        repo = "/".join(key.split("/")[1:]) if key else None
        levels.append(Level("hive", folder, folder.name, repo))
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


# ── tasks ───────────────────────────────────────────────────────────────────────────────────────

def board_columns(tasks: Path) -> list[str]:
    config = read_json(tasks / "config.json") or {}
    columns = [str(column.get("id")) for column in config.get("columns", []) if isinstance(column, dict) and column.get("id")]
    return columns or DEFAULT_COLUMNS


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


# ── machine-local cache of the boards of repositories not checked out here ─────────────────────

def git(args: list[str], cwd: Path | None = None, timeout: int = 90) -> subprocess.CompletedProcess:
    env = dict(os.environ, **GIT_ENV)
    try:
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", env=env, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as error:
        return subprocess.CompletedProcess(args, 1, "", str(error))


def cache_dir(home: Path, key: str) -> Path:
    return home / ".neuroflow" / "boards" / Path(*key.split("/"))


def refresh_cache(home: Path, url: str, key: str) -> tuple[bool, str]:
    """A shallow, sparse clone that holds only the repository's `.neuroflow/tasks/`: cloned once, refreshed after."""
    if shutil.which("git") is None:
        return False, "git is not installed"
    target = cache_dir(home, key)
    if not (target / ".git").exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        steps = [
            (["clone", "--depth", "1", "--filter=blob:none", "--no-checkout", "--quiet", clone_url(url), str(target)], None),
            (["sparse-checkout", "set", "--no-cone", "/.neuroflow/tasks/"], target),
            (["checkout", "--quiet"], target),
        ]
    else:
        steps = [
            (["fetch", "--depth", "1", "--quiet", "origin", "HEAD"], target),
            (["checkout", "--quiet", "--force", "FETCH_HEAD"], target),
        ]
    for args, cwd in steps:
        proc = git(args, cwd)
        if proc.returncode != 0:
            reason = next((line for line in (proc.stderr + proc.stdout).splitlines() if line.strip()), "git failed")
            if args[0] == "clone":
                shutil.rmtree(target, ignore_errors=True)
            return False, reason.strip()[:200]
    (target / ".neuroflow-fetched").write_text(datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") + "\n",
                                               encoding="utf-8")
    return True, ""


def local_projects(home: Path) -> list[dict]:
    data = read_json(home / ".neuroflow" / "local-projects.json") or {}
    return [entry for entry in data.get("projects", []) if isinstance(entry, dict)]


def find_root(start: Path) -> Path | None:
    for folder in [start, *start.parents]:
        if (folder / ".neuroflow" / "project_config.md").is_file():
            return folder
    return None


def card_repos(card: dict) -> list[str]:
    urls = []
    for repo in card.get("repos") or []:
        url = repo.get("url") if isinstance(repo, dict) else repo
        if isinstance(url, str) and repo_key(url):
            urls.append(url)
    return urls


def linked_id(home: Path, levels: list[Level], root: Path) -> str | None:
    """The project this repository is: its local-projects.json entry, else a card or pointer listing its origin."""
    for entry in local_projects(home):
        path = str(entry.get("path") or "")
        if path and Path(path).expanduser().resolve() == root.resolve():
            return str(entry.get("name") or "") or None
    key = repo_key(origin_url(root) or "")
    for level in levels:
        for entry in level.entries:
            if key and any(repo_key(url) == key for url in card_repos(entry)):
                return str(entry["id"])
    return None


def view(home: Path, project_id: str, root: Path | None, remote: bool) -> dict:
    levels = all_levels(home)
    where, card, problems = find_card(levels, project_id)
    result: dict = {"project": project_id, "card": None, "problems": problems, "levels": []}
    if card is not None:
        result["card"] = {"where": where.label, **{field: card.get(field) for field in CARD_FIELDS if field in card}}
    for level in levels:
        tasks = [task for task in read_board(level.root / "tasks") if task["project"] == project_id]
        if tasks or level.kind == "flowie" or level is where:
            result["levels"].append({"level": level.kind, "name": level.label, "source": "local", "tasks": tasks})
    here = find_root(root) if root is not None else None
    if here is not None and linked_id(home, levels, here) == project_id:
        result["levels"].append({"level": "project", "name": "this repository", "source": "local",
                                 "tasks": read_board(here / ".neuroflow" / "tasks")})
    seen = {repo_key(origin_url(here) or "")} if here is not None else set()
    checked_out = {repo_key(str(entry.get("remote") or "")): Path(str(entry.get("path"))).expanduser()
                   for entry in local_projects(home) if entry.get("remote") and entry.get("path")}
    for url in card_repos(card or {}):
        key = repo_key(url)
        if key in seen:
            continue
        seen.add(key)
        local = checked_out.get(key)
        if local is not None and (local / ".neuroflow").is_dir():
            result["levels"].append({"level": "project", "name": key, "source": f"local copy ({local.as_posix()})",
                                     "tasks": read_board(local / ".neuroflow" / "tasks")})
            continue
        entry: dict = {"level": "project", "name": key, "source": "remote", "tasks": []}
        if remote:
            ok, reason = refresh_cache(home, url, key)
            if not ok:
                entry["error"] = reason
        cached = cache_dir(home, key)
        stamp = read_text(cached / ".neuroflow-fetched")
        entry["fetched"] = stamp.strip() if stamp else None
        if (cached / ".git").exists():
            entry["tasks"] = read_board(cached / ".neuroflow" / "tasks")
        elif "error" not in entry:
            entry["error"] = "not fetched yet (run without --no-remote)"
        result["levels"].append(entry)
    return result


def refresh(home: Path, project_id: str) -> dict:
    levels = all_levels(home)
    _, card, problems = find_card(levels, project_id)
    out = {"project": project_id, "problems": problems, "repos": []}
    checked_out = {repo_key(str(entry.get("remote") or "")) for entry in local_projects(home) if entry.get("remote")}
    for url in card_repos(card or {}):
        key = repo_key(url)
        if key in checked_out:
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
            findings.append({"kind": "registry", "where": level.label, "message": "projects/projects.json is not valid JSON"})
    ids = {str(entry["id"]) for level in levels for entry in level.entries}
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
                                        + " — /neuroflow:migrate folds them into one card and a pointer"})
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
    for level in levels:
        tasks = read_board(level.root / "tasks")
        slugs = {task["slug"] for task in tasks}
        known = {str(entry["id"]) for entry in level.entries}
        for task in tasks:
            for slug in task["blocked_by"]:
                if slug not in slugs:
                    findings.append({"kind": "blocked-by", "where": level.label, "file": task["file"],
                                     "message": f"{task['file']}: blocked_by {slug} names no task on the {level.label} board"})
            project = task["project"]
            if task["open"] and project and project.lower() not in NO_PROJECT and known and project not in known:
                findings.append({"kind": "unknown-project", "where": level.label, "file": task["file"],
                                 "message": f"{task['file']}: project {project} is not in the {level.label} registry"})
    return findings


# ── fold: two cards of one project become the hive card and a flowie pointer ───────────────────

def fold_plan(home: Path, keep: dict[str, str]) -> list[dict]:
    levels = all_levels(home)
    flowie = next((level for level in levels if level.kind == "flowie"), None)
    if flowie is None:
        return []
    plan = []
    for entry in flowie.entries:
        if is_pointer(entry):
            continue
        project_id = str(entry["id"])
        hives = [level for level in levels if level.kind == "hive" and (level.entry(project_id) or {}) and not is_pointer(level.entry(project_id))]
        if len(hives) != 1:
            continue  # a personal project, or a card in two hives (check reports it): nothing to fold here
        hive = hives[0]
        if not hive.is_clone:
            plan.append({"project": project_id, "hive": hive.repo or hive.name, "hive_folder": hive.name, "differ": [],
                         "blocked": "that hive is a copy of files, not a git clone: /hive --init replaces it first"})
            continue
        card = hive.entry(project_id)
        fields = []
        for field in CARD_FIELDS:
            mine, theirs = entry.get(field), card.get(field)
            if mine is None or json.dumps(mine, sort_keys=True) == json.dumps(theirs, sort_keys=True):
                continue
            side = keep.get(f"{project_id}.{field}", "hive")
            fields.append({"field": field, "flowie": mine, "hive": theirs, "keep": side})
        plan.append({"project": project_id, "hive": hive.repo or hive.name, "hive_folder": hive.name, "differ": fields})
    return plan


def apply_fold(home: Path, plan: list[dict]) -> dict[str, list[str]]:
    flowie_root = home / ".neuroflow" / "flowie"
    flowie_json = flowie_root / "projects" / "projects.json"
    flowie_data = read_json(flowie_json) or {"projects": []}
    changed: dict[str, list[str]] = {"flowie": []}
    plan = [item for item in plan if not item.get("blocked")]
    for item in plan:
        project_id, hive_root = item["project"], home / ".neuroflow" / "hives" / item["hive_folder"]
        hive_json = hive_root / "projects" / "projects.json"
        hive_data = read_json(hive_json) or {"projects": []}
        updates = {change["field"]: change["flowie"] for change in item["differ"] if change["keep"] == "flowie"}
        if updates:
            for entry in hive_data["projects"]:
                if isinstance(entry, dict) and str(entry.get("id")) == project_id:
                    entry.update(updates)
            write_json(hive_json, hive_data)
            changed.setdefault(item["hive_folder"], []).append("projects/projects.json")
        pointer = {"id": project_id, "ref": f"hive:{item['hive']}"}
        flowie_data["projects"] = [pointer if isinstance(entry, dict) and str(entry.get("id")) == project_id else entry
                                   for entry in flowie_data["projects"]]
        note = flowie_root / "projects" / f"{project_id}.md"
        if note.exists():
            notes = personal_notes(read_text(note) or "")
            note.write_text(f"# {project_id}\n\nCard: hive {item['hive']} → projects/{project_id}.md (status, phase, "
                            f"description and repos live there).\n\n## Notes\n\n{notes}".rstrip() + "\n", encoding="utf-8")
            changed["flowie"].append(f"projects/{project_id}.md")
    if plan:
        write_json(flowie_json, flowie_data)
        changed["flowie"].append("projects/projects.json")
    return changed


def personal_notes(text: str) -> str:
    match = re.search(r"^## Notes\s*\n(.*?)(?=^## |\Z)", text.replace("\r\n", "\n"), re.M | re.S)
    return match.group(1).strip() + "\n" if match and match.group(1).strip() else ""


def write_json(path: Path, data: dict) -> None:
    raw = read_text(path) or ""
    newline = "\r\n" if "\r\n" in raw else "\n"
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.replace("\n", newline).encode("utf-8"))


# ── command line ────────────────────────────────────────────────────────────────────────────────

def print_view(result: dict) -> None:
    card = result["card"]
    print(f"{result['project']}" + (f" — card in the {card['where']}" + (f", {card.get('status')}" if card.get("status") else "")
                                    + (f", phase {card.get('current_phase')}" if card.get("current_phase") else "") if card else " — no card"))
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
    parser.add_argument("--project", help="the project id (view, refresh)")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="a folder inside this repository (view)")
    parser.add_argument("--no-remote", action="store_true", help="view: read the cache only, no network")
    parser.add_argument("--apply", action="store_true", help="fold: write the planned changes")
    parser.add_argument("--keep", action="append", default=[], metavar="ID.FIELD=SIDE",
                        help="fold: keep the flowie's value of a field that differs (SIDE is flowie or hive)")
    parser.add_argument("--home", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--json", action="store_true", help="print the result as JSON")
    args = parser.parse_args(argv)
    home = args.home or Path.home()
    try:
        if args.command in ("view", "refresh") and not args.project:
            raise UsageError(f"{args.command} needs --project ID")
        keep = {}
        for item in args.keep:
            match = re.match(r"^(.+)\.([a-z_]+)=(flowie|hive)$", item)
            if not match or match.group(2) not in CARD_FIELDS:
                raise UsageError(f"--keep {item}: expected ID.FIELD=flowie|hive with FIELD one of {', '.join(CARD_FIELDS)}")
            keep[f"{match.group(1)}.{match.group(2)}"] = match.group(3)
        if args.command == "list":
            levels = all_levels(home)
            rows = [{"project": str(entry["id"]), "where": level.label,
                     "kind": "pointer" if is_pointer(entry) else "card", **({"ref": entry["ref"]} if is_pointer(entry) else {})}
                    for level in levels for entry in level.entries]
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
            result = view(home, args.project, args.root, remote=not args.no_remote)
            print(json.dumps(result, ensure_ascii=False, indent=2)) if args.json else print_view(result)
            return 1 if any(level.get("error") for level in result["levels"]) else 0
        if args.command == "refresh":
            result = refresh(home, args.project)
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                for repo in result["repos"]:
                    print(f"{repo['repo']}: {'refreshed' if repo['ok'] else 'not refreshed — ' + repo['error']}")
            return 1 if any(not repo["ok"] for repo in result["repos"]) else 0
        plan = fold_plan(home, keep)
        changed = apply_fold(home, plan) if args.apply and plan else {}
        if args.json:
            print(json.dumps({"applied": bool(args.apply and plan), "plan": plan, "changed": changed}, ensure_ascii=False, indent=2))
        else:
            for item in plan:
                if item.get("blocked"):
                    print(f"{item['project']}: not folded — {item['blocked']}")
                    continue
                print(f"{item['project']}: one card in hive {item['hive']}, a pointer in the flowie")
                for change in item["differ"]:
                    print(f"    {change['field']}: flowie {json.dumps(change['flowie'], ensure_ascii=False)} · hive "
                          f"{json.dumps(change['hive'], ensure_ascii=False)} → keeps the {change['keep']}'s")
            if not plan:
                print("projects: nothing to fold")
            elif not args.apply:
                print("run again with --apply to write these changes (nothing is staged, committed or pushed)")
        return 1 if plan else 0
    except UsageError as error:
        print(f"projects: {error}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"projects: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
