# Preflight block for PsychoPy paradigms (optional)

A `preflight()` function to paste at the top of a Coder paradigm (or into a Builder
"Begin Experiment" code tab). It runs inside the paradigm, so it runs however the
paradigm is launched — PsychoPy Runner, a double-click, a terminal — with no agent
involved. It checks what usually goes wrong before a session, shows the problems to
the experimenter, and appends one line per session to a local acquisition log.

It is a convenience, not a gate: the experimenter can continue past a problem, and
that override is logged. It is never a safety interlock for stimulation hardware.

Fill in `PREFLIGHT` from `recording-setup.md`. Probing a trigger port or LSL takes a
second or two — run it before the participant is seated, not between trials.

```python
# --- preflight (neuroflow /experiment) -------------------------------------------
import csv
import os
import shutil
from datetime import date, datetime

from psychopy import event, visual

PREFLIGHT = {
    "expected_hz": 60.0,            # stimulus display refresh rate (recording-setup.md)
    "hz_tolerance": 1.0,
    "data_dir": "data",
    "min_free_gb": 5.0,
    "lsl_streams": ["EEG"],         # stream names that must be on the network; [] if no LSL
    "parallel_port": None,          # e.g. 0x3FF8; None if no parallel port
    "ethics_status": None,          # path to .neuroflow/ethics/status.md if this PC has the project
    "log": "data/acquisition-log.csv",
}


def preflight(win, participant, cfg=PREFLIGHT):
    """Return True to start the session; False if the experimenter quits."""
    problems = []
    hz = win.getActualFrameRate(nIdentical=20, nMaxFrames=240, nWarmUpFrames=20)
    if hz is None or abs(hz - cfg["expected_hz"]) > cfg["hz_tolerance"]:
        problems.append(f"refresh rate {hz} Hz, expected {cfg['expected_hz']} Hz")
    os.makedirs(cfg["data_dir"], exist_ok=True)
    free_gb = shutil.disk_usage(cfg["data_dir"]).free / 1e9
    if free_gb < cfg["min_free_gb"]:
        problems.append(f"only {free_gb:.1f} GB free for {cfg['data_dir']}")
    if cfg["lsl_streams"]:
        try:
            import pylsl
            found = {s.name() for s in pylsl.resolve_streams(wait_time=2.0)}
            missing = [n for n in cfg["lsl_streams"] if n not in found]
            if missing:
                problems.append("LSL stream(s) not found: " + ", ".join(missing))
        except ImportError:
            problems.append("pylsl is not installed: LSL streams not checked")
    if cfg["parallel_port"] is not None:
        try:
            from psychopy import parallel
            parallel.ParallelPort(address=cfg["parallel_port"]).setData(0)
        except Exception as exc:  # driver missing, wrong address
            problems.append(f"trigger port {cfg['parallel_port']:#x} not usable: {exc}")
    path = cfg["ethics_status"]
    if path and os.path.exists(path):
        text = open(path, encoding="utf-8").read()
        meta = {}
        if text.startswith("---"):
            for line in text.split("---")[1].splitlines():
                key, sep, value = line.partition(":")
                if sep:
                    meta[key.strip()] = value.split("#")[0].strip()
        if not meta:
            problems.append("ethics status.md has no frontmatter - run /ethics --status once")
        elif meta.get("status") != "approved" or meta.get("set_by") != "person":
            problems.append(f"ethics status {meta.get('status', 'missing')} (set_by {meta.get('set_by')})")
        elif meta.get("expires") and meta["expires"] < date.today().isoformat():
            problems.append(f"ethics approval expired on {meta['expires']}")
    decision = "ok"
    if problems:
        msg = visual.TextStim(win, height=0.04, wrapWidth=1.6, text="PREFLIGHT\n\n" + "\n".join(problems)
                              + "\n\nc = continue anyway (logged)    q = quit")
        msg.draw()
        win.flip()
        decision = "override" if event.waitKeys(keyList=["c", "q"])[0] == "c" else "quit"
        win.flip()
    new = not os.path.exists(cfg["log"])
    with open(cfg["log"], "a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if new:
            writer.writerow(["time", "participant", "refresh_hz", "free_gb", "decision", "problems"])
        writer.writerow([datetime.now().isoformat(timespec="seconds"), participant,
                         f"{hz:.2f}" if hz else "", f"{free_gb:.1f}", decision, " | ".join(problems)])
    return decision != "quit"

# Call it right after the window exists:
#     if not preflight(win, participant=expInfo["participant"]):
#         core.quit()
# --------------------------------------------------------------------------------
```

`participant` is the pseudonymous ID (`sub-07`), never a name. Record overrides that
affect the data as deviations (`/preregistration` deviation log) and in the session
notes.

## Manual checklist (keep it in `recording-setup.md`)

The automated checks do not replace the lab's own run sheet. A typical list:

- [ ] Consent signed on the version in force (`/ethics --status`)
- [ ] Participant ID entered as a pseudonym; allocation slot taken (`allocation.py next`)
- [ ] Impedances / signal quality at target; cap and reference placed as in `recording-setup.md`
- [ ] Photodiode or trigger check done today; recorder running and writing to the right folder
- [ ] Room set up (lights, noise, phones off); Claude Code and other agents closed on the acquisition PCs
