#!/usr/bin/env python3
"""runs.py - the long-run registry: .neuroflow/<phase>/runs.md, one row per long or detached run.

Part of the neuroflow `phase-brain-run` skill; /brain-optimize, /data-preprocess and /data-analyze use
it too (convention: the skill's references/long-runs.md).

  add    register a run you just launched (background, nohup / Start-Process, or an HPC job)
  list   show the registry (default: runs not yet reviewed)
  check  find out what finished: exit-code file, scheduler (squeue/sacct, qstat) or process id;
         updates Status and Note in place
  set    set a run's status by hand - e.g. "reviewed" once its outputs were inspected

Status values: queued, running, done, failed, cancelled, unknown, reviewed. A detached run writes its
exit code to <log>.exitcode when it ends (see long-runs.md) - that is how `check` knows a local run's
outcome. Scheduler state is read only where squeue/sacct or qstat exist (on the cluster).

Examples:
  python runs.py add --file .neuroflow/brain-run/runs.md --command "python models/run_sim.py --config run.yaml" \
      --log models/results/r1/run.log --output models/results/r1/metrics.json --pid 4242
  python runs.py add --file .neuroflow/brain-run/runs.md --command "sbatch job.sh" --where slurm --job-id 812345 \
      --output models/results/sweep/
  python runs.py check                      # every .neuroflow/*/runs.md under the current folder
  python runs.py set --file .neuroflow/brain-run/runs.md --id r-20261007-141200 --status reviewed

Exit codes: add/list/set: 0 = ok, 2 = usage error.
            check: 0 = nothing needs attention; 1 = a run finished, failed or is unknown and has not
            been reviewed yet; 2 = usage error.
Stdlib only, Python 3.10+.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

COLUMNS = ["Run", "Started (UTC)", "Where", "Command", "Log", "Expected outputs", "Status", "Note"]
STATUSES = {"queued", "running", "done", "failed", "cancelled", "unknown", "reviewed"}
OPEN = {"queued", "running", "unknown"}
ATTENTION = {"done", "failed", "unknown"}
HEADER = (
    "# Long runs\n\n"
    "> One row per long or detached run (background, nohup / Start-Process, or HPC job). `runs.py check` updates "
    "Status and Note; rows are never deleted. Status: queued, running, done, failed, cancelled, unknown, reviewed.\n\n"
    "| " + " | ".join(COLUMNS) + " |\n"
    "|" + "---|" * len(COLUMNS) + "\n"
)
_SPLIT = re.compile(r"(?<!\\)\|")


class RunsError(Exception):
    """Usage problem (exit 2)."""


# ------------------------------------------------------------------ table I/O

def esc(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip()


def code(text: str) -> str:
    return f"`{esc(text)}`" if text else ""


def unwrap(cell: str) -> str:
    cell = cell.strip().replace("\\|", "|")
    return cell[1:-1] if len(cell) >= 2 and cell.startswith("`") and cell.endswith("`") else cell


class Registry:
    def __init__(self, path: Path):
        self.path = path
        self.lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
        self.rows: dict[str, int] = {}
        start = next((i for i, ln in enumerate(self.lines) if ln.strip().startswith("| Run |")), None)
        if start is None:
            return
        for i in range(start + 2, len(self.lines)):
            ln = self.lines[i].strip()
            if not ln.startswith("|"):
                break
            cells = self.cells(i)
            if cells and cells[0]:
                self.rows[cells[0]] = i

    def cells(self, i: int) -> list[str]:
        parts = _SPLIT.split(self.lines[i].strip())
        return [p.strip() for p in parts[1:-1]]

    def run(self, run_id: str) -> dict:
        c = self.cells(self.rows[run_id]) + [""] * len(COLUMNS)
        return {"id": c[0], "started": c[1], "where": c[2], "command": unwrap(c[3]), "log": unwrap(c[4]),
                "outputs": [unwrap(o) for o in c[5].split(";") if o.strip()], "status": c[6], "note": c[7].replace("\\|", "|")}

    def all(self) -> list[dict]:
        return [self.run(r) for r in self.rows]

    def update(self, run_id: str, status: str, note: str) -> None:
        i = self.rows[run_id]
        c = (self.cells(i) + [""] * len(COLUMNS))[: len(COLUMNS)]
        c[6], c[7] = status, esc(note)
        self.lines[i] = "| " + " | ".join(c) + " |"

    def save(self) -> None:
        self.path.write_text("\n".join(self.lines) + "\n", encoding="utf-8", newline="\n")


def add_row(path: Path, cells: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        path.write_text(HEADER, encoding="utf-8", newline="\n")
    text = path.read_text(encoding="utf-8")
    if "| Run |" not in text:
        text = text.rstrip("\n") + "\n\n" + HEADER.split("\n\n", 2)[2]
    line = "| " + " | ".join(cells) + " |"
    lines = text.splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.strip().startswith("| Run |"))
    end = start + 2
    while end < len(lines) and lines[end].strip().startswith("|"):
        end += 1
    lines.insert(end, line)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


# ------------------------------------------------------------------ probes

def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return ctypes.get_last_error() == 5  # access denied: the process exists
        exit_code = ctypes.c_ulong()
        ok = kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
        kernel32.CloseHandle(handle)
        return bool(ok) and exit_code.value == 259  # STILL_ACTIVE
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _run(cmd: list[str]) -> tuple[int, str]:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
    except (OSError, subprocess.SubprocessError) as e:
        return 127, str(e)
    return out.returncode, (out.stdout or "") + (out.stderr or "")


def query_slurm(job_id: str) -> tuple[str | None, str]:
    if not shutil.which("squeue") and not shutil.which("sacct"):
        return None, "squeue/sacct not available here - run the check on the cluster"
    if shutil.which("squeue"):
        rc, out = _run(["squeue", "-h", "-j", job_id, "-o", "%T"])
        state = out.strip().splitlines()[0].strip().upper() if rc == 0 and out.strip() else ""
        if state in {"PENDING", "CONFIGURING", "REQUEUED", "RESV_DEL_HOLD", "REQUEUE_HOLD"}:
            return "queued", f"slurm {state.lower()}"
        if state in {"RUNNING", "COMPLETING", "SUSPENDED", "STAGE_OUT", "SIGNALING"}:
            return "running", f"slurm {state.lower()}"
    if shutil.which("sacct"):
        rc, out = _run(["sacct", "-j", job_id, "-n", "-X", "-P", "-o", "State,ExitCode"])
        line = out.strip().splitlines()[0] if rc == 0 and out.strip() else ""
        if line:
            state, _, exit_code = line.partition("|")
            state = state.split()[0].upper()
            if state == "COMPLETED":
                return "done", f"slurm completed, exit {exit_code}"
            if state.startswith("CANCELLED"):
                return "cancelled", "slurm cancelled"
            if state in {"FAILED", "TIMEOUT", "OUT_OF_MEMORY", "NODE_FAIL", "PREEMPTED", "BOOT_FAIL", "DEADLINE"}:
                return "failed", f"slurm {state.lower()}, exit {exit_code}"
            if state in {"PENDING", "REQUEUED"}:
                return "queued", f"slurm {state.lower()}"
            if state in {"RUNNING", "COMPLETING", "SUSPENDED"}:
                return "running", f"slurm {state.lower()}"
    return "unknown", "job not found in squeue or sacct"


def query_pbs(job_id: str) -> tuple[str | None, str]:
    if not shutil.which("qstat"):
        return None, "qstat not available here - run the check on the cluster"
    rc, out = _run(["qstat", "-x", "-f", job_id])
    if rc != 0 or "job_state" not in out.lower():
        rc, out = _run(["qstat", "-f", job_id])
    m = re.search(r"job_state\s*=\s*(\w)", out, re.IGNORECASE)
    if not m:
        return "unknown", "job not found by qstat (finished jobs may have left the history)"
    state = m.group(1).upper()
    ex = re.search(r"exit_status\s*=\s*(-?\d+)", out, re.IGNORECASE)
    if state in {"Q", "H", "W", "T"}:
        return "queued", f"pbs state {state}"
    if state in {"R", "E", "B", "S", "U"}:
        return "running", f"pbs state {state}"
    if state in {"F", "X", "C"}:
        if ex is None:
            return "unknown", f"pbs state {state}, no exit status"
        return ("done" if ex.group(1) == "0" else "failed"), f"pbs finished, exit {ex.group(1)}"
    return "unknown", f"pbs state {state}"


def probe(run: dict, base: Path) -> tuple[str | None, str]:
    """(new status or None for 'no change', note)."""
    log = run["log"]
    if log:
        exit_file = base / f"{log}.exitcode"
        if exit_file.is_file():
            raw = exit_file.read_text(encoding="utf-8", errors="replace").strip()
            try:
                value = int(raw.split()[0])
            except (ValueError, IndexError):
                return "unknown", f"unreadable exit-code file {exit_file.name}"
            return ("done" if value == 0 else "failed"), f"exit code {value}"
    where = run["where"].split()
    if where and where[0] == "slurm" and len(where) > 1:
        return query_slurm(where[1])
    if where and where[0] == "pbs" and len(where) > 1:
        return query_pbs(where[1])
    outputs = [base / o for o in run["outputs"]]
    have = bool(outputs) and all(p.exists() for p in outputs)
    if not outputs:
        out_txt = "no expected outputs registered"
    elif have:
        out_txt = "expected outputs present - inspect the log"
    else:
        out_txt = "expected outputs missing"
    if "pid" in where:
        idx = where.index("pid") + 1
        pid = int(where[idx]) if idx < len(where) and where[idx].isdigit() else -1
        if pid_alive(pid):
            return "running", f"process {pid} alive (a reused pid would also look alive)"
        return "unknown", f"process gone, no exit-code file; {out_txt}"
    if have:
        return "unknown", "expected outputs present, but no exit-code file - inspect the log"
    return None, "cannot tell - register runs with --pid, a job id, or an exit-code file"


# ------------------------------------------------------------------ commands

def registries(args) -> list[Path]:
    if getattr(args, "file", None):
        return [Path(f) for f in args.file]
    root = Path(args.root or ".")
    return sorted(root.glob(".neuroflow/*/runs.md"))


def cmd_add(args) -> int:
    path = Path(args.file)
    if args.job_id and args.where not in {"slurm", "pbs"}:
        raise RunsError("--job-id needs --where slurm or --where pbs")
    if args.where in {"slurm", "pbs"} and not args.job_id:
        raise RunsError(f"--where {args.where} needs --job-id")
    now = datetime.now(timezone.utc)
    reg = Registry(path)
    run_id = args.id or now.strftime("r-%Y%m%d-%H%M%S")
    base_id, n = run_id, 2
    while run_id in reg.rows:
        run_id = f"{base_id}-{n}"
        n += 1
    if args.where in {"slurm", "pbs"}:
        where, status = f"{args.where} {args.job_id}", "queued"
    else:
        where, status = ("local pid " + str(args.pid)) if args.pid else "local", "running"
    cells = [run_id, now.strftime("%Y-%m-%d %H:%M"), where, code(args.command), code(args.log or ""),
             "; ".join(code(o) for o in args.output or []), status, esc(args.note or "")]
    add_row(path, cells)
    if args.json:
        print(json.dumps({"id": run_id, "file": path.as_posix(), "status": status}, indent=2))
    else:
        print(f"registered {run_id} ({status}) in {path.as_posix()}")
    return 0


def cmd_list(args) -> int:
    out = []
    for path in registries(args):
        for run in Registry(path).all():
            if args.all or run["status"] not in {"reviewed", "cancelled"}:
                out.append({**run, "file": path.as_posix()})
    if args.json:
        print(json.dumps(out, indent=2))
    elif not out:
        print("no runs to show")
    else:
        for r in out:
            print(f"{r['id']}  {r['status']:<9} {r['where']:<18} {r['command']}  [{r['file']}]"
                  + (f"  - {r['note']}" if r["note"] else ""))
    return 0


def cmd_check(args) -> int:
    report, unchecked = [], []
    files = registries(args)
    for path in files:
        reg = Registry(path)
        base = Path(args.root or ".")
        changed = False
        for run in reg.all():
            if run["status"] in OPEN:
                new, note = probe(run, base)
                if new is not None and (new != run["status"] or note != run["note"]):
                    reg.update(run["id"], new, note)
                    changed = True
                    run = {**run, "status": new, "note": note}
                elif new is None:
                    unchecked.append({**run, "note": note, "file": path.as_posix()})
            if run["status"] in ATTENTION:
                report.append({**run, "file": path.as_posix()})
        if changed and not args.no_update:
            reg.save()
    if args.json:
        print(json.dumps({"registries": [p.as_posix() for p in files], "needs_attention": report,
                          "not_checked": unchecked}, indent=2))
    elif not files:
        print("no runs.md registries found")
    else:
        for r in report:
            print(f"{r['status'].upper():<8} {r['id']}  {r['command']}  - {r['note']}  [{r['file']}]")
        for r in unchecked:
            print(f"{r['status']:<8} {r['id']}  {r['command']}  - not checked: {r['note']}  [{r['file']}]")
        if report:
            print("Inspect these runs (log, outputs, sanity checks), summarize them, then: "
                  "runs.py set --file <runs.md> --id <run> --status reviewed")
        elif not unchecked:
            print("nothing finished that needs attention")
    return 1 if report else 0


def cmd_set(args) -> int:
    if args.status not in STATUSES:
        raise RunsError(f"status must be one of {', '.join(sorted(STATUSES))}")
    path = Path(args.file)
    reg = Registry(path)
    if args.id not in reg.rows:
        raise RunsError(f"run {args.id} not in {path.as_posix()}")
    note = args.note if args.note is not None else reg.run(args.id)["note"]
    reg.update(args.id, args.status, note)
    reg.save()
    if args.json:
        print(json.dumps({"id": args.id, "status": args.status}, indent=2))
    else:
        print(f"{args.id}: {args.status}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="runs.py", description="Long-run registry .neuroflow/<phase>/runs.md (neuroflow).",
                                epilog="Exit codes: 0 = ok / nothing needs attention; 1 = (check) runs need attention; 2 = usage error.")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add", help="register a launched run")
    a.add_argument("--file", required=True, help="registry, e.g. .neuroflow/brain-run/runs.md")
    a.add_argument("--command", required=True, help="the command that was launched")
    a.add_argument("--log", help="log file (its exit code goes to <log>.exitcode)")
    a.add_argument("--output", action="append", help="expected output path (repeatable)")
    a.add_argument("--where", choices=["local", "slurm", "pbs"], default="local")
    a.add_argument("--job-id", help="scheduler job id")
    a.add_argument("--pid", type=int, help="process id of a detached local run")
    a.add_argument("--id", help="run id (default r-<UTC date>-<time>)")
    a.add_argument("--note", help="short note")
    a.add_argument("--json", action="store_true")
    for name, helptext in (("list", "show registered runs"), ("check", "update open runs and report what needs attention")):
        s = sub.add_parser(name, help=helptext)
        s.add_argument("--file", action="append", help="registry file (repeatable; default: .neuroflow/*/runs.md)")
        s.add_argument("--root", help="project root (default: current folder)")
        s.add_argument("--json", action="store_true")
        if name == "list":
            s.add_argument("--all", action="store_true", help="include reviewed and cancelled runs")
        else:
            s.add_argument("--no-update", action="store_true", help="report only; do not edit runs.md")
    t = sub.add_parser("set", help="set a run's status by hand")
    t.add_argument("--file", required=True)
    t.add_argument("--id", required=True)
    t.add_argument("--status", required=True, help=", ".join(sorted(STATUSES)))
    t.add_argument("--note")
    t.add_argument("--json", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return {"add": cmd_add, "list": cmd_list, "check": cmd_check, "set": cmd_set}[args.cmd](args)
    except (RunsError, OSError) as e:
        print(f"runs.py: error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
