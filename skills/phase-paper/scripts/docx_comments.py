#!/usr/bin/env python3
"""docx_comments.py: list a Word file's comments and tracked changes as a work table.

When a coauthor returns the manuscript as .docx with comments and tracked
changes, /paper --coauthor works through them one by one. This script reads
the .docx (a zip of XML parts) with the standard library and writes one row
per item, with empty Disposition and Note columns to fill in:

- comments (word/comments.xml): author, date, text, the anchored manuscript
  text (between commentRangeStart and commentRangeEnd), reply threads and the
  "resolved" flag (word/commentsExtended.xml);
- tracked changes (w:ins, w:del, w:moveTo, w:moveFrom in the body, footnotes
  and endnotes): author, date, paragraph, the inserted or deleted text; a
  deletion directly followed by an insertion from the same author is shown as
  one replacement;
- formatting-only changes are counted, not listed.

The .docx is never modified.

Usage:
    python docx_comments.py manuscript/main-JS.docx
    python docx_comments.py manuscript/main-JS.docx --round 2 --out .neuroflow/paper/coauthor-round-2.md
    python docx_comments.py manuscript/main-JS.docx --json

Paragraph numbers ("para N") count every paragraph of the body in order, the
same way statcheck.py and cite_check.py number .docx paragraphs.
Exit codes: 0 = no comments or tracked changes; 1 = items to work through;
2 = usage or read error.
"""

import argparse
import datetime as _dt
import json
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _doctext import W, DocumentError, configure_utf8_stdio, read_xml_part, squash  # noqa: E402

W14 = "{http://schemas.microsoft.com/office/word/2010/wordml}"
W15 = "{http://schemas.microsoft.com/office/word/2012/wordml}"
CHANGE_TAGS = {W + "ins": "insertion", W + "del": "deletion", W + "moveTo": "move (new place)",
               W + "moveFrom": "move (old place)"}
FORMAT_CHANGE_TAGS = {W + "rPrChange", W + "pPrChange", W + "sectPrChange", W + "tblPrChange",
                      W + "trPrChange", W + "tcPrChange", W + "numberingChange"}


def _a(el, name: str, ns: str = W):
    return el.get(ns + name)


def _date(raw: str | None) -> str:
    return (raw or "")[:10]


def read_comments(zf: zipfile.ZipFile) -> dict:
    root = read_xml_part(zf, "word/comments.xml")
    comments: dict[str, dict] = {}
    if root is None:
        return comments
    for c in root.iter(W + "comment"):
        cid = _a(c, "id")
        paras = [p for p in c.iter(W + "p")]
        text = " ".join(squash("".join(t.text or "" for t in p.iter(W + "t"))) for p in paras).strip()
        last_para_id = _a(paras[-1], "paraId", W14) if paras else None
        comments[cid] = {"id": cid, "author": _a(c, "author") or "?", "initials": _a(c, "initials") or "",
                         "date": _date(_a(c, "date")), "text": text, "para_id": last_para_id,
                         "anchor": "", "para": None, "parent": None, "done": False}
    ext = read_xml_part(zf, "word/commentsExtended.xml")
    if ext is not None:
        by_para = {c["para_id"]: c for c in comments.values() if c["para_id"]}
        for ex in ext.iter(W15 + "commentEx"):
            c = by_para.get(_a(ex, "paraId", W15))
            if not c:
                continue
            c["done"] = (_a(ex, "done", W15) or "0") in {"1", "true"}
            parent = by_para.get(_a(ex, "paraIdParent", W15))
            if parent:
                c["parent"] = parent["id"]
    return comments


class _Walker:
    """Document-order walk: paragraph numbers, comment anchors, tracked changes."""

    def __init__(self, comments: dict):
        self.comments = comments
        self.para = 0
        self.para_text: dict[int, list[str]] = {}
        self.open: set[str] = set()
        self.anchors: dict[str, list[str]] = {}
        self.changes: list[dict] = []
        self.format_changes = 0
        self.seq = 0  # running index of text nodes, to tell adjacent changes apart

    def walk(self, el: ET.Element, change: dict | None = None) -> None:
        tag = el.tag
        if tag == W + "p":
            self.para += 1
            self.para_text.setdefault(self.para, [])
        elif tag in (W + "rPr", W + "pPr"):
            self.format_changes += sum(1 for d in el.iter() if d.tag in FORMAT_CHANGE_TAGS)
            return
        elif tag in FORMAT_CHANGE_TAGS:
            self.format_changes += 1
            return
        elif tag == W + "commentRangeStart":
            cid = _a(el, "id")
            self.open.add(cid)
            self.anchors.setdefault(cid, [])
            if cid in self.comments and self.comments[cid]["para"] is None:
                self.comments[cid]["para"] = self.para
        elif tag == W + "commentRangeEnd":
            self.open.discard(_a(el, "id"))
        elif tag == W + "commentReference":
            cid = _a(el, "id")
            if cid in self.comments and self.comments[cid]["para"] is None:
                self.comments[cid]["para"] = self.para
        elif tag in CHANGE_TAGS:
            change = {"kind": CHANGE_TAGS[tag], "author": _a(el, "author") or "?", "date": _date(_a(el, "date")),
                      "para": self.para, "parts": [], "first": None, "last": None}
            self.changes.append(change)
        elif tag in (W + "t", W + "delText"):
            text = el.text or ""
            self.seq += 1
            deleted = tag == W + "delText" or (change is not None and change["kind"] in ("deletion", "move (old place)"))
            if change is not None:
                change["parts"].append(text)
                change["first"] = change["first"] or self.seq
                change["last"] = self.seq
            if not deleted:
                self.para_text.setdefault(self.para, []).append(text)
                for cid in self.open:
                    self.anchors[cid].append(text)
        elif tag == W + "tab":
            self.para_text.setdefault(self.para, []).append(" ")
        for child in el:
            self.walk(child, change)


def _merge(changes: list[dict]) -> list[dict]:
    """Drop empty changes; join touching pieces of one edit.

    Word splits one edit into several w:ins/w:del elements when formatting
    changes inside it, and writes a replacement as a deletion followed by an
    insertion. Pieces are joined only when no other text lies between them.
    """
    items = [dict(c, text="".join(c["parts"])) for c in changes]
    items = [c for c in items if c["text"].strip()]
    out: list[dict] = []
    for c in items:
        prev = out[-1] if out else None
        touching = bool(prev) and prev["author"] == c["author"] and prev["para"] == c["para"] \
            and c["first"] == prev["last"] + 1
        if touching and prev["kind"] == c["kind"] and c["kind"] != "replacement":
            prev["text"] += c["text"]
            prev["last"] = c["last"]
            continue
        if touching and prev["kind"] == "deletion" and c["kind"] == "insertion":
            prev.update(kind="replacement", old=prev["text"], new=c["text"], last=c["last"])
            continue
        if touching and prev["kind"] == "replacement" and c["kind"] == "insertion":
            prev["new"] += c["text"]
            prev["last"] = c["last"]
            continue
        out.append(c)
    for c in out:
        if c["kind"] == "replacement":
            c["text"] = f'"{c["old"]}" -> "{c["new"]}"'
        elif c["kind"] == "deletion":
            c["text"] = f'- "{c["text"]}"'
        elif c["kind"] == "insertion":
            c["text"] = f'+ "{c["text"]}"'
        for key in ("parts", "first", "last"):
            c.pop(key, None)
    return out


def extract(path: Path) -> dict:
    try:
        with zipfile.ZipFile(path) as zf:
            comments = read_comments(zf)
            walker = _Walker(comments)
            doc = read_xml_part(zf, "word/document.xml")
            if doc is None:
                raise DocumentError(f"{path}: no word/document.xml inside")
            for part in ("word/document.xml", "word/footnotes.xml", "word/endnotes.xml"):
                root = doc if part == "word/document.xml" else read_xml_part(zf, part)
                if root is not None:
                    walker.walk(root)
    except (zipfile.BadZipFile, OSError) as exc:
        raise DocumentError(f"{path}: not a readable .docx ({exc})") from exc
    for cid, c in comments.items():
        anchor = squash("".join(walker.anchors.get(cid, [])))
        if not anchor and c["para"]:
            anchor = "(paragraph) " + squash("".join(walker.para_text.get(c["para"], [])))
        c["anchor"] = anchor
        c.pop("para_id", None)
    changes = _merge(walker.changes)
    for c in changes:
        c["context"] = squash("".join(walker.para_text.get(c["para"], [])))
    return {"file": str(path), "comments": _threads(comments), "changes": changes,
            "formatting_changes": walker.format_changes}


def _num(cid) -> int:
    return int(cid) if str(cid).isdigit() else 0


def _threads(comments: dict) -> list[dict]:
    """Comments in document order, each reply right after the comment it answers."""
    def root(c):
        seen = set()
        while c["parent"] in comments and c["id"] not in seen:
            seen.add(c["id"])
            c = comments[c["parent"]]
        return c

    for c in comments.values():
        r = root(c)
        if c["para"] is None:
            c["para"] = r["para"]

    def key(c):
        r = root(c)
        para = r["para"] if r["para"] is not None else 10 ** 9
        return (para, _num(r["id"]), 0 if c is r else 1, _num(c["id"]))

    return sorted(comments.values(), key=key)


def _cell(text: str, limit: int = 220) -> str:
    text = squash(text or "")
    if len(text) > limit:
        text = text[:limit - 3] + "..."
    return text.replace("|", "\\|")


def to_markdown(data: dict, round_no: int | None, today: str) -> str:
    comments, changes = data["comments"], data["changes"]
    number = {c["id"]: f"C{i}" for i, c in enumerate(comments, 1)}
    replies = sum(1 for c in comments if c["parent"])
    resolved = sum(1 for c in comments if c["done"])
    title = f"Coauthor round {round_no}" if round_no else "Coauthor round"
    lines = [
        f"# {title}: {Path(data['file']).name}",
        "",
        f"Source: `{data['file']}` · extracted {today} · {len(comments)} comment(s) ({replies} replies, "
        f"{resolved} marked resolved) · {len(changes)} tracked change(s)"
        + (f" · {data['formatting_changes']} formatting change(s) not listed" if data["formatting_changes"] else ""),
        "",
        "Disposition: accept · reply · task · decline (with a reason). The round closes when every row has one.",
        "",
        "| # | Type | Author | Date | Where | Anchor / change | Comment | Disposition | Note |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for c in comments:
        kind = f"reply to {number.get(c['parent'], '?')}" if c["parent"] else "comment"
        if c["done"]:
            kind += " (resolved)"
        where = f"para {c['para']}" if c["para"] else "-"
        lines.append(f"| {number[c['id']]} | {kind} | {_cell(c['author'], 60)} | {c['date']} | {where} | "
                     f"{_cell(c['anchor'])} | {_cell(c['text'], 400)} |  |  |")
    for i, ch in enumerate(changes, 1):
        lines.append(f"| T{i} | {ch['kind']} | {_cell(ch['author'], 60)} | {ch['date']} | para {ch['para']} | "
                     f"{_cell(ch['text'])} | context: {_cell(ch['context'], 160)} |  |  |")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="List comments and tracked changes in a .docx as a markdown work table.")
    ap.add_argument("docx", type=Path, help="the .docx returned by a coauthor (never modified)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--out", type=Path, help="write the markdown table to this file instead of stdout")
    ap.add_argument("--round", type=int, help="round number shown in the title")
    args = ap.parse_args(argv)
    configure_utf8_stdio()

    if not args.docx.exists():
        print(f"docx_comments: {args.docx} does not exist", file=sys.stderr)
        return 2
    if args.docx.suffix.lower() != ".docx":
        print("docx_comments: expected a .docx file (save .doc files as .docx first)", file=sys.stderr)
        return 2
    try:
        data = extract(args.docx)
    except DocumentError as exc:
        print(f"docx_comments: {exc}", file=sys.stderr)
        return 2
    exit_code = 1 if data["comments"] or data["changes"] else 0
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=1))
        return exit_code
    md = to_markdown(data, args.round, _dt.date.today().isoformat())
    if args.out:
        if args.out.exists():
            print(f"docx_comments: {args.out} exists; choose a new round number or file", file=sys.stderr)
            return 2
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(md, encoding="utf-8")
        print(f"docx_comments: {len(data['comments'])} comment(s), {len(data['changes'])} tracked change(s) "
              f"written to {args.out}")
    else:
        print(md, end="")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
