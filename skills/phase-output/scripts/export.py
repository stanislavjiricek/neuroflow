#!/usr/bin/env python3
"""Export project memory or the whole project from an explicit file list (phase-output).

The file list is built first, and the sharing-tier rules are applied to it before
anything is copied (neuroflow-core -> Sharing tiers):

- local tier, never exported: .neuroflow/sessions/, .neuroflow/review/,
  .neuroflow/integrations.json, .neuroflow/flowie/, .neuroflow/paper/xray-*,
  .neuroflow/wiki/.pending/
- never exported: .neuroflow/fails/, .neuroflow/finance/
- .neuroflow/ethics/: only documents on the non-identifying allowlist (status.md,
  flow.md, consent-vN.md form versions, protocol*.md, amendment*.md). Every other
  ethics file is held back unless the person has checked it and passes
  --include-ethics PATH.
- credential files anywhere in the tree (.env, *.pem, private SSH keys,
  client_secret*.json, credentials.json, .netrc, .pypirc, .git-credentials,
  integrations.json)

Then the zip archive or folder copy is written and verified against the list.
This script is also the single home of these path rules: pii_scan.py,
history_audit.py and handoff.py import them from here.

Usage:
    python <phase-output skill base dir>/scripts/export.py --scope memory|project|phase
        [--phase NAME] [--format zip|folder] [--dest PATH] [--root DIR]
        [--include-ethics PATH ...] [--list-limit N] [--dry-run] [--json]

Scopes:
    memory   .neuroflow/ (team tier only)
    project  every git-tracked file plus .neuroflow/ (needs a git repository)
    phase    .neuroflow/<phase>/ plus project_config.md and flow.md

Exit codes:
    0  dry run listed, or export written and verified
    1  export written, but verification failed (the output does not match the plan)
    2  refused or failed: no .neuroflow/ under --root, bad arguments, unknown phase,
       no git repository for --scope project, destination inside the exported
       tree or already present, write error

Stdlib only. Python 3.10+.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Sharing-tier path rules (neuroflow-core -> Sharing tiers). One home: other
# phase-output scripts import these.
# ---------------------------------------------------------------------------

# Relative to a .neuroflow/ folder, matched as prefixes ("paper/xray-" covers paper/xray-*).
LOCAL_TIER = ("sessions/", "review/", "integrations.json", "flowie/", "paper/xray-", "wiki/.pending/")
NEVER_EXPORTED = ("fails/", "finance/")
ETHICS_ALLOWLIST = (
    re.compile(r"status\.md"),
    re.compile(r"flow\.md"),
    re.compile(r"consent-v\d+\.md"),
    re.compile(r"protocol[\w.-]*\.md"),
    re.compile(r"amendments?[\w.-]*\.md"),
)
CREDENTIAL_NAMES = {
    "integrations.json",
    "credentials.json",
    ".netrc",
    ".pypirc",
    ".git-credentials",
}
CREDENTIAL_GLOBS = (
    "*.pem",
    "client_secret*.json",
    "id_rsa",
    "id_rsa.*",
    "id_dsa",
    "id_dsa.*",
    "id_ecdsa",
    "id_ecdsa.*",
    "id_ed25519",
    "id_ed25519.*",
    ".env",
    ".env.*",
)
CREDENTIAL_OK = {".env.example", ".env.sample", ".env.template"}

LOCAL_REASON = "local tier - never leaves this machine"
ETHICS_REASON = "ethics/ - not on the non-identifying allowlist (check it, then pass --include-ethics)"
CREDENTIAL_REASON = "credential file"


def norm_rel(rel: str) -> str:
    """Project-relative path in posix form, without a leading './'."""
    rel = rel.replace("\\", "/")
    while rel.startswith("./"):
        rel = rel[2:]
    return rel


def memory_part(rel: str) -> str | None:
    """The part of `rel` below the first `.neuroflow/` folder, or None if outside memory."""
    parts = norm_rel(rel).split("/")
    if ".neuroflow" not in parts[:-1]:
        return None
    i = parts.index(".neuroflow")
    return "/".join(parts[i + 1 :])


def is_local_tier(rel: str) -> bool:
    """True for local-tier memory paths (never committed, exported or uploaded)."""
    sub = memory_part(rel)
    if sub is None:
        return False
    return any(sub == p.rstrip("/") or sub.startswith(p) for p in LOCAL_TIER)


def is_credential(rel: str) -> bool:
    name = norm_rel(rel).rsplit("/", 1)[-1]
    if name in CREDENTIAL_OK:
        return False
    if name in CREDENTIAL_NAMES:
        return True
    return any(fnmatch.fnmatchcase(name, g) for g in CREDENTIAL_GLOBS)


def classify(rel: str, include_ethics: frozenset[str] = frozenset()) -> str | None:
    """Why `rel` may not leave the project, or None if it may be exported."""
    rel = norm_rel(rel)
    sub = memory_part(rel)
    if sub is not None:
        if is_local_tier(rel):
            return LOCAL_REASON
        for prefix in NEVER_EXPORTED:
            if sub == prefix.rstrip("/") or sub.startswith(prefix):
                return f"{prefix} - never exported"
        if sub.startswith("ethics/") and rel not in include_ethics:
            name = sub[len("ethics/") :]
            if "/" in name or not any(p.fullmatch(name) for p in ETHICS_ALLOWLIST):
                return ETHICS_REASON
    if is_credential(rel):
        return CREDENTIAL_REASON
    return None


# ---------------------------------------------------------------------------
# project_config.md reader (frontmatter contract plus the legacy dialects)
# ---------------------------------------------------------------------------

_FM_RE = re.compile(r"\A\ufeff?---[ \t]*\r?\n(.*?)\r?\n(?:---|\.\.\.)[ \t]*(?:\r?\n|\Z)", re.DOTALL)
_TOP_KEY_RE = re.compile(r"^([^\s:#\-][^:]*?)\s*:(?:\s+(.*))?$")
_NESTED_KEY_RE = re.compile(r"^(.+?)\s*:(?:\s+(.*))?$")
_BOLD_RE = re.compile(r"^\s*[-*]?\s*\*\*(?P<k>[^*]+?)\*\*\s*:?\s*(?P<v>.*?)\s*$")
_PLAIN_RE = re.compile(r"^(?P<k>[A-Za-z_][\w-]*)\s*:\s*(?P<v>.+?)\s*$")
_ALIASES = {
    "phase": "active_phase",
    "active_phase": "active_phase",
    "current_phase": "active_phase",
    "project": "project_name",
    "project_name": "project_name",
}


def _unquote(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    return s


def _split_flow(s: str) -> list[str]:
    items, buf, quote = [], [], None
    for ch in s:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            buf.append(ch)
        elif ch == ",":
            items.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    items.append("".join(buf))
    return [i.strip() for i in items if i.strip()]


def _scalar(value: str | None):
    v = (value or "").strip()
    if v[:1] in ("'", '"'):
        end = v.find(v[0], 1)
        return v[1:end] if end > 0 else v[1:]
    hash_at = v.find(" #")
    if hash_at >= 0:
        v = v[:hash_at].rstrip()
    if v.startswith("[") and v.endswith("]"):
        return [_scalar(x) for x in _split_flow(v[1:-1])]
    if v in ("", "~", "null"):
        return None
    return v


def parse_yaml_block(lines: list[str]) -> dict:
    """Parse the small YAML subset neuroflow frontmatter uses (scalars, flow lists,
    one level of block lists or maps). Not a general YAML parser."""
    data: dict = {}
    current: str | None = None
    for raw in lines:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()
        is_item = line == "-" or line.startswith("- ")
        if indent == 0 and not (is_item and current is not None):
            m = _TOP_KEY_RE.match(line)
            if not m:
                current = None
                continue
            key, value = _unquote(m.group(1)), m.group(2)
            parsed = _scalar(value)
            data[key] = parsed
            current = key if parsed is None else None
            continue
        if current is None:
            continue
        if is_item:
            if not isinstance(data.get(current), list):
                data[current] = []
            data[current].append(_scalar(line[1:]))
            continue
        m = _NESTED_KEY_RE.match(line)
        if m:
            if not isinstance(data.get(current), dict):
                data[current] = {}
            data[current][_unquote(m.group(1))] = _scalar(m.group(2))
    return data


def parse_frontmatter(text: str) -> dict | None:
    """The leading `---` YAML block as a dict, or None when the text has none."""
    m = _FM_RE.match(text)
    if not m:
        return None
    return parse_yaml_block(m.group(1).splitlines())


def read_config(root: Path) -> dict:
    """Facts from .neuroflow/project_config.md. The frontmatter wins; `key: value`
    lines and `**Label:** value` lines (legacy dialects) fill the gaps."""
    path = root / ".neuroflow" / "project_config.md"
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    data = dict(parse_frontmatter(text) or {})
    m = _FM_RE.match(text)
    body = text[m.end() :] if m else text
    for line in body.splitlines():
        hit = _BOLD_RE.match(line) or _PLAIN_RE.match(line)
        if not hit:
            continue
        key = re.sub(r"[\s-]+", "_", hit.group("k").strip().rstrip(":").lower())
        key = _ALIASES.get(key, key)
        value = _scalar(hit.group("v"))
        if value is not None and key not in data:
            data[key] = value
    for alias, key in _ALIASES.items():
        if alias in data and key not in data:
            data[key] = data[alias]
    return data


def slugify(name: str | None) -> str:
    slug = re.sub(r"\s+", "-", (name or "").strip().lower())
    slug = re.sub(r"[^\w-]+", "", slug).strip("-_")
    return slug or "project"


# ---------------------------------------------------------------------------
# Planning
# ---------------------------------------------------------------------------


class ExportError(Exception):
    """A refusal or failure that maps to exit code 2."""


@dataclass
class Plan:
    scope: str
    root: Path
    phase: str | None = None
    files: list[tuple[str, int]] = field(default_factory=list)
    held_back: list[tuple[str, str]] = field(default_factory=list)

    @property
    def total_bytes(self) -> int:
        return sum(size for _, size in self.files)


def _rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def walk_files(base: Path, root: Path) -> tuple[list[str], list[tuple[str, str]]]:
    """Regular files under `base` (project-relative). Symlinks are never followed."""
    files: list[str] = []
    skipped: list[tuple[str, str]] = []
    if not base.exists():
        return files, skipped
    if base.is_file():
        return [_rel(base, root)], skipped
    for dirpath, dirnames, filenames in os.walk(base):
        here = Path(dirpath)
        for d in list(dirnames):
            if d == ".git":
                dirnames.remove(d)
            elif (here / d).is_symlink():
                skipped.append((_rel(here / d, root), "symlink - not followed"))
                dirnames.remove(d)
        for f in sorted(filenames):
            p = here / f
            if p.is_symlink():
                skipped.append((_rel(p, root), "symlink - not followed"))
            elif p.is_file():
                files.append(_rel(p, root))
    return files, skipped


def git_tracked(root: Path) -> list[str]:
    try:
        out = subprocess.run(
            ["git", "-c", "core.quotePath=false", "ls-files", "-z"],
            cwd=root,
            capture_output=True,
            check=False,
        )
    except OSError as e:
        raise ExportError(f"--scope project needs git ({e})") from e
    if out.returncode != 0:
        msg = out.stderr.decode("utf-8", "replace").strip()
        raise ExportError(f"--scope project needs a git repository: {msg or 'git ls-files failed'}")
    return [norm_rel(p) for p in out.stdout.decode("utf-8", "replace").split("\0") if p]


def build_plan(root: Path, scope: str, phase: str | None = None,
               include_ethics: frozenset[str] = frozenset()) -> Plan:
    memory = root / ".neuroflow"
    if not memory.is_dir():
        raise ExportError(f"no .neuroflow/ folder in {root} - run /neuroflow first")
    plan = Plan(scope=scope, root=root, phase=phase)
    candidates: list[str] = []
    skipped: list[tuple[str, str]] = []
    if scope == "memory":
        candidates, skipped = walk_files(memory, root)
    elif scope == "phase":
        if not phase or "/" in phase or "\\" in phase or phase in (".", ".."):
            raise ExportError("--scope phase needs --phase NAME (a .neuroflow/ subfolder)")
        folder = memory / phase
        if not folder.is_dir():
            raise ExportError(f"unknown phase: .neuroflow/{phase}/ does not exist")
        candidates, skipped = walk_files(folder, root)
        for name in ("project_config.md", "flow.md"):
            if (memory / name).is_file():
                candidates.append(f".neuroflow/{name}")
    elif scope == "project":
        candidates = git_tracked(root)
        extra, skipped = walk_files(memory, root)
        candidates += extra
    else:
        raise ExportError(f"unknown scope: {scope}")

    seen: set[str] = set()
    for rel in candidates:
        rel = norm_rel(rel)
        if rel in seen:
            continue
        seen.add(rel)
        reason = classify(rel, include_ethics)
        if reason:
            plan.held_back.append((rel, reason))
            continue
        path = root / rel
        if path.is_symlink():
            plan.held_back.append((rel, "symlink - not followed"))
        elif not path.is_file():
            plan.held_back.append((rel, "not a regular file on disk (deleted, submodule or special)"))
        else:
            plan.files.append((rel, path.stat().st_size))
    for rel, reason in skipped:
        if rel not in seen:
            seen.add(rel)
            plan.held_back.append((rel, reason))
    plan.files.sort()
    plan.held_back.sort()
    return plan


# ---------------------------------------------------------------------------
# Destination, writing, verification
# ---------------------------------------------------------------------------


def _resolve(path: Path) -> Path:
    try:
        return path.expanduser().resolve()
    except OSError:
        return path.expanduser().absolute()


def is_within(path: Path, tree: Path) -> bool:
    p = os.path.normcase(str(_resolve(path)))
    t = os.path.normcase(str(_resolve(tree)))
    return p == t or p.startswith(t.rstrip("\\/") + os.sep)


def exported_tree(plan: Plan) -> Path:
    return plan.root if plan.scope == "project" else plan.root / ".neuroflow"


def default_dest(plan: Plan, fmt: str, project_name: str | None, today: str) -> Path:
    slug = slugify(project_name)
    stem = f"output-{plan.phase}-{slug}-{today}" if plan.scope == "phase" else f"output-{slug}-{today}"
    base = plan.root.parent if plan.scope == "project" else plan.root
    return base / (stem + (".zip" if fmt == "zip" else ""))


def check_dest(dest: Path, plan: Plan, fmt: str) -> Path:
    dest = _resolve(dest)
    tree = exported_tree(plan)
    if is_within(dest, tree):
        raise ExportError(
            f"destination {dest} is inside the exported tree ({_resolve(tree)}) - choose a location outside it"
        )
    if fmt == "zip":
        if dest.suffix.lower() != ".zip":
            raise ExportError("a zip destination must end in .zip")
        if dest.exists():
            raise ExportError(f"{dest} already exists - choose a new name (for example add -v2)")
        if not dest.parent.is_dir():
            raise ExportError(f"destination folder {dest.parent} does not exist")
    else:
        if dest.exists() and (not dest.is_dir() or any(dest.iterdir())):
            raise ExportError(f"{dest} exists and is not an empty folder - choose a new name")
        if not dest.parent.is_dir():
            raise ExportError(f"destination folder {dest.parent} does not exist")
    return dest


def write_zip(plan: Plan, dest: Path) -> list[str]:
    top = dest.stem
    partial = dest.with_name(dest.name + ".partial")
    try:
        with zipfile.ZipFile(partial, "w", compression=zipfile.ZIP_DEFLATED, strict_timestamps=False) as z:
            for rel, _ in plan.files:
                z.write(plan.root / rel, arcname=f"{top}/{rel}")
        os.replace(partial, dest)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise
    problems: list[str] = []
    with zipfile.ZipFile(dest) as z:
        names = set(z.namelist())
        bad = z.testzip()
    expected = {f"{top}/{rel}" for rel, _ in plan.files}
    problems += [f"missing from archive: {n}" for n in sorted(expected - names)]
    problems += [f"unexpected in archive: {n}" for n in sorted(names - expected)]
    if bad is not None:
        problems.append(f"CRC check failed: {bad}")
    return problems


def write_folder(plan: Plan, dest: Path) -> list[str]:
    dest.mkdir(parents=True, exist_ok=True)
    for rel, _ in plan.files:
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(plan.root / rel, target)
    problems: list[str] = []
    for rel, size in plan.files:
        target = dest / rel
        if not target.is_file():
            problems.append(f"missing from copy: {rel}")
        elif target.stat().st_size != size:
            problems.append(f"size differs: {rel}")
    copied = {p.relative_to(dest).as_posix() for p in dest.rglob("*") if p.is_file()}
    problems += [f"unexpected in copy: {n}" for n in sorted(copied - {rel for rel, _ in plan.files})]
    return problems


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def human_size(n: int) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{n} B"


def by_folder(plan: Plan) -> list[dict]:
    groups: dict[str, list[int]] = {}
    for rel, size in plan.files:
        folder = rel.rsplit("/", 1)[0] if "/" in rel else "."
        g = groups.setdefault(folder, [0, 0])
        g[0] += 1
        g[1] += size
    return [{"folder": k, "files": v[0], "bytes": v[1]} for k, v in sorted(groups.items())]


def report_dict(plan: Plan, fmt: str, dest: Path | None, dry_run: bool, limit: int,
                problems: list[str] | None) -> dict:
    return {
        "scope": plan.scope,
        "phase": plan.phase,
        "root": str(plan.root),
        "format": fmt,
        "dest": str(dest) if dest else None,
        "dry_run": dry_run,
        "file_count": len(plan.files),
        "total_bytes": plan.total_bytes,
        "by_folder": by_folder(plan),
        "files": [{"path": r, "bytes": s} for r, s in plan.files[:limit]],
        "files_truncated": len(plan.files) > limit,
        "held_back": [{"path": r, "reason": why} for r, why in plan.held_back],
        "verified": None if problems is None else not problems,
        "problems": problems or [],
    }


def print_human(rep: dict) -> None:
    head = "Export plan (dry run)" if rep["dry_run"] else "Export"
    scope = rep["scope"] + (f" ({rep['phase']})" if rep["phase"] else "")
    print(f"{head} - scope: {scope}, format: {rep['format']}")
    print(f"Destination: {rep['dest']}")
    print(f"\nFiles that leave: {rep['file_count']} ({human_size(rep['total_bytes'])})")
    for f in rep["files"]:
        print(f"  {f['path']}  {human_size(f['bytes'])}")
    if rep["files_truncated"]:
        print(f"  ... {rep['file_count'] - len(rep['files'])} more (see by-folder totals)")
        for g in rep["by_folder"]:
            print(f"    {g['folder']}/  {g['files']} files, {human_size(g['bytes'])}")
    print(f"\nHeld back: {len(rep['held_back'])}")
    for h in rep["held_back"]:
        print(f"  {h['path']}  - {h['reason']}")
    if rep["verified"] is True:
        print("\nVerified: the output matches the plan.")
    elif rep["verified"] is False:
        print("\nVERIFICATION FAILED:")
        for p in rep["problems"]:
            print(f"  {p}")


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(errors="backslashreplace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="Export neuroflow project memory or the whole project.")
    ap.add_argument("--scope", required=True, choices=("memory", "project", "phase"))
    ap.add_argument("--phase", help="phase subfolder for --scope phase")
    ap.add_argument("--format", default="zip", choices=("zip", "folder"))
    ap.add_argument("--dest", help="output .zip file or folder (default: see the command)")
    ap.add_argument("--root", default=".", help="project root (default: current folder)")
    ap.add_argument("--include-ethics", action="append", default=[], metavar="PATH",
                    help="an ethics/ file the person checked and found free of participant-identifying content")
    ap.add_argument("--list-limit", type=int, default=200, help="list at most N files (default 200)")
    ap.add_argument("--dry-run", action="store_true", help="list what would leave; write nothing")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    root = _resolve(Path(args.root))
    include_paths = set()
    for p in args.include_ethics:
        path = Path(p)
        if path.is_absolute():
            try:
                include_paths.add(_resolve(path).relative_to(root).as_posix())
            except ValueError:
                continue  # outside the project - nothing to include
        else:
            include_paths.add(norm_rel(p))
    include = frozenset(include_paths)
    try:
        plan = build_plan(root, args.scope, args.phase, include)
        cfg = read_config(root)
        name = cfg.get("project_name")
        dest = Path(args.dest) if args.dest else default_dest(
            plan, args.format, name if isinstance(name, str) else None, date.today().isoformat())
        if args.format == "zip" and dest.suffix.lower() != ".zip":
            dest = dest.with_name(dest.name + ".zip")
        dest = check_dest(dest, plan, args.format)
        problems = None
        if not args.dry_run:
            if not plan.files:
                raise ExportError("nothing to export - every file in this scope is held back")
            problems = write_zip(plan, dest) if args.format == "zip" else write_folder(plan, dest)
    except ExportError as e:
        if args.json:
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            print(f"export: {e}", file=sys.stderr)
        return 2
    except OSError as e:
        if args.json:
            print(json.dumps({"error": f"write failed: {e}"}, indent=2))
        else:
            print(f"export: write failed: {e}", file=sys.stderr)
        return 2

    rep = report_dict(plan, args.format, dest, args.dry_run, max(args.list_limit, 0), problems)
    if args.json:
        print(json.dumps(rep, indent=2))
    else:
        print_human(rep)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
