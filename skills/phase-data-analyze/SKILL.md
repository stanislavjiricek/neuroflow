---
name: phase-data-analyze
description: Phase guidance for the neuroflow /data-analyze command. Loaded automatically when /data-analyze is invoked to orient agent behavior, relevant skills, and workflow hints for the data-analyze phase.
---

# phase-data-analyze

The data-analyze phase applies statistical and computational methods to preprocessed data to test the research hypothesis.

## Approach

- Read `.neuroflow/ideation/` for the research question and `.neuroflow/data-preprocess/` for the preprocessing report before choosing methods
- Write an `analysis-plan.md` first; do not write analysis code before the plan is accepted
- Audit statistical assumptions explicitly (normality, sphericity, independence) before selecting tests
- Apply appropriate multiple-comparison correction; if omitted, flag it and explain why
- Numbers in summaries and manuscripts come from files the scripts wrote (`results/`), never retyped from a console or a notebook

## Provenance

Pipeline scripts record their own provenance — correct on any machine, HPC jobs included.

1. Copy `<skill base dir>/scripts/nf_provenance.py` once into the folder of the scripts that use it (`scripts/analysis/`, `scripts/preprocessing/`, the model folder) and commit it — jobs and collaborators then have it without neuroflow
2. In each script:
   ```python
   import nf_provenance
   run = nf_provenance.start(inputs=["derivatives/preprocessing/"], seeds={"permutations": 42})
   ...  # use run.seeds["permutations"] - or rng = numpy.random.default_rng(run.seed("cv", 7))
   run.finish(outputs=["results/erp_stats.csv", "figures/erp.png"])
   ```
   or `with nf_provenance.start(...) as run:` — a crash is then recorded as `error`
3. Every run rewrites that script's block in `environment.md` (Python, OS, versions of the imported packages, declared seeds, git commit and dirty flag, job id) and adds `provenance/<UTC time>_<script>.json` (argv, sha256 of inputs and outputs, timestamps, status). Hashes are cached outside the project, so reruns on large data stay fast
4. Non-Python steps (MATLAB, R, shell): `python <skill base dir>/scripts/nf_provenance.py record --input <in> --output <out> -- <command>` — exit 0: the command succeeded; 1: it failed (recorded); 2: it could not start
5. Before quoting results that may be stale: `python <skill base dir>/scripts/nf_provenance.py verify <run record>` — exit 1: an output changed or disappeared since that run

Only seeds the script declares are recorded — an environment variable seeds nothing. Run confirmatory analyses from a committed tree; the record's dirty flag shows when that was not the case. In a DataLad dataset, `datalad run` is an equivalent record.

## Notebooks

- Strip outputs before committing: `nbstripout --install` once per repository (a git filter, so it also covers commits made outside Claude Code), or clear outputs by hand — outputs can carry participant rows, absolute paths and names
- Notebook outputs are never the results of record. A number reaches `analysis-summary.md` or a manuscript only from a script that writes `results/`, or from a clean headless rerun (`jupyter nbconvert --to notebook --execute <nb>.ipynb --output <nb>-rerun.ipynb`) — out-of-order cells and hidden kernel state go unnoticed otherwise

## Multiverse (exploratory)

To show how much a result depends on defensible analysis choices, run every combination of them and report all results — never the best one.

1. Declare the grid before running anything: a JSON spec with `name`, `command` (placeholders `{parameter}`, `{outdir}`), `grid`, `result` (JSON file + keys, or stdout regexes), optional `p_key`, and an `out_dir` under an `exploratory/` folder (e.g. `results/exploratory/multiverse/<name>`) — format in the script's header
2. `python <skill base dir>/scripts/multiverse.py <spec> --dry-run` — show the person the specification count first
3. `python <skill base dir>/scripts/multiverse.py <spec>` — each specification is appended to `.neuroflow/data-analyze/multiverse.md` as soon as it finishes (ledger format of the autoresearch integrity reference; rows are never edited or deleted). Exit 0: all ran; exit 1: some failed, still logged — report them; exit 2: spec error, nothing ran. `--resume` continues an interrupted run without duplicate rows
4. Report the whole curve (`curve.csv`; min, median, max, and how many specifications fall below alpha), labelled EXPLORATORY. The ledger counts only what was logged through `multiverse.py` or autoresearch — wherever "N specifications were tried" appears, say that analyses run any other way are not in it

The preregistered specification stays confirmatory and is reported as such; the multiverse sits beside it.

## Clean-room reproduction

Before `/paper --submit` or `/output --archive`, or whenever a result must be trusted, rerun the confirmatory pipeline from a fresh clone in a fresh environment and compare outputs:

`python <skill base dir>/scripts/cleanroom.py --record <run record> --requirements requirements.txt --link <untracked input data> --report .neuroflow/data-analyze/cleanroom-YYYY-MM-DD.md`

- `--record` supplies the command, the commit and the expected output hashes from an `nf_provenance` run record; without one, give `--output <path>` and the command after `--`
- Environment: `--requirements <file in the repo>` (fresh venv; downloads packages), `--python <interpreter>` for an environment built from a lock file, or `--current-python` (weakest: environment not rebuilt — the report says so)
- `--link` only input data git does not hold — never a folder the pipeline writes into (refused); use `--copy` for that
- JSON/CSV/TSV numbers may differ within `--rtol`/`--atol`; any other file must be byte-identical, so machine-readable statistics reproduce better than figures
- Exit 0: reproduced. Exit 1: the rerun failed or an output differs — check seeds and package versions before suspecting the analysis, and report it. Exit 2: setup failed (clone, environment, link) — fix and rerun
- Long reruns: `run_in_background`, or detached and registered in `.neuroflow/data-analyze/runs.md`

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules
- `neuroflow:bids` — invoke when querying dataset structure with pybids, loading subject/session/task metadata from participants.tsv and events.tsv, or writing analysis outputs to BIDS derivatives

## Workflow hints

- All code, results, and figures go to `output_path` (`scripts/analysis/`, `results/`, `figures/`), not inside `.neuroflow/`
- Save `analysis-plan.md` to `.neuroflow/data-analyze/` before running any scripts
- Log deviations from a pre-registered analysis plan in `.neuroflow/preregistration/deviations.md` (append-only) and in `.neuroflow/reasoning/data-analyze.jsonl`
- `multiverse.md` — written by exploratory `/autoresearch` loops and by `multiverse.py`: every analysis specification tried, with its result. Append-only; anything that came from it is exploratory
- Runs longer than ~10 minutes follow `<skill base dir>/../phase-brain-run/references/long-runs.md` (registry `runs.md` in this phase folder); HPC: `neuroflow:phase-brain-run` → *Long runs and HPC*
- `multiverse.md`, `runs.md` and `cleanroom-*.md` reports live in `.neuroflow/data-analyze/` — list each in the phase `flow.md`

## Slash command

`/neuroflow:data-analyze` — runs this workflow as a slash command.
