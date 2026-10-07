#!/usr/bin/env python3
"""revise_audit.py: does every manuscript change trace to a reviewer comment?

The /paper --revise prime rule: changes are minimal, each one answers a
specific reviewer comment, and the response document and the manuscript diff
match 1:1. This script checks that from disk:

1. diffs each pre-revision file against its revised copy, sentence by
   sentence (difflib), ignoring LaTeX/HTML comments and whitespace;
2. reads the response document, split into comments by headings that start
   with a comment id (## R1.2, ### R2.1, ## E.1 for reviewers and editors;
   C4 / T2 for coauthor-round rows; S3.2-1 for X-ray findings), and collects
   the block-quoted passages introduced as changes:

       ## R1.2 Justify the connectivity measure
       > Reviewer: the choice of connectivity measure is not justified.

       We added the justification.

       Changed (Methods, lines 143-147):
       > We used the weighted phase-lag index because it is insensitive to volume conduction.

   A block quote counts as a change when the line before it says Changed,
   Revised, Added, Inserted, Replaced, Now reads or New text; as a deletion
   when it says Deleted or Removed. Other block quotes (the reviewer's words)
   are context;
3. reports every changed or deleted sentence that no comment quotes
   (untraceable change), and every claimed change that is not in the revised
   text (or claimed deletion still there).

A quote may cover a whole sentence or a fragment of at least 20 characters
("..." splits fragments). Matching ignores case, whitespace and markup.

Usage:
    python revise_audit.py --response manuscript/revision/response-to-reviewers.md \\
        --pair manuscript/methods.md manuscript/revision/methods-r1.md \\
        --pair manuscript/results.md manuscript/revision/results-r1.md

Input: .md .tex .txt .qmd .rmd .docx (a revised .docx is read with its tracked
changes accepted). Exit codes: 0 = every change traces to a comment and every
claimed change is present; 1 = findings; 2 = usage or read error.
"""

import argparse
import difflib
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _doctext import (  # noqa: E402
    DocumentError,
    configure_utf8_stdio,
    read_text,
    squash,
    strip_comments,
)

MIN_FRAGMENT = 20

# Comment ids: R1.2 (reviewer 1, comment 2), E.1 / E1 (editor), C4 / T2 (coauthor round rows),
# S3.2-1 (X-ray finding). The id must start the heading and contain a digit.
_HEADING_ID = re.compile(r"^#{1,6}[ \t]+\**(?P<id>[A-Z]{1,3}\.?\d+(?:\.\d+)*[a-z]?(?:-\d+)?)\b")
_CHANGE_LEAD = re.compile(r"\b(?:changed?|changes|revised|revision|added|inserted|replaced|modified|now reads|new text)\b",
                          re.IGNORECASE)
_DELETE_LEAD = re.compile(r"\b(?:deleted|removed)\b", re.IGNORECASE)
_SENT_SPLIT = re.compile(r"(?<=[.!?])[\"')\]]*\s+(?=[A-Z0-9(\[\"'\u201c])")


@dataclass
class Unit:
    text: str
    norm: str
    line: int


@dataclass
class Passage:
    comment: str
    kind: str            # change | deletion | context
    text: str
    line: int
    fragments: list = field(default_factory=list)


@dataclass
class Change:
    file: str
    line: int
    kind: str            # changed | added | deleted
    text: str
    comments: list = field(default_factory=list)


def norm(s: str) -> str:
    s = s.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    s = s.replace("\u2013", "-").replace("\u2014", "-").replace("\\%", "%")
    s = re.sub(r"\\[A-Za-z]+\*?", " ", s)
    s = re.sub(r"[{}$~*_`]", " ", s)
    s = squash(s).lower()
    return s.strip(" \"'.,;:")


def _fragments(text: str) -> list[str]:
    parts = [norm(p) for p in re.split(r"\.\.\.|\u2026|\[\s*\.\.\.\s*\]", text)]
    return [p for p in parts if len(p) >= MIN_FRAGMENT] or ([norm(text)] if norm(text) else [])


def units(text: str, *, docx: bool) -> list[Unit]:
    """Sentence units with the line (or paragraph, for .docx) where each starts."""
    out: list[Unit] = []
    lines = text.split("\n")
    para: list[tuple[int, str]] = []

    def flush():
        if not para:
            return
        joined = " ".join(t for _, t in para)
        offsets, pos = [], 0
        for ln, t in para:
            offsets.append((pos, ln))
            pos += len(t) + 1
        start = 0
        for piece in _SENT_SPLIT.split(joined):
            idx = joined.find(piece, start)
            start = idx + len(piece) if idx >= 0 else start
            line = next((ln for off, ln in reversed(offsets) if off <= max(idx, 0)), para[0][0])
            n = norm(piece)
            if n:
                out.append(Unit(squash(piece), n, line))
        para.clear()

    for i, raw in enumerate(lines, 1):
        if docx:
            para.append((i, raw))
            flush()
        elif raw.strip():
            para.append((i, raw.strip()))
        else:
            flush()
    flush()
    return out


def parse_response(text: str) -> tuple[dict, list[Passage]]:
    """Comment ids (with heading line) and quoted passages from the response document."""
    comments: dict[str, int] = {}
    passages: list[Passage] = []
    current = None
    lead = ""
    block: list[str] = []
    block_line = 0

    def end_block():
        nonlocal block
        if block and current:
            body = " ".join(block)
            kind = "deletion" if _DELETE_LEAD.search(lead) else ("change" if _CHANGE_LEAD.search(lead) else "context")
            passages.append(Passage(current, kind, squash(body), block_line, _fragments(body)))
        block = []

    for i, raw in enumerate(text.split("\n"), 1):
        line = raw.rstrip()
        m = _HEADING_ID.match(line)
        if m:
            end_block()
            current = m.group("id").upper()
            comments.setdefault(current, i)
            lead = ""
            continue
        if line.lstrip().startswith(">"):
            if not block:
                block_line = i
            block.append(line.lstrip()[1:].strip())
            continue
        end_block()
        if line.strip():
            lead = line
    end_block()
    return comments, passages


def _covered(unit_norm: str, passage: Passage, threshold: float) -> bool:
    for frag in passage.fragments:
        if unit_norm in frag or (len(frag) >= MIN_FRAGMENT and frag in unit_norm):
            return True
    whole = norm(passage.text)
    return bool(whole) and difflib.SequenceMatcher(None, unit_norm, whole, autojunk=False).ratio() >= threshold


def audit_pair(orig_path: Path, rev_path: Path, passages: list[Passage], threshold: float):
    """Changed sentences of one file pair, plus both texts normalized (for the reverse check)."""
    def load(p: Path):
        text = strip_comments(read_text(p), p.suffix)
        return units(text, docx=p.suffix.lower() == ".docx"), norm(text)

    (old, old_text), (new, rev_text) = load(orig_path), load(rev_path)
    sm = difflib.SequenceMatcher(None, [u.norm for u in old], [u.norm for u in new], autojunk=False)
    changes: list[Change] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        if j2 > j1:
            for u in new[j1:j2]:
                ids = sorted({p.comment for p in passages if p.kind == "change" and _covered(u.norm, p, threshold)})
                changes.append(Change(str(rev_path), u.line, "changed" if tag == "replace" else "added", u.text, ids))
        else:
            for u in old[i1:i2]:
                ids = sorted({p.comment for p in passages
                              if p.kind in ("deletion", "change") and _covered(u.norm, p, threshold)})
                changes.append(Change(str(orig_path), u.line, "deleted", u.text, ids))
    return changes, rev_text, old_text


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Check that every manuscript change in a revision traces to a reviewer comment in the response."
    )
    ap.add_argument("--response", required=True, type=Path, help="response-to-reviewers document (.md)")
    ap.add_argument("--pair", nargs=2, action="append", metavar=("ORIGINAL", "REVISED"), required=True,
                    type=Path, help="pre-revision file and its revised copy; repeat for each file")
    ap.add_argument("--similarity", type=float, default=0.85,
                    help="minimum similarity for a quote that is not an exact substring (default 0.85)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)
    configure_utf8_stdio()

    for path in [args.response] + [p for pair in args.pair for p in pair]:
        if not path.exists():
            print(f"revise_audit: {path} does not exist", file=sys.stderr)
            return 2
    try:
        comments, passages = parse_response(read_text(args.response))
        if not comments:
            print("revise_audit: no comment headings found in the response (expected headings like '## R1.2 ...')",
                  file=sys.stderr)
            return 2
        all_changes: list[Change] = []
        rev_all, old_all = [], []
        for orig, rev in args.pair:
            changes, rev_text, old_text = audit_pair(orig, rev, passages, args.similarity)
            all_changes.extend(changes)
            rev_all.append(rev_text)
            old_all.append(old_text)
    except DocumentError as exc:
        print(f"revise_audit: {exc}", file=sys.stderr)
        return 2

    revised_blob, original_blob = " ".join(rev_all), " ".join(old_all)
    missing = []
    for p in passages:
        if p.kind == "change" and not any(f in revised_blob for f in p.fragments):
            missing.append({"comment": p.comment, "line": p.line, "problem": "claimed change not found in the revised text",
                            "text": p.text})
        elif p.kind == "deletion" and (any(f in revised_blob for f in p.fragments)
                                       or not any(f in original_blob for f in p.fragments)):
            missing.append({"comment": p.comment, "line": p.line,
                            "problem": "claimed deletion still in the revised text or not in the original",
                            "text": p.text})
    untraceable = [c for c in all_changes if not c.comments]
    traced = [c for c in all_changes if c.comments]
    exit_code = 1 if untraceable or missing else 0

    if args.json:
        print(json.dumps({
            "comments": sorted(comments), "changes": [asdict(c) for c in all_changes],
            "untraceable": len(untraceable), "claimed_but_missing": missing,
        }, ensure_ascii=False, indent=1))
        return exit_code

    print(f"revise_audit: {len(all_changes)} changed sentence(s) in {len(args.pair)} file pair(s); "
          f"{len(comments)} comment id(s) in {args.response}")
    for c in all_changes:
        tag = "ok  " if c.comments else "FLAG"
        target = ", ".join(c.comments) if c.comments else "no comment quotes this change"
        print(f'{tag} {c.file}:{c.line}  {c.kind}: "{c.text[:160]}"  -> {target}')
    for m in missing:
        print(f'FLAG {args.response}:{m["line"]}  {m["comment"]}: {m["problem"]}: "{m["text"][:160]}"')
    print(f"\nSummary: {len(traced)} change(s) trace to a comment, {len(untraceable)} untraceable, "
          f"{len(missing)} claimed change(s) not matching the manuscript.")
    if exit_code:
        print("Untraceable changes are reverted, or added to the response with the person's approval; "
              "claimed changes that are not in the manuscript are fixed in one place or the other.")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
