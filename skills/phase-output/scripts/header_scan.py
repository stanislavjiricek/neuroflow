#!/usr/bin/env python3
"""De-identification scan of recording headers and participant tables (phase-output).

Run before a dataset leaves the project (/output --archive). It reads headers
only, never signal data, and never prints a value: a finding names the file,
the field and the class.

Checks:
- EDF / EDF+ / BDF: the patient field (EDF+ subfields: code, sex, birthdate,
  name) and the recording field (EDF+: hospital administration code,
  investigator). A patient code is accepted when it equals the BIDS subject
  label in the file name (sub-<label>). Plain EDF free text is a finding.
- BrainVision (.vhdr, .vmrk): DataFile=/MarkerFile= pointers that name a file
  other than the header itself (often the original, possibly identifying
  name), and personal data in comments and marker texts.
- NIfTI-1/2 (.nii, .nii.gz): descrip and aux_file text, DICOM header
  extensions (patient tags), comment extensions.
- participants.tsv: identifying column names (an English baseline plus the
  config's "identifying_columns"), participant_id values that are not
  sub-<label> pseudonyms.
- FIF (.fif): subject_info names, birthday and hospital ID - only when MNE is
  installed (pip install mne); otherwise listed as not scanned.
Free-text fields also go through pii_scan.py (emails, phone numbers, your
configured ID patterns, roster names).

Not covered (listed as other formats): EEGLAB .set, GDF, DICOM files, vendor
formats - check those with a dedicated tool. Defacing of anatomical images is a
separate step.

Usage:
    python <phase-output skill base dir>/scripts/header_scan.py [PATH ...]
        [--config FILE] [--roster FILE] [--json]

Exit codes:
    0  clean
    1  findings, or files that could not be scanned
    2  usage or runtime error

Stdlib only (MNE optional for .fif). Python 3.10+.
"""

from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
import os
import re
import struct
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

IDENTIFYING_COLUMNS = {
    "name", "first_name", "firstname", "given_name", "middle_name", "last_name", "lastname",
    "surname", "family_name", "full_name", "initials", "birth_date", "birthdate",
    "date_of_birth", "dob", "birthday", "email", "e_mail", "email_address", "phone",
    "phone_number", "telephone", "mobile", "address", "street", "street_address",
    "postal_code", "postcode", "zip", "zip_code", "national_id", "ssn",
    "social_security_number", "passport", "passport_number", "insurance_number",
    "health_insurance_number", "mrn", "medical_record_number", "hospital_id", "patient_id",
    "record_number",
}
OTHER_FORMATS = {".set", ".fdt", ".gdf", ".cnt", ".xdf", ".snirf", ".mff", ".dcm", ".mat", ".mgz"}
SKIP_DIRS = {".git", ".datalad", "node_modules", "__pycache__"}
MAX_HEADER_BYTES = 16 * 1024 * 1024
SUB_RE = re.compile(r"sub-([A-Za-z0-9]+)")


@dataclass
class Item:
    path: str
    field: str
    kind: str
    detail: str = ""


class ScanError(Exception):
    """Usage or runtime error (exit code 2)."""


def _pii():
    """pii_scan.py (one home for the text patterns)."""
    name = "_nf_phase_output_pii_scan"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name("pii_scan.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _import_mne():
    try:
        import mne  # noqa: F401 - optional dependency
    except ImportError:
        return None
    return mne


def suffix_of(path: Path) -> str:
    name = path.name.lower()
    for double in (".nii.gz", ".fif.gz"):
        if name.endswith(double):
            return double
    return path.suffix.lower()


def subject_label(path: Path) -> str | None:
    m = SUB_RE.search(path.as_posix())
    return m.group(1) if m else None


def is_pseudonym(code: str, label: str | None) -> bool:
    code = code.strip().lower()
    return bool(label) and code in (label.lower(), f"sub-{label.lower()}")


def text_findings(rel: str, field: str, text: str, scanner) -> list[Item]:
    return [Item(rel, field, kind, f"line {no}" if "\n" in text else "")
            for no, kind in scanner.scan_text(text)]


# ---------------------------------------------------------------------------
# Formats
# ---------------------------------------------------------------------------


def scan_edf(path: Path, rel: str, scanner) -> tuple[list[Item], list[Item]]:
    with open(path, "rb") as fh:
        head = fh.read(256)
    if len(head) < 256:
        return [], [Item(rel, "header", "unreadable", "shorter than the 256-byte EDF header")]
    if not (head[:1] == b"\xff" or head[:8].strip() == b"0"):
        return [], [Item(rel, "header", "unreadable", "not an EDF/BDF header")]
    patient = head[8:88].decode("latin-1").strip()
    recording = head[88:168].decode("latin-1").strip()
    reserved = head[192:236].decode("latin-1").strip()
    label = subject_label(path)
    found: list[Item] = []
    if reserved.startswith(("EDF+", "BDF+")):
        sub = patient.split()
        code, _sex, birth, name = (sub + ["X"] * 4)[:4]
        if code.upper() != "X" and not is_pseudonym(code, label):
            found.append(Item(rel, "patient", "patient-code",
                              "patient code is not the BIDS subject label - verify it is not a hospital or study ID"))
        if birth.upper() != "X":
            found.append(Item(rel, "patient", "birthdate"))
        if name.upper() != "X":
            found.append(Item(rel, "patient", "name"))
        if len(sub) > 4:
            found.append(Item(rel, "patient", "free-text", "additional patient subfields"))
        rsub = recording.split()
        if rsub[:1] == ["Startdate"] and len(rsub) > 2 and rsub[2].upper() != "X":
            found.append(Item(rel, "recording", "admin-code", "hospital administration code is filled"))
    elif patient and patient.upper() != "X" and not is_pseudonym(patient, label):
        found.append(Item(rel, "patient", "free-text", "plain EDF patient field holds text - check it"))
    found += text_findings(rel, "patient", patient, scanner)
    found += text_findings(rel, "recording", recording, scanner)
    return found, []


def _ini_pointer_findings(path: Path, rel: str, text: str) -> list[Item]:
    found = []
    for key in ("DataFile", "MarkerFile"):
        m = re.search(rf"(?im)^\s*{key}\s*=\s*(.+?)\s*$", text)
        if m:
            target = Path(m.group(1).replace("\\", "/")).stem
            if target and target != path.stem:
                found.append(Item(rel, key, "file-pointer",
                                  "names a different file (often the original name; renaming without updating it also breaks loading)"))
    return found


def scan_brainvision(path: Path, rel: str, scanner) -> tuple[list[Item], list[Item]]:
    text = path.read_bytes().decode("utf-8", errors="replace")
    found = _ini_pointer_findings(path, rel, text)
    found += text_findings(rel, "text", text, scanner)
    return found, []


def _read_nifti(path: Path) -> bytes:
    opener = gzip.open if path.name.lower().endswith(".gz") else open
    with opener(path, "rb") as fh:
        head = fh.read(544)
        if len(head) < 348:
            return head
        sizeof = struct.unpack("<i", head[:4])[0]
        endian = "<" if sizeof in (348, 540) else ">"
        sizeof = struct.unpack(endian + "i", head[:4])[0]
        if sizeof == 348:
            vox = struct.unpack(endian + "f", head[108:112])[0]
        elif sizeof == 540:
            vox = struct.unpack(endian + "q", head[168:176])[0]
        else:
            return head
        want = int(vox) if vox == vox and 0 < vox < MAX_HEADER_BYTES else len(head)
        if want > len(head):
            head += fh.read(want - len(head))
        return head


def scan_nifti(path: Path, rel: str, scanner) -> tuple[list[Item], list[Item]]:
    head = _read_nifti(path)
    if len(head) < 348:
        return [], [Item(rel, "header", "unreadable", "shorter than a NIfTI header")]
    endian = "<" if struct.unpack("<i", head[:4])[0] in (348, 540) else ">"
    sizeof = struct.unpack(endian + "i", head[:4])[0]
    if sizeof == 348:
        descrip, aux, ext_at = head[148:228], head[228:252], 348
    elif sizeof == 540 and len(head) >= 540:
        descrip, aux, ext_at = head[240:320], head[320:344], 540
    else:
        return [], [Item(rel, "header", "unreadable", "not a NIfTI-1/2 header")]
    found: list[Item] = []
    for field, raw in (("descrip", descrip), ("aux_file", aux)):
        found += text_findings(rel, field, raw.split(b"\0")[0].decode("latin-1"), scanner)
    notes: list[Item] = []
    if len(head) >= ext_at + 4 and head[ext_at] != 0:
        pos = ext_at + 4
        while pos + 8 <= len(head):
            esize, ecode = struct.unpack(endian + "ii", head[pos : pos + 8])
            if esize < 8:
                break
            data = head[pos + 8 : pos + esize]
            if ecode == 2:
                found.append(Item(rel, "extension", "dicom-extension",
                                  "DICOM header extension can hold patient name, birth date and IDs"))
            elif ecode == 6:
                text = data.split(b"\0")[0].decode("utf-8", errors="replace")
                found += text_findings(rel, "comment-extension", text, scanner)
            else:
                notes.append(Item(rel, "extension", "header-extension", f"extension code {ecode} - check its content"))
            pos += esize
    return found, notes


def scan_participants(path: Path, rel: str, scanner, extra_columns: set[str]) -> tuple[list[Item], list[Item]]:
    text = path.read_bytes().decode("utf-8-sig", errors="replace")
    lines = text.splitlines()
    if not lines:
        return [], []
    header = [c.strip() for c in lines[0].split("\t")]
    normed = [re.sub(r"[\s-]+", "_", c.lower()) for c in header]
    found: list[Item] = []
    for col, norm in zip(header, normed):
        if norm in IDENTIFYING_COLUMNS or norm in extra_columns:
            found.append(Item(rel, f"column {col}", "identifying-column"))
    if "participant_id" in normed:
        i = normed.index("participant_id")
        rows = [r.split("\t") for r in lines[1:] if r.strip()]
        bad = sum(1 for r in rows if len(r) > i and not r[i].strip().startswith("sub-"))
        if bad:
            found.append(Item(rel, "participant_id", "not-pseudonym", f"{bad} rows are not sub-<label>"))
    found += text_findings(rel, "table", text, scanner)
    return found, []


def scan_fif(path: Path, rel: str, scanner) -> tuple[list[Item], list[Item], list[Item]]:
    mne = _import_mne()
    if mne is None:
        return [], [], [Item(rel, "header", "not-scanned",
                             "MNE is not installed - pip install mne, or check with mne.io.anonymize")]
    try:
        info = mne.io.read_info(str(path), verbose="error")
    except Exception as e:  # MNE raises many types for bad files
        return [], [], [Item(rel, "header", "not-scanned", f"MNE could not read it: {type(e).__name__}")]
    found: list[Item] = []
    subject = info.get("subject_info") or {}
    for key, kind in (("his_id", "hospital-id"), ("last_name", "name"), ("first_name", "name"),
                      ("middle_name", "name"), ("birthday", "birthdate")):
        if subject.get(key):
            found.append(Item(rel, f"subject_info.{key}", kind))
    notes = [Item(rel, "experimenter", "staff-name", "experimenter field is filled")] if info.get("experimenter") else []
    found += text_findings(rel, "description", str(info.get("description") or ""), scanner)
    return found, notes, []


# ---------------------------------------------------------------------------
# Walk and report
# ---------------------------------------------------------------------------


def iter_files(paths: list[Path]):
    for p in paths:
        if p.is_file() or (p.is_symlink() and not p.exists()):
            yield p
            continue
        for dirpath, dirnames, filenames in os.walk(p):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for f in sorted(filenames):
                yield Path(dirpath) / f


def scan(paths: list[Path], scanner, extra_columns: set[str], base: Path) -> dict:
    findings: list[Item] = []
    notes: list[Item] = []
    not_scanned: list[Item] = []
    other: dict[str, int] = {}
    checked = 0
    for path in iter_files(paths):
        try:
            rel = path.resolve().relative_to(base).as_posix()
        except ValueError:
            rel = path.as_posix()
        suffix = suffix_of(path)
        kind = None
        if path.name == "participants.tsv":
            kind = "participants"
        elif suffix in (".edf", ".bdf"):
            kind = "edf"
        elif suffix in (".vhdr", ".vmrk"):
            kind = "brainvision"
        elif suffix in (".nii", ".nii.gz"):
            kind = "nifti"
        elif suffix in (".fif", ".fif.gz"):
            kind = "fif"
        elif suffix in OTHER_FORMATS:
            other[suffix] = other.get(suffix, 0) + 1
            continue
        else:
            continue
        if not path.exists():
            not_scanned.append(Item(rel, "file", "not-scanned", "content not present (broken link or annexed file)"))
            continue
        checked += 1
        try:
            if kind == "edf":
                f, n = scan_edf(path, rel, scanner)
            elif kind == "brainvision":
                f, n = scan_brainvision(path, rel, scanner)
            elif kind == "nifti":
                f, n = scan_nifti(path, rel, scanner)
            elif kind == "participants":
                f, n = scan_participants(path, rel, scanner, extra_columns)
            else:
                f, n, ns = scan_fif(path, rel, scanner)
                not_scanned += ns
        except (OSError, EOFError, struct.error, gzip.BadGzipFile) as e:
            not_scanned.append(Item(rel, "file", "not-scanned", f"unreadable: {type(e).__name__}"))
            continue
        for item in n:
            (not_scanned if item.kind == "unreadable" else notes).append(item)
        findings += f
    return {
        "checked": checked,
        "findings": [asdict(i) for i in findings],
        "not_scanned": [asdict(i) for i in not_scanned],
        "notes": [asdict(i) for i in notes],
        "other_formats": dict(sorted(other.items())),
    }


def print_human(rep: dict) -> None:
    print(f"Header scan - {rep['checked']} files checked: {len(rep['findings'])} findings, "
          f"{len(rep['not_scanned'])} not scanned (values are never shown)")
    for title, key in (("FINDINGS", "findings"), ("NOT SCANNED", "not_scanned"), ("NOTES", "notes")):
        if rep[key]:
            print(f"\n{title}")
            for i in rep[key]:
                extra = f" - {i['detail']}" if i["detail"] else ""
                print(f"  {i['path']}  {i['field']}: {i['kind']}{extra}")
    if rep["other_formats"]:
        listed = ", ".join(f"{k} ({v})" for k, v in rep["other_formats"].items())
        print(f"\nOther formats, not covered by this scan: {listed}")


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(errors="backslashreplace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="De-identification scan of recording headers.")
    ap.add_argument("paths", nargs="*", help="files or folders (default: current folder)")
    ap.add_argument("--config", help="pii_scan.py config (id_patterns, allow_emails, identifying_columns)")
    ap.add_argument("--roster", help="salted-hash roster from pii_scan.py --build-roster")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)
    pii = _pii()
    try:
        config = pii.load_config(Path(args.config).expanduser() if args.config else None)
        scanner = pii.scanner_from_args(config, args.roster, [], None, secrets=False)
        extra = {re.sub(r"[\s-]+", "_", str(c).lower()) for c in config.get("identifying_columns", []) or []}
        paths = [Path(p).expanduser() for p in args.paths] or [Path(".")]
        for p in paths:
            if not p.exists() and not p.is_symlink():
                raise ScanError(f"no such path: {p}")
        rep = scan(paths, scanner, extra, Path(".").resolve())
    except (pii.ConfigError, ScanError) as e:
        if args.json:
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            print(f"header_scan: {e}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(rep, indent=2))
    else:
        print_human(rep)
    return 1 if rep["findings"] or rep["not_scanned"] else 0


if __name__ == "__main__":
    sys.exit(main())
