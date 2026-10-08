#!/usr/bin/env python3
"""nf_provenance.py - provenance written by the pipeline itself: environment.md plus one JSON run record per run.

Part of the neuroflow `phase-data-analyze` skill; /data-preprocess and /brain-run use it too.

As a library - copy this file once next to the pipeline scripts that use it (for example
scripts/analysis/nf_provenance.py) and commit it, so HPC jobs and collaborators have it:

    import nf_provenance
    run = nf_provenance.start(inputs=["derivatives/preprocessing/"], seeds={"permutations": 42})
    ...                                   # analysis; use run.seeds["permutations"] where the seed is needed
    run.finish(outputs=["results/erp_stats.csv", "figures/erp.png"])

or as a context manager (records status "error" and re-raises when the script fails):

    with nf_provenance.start(inputs=["derivatives/preprocessing/"]) as run:
        rng = numpy.random.default_rng(run.seed("bootstrap", 7))
        ...
        run.output("results/erp_stats.csv")

Every finish writes, next to the calling script:
  environment.md                      one block per script, replaced on that script's next run: Python, OS,
                                      versions of the imported packages, seeds, git commit + dirty flag, job id
  provenance/<UTC time>_<script>.json  argv, inputs and outputs with sha256, timestamps, status, environment

A run that ends without finish() (crash, sys.exit) is still recorded at interpreter exit, with status
"error" or "unknown". Seeds are recorded only when the script declares them - an environment variable
does not seed numpy, scikit-learn or MNE.

As a command-line tool:
    python nf_provenance.py env [--packages] [--json]     what this interpreter would record
    python nf_provenance.py record [--input P] [--output P] [--dir D] -- Rscript scripts/analysis/stats.R
                                                          run record around any command (R, MATLAB, shell)
    python nf_provenance.py verify scripts/analysis/provenance/<record>.json
                                                          do the recorded outputs still match their hashes?

Exit codes (CLI): 0 = ok / outputs match; 1 = the wrapped command failed, or outputs changed or are
missing; 2 = usage or runtime error.
Stdlib only, Python 3.10+.
"""

from __future__ import annotations

import argparse
import atexit
import hashlib
import json
import os
import platform
import random
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

__version__ = "1"
RECORD_VERSION = 1
BEGIN = "<!-- nf-provenance:begin {name} -->"
END = "<!-- nf-provenance:end {name} -->"
ENV_HEADER = (
    "# Environment\n\n"
    "Written by nf_provenance.py each time a pipeline script finishes - one block per script, replaced on "
    "that script's next run. Run records with input and output hashes are in `provenance/`. "
    "Do not edit the blocks by hand.\n"
)
_ACTIVE: list["Run"] = []
_HOOK_INSTALLED = False


# ------------------------------------------------------------------ helpers

def _utc(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stamp(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _home_short(text: str) -> str:
    """Replace the home folder prefix with ~ so records and environment.md do not carry user names."""
    home = Path.home().as_posix().rstrip("/")
    norm = text.replace("\\", "/")
    if len(home) > 3:
        same = norm.lower().startswith(home.lower()) if os.name == "nt" else norm.startswith(home)
        if same and (len(norm) == len(home) or norm[len(home)] == "/"):
            return "~" + norm[len(home):]
    return text


def _git(args: list[str], cwd: Path) -> tuple[int, str]:
    try:
        out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=20, check=False)
    except (OSError, subprocess.SubprocessError) as e:
        return 127, str(e)
    return out.returncode, out.stdout.strip()


def project_root(start: Path) -> Path:
    code, top = _git(["rev-parse", "--show-toplevel"], start)
    return Path(top) if code == 0 and top else start


def rel_path(path: Path, root: Path) -> str:
    p = Path(path).expanduser().resolve()
    try:
        return p.relative_to(root.resolve()).as_posix()
    except ValueError:
        return _home_short(p.as_posix())


def git_state(cwd: Path) -> dict:
    code, commit = _git(["rev-parse", "HEAD"], cwd)
    if code != 0:
        return {"commit": None, "note": "not a git repository, or git is not installed"}
    _, branch = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd)
    _, status = _git(["status", "--porcelain", "--untracked-files=no"], cwd)
    changed = [ln[3:] for ln in status.splitlines() if ln.strip()]
    return {"commit": commit, "branch": branch or None, "dirty": bool(changed),
            "modified": changed[:20], "modified_count": len(changed)}


def job_info() -> dict | None:
    env = os.environ
    if env.get("SLURM_JOB_ID"):
        info = {"scheduler": "slurm", "id": env["SLURM_JOB_ID"]}
        if env.get("SLURM_ARRAY_TASK_ID"):
            info["array_task"] = env["SLURM_ARRAY_TASK_ID"]
        return info
    if env.get("PBS_JOBID"):
        info = {"scheduler": "pbs", "id": env["PBS_JOBID"]}
        if env.get("PBS_ARRAY_INDEX"):
            info["array_task"] = env["PBS_ARRAY_INDEX"]
        return info
    return None


def python_info() -> dict:
    return {"version": platform.python_version(), "implementation": platform.python_implementation(),
            "executable": _home_short(Path(sys.executable).as_posix())}


def os_info() -> dict:
    return {"platform": platform.platform(), "machine": platform.machine()}


def imported_packages() -> dict:
    """Versions of the third-party distributions whose modules this process has imported."""
    import importlib.metadata as md

    stdlib = set(getattr(sys, "stdlib_module_names", ()))
    top = {n.split(".")[0] for n in list(sys.modules) if n and not n.startswith("_")}
    top -= stdlib | {"__main__", "nf_provenance"}
    try:
        mapping = md.packages_distributions()
    except Exception:  # broken metadata must never break the analysis
        return {}
    found = {}
    for mod in sorted(top):
        for dist in mapping.get(mod, []):
            try:
                found[dist] = md.version(dist)
            except Exception:
                continue
    return dict(sorted(found.items(), key=lambda kv: kv[0].lower()))


def installed_packages() -> dict:
    import importlib.metadata as md

    found = {}
    for dist in md.distributions():
        name = dist.metadata.get("Name") if dist.metadata else None
        if name:
            found[name] = dist.version
    return dict(sorted(found.items(), key=lambda kv: kv[0].lower()))


def _cache_file() -> Path:
    if os.environ.get("NF_PROVENANCE_CACHE"):
        return Path(os.environ["NF_PROVENANCE_CACHE"])
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return base / "neuroflow" / "hashcache.json"


class HashCache:
    """sha256 by (path, size, mtime) - outside the project, so it never shows up in git."""

    def __init__(self, path: Path | None = None):
        self.path = path or _cache_file()
        self.data: dict = {}
        self.dirty = False
        try:
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.data = {}

    def get(self, p: Path, st: os.stat_result) -> str | None:
        hit = self.data.get(str(p))
        if hit and hit.get("size") == st.st_size and hit.get("mtime_ns") == st.st_mtime_ns:
            return hit.get("sha256")
        return None

    def put(self, p: Path, st: os.stat_result, sha: str) -> None:
        self.data[str(p)] = {"size": st.st_size, "mtime_ns": st.st_mtime_ns, "sha256": sha}
        self.dirty = True

    def save(self) -> None:
        if not self.dirty:
            return
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            _atomic_write(self.path, json.dumps(self.data))
        except OSError:
            pass


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _hash_file(p: Path, cache: HashCache | None) -> str:
    st = p.stat()
    if cache is not None:
        hit = cache.get(p.resolve(), st)
        if hit:
            return hit
    sha = _sha256_file(p)
    if cache is not None:
        cache.put(p.resolve(), st, sha)
    return sha


def hash_path(path: Path, cache: HashCache | None = None) -> dict:
    """{"sha256", "bytes"} for a file; a combined hash over sorted (relative path, sha256) for a folder."""
    p = Path(path).expanduser()
    if not p.exists():
        return {"missing": True}
    if p.is_file():
        return {"sha256": _hash_file(p, cache), "bytes": p.stat().st_size}
    h = hashlib.sha256()
    total, count = 0, 0
    for f in sorted(x for x in p.rglob("*") if x.is_file()):
        rel = f.relative_to(p).as_posix()
        h.update(f"{rel}\0{_hash_file(f, cache)}\n".encode("utf-8"))
        total += f.stat().st_size
        count += 1
    return {"sha256": h.hexdigest(), "bytes": total, "files": count, "kind": "folder"}


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".nfprov-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _env_block(name: str, rec: dict, record_link: str) -> str:
    git = rec.get("git") or {}
    if git.get("commit"):
        dirty = (f"dirty: {git.get('modified_count', 0)} tracked file(s) modified" if git.get("dirty") else "clean")
        git_txt = f"{git['commit'][:12]} on {git.get('branch') or '?'} - {dirty}"
    else:
        git_txt = git.get("note", "unknown")
    seeds = ", ".join(f"{k}={v}" for k, v in (rec.get("seeds") or {}).items()) or "none declared"
    job = rec.get("job")
    job_txt = f"{job['scheduler']} {job['id']}" if job else "none (interactive or local)"
    py = rec.get("python")
    py_txt = (f"{py.get('version')} ({py.get('implementation')}) `{py.get('executable')}`" if py
              else "not captured - the command is not this Python process")
    lines = [
        BEGIN.format(name=name),
        f"## {name}",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Status | {rec['status']} - finished {rec['finished_at']}, {rec['duration_s']} s |",
        f"| Run record | `{record_link}` |",
        f"| Python | {py_txt} |",
        f"| OS | {(rec.get('os') or {}).get('platform')} |",
        f"| Git | {git_txt} |",
        f"| Seeds | {seeds} |",
        f"| Job | {job_txt} |",
        "",
    ]
    packages = rec.get("packages")
    if packages:
        lines += ["| Package | Version |", "|---|---|"] + [f"| {k} | {v} |" for k, v in packages.items()]
    elif packages is None:
        lines.append(f"Packages: {rec.get('packages_note', 'not captured')}")
    else:
        lines.append("Packages: no third-party packages imported")
    lines.append(END.format(name=name))
    return "\n".join(lines)


def write_env_block(env_file: Path, name: str, block: str) -> None:
    begin, end = BEGIN.format(name=name), END.format(name=name)
    text = env_file.read_text(encoding="utf-8") if env_file.exists() else ENV_HEADER
    i, j = text.find(begin), text.find(end)
    if i != -1 and j > i:
        text = text[:i] + block + text[j + len(end):]
    else:
        text = text.rstrip("\n") + "\n\n" + block + "\n"
    if not text.endswith("\n"):
        text += "\n"
    _atomic_write(env_file, text)


def write_record(record_dir: Path, name: str, started: float, rec: dict) -> Path:
    record_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{_stamp(started)}_{Path(name).stem or 'run'}"
    path = record_dir / f"{stem}.json"
    n = 2
    while path.exists():
        path = record_dir / f"{stem}-{n}.json"
        n += 1
    _atomic_write(path, json.dumps(rec, indent=2, default=str, ensure_ascii=False) + "\n")
    return path


def _detect_script() -> Path | None:
    main = sys.modules.get("__main__")
    f = getattr(main, "__file__", None)
    if "ipykernel" in sys.modules or not f:
        return None
    return Path(f).resolve()


def _install_hook() -> None:
    global _HOOK_INSTALLED
    if _HOOK_INSTALLED:
        return
    previous = sys.excepthook

    def hook(exc_type, exc, tb):
        for r in _ACTIVE:
            if not r._finished:
                r._exc = f"{exc_type.__name__}: {exc}"
        previous(exc_type, exc, tb)

    sys.excepthook = hook
    _HOOK_INSTALLED = True


# ------------------------------------------------------------------ the run object

class Run:
    """One execution of a pipeline script. Create it with start(); call finish() at the end."""

    def __init__(self, name: str | None = None, inputs=(), outputs=(), seeds: dict | None = None,
                 record_dir: str | os.PathLike | None = None, env_file: str | os.PathLike | None = None,
                 hash_files: bool = True, script: str | os.PathLike | None = None,
                 capture_packages: bool = True, detect_script: bool = True):
        self.started = time.time()
        self.script = Path(script).resolve() if script else (_detect_script() if detect_script else None)
        self.name = name or (self.script.name if self.script else "interactive")
        base = self.script.parent if self.script else Path.cwd()
        self.root = project_root(base)
        self.env_file = Path(env_file) if env_file else base / "environment.md"
        self.record_dir = Path(record_dir) if record_dir else base / "provenance"
        self.argv = [_home_short(a) for a in sys.argv]
        if self.script and self.argv:
            self.argv[0] = rel_path(self.script, self.root)
        self.cwd = rel_path(Path.cwd(), self.root)
        self.inputs = [Path(p) for p in inputs]
        self.outputs = [Path(p) for p in outputs]
        self.seeds = dict(seeds or {})
        self.notes: dict = {}
        self.git = git_state(base)
        self.hash_files = hash_files
        self.capture_packages = capture_packages
        self.record_path: Path | None = None
        self.extra: dict = {}
        self._finished = False
        self._exc: str | None = None
        _ACTIVE.append(self)
        _install_hook()
        atexit.register(self._at_exit)

    def input(self, *paths) -> "Run":
        self.inputs += [Path(p) for p in paths]
        return self

    def output(self, *paths) -> "Run":
        self.outputs += [Path(p) for p in paths]
        return self

    def seed(self, name: str, value):
        """Record a seed the script uses and return it: rng = default_rng(run.seed("cv", 7))."""
        self.seeds[name] = value
        return value

    def set_global_seed(self, value: int) -> int:
        """Seed Python's random module and numpy's legacy global generator (if numpy is installed)."""
        random.seed(value)
        self.seeds["random"] = value
        try:
            import numpy  # noqa: PLC0415 - optional

            numpy.random.seed(value)
            self.seeds["numpy.random (global)"] = value
        except ImportError:
            pass
        return value

    def note(self, key: str, value) -> "Run":
        self.notes[key] = value
        return self

    def _entries(self, paths: list[Path], cache: HashCache | None) -> list[dict]:
        out = []
        for p in paths:
            entry = {"path": rel_path(p, self.root)}
            try:
                entry.update(hash_path(p, cache) if self.hash_files else ({} if p.exists() else {"missing": True}))
            except OSError as e:
                entry["error"] = f"{type(e).__name__}: {e}"
            out.append(entry)
        return out

    def finish(self, outputs=(), status: str = "ok", error: str | None = None) -> Path | None:
        """Hash inputs/outputs, write the run record and the environment.md block. Never raises."""
        if self._finished:
            return self.record_path
        self._finished = True
        self.outputs += [Path(p) for p in outputs]
        ended = time.time()
        try:
            cache = HashCache() if self.hash_files else None
            rec = {
                "nf_provenance": RECORD_VERSION,
                "name": self.name,
                "script": rel_path(self.script, self.root) if self.script else None,
                "argv": self.argv,
                "cwd": self.cwd,
                "started_at": _utc(self.started),
                "finished_at": _utc(ended),
                "duration_s": round(ended - self.started, 3),
                "status": status,
                "error": error,
                "python": python_info(),
                "os": os_info(),
                "git": self.git,
                "job": job_info(),
                "seeds": self.seeds,
                "notes": self.notes,
                "packages": imported_packages() if self.capture_packages else None,
                "inputs": self._entries(self.inputs, cache),
                "outputs": self._entries(self.outputs, cache),
                "helper": {"nf_provenance": __version__},
            }
            rec.update(self.extra)
            missing = [o["path"] for o in rec["outputs"] if o.get("missing")]
            if missing and status == "ok":
                rec["warnings"] = [f"declared output not found: {m}" for m in missing]
            self.record_path = write_record(self.record_dir, self.name, self.started, rec)
            try:
                link = Path(os.path.relpath(self.record_path, self.env_file.parent)).as_posix()
            except ValueError:
                link = rel_path(self.record_path, self.root)
            write_env_block(self.env_file, self.name, _env_block(self.name, rec, link))
            if cache is not None:
                cache.save()
        except Exception as e:  # provenance must never take the analysis down
            print(f"nf_provenance: could not write provenance ({type(e).__name__}: {e})", file=sys.stderr)
        return self.record_path

    def _at_exit(self) -> None:
        if not self._finished:
            if self._exc:
                self.finish(status="error", error=self._exc)
            else:
                self.finish(status="unknown", error="finish() was not called before the interpreter exited")

    def __enter__(self) -> "Run":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is not None:
            self.finish(status="error", error=f"{exc_type.__name__}: {exc}")
        else:
            self.finish()
        return False


def start(inputs=(), outputs=(), seeds: dict | None = None, name: str | None = None, **kwargs) -> Run:
    """Begin recording this run. See the module docstring."""
    return Run(name=name, inputs=inputs, outputs=outputs, seeds=seeds, **kwargs)


# ------------------------------------------------------------------ CLI

def _cmd_env(args) -> int:
    root = project_root(Path.cwd())
    info = {"python": python_info(), "os": os_info(), "git": git_state(Path.cwd()), "job": job_info(),
            "project_root": _home_short(root.as_posix()), "helper": __version__}
    if args.packages:
        info["installed_packages"] = installed_packages()
    if args.json:
        print(json.dumps(info, indent=2))
        return 0
    py = info["python"]
    print(f"Python   {py['version']} ({py['implementation']}) {py['executable']}")
    print(f"OS       {info['os']['platform']}")
    g = info["git"]
    print(f"Git      {g['commit'][:12] + (' (dirty)' if g.get('dirty') else ' (clean)') if g.get('commit') else g.get('note')}")
    print(f"Job      {info['job']['scheduler'] + ' ' + info['job']['id'] if info['job'] else 'none'}")
    for k, v in (info.get("installed_packages") or {}).items():
        print(f"  {k}=={v}")
    return 0


def _cmd_record(args) -> int:
    cmd = list(args.command)
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        print("nf_provenance.py: error: give the command after --", file=sys.stderr)
        return 2
    script = next((Path(a) for a in cmd[1:] if Path(a).is_file()), None)
    base = Path(args.dir) if args.dir else (script.resolve().parent if script else Path.cwd())
    name = args.name or (script.name if script else Path(cmd[0]).name)
    run = Run(name=name, inputs=args.input or [], outputs=args.output or [], record_dir=base / "provenance",
              env_file=base / "environment.md", script=script, capture_packages=False, detect_script=False)
    run.argv = [_home_short(a) for a in cmd]
    run.extra = {"python": None,
                 "packages_note": "not captured - the command is not this Python process; record versions "
                                  "in the script itself (sessionInfo(), ver, pip freeze)"}
    try:
        code = subprocess.run(cmd, check=False).returncode
    except OSError as e:
        run._finished = True  # nothing ran - do not write a record
        print(f"nf_provenance.py: error: cannot start {cmd[0]}: {e}", file=sys.stderr)
        return 2
    run.extra["exit_code"] = code
    path = run.finish(status="ok" if code == 0 else "error",
                      error=None if code == 0 else f"command exited with {code}")
    if args.json:
        print(json.dumps({"exit_code": code, "record": str(path) if path else None}, indent=2))
    else:
        print(f"nf_provenance: exit code {code}; run record {path}")
    return 0 if code == 0 else 1


def _cmd_verify(args) -> int:
    try:
        rec = json.loads(Path(args.record).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"nf_provenance.py: error: cannot read {args.record}: {e}", file=sys.stderr)
        return 2
    root = Path(args.root) if args.root else project_root(Path.cwd())
    results = []
    for out in rec.get("outputs") or []:
        p = Path(out["path"]).expanduser()
        p = p if p.is_absolute() else root / p
        now = hash_path(p)
        if now.get("missing"):
            state = "missing"
        elif not out.get("sha256"):
            state = "not hashed in record"
        else:
            state = "match" if now.get("sha256") == out["sha256"] else "changed"
        results.append({"path": out["path"], "state": state})
    bad = [r for r in results if r["state"] in {"missing", "changed"}]
    if args.json:
        print(json.dumps({"record": args.record, "outputs": results, "problems": len(bad)}, indent=2))
    else:
        for r in results:
            print(f"{r['state']:>20}  {r['path']}")
        print(f"{len(results)} output(s), {len(bad)} changed or missing")
    return 1 if bad else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="nf_provenance.py",
                                description="Provenance for pipeline runs: environment.md and JSON run records (neuroflow).",
                                epilog="Exit codes: 0 = ok; 1 = command failed / outputs changed; 2 = usage or runtime error.")
    sub = p.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("env", help="show what this interpreter would record")
    e.add_argument("--packages", action="store_true", help="also list every installed distribution")
    e.add_argument("--json", action="store_true")
    r = sub.add_parser("record", help="run a command and write its run record")
    r.add_argument("--input", action="append", help="input file or folder to hash (repeatable)")
    r.add_argument("--output", action="append", help="output file or folder to hash (repeatable)")
    r.add_argument("--dir", help="folder for environment.md and provenance/ (default: the script's folder)")
    r.add_argument("--name", help="name of the block in environment.md (default: the script's file name)")
    r.add_argument("--json", action="store_true")
    r.add_argument("command", nargs=argparse.REMAINDER, help="-- command and its arguments")
    v = sub.add_parser("verify", help="re-hash the outputs listed in a run record")
    v.add_argument("record", help="run record JSON")
    v.add_argument("--root", help="project root the record's paths are relative to (default: git top level)")
    v.add_argument("--json", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "env":
        return _cmd_env(args)
    if args.cmd == "record":
        return _cmd_record(args)
    return _cmd_verify(args)


if __name__ == "__main__":
    sys.exit(main())
