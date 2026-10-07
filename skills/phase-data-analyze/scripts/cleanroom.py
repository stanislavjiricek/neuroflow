#!/usr/bin/env python3
"""cleanroom.py - clean-room reproduction: fresh clone, fresh environment, rerun the documented command,
compare the outputs with the originals.

Part of the neuroflow `phase-data-analyze` skill. It clones the project at the recorded commit into a
scratch folder, builds or picks the Python environment, links in the data that git does not hold,
reruns the command, and compares every declared output with the original: identical (same sha256),
within tolerance (JSON/CSV/TSV numbers within --rtol/--atol), different, or missing.

The command and outputs come from an nf_provenance run record (--record) or are given explicitly:

  python cleanroom.py --record scripts/analysis/provenance/20261007T120000Z_erp.json \
      --requirements requirements.txt --link data/bids --report .neuroflow/data-analyze/cleanroom-2026-10-07.md
  python cleanroom.py --current-python --output results/stats.json --link derivatives \
      -- python scripts/analysis/stats.py

Environment (exactly one): --requirements FILE (fresh venv + pip install -r FILE from the clone),
--python EXE (an environment you built, e.g. from a conda lock file), --current-python (this
interpreter: a clean checkout, but not a clean environment - the report says so).

Exit codes: 0 = command succeeded and every output is identical or within tolerance;
            1 = command failed, or an output is different or missing;
            2 = usage or setup error (clone, environment, data link).
Run it from the project root. Long reruns: start it in the background and register it in runs.md.
Stdlib only, Python 3.10+.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

PY_NAMES = {"python", "python3", "python.exe", "python3.exe", "py", "py.exe"}


class SetupError(Exception):
    """Usage or setup problem (exit 2)."""


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(args: list[str], cwd: Path, check: bool = True) -> str:
    try:
        out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=600, check=False)
    except (OSError, subprocess.SubprocessError) as e:
        raise SetupError(f"git {' '.join(args)} failed: {e}")
    if check and out.returncode != 0:
        raise SetupError(f"git {' '.join(args)} failed: {out.stderr.strip() or out.stdout.strip()}")
    return out.stdout.strip()


# ------------------------------------------------------------------ comparison

def _close(a: float, b: float, rtol: float, atol: float) -> bool:
    if math.isnan(a) and math.isnan(b):
        return True
    return abs(a - b) <= atol + rtol * abs(b)


def _num(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    return None


def compare_json(a, b, rtol, atol, where="$") -> tuple[bool, float, str]:
    na, nb = _num(a), _num(b)
    if na is not None and nb is not None:
        diff = 0.0 if (math.isnan(na) and math.isnan(nb)) else abs(na - nb)
        return _close(na, nb, rtol, atol), diff, "" if _close(na, nb, rtol, atol) else f"{where}: {a} vs {b}"
    if type(a) is not type(b):
        return False, math.inf, f"{where}: type {type(a).__name__} vs {type(b).__name__}"
    if isinstance(a, dict):
        if set(a) != set(b):
            return False, math.inf, f"{where}: keys differ"
        worst, ok, first = 0.0, True, ""
        for k in a:
            o, d, msg = compare_json(a[k], b[k], rtol, atol, f"{where}.{k}")
            worst = max(worst, d)
            if not o and ok:
                ok, first = False, msg
        return ok, worst, first
    if isinstance(a, list):
        if len(a) != len(b):
            return False, math.inf, f"{where}: length {len(a)} vs {len(b)}"
        worst, ok, first = 0.0, True, ""
        for i, (x, y) in enumerate(zip(a, b)):
            o, d, msg = compare_json(x, y, rtol, atol, f"{where}[{i}]")
            worst = max(worst, d)
            if not o and ok:
                ok, first = False, msg
        return ok, worst, first
    return (a == b), (0.0 if a == b else math.inf), "" if a == b else f"{where}: {a!r} vs {b!r}"


def _float_or_none(text: str):
    try:
        return float(text)
    except ValueError:
        return None


def compare_table(a: Path, b: Path, rtol, atol) -> tuple[bool, float, str]:
    delim = "\t" if a.suffix.lower() == ".tsv" else ","
    with a.open(newline="", encoding="utf-8-sig") as fa, b.open(newline="", encoding="utf-8-sig") as fb:
        ra, rb = list(csv.reader(fa, delimiter=delim)), list(csv.reader(fb, delimiter=delim))
    if len(ra) != len(rb):
        return False, math.inf, f"{len(ra)} vs {len(rb)} rows"
    worst = 0.0
    for i, (x, y) in enumerate(zip(ra, rb), start=1):
        if len(x) != len(y):
            return False, math.inf, f"row {i}: {len(x)} vs {len(y)} columns"
        for j, (cx, cy) in enumerate(zip(x, y), start=1):
            fx, fy = _float_or_none(cx), _float_or_none(cy)
            if fx is not None and fy is not None:
                if not _close(fx, fy, rtol, atol):
                    return False, abs(fx - fy), f"row {i}, column {j}: {cx} vs {cy}"
                if not (math.isnan(fx) and math.isnan(fy)):
                    worst = max(worst, abs(fx - fy))
            elif cx != cy:
                return False, math.inf, f"row {i}, column {j}: {cx!r} vs {cy!r}"
    return True, worst, ""


def compare_tolerant(ref: Path, new: Path, rtol: float, atol: float) -> tuple[bool, float, str]:
    suffix = ref.suffix.lower()
    try:
        if suffix == ".json":
            return compare_json(json.loads(ref.read_text(encoding="utf-8")),
                                json.loads(new.read_text(encoding="utf-8")), rtol, atol)
        if suffix in {".csv", ".tsv"}:
            return compare_table(ref, new, rtol, atol)
    except (OSError, ValueError, UnicodeDecodeError) as e:
        return False, math.inf, f"could not parse for a tolerance check ({e})"
    return False, math.inf, "format is compared by hash only (use JSON/CSV/TSV for numbers that may drift)"


def compare_file(rel: str, ref: Path, new: Path, rec_sha: str | None, rtol, atol) -> dict:
    out = {"output": rel, "verdict": "", "detail": ""}
    if not new.exists():
        out.update(verdict="missing", detail="not produced in the clean room")
        return out
    new_sha = sha256(new)
    out["clean_sha256"] = new_sha
    ref_sha = rec_sha
    reference_ok = ref.is_file() and (rec_sha is None or sha256(ref) == rec_sha)
    if ref_sha is None:
        if not ref.is_file():
            out.update(verdict="no-reference", detail="no original file and no recorded hash")
            return out
        ref_sha = sha256(ref)
    out["reference_sha256"] = ref_sha
    if new_sha == ref_sha:
        out.update(verdict="identical")
        return out
    if not reference_ok:
        out.update(verdict="different", detail="hash differs; the original file changed since the record "
                                               "(or is gone), so no tolerance check was possible")
        return out
    ok, diff, msg = compare_tolerant(ref, new, rtol, atol)
    if ok:
        out.update(verdict="within-tolerance", detail=f"max abs difference {diff:.3g}")
    else:
        out.update(verdict="different", detail=msg)
    return out


def compare_output(rel: str, repo: Path, clone: Path, rec_sha: str | None, rtol, atol) -> list[dict]:
    ref, new = repo / rel, clone / rel
    if ref.is_dir() or new.is_dir():
        if not new.is_dir():
            return [{"output": rel, "verdict": "missing", "detail": "folder not produced in the clean room"}]
        if not ref.is_dir():
            return [{"output": rel, "verdict": "no-reference", "detail": "original folder not found"}]
        names = sorted({p.relative_to(ref).as_posix() for p in ref.rglob("*") if p.is_file()}
                       | {p.relative_to(new).as_posix() for p in new.rglob("*") if p.is_file()})
        results = []
        for n in names:
            r = compare_file(f"{rel.rstrip('/')}/{n}", ref / n, new / n, None, rtol, atol)
            if not (ref / n).exists():
                r.update(verdict="different", detail="extra file in the clean room")
            results.append(r)
        return results
    return [compare_file(rel, ref, new, rec_sha, rtol, atol)]


# ------------------------------------------------------------------ setup

def _rmtree(path: Path) -> None:
    """Remove the scratch clone; git object files are read-only on Windows."""
    def retry(func, p, _exc):
        try:
            os.chmod(p, stat.S_IWRITE)
            func(p)
        except OSError:
            pass
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=retry)
    else:
        shutil.rmtree(path, onerror=retry)


def venv_python(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def build_env(args, clone: Path, workdir: Path) -> tuple[str, str, dict]:
    env = dict(os.environ)
    if args.python:
        exe = shutil.which(args.python) or args.python
        if not Path(exe).exists():
            raise SetupError(f"--python {args.python} not found")
        return exe, f"given interpreter {args.python}", env
    if args.current_python:
        return sys.executable, "current interpreter (clean checkout, NOT a rebuilt environment)", env
    req = clone / args.requirements
    if not req.is_file():
        raise SetupError(f"--requirements {args.requirements} is not in the clean checkout")
    venv = workdir / "venv"
    out = subprocess.run([sys.executable, "-m", "venv", str(venv)], capture_output=True, text=True, check=False)
    if out.returncode != 0:
        raise SetupError(f"venv creation failed: {out.stderr.strip()}")
    py = venv_python(venv)
    out = subprocess.run([str(py), "-m", "pip", "install", "--quiet", "-r", str(req)],
                         capture_output=True, text=True, check=False)
    if out.returncode != 0:
        raise SetupError(f"pip install -r {args.requirements} failed:\n{out.stderr.strip()[-2000:]}")
    env["VIRTUAL_ENV"] = str(venv)
    env["PATH"] = str(py.parent) + os.pathsep + env.get("PATH", "")
    return str(py), f"fresh venv from {args.requirements}", env


def link_data(repo: Path, clone: Path, rel: str, copy: bool, links: list[Path]) -> str:
    """Make untracked data visible in the clone. Links are recorded in `links` and removed after the run."""
    src, dst = repo / rel, clone / rel
    if not src.exists():
        raise SetupError(f"{rel} does not exist in the project")
    if dst.exists():
        raise SetupError(f"{rel} is already in the clean checkout (tracked by git) - no need to link it")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if copy:
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        return "copied"
    try:
        os.symlink(src.resolve(), dst, target_is_directory=src.is_dir())
        links.append(dst)
        return "linked"
    except OSError as e:
        if os.name == "nt" and src.is_dir():
            out = subprocess.run(["cmd", "/c", "mklink", "/J", str(dst), str(src.resolve())],
                                 capture_output=True, text=True, check=False)
            if out.returncode == 0:
                links.append(dst)
                return "linked (junction)"
        raise SetupError(f"cannot link {rel} ({e}); enable symlinks or use --copy {rel}")


def remove_links(links: list[Path]) -> None:
    """Remove the links themselves - never the data they point to."""
    for p in links:
        try:
            if os.name == "nt":
                try:
                    os.rmdir(p)  # directory symlink or junction: removes the link only
                except OSError:
                    os.unlink(p)  # file symlink
            else:
                os.unlink(p)
        except OSError:
            pass


def resolve_command(args, record: dict | None, clone: Path, py: str) -> tuple[list[str], Path]:
    cmd = list(args.command or [])
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if cmd:
        if Path(cmd[0]).name.lower() in PY_NAMES:
            cmd[0] = py
        return cmd, clone
    if not record:
        raise SetupError("give the command after --, or a run record with --record")
    if not record.get("script"):
        raise SetupError("the run record has no script; give the command after --")
    cwd = clone / (record.get("cwd") or ".")
    argv = list(record.get("argv") or [record["script"]])
    return [py, str(clone / record["script"])] + argv[1:], cwd


# ------------------------------------------------------------------ report

def render(report: dict) -> str:
    lines = [
        f"# Clean-room reproduction - {report['finished_at'][:10]}",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Commit | `{report['commit'][:12]}` |",
        f"| Command | `{' '.join(report['command_display'])}` |",
        f"| Environment | {report['environment']} |",
        f"| Data | {', '.join(report['data']) or 'none linked'} |",
        f"| Exit code | {report['exit_code']} |",
        f"| Duration | {report['duration_s']} s |",
        f"| Verdict | **{report['verdict']}** |",
        "",
        "| Output | Verdict | Detail |",
        "|---|---|---|",
    ]
    for r in report["outputs"]:
        lines.append(f"| `{r['output']}` | {r['verdict']} | {r.get('detail', '').replace('|', '/')} |")
    lines += ["", "Notes:"]
    for n in report["notes"]:
        lines.append(f"- {n}")
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cleanroom.py",
                                description="Clean-room reproduction: fresh clone + environment, rerun, compare outputs (neuroflow).",
                                epilog="Exit codes: 0 = reproduced; 1 = failed or different; 2 = usage or setup error.")
    env = p.add_mutually_exclusive_group(required=True)
    env.add_argument("--requirements", help="requirements file (path in the repo) for a fresh venv")
    env.add_argument("--python", help="interpreter of an environment you built (e.g. from a lock file)")
    env.add_argument("--current-python", action="store_true", help="use this interpreter (environment not rebuilt)")
    p.add_argument("--record", help="nf_provenance run record: command, commit and outputs come from it")
    p.add_argument("--repo", help="project repository (default: git top level of the current folder)")
    p.add_argument("--ref", help="commit to reproduce (default: the record's commit, else HEAD)")
    p.add_argument("--output", action="append", help="output path to compare, relative to the repo (repeatable)")
    p.add_argument("--link", action="append", default=[], help="untracked data path to link into the clone (repeatable)")
    p.add_argument("--copy", action="append", default=[], help="untracked data path to copy into the clone (repeatable)")
    p.add_argument("--rtol", type=float, default=1e-6, help="relative tolerance for numbers (default 1e-6)")
    p.add_argument("--atol", type=float, default=1e-9, help="absolute tolerance for numbers (default 1e-9)")
    p.add_argument("--timeout", type=float, default=None, help="seconds before the rerun is stopped")
    p.add_argument("--workdir", help="scratch folder (default: a new temporary folder)")
    p.add_argument("--keep", action="store_true", help="keep the scratch folder even when everything matches")
    p.add_argument("--report", help="write the markdown report here, e.g. .neuroflow/data-analyze/cleanroom-<date>.md")
    p.add_argument("--json", action="store_true", help="print JSON")
    p.add_argument("command", nargs=argparse.REMAINDER, help="-- command to rerun (if no --record)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    workdir: Path | None = None
    links: list[Path] = []
    try:
        record = None
        if args.record:
            try:
                record = json.loads(Path(args.record).read_text(encoding="utf-8"))
            except (OSError, ValueError) as e:
                raise SetupError(f"cannot read run record {args.record}: {e}")
        repo = Path(args.repo).resolve() if args.repo else Path(git(["rev-parse", "--show-toplevel"], Path.cwd()))
        ref = args.ref or ((record or {}).get("git") or {}).get("commit") or "HEAD"
        commit = git(["rev-parse", "--verify", f"{ref}^{{commit}}"], repo)
        rec_hashes = {o["path"]: o.get("sha256") for o in (record or {}).get("outputs") or [] if "path" in o}
        outputs = [Path(o).as_posix() for o in args.output] if args.output else list(rec_hashes)
        if not outputs:
            raise SetupError("nothing to compare: give --output (or a run record that lists outputs)")
        for linked in args.link:
            lk = Path(linked).as_posix().rstrip("/")
            for o in outputs:
                if o == lk or o.startswith(lk + "/"):
                    raise SetupError(f"output {o} is inside the linked folder {lk}: the rerun would write into the "
                                     f"original data - use --copy {lk}, or link a narrower input folder")
        workdir = Path(args.workdir) if args.workdir else Path(tempfile.mkdtemp(prefix="nf-cleanroom-"))
        workdir.mkdir(parents=True, exist_ok=True)
        clone = workdir / "repo"
        if clone.exists():
            raise SetupError(f"{clone} already exists - use an empty --workdir")
        git(["clone", "--quiet", "--no-checkout", str(repo), str(clone)], workdir)
        git(["checkout", "--quiet", "--detach", commit], clone)
        py, env_desc, env = build_env(args, clone, workdir)
        data = [f"{rel} ({link_data(repo, clone, Path(rel).as_posix(), False, links)})" for rel in args.link]
        data += [f"{rel} ({link_data(repo, clone, Path(rel).as_posix(), True, links)})" for rel in args.copy]
        cmd, cwd = resolve_command(args, record, clone, py)
    except SetupError as e:
        remove_links(links)
        print(f"cleanroom.py: error: {e}", file=sys.stderr)
        if workdir is not None:
            print(f"cleanroom.py: scratch folder kept for inspection: {workdir}", file=sys.stderr)
        return 2

    t0 = time.time()
    log = workdir / "cleanroom.log"
    with log.open("w", encoding="utf-8", errors="replace") as fh:
        try:
            code = subprocess.run(cmd, cwd=cwd, env=env, stdout=fh, stderr=subprocess.STDOUT,
                                  timeout=args.timeout, check=False).returncode
        except subprocess.TimeoutExpired:
            code = "timeout"
        except OSError as e:
            code = f"could not start: {e}"
    duration = round(time.time() - t0, 1)

    results = []
    for rel in outputs:
        results.extend(compare_output(rel, repo, clone, rec_hashes.get(rel), args.rtol, args.atol))
    remove_links(links)
    good = code == 0 and all(r["verdict"] in {"identical", "within-tolerance"} for r in results)
    notes = ["A match shows that the committed code and the declared environment reproduce these outputs; "
             "it does not show the analysis is correct."]
    if args.current_python:
        notes.append("Environment not rebuilt (--current-python): package drift is not tested.")
    if record and (record.get("git") or {}).get("dirty"):
        notes.append("The original run came from a working tree with uncommitted changes; those changes were not "
                     "in the clean room.")
    if any(r["verdict"] == "different" for r in results):
        notes.append("Differences can come from unseeded randomness, multithreaded BLAS, GPU kernels or package "
                     "versions - check the seeds in the run record before suspecting the analysis.")
    display = [Path(c).name if i == 0 else c for i, c in enumerate(cmd)]
    report = {
        "finished_at": now_utc(), "commit": commit, "command_display": display, "environment": env_desc,
        "data": data, "exit_code": code, "duration_s": duration,
        "verdict": "reproduced" if good else "NOT reproduced", "outputs": results, "notes": notes,
        "workdir": None,
    }
    if good and not args.keep:
        if args.workdir:  # a folder the person chose: remove only what cleanroom created in it
            for made in (workdir / "repo", workdir / "venv", workdir / "cleanroom.log"):
                if made.is_dir():
                    _rmtree(made)
                elif made.exists():
                    made.unlink()
        else:
            _rmtree(workdir)
    else:
        report["workdir"] = str(workdir)
        notes.append(f"Scratch folder kept: {workdir} (log: cleanroom.log)")
    md = render(report)
    if args.report:
        rp = Path(args.report)
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text(md, encoding="utf-8", newline="\n")
    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        sys.stdout.write(md)
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
