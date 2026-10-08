# Long runs — launch, register, check

Shared by `/brain-run`, `/brain-optimize`, `/data-preprocess` and `/data-analyze`. `<skill base dir>` below is the `phase-brain-run` skill folder; from another phase skill it is `<that skill's base dir>/../phase-brain-run`.

A run is **long** when it may take more than about 10 minutes (the longest a foreground tool call waits) or must outlive the session — preprocessing a cohort, a simulation, a sweep, a multiverse, a clean-room rerun.

---

## 1 — Where it runs

| Situation | How |
|---|---|
| Finishes while the session is open | Bash/PowerShell tool with `run_in_background`. Print progress lines (`k/N`, tqdm). Claude Code reports when it ends; arm the Monitor tool on the log to catch `Traceback`, `nan` or `Killed` early. Register it only if it might outlive the session. |
| Must survive the session (overnight, laptop lid open) | Detached launch below, then register in `runs.md`. |
| HPC cluster | A job — never the login node (rule LOGIN-NODE in this skill's `SKILL.md`). Start from `templates/job-slurm.sh` or `templates/job-pbs.sh`, submit, register the job id. |

**Preflight before a long run:** free disk for the outputs (`df -h <output dir>`, or `Get-PSDrive` on Windows), GPU memory if used (`nvidia-smi`), and memory and runtime from the smoke test — never launch the full run blind.

## 2 — Detached launch (exit code goes to `<log>.exitcode`)

Linux / macOS:

```bash
mkdir -p models/results/r1
nohup sh -c 'python models/run_sim.py --config run.yaml > models/results/r1/run.log 2>&1; echo $? > models/results/r1/run.log.exitcode' > /dev/null 2>&1 &
echo $!          # process id for --pid
```

Windows (PowerShell; Git Bash `$!` is not a Windows process id):

```powershell
New-Item -ItemType Directory -Force models/results/r1 | Out-Null
$p = Start-Process cmd -WindowStyle Hidden -PassThru -ArgumentList '/v:on /c "python models\run_sim.py --config run.yaml > models\results\r1\run.log 2>&1 & echo !errorlevel! > models\results\r1\run.log.exitcode"'
$p.Id            # process id for --pid
```

## 3 — Register it

```bash
python <skill base dir>/scripts/runs.py add --file .neuroflow/<phase>/runs.md \
    --command "python models/run_sim.py --config run.yaml" --log models/results/r1/run.log \
    --output models/results/r1/metrics.json --pid <pid>
# HPC: --where slurm|pbs --job-id <id> instead of --log/--pid
```

`runs.md` lives in the phase folder of the command that launched the run — list it in that phase's `flow.md`. One row per run: run id, start (UTC), where (`local pid …`, `slurm …`, `pbs …`), command, log, expected outputs, status, note. Rows are never deleted.

## 4 — Next session: check before new work

At the start of the command, when `.neuroflow/<phase>/runs.md` exists:

```bash
python <skill base dir>/scripts/runs.py check --file .neuroflow/<phase>/runs.md
```

| Exit | Meaning | Do |
|---|---|---|
| 0 | nothing finished that needs attention | continue; mention runs still queued or running |
| 1 | a run is `done`, `failed` or `unknown` | inspect it now: log tail, outputs, sanity checks; write the phase's summary (`run-summary.md`, `preprocess-report.md` …); then `runs.py set --file … --id <run> --status reviewed` |
| 2 | usage error | fix the command |

Scheduler state comes from `squeue`/`sacct` (SLURM) or `qstat` (PBS), so `check` sees jobs only when it runs on the cluster; from elsewhere it says "not checked". The scheduler's mail (`--mail-type=END,FAIL`, `#PBS -m ae` in the templates) covers the gap.
