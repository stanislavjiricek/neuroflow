#!/usr/bin/env python3
"""cite_check.py: do the cited DOIs resolve, and has Crossref recorded a notice?

Extracts DOIs from .bib, .md, .tex, .txt, .ris and .docx files (including the
hyperlinks and reference-manager field codes inside a .docx), then for each DOI:

1. asks the Crossref REST API for the record (api.crossref.org/works/{doi});
   if Crossref does not know it, asks the doi.org handle API, which also covers
   DataCite DOIs (Zenodo, OSF, figshare);
2. looks for editorial notices that update the DOI: retraction, withdrawal,
   removal, expression of concern, correction (the record's "updated-by" field
   and the works?filter=updates:{doi} query). Crossref merges publisher notices
   with the Retraction Watch database;
3. notes preprints whose record links a published version.

Wording names the test, never a virtue: "DOI resolves", "does not resolve",
"no retraction notice found in Crossref as of <date>". Never "verified": a DOI
that resolves can still be cited for something the paper does not say, and
notice coverage in Crossref is incomplete.

Only DOI strings leave the machine. No e-mail address is sent unless you pass
--mailto (Crossref's "polite pool").

Usage:
    python cite_check.py manuscript/references.bib
    python cite_check.py manuscript/ --library .neuroflow/ideation/papers --cache .neuroflow/paper/doi-cache.json
    python cite_check.py manuscript/main.docx --offline --cache .neuroflow/paper/doi-cache.json --json
    python cite_check.py manuscript/ --cache .neuroflow/paper/doi-cache.json --max-age 7 --json
        (looks up only DOIs that are new or were last checked more than 7 days ago)

Exit codes: 0 = every DOI resolves and no retraction, withdrawal, removal or
expression-of-concern notice was found (and, with --library, every cited DOI is
in the library); 1 = findings (including DOIs that could not be checked);
2 = usage error, unreadable input, or no network at all (use --offline with a cache).
"""

import argparse
import datetime as _dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _doctext import (  # noqa: E402
    W,
    DocumentError,
    configure_utf8_stdio,
    docx_paragraphs,
    iter_files,
    line_number,
    read_text,
    read_xml_part,
)

INPUT_EXTS = frozenset({".bib", ".md", ".markdown", ".tex", ".txt", ".ris", ".qmd", ".rmd", ".docx", ".html", ".htm"})
LIBRARY_EXTS = frozenset({".md", ".bib", ".ris", ".txt"})

CROSSREF_WORK = "https://api.crossref.org/works/{doi}"
CROSSREF_UPDATES = "https://api.crossref.org/works?filter=updates:{doi}&rows=50"
DOI_HANDLE = "https://doi.org/api/handles/{doi}"
USER_AGENT = "neuroflow-cite-check/1.0 (+https://github.com/stanislavjiricek/neuroflow)"

SERIOUS_NOTICES = frozenset(
    {"retraction", "partial_retraction", "withdrawal", "removal", "expression_of_concern"}
)

DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"'<>{}|\\^`]+")
_TRAILING = ".,;:)]}>*"


class NetworkError(Exception):
    """The lookup could not reach the server (DNS, timeout, refused)."""


def fetch_json(url: str, timeout: float, user_agent: str = USER_AGENT):
    """GET a JSON document. Returns (HTTP status, parsed JSON or None).

    Raises NetworkError when the server cannot be reached. Tests replace this
    function, so it is the only place that touches the network.
    """
    req = urllib.request.Request(url, headers={"User-Agent": user_agent, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - fixed https hosts
            status, body = resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        status, body = exc.code, (exc.read() or b"")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise NetworkError(str(getattr(exc, "reason", exc))) from exc
    try:
        data = json.loads(body.decode("utf-8")) if body else None
    except (ValueError, UnicodeDecodeError):
        data = None
    return status, data


_sleep = time.sleep


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------


def clean_doi(raw: str) -> str:
    """Strip URL encoding and trailing punctuation; keep balanced parentheses."""
    doi = raw.strip()
    if "%" in doi:
        doi = urllib.parse.unquote(doi)
    while doi and doi[-1] in _TRAILING:
        if doi[-1] == ")" and doi.count("(") >= doi.count(")"):
            break
        doi = doi[:-1]
    return doi


def _docx_hidden_sources(path: Path) -> str:
    """Hyperlink targets and field codes (HYPERLINK, Zotero/Mendeley/EndNote CSL JSON)."""
    chunks: list[str] = []
    try:
        with zipfile.ZipFile(path) as zf:
            rels = read_xml_part(zf, "word/_rels/document.xml.rels")
            if rels is not None:
                for rel in rels:
                    target = rel.get("Target") or ""
                    if rel.get("TargetMode") == "External":
                        chunks.append(urllib.parse.unquote(target))
            for part in ("word/document.xml", "word/footnotes.xml", "word/endnotes.xml"):
                root = read_xml_part(zf, part)
                if root is not None:
                    chunks.append("".join(el.text or "" for el in root.iter(W + "instrText")))
    except (zipfile.BadZipFile, OSError) as exc:
        raise DocumentError(f"{path}: not a readable .docx ({exc})") from exc
    return "\n".join(chunks)


def extract_dois(path: Path):
    """Yield (doi, location) pairs found in one file."""
    if path.suffix.lower() == ".docx":
        for i, para in enumerate(docx_paragraphs(path), 1):
            for m in DOI_RE.finditer(para):
                yield clean_doi(m.group(0)), f"{path} para {i}"
        for m in DOI_RE.finditer(_docx_hidden_sources(path)):
            yield clean_doi(m.group(0)), f"{path} (link or field code)"
        return
    text = read_text(path)
    for m in DOI_RE.finditer(text):
        yield clean_doi(m.group(0)), f"{path}:{line_number(text, m.start())}"


_BIB_ENTRY = re.compile(r"@(\w+)\s*[{(]\s*([^,\s]+)\s*,", re.IGNORECASE)
_BIB_DOI = re.compile(r"\bdoi\s*=\s*[{\"]", re.IGNORECASE)


def bib_entries_without_doi(path: Path) -> list[str]:
    """Keys of .bib entries that carry no doi field (they cannot be checked by DOI)."""
    text = read_text(path)
    starts = [m for m in _BIB_ENTRY.finditer(text) if m.group(1).lower() not in {"comment", "string", "preamble"}]
    missing = []
    for i, m in enumerate(starts):
        body = text[m.end(): starts[i + 1].start() if i + 1 < len(starts) else len(text)]
        if not _BIB_DOI.search(body) and not DOI_RE.search(body):
            missing.append(f"{m.group(2)} ({path}:{line_number(text, m.start())})")
    return missing


# ---------------------------------------------------------------------------
# Lookup
# ---------------------------------------------------------------------------


def _date_of(obj) -> str | None:
    parts = (obj or {}).get("date-parts") or [[]]
    nums = [p for p in (parts[0] if parts else []) if p is not None]
    return "-".join(f"{n:02d}" if i else str(n) for i, n in enumerate(nums)) or None


def _get_with_retry(url: str, fetch, timeout: float, user_agent: str):
    status, data = fetch(url, timeout, user_agent)
    if status in (429, 503):
        _sleep(2.0)
        status, data = fetch(url, timeout, user_agent)
    return status, data


def lookup(doi: str, *, fetch=None, timeout: float = 15.0, user_agent: str = USER_AGENT,
           notices: bool = True, today: str | None = None) -> dict:
    """Check one DOI. Returns a cache-ready dict. Raises NetworkError when offline."""
    fetch = fetch or fetch_json
    entry = {
        "doi": doi, "checked_at": today or _dt.date.today().isoformat(), "resolves": None, "source": None,
        "title": None, "type": None, "year": None, "container": None, "notices": [], "vor": [],
        "notices_checked": False, "error": None,
    }
    quoted = urllib.parse.quote(doi, safe="/")
    status, data = _get_with_retry(CROSSREF_WORK.format(doi=quoted), fetch, timeout, user_agent)
    if status == 200 and isinstance(data, dict) and isinstance(data.get("message"), dict):
        msg = data["message"]
        entry.update(
            resolves=True, source="crossref", type=msg.get("type"),
            title=(msg.get("title") or [None])[0], container=(msg.get("container-title") or [None])[0],
            year=(_date_of(msg.get("issued")) or "")[:4] or None,
        )
        relation = msg.get("relation") or {}
        entry["vor"] = sorted({r.get("id") for r in relation.get("is-preprint-of", []) if r.get("id")})
        found = {}
        for upd in msg.get("updated-by") or []:
            key = ((upd.get("type") or "").lower(), (upd.get("DOI") or "").lower())
            found[key] = {"type": key[0], "notice_doi": upd.get("DOI"), "date": _date_of(upd.get("updated")),
                          "source": upd.get("source"), "label": upd.get("label")}
        if notices:
            st2, d2 = _get_with_retry(CROSSREF_UPDATES.format(doi=quoted), fetch, timeout, user_agent)
            if st2 == 200 and isinstance(d2, dict):
                for item in (d2.get("message") or {}).get("items") or []:
                    for upd in item.get("update-to") or []:
                        if (upd.get("DOI") or "").lower() != doi.lower():
                            continue
                        key = ((upd.get("type") or "").lower(), (item.get("DOI") or "").lower())
                        found.setdefault(key, {"type": key[0], "notice_doi": item.get("DOI"),
                                               "date": _date_of(upd.get("updated")),
                                               "source": upd.get("source"), "label": upd.get("label")})
                entry["notices_checked"] = True
            else:
                entry["error"] = f"notice query failed (HTTP {st2})"
        entry["notices"] = sorted(found.values(), key=lambda n: (n["type"], n["notice_doi"] or ""))
        return entry
    if status == 404:
        st2, d2 = _get_with_retry(DOI_HANDLE.format(doi=quoted), fetch, timeout, user_agent)
        code = d2.get("responseCode") if isinstance(d2, dict) else None
        if st2 == 200 and code == 1:
            entry.update(resolves=True, source="doi.org")
        elif code == 100 or st2 == 404:
            entry.update(resolves=False, source="doi.org")
        else:
            entry["error"] = f"doi.org lookup failed (HTTP {st2})"
        return entry
    entry["error"] = f"Crossref lookup failed (HTTP {status})"
    return entry


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    doi: str
    locations: list
    status: str            # ok | flag | note | unchecked
    label: str
    entry: dict = field(default_factory=dict)
    in_library: bool | None = None


def judge(doi: str, entry: dict | None, locations: list, library: set | None) -> Finding:
    in_lib = None if library is None else doi.lower() in library
    if entry is None:
        return Finding(doi, locations, "unchecked", "not checked (offline and not in the cache)", {}, in_lib)
    as_of = entry.get("checked_at")
    if entry.get("resolves") is None:
        return Finding(doi, locations, "unchecked", f"could not be checked: {entry.get('error')}", entry, in_lib)
    if entry["resolves"] is False:
        return Finding(doi, locations, "flag", "does not resolve", entry, in_lib)
    parts = [f"DOI resolves ({entry.get('source')})"]
    serious = [n for n in entry.get("notices", []) if n["type"] in SERIOUS_NOTICES]
    other = [n for n in entry.get("notices", []) if n["type"] not in SERIOUS_NOTICES]
    for n in serious + other:
        parts.append(f"{n['type'].replace('_', ' ')} notice {n.get('notice_doi') or '?'}"
                     f" ({n.get('date') or 'undated'}{', ' + n['source'] if n.get('source') else ''})")
    if entry.get("source") == "crossref" and entry.get("notices_checked") and not serious:
        parts.append(f"no retraction notice found in Crossref as of {as_of}")
    elif entry.get("source") == "doi.org":
        parts.append("not registered with Crossref, so notices were not checked")
    elif entry.get("error"):
        parts.append(entry["error"])
    if entry.get("vor"):
        parts.append("preprint; published version: " + ", ".join(entry["vor"]))
    status = "flag" if serious else ("note" if other or entry.get("vor") or entry.get("error") else "ok")
    if library is not None and not in_lib:
        parts.append("not in the project library")
        status = "flag"
    return Finding(doi, locations, status, "; ".join(parts), entry, in_lib)


def _load_cache(path: Path | None) -> dict:
    if path is None or not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data.get("entries", {}) if isinstance(data, dict) else {}


def _is_fresh(entry: dict | None, today: str, max_age: int) -> bool:
    """A cached lookup that answered (resolves or not) no more than max_age days before today."""
    if not entry or entry.get("resolves") is None or entry.get("error"):
        return False
    try:
        age = (_dt.date.fromisoformat(today) - _dt.date.fromisoformat(str(entry.get("checked_at")))).days
    except ValueError:
        return False
    return 0 <= age <= max_age


def _save_cache(path: Path, entries: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps({"version": 1, "entries": entries}, indent=1, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Check that cited DOIs resolve and look for retraction or correction notices in Crossref."
    )
    ap.add_argument("paths", nargs="+", help="manuscript, bibliography or library files or folders")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--offline", action="store_true", help="no network; use only the --cache file")
    ap.add_argument("--cache", type=Path, help="JSON cache of earlier lookups (read, and updated when online)")
    ap.add_argument("--library", type=Path,
                    help="project library: a folder (e.g. .neuroflow/ideation/papers) or a reference-manager "
                         "export (.bib/.ris); flag cited DOIs not in it")
    ap.add_argument("--mailto", help="e-mail for Crossref's polite pool (only if the person asked to send it)")
    ap.add_argument("--no-notices", action="store_true", help="only check that DOIs resolve")
    ap.add_argument("--timeout", type=float, default=15.0, help="seconds per request (default 15)")
    ap.add_argument("--delay", type=float, default=0.2, help="pause between DOIs in seconds (default 0.2)")
    ap.add_argument("--max-age", type=int, metavar="DAYS",
                    help="with --cache: look up only DOIs that are not cached or were checked more than DAYS days "
                         "ago (or failed); reuse the rest. A weekly --max-age 7 run re-checks every notice")
    args = ap.parse_args(argv)
    configure_utf8_stdio()

    if args.offline and not args.cache:
        print("cite_check: --offline needs --cache FILE", file=sys.stderr)
        return 2
    if args.max_age is not None and (not args.cache or args.max_age < 0):
        print("cite_check: --max-age needs --cache FILE and a number of days >= 0", file=sys.stderr)
        return 2

    locations: dict[str, list] = {}
    display: dict[str, str] = {}
    no_doi: list[str] = []
    try:
        files = iter_files(args.paths, INPUT_EXTS)
        for f in files:
            if not f.exists():
                print(f"cite_check: {f} does not exist", file=sys.stderr)
                return 2
            for doi, where in extract_dois(f):
                key = doi.lower()
                display.setdefault(key, doi)
                locations.setdefault(key, []).append(where)
            if f.suffix.lower() == ".bib":
                no_doi.extend(bib_entries_without_doi(f))
        library = None
        if args.library:
            if not args.library.exists():
                print(f"cite_check: library {args.library} does not exist", file=sys.stderr)
                return 2
            library = {d.lower() for lf in iter_files([args.library], LIBRARY_EXTS) for d, _ in extract_dois(lf)}
    except DocumentError as exc:
        print(f"cite_check: {exc}", file=sys.stderr)
        return 2

    cache = _load_cache(args.cache)
    user_agent = USER_AGENT + (f" mailto:{args.mailto}" if args.mailto else "")
    today = _dt.date.today().isoformat()
    findings: list[Finding] = []
    attempted = failed_network = reused = 0
    for key in sorted(locations):
        entry = cache.get(key)
        if not args.offline and args.max_age is not None and _is_fresh(entry, today, args.max_age):
            reused += 1
        elif not args.offline:
            if attempted:
                _sleep(args.delay)
            attempted += 1
            try:
                entry = lookup(display[key], timeout=args.timeout, user_agent=user_agent,
                               notices=not args.no_notices, today=today)
                cache[key] = entry
            except NetworkError as exc:
                failed_network += 1
                entry = {"doi": display[key], "resolves": None, "error": f"network error: {exc}",
                         "checked_at": today, "notices": []}
        findings.append(judge(display[key], entry, locations[key], library))

    if attempted and failed_network == attempted:
        print("cite_check: no network: none of the DOIs could be looked up. "
              "Run again later, or use --offline --cache FILE.", file=sys.stderr)
        return 2
    if args.cache and not args.offline:
        _save_cache(args.cache, {k: v for k, v in cache.items() if v.get("resolves") is not None})

    counts = {
        "dois": len(findings),
        "resolve": sum(1 for f in findings if f.entry.get("resolves") is True),
        "do_not_resolve": sum(1 for f in findings if f.entry.get("resolves") is False),
        "unchecked": sum(1 for f in findings if f.status == "unchecked"),
        "serious_notices": sum(1 for f in findings
                               if any(n["type"] in SERIOUS_NOTICES for n in f.entry.get("notices", []))),
        "other_notices": sum(1 for f in findings
                             if any(n["type"] not in SERIOUS_NOTICES for n in f.entry.get("notices", []))),
        "not_in_library": sum(1 for f in findings if f.in_library is False),
    }
    exit_code = 1 if any(f.status in ("flag", "unchecked") for f in findings) else 0

    if args.json:
        print(json.dumps({
            "checked_at": today, "mode": "offline" if args.offline else "online",
            "max_age_days": args.max_age, "reused_from_cache": reused,
            "summary": counts, "bib_entries_without_doi": no_doi,
            "dois": [asdict(f) for f in findings],
        }, ensure_ascii=False, indent=1))
        return exit_code

    if not findings:
        print("cite_check: no DOIs found. Citations without a DOI are not checked by this script.")
    order = {"flag": 0, "unchecked": 1, "note": 2, "ok": 3}
    for f in sorted(findings, key=lambda x: (order[x.status], x.doi.lower())):
        tag = {"flag": "FLAG", "unchecked": "FLAG", "note": "note", "ok": "ok  "}[f.status]
        first = f.locations[0] + (f" (+{len(f.locations) - 1} more)" if len(f.locations) > 1 else "")
        print(f"{tag} {f.doi}  {f.label}  [{first}]")
    if no_doi:
        print(f"\nBibliography entries without a DOI (not checked here; check them by hand): {', '.join(no_doi)}")
    if findings:
        print(
            f"\nSummary: {counts['dois']} DOIs; {counts['resolve']} DOI resolves, {counts['do_not_resolve']} do not "
            f"resolve, {counts['unchecked']} could not be checked; {counts['serious_notices']} with a retraction, "
            f"withdrawal, removal or expression-of-concern notice; {counts['other_notices']} with other notices"
            + (f"; {counts['not_in_library']} not in the project library" if library is not None else "") + "."
        )
        print("Notices come from Crossref metadata (publishers and the Retraction Watch database). Coverage is "
              "incomplete: 'no retraction notice found' is not proof that a paper was not retracted, and a DOI "
              "that resolves says nothing about whether the paper supports the sentence that cites it.")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
