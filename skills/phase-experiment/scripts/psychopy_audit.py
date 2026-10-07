#!/usr/bin/env python3
"""Static audit of PsychoPy paradigms, plus a post-run timing check of a run's data.

Audit mode reads PsychoPy Coder scripts (.py, via the ast module) and Builder files
(.psyexp, via xml.etree) without running them. It flags timing anti-patterns and
extracts the marker map (which trigger/marker codes the paradigm sends, and whether
they are locked to a screen flip) for /tool-validate.

    python <phase-experiment base dir>/scripts/psychopy_audit.py PATH [PATH ...] [--json]
    python <phase-experiment base dir>/scripts/psychopy_audit.py PATH --hook

PATH may be a file or a folder (all .psyexp files and .py files that import psychopy).
--hook prints a PostToolUse `additionalContext` JSON object when there are warnings,
nothing otherwise, and always exits 0.

Run-check mode (--csv) reads what a run produced:
  - a frame-interval log (win.saveFrameIntervals, or a CSV column such as
    frame_interval / frameIntervals / interval) -> dropped frames, vsync, refresh rate
  - a Builder trial CSV with <component>.started / <component>.stopped columns ->
    presentation durations per component, trials per condition, missing responses

    python <phase-experiment base dir>/scripts/psychopy_audit.py --csv data/run.csv
        [--refresh-hz 60] [--condition-column cond] [--rt-column key_resp.rt] [--json]

Software frame timing is not stimulus-onset timing: a clean report does not replace
a photodiode check on the stimulus PC (/tool-validate, timing_check.py).

Rules (severity):
    PSY000 info  Builder-generated .py: edit and audit the .psyexp instead
    PSY001 warn  core.wait() times a stimulus left on screen by a flip (not frame-locked)
    PSY002 warn  time.sleep() inside a loop that flips the screen
    PSY003 warn  marker/trigger sent outside win.callOnFlip() next to a flip
    PSY004 warn  parallel-port code set but never reset to 0
    PSY005 warn  hard-coded refresh rate or frame duration
    PSY006 info  frame rate never measured (win.getActualFrameRate)
    PSY007 info  frame intervals not recorded (win.recordFrameIntervals)
    PSY008 info  no trial data saved (warn in .psyexp when every data file is off)
    PSY009 info  no PsychoPy log file
    PSY010 info  event.getKeys/waitKeys used for responses (keyboard.Keyboard is more precise)
    PSY012 info  stimulus duration controlled by a clock loop rather than frame counts
    PSY101 info  short visual duration set in seconds in Builder (frames are exact)
    PSY102 warn  Builder trigger component not synced to the screen refresh
    PSY103 info  Builder keyboard RT clock not synced to the screen refresh
    PSY104 warn  blocking call in a Builder 'Each Frame' code tab (info in 'Begin Routine')
    PSY201 warn  dropped frames in a run           PSY202 warn  intervals shorter than half a frame
    PSY203 warn  measured refresh differs from --refresh-hz
    PSY204 warn  presentation durations differ from the median by a frame or more

Exit codes:
    0  no warnings (info notes may be listed)
    1  warnings found
    2  usage or runtime error (no input, unreadable file, nothing to analyse)

Stdlib only. Python 3.10+.
"""

from __future__ import annotations

import argparse
import ast
import csv
import io
import json
import re
import statistics
import sys
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path

WARN, INFO = "warn", "info"
MARKER_ALWAYS = {"push_sample", "push_chunk", "setData", "setPin", "send_trigger", "sendTrigger"}
MARKER_IF_RECEIVER = {"write", "sendMessage", "send", "trigger", "pulse"}
MARKER_TOKENS = {
    "port", "pport", "parallel", "serial", "ser", "trig", "trigger", "triggers", "lpt", "outlet", "marker",
    "markers", "daq", "ttl", "lsl",
}
REFRESH_NAME_RE = re.compile(
    r"(refresh|frame_?rate|framerate|fps|frame_?dur|frame_?period|ms_?per_?frame|monitor_?(hz|rate))", re.IGNORECASE
)
REFRESH_VALUES = {50, 59.94, 60, 70, 72, 75, 85, 100, 120, 144, 165, 240, 360}
DATA_SAVERS = {
    "ExperimentHandler", "addData", "saveAsWideText", "saveAsExcel", "saveAsPickle", "saveAsText",
    "DictWriter", "writer", "writerow", "to_csv", "savetxt",
}
FRAME_RATE_CHECKS = {"getActualFrameRate", "getMsPerFrame"}
BLOCKING = {("core", "wait"), ("time", "sleep"), ("event", "waitKeys"), (None, "input")}
VISUAL_COMPONENTS = {
    "TextComponent", "TextboxComponent", "ImageComponent", "PolygonComponent", "GratingComponent",
    "MovieComponent", "DotsComponent", "NoiseStimComponent", "EnvGratingComponent", "PatchComponent",
}
TRIGGER_SYNC = {"ParallelOutComponent": ("syncScreen", True), "SerialOutComponent": ("syncScreenRefresh", False)}
CODE_TABS = {"Before Experiment", "Begin Experiment", "Begin Routine", "Each Frame", "End Routine", "End Experiment"}
DATA_SETTINGS = ["Save csv file", "Save wide csv file", "Save excel file", "Save psydat file", "Save hdf5 file"]


@dataclass
class Finding:
    rule: str
    severity: str
    file: str
    line: int | None
    message: str
    where: str | None = None


@dataclass
class Marker:
    file: str
    line: int | None
    via: str
    on_flip: bool
    code: object
    expr: str
    where: str | None = None


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    markers: list[Marker] = field(default_factory=list)

    def add(self, *args, **kwargs) -> None:
        f = Finding(*args, **kwargs)
        key = (f.rule, f.file, f.line, f.where)
        if not any((g.rule, g.file, g.line, g.where) == key for g in self.findings):
            self.findings.append(f)


# ------------------------------------------------------------------ AST helpers


def dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Call):
        return dotted(node.func) + "()"
    return ""


def call_parts(node: ast.Call) -> tuple[str | None, str]:
    """(receiver, name) of a call: core.wait -> ('core', 'wait'); input -> (None, 'input')."""
    if isinstance(node.func, ast.Attribute):
        return dotted(node.func.value) or None, node.func.attr
    if isinstance(node.func, ast.Name):
        return None, node.func.id
    return None, ""


def is_flip(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "flip"


def has_flip(node: ast.AST) -> bool:
    return any(is_flip(n) for n in ast.walk(node))


def has_draw(node: ast.AST) -> bool:
    return any(
        isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "draw" for n in ast.walk(node)
    )


def name_tokens(name: str) -> set[str]:
    """'lsl_outlet' -> {'lsl', 'outlet'}; 'triggerBox' -> {'trigger', 'box'}; 'LPT1' -> {'lpt'}."""
    last = name.split(".")[-1]
    return {part.lower() for part in re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])", last)}


def marker_method(receiver: str | None, name: str) -> bool:
    if name in MARKER_ALWAYS:
        return True
    return name in MARKER_IF_RECEIVER and bool(receiver) and bool(name_tokens(receiver) & MARKER_TOKENS)


def literal(node: ast.AST | None):
    if node is None:
        return None
    try:
        value = ast.literal_eval(node)
    except (ValueError, SyntaxError, TypeError):
        return None
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, (list, tuple)) and len(value) == 1:
        value = value[0]
    if isinstance(value, (list, tuple)):
        return [v.hex() if isinstance(v, bytes) else v for v in value]
    return value


def safe_unparse(node: ast.AST | None) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:  # pragma: no cover - ast.unparse is total for parsed trees
        return ""


class PyAudit(ast.NodeVisitor):
    """Walks one Python source; block rules look at sibling statements, loop rules at the enclosing loop."""

    def __init__(self, report: Report, fname: str, where: str | None = None, tab: str | None = None):
        self.r, self.f, self.where, self.tab = report, fname, where, tab
        self.loops: list[ast.AST] = []
        self.loop_flip: list[bool] = []
        self.wait_aliases = {("core", "wait"), ("psychopy.core", "wait")}
        self.bare_wait = False
        self.seen_getkeys = False

    # -- traversal -----------------------------------------------------------------
    def run(self, tree: ast.Module) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module in ("psychopy.core",):
                if any(a.name == "wait" and a.asname is None for a in node.names):
                    self.bare_wait = True
        self.block(tree.body)

    def block(self, stmts: list[ast.stmt]) -> None:
        defs = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        flips = [has_flip(s) and not isinstance(s, defs) for s in stmts]
        draws = [has_draw(s) and not isinstance(s, defs) for s in stmts]
        for i, stmt in enumerate(stmts):
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                saved = (self.loops, self.loop_flip)
                self.loops, self.loop_flip = [], []
                self.block(stmt.body)
                self.loops, self.loop_flip = saved
                continue
            if isinstance(stmt, (ast.For, ast.AsyncFor, ast.While)):
                if isinstance(stmt, ast.While):
                    self.check_clock_loop(stmt)
                self.loops.append(stmt)
                self.loop_flip.append(has_flip(stmt))
                self.block(stmt.body)
                self.loops.pop()
                self.loop_flip.pop()
                self.block(stmt.orelse)
                continue
            if isinstance(stmt, ast.If):
                self.block(stmt.body)
                self.block(stmt.orelse)
                continue
            if isinstance(stmt, (ast.With, ast.AsyncWith)):
                self.block(stmt.body)
                continue
            if isinstance(stmt, ast.Try) or type(stmt).__name__ == "TryStar":
                self.block(stmt.body)
                for handler in stmt.handlers:
                    self.block(handler.body)
                self.block(stmt.orelse)
                self.block(stmt.finalbody)
                continue
            if isinstance(stmt, ast.Match):
                for case in stmt.cases:
                    self.block(case.body)
                continue
            # Is a drawn stimulus on screen at this point? Look at the last flip before this
            # statement and at the draw calls since the flip before that one.
            last = max((k for k in range(i) if flips[k]), default=None)
            shown = False
            if last is not None:
                prev = max((k for k in range(last) if flips[k]), default=-1)
                shown = draws[last] or any(draws[prev + 1 : last])
            self.simple(stmt, stim_shown=shown, flip_in_block=any(flips))

    # -- rules on simple statements --------------------------------------------------------
    def simple(self, stmt: ast.stmt, stim_shown: bool, flip_in_block: bool) -> None:
        self.check_refresh_assign(stmt)
        in_loop = bool(self.loops)
        loop_flips = bool(self.loop_flip and self.loop_flip[-1])
        for node in ast.walk(stmt):
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
                self.check_frame_div(node)
            if not isinstance(node, ast.Call):
                continue
            receiver, name = call_parts(node)
            line = getattr(node, "lineno", None)
            if (receiver, name) in self.wait_aliases or (self.bare_wait and receiver is None and name == "wait"):
                if self.tab:
                    self.tab_blocking(line, "core.wait()")
                elif in_loop and stim_shown:
                    self.r.add("PSY001", WARN, self.f, line,
                               "core.wait() times a stimulus that is on screen after win.flip(): the wait is not "
                               "locked to screen refreshes, so the duration varies by up to a frame. Count frames "
                               "instead (draw + win.flip() n times); a blank-screen ITI wait is fine.", self.where)
            elif (receiver, name) in (("time", "sleep"), ("event", "waitKeys"), (None, "input")):
                if self.tab:
                    self.tab_blocking(line, f"{receiver + '.' if receiver else ''}{name}()")
                elif name == "sleep" and in_loop and loop_flips:
                    self.r.add("PSY002", WARN, self.f, line,
                               "time.sleep() inside a loop that flips the screen: imprecise and it stalls "
                               "screen updates. Use frame counting.", self.where)
            if receiver and receiver.split(".")[-1] == "event" and name in ("getKeys", "waitKeys"):
                if not self.seen_getkeys:
                    self.seen_getkeys = True
                    self.r.add("PSY010", INFO, self.f, line,
                               "event.getKeys()/waitKeys() timestamps follow the frame loop; "
                               "psychopy.hardware.keyboard.Keyboard gives more precise response times.", self.where)
            if name == "callOnFlip" and node.args:
                target = node.args[0]
                if isinstance(target, ast.Attribute) and marker_method(dotted(target.value), target.attr):
                    arg = node.args[1] if len(node.args) > 1 else None
                    self.add_marker(line, target.attr, True, arg)
                continue
            if marker_method(receiver, name):
                arg = node.args[0] if node.args else None
                self.add_marker(line, name, False, arg)
                if self.tab in ("Begin Routine", "Each Frame"):
                    self.r.add("PSY003", WARN, self.f, line,
                               f"marker sent from '{self.tab}' code without win.callOnFlip(): it goes out "
                               "before the stimulus frame appears. Use win.callOnFlip(...) or a trigger "
                               "component with 'sync to screen' on.", self.where)
                elif flip_in_block or loop_flips:
                    self.r.add("PSY003", WARN, self.f, line,
                               "marker sent outside win.callOnFlip(): it is off from stimulus onset by up to a "
                               "frame. Use win.callOnFlip(<sender>, <code>) right before win.flip(). (For "
                               "sounds, schedule the marker with the sound onset instead.)", self.where)

    def tab_blocking(self, line: int | None, what: str) -> None:
        if self.tab == "Each Frame":
            self.r.add("PSY104", WARN, self.f, line,
                       f"{what} in an 'Each Frame' code tab blocks the frame loop and drops frames.", self.where)
        elif self.tab == "Begin Routine":
            self.r.add("PSY104", INFO, self.f, line,
                       f"{what} in 'Begin Routine' delays the routine start and shifts its timing.", self.where)

    def add_marker(self, line, via: str, on_flip: bool, arg) -> None:
        code = literal(arg)
        if via == "setData" and code == 0:
            return  # reset, not a marker
        self.r.markers.append(Marker(self.f, line, via, on_flip, code, safe_unparse(arg), self.where))

    def check_refresh_assign(self, stmt: ast.stmt) -> None:
        targets: list[ast.AST] = []
        value = None
        if isinstance(stmt, ast.Assign):
            targets, value = stmt.targets, stmt.value
        elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
            targets, value = [stmt.target], stmt.value
        for target in targets:
            name = target.id if isinstance(target, ast.Name) else target.attr if isinstance(target, ast.Attribute) else ""
            if name and REFRESH_NAME_RE.search(name) and self.numeric(value):
                self.r.add("PSY005", WARN, self.f, stmt.lineno,
                           f"hard-coded refresh rate or frame duration ({name} = {safe_unparse(value)}): measure "
                           "it with win.getActualFrameRate() at start-up and stop if it differs from the "
                           "expected value.", self.where)

    @staticmethod
    def numeric(node) -> bool:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return True
        if isinstance(node, ast.BinOp):
            return PyAudit.numeric(node.left) and PyAudit.numeric(node.right)
        return False

    def check_frame_div(self, node: ast.BinOp) -> None:
        left, right = node.left, node.right
        if (
            isinstance(left, ast.Constant) and left.value in (1, 1.0, 1000, 1000.0)
            and isinstance(right, ast.Constant) and isinstance(right.value, (int, float))
            and right.value in REFRESH_VALUES
        ):
            self.r.add("PSY005", WARN, self.f, node.lineno,
                       f"frame duration computed from an assumed refresh rate ({safe_unparse(node)}): use "
                       "the measured frame rate (win.getActualFrameRate()).", self.where)

    def check_clock_loop(self, loop: ast.While) -> None:
        calls = [n for n in ast.walk(loop.test) if isinstance(n, ast.Call)]
        timed = [c for c in calls if call_parts(c)[1] == "getTime" and "routineTimer" not in (call_parts(c)[0] or "")]
        if timed and has_flip(loop):
            self.r.add("PSY012", INFO, self.f, loop.lineno,
                       "stimulus duration controlled by a clock loop: durations still come in whole frames; "
                       "for short presentations count frames explicitly.", self.where)


def names_and_attrs(tree: ast.AST) -> set[str]:
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            out.add(node.id)
        elif isinstance(node, ast.Attribute):
            out.add(node.attr)
        elif isinstance(node, ast.keyword) and node.arg:
            out.add(node.arg)
    return out


def check_port_resets(tree: ast.AST, report: Report, fname: str) -> None:
    nonzero_line, zero = None, False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        _, name = call_parts(node)
        arg = None
        if name == "setData" and node.args:
            arg = node.args[0]
        elif name == "callOnFlip" and len(node.args) > 1 and isinstance(node.args[0], ast.Attribute):
            if node.args[0].attr == "setData":
                arg = node.args[1]
        if arg is None:
            continue
        value = literal(arg)
        if value == 0:
            zero = True
        elif isinstance(value, int) and nonzero_line is None:
            nonzero_line = node.lineno
    if nonzero_line is not None and not zero:
        report.add("PSY004", WARN, fname, nonzero_line,
                   "parallel-port code is set but never reset to 0: the next identical code makes no new edge, "
                   "so the recorder misses it. Reset (setData(0)) a few ms later or on the next flip.")


def audit_python_source(source: str, fname: str, report: Report) -> None:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise RuntimeError(f"{fname}: cannot parse Python ({exc.msg}, line {exc.lineno})") from exc
    head = "\n".join(source.splitlines()[:40])
    if "Experiment Builder" in head:
        report.add("PSY000", INFO, fname, 1,
                   "Builder-generated script: edit and audit the .psyexp; regenerating overwrites changes here.")
    PyAudit(report, fname).run(tree)
    check_port_resets(tree, report, fname)
    used = names_and_attrs(tree)
    if "Window" in used:
        if not used & FRAME_RATE_CHECKS:
            report.add("PSY006", INFO, fname, None,
                       "the frame rate is never measured: call win.getActualFrameRate() at start-up and stop "
                       "if it differs from the expected refresh rate.")
        if "recordFrameIntervals" not in used:
            report.add("PSY007", INFO, fname, None,
                       "frame intervals are not recorded: set win.recordFrameIntervals = True and save them "
                       "(win.saveFrameIntervals) to count dropped frames after a run (--csv).")
        if not used & DATA_SAVERS:
            report.add("PSY008", INFO, fname, None, "no trial data are saved (ExperimentHandler/addData or a CSV writer).")
        if "LogFile" not in used:
            report.add("PSY009", INFO, fname, None,
                       "no PsychoPy log file (logging.LogFile): the log records flip times and dropped frames.")


# ------------------------------------------------------------------ .psyexp audit


def param_map(element: ET.Element) -> dict[str, str]:
    return {p.get("name"): (p.get("val") or "") for p in element.findall("Param") if p.get("name")}


def audit_psyexp(path: Path, report: Report) -> None:
    fname = path.as_posix()
    try:
        root = ET.fromstring(path.read_bytes())
    except ET.ParseError as exc:
        raise RuntimeError(f"{fname}: not a readable .psyexp file ({exc})") from exc
    settings = root.find("Settings")
    sparams = param_map(settings) if settings is not None else {}
    if sparams.get("Save log file", "True") == "False":
        report.add("PSY009", INFO, fname, None, "the PsychoPy log file is switched off (Settings > Save log file).")
    present = [k for k in DATA_SETTINGS if k in sparams]
    if present and all(sparams[k] == "False" for k in present):
        report.add("PSY008", WARN, fname, None, "every data file is switched off in Settings: the run saves no data.")
    routines = root.find("Routines")
    for routine in list(routines) if routines is not None else []:
        rname = routine.get("name") or routine.tag
        for comp in routine:
            cname = comp.get("name") or comp.tag
            where = f"{rname}/{cname}"
            params = param_map(comp)
            if comp.tag in VISUAL_COMPONENTS and params.get("stopType") == "duration (s)":
                try:
                    dur = float(params.get("stopVal", "").strip())
                except ValueError:
                    dur = None
                if dur is not None and 0 < dur < 0.5:
                    report.add("PSY101", INFO, fname, None,
                               f"visual duration {dur:g} s set in seconds: 'duration (frames)' is exact for short "
                               "presentations.", where)
            if comp.tag in TRIGGER_SYNC:
                key, default = TRIGGER_SYNC[comp.tag]
                synced = params.get(key, str(default)) == "True"
                if not synced:
                    report.add("PSY102", WARN, fname, None,
                               f"{comp.tag} '{cname}' is not synced to the screen refresh: the trigger goes out when "
                               "the frame is drawn, not when it appears. Turn on 'sync to screen'.", where)
            if comp.tag == "KeyboardComponent" and params.get("syncScreenRefresh", "True") == "False":
                report.add("PSY103", INFO, fname, None,
                           "keyboard RT clock is not synced to the screen refresh: RTs are not measured from the "
                           "stimulus frame.", where)
            if comp.tag == "CodeComponent":
                for tab in sorted(CODE_TABS & params.keys()):
                    code = params[tab]
                    if not code.strip():
                        continue
                    try:
                        tree = ast.parse(code)
                    except SyntaxError:
                        report.add("PSY000", INFO, fname, None, f"could not parse the '{tab}' Python code.", where)
                        continue
                    PyAudit(report, fname, where=f"{where} [{tab}]", tab=tab).run(tree)


# ------------------------------------------------------------------ run check (--csv)


def _num(value) -> float | None:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return number if number == number else None  # drop NaN


INTERVAL_COL = re.compile(r"^(frame[_ ]?intervals?|frameintervals|intervals?|dt|frame[_ ]?times?)$", re.IGNORECASE)


def load_run(path: Path) -> tuple[list[float] | None, list[dict] | None, list[str]]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    stripped = text.strip()
    if not stripped:
        return None, None, []
    first = stripped.splitlines()[0]
    if re.search(r"[A-Za-z_]", first) and not re.fullmatch(r"[\s,;0-9.eE+-]+", first):
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        header = reader.fieldnames or []
        for col in header:
            if col and INTERVAL_COL.match(col.strip()):
                values = [_num(r.get(col)) for r in rows]
                return [v for v in values if v is not None], None, header
        return None, rows, header
    numbers = [_num(tok) for tok in re.split(r"[\s,;]+", stripped)]
    return [v for v in numbers if v is not None], None, []


def analyze_intervals(intervals: list[float], refresh_hz: float | None, report: Report, fname: str) -> dict:
    if len(intervals) < 2:
        raise RuntimeError(f"{fname}: fewer than 2 frame intervals")
    unit = "ms" if statistics.median(intervals) > 1.0 else "s"
    secs = [v / 1000.0 for v in intervals] if unit == "ms" else intervals
    median = statistics.median(secs)
    period = 1.0 / refresh_hz if refresh_hz else median
    dropped = [v for v in secs if v > 1.5 * period]
    short = [v for v in secs if v < 0.5 * period]
    summary = {
        "kind": "frame-intervals",
        "frames": len(secs),
        "input_unit": unit,
        "median_ms": round(median * 1000, 3),
        "measured_hz": round(1.0 / median, 2),
        "max_ms": round(max(secs) * 1000, 3),
        "dropped": len(dropped),
        "dropped_pct": round(100.0 * len(dropped) / len(secs), 3),
        "short": len(short),
    }
    if dropped:
        report.add("PSY201", WARN, fname, None,
                   f"{len(dropped)} dropped frame(s) ({summary['dropped_pct']}%), longest interval "
                   f"{summary['max_ms']} ms")
    if len(short) > max(1, 0.01 * len(secs)):
        report.add("PSY202", WARN, fname, None,
                   f"{len(short)} interval(s) shorter than half a frame: vsync may be off (tearing, wrong timing)")
    if refresh_hz and abs(summary["measured_hz"] - refresh_hz) > 1.0:
        report.add("PSY203", WARN, fname, None,
                   f"measured refresh {summary['measured_hz']} Hz differs from the expected {refresh_hz:g} Hz")
    return summary


def analyze_trials(rows: list[dict], header: list[str], args, report: Report, fname: str) -> dict:
    refresh = args.refresh_hz
    if refresh is None and "frameRate" in header:
        refresh = next((v for v in (_num(r.get("frameRate")) for r in rows) if v), None)
    period = 1.0 / refresh if refresh else None
    comps = sorted({h[: -len(".started")] for h in header if h and h.endswith(".started")}
                   & {h[: -len(".stopped")] for h in header if h and h.endswith(".stopped")})
    summary: dict = {"kind": "trial-csv", "rows": len(rows), "refresh_hz": refresh, "components": {}}
    for comp in comps:
        durs = []
        for row in rows:
            start, stop = _num(row.get(f"{comp}.started")), _num(row.get(f"{comp}.stopped"))
            if start is not None and stop is not None and stop >= start:
                durs.append(stop - start)
        if not durs:
            continue
        med = statistics.median(durs)
        entry = {"n": len(durs), "median_ms": round(med * 1000, 3), "min_ms": round(min(durs) * 1000, 3),
                 "max_ms": round(max(durs) * 1000, 3)}
        if period:
            off = [d for d in durs if abs(d - med) >= 0.75 * period]
            entry["off_by_a_frame"] = len(off)
            if off:
                report.add("PSY204", WARN, fname, None,
                           f"{len(off)} of {len(durs)} '{comp}' presentations differ from the median duration "
                           f"({entry['median_ms']} ms) by a frame or more")
        summary["components"][comp] = entry
    if args.condition_column:
        counts: dict[str, int] = {}
        for row in rows:
            key = (row.get(args.condition_column) or "").strip()
            if key:
                counts[key] = counts.get(key, 0) + 1
        summary["trials_per_condition"] = counts
    if args.rt_column:
        rts = [_num(r.get(args.rt_column)) for r in rows]
        valid = [v for v in rts if v is not None]
        summary["responses"] = {
            "missing": len(rts) - len(valid),
            "median_rt_ms": round(statistics.median(valid) * 1000, 1) if valid else None,
        }
    if not summary["components"] and not args.condition_column and not args.rt_column:
        raise RuntimeError(
            f"{fname}: no frame intervals and no <component>.started/.stopped columns found; "
            "pass --condition-column/--rt-column or a frame-interval log"
        )
    if period is None and summary["components"]:
        summary["note"] = "no refresh rate known (pass --refresh-hz): durations summarised only"
    return summary


# ------------------------------------------------------------------ output


def collect_targets(paths: list[str]) -> list[Path]:
    targets: list[Path] = []
    for name in paths:
        path = Path(name)
        if path.is_dir():
            for cand in sorted(path.rglob("*")):
                if cand.suffix == ".psyexp":
                    targets.append(cand)
                elif cand.suffix == ".py" and "psychopy" in cand.read_text(encoding="utf-8", errors="replace"):
                    targets.append(cand)
        elif path.is_file():
            targets.append(path)
        else:
            raise RuntimeError(f"no such file or folder: {name}")
    return targets


def audit_paths(paths: list[str]) -> tuple[Report, list[str]]:
    report = Report()
    files = []
    for path in collect_targets(paths):
        files.append(path.as_posix())
        if path.suffix == ".psyexp":
            audit_psyexp(path, report)
        else:
            audit_python_source(path.read_text(encoding="utf-8", errors="replace"), path.as_posix(), report)
    return report, files


def format_finding(f: Finding) -> str:
    loc = f.file + (f":{f.line}" if f.line else "") + (f" ({f.where})" if f.where else "")
    return f"{loc}  {f.severity.upper():4}  {f.rule}  {f.message}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Static audit of PsychoPy paradigms (.py/.psyexp) and a post-run frame-timing check (--csv).",
    )
    parser.add_argument("paths", nargs="*", help=".py/.psyexp files or folders to audit")
    parser.add_argument("--csv", dest="csv_path", help="run-check mode: a frame-interval log or a Builder trial CSV")
    parser.add_argument("--refresh-hz", type=float, help="expected refresh rate (run-check mode)")
    parser.add_argument("--condition-column", help="trial CSV column with the condition label")
    parser.add_argument("--rt-column", help="trial CSV column with the response time (s)")
    parser.add_argument("--hook", action="store_true", help="print PostToolUse additionalContext JSON; always exit 0")
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass
    args = build_parser().parse_args(argv)
    if args.hook:
        try:
            targets = [p for p in args.paths if p.endswith(".psyexp") or
                       (p.endswith(".py") and "psychopy" in Path(p).read_text(encoding="utf-8", errors="replace"))]
            report, _ = audit_paths(targets) if targets else (Report(), [])
        except (RuntimeError, OSError):
            return 0
        warns = [f for f in report.findings if f.severity == WARN]
        if warns:
            lines = [f"{f.rule} {f.file}{':' + str(f.line) if f.line else ''}: {f.message}" for f in warns[:8]]
            context = "psychopy_audit found timing warnings in the paradigm just edited:\n" + "\n".join(lines)
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": context}}))
        return 0
    if bool(args.paths) == bool(args.csv_path):
        print("error: give paradigm files to audit, or --csv FILE for a run check (not both)", file=sys.stderr)
        return 2
    try:
        if args.csv_path:
            path = Path(args.csv_path)
            report = Report()
            intervals, rows, header = load_run(path)
            if intervals:
                summary = analyze_intervals(intervals, args.refresh_hz, report, path.as_posix())
            elif rows is not None:
                summary = analyze_trials(rows, header, args, report, path.as_posix())
            else:
                raise RuntimeError(f"{path.as_posix()}: nothing to analyse")
            payload = {"mode": "run-check", "file": path.as_posix(), "summary": summary,
                       "findings": [asdict(f) for f in report.findings]}
            text = [f"run check: {path.as_posix()}", json.dumps(summary, indent=2)]
        else:
            report, files = audit_paths(args.paths)
            payload = {"mode": "audit", "files": files, "findings": [asdict(f) for f in report.findings],
                       "markers": [asdict(m) for m in report.markers]}
            text = [f"audited {len(files)} file(s)"]
            if report.markers:
                text.append("marker map:")
                for m in report.markers:
                    code = m.code if m.code is not None else f"<dynamic: {m.expr}>"
                    loc = m.file + (f":{m.line}" if m.line else "") + (f" ({m.where})" if m.where else "")
                    text.append(f"  {loc}  {m.via}  code={code}  on_flip={'yes' if m.on_flip else 'NO'}")
    except (RuntimeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    warns = sum(1 for f in report.findings if f.severity == WARN)
    infos = len(report.findings) - warns
    if args.json:
        print(json.dumps(payload, indent=2, default=str))
    else:
        text += [format_finding(f) for f in report.findings]
        text.append(f"{warns} warning(s), {infos} note(s)")
        print("\n".join(text))
    return 1 if warns else 0


if __name__ == "__main__":
    sys.exit(main())
