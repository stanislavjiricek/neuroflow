#!/usr/bin/env python3
"""Turn the open action items of a neuroflow meeting note into task files.

Reads the meeting's action-items section, parses each unchecked checkbox

    - [ ] Description -> @owner due:YYYY-MM-DD [level/column]

(the arrow may be "->" or the Unicode arrow; owner, due and the [level/column]
annotation are optional; [level] or [column] alone also work) and plans one
task file per item in the /tasks schema:

    <level root>/tasks/<column>/<slug>.md

Dry run by default: prints the plan and writes nothing. With --write it
creates the task files, adds them to the meeting's `linked_tasks` and stamps
`closed:` in the meeting frontmatter. Items already converted from this
meeting are reported as "exists" and never duplicated.

It never sends invites or emails, never pushes, and never touches the network.

Level roots: project = <project root>/.neuroflow, flowie = ~/.neuroflow/flowie,
hive = the hive cache folder (pass --hive-root). The meeting's own level root
is derived from its path (<root>/meetings/<file>).

Exit codes: 0 = plan is clean (or written); 1 = findings (items that need a
person's decision; with --write nothing is written); 2 = usage or runtime error.
"""

import argparse
import codecs
import json
import os
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path

LEVELS = ("project", "flowie", "hive")
DEFAULT_COLUMNS = ("inbox", "ready", "active", "review", "meeting", "done", "archive")
DEFAULT_LEVEL = "project"
DEFAULT_COLUMN = "inbox"
SLUG_MAX = 40

BULLET = r"(?:[-*+]|\d+[.)])"
CHECKBOX_RE = re.compile(rf"^\s*{BULLET}\s+\[([ xX])\]\s*(.*?)\s*$")
PLAIN_BULLET_RE = re.compile(rf"^\s*{BULLET}\s+(?!\[[ xX]\])(\S.*?)\s*$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
ANNOT_RE = re.compile(r"\[\s*([A-Za-z][\w-]*)\s*(?:/\s*([A-Za-z][\w-]*)\s*)?\]\s*$")
DUE_RE = re.compile(r"(?<!\S)due:\s*(\S+)", re.IGNORECASE)
OWNER_RE = re.compile(r"\s*(?:→|->)\s*@([A-Za-z0-9][\w.-]*)\s*$")
FM_KEY_RE = re.compile(r"^([A-Za-z_][\w-]*):\s*(.*?)\s*$")
SETUP_HINT = {
    "project": "run /neuroflow first",
    "flowie": "run /flowie first",
    "hive": "run /hive --init first",
}


class UsageError(Exception):
    """Bad input or an unreadable/unwritable file (exit 2)."""


@dataclass
class Item:
    line: int
    text: str
    title: str = ""
    level: str = ""
    column: str = ""
    owner: str | None = None
    due: str | None = None
    slug: str = ""
    path: str = ""
    action: str = "create"  # create | exists | error
    message: str = ""


@dataclass
class Plan:
    meeting: str
    meeting_level: str
    source: str
    write: bool
    items: list[Item] = field(default_factory=list)
    skipped: list[dict] = field(default_factory=list)
    linked_tasks: list[str] = field(default_factory=list)
    created: list[str] = field(default_factory=list)
    meeting_updated: bool = False

    @property
    def errors(self) -> int:
        return sum(1 for i in self.items if i.action == "error")


@dataclass
class Meeting:
    path: Path
    lines: list[str]
    newline: str
    bom: bool
    level: str
    roots: dict[str, Path | None]
    project_root: Path


# --- small parsers -----------------------------------------------------------


def split_comment(value: str) -> tuple[str, str]:
    """Split a YAML scalar into (value, trailing '# comment'); a '#' inside quotes is kept."""
    quote = None
    for idx, ch in enumerate(value):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (idx == 0 or value[idx - 1] in " \t"):
            return value[:idx].strip(), value[idx:]
    return value.strip(), ""


def unquote(value: str) -> str:
    value = split_comment(value)[0]
    if len(value) >= 2 and value[0] == value[-1] == '"':
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value[1:-1]
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    return value


def split_frontmatter(lines: list[str]) -> tuple[int, int] | None:
    """Return (start, end) line indexes of the frontmatter delimiters, or None."""
    if not lines or lines[0].strip() != "---":
        return None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return 0, idx
    return None


def frontmatter_scalars(lines: list[str]) -> dict[str, str]:
    bounds = split_frontmatter(lines)
    if not bounds:
        return {}
    out: dict[str, str] = {}
    for line in lines[bounds[0] + 1 : bounds[1]]:
        m = FM_KEY_RE.match(line)
        if m and not line.startswith((" ", "\t")):
            out[m.group(1)] = unquote(m.group(2)) if m.group(2) else ""
    return out


def slugify(title: str) -> str:
    text = unicodedata.normalize("NFKD", title)
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    slug = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    if len(slug) > SLUG_MAX:
        cut = slug[:SLUG_MAX]
        if "-" in cut[SLUG_MAX // 2 :]:
            cut = cut[: cut.rfind("-")]
        slug = cut.strip("-")
    return slug or "task"


def read_columns(root: Path) -> tuple[str, ...]:
    """Column ids from <root>/tasks/config.json, or the default set."""
    try:
        data = json.loads((root / "tasks" / "config.json").read_text(encoding="utf-8"))
        ids = tuple(
            str(c["id"]).lower() for c in data.get("columns", []) if c.get("id")
        )
        return ids or DEFAULT_COLUMNS
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return DEFAULT_COLUMNS


def existing_tasks(root: Path) -> list[dict]:
    """Every task file at a level: slug, column, title and source."""
    tasks_dir = root / "tasks"
    found: list[dict] = []
    if not tasks_dir.is_dir():
        return found
    for column_dir in sorted(p for p in tasks_dir.iterdir() if p.is_dir()):
        for task in sorted(column_dir.glob("*.md")):
            try:
                lines = task.read_text(
                    encoding="utf-8-sig", errors="replace"
                ).splitlines()
            except OSError:
                continue
            fm = frontmatter_scalars(lines)
            found.append(
                {
                    "slug": task.stem,
                    "column": column_dir.name,
                    "title": fm.get("title", ""),
                    "source": fm.get("source", ""),
                }
            )
    return found


def project_name(project_root: Path) -> str:
    """project_name from project_config.md (frontmatter or legacy line), else the folder name."""
    config = project_root / ".neuroflow" / "project_config.md"
    try:
        for line in config.read_text(
            encoding="utf-8-sig", errors="replace"
        ).splitlines():
            m = re.match(
                r"^\s*(?:\*\*)?project_name(?:\*\*)?:\s*(?:\*\*)?\s*(.+?)\s*$", line
            )
            if m:
                return unquote(m.group(1))
    except OSError:
        pass
    return project_root.resolve().name


# --- loading -----------------------------------------------------------------


def infer_level(path: Path, fm: dict[str, str]) -> str:
    level = fm.get("level", "").strip().lower()
    if level in LEVELS:
        return level
    parts = [p.lower() for p in path.parts]
    if len(parts) >= 3:
        if parts[-3] == ".neuroflow":
            return "project"
        if parts[-3] == "flowie":
            return "flowie"
        if len(parts) >= 4 and parts[-4] == "hives":
            return "hive"
    return DEFAULT_LEVEL


def load_meeting(args: argparse.Namespace) -> Meeting:
    path = Path(args.meeting).resolve()
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise UsageError(
            f"cannot read meeting file {args.meeting}: {exc.strerror or exc}"
        ) from exc
    bom = raw.startswith(codecs.BOM_UTF8)
    newline = "\r\n" if b"\r\n" in raw else "\n"
    lines = raw.decode("utf-8-sig", errors="replace").splitlines()
    level = infer_level(path, frontmatter_scalars(lines))
    own_root = path.parent.parent
    if args.project_root:
        project_root = Path(args.project_root).expanduser().resolve()
    elif level == "project" and own_root.name.lower() == ".neuroflow":
        project_root = own_root.parent
    else:
        project_root = Path.cwd()
    roots: dict[str, Path | None] = {
        "project": project_root / ".neuroflow",
        "flowie": Path(args.flowie_root).expanduser().resolve()
        if args.flowie_root
        else Path.home() / ".neuroflow" / "flowie",
        "hive": Path(args.hive_root).expanduser().resolve() if args.hive_root else None,
    }
    if level == "flowie" and not args.flowie_root:
        roots["flowie"] = own_root
    if level == "hive" and not args.hive_root:
        roots["hive"] = own_root
    return Meeting(path, lines, newline, bom, level, roots, project_root)


def source_ref(meeting: Meeting) -> str:
    root = meeting.roots.get(meeting.level)
    if root is not None:
        try:
            return (
                f"{meeting.level}:{meeting.path.relative_to(root.resolve()).as_posix()}"
            )
        except ValueError:
            pass
    return f"{meeting.level}:{meeting.path.name}"


# --- planning ----------------------------------------------------------------


def parse_item(item: Item, columns_of) -> None:
    text = item.text
    level = column = None
    m = ANNOT_RE.search(text)
    if m:
        first, second = m.group(1).lower(), (m.group(2) or "").lower()
        text = text[: m.start()].rstrip()
        if second:
            level, column = first, second
        elif first in LEVELS:
            level = first
        elif first in columns_of(DEFAULT_LEVEL) or first in DEFAULT_COLUMNS:
            column = first
        else:
            item.action, item.message = (
                "error",
                f"unknown level or column '{m.group(1)}'",
            )
            return
    due_m = DUE_RE.search(text)
    if due_m:
        raw_due = due_m.group(1).rstrip(".,;")
        try:
            item.due = date.fromisoformat(raw_due).isoformat()
        except ValueError:
            item.action, item.message = (
                "error",
                f"due date '{raw_due}' is not YYYY-MM-DD",
            )
            return
        text = re.sub(
            r"\s{2,}", " ", (text[: due_m.start()] + text[due_m.end() :]).strip()
        )
    owner_m = OWNER_RE.search(text)
    if owner_m:
        item.owner = owner_m.group(1)
        text = text[: owner_m.start()].rstrip()
    item.title = text.strip().rstrip(" -–—:;,").strip()
    item.level = level or DEFAULT_LEVEL
    if item.level not in LEVELS:
        item.action, item.message = (
            "error",
            f"unknown level '{item.level}' (use project, flowie or hive)",
        )
        return
    item.column = column or DEFAULT_COLUMN
    if item.column not in columns_of(item.level):
        item.action = "error"
        item.message = f"unknown column '{item.column}' for {item.level} (use {', '.join(columns_of(item.level))})"
        return
    if not item.title:
        item.action, item.message = "error", "empty action item"


def find_section(lines: list[str], heading: str) -> tuple[int, int] | None:
    want = heading.strip().rstrip(":").lower()
    for idx, line in enumerate(lines):
        m = HEADING_RE.match(line)
        if m and m.group(2).strip().rstrip(":").lower() == want:
            depth = len(m.group(1))
            for end in range(idx + 1, len(lines)):
                h = HEADING_RE.match(lines[end])
                if h and len(h.group(1)) <= depth:
                    return idx + 1, end
            return idx + 1, len(lines)
    return None


def build_plan(args: argparse.Namespace, meeting: Meeting) -> Plan:
    plan = Plan(
        meeting=args.meeting,
        meeting_level=meeting.level,
        source=source_ref(meeting),
        write=args.write,
    )
    columns_cache: dict[str, tuple[str, ...]] = {}

    def columns_of(lvl: str) -> tuple[str, ...]:
        if lvl not in columns_cache:
            root = meeting.roots.get(lvl)
            columns_cache[lvl] = (
                read_columns(root)
                if root is not None and root.is_dir()
                else DEFAULT_COLUMNS
            )
        return columns_cache[lvl]

    section = find_section(meeting.lines, args.section)
    if section is None:
        plan.items.append(
            Item(
                line=0,
                text="",
                action="error",
                message=f"no '{args.section}' heading found (use --section for another heading)",
            )
        )
        return plan
    for idx in range(*section):
        line = meeting.lines[idx]
        cb = CHECKBOX_RE.match(line)
        if cb:
            if cb.group(1).lower() == "x":
                plan.skipped.append(
                    {"line": idx + 1, "text": cb.group(2), "reason": "checked"}
                )
                continue
            item = Item(line=idx + 1, text=cb.group(2))
            parse_item(item, columns_of)
            plan.items.append(item)
            continue
        bullet = PLAIN_BULLET_RE.match(line)
        if bullet:
            plan.skipped.append(
                {"line": idx + 1, "text": bullet.group(1), "reason": "not a checkbox"}
            )

    existing: dict[str, list[dict]] = {}
    taken: dict[str, set[str]] = {}
    claimed: set[tuple[str, str]] = set()
    ready: list[Item] = []
    for item in plan.items:
        if item.action == "error":
            continue
        root = meeting.roots.get(item.level)
        if root is None:
            item.action, item.message = (
                "error",
                "no hive root - pass --hive-root ~/.neuroflow/hives/<org-repo>",
            )
            continue
        if not root.is_dir():
            item.action = "error"
            item.message = f"{item.level} level not set up ({root} not found) - {SETUP_HINT[item.level]} or pick another level"
            continue
        if item.level not in existing:
            existing[item.level] = [
                t for t in existing_tasks(root) if t["source"] == plan.source
            ]
            taken[item.level] = {t["slug"] for t in existing_tasks(root)}
        ready.append(item)

    # Already converted from this meeting? Match by title first, then by slug.
    for by_title in (True, False):
        for item in ready:
            if item.action == "exists":
                continue
            base = slugify(item.title)
            for task in existing[item.level]:
                key = (item.level, task["slug"])
                if key in claimed:
                    continue
                same = (
                    task["title"] == item.title
                    if by_title
                    else re.fullmatch(re.escape(base) + r"(-\d+)?", task["slug"])
                )
                if same:
                    claimed.add(key)
                    item.action, item.slug, item.column = (
                        "exists",
                        task["slug"],
                        task["column"],
                    )
                    item.message = "already created from this meeting"
                    break

    for item in ready:
        root = meeting.roots[item.level]
        if item.action == "create":
            base = slugify(item.title)
            slug, n = base, 2
            while slug in taken[item.level]:
                slug, n = f"{base}-{n}", n + 1
            taken[item.level].add(slug)
            item.slug = slug
        item.path = str(root / "tasks" / item.column / f"{item.slug}.md")
        ref = f"{item.level}:{item.slug}"
        if ref not in plan.linked_tasks:
            plan.linked_tasks.append(ref)
    return plan


# --- writing -----------------------------------------------------------------


def task_text(
    item: Item, plan: Plan, meeting_fm: dict[str, str], today: str, project: str
) -> str:
    out = [
        "---",
        f"title: {json.dumps(item.title, ensure_ascii=False)}",
        f"status: {item.column}",
    ]
    if item.owner:
        out.append(f"owner: {item.owner}")
    if item.due:
        out.append(f"due: {item.due}")
    out += [f"created: {today}", f"updated: {today}"]
    if item.level != "project":
        out.append(f"project: {json.dumps(project, ensure_ascii=False)}")
    out += [f"source: {plan.source}", "---", ""]
    title = meeting_fm.get("title") or Path(plan.meeting).stem
    when = (meeting_fm.get("date") or "")[:10]
    out.append(
        f"From meeting {json.dumps(title, ensure_ascii=False)}"
        + (f" ({when})." if when else ".")
    )
    return "\n".join(out) + "\n"


def parse_list_value(value: str) -> list[str]:
    value = split_comment(value)[0]
    if not value:
        return []
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        return [unquote(v) for v in inner.split(",") if v.strip()] if inner else []
    return [unquote(value)]


def update_meeting(lines: list[str], refs: list[str], today: str) -> list[str]:
    """Merge refs into linked_tasks (flow style) and stamp closed: if empty or missing."""
    lines = list(lines)
    bounds = split_frontmatter(lines)
    if not bounds:
        return [
            "---",
            f"linked_tasks: [{', '.join(refs)}]",
            f"closed: {today}",
            "---",
            *lines,
        ]
    start, end = bounds
    current: list[str] = []
    for idx in range(start + 1, end):
        m = FM_KEY_RE.match(lines[idx])
        if (
            m
            and m.group(1) == "linked_tasks"
            and not lines[idx].startswith((" ", "\t"))
        ):
            value, comment = split_comment(m.group(2))
            current = parse_list_value(value)
            stop = idx + 1
            if not value:
                while stop < end and re.match(r"^\s+-\s+", lines[stop]):
                    current.append(unquote(re.sub(r"^\s+-\s+", "", lines[stop])))
                    stop += 1
            merged = list(dict.fromkeys([*current, *refs]))
            lines[idx:stop] = [
                f"linked_tasks: [{', '.join(merged)}]"
                + (f"  {comment}" if comment else "")
            ]
            end -= stop - idx - 1
            break
    else:
        lines.insert(end, f"linked_tasks: [{', '.join(refs)}]")
        end += 1
    for idx in range(start + 1, end):
        m = FM_KEY_RE.match(lines[idx])
        if m and m.group(1) == "closed" and not lines[idx].startswith((" ", "\t")):
            value, comment = split_comment(m.group(2))
            if not unquote(value):
                lines[idx] = f"closed: {today}" + (f"  {comment}" if comment else "")
            break
    else:
        lines.insert(end, f"closed: {today}")
    return lines


def write_plan(plan: Plan, meeting: Meeting, today: str, project: str) -> None:
    meeting_fm = frontmatter_scalars(meeting.lines)
    for item in plan.items:
        if item.action != "create":
            continue
        path = Path(item.path)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8", newline="\n") as fh:
                fh.write(task_text(item, plan, meeting_fm, today, project))
        except FileExistsError as exc:
            raise UsageError(f"{path} appeared while writing - run again") from exc
        except OSError as exc:
            raise UsageError(f"cannot write {path}: {exc.strerror or exc}") from exc
        plan.created.append(str(path))
    text = (
        meeting.newline.join(update_meeting(meeting.lines, plan.linked_tasks, today))
        + meeting.newline
    )
    data = (codecs.BOM_UTF8 if meeting.bom else b"") + text.encode("utf-8")
    try:
        meeting.path.write_bytes(data)
    except OSError as exc:
        raise UsageError(
            f"cannot update {plan.meeting}: {exc.strerror or exc}"
        ) from exc
    plan.meeting_updated = True


# --- output ------------------------------------------------------------------


def display(path: str) -> str:
    try:
        return os.path.relpath(path)
    except ValueError:
        return path


def render_text(plan: Plan) -> str:
    out = [f"Meeting: {display(plan.meeting)} ({plan.meeting_level})"]
    out.append(
        "Written:" if plan.meeting_updated else "Plan (dry run - nothing written):"
    )
    for item in plan.items:
        if item.action == "error":
            where = f"line {item.line}: " if item.line else ""
            snippet = f'  "{item.text}"' if item.text else ""
            out.append(f"  ERROR   {where}{item.message}{snippet}")
            continue
        extra = ", ".join(
            x
            for x in (
                f"owner @{item.owner}" if item.owner else "",
                f"due {item.due}" if item.due else "",
            )
            if x
        )
        label = (
            "created"
            if item.action == "create" and plan.meeting_updated
            else item.action
        )
        where = f"{item.level}/{item.column}"
        out.append(
            f"  {label:<7} {where:<16} {item.slug:<28} {item.title}"
            + (f"  [{extra}]" if extra else "")
        )
    if not plan.items:
        out.append("  (no open action items)")
    if plan.skipped:
        checked = sum(1 for s in plan.skipped if s["reason"] == "checked")
        plain = [s for s in plan.skipped if s["reason"] == "not a checkbox"]
        out.append(f"Skipped: {checked} checked, {len(plain)} not a checkbox")
        out += [f"  line {s['line']}: {s['text']}" for s in plain]
    to_create = sum(1 for i in plan.items if i.action == "create")
    if plan.errors:
        out.append(
            f"{plan.errors} error(s) - fix the meeting note or ask the person, then run again. Nothing was written."
        )
    elif plan.meeting_updated:
        out.append(
            f"Created {len(plan.created)} task file(s); linked_tasks and closed: updated in the meeting file."
        )
    else:
        out.append(
            f"Run again with --write to create {to_create} task file(s) and update linked_tasks."
        )
    return "\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="meeting_close.py",
        description="Turn a meeting note's open action items into /tasks task files. Dry run unless --write. "
        "Never sends invites or emails and never pushes.",
    )
    ap.add_argument(
        "meeting",
        help="path to the meeting file (e.g. .neuroflow/meetings/2026-04-20-weekly-lab.md)",
    )
    ap.add_argument(
        "--project-root",
        help="project root holding .neuroflow/ (default: derived from a project meeting, else cwd)",
    )
    ap.add_argument("--flowie-root", help="flowie repo (default: ~/.neuroflow/flowie)")
    ap.add_argument(
        "--hive-root",
        help="hive cache folder (~/.neuroflow/hives/<org-repo>); needed for [hive/...] items",
    )
    ap.add_argument(
        "--project",
        help="project name for flowie/hive tasks (default: project_name from project_config.md)",
    )
    ap.add_argument(
        "--section",
        default="Action Items",
        help="heading of the action-items section (default: %(default)s)",
    )
    ap.add_argument(
        "--today",
        help="date to stamp as created/updated/closed (YYYY-MM-DD, default: today)",
    )
    ap.add_argument(
        "--write",
        action="store_true",
        help="create the task files and update the meeting (default: dry run)",
    )
    ap.add_argument("--json", action="store_true", help="print the plan as JSON")
    return ap


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    try:
        today = (
            date.fromisoformat(args.today).isoformat()
            if args.today
            else datetime.now().astimezone().date().isoformat()
        )
    except ValueError:
        print(
            f"meeting_close: --today '{args.today}' is not YYYY-MM-DD", file=sys.stderr
        )
        return 2
    try:
        meeting = load_meeting(args)
        plan = build_plan(args, meeting)
        if args.write and plan.errors == 0:
            write_plan(
                plan, meeting, today, args.project or project_name(meeting.project_root)
            )
    except UsageError as exc:
        print(f"meeting_close: {exc}", file=sys.stderr)
        return 2
    if args.json:
        payload = asdict(plan)
        payload["errors"] = plan.errors
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(render_text(plan))
    return 1 if plan.errors else 0


if __name__ == "__main__":
    sys.exit(main())
