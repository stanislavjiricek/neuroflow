#!/usr/bin/env python3
"""Collect the deterministic parts of a project handoff dossier (phase-output).

When a project changes hands, this gathers what the successor needs that no
single file states: git state (uncommitted, unpushed, stashed, local-only
branches), data roots, the preregistration freeze (verified by
phase-preregistration/scripts/freeze.py), ethics status and expiry, open tasks
by owner, integrations that were connected with personal credentials (key
names only), HPC jobs, and what stays with the person leaving.

Read-only: it never writes, commits, pushes or uploads anything. It prints the
dossier as Markdown (or JSON); the /output --handoff mode reviews it with the
person and saves it.

Usage:
    python <phase-output skill base dir>/scripts/handoff.py [--root DIR] [--no-hpc] [--json]

Exit codes:
    0  dossier built, nothing needs attention
    1  dossier built, items need attention (listed first)
    2  no .neuroflow/ under --root, or a runtime error

Stdlib only. Python 3.10+.
"""

from __future__ import annotations

import argparse
import getpass
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

# The task board as commands/tasks.md defines it: default columns, and the keys that name a task's people
# (`owner`, then the legacy `assignee` / `responsible`, read as owner).
DEFAULT_COLUMNS = ("inbox", "ready", "active", "review", "meeting", "done", "archive")
OWNER_KEYS = ("owner", "assignee", "responsible")
EXPIRY_WARN_DAYS = 60
WALK_CAP = 200_000


def _export():
    """export.py: config reader and sharing-tier rules (one home)."""
    name = "_nf_phase_output_export"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name("export.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _git(root: Path, *args: str) -> str | None:
    try:
        out = subprocess.run(["git", "-c", "core.quotePath=false", *args], cwd=root,
                             capture_output=True, check=False)
    except OSError:
        return None
    return out.stdout.decode("utf-8", "replace") if out.returncode == 0 else None


def _frontmatter(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    return _export().parse_frontmatter(text) or {}


def _table_value(path: Path, label: str) -> str | None:
    """Legacy `| Label | value |` rows (older ethics/status.md files)."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = re.search(rf"(?im)^\|\s*{re.escape(label)}\s*\|\s*([^|]*?)\s*\|", text)
    return m.group(1) if m and m.group(1) else None


def _parse_date(value) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def section_git(root: Path, attention: list[str]) -> dict:
    if _git(root, "rev-parse", "--git-dir") is None:
        attention.append("the project is not a git repository - nothing is versioned or shared")
        return {"repository": False}
    branch = (_git(root, "rev-parse", "--abbrev-ref", "HEAD") or "").strip()
    upstream = (_git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}") or "").strip() or None
    ahead = behind = None
    if upstream:
        counts = (_git(root, "rev-list", "--left-right", "--count", "@{u}...HEAD") or "").split()
        if len(counts) == 2:
            behind, ahead = int(counts[0]), int(counts[1])
    changed = untracked = 0
    entries = iter((_git(root, "status", "--porcelain=v1", "-z") or "").split("\0"))
    for entry in entries:
        if not entry.strip():
            continue
        if entry.startswith("??"):
            untracked += 1
            continue
        changed += 1
        if entry[:1] in ("R", "C"):
            next(entries, None)  # the rename/copy source path follows as its own entry
    stashes = len([s for s in (_git(root, "stash", "list") or "").splitlines() if s.strip()])
    remotes = {}
    for line in (_git(root, "remote", "-v") or "").splitlines():
        parts = line.split()
        if len(parts) >= 2:
            remotes[parts[0]] = re.sub(r"(https?://)[^/@\s]+@", r"\1", parts[1])
    no_upstream = []
    refs = _git(root, "for-each-ref", "--format=%(refname:short)\t%(upstream:short)", "refs/heads") or ""
    for line in refs.splitlines():
        name, _, up = line.partition("\t")
        if name.strip() and not up.strip():
            no_upstream.append(name.strip())
    unpushed = len([c for c in (_git(root, "log", "--branches", "--not", "--remotes", "--format=%h") or "").splitlines()
                    if c.strip()])
    if changed or untracked:
        attention.append(f"uncommitted work: {changed} changed and {untracked} untracked files")
    if not remotes:
        attention.append("no git remote - the successor cannot get this repository")
    elif unpushed:
        attention.append(f"{unpushed} commits exist only on this machine (not on any remote)")
    if stashes:
        attention.append(f"{stashes} stashes exist only on this machine")
    if no_upstream and remotes:
        attention.append(f"local branches without an upstream: {', '.join(sorted(no_upstream))}")
    return {"repository": True, "branch": branch, "upstream": upstream, "ahead": ahead, "behind": behind,
            "changed": changed, "untracked": untracked, "stashes": stashes, "remotes": remotes,
            "unpushed_commits": unpushed, "branches_without_upstream": sorted(no_upstream)}


def section_data(root: Path, cfg: dict, attention: list[str]) -> list[dict]:
    roots = cfg.get("raw_roots") or []
    if isinstance(roots, str):
        roots = [r.strip() for r in roots.split(",") if r.strip()]
    out = []
    for r in roots:
        path = (root / str(r)).resolve()
        entry = {"path": str(r), "exists": path.is_dir()}
        if not path.is_dir():
            attention.append(f"data root {r} is missing on this machine - record where the data lives")
        else:
            files = size = 0
            capped = False
            for dirpath, _dirs, names in os.walk(path):
                for n in names:
                    files += 1
                    try:
                        size += (Path(dirpath) / n).stat().st_size
                    except OSError:
                        pass
                    if files >= WALK_CAP:
                        capped = True
                        break
                if capped:
                    break
            entry.update({"files": files, "bytes": size, "capped": capped,
                          "bids": (path / "dataset_description.json").is_file()})
        out.append(entry)
    return out


def freeze_verify(root: Path) -> dict | None:
    """Run the preregistration hash lock's own verifier (one home for that check:
    skills/phase-preregistration/scripts/freeze.py). None when it is unavailable."""
    script = Path(__file__).resolve().parents[2] / "phase-preregistration" / "scripts" / "freeze.py"
    if not script.is_file():
        return None
    try:
        out = subprocess.run([sys.executable, str(script), "verify", "--root", str(root), "--json"],
                             capture_output=True, text=True, timeout=120, check=False)
        return json.loads(out.stdout) if out.returncode in (0, 1) else None
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return None


def section_prereg(root: Path, attention: list[str]) -> dict:
    status_md = root / ".neuroflow" / "preregistration" / "status.md"
    if not status_md.is_file():
        return {"present": False}
    fm = _frontmatter(status_md)
    status = str(fm.get("status") or "unknown")
    files: list[dict] = []
    verified = None
    if status == "frozen":
        result = freeze_verify(root)
        verified = result is not None
        if result is None:
            attention.append("preregistration is frozen but its hashes could not be verified - run /preregistration")
        else:
            files = [{"path": f.get("path"), "state": "ok" if f.get("ok") else "changed or missing"}
                     for f in result.get("files", [])]
            for f in result.get("findings", []):
                attention.append(f"preregistration: {f.get('kind')} - {f.get('path')}")
    deviations = root / ".neuroflow" / "preregistration" / "deviations.md"
    return {"present": True, "status": status, "frozen_at": fm.get("frozen_at"), "set_by": fm.get("set_by"),
            "registry": fm.get("registry"), "doi": fm.get("doi"), "files": files, "verified": verified,
            "deviations_file": deviations.is_file()}


def section_ethics(root: Path, attention: list[str], today: date) -> dict:
    status_md = root / ".neuroflow" / "ethics" / "status.md"
    if not status_md.is_file():
        return {"present": False}
    fm = _frontmatter(status_md)
    status = str(fm.get("status") or _table_value(status_md, "Status") or "unknown").lower()
    expires = _parse_date(fm.get("expires") or _table_value(status_md, "Expires"))
    set_by = fm.get("set_by")
    if status == "approved" and fm and set_by != "person":
        attention.append("ethics approval was not recorded by a person (set_by is not person) - treat it as not set")
    elif status not in ("approved", "none"):
        attention.append(f"ethics status is {status}")
    if expires:
        days = (expires - today).days
        if days < 0:
            attention.append(f"ethics approval expired on {expires.isoformat()}")
        elif days <= EXPIRY_WARN_DAYS:
            attention.append(f"ethics approval expires in {days} days ({expires.isoformat()})")
    return {"present": True, "status": status, "expires": expires.isoformat() if expires else None,
            "approval_id": fm.get("approval_id"), "ai_processing": fm.get("ai_processing"), "set_by": set_by}


def task_columns(folder: Path) -> tuple[list[str], set[str]]:
    """The board's column ids (tasks/config.json, else the defaults) and the columns whose tasks are not open:
    done and every archive column (commands/tasks.md -> Columns)."""
    columns: list[str] = []
    closed = {"done", "archive"}
    try:
        config = json.loads((folder / "config.json").read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        config = None
    entries = config.get("columns") if isinstance(config, dict) else None
    for entry in entries if isinstance(entries, list) else []:
        cid = entry.get("id") if isinstance(entry, dict) else None
        if isinstance(cid, str) and cid.strip():
            columns.append(cid.strip().lower())
            if entry.get("archive") is True:
                closed.add(columns[-1])
    return columns or list(DEFAULT_COLUMNS), closed


def task_owners(fm: dict) -> list[str]:
    """Each person a task names in `owner` (one handle or a list), then in the legacy `assignee` / `responsible`:
    roster handles without the @, each once (commands/tasks.md -> Task file format)."""
    people: dict[str, str] = {}
    for key in OWNER_KEYS:
        value = fm.get(key)
        for item in value if isinstance(value, list) else [value]:
            handle = item.strip().lstrip("@").strip() if isinstance(item, str) else ""
            if handle:
                people.setdefault(handle.lower(), handle)
    return list(people.values())


def section_tasks(root: Path, today: date) -> dict:
    """Open tasks by owner. A task at tasks/{column}/{slug}.md is in its folder's column, whatever its `status`
    says; a legacy flat tasks/{id}-{slug}.md is in the column its `status` names (`archived` = archive; without
    one, the inbox, or the board's first column when it has no inbox). Tasks in done or an archive column are not
    open. A task naming several people is listed under each, so nobody is dropped from the handoff."""
    folder = root / ".neuroflow" / "tasks"
    by_owner: dict[str, list] = {}
    if not folder.is_dir():
        return by_owner
    columns, closed = task_columns(folder)
    inbox = "inbox" if "inbox" in columns else columns[0]
    headings: dict[str, str] = {}  # one heading per person: handles compare without case
    for path in sorted(folder.rglob("*.md")):
        if path.name.lower() in ("flow.md", "readme.md", "index.md"):
            continue
        fm = _frontmatter(path)
        if not fm:  # not a task file: the board does not show it either
            continue
        parts = path.relative_to(folder).parts
        status = (parts[0] if len(parts) > 1 else str(fm.get("status") or inbox)).strip().lower()
        if status == "archived":
            status = "archive"
        if status in closed:
            continue
        due = _parse_date(fm.get("due"))
        task = {"id": fm.get("id") or path.stem, "title": fm.get("title") or path.stem, "status": status,
                "due": due.isoformat() if due else None, "overdue": bool(due and due < today)}
        for person in task_owners(fm) or ["unassigned"]:
            by_owner.setdefault(headings.setdefault(person.lower(), person), []).append(task)
    return by_owner


def section_integrations(root: Path) -> list[str]:
    path = root / ".neuroflow" / "integrations.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    keys = []
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict):
                keys += [f"{k}.{kk}" for kk in v]
            else:
                keys.append(str(k))
    return sorted(keys)


def section_hpc() -> list[str]:
    user = getpass.getuser()
    for cmd in (["squeue", "-h", "-u", user, "-o", "%i %j %T %M"], ["qstat", "-u", user]):
        if shutil.which(cmd[0]):
            try:
                out = subprocess.run(cmd, capture_output=True, text=True, timeout=20, check=False)
            except (OSError, subprocess.TimeoutExpired):
                return [f"{cmd[0]} did not answer"]
            lines = [ln for ln in out.stdout.splitlines() if ln.strip()]
            return [f"{cmd[0]}: {ln}" for ln in lines[:50]] or [f"{cmd[0]}: no jobs"]
    return []


def section_personal(root: Path) -> list[dict]:
    """Local-tier memory that stays with the person leaving, with file counts. A folder's own
    .gitignore is housekeeping, not content (the wiki review queue keeps one with `*` so its cards
    stay local): it is not counted, and a folder with nothing else is not listed."""
    rules = _export()
    out = []
    for sub in rules.LOCAL_TIER:
        path = root / ".neuroflow" / sub.rstrip("/")
        if path.exists():
            if path.is_dir():
                own_ignore = path / ".gitignore"
                count = sum(1 for p in path.rglob("*") if p.is_file() and p != own_ignore)
            else:
                count = 1
            if count:
                out.append({"path": f".neuroflow/{sub}", "files": count})
        elif not sub.endswith("/") and path.parent.is_dir():  # a name prefix such as paper/xray-
            count = sum(1 for p in path.parent.iterdir() if p.is_file() and p.name.startswith(path.name))
            if count:
                out.append({"path": f".neuroflow/{sub}*", "files": count})
    return out


def build(root: Path, hpc: bool, today: date | None = None) -> dict:
    today = today or date.today()
    if not (root / ".neuroflow").is_dir():
        raise FileNotFoundError(f"no .neuroflow/ folder in {root} - run /neuroflow first")
    cfg = _export().read_config(root)
    attention: list[str] = []
    dossier = {
        "generated": today.isoformat(),
        "project": {k: cfg.get(k) for k in ("project_name", "active_phase", "hive_repo", "target_journal",
                                             "plugin_version")},
        "git": section_git(root, attention),
        "data_roots": section_data(root, cfg, attention),
        "preregistration": section_prereg(root, attention),
        "ethics": section_ethics(root, attention, today),
        "tasks": section_tasks(root, today),
        "integrations": section_integrations(root),
        "hpc": section_hpc() if hpc else [],
        "stays_with_leaver": section_personal(root),
    }
    dossier["attention"] = attention
    return dossier


def to_markdown(d: dict) -> str:
    p = d["project"]
    out = [f"# Handoff dossier - {p.get('project_name') or 'project'}", "",
           f"Generated {d['generated']} by handoff.py (read-only). Key names and paths only - "
           "no credentials, no participant data.", "", "## Needs attention", ""]
    out += [f"- {a}" for a in d["attention"]] or ["- nothing flagged"]
    out += ["", "## Project", "", "| Field | Value |", "|---|---|"]
    out += [f"| {k} | {v} |" for k, v in p.items() if v]
    g = d["git"]
    out += ["", "## Git", ""]
    if g.get("repository"):
        track = f"upstream {g['upstream']}, ahead {g['ahead']}, behind {g['behind']}" if g["upstream"] else "no upstream"
        out += [f"- Branch: {g['branch']} ({track})",
                f"- Uncommitted: {g['changed']} changed, {g['untracked']} untracked; stashes: {g['stashes']}",
                f"- Commits on no remote: {g['unpushed_commits']}",
                f"- Remotes: {', '.join(f'{k} {v}' for k, v in g['remotes'].items()) or 'none'}"]
        if g["branches_without_upstream"]:
            out.append(f"- Local-only branches: {', '.join(g['branches_without_upstream'])}")
    else:
        out.append("- Not a git repository.")
    out += ["", "## Data roots", ""]
    for r in d["data_roots"] or []:
        if r["exists"]:
            more = "+" if r["capped"] else ""
            out.append(f"- {r['path']}: {r['files']}{more} files, {r['bytes'] / 1024 / 1024:.1f} MB"
                       f"{', BIDS' if r['bids'] else ''}")
        else:
            out.append(f"- {r['path']}: missing on this machine")
    if not d["data_roots"]:
        out.append("- no raw_roots in project_config.md - record where the raw data lives")
    pr = d["preregistration"]
    out += ["", "## Preregistration", ""]
    if pr.get("present"):
        out.append(f"- Status: {pr['status']} (set by {pr['set_by'] or 'unknown'}, frozen {pr['frozen_at'] or '-'})")
        out += [f"- {f['path']}: {f['state']}" for f in pr["files"]]
        if pr["verified"] is False:
            out.append("- frozen file hashes were not verified (freeze.py unavailable)")
        out.append(f"- deviations.md: {'present' if pr['deviations_file'] else 'none'}")
    else:
        out.append("- no preregistration/status.md")
    e = d["ethics"]
    out += ["", "## Ethics", ""]
    if e.get("present"):
        out.append(f"- Status: {e['status']}, expires {e['expires'] or '-'}, approval {e['approval_id'] or '-'}, "
                   f"AI processing: {e['ai_processing'] or '-'}")
    else:
        out.append("- no ethics/status.md")
    out += ["", "## Open tasks by owner", ""]
    for owner, tasks in sorted(d["tasks"].items()):
        out.append(f"### {owner}")
        for t in tasks:
            due = f", due {t['due']}" if t["due"] else ""
            flag = " - OVERDUE" if t["overdue"] else ""
            out.append(f"- {t['id']} - {t['title']} ({t['status']}{due}){flag}")
    if not d["tasks"]:
        out.append("- no open tasks")
    out += ["", "## Integrations connected with personal credentials", ""]
    out += [f"- {k}" for k in d["integrations"]] or ["- none in .neuroflow/integrations.json"]
    out.append("- The successor connects their own accounts; rotate any shared secret the leaver knew.")
    if d["hpc"]:
        out += ["", "## HPC jobs", ""] + [f"- {ln}" for ln in d["hpc"]]
    out += ["", "## Stays with the person leaving (never handed over)", ""]
    out += [f"- {s['path']} ({s['files']} files)" for s in d["stays_with_leaver"]]
    out += ["- ~/.neuroflow/ (flowie profile, wellbeing data, private notes, ideas, user.yaml, integrations.json)",
            "- Claude Code's own MCP configuration and credentials"]
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(errors="backslashreplace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="Collect a project handoff dossier (read-only).")
    ap.add_argument("--root", default=".", help="project root (default: current folder)")
    ap.add_argument("--no-hpc", action="store_true", help="skip squeue/qstat")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)
    try:
        dossier = build(Path(args.root).expanduser().resolve(), hpc=not args.no_hpc)
    except (FileNotFoundError, OSError) as e:
        if args.json:
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            print(f"handoff: {e}", file=sys.stderr)
        return 2
    print(json.dumps(dossier, indent=2) if args.json else to_markdown(dossier))
    return 1 if dossier["attention"] else 0


if __name__ == "__main__":
    sys.exit(main())
