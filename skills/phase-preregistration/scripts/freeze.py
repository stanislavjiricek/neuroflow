#!/usr/bin/env python3
"""Freeze, verify and unfreeze a preregistration (neuroflow contract C2).

One implementation of the preregistration hash lock, shared by /preregistration,
/sentinel and the neuroflow mod. State lives in the frontmatter of
`.neuroflow/preregistration/status.md`; every frozen file gets the plain-text
banner `> FROZEN <date> — sha256 <hash>… — do not edit; record changes in
deviations.md` as its first line.

The hash of a file is the SHA-256 of its bytes after removing a leading FROZEN
banner (plus the blank line after it), a UTF-8 byte-order mark, and CRLF line
endings (normalised to LF). So the hash does not change when the banner is added,
and it is the same on Windows and macOS checkouts.

Usage (run from the project root, or pass --root):
    python <phase-preregistration base dir>/scripts/freeze.py hash FILE [FILE ...]
    python <phase-preregistration base dir>/scripts/freeze.py freeze FILE [FILE ...]
        --set-by person|model [--registry OSF] [--doi DOI] [--planned-n N]
    python <phase-preregistration base dir>/scripts/freeze.py verify
    python <phase-preregistration base dir>/scripts/freeze.py unfreeze
        --set-by person --reason TEXT
All subcommands take --root DIR and --json.

`--set-by person` is written only when a person pressed the freeze button in the
neuroflow mod or explicitly confirmed the freeze in the conversation right before
the call. Readers treat a freeze with `set_by: model` as not set.

Exit codes:
    0  clean: hashes printed, freeze or unfreeze written, or verify found every
       frozen file unchanged (or nothing is frozen)
    1  findings (verify): a frozen file changed, is missing or lost its banner, or
       the freeze was not set by a person
    2  usage or runtime error: bad arguments, file outside the project, not UTF-8
       text, already frozen, not frozen, unfreeze without a person

Stdlib only. Python 3.10+.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1
STATUS_REL = ".neuroflow/preregistration/status.md"
DEVIATIONS_REL = ".neuroflow/preregistration/deviations.md"
BANNER_PREFIX = "> FROZEN "
BANNER_RE = re.compile(rb"\A> FROZEN [^\n]*\n(?:\r?\n)?")
DEFAULT_BODY = (
    "# Preregistration status\n\n"
    "The frontmatter above is the machine-readable freeze record (neuroflow-core, contract C2).\n"
    "Frozen files are never edited; record every change in `deviations.md`.\n"
)
SAFE_SCALAR = re.compile(r"^[A-Za-z0-9_.][A-Za-z0-9_./@+:-]*$")
YAML_SPECIAL = {"true", "false", "null", "yes", "no", "on", "off", "~", ".inf", ".nan"}
NUMBER_LIKE = re.compile(r"^[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?$")
KEY_ORDER = ["nf_schema", "status", "frozen_at", "files", "registry", "doi", "planned_n", "set_by", "set_at"]


class UsageError(Exception):
    """Raised for anything that should end with exit code 2."""


# --------------------------------------------------------------------------- hashing


def canonical_bytes(data: bytes) -> bytes:
    """Bytes that are hashed: no BOM, LF line endings, no leading FROZEN banner."""
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    data = data.replace(b"\r\n", b"\n")
    return BANNER_RE.sub(b"", data, count=1)


def file_hash(path: Path) -> str:
    return hashlib.sha256(canonical_bytes(path.read_bytes())).hexdigest()


def has_banner(path: Path) -> bool:
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    return data.startswith(BANNER_PREFIX.encode("utf-8"))


def banner_line(day: str, digest: str) -> str:
    return f"> FROZEN {day} — sha256 {digest[:8]}… — do not edit; record changes in deviations.md"


def strip_banner_text(text: str) -> str:
    """Remove a leading FROZEN banner (and the blank line after it) from decoded text."""
    bom = "﻿" if text.startswith("﻿") else ""
    body = text[len(bom) :]
    if body.startswith(BANNER_PREFIX):
        nl = body.find("\n")
        body = "" if nl == -1 else body[nl + 1 :]
        if body.startswith("\r\n"):
            body = body[2:]
        elif body.startswith("\n"):
            body = body[1:]
    return bom + body


def read_text(path: Path) -> str:
    try:
        return path.read_bytes().decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UsageError(f"{path} is not UTF-8 text; only text documents can carry the FROZEN banner") from exc


def write_text(path: Path, text: str) -> None:
    path.write_bytes(text.encode("utf-8"))


def add_banner(path: Path, day: str, digest: str) -> None:
    text = strip_banner_text(read_text(path))
    newline = "\r\n" if "\r\n" in text else "\n"
    bom = "﻿" if text.startswith("﻿") else ""
    write_text(path, bom + banner_line(day, digest) + newline + newline + text[len(bom) :])


def remove_banner(path: Path) -> None:
    text = read_text(path)
    stripped = strip_banner_text(text)
    if stripped != text:
        write_text(path, stripped)


# ------------------------------------------------------------------ frontmatter I/O


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value[1:-1]
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    return value


def _strip_comment(value: str) -> str:
    """Drop a trailing ` # comment` outside quotes."""
    quote = None
    for i, ch in enumerate(value):
        if ch in "\"'":
            if quote is None:
                quote = ch
            elif quote == ch:
                quote = None
        elif ch == "#" and quote is None and (i == 0 or value[i - 1] in " \t"):
            return value[:i].rstrip()
    return value.rstrip()


def _split_key(line: str) -> tuple[str, str]:
    """Split `key: value` where the key may be quoted (paths with spaces)."""
    line = line.strip()
    if line[:1] in "\"'":
        quote = line[0]
        end = line.find(quote, 1)
        while end != -1 and quote == '"' and line[end - 1] == "\\":
            end = line.find(quote, end + 1)
        if end == -1 or ":" not in line[end:]:
            raise UsageError(f"cannot parse frontmatter line: {line}")
        key = _unquote(line[: end + 1])
        rest = line[end + 1 :].lstrip()
        return key, rest[1:] if rest.startswith(":") else rest
    key, sep, value = line.partition(":")
    if not sep:
        raise UsageError(f"cannot parse frontmatter line: {line}")
    return key.strip(), value


def _scalar(value: str):
    value = _unquote(_strip_comment(value))
    if isinstance(value, str) and re.fullmatch(r"-?\d+", value):
        return int(value)
    return value


def parse_status(text: str) -> tuple[dict, str]:
    """Parse the C2 frontmatter subset: top-level scalars plus one nested mapping (files)."""
    if text.startswith("﻿"):
        text = text[1:]
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return {}, text
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return {}, text
    data: dict = {}
    current: str | None = None
    for raw in lines[1:end]:
        line = raw.rstrip("\r\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indented = line[:1] in (" ", "\t")
        key, value = _split_key(line)
        value = _strip_comment(value)
        if indented and current is not None:
            data[current][key] = _scalar(value)
            continue
        if value.strip() == "":
            data[key] = {}
            current = key
        else:
            data[key] = _scalar(value)
            current = None
    return data, "".join(lines[end + 1 :])


def _yaml_value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    text = str(value)
    plain = SAFE_SCALAR.match(text) and text.lower() not in YAML_SPECIAL and not NUMBER_LIKE.match(text)
    return text if plain else json.dumps(text, ensure_ascii=False)


def render_status(data: dict, body: str) -> str:
    out = ["---"]
    keys = [k for k in KEY_ORDER if k in data] + [k for k in data if k not in KEY_ORDER]
    for key in keys:
        value = data[key]
        if value is None:
            continue
        if isinstance(value, dict):
            out.append(f"{key}:")
            for sub, subval in value.items():
                out.append(f"  {_yaml_value(sub)}: {_yaml_value(subval)}")
        else:
            out.append(f"{key}: {_yaml_value(value)}")
    out.append("---")
    body = body.lstrip("\r\n") or DEFAULT_BODY
    return "\n".join(out) + "\n" + body


# ------------------------------------------------------------------------- helpers


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def find_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".neuroflow").is_dir():
            return candidate
    return start


def rel_to_root(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise UsageError(f"{path} is outside the project root {root}") from exc


def load_status(root: Path) -> tuple[dict, str, Path]:
    path = root / STATUS_REL
    if not path.exists():
        return {}, "", path
    data, body = parse_status(path.read_text(encoding="utf-8"))
    return data, body, path


def emit(payload: dict, as_json: bool, lines: list[str]) -> None:
    if as_json:
        print(json.dumps(payload, indent=2))
    else:
        for line in lines:
            print(line)


# --------------------------------------------------------------------- subcommands


def cmd_hash(args, root: Path) -> int:
    rows = []
    for name in args.files:
        path = Path(name)
        if not path.is_file():
            raise UsageError(f"no such file: {name}")
        try:
            shown = rel_to_root(path, root)
        except UsageError:
            shown = path.as_posix()
        rows.append({"path": shown, "sha256": file_hash(path)})
    emit({"files": rows}, args.json, [f"{r['sha256']}  {r['path']}" for r in rows])
    return 0


def cmd_freeze(args, root: Path) -> int:
    data, body, status_path = load_status(root)
    if data.get("status") == "frozen" and data.get("set_by") == "person":
        raise UsageError(
            "already frozen by a person; unfreezing is a person's action (freeze.py unfreeze), "
            "otherwise record changes in deviations.md"
        )
    files: dict[str, str] = {}
    paths: list[tuple[Path, str]] = []
    for name in args.files:
        path = Path(name)
        if not path.is_file():
            raise UsageError(f"no such file: {name}")
        read_text(path)  # must be UTF-8 text to carry the banner
        digest = file_hash(path)
        files[rel_to_root(path, root)] = digest
        paths.append((path, digest))
    stamp = now_utc()
    data.update(
        {
            "nf_schema": SCHEMA_VERSION,
            "status": "frozen",
            "frozen_at": stamp,
            "files": files,
            "set_by": args.set_by,
            "set_at": stamp,
        }
    )
    for key in ("registry", "doi", "planned_n"):
        value = getattr(args, key)
        if value is not None:
            data[key] = value
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(render_status(data, body), encoding="utf-8", newline="\n")
    for path, digest in paths:
        add_banner(path, stamp[:10], digest)
    lines = [f"frozen {len(files)} file(s) at {stamp} (set_by: {args.set_by})"]
    lines += [f"  {digest}  {rel}" for rel, digest in files.items()]
    lines.append(f"status written to {STATUS_REL}")
    if args.set_by != "person":
        lines.append("note: set_by is 'model' - readers treat this freeze as not set until a person confirms it")
    emit({"status": "frozen", "frozen_at": stamp, "files": files, "set_by": args.set_by}, args.json, lines)
    return 0


def cmd_verify(args, root: Path) -> int:
    data, _body, status_path = load_status(root)
    status = data.get("status")
    if not data or status != "frozen":
        state = "none" if not data else str(status)
        emit({"status": state, "findings": []}, args.json, [f"not frozen (status: {state}) - nothing to verify"])
        return 0
    findings: list[dict] = []
    if data.get("set_by") != "person":
        findings.append(
            {
                "kind": "unconfirmed-freeze",
                "path": STATUS_REL,
                "detail": f"set_by is {data.get('set_by')!r}; a freeze counts only when a person set it",
            }
        )
    files = data.get("files") or {}
    if not isinstance(files, dict) or not files:
        findings.append({"kind": "no-files", "path": STATUS_REL, "detail": "status is frozen but lists no files"})
        files = {}
    results = []
    for rel, expected in files.items():
        path = root / rel
        if not path.is_file():
            findings.append({"kind": "missing", "path": rel, "detail": "frozen file is missing"})
            results.append({"path": rel, "expected": expected, "actual": None, "ok": False})
            continue
        actual = file_hash(path)
        ok = actual == str(expected)
        results.append({"path": rel, "expected": expected, "actual": actual, "ok": ok})
        if not ok:
            findings.append(
                {"kind": "changed", "path": rel, "detail": "content differs from the frozen hash; record a deviation"}
            )
        if not has_banner(path):
            findings.append({"kind": "banner-missing", "path": rel, "detail": "the FROZEN banner line was removed"})
    lines = [f"frozen at {data.get('frozen_at')} (set_by: {data.get('set_by')}), {len(results)} file(s)"]
    lines += [f"  {'ok     ' if r['ok'] else 'CHANGED'}  {r['path']}" for r in results]
    lines += [f"FINDING {f['kind']}: {f['path']} - {f['detail']}" for f in findings]
    if not findings:
        lines.append("all frozen files match their hashes")
    emit({"status": "frozen", "files": results, "findings": findings}, args.json, lines)
    return 1 if findings else 0


def cmd_unfreeze(args, root: Path) -> int:
    if args.set_by != "person":
        raise UsageError("unfreezing is a person's action: run it only after the person confirmed (--set-by person)")
    if not args.reason or not args.reason.strip():
        raise UsageError("--reason is required; it is logged in deviations.md")
    data, body, status_path = load_status(root)
    if data.get("status") != "frozen":
        raise UsageError("nothing to unfreeze: status is not 'frozen'")
    previous = data.get("files") or {}
    frozen_at = data.get("frozen_at")
    stamp = now_utc()
    for rel in previous:
        path = root / rel
        if path.is_file():
            remove_banner(path)
    for key in ("frozen_at", "files"):
        data.pop(key, None)
    data.update({"nf_schema": SCHEMA_VERSION, "status": "draft", "set_by": "person", "set_at": stamp})
    status_path.write_text(render_status(data, body), encoding="utf-8", newline="\n")
    entry = [
        f"## {stamp[:10]} — Preregistration unfrozen",
        "",
        f"- Unfrozen by: person ({stamp})",
        f"- Reason: {args.reason.strip()}",
        f"- Previously frozen at {frozen_at}:",
    ]
    entry += [f"  - `{rel}` sha256 {digest}" for rel, digest in previous.items()]
    deviations = root / DEVIATIONS_REL
    deviations.parent.mkdir(parents=True, exist_ok=True)
    existing = deviations.read_bytes() if deviations.exists() else None
    if existing is None:
        prefix = "# Deviations from the preregistration\n\n"
    elif not existing or existing.endswith(b"\n\n"):
        prefix = ""
    elif existing.endswith(b"\n"):
        prefix = "\n"
    else:
        prefix = "\n\n"
    # Append-only (contract C2/C4): never rewrite earlier entries.
    with deviations.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(prefix + "\n".join(entry) + "\n")
    lines = [
        f"unfrozen at {stamp}; banners removed from {len(previous)} file(s)",
        f"status set to draft in {STATUS_REL}; unfreeze logged in {DEVIATIONS_REL}",
    ]
    emit({"status": "draft", "unfrozen_at": stamp, "previous_files": previous}, args.json, lines)
    return 0


# ---------------------------------------------------------------------------- main


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", help="project root (default: nearest folder with .neuroflow/, else the cwd)")
    common.add_argument("--json", action="store_true", help="print JSON instead of text")
    parser = argparse.ArgumentParser(
        description="Freeze, verify and unfreeze a neuroflow preregistration (contract C2).",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    p_hash = sub.add_parser("hash", parents=[common], help="print the canonical SHA-256 of files")
    p_hash.add_argument("files", nargs="+")
    p_freeze = sub.add_parser("freeze", parents=[common], help="hash files, write status.md, add FROZEN banners")
    p_freeze.add_argument("files", nargs="+")
    p_freeze.add_argument("--set-by", required=True, choices=["person", "model"])
    p_freeze.add_argument("--registry", help="e.g. OSF, AsPredicted")
    p_freeze.add_argument("--doi", help="registration DOI or URL")
    p_freeze.add_argument("--planned-n", type=int, help="sample size the preregistration commits to")
    sub.add_parser("verify", parents=[common], help="recompute hashes of the frozen files")
    p_unfreeze = sub.add_parser("unfreeze", parents=[common], help="a person's action: back to draft, logged")
    p_unfreeze.add_argument("--set-by", required=True, choices=["person", "model"])
    p_unfreeze.add_argument("--reason", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass
    args = build_parser().parse_args(argv)
    root = Path(args.root) if args.root else find_root(Path.cwd())
    if not root.is_dir():
        print(f"error: project root not found: {root}", file=sys.stderr)
        return 2
    handlers = {"hash": cmd_hash, "freeze": cmd_freeze, "verify": cmd_verify, "unfreeze": cmd_unfreeze}
    try:
        return handlers[args.command](args, root)
    except UsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
