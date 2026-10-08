"""Shared text extraction for the phase-paper scripts (stdlib only).

Not a CLI. Imported by cite_check.py, statcheck.py, revise_audit.py and
docx_comments.py, which add this folder to sys.path before importing it.

- Plain-text formats (.md, .tex, .bib, .txt, ...) are read as UTF-8.
- .docx is read from word/document.xml (plus footnotes and endnotes) with the
  standard library: one string per paragraph, tracked insertions kept and
  tracked deletions dropped (the "accepted" view), or the reverse for the
  "original" view.
"""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{W_NS}}}"

TEXT_EXTS = frozenset(
    {".md", ".markdown", ".txt", ".tex", ".bib", ".ris", ".rst", ".qmd", ".rmd", ".html", ".htm"}
)
DOCX_EXTS = frozenset({".docx"})
SKIP_DIRS = frozenset({".git", "node_modules", "__pycache__", ".venv", "venv", ".ipynb_checkpoints"})

# Parts of a .docx that carry manuscript text, in reading order.
DOCX_TEXT_PARTS = ("word/document.xml", "word/footnotes.xml", "word/endnotes.xml")

_INS_TAGS = frozenset({W + "ins", W + "moveTo"})
_DEL_TAGS = frozenset({W + "del", W + "moveFrom"})


class DocumentError(Exception):
    """A file could not be read as a manuscript."""


def read_xml_part(zf: zipfile.ZipFile, name: str) -> ET.Element | None:
    """Parse one XML part of an OOXML package; None when the part is absent."""
    try:
        data = zf.read(name)
    except KeyError:
        return None
    try:
        return ET.fromstring(data)
    except ET.ParseError as exc:
        raise DocumentError(f"{name} is not well-formed XML: {exc}") from exc


def paragraph_text(p: ET.Element, *, accept_changes: bool = True) -> str:
    """Text of one w:p element.

    accept_changes=True  -> insertions kept, deletions dropped (what Word shows
                            after "Accept all").
    accept_changes=False -> deletions kept, insertions dropped (the text before
                            the tracked changes).
    Nested paragraphs (text boxes) are skipped here; iterate them separately.
    """
    out: list[str] = []

    def walk(el: ET.Element, in_ins: bool, in_del: bool) -> None:
        tag = el.tag
        if tag == W + "p" and el is not p:
            return
        if tag in _INS_TAGS:
            in_ins = True
        elif tag in _DEL_TAGS:
            in_del = True
        if tag in (W + "t", W + "delText"):
            keep = (not in_del) if accept_changes else (not in_ins)
            if keep and (tag == W + "t" or not accept_changes):
                out.append(el.text or "")
        elif tag == W + "tab":
            out.append("\t")
        elif tag in (W + "br", W + "cr"):
            out.append(" ")
        elif tag == W + "noBreakHyphen":
            out.append("-")
        for child in el:
            walk(child, in_ins, in_del)

    walk(p, False, False)
    return "".join(out)


def docx_paragraphs(path: Path, *, accept_changes: bool = True, parts=DOCX_TEXT_PARTS) -> list[str]:
    """One string per paragraph of the body, then footnotes and endnotes."""
    try:
        with zipfile.ZipFile(path) as zf:
            roots = [(name, read_xml_part(zf, name)) for name in parts]
    except (zipfile.BadZipFile, OSError) as exc:
        raise DocumentError(f"{path}: not a readable .docx ({exc})") from exc
    if roots[0][1] is None:
        raise DocumentError(f"{path}: no word/document.xml inside")
    paras: list[str] = []
    for _name, root in roots:
        if root is None:
            continue
        for p in root.iter(W + "p"):
            paras.append(paragraph_text(p, accept_changes=accept_changes))
    return paras


def read_text(path: Path, *, accept_changes: bool = True) -> str:
    """Plain text of a manuscript or bibliography file ('-' is not handled here)."""
    path = Path(path)
    if path.suffix.lower() in DOCX_EXTS:
        return "\n".join(docx_paragraphs(path, accept_changes=accept_changes))
    try:
        return path.read_bytes().decode("utf-8-sig", errors="replace")
    except OSError as exc:
        raise DocumentError(f"{path}: cannot read ({exc})") from exc


def iter_files(paths, exts) -> list[Path]:
    """Expand directories (recursively, sorted) to files with the given suffixes.

    Explicit file arguments are returned as given, whatever their suffix.
    Hidden tool folders and Word lock files (~$name.docx) are skipped.
    """
    out: list[Path] = []
    seen: set[Path] = set()
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            candidates = []
            for f in sorted(p.rglob("*")):
                rel_parts = f.relative_to(p).parts
                if any(part in SKIP_DIRS for part in rel_parts[:-1]):
                    continue
                if f.is_file() and f.suffix.lower() in exts and not f.name.startswith("~$"):
                    candidates.append(f)
        else:
            candidates = [p]
        for f in candidates:
            key = f.resolve() if f.exists() else f
            if key not in seen:
                seen.add(key)
                out.append(f)
    return out


def line_number(text: str, offset: int) -> int:
    """1-based line number of a character offset."""
    return text.count("\n", 0, offset) + 1


_TEX_COMMENT = re.compile(r"(?<!\\)%.*")
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


def strip_comments(text: str, suffix: str) -> str:
    """Remove LaTeX (%) or HTML (<!-- -->) comments, keeping every newline.

    Comments are not part of the rendered manuscript, so checks of the
    manuscript ignore them. (hidden_text_scan.py in review-neuro is the tool
    that reads comments on purpose.)
    """
    suffix = suffix.lower()
    if suffix == ".tex":
        return _TEX_COMMENT.sub("", text)
    if suffix in {".md", ".markdown", ".qmd", ".rmd", ".html", ".htm"}:
        return _HTML_COMMENT.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    return text


def configure_utf8_stdio() -> None:
    """Make stdin/stdout UTF-8 so Greek letters and minus signs survive Windows pipes."""
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass


_WS = re.compile(r"\s+")


def squash(text: str) -> str:
    """Collapse runs of whitespace to one space and strip."""
    return _WS.sub(" ", text).strip()
