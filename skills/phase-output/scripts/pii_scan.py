#!/usr/bin/env python3
"""Deterministic personal-data and secret scan for shared project files (phase-output).

Finds, without any model call:
- email addresses (reserved example domains, `noreply` addresses, addresses
  already listed in .neuroflow/project_config.md and --allow-email entries are
  ignored)
- international phone numbers (+ country code, 9-15 digits)
- ID numbers from YOUR configuration: neuroflow ships no country-specific
  pattern. Each pattern has a name, a regex and an optional checksum
  (none | luhn | mod11 = the digits form a number divisible by 11)
- participant names from a salted-hash roster (--build-roster makes one; the
  names file is read only by this script and never printed)
- secrets: token prefixes (GitHub, Slack, AWS, Google, sk-), JWTs, private-key
  blocks, quoted password/api_key/token assignments
- in --staged mode also local-tier memory paths and credential files that are
  staged for commit (neuroflow-core -> Sharing tiers)

Values are never printed: a finding is a path, a line number and a class.
This script is the single home of these text patterns; header_scan.py and
history_audit.py import them.

Usage:
    python <phase-output skill base dir>/scripts/pii_scan.py [PATH ...] [--root DIR]
        [--staged] [--config FILE] [--roster FILE] [--allow-email ADDR|@DOMAIN ...]
        [--no-secrets] [--include-local] [--json]
    python <phase-output skill base dir>/scripts/pii_scan.py --build-roster NAMES_FILE
        --out ROSTER_FILE

Without PATH and without --staged it scans .neuroflow/ under --root. In any
folder it walks, local-tier memory (sessions/, review/, integrations.json,
flowie/, paper/xray-*, wiki/.pending/) is skipped - it never leaves the
machine - unless --include-local.
As a pre-commit check, run it with --staged from the repository root; exit 1
blocks the commit.

Config file (JSON, optional):
    {"id_patterns": [{"name": "staff-id", "regex": "\\\\bST-\\\\d{6}\\\\b", "checksum": "none"}],
     "allow_emails": ["@lab.example.org"],
     "roster": "/path/outside/the/project/roster.json"}

Exit codes:
    0  clean (or roster written)
    1  findings
    2  usage or runtime error (bad config or regex, unreadable roster, git failure)

Stdlib only. Python 3.10+.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import secrets as _secrets
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

MAX_BYTES = 10 * 1024 * 1024

EMAIL_RE = re.compile(
    r"(?<![\w.%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)*\.[A-Za-z]{2,24}(?![\w-])"
)
RESERVED_EMAIL_DOMAINS = ("example.com", "example.org", "example.net", "users.noreply.github.com")
RESERVED_EMAIL_TLDS = (".example", ".test", ".invalid", ".localhost")
SYSTEM_LOCAL_PARTS = {"git", "noreply", "no-reply", "donotreply", "do-not-reply"}

PHONE_RE = re.compile(r"(?<![\w+])\+[1-9]\d{0,2}(?:[ -]?\(?\d{2,4}\)?){2,5}(?!\w)")

SECRET_PATTERNS = {
    "github-token": re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,255}\b|\bgithub_pat_[A-Za-z0-9_]{22,255}\b"),
    "slack-token": re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b"),
    "aws-access-key": re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    "google-api-key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    "sk-key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "jwt": re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    "private-key": re.compile(r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY(?: BLOCK)?-----"),
    "assignment": re.compile(
        r"(?i)\b(?:password|passwd|secret|api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret)\b"
        r"[\"']?\s*[:=]\s*[\"']([^\"'\s]{8,})[\"']"
    ),
}
PLACEHOLDER_RE = re.compile(r"(?i)placeholder|example|changeme|your[_-]|xxxx|dummy|redacted|\*\*\*")

WORD_RE = re.compile(r"[^\W\d_]+(?:['\u2019-][^\W\d_]+)*")


# ---------------------------------------------------------------------------
# Checksums and normalisation
# ---------------------------------------------------------------------------


def luhn_ok(digits: str) -> bool:
    if not digits:
        return False
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def mod11_ok(digits: str) -> bool:
    return bool(digits) and int(digits) % 11 == 0


CHECKSUMS = {"none": lambda d: True, "luhn": luhn_ok, "mod11": mod11_ok}


def normalize_name(text: str) -> str:
    """Casefolded, accent-free, single-spaced words."""
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return " ".join(w.casefold() for w in WORD_RE.findall(stripped))


def name_hash(salt: str, normalized: str) -> str:
    return hashlib.sha256(f"{salt}\0{normalized}".encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------


class ConfigError(Exception):
    """Bad configuration or roster (exit code 2)."""


@dataclass(frozen=True)
class IdPattern:
    name: str
    regex: re.Pattern
    checksum: str = "none"


@dataclass
class Roster:
    salt: str
    hashes: frozenset[str]
    max_tokens: int


def load_roster(path: Path) -> Roster:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return Roster(str(data["salt"]), frozenset(data["hashes"]), int(data.get("max_tokens", 3)))
    except (OSError, ValueError, KeyError, TypeError) as e:
        raise ConfigError(f"cannot read roster {path}: {e}") from e


def load_config(path: Path | None) -> dict:
    if path is None:
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ConfigError(f"cannot read config {path}: {e}") from e
    if not isinstance(data, dict):
        raise ConfigError(f"config {path} must be a JSON object")
    return data


def id_patterns_from(config: dict) -> list[IdPattern]:
    out = []
    for entry in config.get("id_patterns", []) or []:
        try:
            name, regex = str(entry["name"]), str(entry["regex"])
        except (KeyError, TypeError) as e:
            raise ConfigError(f"id_patterns entry needs name and regex: {entry!r}") from e
        checksum = str(entry.get("checksum", "none"))
        if checksum not in CHECKSUMS:
            raise ConfigError(f"unknown checksum {checksum!r} for {name} (use: {', '.join(CHECKSUMS)})")
        try:
            out.append(IdPattern(name, re.compile(regex), checksum))
        except re.error as e:
            raise ConfigError(f"bad regex for {name}: {e}") from e
    return out


class Scanner:
    """Line-numbered findings for one text. Never keeps or returns matched values."""

    def __init__(self, id_patterns=(), roster: Roster | None = None, allow_emails=(),
                 known_emails=(), secrets: bool = True, pii: bool = True):
        self.id_patterns = list(id_patterns)
        self.roster = roster
        self.allow = [a.lower() for a in allow_emails]
        self.known = {e.lower() for e in known_emails}
        self.secrets = secrets
        self.pii = pii

    def _email_ignored(self, addr: str) -> bool:
        addr = addr.lower()
        local, _, domain = addr.partition("@")
        if addr in self.known or local in SYSTEM_LOCAL_PARTS:
            return True
        if domain in RESERVED_EMAIL_DOMAINS or domain.endswith(RESERVED_EMAIL_TLDS):
            return True
        for a in self.allow:
            if (a.startswith("@") and (domain == a[1:] or domain.endswith("." + a[1:]))) or addr == a:
                return True
        return False

    def _roster_hits(self, line: str) -> int:
        if not self.roster:
            return 0
        words = normalize_name(line).split()
        hits = 0
        for i in range(len(words)):
            for n in range(1, self.roster.max_tokens + 1):
                if i + n > len(words):
                    break
                if name_hash(self.roster.salt, " ".join(words[i : i + n])) in self.roster.hashes:
                    hits += 1
        return hits

    def scan_line(self, line: str) -> list[str]:
        kinds: list[str] = []
        if self.pii:
            for m in EMAIL_RE.finditer(line):
                if not self._email_ignored(m.group()):
                    kinds.append("email")
            for m in PHONE_RE.finditer(line):
                if 9 <= len(re.sub(r"\D", "", m.group())) <= 15:
                    kinds.append("phone")
            for p in self.id_patterns:
                for m in p.regex.finditer(line):
                    if CHECKSUMS[p.checksum](re.sub(r"\D", "", m.group())):
                        kinds.append(f"id:{p.name}")
            kinds += ["roster-name"] * self._roster_hits(line)
        if self.secrets:
            for kind, rx in SECRET_PATTERNS.items():
                for m in rx.finditer(line):
                    value = m.group(1) if m.groups() else m.group()
                    if PLACEHOLDER_RE.search(value):
                        continue
                    if kind == "assignment" and (value.isupper() or value.startswith(("$", "%", "{", "<"))):
                        continue
                    kinds.append(f"secret:{kind}")
        return kinds

    def scan_text(self, text: str) -> list[tuple[int, str]]:
        found = []
        for no, line in enumerate(text.splitlines(), start=1):
            for kind in self.scan_line(line):
                found.append((no, kind))
        return found


def emails_in(path: Path) -> set[str]:
    try:
        return {m.group().lower() for m in EMAIL_RE.finditer(path.read_text(encoding="utf-8", errors="replace"))}
    except OSError:
        return set()


def scanner_from_args(config: dict, roster_path: str | None, allow: list[str], root: Path | None,
                      secrets: bool = True) -> Scanner:
    roster_file = roster_path or config.get("roster")
    roster = load_roster(Path(roster_file).expanduser()) if roster_file else None
    known = emails_in(root / ".neuroflow" / "project_config.md") if root else set()
    return Scanner(id_patterns_from(config), roster, list(config.get("allow_emails", []) or []) + allow,
                   known, secrets=secrets)


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------


def _export_rules():
    """Path rules from export.py (one home for the sharing tiers)."""
    name = "_nf_phase_output_export"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name("export.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def decode_text(data: bytes) -> str | None:
    """Text content, or None for binary data."""
    if b"\0" in data[:8192]:
        return None
    return data.decode("utf-8", errors="replace")


def file_targets(paths: list[Path], root: Path, include_local: bool = False) -> list[Path]:
    """Files to scan. Folders are walked; local-tier memory found while walking is
    skipped unless include_local (it never leaves the machine)."""
    rules = _export_rules()
    targets: list[Path] = []
    for p in paths or [root / ".neuroflow"]:
        if not p.exists():
            raise ConfigError(f"no such path: {p}")
        if p.is_file():
            targets.append(p)
            continue
        for item in sorted(x for x in p.rglob("*") if x.is_file() and ".git" not in x.parts):
            try:
                rel = item.resolve().relative_to(root.resolve()).as_posix()
            except ValueError:
                rel = item.as_posix()
            if include_local or not rules.is_local_tier(rel):
                targets.append(item)
    return targets


def scan_files(scanner: Scanner, targets: list[Path], root: Path) -> tuple[list[dict], list[dict], int]:
    findings, skipped, scanned = [], [], 0
    for path in targets:
        try:
            rel = path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            rel = path.as_posix()
        try:
            if path.stat().st_size > MAX_BYTES:
                skipped.append({"path": rel, "reason": "larger than 10 MB"})
                continue
            text = decode_text(path.read_bytes())
        except OSError as e:
            skipped.append({"path": rel, "reason": f"unreadable: {e.strerror or e}"})
            continue
        if text is None:
            skipped.append({"path": rel, "reason": "binary"})
            continue
        scanned += 1
        findings += [{"path": rel, "line": no, "kind": kind} for no, kind in scanner.scan_text(text)]
    return findings, skipped, scanned


def _git(root: Path, *args: str) -> bytes:
    out = subprocess.run(["git", "-c", "core.quotePath=false", *args], cwd=root, capture_output=True, check=False)
    if out.returncode != 0:
        raise ConfigError(f"git {' '.join(args)} failed: {out.stderr.decode('utf-8', 'replace').strip()}")
    return out.stdout


def scan_staged(scanner: Scanner, root: Path) -> tuple[list[dict], list[dict], int]:
    rules = _export_rules()
    names = [n for n in _git(root, "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR")
             .decode("utf-8", "replace").split("\0") if n]
    findings, skipped, scanned = [], [], 0
    for rel in names:
        if rules.is_local_tier(rel):
            findings.append({"path": rel, "line": 0, "kind": "local-tier-staged"})
        elif rules.is_credential(rel):
            findings.append({"path": rel, "line": 0, "kind": "credential-file-staged"})
        try:
            data = _git(root, "show", f":{rel}")
        except ConfigError:
            skipped.append({"path": rel, "reason": "cannot read the staged blob"})
            continue
        if len(data) > MAX_BYTES:
            skipped.append({"path": rel, "reason": "larger than 10 MB"})
            continue
        text = decode_text(data)
        if text is None:
            skipped.append({"path": rel, "reason": "binary"})
            continue
        scanned += 1
        findings += [{"path": rel, "line": no, "kind": kind} for no, kind in scanner.scan_text(text)]
    return findings, skipped, scanned


# ---------------------------------------------------------------------------
# Roster building
# ---------------------------------------------------------------------------


def build_roster(names_file: Path, out: Path, root: Path) -> dict:
    try:
        lines = names_file.read_text(encoding="utf-8").splitlines()
    except OSError as e:
        raise ConfigError(f"cannot read names file: {e}") from e
    names = [normalize_name(x) for x in lines if x.strip() and not x.lstrip().startswith("#")]
    names = [n for n in names if n]
    if not names:
        raise ConfigError("the names file holds no names")
    rules = _export_rules()
    if rules.is_within(out, root / ".neuroflow"):
        raise ConfigError("never write the roster inside .neuroflow/ - keep it outside the project tree")
    salt = _secrets.token_hex(16)
    data = {
        "salt": salt,
        "algorithm": "sha256(salt + NUL + normalized name)",
        "max_tokens": max(len(n.split()) for n in names),
        "hashes": sorted({name_hash(salt, n) for n in names}),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    warning = None
    if rules.is_within(out, root):
        warning = "the roster is inside the project folder - move it outside and never commit it"
    return {"roster": str(out), "names": len(data["hashes"]), "warning": warning}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(errors="backslashreplace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="Deterministic personal-data and secret scan.")
    ap.add_argument("paths", nargs="*", help="files or folders (default: team-tier files in .neuroflow/)")
    ap.add_argument("--root", default=".", help="project root (default: current folder)")
    ap.add_argument("--staged", action="store_true", help="scan what is staged for commit (pre-commit check)")
    ap.add_argument("--config", help="JSON config with id_patterns, allow_emails, roster")
    ap.add_argument("--roster", help="salted-hash roster file (from --build-roster)")
    ap.add_argument("--allow-email", action="append", default=[], metavar="ADDR|@DOMAIN")
    ap.add_argument("--no-secrets", action="store_true", help="personal data only")
    ap.add_argument("--include-local", action="store_true",
                    help="also scan local-tier memory found in folders (sessions/, review/, ...)")
    ap.add_argument("--build-roster", metavar="NAMES_FILE", help="hash a names file (one name per line)")
    ap.add_argument("--out", help="roster output path for --build-roster")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)
    root = Path(args.root).expanduser().resolve()

    def fail(msg: str) -> int:
        if args.json:
            print(json.dumps({"error": msg}, indent=2))
        else:
            print(f"pii_scan: {msg}", file=sys.stderr)
        return 2

    try:
        if args.build_roster:
            if not args.out:
                return fail("--build-roster needs --out ROSTER_FILE")
            res = build_roster(Path(args.build_roster).expanduser(), Path(args.out).expanduser(), root)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(f"Roster written: {res['roster']} ({res['names']} names, hashed; names are not stored)")
                if res["warning"]:
                    print(f"Warning: {res['warning']}")
            return 0
        config = load_config(Path(args.config).expanduser() if args.config else None)
        scanner = scanner_from_args(config, args.roster, args.allow_email, root, secrets=not args.no_secrets)
        if args.staged:
            findings, skipped, scanned = scan_staged(scanner, root)
        else:
            targets = file_targets([Path(p).expanduser() for p in args.paths], root, args.include_local)
            findings, skipped, scanned = scan_files(scanner, targets, root)
    except ConfigError as e:
        return fail(str(e))

    report = {"scanned": scanned, "findings": findings, "skipped": skipped,
              "mode": "staged" if args.staged else "files"}
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"PII scan - {scanned} files scanned, {len(findings)} findings (values are never shown)")
        for f in findings:
            where = f"{f['path']}:{f['line']}" if f["line"] else f["path"]
            print(f"  {where}  {f['kind']}")
        if skipped:
            print(f"Skipped: {len(skipped)}")
            for s in skipped:
                print(f"  {s['path']}  - {s['reason']}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
