#!/usr/bin/env python3
"""The claude.ai workbench: one person's private page over their flowie, hives and projects (neuroflow-core →
Workbench snapshot). Git stays the only store. This script exports a derived snapshot for the page's owner-only
database, checks the clicks the page queued (intents) against git, and moves the accepted ones in the task files the
way /tasks moves them. It never commits, pushes or uploads: the prose runs the commits and the Artifact and
ArtifactData tools, after the person's yes.

subcommands:
  sources [--markdown]        what reaches claude.ai, per source (one allowlist: the export, the preview and the docs)
  levels                      the levels this machine can mirror: key, the team's opt-in, the person's consent
  export --out DIR            the snapshot documents of the mirrored levels and a preview; with --remote DIR (the
                              ArtifactData listing of data/users/me) also the refresh guard's verdicts and the batch
                              writes; --outcomes PLAN adds the outcomes of an apply run; --fetch fetches each repo first
  pickup --intents DIR        which queued intents this session may claim, and the claim batch (pinned)
  validate --intents DIR --out PLAN   one verdict per claimed intent and the plan of task-file changes, per level
  apply --plan PLAN --level KEY       edit and move the planned task files of one level (git mv) and stage them in
                              a flowie or hive clone; prints the commit to run, with its Neuroflow-Intent trailers
  pending --intents DIR [--plan PLAN] write ~/.neuroflow/workbench/pending.json (the mod's board and band read it)
  gc --intents DIR --remote DIR       deletes: finished intents older than --days, orphaned parts, the levels whose
                              team no longer allows them and the ones --purge KEY names (the person took them off);
                              never a level only because this machine lacks it. --remote lists every level's parts
  record [--set KEY=VALUE ...] [--prefs FILE]   the workbench record: the flowie's workbench.json, else user.yaml
  stage --out DIR             the page: template plus logic module, with its hashes, capabilities and contract
  page --check FILE           whether a page read back from claude.ai is still the one neuroflow published
  check                       the template's safety rules (no innerHTML, no external script, a version tag)
  key [--hive DIR | --project DIR]    the level key of a hive clone or a project (default: the flowie's)
  fixtures --out DIR          write the golden snapshot fixtures both test suites read
  --json for machine-readable output; --home DIR and --now ISO stand in for the home folder and the clock (tests)

exit codes: 0 done or clean · 1 findings (items held back, levels skipped or asked, intents not accepted, actions
not applied, deletes planned, template findings, a page that changed) · 2 usage or runtime error
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN = HERE.parents[2]
ASSETS = HERE.parent / "assets" / "workbench"
TEMPLATE = ASSETS / "workbench.html"
MODULE = ASSETS / "workbench.mjs"
PII_SCAN = PLUGIN / "skills" / "phase-output" / "scripts" / "pii_scan.py"
LOCAL_PATHS = PLUGIN / "skills" / "phase-flowie" / "scripts" / "local_paths.py"

SNAP_SCHEMA = 1
INTENT_SCHEMA = 1
PREFS_SCHEMA = 1
PART_MAX = 200_000          # bytes of one part document (the store takes 256 KiB)
BODY_MAX = 150_000          # bytes of one wiki page body
NOTES_MAX = 1000            # characters of a card's notes and of a registry description
TEXT_MAX = 40_000           # bytes of a panel text (ideas, hive.md): two of them and the lists fit the core part
LIST_MAX = 200              # entries of a panel list (notes, meetings, an erratum's rows): the newest
BATCH_WRITES = 50
BATCH_BYTES = 900_000       # under the batch limit of 1 MiB
SIZE_WARN = 8_000_000       # bytes of one export: past this the page is slow to load
CLAIM_TTL = timedelta(minutes=30)
GC_DAYS = 7
LEDGER_DAYS = 60
OPS = ("move", "add", "cancel")
CAPABILITIES = {"db": {"rules": [{"path": "", "read": "owner", "write": "owner"}]}, "user": {}}
TITLE = "neuroflow workbench"
ICON = "board"
DESCRIPTION = ("Your private neuroflow workbench: the task boards, project lists and wikis of your flowie, hives and "
               "projects, mirrored from git; moves go back through Claude Code.")
POLICIES = ("allow", "allow-names", "forbid")
PERSONAL = {"workbench", "workbench_levels", "workbench_index_only", "workbench_machine", "workbench_account",
            "workbench_records"}
HANDLE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")
SEGMENT = re.compile(r"^(?!\.\.?$)[A-Za-z0-9_\-.~:@+]{1,200}$")
INTENT_ID = re.compile(r"^i-[0-9a-z]{1,16}-[0-9a-z]{4,24}$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SHA = re.compile(r"^[0-9a-f]{64}$")
TRAILER = "Neuroflow-Intent"
BEGIN, END = "<!-- neuroflow-workbench:begin -->", "<!-- neuroflow-workbench:end -->"
LOGIC_MARK = "/* @@WORKBENCH_LOGIC@@ */"


class UsageError(Exception):
    pass


def utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def _load(name: str, path: Path):
    """A sibling script, imported by path (one home for each rule it holds)."""
    if name in sys.modules:
        return sys.modules[name]
    if not path.is_file():
        raise UsageError(f"{path} is missing: the workbench needs it ({path.name})")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pj = _load("_nf_core_projects", HERE / "projects.py")        # the board reader, the registry, repository keys
mg = _load("_nf_core_migrate", HERE / "migrate.py")          # slugs, phases, frontmatter lists, YAML scalars


def pii():
    """pii_scan.py: the one home of the personal-data and secret patterns (imported as header_scan.py does)."""
    return _load("_nf_phase_output_pii_scan", PII_SCAN)


def local_paths():
    """local_paths.py: the one home of the machine-local path patterns (phase-flowie → Write rules)."""
    return _load("_nf_phase_flowie_local_paths", LOCAL_PATHS)


# ── small helpers ───────────────────────────────────────────────────────────────────────────────

def read_text(path: Path) -> str | None:
    return pj.read_text(path)


def parse_time(value) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        return None
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def canonical(doc) -> str:
    return json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def doc_bytes(doc) -> int:
    return len(canonical(doc).encode("utf-8"))


def with_hash(doc: dict) -> dict:
    """A part with its own sha256 (of its canonical JSON without that field): the page compares it with the meta."""
    body = {key: value for key, value in doc.items() if key != "sha256"}
    return {**body, "sha256": hashlib.sha256(canonical(body).encode("utf-8")).hexdigest()}


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True) + "\n").encode("utf-8"))


def write_doc(path: Path, doc) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(doc).encode("utf-8"))


def split_fm(text: str) -> tuple[dict, str]:
    """(frontmatter keys, body) of a markdown file; ({}, text) without a frontmatter."""
    lines = text.lstrip("\ufeff").replace("\r\n", "\n").split("\n")
    if lines and lines[0].strip() == "---":
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
        if end is not None:
            return pj.frontmatter("\n".join(lines[:end + 1])), "\n".join(lines[end + 1:])
    return {}, "\n".join(lines)


def scalar(fm: dict, key: str) -> str | None:
    value = fm.get(key)
    return str(value).strip() if value not in (None, [], "") and not isinstance(value, list) else None


def handle_of(value) -> str | None:
    text = str(value or "").strip().lstrip("@")
    return text if HANDLE.match(text) else None


# ── the person's layer: ~/.neuroflow/user.yaml ──────────────────────────────────────────────────

def user_yaml_path(home: Path) -> Path:
    return home / ".neuroflow" / "user.yaml"


def _yaml_value(raw: str):
    raw = raw.strip()
    if raw[:1] in "[{":
        for candidate in (raw, re.split(r"\s+#", raw, maxsplit=1)[0]):
            try:
                return json.loads(candidate)
            except ValueError:
                continue
        inner = re.split(r"\s+#", raw, maxsplit=1)[0].strip()
        if inner.startswith("[") and inner.endswith("]"):
            return [mg.clean_scalar(part) for part in inner[1:-1].split(",") if mg.clean_scalar(part)]
    return mg.clean_scalar(raw)


def read_user_yaml(home: Path) -> dict:
    """The top-level keys of user.yaml this script needs: scalars, inline or JSON lists and maps, block lists."""
    text = (read_text(user_yaml_path(home)) or "").replace("\r\n", "\n")
    lines = text.split("\n")
    out: dict = {}
    i = 0
    while i < len(lines):
        match = re.match(r"^([A-Za-z_][\w-]*):(?:[ \t]+(.*?))?[ \t]*$", lines[i])
        if not match:
            i += 1
            continue
        key, raw = match.group(1), match.group(2) or ""
        if raw.strip() == "" or raw.strip().startswith("#"):
            items, j = [], i + 1
            while j < len(lines) and lines[j].strip() and (lines[j][0] in " \t-"):
                item = re.match(r"^\s*-\s+(.*?)\s*$", lines[j])
                if item:
                    items.append(mg.clean_scalar(item.group(1)))
                j += 1
            out[key] = items
            i = j
            continue
        out[key] = _yaml_value(raw)
        i += 1
    return out


def set_user_yaml(home: Path, key: str, value) -> bool:
    """Writes one top-level key, keeping every other line (merge, never replace). Lists and maps go in as JSON, which
    is YAML too. Returns whether the file changed."""
    path = user_yaml_path(home)
    original = read_text(path) or ""
    newline = "\r\n" if "\r\n" in original else "\n"
    rendered = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    line = f"{key}: {rendered}"
    lines = original.replace("\r\n", "\n").split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    for i, current in enumerate(lines):
        if re.match(rf"^{re.escape(key)}:(?:\s|$)", current):
            j = i + 1
            while j < len(lines) and lines[j].strip() and lines[j][0] in " \t-":
                j += 1
            new = lines[:i] + [line] + lines[j:]
            break
    else:
        new = lines + [line]
    text = "\n".join(new) + "\n"
    if text == original.replace("\r\n", "\n"):
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.replace("\n", newline).encode("utf-8"))
    return True


def on(value) -> bool:
    return str(value).strip().lower() in ("on", "yes", "true", "1")


def as_keys(value) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [part.strip() for part in value.split(",") if part.strip()]
    return []


# ── level keys ──────────────────────────────────────────────────────────────────────────────────

# Keys use `+` between their parts: the store allows it, and unlike `:` it is a valid file-name character on every
# system — an ArtifactData listing saved with out_dir names files and folders after document ids. Keys are lower case,
# so a case-insensitive file system cannot fold two levels into one file.

def escape_segment(text: str) -> str:
    """A card id in key characters: lower-case letters, digits and `_ . -` stay, every other byte becomes `~hh`."""
    return "".join(ch if re.fullmatch(r"[a-z0-9_.\-]", ch) else "".join(f"~{byte:02x}" for byte in ch.encode("utf-8"))
                   for ch in text.lower())


def project_key(card: str | None, origin: str | None) -> str | None:
    """`project+{card id}` (escaped), else `project+{host}+{owner}+{repo}` from the origin remote; None with neither.
    An escaped id never holds a raw `+`, so the two forms cannot meet; an id with capitals gets a short hash of itself,
    so ids that differ only in case stay two levels."""
    if card:
        key = "project+" + escape_segment(card) + (f"~~{hashlib.sha256(card.encode('utf-8')).hexdigest()[:8]}" if card != card.lower() else "")
        return key if len(key.encode("utf-8")) <= 200 else "project+~~" + hashlib.sha256(card.encode("utf-8")).hexdigest()[:48]
    parsed = pj.repo_key(origin or "")
    return "project+" + parsed.replace("/", "+") if parsed else None


def hive_key(origin: str | None) -> str | None:
    """`hive+{org}+{repo}` from the clone's origin remote, never its folder name; None without an origin."""
    parsed = pj.repo_key(origin or "")
    if not parsed:
        return None
    _, owner, repo = parsed.split("/")
    return f"hive+{owner}+{repo}"


def valid_level_key(key) -> bool:
    return isinstance(key, str) and key not in ("prefs", "inbox") and bool(re.fullmatch(r"[a-z0-9_\-.~+]{1,200}", key)) and (
        key == "flowie" or key.startswith(("hive+", "project+")))


def key_file(key: str) -> str:
    return key  # keys are already safe file names (see above)


# ── database paths (one home: the page builds the same ones from data/users/{its own id}) ──────────

def meta_collection(user: str = "me") -> str:
    return f"data/users/{user}"


def parts_collection(key: str, user: str = "me") -> str:
    return f"data/users/{user}/{key}/parts"


def intents_collection(user: str = "me") -> str:
    return f"data/users/{user}/inbox/intents"


PREFS_DOC = "prefs"


def segments(path: str) -> int:
    return len(path.split("/"))


def is_collection(path: str) -> bool:
    return segments(path) % 2 == 1


def is_document(path: str) -> bool:
    return segments(path) % 2 == 0


# ── levels on this machine ──────────────────────────────────────────────────────────────────────

class Source:
    """One level this machine can read: the flowie, a hive clone or the project here."""

    def __init__(self, kind: str, key: str, label: str, repo: Path, memory: Path, policy: str | None,
                 board: str, card: str | None = None, upstream: tuple[bool, str | None] = (False, None)) -> None:
        self.kind, self.key, self.label = kind, key, label
        self.repo, self.memory = repo, memory            # the git work tree, and where tasks/ and wiki/ live
        self.local_policy = policy                       # the team's value in this working tree
        self.upstream_known, self.upstream_policy = upstream  # the upstream's value, as last fetched
        # own | allow | allow-names | forbid | None (absent): the stricter of the two — a clone that is behind cannot
        # keep mirroring what the team stopped, and a value nobody pushed cannot start it
        self.policy = stricter(policy, self.upstream_policy) if self.upstream_known else policy
        self.board = board                               # the mod's board id: flowie | hive:{folder} | project
        self.card = card

    @property
    def allowed(self) -> bool:
        return self.policy in ("own", "allow", "allow-names")

    @property
    def names(self) -> bool:
        return self.policy in ("own", "allow-names")

    def as_dict(self) -> dict:
        return {"level": self.key, "kind": self.kind, "label": self.label, "policy": self.policy or "absent",
                "board": self.board, **({"card": self.card} if self.card else {})}


def policy_of(text: str | None) -> str | None:
    value = scalar(split_fm(text or "")[0], "workbench_mirror")
    return value.lower() if value and value.lower() in POLICIES else None


STRICTNESS = {"forbid": 0, None: 1, "allow": 2, "allow-names": 3}


def stricter(a: str | None, b: str | None) -> str | None:
    return a if STRICTNESS.get(a, 1) <= STRICTNESS.get(b, 1) else b


def upstream_policy(repo: Path, rel: str) -> tuple[bool, str | None]:
    """(whether the clone has an upstream, the workbench_mirror its copy of `rel` holds, as last fetched)."""
    if not is_repo(repo) or out_of(git(repo, "rev-parse", "--verify", "--quiet", "@{u}")) is None:
        return False, None
    shown = git(repo, "show", f"@{{u}}:./{rel}")
    return True, (policy_of(shown.stdout) if shown.returncode == 0 else None)


def fetch_clone(repo: Path, home: Path) -> None:
    """A read-only fetch, so the upstream's values are current (a repository git cannot read, or without a commit, is
    left as it is)."""
    if is_repo(repo) and out_of(git(repo, "rev-parse", "HEAD")):
        git(repo, "fetch", "--quiet", home=home, timeout=120)


def project_root(start: Path | None) -> Path | None:
    return pj.find_root(start.resolve()) if start is not None else None


def discover(home: Path, root: Path | None, fetch: bool = False) -> tuple[list[Source], list[dict]]:
    """Every level this machine has, and the ones that can get no key (said why). The team's workbench_mirror is read
    from the working tree and from the clone's upstream as last fetched — `fetch` fetches every clone first."""
    found: list[Source] = []
    unkeyed: list[dict] = []
    levels = pj.all_levels(home)
    here = project_root(root)
    if fetch:
        for repo in [level.root for level in levels] + ([here] if here is not None else []):
            fetch_clone(repo, home)
    for level in levels:
        if level.kind == "flowie":
            found.append(Source("flowie", "flowie", "flowie", level.root, level.root, "own", "flowie"))
            continue
        key = hive_key(pj.origin_url(level.root))
        if key is None:
            unkeyed.append({"kind": "hive", "folder": level.name, "reason": "the clone has no origin remote, so it gets no tab"})
            continue
        found.append(Source("hive", key, level.repo or level.name, level.root, level.root,
                            policy_of(read_text(level.root / "hive.md")), f"hive:{level.name}",
                            upstream=upstream_policy(level.root, "hive.md")))
    if here is not None:
        card = pj.linked_id(home, levels, here)
        key = project_key(card, pj.origin_url(here))
        config = read_text(here / ".neuroflow" / "project_config.md") or ""
        name = scalar(split_fm(config)[0], "project_name")
        if key is None:
            unkeyed.append({"kind": "project", "reason": "this project has neither a registry card nor an origin remote, "
                                                         "so it gets no tab (/flowie --projects --add registers it)"})
        else:
            found.append(Source("project", key, name or card or here.name, here, here / ".neuroflow", policy_of(config),
                                "project", card, upstream=upstream_policy(here, ".neuroflow/project_config.md")))
    return found, unkeyed


def consent(home: Path) -> dict:
    data = read_user_yaml(home)
    return {"on": on(data.get("workbench")), "levels": as_keys(data.get("workbench_levels")),
            "index_only": as_keys(data.get("workbench_index_only")), "machine": str(data.get("workbench_machine") or "").strip(),
            "account": str(data.get("workbench_account") or "").strip(), "handle": str(data.get("flowie_handle") or "").strip(),
            "pii_config": str(data.get("pii_config") or "").strip() if not isinstance(data.get("pii_config"), (list, dict)) else ""}


def pii_settings(path_text: str | None) -> dict | None:
    """The person's pii_scan.py config (id_patterns, roster) — from --pii-config, else the file `pii_config` names in
    user.yaml; None without one. A relative roster path is read from the config's own folder. A config that cannot be
    read stops the export: going on would upload ID numbers and roster names the person asked to be caught."""
    if not path_text:
        return None
    path = Path(path_text).expanduser()
    try:
        config = json.loads(path.read_bytes().decode("utf-8-sig"))
    except (OSError, ValueError) as error:
        raise UsageError(f"the pii_scan config {path} cannot be read ({error}); fix it, or remove pii_config from "
                         "~/.neuroflow/user.yaml") from error
    if not isinstance(config, dict):
        raise UsageError(f"the pii_scan config {path} must be a JSON object")
    roster = config.get("roster")
    if isinstance(roster, str) and roster.strip() and not Path(roster.strip()).expanduser().is_absolute():
        config = {**config, "roster": str(path.parent / roster.strip())}
    return config


def level_rows(sources: list[Source], person: dict) -> list[dict]:
    rows = []
    for src in sources:
        consented = src.key in person["levels"]
        reason = None
        if not src.allowed:
            where = "hive.md" if src.kind == "hive" else "project_config.md"
            reason = ("the team forbids mirroring it" if src.policy == "forbid" else
                      f"the team has not opted in (workbench_mirror in {where})")
            if src.local_policy in ("allow", "allow-names"):
                reason += f" — so says the upstream {where}; pull this clone"
            elif src.upstream_policy in ("allow", "allow-names"):
                reason += f" — here; the upstream {where} allows it: pull this clone"
        elif not person["on"]:
            reason = "your workbench is off (workbench: on in ~/.neuroflow/user.yaml)"
        elif not consented:
            reason = "not one of your workbench_levels"
        # purge: the team no longer allows it — a shared decision every machine reads alike, so gc deletes the level
        # wherever the person's workbench holds it; when the upstream still allows it (this clone is behind, or holds
        # a change nobody pushed), another machine may mirror it rightly, so it stays. This machine's own settings never
        # purge a level by themselves: the person takes a level off with --web --levels, which names it to gc.
        upstream_allows = src.upstream_known and src.upstream_policy in ("allow", "allow-names")
        rows.append({**src.as_dict(), "consented": consented, "mirrored": reason is None,
                     "purge": not src.allowed and not upstream_allows,
                     "index_only": src.key in person["index_only"], **({"reason": reason} if reason else {})})
    return rows


# ── the allowlist: every field that leaves, per kind of item ────────────────────────────────────

# The export keeps only these keys (allow()). `sources` prints them per source, docs/concepts/workbench.md carries the
# same table, and the tests hold the table, this allowlist and every exported document to one another.
FIELDS: dict[str, tuple[str, ...]] = {
    "card": ("slug", "file", "column", "title", "owner", "due", "created", "updated", "phase", "tags", "project",
             "blocked_by", "sha256", "notes", "legacy", "readable"),
    "column": ("id", "label", "archive", "closed", "extra"),
    "registry": ("id", "description", "status", "current_phase", "visited_phases", "repos", "pointer", "hive"),
    "page": ("id", "title", "type", "tags", "status", "updated", "summary", "sources", "body"),
    "person": ("handle", "name", "role"),
    "note": ("file", "title", "date"),
    "meeting": ("slug", "title", "date"),
    "erratum": ("dataset", "columns", "rows"),
    "date": ("date", "what", "gates"),
    "marker": ("status", "expires", "frozen_at", "by_person"),
    "flowie_panel": ("ideas", "ideas_inbox", "notes", "meetings"),
    "hive_panel": ("team", "ideas", "errata", "meetings"),
    "project_panel": ("project_name", "active_phase", "recommended_phases", "visited", "ethics_not_applicable", "ethics",
                      "prereg", "dates", "meetings"),
    "source": ("git", "branch", "head", "upstream", "upstream_head", "ahead", "behind", "fetched_at", "shallow",
               "uncommitted_tasks"),
    "applied": ("state", "commit"),
    "core": ("snap_schema", "level", "part", "kind", "label", "columns", "archive_after_days", "people", "registry",
             "panel", "phases", "card", "sha256"),
    "part": ("snap_schema", "level", "part", "cards", "pages", "sha256"),
    "meta": ("snap_schema", "intent_schema", "level", "kind", "label", "exported_at", "machine", "policy", "working_tree",
             "index_only", "source", "parts", "applied", "withheld", "counts"),
    "part_ref": ("id", "sha256", "bytes"),
    "withheld": ("source", "reason"),
    "counts": ("cards", "open", "pages"),
}


def allow(kind: str, item: dict) -> dict:
    """The allowlisted fields of one exported item; every other key stays on this machine."""
    fields = FIELDS[kind]
    return {key: value for key, value in item.items() if key in fields}


def every(kind: str) -> list[str]:
    return [f"{kind}.{name}" for name in FIELDS[kind]]


# One row per source: where it is read and the `kind.field` entries it puts in the store. Together the rows name every
# entry of FIELDS, and nothing else (a test holds them equal).
SOURCES = [
    {"source": "tasks", "levels": "flowie, hive, project", "from": "tasks/{column}/{slug}.md",
     "fields": ["part.cards", *every("card")],
     "note": "owner only as a roster handle; the first 1,000 characters of the notes; sha256 is the content hash; legacy "
             "and readable say whether the file is in an older format or carries a merge conflict"},
    {"source": "columns", "levels": "flowie, hive, project", "from": "tasks/config.json",
     "fields": ["core.columns", *every("column"), "core.archive_after_days"],
     "note": "extra marks a folder that config.json does not name"},
    {"source": "registry", "levels": "flowie, hive", "from": "projects/projects.json",
     "fields": ["core.registry", *every("registry")],
     "note": "remote repository URLs only, without a user name, password or query; the first 1,000 characters of a "
             "description; a flowie pointer as its id and hive only"},
    {"source": "wiki", "levels": "flowie, hive, project", "from": "wiki/pages/**, wiki/index.md",
     "fields": ["part.pages", *every("page")],
     "note": "no body with index only; [[links]] resolved to pages; sources, raw/ files and images named, never uploaded"},
    {"source": "people", "levels": "flowie, hive, project", "from": "your handle, members.md, collaborators",
     "fields": ["core.people", *every("person")],
     "note": "name and role only with allow-names; your own handle only at flowie level; never an email address"},
    {"source": "ideas", "levels": "flowie, hive", "from": "ideas.md, ideas-inbox.md (flowie)",
     "fields": ["flowie_panel.ideas", "flowie_panel.ideas_inbox", "hive_panel.ideas"], "note": "the text, at most 40 KB"},
    {"source": "notes", "levels": "flowie", "from": "notes/*.md", "fields": ["flowie_panel.notes", *every("note")],
     "note": "never the notes themselves; the newest 200"},
    {"source": "meetings", "levels": "flowie, hive, project", "from": "meetings/*.md",
     "fields": ["flowie_panel.meetings", "hive_panel.meetings", "project_panel.meetings", *every("meeting")],
     "note": "never attendees, agenda or notes; the newest 200"},
    {"source": "team", "levels": "hive", "from": "hive.md", "fields": ["hive_panel.team"],
     "note": "the text after the frontmatter, at most 40 KB: the team's name, description, norms and research directions"},
    {"source": "errata", "levels": "hive", "from": "errata/*.md", "fields": ["hive_panel.errata", *every("erratum")],
     "note": "the table rows (the newest 200 per dataset): date, scope, problem, workaround, reported_by"},
    {"source": "phases", "levels": "project", "from": "project_config.md, phase folders",
     "fields": ["project_panel.project_name", "project_panel.active_phase", "project_panel.recommended_phases",
                "project_panel.visited", "project_panel.ethics_not_applicable", "core.phases", "core.card"],
     "note": "visited names the phase folders that exist, card the project's id in your registry; no other config field"},
    {"source": "dates", "levels": "project", "from": "timeline.md", "fields": ["project_panel.dates", *every("date")],
     "note": "the dated rows; gates names the phase a date gates"},
    {"source": "integrity", "levels": "project", "from": "ethics/status.md, preregistration/status.md",
     "fields": ["project_panel.ethics", "project_panel.prereg", *every("marker")],
     "note": "by_person says whether a person set the marker; never approval documents"},
    {"source": "git", "levels": "flowie, hive, project", "from": "the clone",
     "fields": ["meta.source", *every("source"), "meta.machine", "meta.applied", *every("applied")],
     "note": "machine is your label for this computer; applied names your own clicks that reached git, by their "
             "Neuroflow-Intent trailers"},
    {"source": "the level", "levels": "flowie, hive, project", "from": "the export itself",
     "fields": [*(f"core.{name}" for name in ("snap_schema", "level", "part", "kind", "label", "panel", "sha256")),
                *(f"part.{name}" for name in ("snap_schema", "level", "part", "sha256")),
                *(f"meta.{name}" for name in ("snap_schema", "intent_schema", "level", "kind", "label", "exported_at",
                                              "policy", "working_tree", "index_only", "parts", "withheld", "counts")),
                *every("part_ref"), *every("withheld"), *every("counts")],
     "note": "the level's name and kind, format versions, the export time, the team's workbench_mirror value, part sizes "
             "and hashes, counts, and which sources held items back and why — never the held items or their names"},
]
NEVER = ["sessions/, review/, paper/xray-*, wiki/.pending/ and every other local-tier path",
         "integrations.json, user.yaml, local-projects.json, boards/", "fails/, finance/, reasoning/",
         "the flowie's profile.md and wellbeing/", "wiki raw/ files and images", "email addresses, anywhere",
         "meeting attendees, agendas and notes", "machine-local paths"]
SCRUB = ("Free text (titles, notes, descriptions, a project's status and phase, column labels, wiki pages with their type "
         "and status, ideas, team text, people's names and roles, errata rows, dated rows) "
         "goes through pii_scan.py's patterns, without its allowance for addresses the project lists: an email address "
         "becomes [email removed], a phone number [phone removed], an ID number your pii_scan config names [id removed], "
         "and a machine-local path (C:\\Users\\…, /home/…, ~/…, as local_paths.py finds them) [local path removed]. "
         "An item with secret-like text or a name from that config's participant roster is held back whole, and so is one "
         "whose file name, tags or links carry personal data, as they travel unchanged. Your pii_scan config is the file "
         "pii_config names in ~/.neuroflow/user.yaml (its id_patterns and roster); without it, ID numbers and participant "
         "names are not checked. The preview names each item held back; the page only counts them.")


def sources_markdown() -> str:
    rows = ["| Source | Levels | Read from | What is uploaded |", "|---|---|---|---|"]
    for item in SOURCES:
        names = ", ".join(f"`{name}`" for name in dict.fromkeys(field.split(".", 1)[1] for field in item["fields"]))
        rows.append(f"| {item['source']} | {item['levels']} | `{item['from']}` | {names} — {item['note']} |")
    rows += ["", "Never uploaded: " + "; ".join(NEVER) + ".", "", SCRUB]
    return "\n".join(rows) + "\n"


# ── personal data in free text ──────────────────────────────────────────────────────────────────

class Scrubber:
    """pii_scan.py's patterns for uploads: no allowance for the project's own addresses (pii_scan was written for
    shared repositories; claude.ai is outside them). Values are replaced or the item is held back; none is printed."""

    def __init__(self, config: dict | None = None) -> None:
        mod = pii()
        self.mod = mod
        cfg = config or {}
        roster_file = cfg.get("roster")
        try:
            roster = mod.load_roster(Path(roster_file).expanduser()) if roster_file else None
            patterns = mod.id_patterns_from(cfg)
        except mod.ConfigError as error:
            raise UsageError(f"the pii_scan config: {error}") from error
        # No allowed or known addresses: an email address never leaves (only reserved example domains pass).
        self.scanner = mod.Scanner(patterns, roster, (), (), secrets=True)
        self.paths = local_paths()

    def text(self, value: str | None) -> tuple[str, set[str]]:
        if not value:
            return value or "", set()
        hits: set[str] = set()
        mod = self.mod
        # a folder on one machine (C:\Users\…, /home/…, ~/…) means nothing on the page and says where the data is
        for path in sorted({hit["path"] for hit in self.paths.findings_in_text(value)}, key=len, reverse=True):
            if path in value:
                value = value.replace(path, "[local path removed]")
                hits.add("local-path")

        def email(match: re.Match) -> str:
            if self.scanner._email_ignored(match.group()):
                return match.group()
            hits.add("email")
            return "[email removed]"

        def phone(match: re.Match) -> str:
            if 9 <= len(re.sub(r"\D", "", match.group())) <= 15:
                hits.add("phone")
                return "[phone removed]"
            return match.group()

        value = mod.EMAIL_RE.sub(email, value)
        value = mod.PHONE_RE.sub(phone, value)
        for pattern in self.scanner.id_patterns:
            def ident(match: re.Match, pattern=pattern) -> str:
                if mod.CHECKSUMS[pattern.checksum](re.sub(r"\D", "", match.group())):
                    hits.add(f"id:{pattern.name}")
                    return "[id removed]"
                return match.group()
            value = pattern.regex.sub(ident, value)
        for line in value.splitlines():
            for kind in self.scanner.scan_line(line):
                if kind.startswith("secret:") or kind == "roster-name":
                    hits.add(kind)
        return value, hits


def held(hits: set[str]) -> str | None:
    if any(kind.startswith("secret:") for kind in hits):
        return "secret-like text"
    if "roster-name" in hits:
        return "a name from your participant roster"
    return None


def name_held(scrub: Scrubber, *names) -> str | None:
    """File names, ids, tags and links travel unchanged (a card's file is its identity on the page), so any personal
    data in them holds the item back instead of being rewritten."""
    text = " ".join(str(name) for name in names if name)
    if not text:
        return None
    hits = scrub.text(text)[1] | scrub.text(re.sub(r"[-_./\\]+", " ", text))[1]
    return held(hits) or ("personal data in its file name, tags or links" if hits else None)


DATE_TIME = re.compile(r"^\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?)?")


def date_of(*values) -> str | None:
    """The date (and time) a value starts with, from the first value that has one: a date field never carries free
    text."""
    for value in values:
        match = DATE_TIME.match(str(value or ""))
        if match:
            return match.group(0)
    return None


def clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit].rstrip() + " …"


def clip_bytes(text: str, limit: int) -> str:
    """At most `limit` bytes of UTF-8 (a part's limit is bytes: 60,000 CJK characters are 180 KB)."""
    data = text.encode("utf-8")
    return text if len(data) <= limit else data[:limit].decode("utf-8", "ignore").rstrip() + " …"


def newest(items: list, source: str, withheld: list[dict]) -> list:
    """The newest LIST_MAX entries of a list sorted oldest first; how many were left out is counted, with why."""
    if len(items) <= LIST_MAX:
        return items
    withheld.append({"source": source, "item": f"{len(items) - LIST_MAX} older", "reason": f"the panel lists the newest {LIST_MAX}"})
    return items[-LIST_MAX:]


# ── what a level holds ──────────────────────────────────────────────────────────────────────────

def columns_of(tasks: Path) -> tuple[list[dict], int]:
    data = pj.read_json(tasks / "config.json") if (tasks / "config.json").is_file() else None
    columns = []
    if isinstance(data, dict) and isinstance(data.get("columns"), list):
        for item in data["columns"]:
            if isinstance(item, dict) and str(item.get("id") or "").strip():
                cid = str(item["id"]).strip()
                columns.append({"id": cid, "label": str(item.get("label") or cid), "archive": item.get("archive") is True})
    if not columns:
        columns = [{"id": cid, "label": cid, "archive": cid == "archive"} for cid in pj.DEFAULT_COLUMNS]
    for column in columns:
        column["closed"] = column["id"] == "done" or column["archive"]
    days = data.get("archive_after_days") if isinstance(data, dict) else None
    return columns, days if isinstance(days, int) and days > 0 else 90


def roster(src: Source, person: dict, scrub: Scrubber | None = None, withheld: list[dict] | None = None) -> list[dict]:
    """The level's people as roster handles; names and roles only where the team's opt-in allows them, and only through
    the scrubber (without one — the validator needs handles only — none at all)."""
    people: dict[str, dict] = {}

    def named(entry: dict, values: dict) -> dict:
        if not src.names or scrub is None:
            return entry
        for key in ("name", "role"):
            if not values.get(key):
                continue
            text, hits = scrub.text(str(values[key]))
            if held(hits):
                if withheld is not None:
                    withheld.append({"source": "people", "item": entry["handle"], "reason": held(hits)})
                continue
            entry[key] = text
        return entry

    if src.kind == "flowie":
        handle = handle_of(person.get("handle"))
        if handle:
            people[handle.lower()] = {"handle": handle}
    elif src.kind == "hive":
        headers, rows = parse_table(read_text(src.repo / "members.md") or "")
        index = {name.strip().lower(): n for n, name in enumerate(headers)}
        for row in rows:
            cell = lambda name: row[index[name]].strip() if name in index and index[name] < len(row) else ""  # noqa: E731
            handle = handle_of(cell("github") or cell("handle"))
            if handle:
                people[handle.lower()] = named({"handle": handle}, {key: cell(key) for key in ("name", "role")})
    else:
        config = read_text(src.repo / ".neuroflow" / "project_config.md") or ""
        split = mg.sc.split_frontmatter(config)
        for seg in mg.segment_frontmatter(split[0]) if split else []:
            if seg[0] != "collaborators":
                continue
            value = mg.segment_value(seg[1])
            for item in value if isinstance(value, list) else []:
                if isinstance(item, dict):
                    handle = handle_of(item.get("handle"))
                    if handle:
                        people[handle.lower()] = named({"handle": handle}, item)
    return sorted((allow("person", entry) for entry in people.values()), key=lambda entry: entry["handle"].lower())


def parse_table(text: str) -> tuple[list[str], list[list[str]]]:
    """The first markdown table: its header cells and its rows."""
    headers: list[str] = []
    rows: list[list[str]] = []
    for line in text.replace("\r\n", "\n").split("\n"):
        stripped = line.strip()
        if not stripped.startswith("|"):
            if headers:
                break
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not headers:
            headers = cells
        elif all(re.fullmatch(r":?-{2,}:?", cell) for cell in cells if cell):
            continue
        else:
            rows.append(cells)
    return headers, rows


def export_cards(src: Source, scrub: Scrubber, withheld: list[dict], handles: set[str] | None = None) -> list[dict]:
    """The level's cards; an owner goes up only as a handle on the level's roster (`handles`, lower case) — a legacy
    `assignee: Kristyna` that matches no roster entry is left out."""
    cards = []
    for task in pj.read_board(src.memory / "tasks", details=True):
        title, title_hits = scrub.text(task["title"])
        notes, note_hits = scrub.text(clip(task.get("notes") or "", NOTES_MAX))
        reason = held(title_hits | note_hits) or name_held(scrub, task["file"], task.get("project"), task.get("phase"),
                                                           *(task.get("tags") or []), *(task.get("blocked_by") or []))
        if reason:
            withheld.append({"source": "tasks", "item": task["file"], "reason": reason})
            continue
        owner = handle_of(task.get("owner")) if task.get("owner") else None
        if owner and owner.lower() not in (handles or set()):
            owner = None
        cards.append(allow("card", {
            "slug": task["slug"], "file": task["file"], "column": task["column"], "title": title,
            "owner": owner, "due": task["due"] if task["due"] and DATE.match(task["due"]) else None,
            "created": date_of(task.get("created")), "updated": date_of(task.get("updated")), "phase": task.get("phase"),
            "tags": task.get("tags") or [], "project": task.get("project"), "blocked_by": task.get("blocked_by") or [],
            "sha256": task["sha256"], "notes": notes, "legacy": task["legacy"], "readable": not task["conflicted"],
        }))
    return cards


def public_url(url: str) -> str:
    """A repository URL as it may leave: without a user name or password (`https://user:token@host/…`, a clone made
    with a token), a query or a fragment; an scp-style address keeps only the generic `git@` user."""
    url = url.strip()
    match = re.match(r"^([a-z][a-z0-9+.-]*://)(?:[^/?#]*@)?([^?#]*)", url, re.I)
    if match:
        return match.group(1) + match.group(2)
    scp = re.match(r"^([^@/\\:\s]+)@([^:/\s]+:\S+)$", url)
    if scp:
        return url if scp.group(1).lower() == "git" else scp.group(2)
    return url


def export_registry(src: Source, scrub: Scrubber, withheld: list[dict]) -> list[dict]:
    if src.kind == "project":
        return []
    entries, _ = pj.registry_entries(src.repo / "projects" / "projects.json")
    out = []
    for entry in entries:
        pid = pj.entry_id(entry)
        reason = name_held(scrub, pid)
        if reason:
            withheld.append({"source": "registry", "item": pid, "reason": reason})
            continue
        if pj.is_pointer(entry):
            out.append(allow("registry", {"id": pid, "pointer": True, "hive": entry["ref"][len("hive:"):].strip()}))
            continue
        # a URL travels unchanged, like a name: personal data or a secret left in it holds the entry back
        repos = [public_url(url) for url in pj.repo_values(entry) if pj.is_remote(url) and not url.lower().startswith("file:")]
        visited = pj.as_list(entry.get("visited_phases"))
        reason = name_held(scrub, *repos, *visited)
        if reason:
            withheld.append({"source": "registry", "item": pid, "reason": reason})
            continue
        text: dict[str, str] = {}
        for name in ("description", "status", "current_phase"):  # free text: rewritten, or left out when held back
            text[name], hits = scrub.text(clip(str(entry.get(name) or ""), NOTES_MAX))
            if held(hits):
                withheld.append({"source": "registry", "item": pid, "reason": held(hits)})
                text[name] = ""
        out.append(allow("registry", {
            "id": pid, "description": text["description"], "status": text["status"] or None,
            "current_phase": text["current_phase"] or None, "visited_phases": visited, "repos": repos}))
    return out


def text_block(path: Path, source: str, scrub: Scrubber, withheld: list[dict], frontmatter: bool = False) -> str | None:
    text = read_text(path)
    if text is None:
        return None
    if frontmatter:
        text = split_fm(text)[1]
    value, hits = scrub.text(clip_bytes(text.replace("\r\n", "\n").strip(), TEXT_MAX))
    if held(hits):
        withheld.append({"source": source, "item": path.name, "reason": held(hits)})
        return None
    return value


def dated_list(folder: Path, source: str, kind: str, scrub: Scrubber, withheld: list[dict]) -> list[dict]:
    """Meetings or notes as a list: name, title and date — never the file's content."""
    out = []
    for path in sorted(folder.glob("*.md")) if folder.is_dir() else []:
        fm, body = split_fm(read_text(path) or "")
        title = scalar(fm, "title") or next((line[2:].strip() for line in body.split("\n") if line.startswith("# ")), path.stem)
        title, hits = scrub.text(title)
        reason = held(hits) or name_held(scrub, path.stem)
        if reason:
            withheld.append({"source": source, "item": path.name, "reason": reason})
            continue
        out.append(allow(kind, {"slug": path.stem, "file": path.name, "title": clip(title, 300),
                                "date": date_of(scalar(fm, "date"), path.stem)}))
    return newest(out, source, withheld)


def export_panel(src: Source, scrub: Scrubber, withheld: list[dict]) -> dict:
    if src.kind == "flowie":
        return allow("flowie_panel", {
            "ideas": text_block(src.repo / "ideas.md", "ideas", scrub, withheld),
            "ideas_inbox": text_block(src.repo / "ideas-inbox.md", "ideas", scrub, withheld),
            "notes": dated_list(src.repo / "notes", "notes", "note", scrub, withheld),
            "meetings": dated_list(src.repo / "meetings", "meetings", "meeting", scrub, withheld)})
    if src.kind == "hive":
        errata = []
        for path in sorted((src.repo / "errata").glob("*.md")) if (src.repo / "errata").is_dir() else []:
            headers, rows = parse_table(read_text(path) or "")
            reason = name_held(scrub, path.stem) or held(scrub.text(" ".join(headers))[1])
            if reason:
                withheld.append({"source": "errata", "item": path.name, "reason": reason})
                continue
            clean = []
            for row in rows:
                cells = []
                stop = None
                for cell in row:
                    value, hits = scrub.text(cell)
                    stop = stop or held(hits)
                    cells.append(value)
                if stop:
                    withheld.append({"source": "errata", "item": path.name, "reason": stop})
                    continue
                clean.append(cells)
            errata.append(allow("erratum", {"dataset": path.stem, "columns": [scrub.text(cell)[0] for cell in headers],
                                            "rows": newest(clean, "errata", withheld)}))
        return allow("hive_panel", {
            "team": text_block(src.repo / "hive.md", "team", scrub, withheld, frontmatter=True),
            "ideas": text_block(src.repo / "ideas.md", "ideas", scrub, withheld),
            "errata": errata, "meetings": dated_list(src.repo / "meetings", "meetings", "meeting", scrub, withheld)})
    nf = src.memory
    fm, _ = split_fm(read_text(nf / "project_config.md") or "")
    phases = sorted(mg.canonical_phases() - {"setup"})
    timeline = []
    for row in parse_table(read_text(nf / "timeline.md") or "")[1]:
        if row and DATE.match(row[0]):
            what, hits = scrub.text(row[1] if len(row) > 1 else "")
            gates, gate_hits = scrub.text(row[2] if len(row) > 2 else "")
            if held(hits | gate_hits):
                withheld.append({"source": "dates", "item": row[0], "reason": held(hits | gate_hits)})
                continue
            timeline.append(allow("date", {"date": row[0], "what": what, "gates": gates or None}))

    def marker(path: Path, *keys: str) -> dict | None:
        text = read_text(path)
        if text is None:
            return None
        meta = split_fm(text)[0]
        values = {key: date_of(scalar(meta, key)) if key != "status" else scalar(meta, key) for key in keys}
        return allow("marker", {**values, "by_person": scalar(meta, "set_by") == "person"})

    return allow("project_panel", {
        "project_name": scrub.text(scalar(fm, "project_name"))[0] or None, "active_phase": scalar(fm, "active_phase"),
        "recommended_phases": pj.as_list(fm.get("recommended_phases")),
        "visited": sorted(p.name for p in nf.iterdir() if p.is_dir() and p.name in phases) if nf.is_dir() else [],
        "ethics_not_applicable": scalar(fm, "ethics") == "not-applicable",
        "ethics": marker(nf / "ethics" / "status.md", "status", "expires"),
        "prereg": marker(nf / "preregistration" / "status.md", "status", "frozen_at"),
        "dates": newest(timeline, "dates", withheld), "meetings": dated_list(nf / "meetings", "meetings", "meeting", scrub, withheld)})


WIKILINK = re.compile(r"(!?)\[\[([^\[\]\n|#]*)(?:#[^\[\]\n|]*)?(?:\|([^\[\]\n]*))?\]\]")
MDLINK = re.compile(r"(!?)\[([^\[\]\n]*)\]\(([^()\s]+)(?:\s+\"[^\"]*\")?\)")


def export_wiki(src: Source, scrub: Scrubber, withheld: list[dict], index_only: bool) -> list[dict]:
    """Every page under wiki/pages/: frontmatter facts, the index summary and the body with [[links]] resolved to page
    ids. raw/ files, images and other local files are named in a marker, never uploaded (wiki-protocol)."""
    root = src.memory / "wiki"
    pages_dir = root / "pages"
    if not pages_dir.is_dir():
        return []
    summaries = {}
    for row in parse_table(read_text(root / "index.md") or "")[1]:
        link = re.search(r"\]\((pages/[^)]+\.md)\)", row[0]) if row else None
        if link and len(row) > 1:
            summaries[link.group(1)[len("pages/"):-3]] = row[1]
    raw: list[tuple[str, dict, str]] = []
    for path in sorted(pages_dir.rglob("*.md")):
        rel = path.relative_to(pages_dir).as_posix()[:-3]
        fm, body = split_fm(read_text(path) or "")
        raw.append((rel, fm, body))
    titles: dict[str, str] = {}
    for rel, fm, _ in raw:
        for name in (scalar(fm, "title"), rel.split("/")[-1], rel):
            if name and name.strip().lower() not in titles:
                titles[name.strip().lower()] = rel

    def resolve(target: str) -> str | None:
        target = target.strip()
        if target.lower().endswith(".md"):
            target = target[:-3]
        return titles.get(target.lower()) or titles.get(target.split("/")[-1].lower())

    def local(name: str) -> str:
        return f"[local file, not mirrored: {name.split('/')[-1] or name}]"

    def rewrite(body: str, here: str) -> str:
        def wiki(match: re.Match) -> str:
            embed, target, alias = match.group(1), match.group(2), match.group(3)
            if embed:
                return local(target.strip())
            label = (alias or target).strip()
            found = resolve(target)
            return f"[[{found}|{label}]]" if found else f"[[|{label}]]"

        def markdown(match: re.Match) -> str:
            image, label, url = match.group(1), match.group(2), match.group(3)
            if re.match(r"^https?://", url, re.I):
                return f"[{label or 'image'}]({url})" if image else match.group(0)
            if image or url.startswith(("raw/", "../raw/", "assets/")) or "/raw/" in url:
                return local(url)
            base = here.rsplit("/", 1)[0] if "/" in here else ""
            joined = os.path.normpath(os.path.join(base, url.split("#")[0])).replace("\\", "/")
            found = resolve(joined.replace("pages/", "", 1)) or resolve(url.split("#")[0])
            return f"[[{found}|{label}]]" if found else local(url)

        return MDLINK.sub(markdown, WIKILINK.sub(wiki, body))

    out = []
    for rel, fm, body in raw:
        title, hits = scrub.text(scalar(fm, "title") or rel.split("/")[-1])
        summary, summary_hits = scrub.text(summaries.get(rel, ""))
        page_type, type_hits = scrub.text(scalar(fm, "type") or "")
        status, status_hits = scrub.text(scalar(fm, "status") or "")
        summary_hits |= type_hits | status_hits
        tags = pj.as_list(fm.get("tags"))
        sources = [name.replace("\\", "/").split("/")[-1] for name in pj.as_list(fm.get("sources"))]  # a name, never a path
        text = ""
        if not index_only:
            text, body_hits = scrub.text(rewrite(body.strip(), rel))
            hits |= body_hits
            if len(text.encode("utf-8")) > BODY_MAX:
                text = text.encode("utf-8")[:BODY_MAX].decode("utf-8", "ignore") + "\n\n[truncated: the page is longer than 150 KB]"
        reason = held(hits | summary_hits) or name_held(scrub, rel, *tags, *sources)
        if reason:
            withheld.append({"source": "wiki", "item": rel, "reason": reason})
            continue
        page = {"id": rel, "title": title, "type": page_type or None, "tags": tags, "status": status or None,
                "updated": date_of(scalar(fm, "updated")), "summary": summary, "sources": sources}
        if not index_only:
            page["body"] = text
        out.append(allow("page", page))
    return out


# ── git: where the level was read from ──────────────────────────────────────────────────────────

def git(repo: Path, *args: str, home: Path | None = None, timeout: int = 60) -> subprocess.CompletedProcess:
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
    if not (os.environ.get("GIT_SSH_COMMAND") or os.environ.get("GIT_SSH") or (home and pj.own_ssh(home))):
        env["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes"
    try:
        return subprocess.run(["git", "-C", str(repo), "-c", "core.quotePath=false", *args], capture_output=True,
                              text=True, encoding="utf-8", errors="replace", env=env, stdin=subprocess.DEVNULL, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as error:
        return subprocess.CompletedProcess(args, 1, "", str(error))


def is_repo(path: Path) -> bool:
    return (path / ".git").exists() and shutil.which("git") is not None


def out_of(proc: subprocess.CompletedProcess) -> str | None:
    return proc.stdout.strip() if proc.returncode == 0 and proc.stdout.strip() else None


def git_source(src: Source, home: Path, fetch: bool) -> dict:
    """Branch, head, upstream head, ahead/behind, last fetch and uncommitted task files: the tab's freshness label
    (records state their blind spots) and the refresh guard's facts."""
    if not is_repo(src.repo):
        return {"git": False}
    head = out_of(git(src.repo, "rev-parse", "HEAD"))
    if head is None:
        return {"git": False}  # not a repository git can read (or no commit yet): the files as they are
    if fetch:
        git(src.repo, "fetch", "--quiet", home=home, timeout=120)
    info: dict = {"git": True, "branch": out_of(git(src.repo, "rev-parse", "--abbrev-ref", "HEAD")), "head": head}
    upstream = out_of(git(src.repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"))
    info["upstream"] = upstream
    info["upstream_head"] = out_of(git(src.repo, "rev-parse", "@{u}")) if upstream else None
    counts = out_of(git(src.repo, "rev-list", "--left-right", "--count", "HEAD...@{u}")) if upstream else None
    if counts and re.fullmatch(r"\d+\s+\d+", counts):
        info["ahead"], info["behind"] = (int(n) for n in counts.split())
    fetch_head = out_of(git(src.repo, "rev-parse", "--git-path", "FETCH_HEAD"))
    if fetch_head:
        path = Path(fetch_head) if Path(fetch_head).is_absolute() else src.repo / fetch_head
        if path.is_file():
            info["fetched_at"] = iso(datetime.fromtimestamp(path.stat().st_mtime, timezone.utc))
    info["shallow"] = out_of(git(src.repo, "rev-parse", "--is-shallow-repository")) == "true"
    tasks = "tasks" if src.kind != "project" else ".neuroflow/tasks"
    status = git(src.repo, "status", "--porcelain", "--untracked-files=all", "--", tasks)
    info["uncommitted_tasks"] = len([line for line in status.stdout.splitlines() if line.strip()]) if status.returncode == 0 else None
    return allow("source", info)


def default_remote_ref(repo: Path) -> str | None:
    return out_of(git(repo, "rev-parse", "--abbrev-ref", "origin/HEAD")) or out_of(
        git(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"))


def trailer_commits(repo: Path, limit: int = 1000) -> dict[str, str]:
    """intent id → the commit whose message carries its Neuroflow-Intent trailer, in the history checked out here."""
    proc = git(repo, "log", f"--max-count={limit}", "-F", f"--grep={TRAILER}:", "--format=%H%x1f%B%x1e", "HEAD")
    found: dict[str, str] = {}
    if proc.returncode != 0:
        return found
    for record in proc.stdout.split("\x1e"):
        if "\x1f" not in record:
            continue
        sha, message = record.strip().split("\x1f", 1)
        for match in re.finditer(rf"^{TRAILER}:\s*(\S+)\s*$", message, re.M):
            found.setdefault(match.group(1), sha.strip())
    return found


def landed_states(repo: Path, commits: dict[str, str]) -> dict[str, dict]:
    """For each trailer commit: committed (only here), pushed (a remote branch has it) or merged (the default branch has
    it). Recomputed on every export, so the page stays right after a later push from /hive or /git."""
    if not commits:
        return {}
    default = default_remote_ref(repo)
    merged = set(git(repo, "rev-list", "--max-count=5000", default).stdout.split()) if default else set()
    pushed = set(git(repo, "rev-list", "--max-count=5000", "--remotes").stdout.split())
    return {intent: {"state": "merged" if sha in merged else "pushed" if sha in pushed else "committed", "commit": sha}
            for intent, sha in commits.items()}


# ── machine-local state: ~/.neuroflow/workbench/ ────────────────────────────────────────────────

def local_dir(home: Path) -> Path:
    return home / ".neuroflow" / "workbench"


def read_ledger(home: Path) -> dict:
    data = pj.read_json(local_dir(home) / "ledger.json")
    return data if isinstance(data, dict) and isinstance(data.get("levels"), dict) else {"levels": {}}


def write_ledger(home: Path, ledger: dict, now: datetime) -> None:
    cutoff = now - timedelta(days=LEDGER_DAYS)
    for key, entries in list(ledger["levels"].items()):
        ledger["levels"][key] = {iid: entry for iid, entry in entries.items() if (parse_time(entry.get("at")) or now) >= cutoff}
    write_json(local_dir(home) / "ledger.json", ledger)


def effect_present(src: Source, entry: dict) -> bool:
    """Whether a ledger entry's change is still in the working tree: its task file where it put it, in its column."""
    rel = entry.get("path")
    if not isinstance(rel, str) or not rel.startswith("tasks/"):
        return False
    path = src.memory / rel
    return path.is_file() and scalar(split_fm(read_text(path) or "")[0], "status") == entry.get("to")


def staged_entries(src: Source, ledger: dict, ids: set[str], committed: set[str]) -> dict[str, dict]:
    """A flowie's or hive's changes `apply` made whose commit never ran (no trailer yet), while the working tree still
    holds them: the next run commits them as they are and never makes them again."""
    out = {}
    for intent, entry in (ledger["levels"].get(src.key) or {}).items():
        if intent in ids and intent not in committed and isinstance(entry, dict) and effect_present(src, entry):
            out[intent] = entry
    return out


def ledger_states(src: Source, ledger: dict) -> dict[str, dict]:
    """Intents applied to a project's working tree (no trailer exists there): contained while their effect is."""
    out = {}
    for intent, entry in (ledger["levels"].get(src.key) or {}).items():
        path = src.repo / ".neuroflow" / entry.get("path", "")
        if not entry.get("path") or not path.is_file():
            continue
        fm = split_fm(read_text(path) or "")[0]
        if scalar(fm, "status") != entry.get("to"):
            continue
        rel = f".neuroflow/{entry['path']}"
        state = "worktree"
        if is_repo(src.repo):
            for ref, name in ((default_remote_ref(src.repo), "merged"), ("@{u}", "pushed"), ("HEAD", "committed")):
                shown = git(src.repo, "show", f"{ref}:{rel}") if ref else None
                if shown is not None and shown.returncode == 0 and scalar(split_fm(shown.stdout)[0], "status") == entry.get("to"):
                    state = name
                    break
        out[intent] = {"state": state}
    return out


# ── export ──────────────────────────────────────────────────────────────────────────────────────

def part_overhead(level: str, kind: str, field: str) -> int:
    return doc_bytes({"snap_schema": SNAP_SCHEMA, "level": level, "part": f"{kind}-000", field: [], "sha256": "0" * 64})


def fitting(level: str, kind: str, field: str, items: list[dict], source: str, name: str, withheld: list[dict]) -> list[dict]:
    """The items that fit a part on their own; one that does not is held back with a reason, never the whole run."""
    overhead = part_overhead(level, kind, field)
    out = []
    for item in items:
        if doc_bytes(item) + 1 + overhead > PART_MAX:
            withheld.append({"source": source, "item": str(item.get(name)), "reason": f"larger than one part ({PART_MAX // 1000} KB)"})
        else:
            out.append(item)
    return out


def pack(level: str, kind: str, items: list[dict], field: str) -> list[dict]:
    """Items packed into parts of at most PART_MAX bytes: `{kind}-000`, `{kind}-001`, … (each item fits alone)."""
    parts, current, size = [], [], 0
    overhead = part_overhead(level, kind, field)
    for item in items:
        weight = doc_bytes(item) + 1
        if current and size + weight + overhead > PART_MAX:
            parts.append(current)
            current, size = [], 0
        current.append(item)
        size += weight
    if current or not parts:
        parts.append(current)
    return [with_hash(allow("part", {"snap_schema": SNAP_SCHEMA, "level": level, "part": f"{kind}-{n:03d}", field: chunk}))
            for n, chunk in enumerate(parts)]


def build_level(src: Source, person: dict, scrub: Scrubber, home: Path, now: datetime, machine: str, fetch: bool) -> dict:
    withheld: list[dict] = []
    columns, archive_days = columns_of(src.memory / "tasks")
    people = roster(src, person, scrub, withheld)
    cards = export_cards(src, scrub, withheld, {entry["handle"].lower() for entry in people})
    known = {column["id"] for column in columns}
    for card in cards:
        if card["column"] not in known:
            known.add(card["column"])
            columns.append({"id": card["column"], "label": card["column"], "archive": False, "closed": False, "extra": True})
    for column in columns:
        label, hits = scrub.text(column["label"])
        column["label"] = column["id"] if held(hits) else label
    columns = [allow("column", column) for column in columns]
    index_only = src.key in person["index_only"]
    cards = fitting(src.key, "cards", "cards", cards, "tasks", "file", withheld)
    pages = fitting(src.key, "wiki", "pages", export_wiki(src, scrub, withheld, index_only), "wiki", "id", withheld)
    registry, panel = export_registry(src, scrub, withheld), export_panel(src, scrub, withheld)
    # The core part is one document. Panel texts are clipped by bytes and lists keep their newest entries, so it fits;
    # if it still does not, the panel goes, then the registry — said why — and only then is the level skipped.
    core = None
    for keep_panel, keep_registry in ((True, True), (False, True), (True, False), (False, False)):
        candidate = with_hash(allow("core", {
            "snap_schema": SNAP_SCHEMA, "level": src.key, "part": "core", "kind": src.kind, "label": src.label,
            "columns": columns, "archive_after_days": archive_days, "people": people,
            "registry": registry if keep_registry else [], "panel": panel if keep_panel else {},
            "phases": sorted(mg.canonical_phases() - {"setup"}), "card": src.card}))
        if doc_bytes(candidate) <= PART_MAX:
            core = candidate
            break
    too_big = f"larger than one part ({PART_MAX // 1000} KB) with the rest of the level"
    if core is None:
        return {"source": src, "skipped": f"its columns and people alone are larger than one part ({PART_MAX // 1000} KB)"}
    if not keep_panel:
        withheld.append({"source": "panel", "item": "the level's panel", "reason": too_big})
    if not keep_registry:
        withheld.append({"source": "registry", "item": "the project registry", "reason": too_big})
    parts = [core, *pack(src.key, "cards", cards, "cards"), *(pack(src.key, "wiki", pages, "pages") if pages else [])]
    oversized = [part["part"] for part in parts if doc_bytes(part) > PART_MAX]
    if oversized:
        return {"source": src, "skipped": f"{', '.join(oversized)} would exceed {PART_MAX} bytes"}
    source = git_source(src, home, fetch)
    applied: dict[str, dict] = {}
    if src.kind != "project" and source.get("git"):
        applied = landed_states(src.repo, trailer_commits(src.repo))
    elif src.kind == "project":
        applied = ledger_states(src, read_ledger(home))
    closed = {column["id"] for column in columns if column.get("closed")}
    # the page counts what was held back and says why; which items they were only the local preview says
    meta = allow("meta", {
        "snap_schema": SNAP_SCHEMA, "intent_schema": INTENT_SCHEMA, "level": src.key, "kind": src.kind, "label": src.label,
        "exported_at": iso(now), "machine": machine, "policy": src.policy, "working_tree": src.kind == "project",
        "index_only": index_only, "source": source,
        "parts": [allow("part_ref", {"id": part["part"], "sha256": part["sha256"], "bytes": doc_bytes(part)}) for part in parts],
        "applied": {intent: allow("applied", state) for intent, state in applied.items()},
        "withheld": [allow("withheld", item) for item in withheld],
        "counts": allow("counts", {"cards": len(cards), "open": sum(1 for card in cards if card["column"] not in closed),
                                   "pages": len(pages)})})
    return {"source": src, "meta": meta, "parts": parts, "withheld": withheld}


def freshness(meta: dict) -> str:
    """The tab's label: what the export saw, and what it could not."""
    src = meta.get("source") or {}
    if not src.get("git"):
        return f"files as they are on {meta.get('machine') or 'this machine'} (no git), exported {meta.get('exported_at')}"
    head = (src.get("head") or "?")[:7]
    text = f"{'working tree' if meta.get('working_tree') else 'clone'} on {src.get('branch') or '?'} @ {head}"
    if src.get("uncommitted_tasks"):
        text += f" + {src['uncommitted_tasks']} uncommitted task change{'s' if src['uncommitted_tasks'] != 1 else ''}"
    text += f" · upstream fetched {src.get('fetched_at') or 'never'}"
    return text + f" · from {meta.get('machine') or 'an unnamed machine'}"


def preview(levels: list[dict]) -> list[dict]:
    rows = []
    for item in levels:
        meta = item["meta"]
        size = sum(part["bytes"] for part in meta["parts"]) + doc_bytes(meta)
        rows.append({"level": meta["level"], "label": meta["label"], "kind": meta["kind"], "bytes": size,
                     "documents": len(meta["parts"]) + 1, "cards": meta["counts"]["cards"], "pages": meta["counts"]["pages"],
                     "index_only": meta["index_only"], "withheld": item["withheld"], "freshness": freshness(meta)})
    return rows


# ── what the store holds (an ArtifactData listing saved with out_dir) ──────────────────────────────

def saved_doc(data) -> tuple[dict | None, int | None]:
    """A saved document's body and version, whichever of the plain shapes the listing used."""
    if not isinstance(data, dict):
        return None, None
    for key in ("data", "body", "document"):
        if isinstance(data.get(key), dict) and set(data) <= {key, "version", "id", "path", "_version", "__version__", "updated", "created"}:
            version = data.get("version", data.get("_version", data.get("__version__")))
            return data[key], version if isinstance(version, int) else None
    body = dict(data)
    version = None
    for key in ("__version__", "_version", "version"):
        if isinstance(body.get(key), int):
            version = body.pop(key)
            break
    return body, version


def normal_path(rel: str) -> str:
    """A document path with the viewer's id as `me` (the listing may save under the resolved id)."""
    parts = rel.strip("/").split("/")
    if len(parts) >= 3 and parts[0] == "data" and parts[1] == "users":
        parts[2] = "me"
    return "/".join(parts)


def load_docs(folder: Path | None, versions: dict | None = None) -> dict[str, dict]:
    """Every saved document under `folder`: path → {body, version}; `versions` ({path: n}) fills missing versions."""
    docs: dict[str, dict] = {}
    if folder is None or not folder.is_dir():
        return docs
    extra = {normal_path(key): value for key, value in (versions or {}).items() if isinstance(value, int)}
    for path in sorted(folder.rglob("*.json")):
        rel = path.relative_to(folder).as_posix()[:-5]
        if "data/users/" in rel:
            rel = rel[rel.index("data/users/"):]
        try:
            body, version = saved_doc(json.loads(path.read_bytes().decode("utf-8-sig")))
        except (OSError, ValueError):
            continue
        if body is None:
            continue
        key = normal_path(rel)
        docs[key] = {"body": body, "version": version if version is not None else extra.get(key), "file": str(path)}
    return docs


def is_ancestor(repo: Path, older: str, newer: str) -> bool | None:
    proc = git(repo, "merge-base", "--is-ancestor", older, newer)
    return True if proc.returncode == 0 else False if proc.returncode == 1 else None


def known_commit(repo: Path, sha: str) -> bool:
    return git(repo, "cat-file", "-e", f"{sha}^{{commit}}").returncode == 0


def guard(item: dict, remote: dict | None, machine: str, home: Path) -> dict:
    """May this export overwrite what the store holds for its level? Upstream heads are compared, not HEADs."""
    meta, src = item["meta"], item["source"]
    if remote is None:
        return {"verdict": "write", "reason": "new level"}
    if not isinstance(remote.get("snap_schema"), int) or remote["snap_schema"] > SNAP_SCHEMA:
        return {"verdict": "refuse", "reason": "a newer neuroflow on another machine wrote this level; update neuroflow "
                                               "here first"}
    theirs, ours = remote.get("source") or {}, meta["source"]
    same = remote.get("machine") == machine and theirs.get("branch") == ours.get("branch")
    if same:
        return {"verdict": "write", "reason": "same machine and branch"}
    stored, local = theirs.get("upstream_head"), ours.get("upstream_head")
    if stored and local and stored != local and ours.get("git"):
        if not known_commit(src.repo, stored) and ours.get("shallow"):
            git(src.repo, "fetch", "--quiet", "--deepen=200", home=home, timeout=120)
        if not known_commit(src.repo, stored):
            return {"verdict": "skip", "reason": f"the upstream commit {stored[:7]} that {remote.get('machine') or 'another machine'} "
                                                  "exported is not in this clone, even after a fetch"}
        if is_ancestor(src.repo, local, stored):
            return {"verdict": "skip", "reason": f"this clone's upstream ({local[:7]}) is behind the one "
                                                  f"{remote.get('machine') or 'another machine'} exported ({stored[:7]}): pull first"}
    question = (f"{meta['label']} was last exported from {remote.get('machine') or 'an unnamed machine'} on "
                f"{theirs.get('branch') or 'no branch'}; this is {machine} on {ours.get('branch') or 'no branch'} — overwrite it?")
    return {"verdict": "ask", "reason": "another machine or branch", "question": question}


def plan_batches(entries: list[dict]) -> list[dict]:
    """Writes in order, in batches of at most BATCH_WRITES entries and BATCH_BYTES; a level's meta follows its parts."""
    batches: list[dict] = []
    current: list[dict] = []
    size = 0
    for entry in entries:
        weight = entry.pop("_bytes", 0) + 200
        if current and (len(current) >= BATCH_WRITES or size + weight > BATCH_BYTES):
            batches.append({"writes": current, "bytes": size})
            current, size = [], 0
        current.append(entry)
        size += weight
    if current:
        batches.append({"writes": current, "bytes": size})
    return batches


class MissingVersions(Exception):
    pass


def pinned(entry: dict, existing: dict | None, missing: list[str]) -> dict:
    """An entry pinned to the version the listing showed; a document the listing lacks is created (no pin)."""
    if existing is not None:
        if existing.get("version") is None:
            missing.append(f"{entry['collection']}/{entry['doc_id']}")
        else:
            entry["if_version"] = existing["version"]
    return entry


def level_writes(item: dict, docs: dict, out: Path, missing: list[str]) -> list[dict]:
    meta, key = item["meta"], item["meta"]["level"]
    writes = []
    remote_parts = {path.split("/")[-1]: doc for path, doc in docs.items() if path.startswith(parts_collection(key) + "/")}
    for part in item["parts"]:
        held_now = remote_parts.get(part["part"])
        if held_now and held_now["body"].get("sha256") == part["sha256"]:
            continue
        file = out / "docs" / key_file(key) / f"{part['part']}.json"
        write_doc(file, part)
        writes.append(pinned({"op": "set", "collection": parts_collection(key), "doc_id": part["part"], "file_path": str(file),
                              "_bytes": doc_bytes(part)}, held_now, missing))
    file = out / "docs" / key_file(key) / "meta.json"
    write_doc(file, meta)
    writes.append(pinned({"op": "set", "collection": meta_collection(), "doc_id": key, "file_path": str(file),
                          "_bytes": doc_bytes(meta)}, docs.get(f"{meta_collection()}/{key}"), missing))
    keep = {part["part"] for part in item["parts"]}
    for name, held_now in sorted(remote_parts.items()):
        if name not in keep:
            writes.append(pinned({"op": "delete", "collection": parts_collection(key), "doc_id": name}, held_now, missing))
    return writes


def outcome_writes(plan: dict, listed: dict, out: Path, home: Path, now: datetime, missing: list[str]) -> tuple[list[dict], list[dict]]:
    """The outcome of every intent the plan decided, as pinned updates. An accepted change that is not in git yet gets
    none, and neither do the intents coalesced into it: they stay claimed and the next pickup finishes them."""
    writes, open_ = [], []
    ledger = read_ledger(home)

    def write(intent_id: str, outcome: dict) -> None:
        outcome = {key: value for key, value in outcome.items() if key not in ("noop", "action")}
        outcome["at"] = iso(now)
        file = out / "docs" / "intents" / f"{intent_id}.json"
        write_doc(file, {"status": "done", "outcome": outcome})
        writes.append(pinned({"op": "update", "collection": intents_collection(), "doc_id": intent_id, "file_path": str(file),
                              "_bytes": 400}, listed.get(f"{intents_collection()}/{intent_id}") or {"version": None}, missing))

    for level in plan.get("levels", []):
        repo = Path(level["repo"])
        commits = trailer_commits(repo) if level["kind"] != "project" and is_repo(repo) else {}
        states = landed_states(repo, commits) if commits else {}
        entries = ledger["levels"].get(level["key"]) or {}
        verdicts = level.get("verdicts", {})
        landed: dict[str, dict | None] = {}
        for intent_id, verdict in verdicts.items():
            if verdict.get("result") != "applied" or verdict.get("noop") or str(verdict.get("note", "")).startswith("cancelled "):
                continue
            if level["kind"] == "project":
                landed[intent_id] = {"state": "worktree"} if intent_id in entries else None
            else:
                landed[intent_id] = states.get(intent_id)
        for intent_id, verdict in verdicts.items():
            outcome = dict(verdict)
            lead = outcome.get("into") if outcome.get("result") == "coalesced" else intent_id
            if lead in landed and landed[lead] is None:
                open_.append({"intent": intent_id, "reason": "its change is not in git yet" if level["kind"] != "project"
                              else "its change is not in the working tree"})
                continue
            if outcome.get("result") == "applied" and intent_id in landed:
                outcome.update(landed[intent_id] or {})
            write(intent_id, outcome)
    for intent_id, verdict in (plan.get("rejected") or {}).items():
        write(intent_id, verdict)
    return writes, open_


def cmd_export(args, home: Path, now: datetime) -> tuple[int, dict]:
    person = consent(home)
    machine = args.machine or person["machine"]
    if not machine:
        raise UsageError("no machine label: set workbench_machine in ~/.neuroflow/user.yaml (/dashboard --web asks once)")
    sources, unkeyed = discover(home, args.root, fetch=args.fetch)
    rows = {row["level"]: row for row in level_rows(sources, person)}
    wanted = set(args.level or [])
    if wanted - set(rows):
        raise UsageError(f"not a level of this machine: {', '.join(sorted(wanted - set(rows)))}")
    chosen = [src for src in sources if rows[src.key]["mirrored"] and (not wanted or src.key in wanted)]
    if wanted:
        refused = [key for key in wanted if not rows[key]["mirrored"]]
        if refused:
            raise UsageError("not mirrored: " + "; ".join(f"{key} ({rows[key]['reason']})" for key in refused))
    scrub = Scrubber(pii_settings(args.pii_config or person["pii_config"]))
    out = Path(args.out)
    built, skipped = [], []
    for src in chosen:
        item = build_level(src, person, scrub, home, now, machine, False)  # discover fetched them
        if "skipped" in item:  # one level too large never stops the others
            skipped.append({"level": src.key, "label": src.label, "reason": item["skipped"]})
        else:
            built.append(item)
    result: dict = {"machine": machine, "exported_at": iso(now), "levels": preview(built), "unkeyed": unkeyed,
                    "skipped": skipped,
                    "not_mirrored": [row for row in rows.values() if not row["mirrored"]],
                    # what gc deletes from the workbench, where it holds them: the preview names them
                    "purge": [{"level": row["level"], "label": row["label"], "reason": row.get("reason")}
                              for row in rows.values() if row.get("purge")]}
    for item in built:
        key = item["meta"]["level"]
        write_doc(out / "docs" / key_file(key) / "meta.json", item["meta"])
        for part in item["parts"]:
            write_doc(out / "docs" / key_file(key) / f"{part['part']}.json", part)
    findings = any(row["withheld"] for row in result["levels"]) or bool(unkeyed) or bool(skipped)
    total = sum(row["bytes"] for row in result["levels"])
    if total > SIZE_WARN:
        def wiki_bytes(item: dict) -> int:
            return sum(part["bytes"] for part in item["meta"]["parts"] if part["id"].startswith("wiki-"))

        heavy = max(built, key=wiki_bytes)
        hint = (f"; the wiki of {heavy['meta']['label']} is {wiki_bytes(heavy) // 1024} KB of it — with "
                f"{heavy['meta']['level']} in workbench_index_only its pages go up without their bodies"
                if wiki_bytes(heavy) and not heavy["meta"]["index_only"] else "")
        result["warnings"] = [f"this export is {total / 1_000_000:.1f} MB, slow for the page to load{hint}"]
        findings = True
    if args.remote is not None or args.outcomes:
        versions = json.loads(Path(args.versions).read_text(encoding="utf-8")) if args.versions else None
        docs = load_docs(Path(args.remote), versions) if args.remote else {}
        missing: list[str] = []
        entries: list[dict] = []
        saved = (active_record(home) or {}).get("prefs")
        if args.remote and isinstance(saved, dict) and saved and f"{meta_collection()}/{PREFS_DOC}" not in docs:
            # a page without settings (a new page, or one rebuilt) gets back the copy the record keeps
            file = out / "docs" / "prefs.json"
            write_doc(file, saved)
            entries.append({"op": "set", "collection": meta_collection(), "doc_id": PREFS_DOC, "file_path": str(file),
                            "_bytes": doc_bytes(saved)})
            result["prefs"] = "restored from the record"
        if args.outcomes:
            plan = json.loads(Path(args.outcomes).read_text(encoding="utf-8"))
            listed = load_docs(Path(args.intents), versions) if args.intents else {}
            writes, open_ = outcome_writes(plan, listed, out, home, now, missing)
            entries += writes
            result["outcomes"] = {"written": len(writes), "not_yet": open_}
            findings = findings or bool(open_)
        verdicts = {}
        for item in built:
            key = item["meta"]["level"]
            verdict = guard(item, (docs.get(f"{meta_collection()}/{key}") or {}).get("body"), machine, home)
            if verdict["verdict"] == "ask" and key in (args.overwrite or []):
                verdict = {"verdict": "write", "reason": "overwrite confirmed"}
            verdicts[key] = verdict
            if verdict["verdict"] == "write":
                entries += level_writes(item, docs, out, missing)
        if missing:
            raise MissingVersions("the listing shows no version for: " + ", ".join(sorted(missing)) +
                                  " — write the versions the ArtifactData result names as {\"path\": version} to a JSON "
                                  "file and pass it with --versions")
        batches = plan_batches(entries)
        result.update({"guard": verdicts, "batches": batches,
                       "upload": {"documents": sum(len(batch["writes"]) for batch in batches),
                                  "bytes": sum(batch["bytes"] for batch in batches), "batches": len(batches)}})
        findings = findings or any(v["verdict"] != "write" for v in verdicts.values())
        write_json(out / "batches.json", batches)
    return (1 if findings else 0), result


# ── intents: pickup, validation, apply ──────────────────────────────────────────────────────────

def intent_docs(folder: Path, versions: dict | None = None) -> dict[str, dict]:
    """intent id → {body, version} from a listing of data/users/me/inbox/intents saved with out_dir."""
    out = {}
    for path, doc in load_docs(folder, versions).items():
        parts = path.split("/")
        if len(parts) >= 2 and parts[-2] == "intents":
            out[parts[-1]] = doc
    return out


def schema_problem(intent: dict) -> str | None:
    """None when the intent is a well-formed intent_schema 1 document; else what is wrong with it ('schema: …')."""
    version = intent.get("intent_schema")
    if version != INTENT_SCHEMA:
        translate = TRANSLATE.get(version) if isinstance(version, int) else None
        if translate is None:
            return f"schema: intent_schema {version!r} is not one this neuroflow knows (it knows {INTENT_SCHEMA})"
        intent.update(translate(dict(intent)))
    op = intent.get("op")
    if op not in OPS:
        return f"schema: op {op!r} is not move, add or cancel"
    if not valid_level_key(intent.get("level")):
        return "schema: no valid level"
    if parse_time(intent.get("created_at")) is None:
        return "schema: no created_at time"
    after = intent.get("after")
    if after is not None and not (isinstance(after, str) and INTENT_ID.match(after)):
        return "schema: after is not an intent id"
    target = intent.get("target")
    if op in ("move", "cancel"):
        if not isinstance(target, dict) or len(target) != 1 or not any(
                isinstance(target.get(key), str) and target[key] for key in ("slug", "intent")):
            return "schema: target must name one slug or one intent"
        if op == "cancel" and "intent" not in target:
            return "schema: a cancel names the intent it cancels"
    if op == "move":
        if not isinstance(intent.get("to"), str) or not intent["to"] or not isinstance(intent.get("from"), str):
            return "schema: a move needs from and to"
        if "slug" in target and not (isinstance(intent.get("base"), str) and SHA.match(intent["base"])):
            return "schema: a move of an exported card carries its content hash (base)"
    if op == "add":
        fields = intent.get("fields")
        if not isinstance(fields, dict) or not isinstance(fields.get("title"), str) or not fields["title"].strip():
            return "schema: an add needs a title"
        if len(fields["title"]) > 200:
            return "schema: the title is longer than 200 characters"
        if fields.get("due") not in (None, "") and not (isinstance(fields["due"], str) and DATE.match(fields["due"])):
            return "schema: due is not YYYY-MM-DD"
        if fields.get("tags") is not None and not (isinstance(fields["tags"], list) and all(isinstance(t, str) for t in fields["tags"])):
            return "schema: tags must be a list of words"
        if intent.get("to") is not None and not isinstance(intent["to"], str):
            return "schema: to must be a column id"
    return None


# Known older intent formats → a function that rewrites one into intent_schema 1. None exist yet; an unknown
# version is rejected with the reason 'schema', never dropped.
TRANSLATE: dict[int, object] = {}


def claim_of(intent: dict) -> tuple[str | None, datetime | None]:
    claim = intent.get("claim") if isinstance(intent.get("claim"), dict) else {}
    return claim.get("machine"), parse_time(claim.get("claimed_at"))


def cmd_pickup(args, home: Path, now: datetime) -> tuple[int, dict]:
    person = consent(home)
    machine = args.machine or person["machine"]
    if not machine:
        raise UsageError("no machine label: set workbench_machine in ~/.neuroflow/user.yaml")
    versions = json.loads(Path(args.versions).read_text(encoding="utf-8")) if args.versions else None
    docs = intent_docs(Path(args.intents), versions)
    sources, _ = discover(home, args.root)
    here = {src.key: src for src in sources}
    claims, skipped, missing = [], [], []
    out = Path(args.out) if args.out else Path(args.intents).parent / "claims"
    held_back: set[str] = set()
    for intent_id, doc in sorted(docs.items(), key=lambda pair: (str(pair[1]["body"].get("created_at")), pair[0])):
        after = doc["body"].get("after")
        # a chain is claimed whole: a link whose earlier link waits elsewhere waits too
        if after in held_back or (after in docs and docs[after]["body"].get("status") == "claimed"
                                  and claim_of(docs[after]["body"])[0] != machine
                                  and (claim_of(docs[after]["body"])[1] or now) > now - CLAIM_TTL):
            if doc["body"].get("status") != "done":
                held_back.add(intent_id)
                skipped.append({"intent": intent_id, "reason": f"waits for {after}"})
    for intent_id, doc in sorted(docs.items(), key=lambda pair: (str(pair[1]["body"].get("created_at")), pair[0])):
        if intent_id in held_back:
            continue
        body = doc["body"]
        status = body.get("status")
        if status == "done":
            continue
        who, when = claim_of(body)
        if status == "claimed" and who != machine and when is not None and now - when < CLAIM_TTL:
            skipped.append({"intent": intent_id, "reason": f"claimed by {who} {int((now - when).total_seconds() // 60)} min ago"})
            continue
        level = body.get("level")
        if level not in here and valid_level_key(level):
            label = str(level)
            reason = (f"open Claude Code in the project {label[len('project+'):]}" if label.startswith("project+") else
                      f"{label[len('hive+'):].replace('+', '/')} is not cloned on this machine" if label.startswith("hive+")
                      else "your flowie is not linked on this machine")
            skipped.append({"intent": intent_id, "level": level, "reason": reason})
            continue  # a malformed intent is claimed too, so validate can reject it with its reason
        file = out / f"{intent_id}.json"
        write_doc(file, {"status": "claimed", "claim": {"machine": machine, "claimed_at": iso(now)}})
        claims.append(pinned({"op": "update", "collection": intents_collection(), "doc_id": intent_id, "file_path": str(file),
                              "_bytes": 200}, doc, missing))
    if missing:
        raise MissingVersions("the listing shows no version for: " + ", ".join(missing) + " — pass them with --versions")
    batches = plan_batches(claims)
    return (1 if skipped else 0), {"machine": machine, "claim": len(claims), "batches": batches, "skipped": skipped}


def board_state(src: Source) -> dict:
    tasks = pj.read_board(src.memory / "tasks", details=True)
    columns, _ = columns_of(src.memory / "tasks")
    return {"cards": {task["slug"]: task for task in tasks}, "columns": {c["id"]: c for c in columns}}


def unique_slug(title: str, taken: set[str]) -> str:
    base = mg.slugify(title)
    slug, n = base, 2
    while slug in taken:
        slug, n = f"{base}-{n}", n + 1
    return slug


RELEASED_LATE = "already applied — the release came after it; move the card back"


def validate_level(src: Source, intents: list[tuple[str, dict]], done: dict[str, dict], machine: str,
                   people: set[str], phases: set[str], applied: dict[str, dict], staged: dict[str, dict] | None = None) -> dict:
    """Verdicts and actions for one level's intents, in creation order (neuroflow-core → Workbench snapshot):
    an accepted intent's result is the base of the ones after it, consecutive moves of one card merge into one,
    an added card's slug comes from the add, and a chain whose first intent failed fails with 'depends on'.
    `staged` holds the ledger entries of changes a run made without committing them: each keeps the verdict it had and
    becomes a `commit` action, never a second change."""
    staged = staged or {}
    commits: dict[str, dict] = {}          # lead intent → the commit action of a change a run made, not committed
    state = board_state(src)
    cards = {slug: {"column": task["column"], "sha256": task["sha256"], "file": f"tasks/{task['file']}", "legacy": task["legacy"],
                    "conflicted": task["conflicted"]} for slug, task in state["cards"].items()}
    columns = state["columns"]
    taken = set(cards)
    verdicts: dict[str, dict] = {}
    actions: list[dict] = []
    planned_slug: dict[str, str] = {}      # add intent id → its slug (this run, or an earlier outcome)
    touched: dict[str, dict] = {}          # slug → the last action that touched it in this run
    for intent_id, body in done.items():
        outcome = body.get("outcome") if isinstance(body.get("outcome"), dict) else {}
        if body.get("op") == "add" and outcome.get("slug"):
            planned_slug[intent_id] = outcome["slug"]
    cancels = {}
    for intent_id, body in intents:
        if body.get("op") == "cancel" and schema_problem(body) is None:
            cancels.setdefault(body["target"]["intent"], intent_id)
    present = dict(intents)
    for intent_id, body in intents:
        problem = schema_problem(body)
        if problem:
            verdicts[intent_id] = {"result": "rejected", "reason": problem}
            continue
        op = body["op"]
        if intent_id in applied:
            # its trailer (flowie, hive) or ledger entry (project) is already there: a run that stopped half way
            verdicts[intent_id] = {"result": "applied", **applied[intent_id],
                                   "note": RELEASED_LATE if body.get("cancel_requested_at") else "already in git"}
            continue
        if intent_id in staged:
            # applied by a run that stopped before its commit: commit it as it is — never add, move or judge it again,
            # and a release that came after it cannot undo it
            entry = staged[intent_id]
            verdict = dict(entry.get("verdict") or {"result": "applied", "slug": entry.get("slug"), "column": entry.get("to")})
            if body.get("cancel_requested_at"):
                verdict["note"] = RELEASED_LATE
            verdicts[intent_id] = verdict
            lead = entry.get("lead") or intent_id
            if lead not in commits:
                commits[lead] = {"op": "commit", "of": entry.get("op"), "intents": [], "lead": lead, "slug": entry.get("slug"),
                                 "to": entry.get("to"), "path_to": entry.get("path"), "paths": list(entry.get("paths") or [])}
                actions.append(commits[lead])
            commits[lead]["intents"].append(intent_id)
            if entry.get("op") == "add" and entry.get("slug"):
                planned_slug[intent_id] = entry["slug"]
            continue
        if op == "cancel":
            target = body["target"]["intent"]
            prior = verdicts.get(target) or ((done[target].get("outcome") or {}) if target in done else None)
            if prior is None and target not in present:
                verdicts[intent_id] = {"result": "rejected", "reason": f"{target} is not in the workbench"}
            elif prior is not None and prior.get("result") in ("applied", "coalesced"):
                verdicts[intent_id] = {"result": "rejected", "reason": "that change is already applied — move the card back instead"}
            else:
                verdicts[intent_id] = {"result": "applied", "note": f"cancelled {target}"}
            continue
        if body.get("cancel_requested_at"):
            verdicts[intent_id] = {"result": "cancelled", "by": "release"}
            continue
        if intent_id in cancels:
            verdicts[intent_id] = {"result": "cancelled", "by": cancels[intent_id]}
            continue
        after = body.get("after")
        if after:
            # a chain whose earlier link failed fails too; an earlier link the store no longer holds (gc) leaves the
            # checks below to decide, against the files as they are
            before = verdicts.get(after) or ((done[after].get("outcome") or {}) if after in done else None)
            if before is not None and before.get("result") in ("rejected", "cancelled", "conflict"):
                verdicts[intent_id] = {"result": "rejected", "reason": f"depends on {after}"}
                continue
        if op == "add":
            fields = body["fields"]
            to = body.get("to") or "inbox"
            owner = fields.get("owner")
            if to not in columns or columns[to].get("archive"):
                verdicts[intent_id] = {"result": "rejected", "reason": f"the board has no column {to} to add to"}
            elif owner and str(owner).lower() not in people:
                verdicts[intent_id] = {"result": "rejected", "reason": f"{owner} is not on the level's roster"}
            elif fields.get("phase") and fields["phase"] not in phases:
                verdicts[intent_id] = {"result": "rejected", "reason": f"{fields['phase']} is not a phase"}
            else:
                slug = unique_slug(fields["title"], taken)
                taken.add(slug)
                planned_slug[intent_id] = slug
                action = {"op": "add", "intents": [intent_id], "slug": slug, "to": to, "path_to": f"tasks/{to}/{slug}.md",
                          "fields": {key: fields[key] for key in ("title", "owner", "due", "phase", "tags", "project")
                                     if fields.get(key) not in (None, "", [])}}
                actions.append(action)
                touched[slug] = action
                cards[slug] = {"column": to, "sha256": None, "file": action["path_to"], "legacy": False, "conflicted": False,
                               "planned": True}
                verdicts[intent_id] = {"result": "applied", "slug": slug, "column": to}
            continue
        # a move
        target = body["target"]
        slug = target.get("slug") or planned_slug.get(target.get("intent"))
        if not slug:
            verdicts[intent_id] = {"result": "rejected", "reason": f"depends on {target.get('intent')}, whose card was not added"}
            continue
        card = cards.get(slug)
        to, came_from = body["to"], body["from"]
        if card is None:
            verdicts[intent_id] = {"result": "conflict", "reason": "the task no longer exists on the board", "column": None}
            continue
        if card["legacy"]:
            verdicts[intent_id] = {"result": "rejected", "reason": "a legacy task file — move it once with /tasks --move, "
                                                                 "which brings it into its column folder"}
            continue
        if card["conflicted"]:
            verdicts[intent_id] = {"result": "rejected", "reason": "the task file holds merge-conflict markers (neuroflow-core → Merge safety)"}
            continue
        if to not in columns or columns[to].get("extra"):
            verdicts[intent_id] = {"result": "rejected", "reason": f"the board has no column {to}"}
            continue
        # The content hash leaves out what a move writes, so it holds across earlier moves: every move of an exported
        # card is checked against it, chained or not. The column is checked against the state the earlier accepted
        # intents of this run left (`cards` follows them).
        half_done = False
        if not card.get("planned") and "slug" in target and card["sha256"] != body.get("base"):
            verdicts[intent_id] = {"result": "conflict", "reason": "the task changed since your workbench was refreshed",
                                   "column": card["column"]}
            continue
        if card["column"] != came_from:
            if not card.get("planned") and card["column"] == to and slug not in touched:
                half_done = True   # moved by a run that stopped before its commit: commit it, never move it twice
            else:
                verdicts[intent_id] = {"result": "conflict", "reason": f"the task is now in {card['column']}",
                                       "column": card["column"]}
                continue
        previous = touched.get(slug)
        if previous is not None and previous["op"] == "add":
            # moves of a card added in this run go into the add: the file is written once, in its last column
            previous.update({"to": to, "path_to": f"tasks/{to}/{slug}.md", "intents": [*previous["intents"], intent_id]})
            verdicts[intent_id] = {"result": "coalesced", "into": previous["intents"][0]}
            verdicts[previous["intents"][0]]["column"] = to
            card.update({"column": to, "file": previous["path_to"]})
            continue
        if previous is not None and previous["op"] == "move":
            # consecutive moves of one card merge into the later one; the earlier ones are coalesced into it
            for earlier in previous["intents"]:
                verdicts[earlier] = {"result": "coalesced", "into": intent_id}
            previous.update({"intents": [*previous["intents"], intent_id], "to": to, "path_to": f"tasks/{to}/{slug}.md",
                             "lead": intent_id})
            card.update({"column": to, "file": previous["path_to"]})
            verdicts[intent_id] = {"result": "applied", "slug": slug, "column": to}
            continue
        start = came_from if half_done else card["column"]
        action = {"op": "move", "intents": [intent_id], "lead": intent_id, "slug": slug, "from": start, "to": to,
                  "path_from": f"tasks/{start}/{slug}.md" if half_done else card["file"], "path_to": f"tasks/{to}/{slug}.md",
                  "base": card["sha256"], "half_done": half_done}
        actions.append(action)
        touched[slug] = action
        card.update({"column": to, "file": action["path_to"]})
        verdicts[intent_id] = {"result": "applied", "slug": slug, "column": to}
    # a merged move that ends where it began changes nothing
    final = []
    for action in actions:
        if action["op"] == "move" and not action["half_done"] and action["path_from"] == action["path_to"]:
            for intent in action["intents"]:
                if verdicts[intent].get("result") == "applied":
                    verdicts[intent].update({"noop": True, "note": "no change: the card ends where it was"})
            continue
        final.append(action)
    return {"actions": final, "verdicts": verdicts}


def cmd_validate(args, home: Path, now: datetime) -> tuple[int, dict]:
    person = consent(home)
    machine = args.machine or person["machine"]
    if not machine:
        raise UsageError("no machine label: set workbench_machine in ~/.neuroflow/user.yaml")
    versions = json.loads(Path(args.versions).read_text(encoding="utf-8")) if args.versions else None
    docs = intent_docs(Path(args.intents), versions)
    sources, _ = discover(home, args.root)
    rows = {row["level"]: row for row in level_rows(sources, person)}
    here = {src.key: src for src in sources}
    phases = mg.canonical_phases() - {"setup"}
    mine = {iid: doc["body"] for iid, doc in docs.items() if doc["body"].get("status") == "claimed"
            and claim_of(doc["body"])[0] == machine}
    done = {iid: doc["body"] for iid, doc in docs.items() if doc["body"].get("status") == "done"}
    pending_cancels = {iid: doc["body"] for iid, doc in docs.items() if doc["body"].get("status") == "pending"
                       and doc["body"].get("op") == "cancel"}
    by_level: dict[str, list] = {}
    rejected: dict[str, dict] = {}
    for iid, body in mine.items():
        level = body.get("level")
        problem = schema_problem(body)
        if problem:
            rejected[iid] = {"result": "rejected", "reason": problem}
            continue
        if level not in here:
            rejected[iid] = {"result": "rejected", "reason": "its level is not on this machine"}
            continue
        if not rows[level]["mirrored"]:
            rejected[iid] = {"result": "rejected", "reason": f"the level is not mirrored ({rows[level]['reason']})"}
            continue
        by_level.setdefault(level, []).append((iid, body))
    for iid, body in pending_cancels.items():
        if body.get("level") in by_level and (body.get("target") or {}).get("intent") in mine:
            by_level[body["level"]].append((iid, body))  # a cancel the page queued after the claim still counts
    plan: dict = {"machine": machine, "validated_at": iso(now), "levels": [], "rejected": rejected}
    ledger = read_ledger(home)
    for key, items in by_level.items():
        src = here[key]
        items.sort(key=lambda pair: (str(pair[1].get("created_at")), pair[0]))
        people = {entry["handle"].lower() for entry in roster(src, person)}
        ids = {iid for iid, _ in items}
        applied, staged = {}, {}
        if src.kind != "project" and is_repo(src.repo):
            trailers = trailer_commits(src.repo)
            applied = landed_states(src.repo, {iid: sha for iid, sha in trailers.items() if iid in ids})
            staged = staged_entries(src, ledger, ids, set(trailers))
        elif src.kind == "project":
            applied = {iid: {"state": "worktree"} for iid in (ledger["levels"].get(key) or {}) if iid in ids}
        result = validate_level(src, items, done, machine, people, phases, applied, staged)
        plan["levels"].append({"key": key, "kind": src.kind, "label": src.label, "repo": str(src.repo),
                               "memory": str(src.memory), "push": {"flowie": "flowie", "hive": "hive"}.get(src.kind, "none"),
                               "actions": result["actions"], "verdicts": result["verdicts"]})
    if args.out:
        write_json(Path(args.out), plan)
    counts: dict[str, int] = {}
    for level in plan["levels"]:
        for verdict in level["verdicts"].values():
            counts[verdict["result"]] = counts.get(verdict["result"], 0) + 1
    for verdict in rejected.values():
        counts["rejected"] = counts.get("rejected", 0) + 1
    summary = {"machine": machine, "counts": counts,
               "levels": [{"key": level["key"], "label": level["label"], "actions": len(level["actions"]), "push": level["push"]}
                          for level in plan["levels"]]}
    issues = any(name in counts for name in ("conflict", "rejected"))
    return (1 if issues else 0), {**summary, "plan": str(args.out) if args.out else plan}


def set_fields(text: str, values: dict[str, str]) -> str:
    """The task file with `status` and `updated` set in its frontmatter (in place, or added), line endings kept."""
    newline = "\r\n" if "\r\n" in text else "\n"
    bom = "\ufeff" if text.startswith("\ufeff") else ""
    lines = text.lstrip("\ufeff").replace("\r\n", "\n").split("\n")
    if not lines or lines[0].strip() != "---":
        raise ValueError("the task file has no frontmatter")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise ValueError("the task file's frontmatter does not end")
    for key, value in values.items():
        at = next((i for i in range(1, end) if re.match(rf"^{key}:", lines[i])), None)
        if at is not None:
            lines[at] = f"{key}: {value}"
            continue
        anchor = next((i for i in range(1, end) if re.match(r"^created:", lines[i])), None)
        position = anchor + 1 if anchor is not None and key == "updated" else end
        lines.insert(position, f"{key}: {value}")
        end += 1
    return bom + newline.join(lines)


def new_task(fields: dict, column: str, today: str) -> str:
    lines = ["---", f"title: {json.dumps(fields['title'].strip(), ensure_ascii=False)}", f"status: {column}"]
    if fields.get("owner"):
        lines.append(f"owner: {fields['owner']}")
    if fields.get("due"):
        lines.append(f"due: {fields['due']}")
    if fields.get("phase"):
        lines.append(f"phase: {fields['phase']}")
    if fields.get("tags"):
        lines.append("tags: [" + ", ".join(mg.sc.yaml_scalar(tag, in_flow=True) for tag in fields["tags"]) + "]")
    lines += [f"created: {today}", f"updated: {today}"]
    if fields.get("project"):
        lines.append(f"project: {mg.sc.yaml_scalar(str(fields['project']))}")
    return "\n".join(lines + ["---", "", ""])


def known_to_git(repo: Path, rel: str) -> bool:
    """Whether a commit by path may name `rel`: it is in the index or in HEAD (a staged deletion counts)."""
    if not is_repo(repo):
        return False
    return (git(repo, "ls-files", "--error-unmatch", "--", rel).returncode == 0
            or git(repo, "cat-file", "-e", f"HEAD:{rel}").returncode == 0)


def summary_of(actions: list[dict]) -> str:
    kind = lambda a: a.get("of") if a["op"] == "commit" else a["op"]  # noqa: E731 — a commit names what was done
    words = [f"add {a['slug']}" if kind(a) == "add" else f"move {a['slug']} → {a['to']}" for a in actions]
    head = ", ".join(words[:3]) + (f" and {len(words) - 3} more" if len(words) > 3 else "")
    return f"tasks: workbench — {head}"


def restage(repo: Path, rel: str) -> None:
    """Stages a path again as the working tree has it (the file, or its deletion); a path git never saw is left alone.
    A pull with --autostash between two runs can leave a staged rename half unstaged."""
    if (repo / rel).exists() or git(repo, "ls-files", "--error-unmatch", "--", rel).returncode == 0:
        proc = git(repo, "add", "-A", "--", rel)
        if proc.returncode != 0:
            raise ValueError(pj.first_line(proc))


def cmd_apply(args, home: Path, now: datetime) -> tuple[int, dict]:
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    level = next((item for item in plan.get("levels", []) if item["key"] == args.level), None)
    if level is None:
        raise UsageError(f"the plan has no level {args.level}")
    repo, memory = Path(level["repo"]), Path(level["memory"])
    tasks_rel = "tasks" if level["kind"] != "project" else ".neuroflow/tasks"
    today = args.today or date.today().isoformat()
    git_level = is_repo(repo)
    applied, failed, paths, intents = [], [], [], []
    ledger = read_ledger(home)
    entries = ledger["levels"].setdefault(level["key"], {})
    if level["kind"] != "project" and git_level:
        # a flowie's or hive's entry lives only until its commit exists
        landed = set(trailer_commits(repo)) & set(entries)
        for intent in landed:
            del entries[intent]
        if landed:
            write_ledger(home, ledger, now)
    for action in level["actions"]:
        target = memory / action["path_to"]
        rel_to = f"{tasks_rel}/{action['path_to'][len('tasks/'):]}"
        try:
            if action["op"] == "commit":
                # made by a run that stopped before its commit (the ledger names it): stage it again, change nothing
                for rel in action.get("paths") or []:
                    if git_level:
                        restage(repo, rel)
                touched = list(action.get("paths") or [])
            elif action["op"] == "add":
                if target.exists():
                    raise ValueError(f"{action['path_to']} already exists")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(new_task(action["fields"], action["to"], today).encode("utf-8"))
                if git_level and level["kind"] != "project":
                    stage = git(repo, "add", "--", rel_to)
                    if stage.returncode != 0:
                        raise ValueError(pj.first_line(stage))
                touched = [rel_to]
            else:
                rel_from = f"{tasks_rel}/{action['path_from'][len('tasks/'):]}"
                # Only where the check saw the file — or, for a move a run left half done, where that run put it. A
                # file anywhere else moved after the check (a pull brought a teammate's move): it is not touched, and
                # the intent gets no outcome, so the next run checks it again.
                current = target if action.get("half_done") else memory / action["path_from"]
                if not current.is_file():
                    now_in = [path.parent.name for path in sorted((memory / "tasks").glob(f"*/{action['slug']}.md")) if path.is_file()]
                    raise ValueError(f"the task moved after the check (it is in {now_in[0]} now): the next run checks it "
                                     "again" if now_in else f"{action['path_from']} is gone")
                rel_now = f"{tasks_rel}/{current.relative_to(memory / 'tasks').as_posix()}"
                text = current.read_bytes().decode("utf-8")
                if action.get("base") and pj.task_hash(text) != action["base"]:
                    raise ValueError("the task changed after the check: refresh the workbench and move it again")
                if current != target and target.exists():
                    raise ValueError(f"{action['path_to']} already exists")
                current.write_bytes(set_fields(text, {"status": action["to"], "updated": today}).encode("utf-8"))
                if current != target:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    tracked = git_level and git(repo, "ls-files", "--error-unmatch", "--", rel_now).returncode == 0
                    if tracked:
                        moved = git(repo, "mv", "--", rel_now, rel_to)
                        if moved.returncode != 0:
                            raise ValueError(pj.first_line(moved))
                    else:
                        current.rename(target)
                if git_level and level["kind"] != "project":
                    stage = git(repo, "add", "--", rel_to)
                    if stage.returncode != 0:
                        raise ValueError(pj.first_line(stage))
                # the commit names where the file went and every path it came from that git knows
                touched = [rel_to, rel_from, rel_now]
        except (OSError, ValueError, UnicodeDecodeError) as error:
            failed.append({"slug": action["slug"], "intents": action["intents"], "reason": str(error)})
            continue
        applied.append({"slug": action["slug"], "op": action.get("of") or action["op"], "to": action["to"], "intents": action["intents"]})
        paths += [path for path in dict.fromkeys(touched) if path not in paths]
        intents += action["intents"]
        if action["op"] != "commit":
            # Recorded the moment the change is made, before any commit: a project's entry says the change is in its
            # working tree; a flowie's or hive's lets the next run commit a change whose commit never ran, never redo it.
            lead = action.get("lead") or action["intents"][0]
            for intent in action["intents"]:
                entries[intent] = {"op": action["op"], "slug": action["slug"], "to": action["to"], "path": action["path_to"],
                                   "paths": list(dict.fromkeys(touched)), "lead": lead,
                                   "verdict": dict((level.get("verdicts") or {}).get(intent) or {}), "at": iso(now)}
            write_ledger(home, ledger, now)
    result: dict = {"level": level["key"], "applied": applied, "failed": failed, "push": level["push"]}
    # a commit by path names only paths git knows (in the index or in HEAD): a file renamed twice in one run leaves an
    # intermediate path git never saw
    paths = [path for path in paths if known_to_git(repo, path)]
    if applied and level["kind"] != "project" and git_level:
        message = summary_of([a for a in level["actions"] if any(i in intents for i in a["intents"])]) + "\n\n" + \
            "\n".join(f"{TRAILER}: {intent}" for intent in intents) + "\n"
        message_file = Path(args.plan).with_name(f"commit-{key_file(level['key'])}.txt")
        message_file.write_bytes(message.encode("utf-8"))
        result["commit"] = {"argv": ["git", "-C", str(repo), "commit", "-F", str(message_file), "--", *paths],
                            "message": message, "paths": paths}
    return (1 if failed else 0), result


# ── pending.json: what the mod's board and band show ────────────────────────────────────────────

def cmd_pending(args, home: Path, now: datetime) -> tuple[int, dict]:
    docs = intent_docs(Path(args.intents))
    finished = set()
    if args.plan and Path(args.plan).is_file():
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
        for level in plan.get("levels", []):
            finished |= {iid for iid, v in level.get("verdicts", {}).items() if v.get("result") != "applied" or v.get("noop")}
        finished |= set(plan.get("rejected", {}))
    sources, _ = discover(home, args.root)
    here = {src.key: src for src in sources}
    levels: dict[str, dict] = {}
    # an undone change (a cancel or a release waits for it) is no longer waiting, as the page counts it too
    undone = {(doc["body"].get("target") or {}).get("intent") for doc in docs.values()
              if doc["body"].get("op") == "cancel" and doc["body"].get("status") != "done"}
    undone |= {iid for iid, doc in docs.items() if doc["body"].get("cancel_requested_at")}
    grew = True
    while grew:  # a change chained to an undone one is rejected later ("depends on …"): not waiting either
        grew = False
        for iid, doc in docs.items():
            if iid not in undone and doc["body"].get("after") in undone and doc["body"].get("status") != "done":
                undone.add(iid)
                grew = True
    for intent_id, doc in docs.items():
        body = doc["body"]
        if body.get("status") == "done" or intent_id in finished or body.get("op") == "cancel" or intent_id in undone:
            continue
        key = body.get("level")
        entry = levels.setdefault(key, {"level": key, "slugs": [], "adds": 0, "count": 0, "oldest": None})
        entry["count"] += 1
        made = parse_time(body.get("created_at"))
        if made is not None and (entry["oldest"] is None or made < parse_time(entry["oldest"])):
            entry["oldest"] = iso(made)
        target = body.get("target") if isinstance(body.get("target"), dict) else {}
        if body.get("op") == "add":
            entry["adds"] += 1
        elif target.get("slug") and target["slug"] not in entry["slugs"]:
            entry["slugs"].append(target["slug"])
        src = here.get(key)
        if src is not None:
            entry.update({"kind": src.kind, "label": src.label, "board": src.board})
            if src.kind == "project":
                entry["root"] = src.repo.as_posix()
    record = active_record(home)
    data = {"checked_at": iso(now), "url": (record or {}).get("url"), "count": sum(e["count"] for e in levels.values()),
            "oldest": min((e["oldest"] for e in levels.values() if e["oldest"]), key=parse_time, default=None),
            "command": "/neuroflow:tasks --apply-web", "levels": sorted(levels.values(), key=lambda e: str(e["level"]))}
    write_json(local_dir(home) / "pending.json", data)
    return 0, data


# ── gc ──────────────────────────────────────────────────────────────────────────────────────────

def cmd_gc(args, home: Path, now: datetime) -> tuple[int, dict]:
    versions = json.loads(Path(args.versions).read_text(encoding="utf-8")) if args.versions else None
    intents = intent_docs(Path(args.intents), versions) if args.intents else {}
    docs = load_docs(Path(args.remote), versions) if args.remote else {}
    person = consent(home)
    sources, _ = discover(home, args.root)
    rows = {row["level"]: row for row in level_rows(sources, person)}
    asked = set(args.purge or [])
    bad = sorted(key for key in asked if not valid_level_key(key))
    if bad:
        raise UsageError(f"--purge {', '.join(bad)}: not a level key")
    still = sorted(key for key in asked if (rows.get(key) or {}).get("mirrored"))
    if still:
        raise UsageError(f"still mirrored on this machine: {', '.join(still)} — take it off workbench_levels first")
    cutoff = now - timedelta(days=args.days)
    deletes, missing, reasons, unlisted = [], [], [], []
    for intent_id, doc in sorted(intents.items()):
        body = doc["body"]
        at = parse_time((body.get("outcome") or {}).get("at") if isinstance(body.get("outcome"), dict) else None)
        if body.get("status") == "done" and at is not None and at < cutoff:
            deletes.append(pinned({"op": "delete", "collection": intents_collection(), "doc_id": intent_id}, doc, missing))
    metas = {path.split("/")[-1]: doc for path, doc in docs.items()
             if path.startswith(meta_collection() + "/") and segments(path) == 4 and valid_level_key(path.split("/")[-1])}
    # What is purged: the levels the person took off (--purge), and the levels this machine has whose team no longer
    # allows mirroring them. Never a level only because this machine lacks it or does not list it: workbench_levels is
    # this machine's own, and another machine of the person's may mirror that level.
    purge = {key: "you took it off your workbench" for key in asked}
    for key in metas:
        if (rows.get(key) or {}).get("purge"):
            purge.setdefault(key, rows[key].get("reason") or "the team no longer allows mirroring it")
    for key in sorted(purge):
        part_docs = {path: doc for path, doc in docs.items() if path.startswith(parts_collection(key) + "/")}
        named = {part.get("id") for part in ((metas.get(key) or {}).get("body") or {}).get("parts") or [] if isinstance(part, dict)}
        if named and not part_docs:
            # deleting the meta alone would leave every part behind, unreachable (a delete never deletes what is below)
            unlisted.append({"level": key, "list": parts_collection(key)})
            continue
        for path, doc in sorted(part_docs.items()):     # the parts first, then the meta above them
            deletes.append(pinned({"op": "delete", "collection": parts_collection(key), "doc_id": path.split("/")[-1]}, doc, missing))
        if key in metas:
            deletes.append(pinned({"op": "delete", "collection": meta_collection(), "doc_id": key}, metas[key], missing))
        reasons.append({"level": key, "reason": purge[key]})
    for key, meta in metas.items():
        if key in purge:
            continue
        listed = {part.get("id") for part in (meta["body"].get("parts") or []) if isinstance(part, dict)}
        for path, doc in sorted(docs.items()):
            if path.startswith(parts_collection(key) + "/") and path.split("/")[-1] not in listed:
                deletes.append(pinned({"op": "delete", "collection": parts_collection(key), "doc_id": path.split("/")[-1]}, doc, missing))
    if missing:
        raise MissingVersions("the listing shows no version for: " + ", ".join(missing) + " — pass them with --versions")
    batches = plan_batches(deletes)
    return (1 if deletes or unlisted else 0), {"deletes": len(deletes), "purge": reasons, "unlisted": unlisted, "batches": batches}


# ── the workbench record ────────────────────────────────────────────────────────────────────────

def record_store(home: Path) -> tuple[str, Path]:
    flowie = home / ".neuroflow" / "flowie"
    if (flowie / ".git").exists():
        return "flowie", flowie / "workbench.json"
    return "user.yaml", user_yaml_path(home)


def read_records(home: Path) -> tuple[str, list[dict]]:
    where, path = record_store(home)
    if where == "flowie":
        data = pj.read_json(path)
        records = data.get("workbenches") if isinstance(data, dict) else None
    else:
        records = read_user_yaml(home).get("workbench_records")
    return where, [item for item in records if isinstance(item, dict)] if isinstance(records, list) else []


def active_record(home: Path) -> dict | None:
    _, records = read_records(home)
    account = consent(home)["account"]
    if account:
        return next((item for item in records if item.get("account") == account), None)
    return records[0] if len(records) == 1 else None


RECORD_KEYS = ("url", "account", "template_version", "contract", "page_sha256", "published_at")


def cmd_record(args, home: Path, now: datetime) -> tuple[int, dict]:
    where, records = read_records(home)
    person = consent(home)
    updates = {}
    for item in args.set or []:
        key, sep, value = item.partition("=")
        if not sep or key not in RECORD_KEYS:
            raise UsageError(f"--set {item}: expected KEY=VALUE with KEY one of {', '.join(RECORD_KEYS)}")
        updates[key] = int(value) if key == "template_version" and value.isdigit() else value
    prefs = None
    if args.prefs:
        body, _ = saved_doc(json.loads(Path(args.prefs).read_text(encoding="utf-8-sig")))
        prefs = {key: value for key, value in (body or {}).items() if key not in ("version",)}
    if not updates and prefs is None:
        return 0, {"where": where, "records": records, "active": active_record(home), "account": person["account"] or None}
    account = updates.get("account") or person["account"] or (records[0].get("account") if len(records) == 1 else None)
    if not account:
        raise UsageError("no account label: pass --set account=LABEL (the person names the claude.ai account)")
    record = next((item for item in records if item.get("account") == account), None)
    before = json.dumps(record, sort_keys=True)
    if record is None:
        record = {"account": account}
        records.append(record)
    record.update(updates)
    if prefs is not None and record.get("prefs") != prefs:
        record["prefs"] = prefs
        record["prefs_copied_at"] = iso(now)
    changed = json.dumps(record, sort_keys=True) != before
    if changed:
        if where == "flowie":
            store = record_store(home)[1]
            raw = read_text(store) or ""
            text = json.dumps({"nf_schema": 1, "workbenches": records}, ensure_ascii=False, indent=2) + "\n"
            store.write_bytes(text.replace("\n", "\r\n" if "\r\n" in raw else "\n").encode("utf-8"))
        else:
            set_user_yaml(home, "workbench_records", records)
    if not person["account"] or updates.get("account"):
        set_user_yaml(home, "workbench_account", account)
    commit = None
    if changed and where == "flowie":
        commit = {"argv": ["git", "-C", str(home / ".neuroflow" / "flowie"), "commit", "-m", "workbench: record", "--", "workbench.json"],
                  "add": ["git", "-C", str(home / ".neuroflow" / "flowie"), "add", "--", "workbench.json"]}
    return 0, {"where": where, "changed": changed, "record": record, "commit": commit}


# ── the page ────────────────────────────────────────────────────────────────────────────────────

def template_meta(text: str, name: str) -> str | None:
    match = re.search(rf'<meta\s+name="neuroflow:{name}"\s+content="([^"]*)"', text)
    return match.group(1) if match else None


def page_hash(text: str) -> str | None:
    """sha256 of the page between its begin and end markers, LF line endings, trailing spaces dropped: a page read
    back from claude.ai inside the publish skeleton still hashes the same."""
    start, stop = text.find(BEGIN), text.find(END)
    if start < 0 or stop < start:
        return None
    inner = text[start + len(BEGIN):stop].replace("\r\n", "\n")
    inner = "\n".join(line.rstrip() for line in inner.split("\n")).strip("\n")
    return hashlib.sha256(inner.encode("utf-8")).hexdigest()


UNSAFE = [
    (re.compile(r"\binnerHTML\b|\bouterHTML\b"), "innerHTML or outerHTML"),
    (re.compile(r"\binsertAdjacentHTML\b"), "insertAdjacentHTML"),
    (re.compile(r"\bdocument\.write(?:ln)?\b"), "document.write"),
    (re.compile(r"\beval\s*\(|\bnew\s+Function\b"), "eval or new Function"),
    (re.compile(r"\bfetch\s*\(|\bXMLHttpRequest\b|\bWebSocket\b|\bsendBeacon\b"), "a network call"),
    (re.compile(r"<script\b[^>]*\bsrc\s*=", re.I), "an external script"),
    (re.compile(r"@import\b|url\(\s*['\"]?\s*(?:https?:)?//", re.I), "an external stylesheet or image in CSS"),
    (re.compile(r"\bcreateContextualFragment\b|\bDOMParser\b|\bsrcdoc\b", re.I), "an HTML parser"),
]


def check_template(html: str, module: str) -> list[str]:
    findings = []
    for name, text in (("workbench.html", html), ("workbench.mjs", module)):
        for pattern, what in UNSAFE:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append(f"{name}:{line} uses {what}")
    for match in re.finditer(r"<link\b[^>]*>", html, re.I):
        href = re.search(r'href="([^"]*)"', match.group(0))
        if href and not re.match(r"^https://fonts\.(?:googleapis|gstatic)\.com(?:/|$)", href.group(1)):
            findings.append(f"workbench.html links {href.group(1)} (only Google Fonts may load)")
    if not (template_meta(html, "workbench-template") or "").isdigit():
        findings.append("workbench.html has no <meta name=\"neuroflow:workbench-template\" content=\"N\"> version tag")
    if not template_meta(html, "workbench-contract"):
        findings.append("workbench.html names no runtime contract (<meta name=\"neuroflow:workbench-contract\">)")
    for mark in (BEGIN, END, LOGIC_MARK):
        if html.count(mark) != 1:
            findings.append(f"workbench.html must hold {mark} exactly once")
    if re.search(r"^\s*(import|export\s+(default|\{|\*))", module, re.M):
        findings.append("workbench.mjs must stay dependency-free: no import, no export default or export lists")
    return findings


def inline_module(module: str) -> str:
    return re.sub(r"^export (?=(?:async )?function |const |let |class )", "", module, flags=re.M)


def cmd_stage(args, home: Path, now: datetime) -> tuple[int, dict]:
    html = TEMPLATE.read_bytes().decode("utf-8").replace("\r\n", "\n")
    module = MODULE.read_bytes().decode("utf-8").replace("\r\n", "\n")
    findings = check_template(html, module)
    if findings:
        return 1, {"findings": findings}
    page = html.replace(LOGIC_MARK, inline_module(module).strip("\n"))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    file = out / "workbench.html"
    file.write_bytes(page.encode("utf-8"))
    return 0, {"file": str(file), "bytes": len(page.encode("utf-8")), "sha256": hashlib.sha256(page.encode("utf-8")).hexdigest(),
               "page_sha256": page_hash(page), "template_version": int(template_meta(html, "workbench-template")),
               "contract": template_meta(html, "workbench-contract"), "capabilities": CAPABILITIES, "title": TITLE,
               "icon": ICON, "description": DESCRIPTION}


def cmd_page(args, home: Path, now: datetime) -> tuple[int, dict]:
    text = Path(args.check).read_bytes().decode("utf-8", "replace")
    found = page_hash(text)
    version = template_meta(text, "workbench-template")
    record = active_record(home) or {}
    shipped = int(template_meta(TEMPLATE.read_text(encoding="utf-8"), "workbench-template") or 0)
    status = "unknown" if found is None else "same" if found == record.get("page_sha256") else "changed"
    result = {"status": status, "page_sha256": found, "recorded": record.get("page_sha256"),
              "template_version": int(version) if (version or "").isdigit() else None, "plugin_template_version": shipped,
              "upgrade": (int(version) if (version or "").isdigit() else 0) < shipped}
    return (0 if status == "same" else 1), result


def cmd_check(args, home: Path, now: datetime) -> tuple[int, dict]:
    findings = check_template(TEMPLATE.read_bytes().decode("utf-8"), MODULE.read_bytes().decode("utf-8"))
    return (1 if findings else 0), {"findings": findings}


# ── the levels list and the key ─────────────────────────────────────────────────────────────────

def cmd_levels(args, home: Path, now: datetime) -> tuple[int, dict]:
    person = consent(home)
    sources, unkeyed = discover(home, args.root)
    return 0, {"workbench": "on" if person["on"] else "off", "machine": person["machine"] or None,
               "pii_config": person["pii_config"] or None, "levels": level_rows(sources, person), "unkeyed": unkeyed}


def cmd_key(args, home: Path, now: datetime) -> tuple[int, dict]:
    if args.hive:
        key = hive_key(pj.origin_url(Path(args.hive)))
    elif args.project:
        here = project_root(Path(args.project))
        if here is None:
            raise UsageError(f"no neuroflow project at or above {args.project}")
        key = project_key(pj.linked_id(home, pj.all_levels(home), here), pj.origin_url(here))
    else:
        key = "flowie"
    return (0 if key else 1), {"key": key}


# ── golden fixtures ─────────────────────────────────────────────────────────────────────────────

FIXTURE_SOURCE = PLUGIN / "tests" / "fixtures" / "workbench" / "source.json"


def fixture_home(base: Path, source: dict) -> tuple[Path, Path]:
    """The source's files under `base` (home/… and work/…, fixed content, no git), so its export never changes."""
    for rel, text in source["files"].items():
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
    home, project = base / "home", base / source["project"]
    links = [{"name": name, "path": str(project)} for name in source.get("link_project_as", [])]
    if links:
        write_json(home / ".neuroflow" / "local-projects.json", {"projects": links})
    return home, project


def cmd_fixtures(args, home: Path, now: datetime) -> tuple[int, dict]:
    """The golden snapshot both test suites read: tests/fixtures/workbench/source.json exported as the page sees it."""
    source = json.loads(Path(args.source or FIXTURE_SOURCE).read_text(encoding="utf-8"))
    out = Path(args.out)
    with tempfile.TemporaryDirectory() as tmp:
        fhome, project = fixture_home(Path(tmp), source)
        person = consent(fhome)
        sources, _ = discover(fhome, project)
        stamp = parse_time(source["now"])
        built = [build_level(src, person, Scrubber(), fhome, stamp, person["machine"], False)
                 for src in sources if src.key in person["levels"] and src.allowed]
        snapshot: dict = {"metas": {}, "parts": {}}
        for item in built:
            key = item["meta"]["level"]
            snapshot["metas"][key] = item["meta"]
            snapshot["parts"][key] = {part["part"]: part for part in item["parts"]}
        intents = json.loads(json.dumps(source.get("intents", {})))
        for body in intents.values():
            if body.get("base") == "@export":   # the card's hash as this export computed it
                cards = [card for part in snapshot["parts"].get(body["level"], {}).values() for card in part.get("cards", [])]
                body["base"] = next(card["sha256"] for card in cards if card["slug"] == body["target"]["slug"])
        # what the page must agree with: each tab's freshness label, and where the validator puts each card once
        # this machine claims the golden intents (the page's pending overlay shows the same columns)
        expected: dict = {"freshness": {item["meta"]["level"]: freshness(item["meta"]) for item in built}, "final": {},
                          "verdicts": {}, "adds": {}}
        claimed = {iid: {**body, "status": "claimed", "claim": {"machine": person["machine"], "claimed_at": source["now"]}}
                   for iid, body in intents.items()}
        phases = mg.canonical_phases() - {"setup"}
        for src in sources:
            items = sorted(((iid, body) for iid, body in claimed.items() if body.get("level") == src.key),
                           key=lambda pair: (str(pair[1].get("created_at")), pair[0]))
            if not items:
                continue
            people = {entry["handle"].lower() for entry in roster(src, person)}
            result = validate_level(src, items, {}, person["machine"], people, phases, {})
            expected["final"][src.key] = {action["slug"]: action["to"] for action in result["actions"]}
            expected["adds"].update({action["intents"][0]: action["slug"] for action in result["actions"] if action["op"] == "add"})
            expected["verdicts"].update({iid: verdict["result"] for iid, verdict in result["verdicts"].items()})
        text = json.dumps(snapshot, ensure_ascii=False)
        if any(marker in text for marker in {str(Path(tmp)), Path(tmp).as_posix(), str(Path(tmp)).replace("\\", "\\\\")}):
            raise UsageError("the fixture export holds a local path")
    write_json(out / "snapshot.json", snapshot)
    write_json(out / "intents.json", intents)
    write_json(out / "expected.json", expected)
    return 0, {"written": [str(out / name) for name in ("snapshot.json", "intents.json", "expected.json")]}


# ── command line ────────────────────────────────────────────────────────────────────────────────

def print_human(command: str, code: int, result: dict) -> None:
    if command == "sources":
        print(sources_markdown(), end="")
        return
    if command == "levels":
        print(f"workbench: {result['workbench']} · machine: {result['machine'] or 'not named yet'}")
        print(f"ID numbers and participant names: {'checked with ' + result['pii_config'] if result['pii_config'] else 'not checked (no pii_config)'}")
        for row in result["levels"]:
            print(f"  {row['level']}: {row['label']} — {'mirrored' if row['mirrored'] else row['reason']}")
        for item in result["unkeyed"]:
            print(f"  ({item['kind']}) {item['reason']}")
        return
    if command == "export":
        for row in result["levels"]:
            print(f"{row['label']} ({row['level']}): {row['documents']} documents, {row['bytes'] // 1024} KB, "
                  f"{row['cards']} cards, {row['pages']} wiki pages{' (index only)' if row['index_only'] else ''}")
            print(f"  {row['freshness']}")
            for item in row["withheld"]:
                print(f"  held back: {item['source']} {item['item']} ({item['reason']})")
        for warning in result.get("warnings") or []:
            print(f"warning: {warning}")
        for row in result.get("skipped") or []:
            print(f"not exported: {row['label']} ({row['level']}) — {row['reason']}")
        for row in result.get("purge") or []:
            print(f"deleted from the workbench where it holds it: {row['label']} ({row['level']}) — {row['reason']}")
        for key, verdict in (result.get("guard") or {}).items():
            print(f"  {key}: {verdict['verdict']} — {verdict.get('question') or verdict['reason']}")
        if result.get("prefs"):
            print(f"page settings: {result['prefs']}")
        if "upload" in result:
            print(f"upload: {result['upload']['documents']} writes, {result['upload']['bytes'] // 1024} KB, "
                  f"{result['upload']['batches']} batch(es)")
        return
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=__doc__.split("\n\n", 1)[1])
    parser.add_argument("command", choices=["sources", "levels", "export", "pickup", "validate", "apply", "pending", "gc",
                                            "record", "stage", "page", "check", "key", "fixtures"])
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="a folder inside the project (default: here)")
    parser.add_argument("--out", help="export, stage, fixtures: the folder to write to; validate: the plan file")
    parser.add_argument("--level", action="append", help="export: only this level key; apply: the level to apply")
    parser.add_argument("--remote", help="export, gc: an ArtifactData listing of data/users/me saved with out_dir")
    parser.add_argument("--intents", help="pickup, validate, pending, gc, export --outcomes: a listing of the intents")
    parser.add_argument("--versions", help="a JSON file {document path: version} for documents a listing saved without one")
    parser.add_argument("--outcomes", metavar="PLAN", help="export: add the outcome writes of this validated plan")
    parser.add_argument("--overwrite", action="append", metavar="KEY", help="export: the person said yes to overwriting this level")
    parser.add_argument("--fetch", action="store_true", help="export: fetch each level's repository first (read-only)")
    parser.add_argument("--plan", help="apply, pending: the plan validate wrote")
    parser.add_argument("--today", help="apply: the date written into updated: (default: today)")
    parser.add_argument("--machine", help="the machine label (default: workbench_machine in user.yaml)")
    parser.add_argument("--pii-config", help="export: a pii_scan.py config (id_patterns, roster) instead of the one pii_config "
                                             "in user.yaml names")
    parser.add_argument("--days", type=int, default=GC_DAYS, help="gc: keep finished intents this many days")
    parser.add_argument("--purge", action="append", metavar="KEY",
                        help="gc: delete this level's documents too — one the person took off (its parts must be listed)")
    parser.add_argument("--set", action="append", metavar="KEY=VALUE", help="record: write a field of the workbench record")
    parser.add_argument("--prefs", help="record: the page's prefs document (an ArtifactData get saved with out_dir)")
    parser.add_argument("--check", help="page: the page file an Artifact read saved")
    parser.add_argument("--hive", help="key: a hive clone's folder")
    parser.add_argument("--project", help="key: a folder inside a project")
    parser.add_argument("--markdown", action="store_true", help="sources: print the table (the default without --json)")
    parser.add_argument("--source", help="fixtures: the fixture source (default: tests/fixtures/workbench/source.json)")
    parser.add_argument("--home", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--now", help=argparse.SUPPRESS)
    parser.add_argument("--json", action="store_true", help="print the result as JSON")
    args = parser.parse_args(argv)
    home = args.home or Path.home()
    now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
    handlers = {"sources": lambda *_: (0, {"sources": SOURCES, "never": NEVER, "scrub": SCRUB}), "levels": cmd_levels,
                "export": cmd_export, "pickup": cmd_pickup, "validate": cmd_validate, "apply": cmd_apply, "pending": cmd_pending,
                "gc": cmd_gc, "record": cmd_record, "stage": cmd_stage, "page": cmd_page, "check": cmd_check, "key": cmd_key,
                "fixtures": cmd_fixtures}
    needs = {"export": ["out"], "pickup": ["intents"], "validate": ["intents"], "apply": ["plan", "level"],
             "pending": ["intents"], "stage": ["out"], "page": ["check"], "fixtures": ["out"]}
    try:
        if now is None:
            raise UsageError(f"--now {args.now!r} is not an ISO time")
        missing = [name for name in needs.get(args.command, []) if not getattr(args, name)]
        if missing:
            raise UsageError(f"{args.command} needs " + " and ".join(f"--{name}" for name in missing))
        if args.command == "apply":
            args.level = args.level[0]
        code, result = handlers[args.command](args, home, now)
    except (UsageError, MissingVersions) as error:
        if args.json:
            print(json.dumps({"error": str(error)}, ensure_ascii=False))
        else:
            print(f"workbench: {error}", file=sys.stderr)
        return 2
    except Exception as error:  # an unforeseen shape is a runtime error, never "findings"
        if args.json:
            print(json.dumps({"error": f"{type(error).__name__}: {error}"}, ensure_ascii=False))
        else:
            print(f"workbench: {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_human(args.command, code, result)
    return code


if __name__ == "__main__":
    sys.exit(main())
