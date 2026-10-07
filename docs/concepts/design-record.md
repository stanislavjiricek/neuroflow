---
title: Design record
---

# Design record

neuroflow 0.2.22 came out of a review of 270 ideas for Claude Code function hooks ("mods"): what a hooks
module could do for a research workflow, and what it should not. Each idea was rated for feasibility, for whether it
needs a mod at all, for value, effort and risk, and put in a tier. This page records what became of each one.

| Tier | Meaning | Ideas |
|---|---|---|
| T0 | Groundwork: tests, rollout, contracts the rest depends on | 33 |
| T1 | Build first: clear value, low risk | 17 |
| T2 | Build with care: value, with conditions | 44 |
| T3 | Later, behind go criteria | 14 |
| X | Do not build as proposed: done another way, folded, or an anti-pattern kept as a charter rule | 162 |

| Outcome | Ideas |
|---|---|
| In the mod | 40 |
| Built | 63 |
| Built differently | 61 |
| Folded into another | 10 |
| Charter rule | 37 |
| Not built | 59 |

*Built* means the plugin's prose, scripts or CI do it, for everyone. *In the mod* means the optional hooks module
does it (see [The neuroflow mod](mods.md)); every such feature has a prose path that works without it. *Built
differently* means the need is met another way than the idea proposed. *Charter rule* means the idea was a
warning, kept as a rule of the mod's charter.

## Anti pattern

| ID | Idea | Tier | Outcome | Note |
|---|---|---|---|---|
| G102 | Anti-pattern: giving other people's text system-prompt authority | X | Charter rule | Charter: others' text never gets system-prompt authority. |
| G106 | Anti-pattern: deferring durable writes to session end, timers or child processes | X | Charter rule | Charter: recover on start, never flush on end; idempotent effects. |
| G123 | Anti-pattern: feature sprawl on an early-access API with no kill rule | X | Charter rule | Charter: fixed allowlist; features must retire a failing rule. |
| G124 | Anti-pattern: verification badges that claim more than they check | X | Charter rule | 'verified/unverified' DOI wording replaced by a doi_check stub field that names the test performed (record:<api> \| resolves:<date> via discover_paper_access landingUrl \| not-resolving:<date> \| none), plus a note that a… |
| G201 | Anti-pattern: ledgers that hide what they did not observe | X | Charter rule | Charter: generated records print observation window and blind spots. |
| G202 | Anti-pattern: records that satisfy the checker but not their purpose | X | Charter rule | Charter, built into M018: markers set only by a press; model edits denied. |
| M201 | Anti-pattern: noisy UI the user did not ask for | X | Charter rule | Charter: no unasked panes, one band slot, quiet by default. |
| M202 | Anti-pattern: platform-blind features | X | Charter rule | Charter: every visual has a text or file fallback; Windows realities. |
| M203 | Anti-pattern: API capabilities neuroflow should not use | X | Charter rule | Charter: no fake turns, hostile UI control or Elicitation auto-answers. |
| M204 | Anti-pattern: soft gates for hard rules | X | Charter rule | Charter: hard rules deny before next with .catch, backed by detection. |
| M205 | Anti-pattern: integrity theater and over-blocking | X | Charter rule | Charter: observe, warn, ask ladder; deny only irreversible breaks. |
| M206 | Anti-pattern: rewriting or forging the record | X | Charter rule | Charter: annotate, never rewrite the record; consent only from a press. |
| M207 | Anti-pattern: hidden judgment and unbounded background spend | X | Charter rule | Autoresearch part done: an iteration/time/cost cap plus stop conditions replaces the uncapped loop (same text as M220). |
| M208 | Anti-pattern: the mod in the acquisition data path | X | Charter rule | Charter: the mod may observe acquisition, never carry samples. |
| M209 | Anti-pattern: surveillance creep | X | Charter rule | Rule text in phase-hive (privacy rule and governance rows: no inferred or broadcast presence, activity, hours, progress or mood; sync.json is now local-only and gitignored by the hive repo) and in phase-flowie and… |
| M210 | Anti-pattern: a third implementation of every check | X | Built differently | scripts/automation/repo_checks.py now holds every repo check once, under stable ids V1-V15. |
| M211 | Anti-pattern: rewriting skill text at runtime | X | Charter rule | Charter: skill.prompt only adds delimited preambles. |
| M212 | Anti-pattern: letting the mod become the source of truth | X | Charter rule | Charter: skills stay normative; mod writes marked and idempotent. |
| M213 | Anti-pattern: ungated, unscoped activation | X | Charter rule | Charter: project-only activation, version floor, observe default. |
| M214 | Anti-pattern: digit hotkeys in the AbovePrompt band | X | Charter rule | Charter: letter hotkeys only in the band. |
| M215 | Anti-pattern: volatile or bloated context injection | X | Charter rule | Charter: only stable facts in prompt.compose; budgeted digests. |
| M216 | Anti-pattern: model calls in hot paths | X | Charter rule | The rule (no awaited model calls in prompt.submit, prompt.edit or render) belongs to the mod charter. |
| M217 | Anti-pattern: automatic outbound data movement | X | Charter rule | The rule lives in neuroflow-core → Sharing tiers (Egress, EGRESS-CONFIRM). |
| M218 | Anti-pattern: git through $.process.run without noticing repo hooks are off | X | Charter rule | Mod-charter rule: mod-run git ($.process.run/spawn, repo hooks off) only in ~/.neuroflow/flowie and hive caches, after checking hooksPath/hooks/LFS. |
| M219 | Anti-pattern: AI-disclosure evasion | X | Charter rule | Rule lives in skills/humanizer/SKILL.md ('When to use — and what it is not'): style edit only on request, never to evade AI detection or disclosure. |
| M220 | Anti-pattern: an unkillable NEVER-STOP loop | X | Charter rule | Charter: every loop has caps and a visible stop. |
| M221 | Anti-pattern: blanket permission auto-approval for .neuroflow work | X | Charter rule | Charter: no blanket auto-approval; native scoped rules instead. |
| M222 | Anti-pattern: running stimuli, questionnaires or consent inside Claude Code | X | Charter rule | Rule 'participants only ever see validated software (never Claude Code); answers would reach the model and every installed plugin' in /ethics rule 5, /experiment ground rules, /tool-validate rules and the… |
| M223 | Anti-pattern: owning the engine | X | Charter rule | Charter: stay additive; never swap models or refuse other plugins. |
| M224 | Anti-pattern: auto-booking AI compute into grant expenses | X | Charter rule | Rule text in phase-finance (Approach) and /finance (Expense log), and stated in the docs: every expense comes from the person with a receipt; AI usage figures (/cost, tokens, a share of a subscription) are never booked… |
| M225 | Anti-pattern: shadow research state in $.store | X | Charter rule | Charter: truth in .neuroflow files; $.store only for prefs and caches. |

## Automation background

| ID | Idea | Tier | Outcome | Note |
|---|---|---|---|---|
| G111 | Engine-native goals for bounded multi-turn commands | T3 | Not built | Later spike. |
| G119 | Network-loss degradation and durable outbox | X | Built differently | Git is the outbox: unpushed commits and flowie sync failures are doctor and `/hive --doctor` lines. |
| M101 | Background literature watch and scoop alarm | T3 | In the mod | Pinned literature queries unchecked for a week raise a reminder at start; searches still run only on request. |
| M102 | Pipeline runner state machine | X | Built differently | Built the verdict's alternative: /pipeline runs exactly one step per invocation and pipeline-plan.md carries the state. |
| M103 | Autoresearch driver: one iteration per turn | T2 | In the mod | `/autoresearch drive {name}`: one iteration per turn, caps checked with `ar.py status` between turns, a stop key. |
| M104 | Zero-turn live note capture (/notes and /meeting live) | T2 | In the mod | Live note capture writes each message verbatim into the notes file without a model turn. |
| M105 | Flowie and hive sync engine | T0 | Built | Flowie prose now has one Git operations pattern: pull --rebase, abort on conflict, Sync by explicit paths, never add -A, never integrations.json. |
| M106 | Safe-point compaction and summary archive | X | Folded into another | Safe-point compaction is covered by M102 (/compact between pipeline steps) and by the M103 driver requirement (compact only between iterations). |
| M107 | Background pollers: NotebookLM artifacts and reminders | X | Not built | Claude Code's background Bash, Monitor and CronCreate already poll slow jobs. |
| M108 | Spend and concurrency governor | X | Built differently | Same concurrency cap as M089. |
| M109 | Notification policy center | X | Not built | neuroflow sends no notifications; write a small notify() helper when the first feature needs one. |
| M110 | Machine-local project registry | X | Built differently | Added a machine-local registry ~/.neuroflow/local-projects.json (name, path, remote, last_opened), written by /flowie --link and never synced. |
| M111 | LabRecorder remote control and XDF verification | X | Built differently | xdf_check.py: standalone post-run XDF check (expected streams, nominal vs effective rate drift, gaps, backwards timestamps, marker counts per code; pyxdf optional) for use at the rig with no agent. |
| M112 | HPC job tracker for PBS Pro and SLURM | T3 | Built | runs.py check reads job state on demand: squeue then sacct for SLURM, qstat -x -f for PBS, or 'not checked' when those tools are absent. |
| M113 | Autoresearch branches in git worktrees | X | Not built | Autoresearch branches are sequential snapshots by design, and the files involved are not owned by this package. |

## Collaboration

| ID | Idea | Tier | Outcome | Note |
|---|---|---|---|---|
| G127 | Coauthor comment round-trip for Word manuscripts | T3 | Built | /paper --coauthor <file.docx> asks which file is the source of truth, takes dispositions in batches of about ten (accept/reply/task/decline), never edits the coauthor's file, and audits the reply file with… |
| G128 | Shared-dataset errata with impact tracing | T3 | Built | Defined an errata/{dataset-id}.md format in the hive: an append-only table, with scope limited to dataset labels. |
| G203 | Schema version and lock visibility for mixed-version teams | T0 | Built | Every config written by the scaffold or migrate carries nf_schema: 1. |
| G204 | Merge-safe memory formats and a conflict-marker tripwire | T0 | Built | Core now defines the C3 Reasoning log and C4 Merge safety (union lines, rebuild flow.md after a conflict, conflict-marker tripwire). |
| G211 | Project handoff dossier | T3 | Built | New /output --handoff mode (steps H1-H3) plus read-only handoff.py. |
| M133 | Wiki ambient pre-query and backlinks | T2 | In the mod | Wiki page titles a prompt names are attached as data, at most three. |
| M134 | Deterministic meeting close with review pane and invites | X | Built differently | New skills/phase-meeting/scripts/meeting_close.py. |
| M135 | Supervisor 1:1 agenda drafted from your own record | X | Built differently | /meeting --prepare for a recurring template now adds Follow-ups (open tasks whose source is an earlier meeting of the same template) and Since last time (tasks done since then by updated date, plus reasoning .jsonl… |
| M136 | @people autocomplete with roster context | X | Built differently | Rule added: never invent an email address or handle. |
| M137 | Upstream change digests: hive norms and teammate activity | X | Not built | Not built: /hive --sync already prints a change digest (now computed by git diff), and a teammate 'who changed what' feed would break the hive's no-surveillance rule. |
| M138 | Authorship stamps on shared memory | X | Not built | Not built: git blame already records authorship for everyone, and silently stamping the model's writes would break the files and the reasoning-log format. |
| M139 | Supervisor status page and feedback through a private Artifact | X | Not built | Not built: supervisor accounts, hosting rules and comment intake are outside the plugin, and a --share step would belong in /write-report, which is not in this package. |
| M140 | Lab-curated agents and checklists from the hive | X | Built differently | Defined an optional review_checklist.md format in the hive repo, which reaches members through the clone on --sync. |
| M141 | Lab policy edition at the managed tier | X | Not built | Not built: this is an enterprise lockdown product that would promise PHI protection with holes (Bash, MCP), well outside a research plugin. |
| M142 | Cross-session loop steering and GitHub event intake | X | Not built | Not built: answers.md and SendMessage already cover steering a loop, and GitHub event intake for local sessions cannot be verified. |

## Guards integrity

| ID | Idea | Tier | Outcome | Note |
|---|---|---|---|---|
| G101 | Hidden-instruction scanner for manuscripts and sources | T2 | In the mod | Documents from outside are scanned with `hidden_text_scan.py` when read; findings follow the Read result as data. |
| G107 | Retraction and correction watch | T2 | In the mod | Once a week the manuscript's DOIs are re-checked for retraction and correction notices. |
| G108 | Citation-claim support check | T2 | Built | Cite only from the project library: phase-paper Approach, a paper-writer Citations section ([CITE] placeholders and a citations table) and /paper Step 1. |
| G109 | Jupyter notebook hygiene | T2 | Built | New Notebooks section in phase-data-analyze: run nbstripout --install (or clear outputs) before committing; notebook outputs are never the results of record; rerun headless with jupyter nbconvert --execute before… |
| G115 | Guard self-protection against the agent | X | Not built | A guard cannot protect itself from an agent with a shell; detection (hash checks, `/sentinel`) backs it instead. |
| G116 | Allocation and counterbalancing ledger | T3 | Built | allocation.py: seeded Williams/Latin/full/block schedules generated once (refuses overwrite) with a sidecar holding seed and hash. |
| G205 | Storage-location probe for network shares and synced folders | T0 | Built | /data step 1 warns when data sit in a synced folder (OneDrive, Dropbox, iCloud Drive, Google Drive) or on a network share (UNC, mapped drive, SMB/NFS), explains the risks, recommends a local working copy, and records… |
| G208 | Research context on the engine's own permission dialog | T2 | In the mod | Every guard finding is attached to the tool call as a notice, also on the permission dialog. |
| G209 | Study-personnel and training check | X | Folded into another | Folded into M021: /data and /experiment now check the ethics approval. |
| M016 | Fail-closed guard kernel | T1 | In the mod | Guards judge before the call, fail closed through `.catch`, resolve real paths and fold Windows case. |
| M017 | Memory-structure purity guard | T1 | In the mod | Writes outside the documented `.neuroflow/` structure warn, using `nf_check.py --structure`. |
| M018 | Preregistration freeze: hash lock, git tag, append-only deviations | T1 | In the mod | Frozen preregistration files are write-protected, `deviations.md` stays append-only, and the dashboard freezes or unfreezes on a key press. |
| M019 | Live preregistration drift detection | T3 | Built | The prereg template ends with a fenced 'yaml prereg-parameters' block: planned_n, stopping_rule, alpha, filters, epoch/baseline, ROIs, windows, tests, exclusions, allocation seed/hash. |
| M020 | Results-first-seen stamp and post-results locks | X | Not built | The stamp would record when Claude saw the results, not the researcher, and needs a registry of confirmatory scripts in data-analyze (outside this package). |
| M021 | Ethics/IRB hard gate with expiry band | T0 | Built | /ethics writes the C2 frontmatter (status, approval_id, expires, ai_processing, set_by, set_at). |
| M022 | Consent immutability, consent-in-force and withdrawals | X | Built differently | The /output --archive 'consent covers sharing' item now also checks that no participant who withdrew consent is in the deposit. |
| M023 | Raw data immutability and per-subject protocol hash | T1 | In the mod | Existing files under `raw_roots` cannot be changed; new recordings may be added. |
| M024 | Plan-before-code gate | X | Not built | Plan-before-code is already prose in phase-data-analyze, brain-build, brain-optimize and brain-run. |
| M025 | Analysis run ledger with result lineage | X | Folded into another | Folded into M125: nf_provenance run records (argv, git, input/output hashes, status) cover background, HPC and terminal runs; datalad run is noted as an equivalent. |
| M026 | Reproducibility lock: environment drift, seed lint, dirty-tree guard | X | Folded into another | Folded into M125: the environment is captured inside scripts, the dirty flag is recorded, and prose says to run confirmatory analyses from a committed tree. |
| M027 | Autoresearch integrity gate and multiverse reporting | T0 | Built | Already implemented in a18358c. |
| M028 | Questionable-request detector | X | Built differently | One line in core Scientific honesty: offer the honest options (deviation via /preregistration, label exploratory, report every variant) and never write the request into project memory. |
| M029 | BIDS guard: inventory, naming, sidecars and validator gate | T0 | Built | Fixed the EEG/MEG/iEEG REQUIRED sidecar tables against BIDS 1.11.2 (fetched from bids-specification.readthedocs.io stable, cited in the files). |
| M030 | Citation existence check at write time | T1 | In the mod | After a turn that wrote a manuscript, grant, poster or report, `cite_check.py` looks up the new DOIs (setting `citations`). |
| M031 | Streaming citation firewall | X | Folded into another | Covered by M030: cite_check.py at --submit, --xray, /grant-proposal, /poster and review, plus the critic's citation-support check (G108). |
| M032 | Statistics firewall: statcheck and number provenance | T2 | Built | New skills/phase-paper/scripts/statcheck.py covers t/F/r/χ²/z, accounts for rounding, skips corrected p and handles one-tailed tests when stated (stdlib, scipy optional); 17 tests. |
| M033 | Spin and claim linter | X | Built differently | humanizer: 'Technical senses are exempt' (significant/significantly for a reported test, robust regression, essential tremor…). |
| M034 | Claim verifier for agent self-reports | T2 | In the mod | A scholar run's closing REPORT line is checked against the files on disk. |
| M035 | Worker-critic referee in code | X | Built differently | Section: and Round: lines added to the worker-critic and paper-writer prompt formats, so rounds can be counted. |
| M036 | Publication tail integrity (--revise, --submit, --abstract) | T2 | Built | New skills/phase-paper/scripts/revise_audit.py diffs the original against the -r1 copy sentence by sentence; every change must be quoted under a comment-id heading in the response, and claimed changes missing from the… |
| M037 | Structured critic verdicts | X | Built differently | paper-critic 'six review areas' changed to eight in both places. |
| M038 | Blind pairwise judge | X | Not built | Niche autoresearch judge: fresh-eval already covers self-grading bias, the autoresearch-protocol skill is outside this package, and resuming the same critic (M087) is what its convergence rule needs. |
| M039 | Human-only overrides, guard registry and override ledger | X | Not built | Unfreezing is simply a person's key press, logged in `deviations.md`. |
| M040 | MCP policy: Sci-Hub blocked, rules in tool descriptions | T0 | Built differently | Prose: never Sci-Hub on any path (search_scihub, check_scihub_mirrors, platform 'scihub' on the 5 tools that accept it, even when asked); get_paper_markdown replaces the nonexistent get_full_text_article in the… |
| M041 | Code-run sentinel with one-click fixes | T2 | Built | New skills/neuroflow-core/scripts/nf_check.py runs checks NF1-NF8. |
| M042 | Hash-chained provenance log and self-writing lab notebook | X | Built differently | No hash chain: it would be unanchored, and git history is already the stronger chain. |
| M043 | AI-use disclosure statement from evidence | T0 | Built | AI-use statement drafted from evidence (sessions/ [paper] lines, critic-log, reasoning/paper.jsonl, git Co-Authored-By trailers) and confirmed by the person: /paper --submit item 6 and /grant-proposal Step 6b. |
| M044 | Acquisition quiet-mode guard | X | Charter rule | Rule 'no agent on the acquisition PC during a recording' added to /experiment ground rules, /tool-validate rules, /tool-build, phase-experiment and phase-tool-validate skills, and the preflight manual checklist. |
| M045 | Preflight gate and digital runbook | X | Built differently | Optional preflight() template for the top of a paradigm: refresh rate, disk space, LSL streams, trigger port, ethics status/expiry, local acquisition-log line, logged override. |
| M046 | Rig registry and rig-aware code checks | X | Built differently | Partial, cheap part only. |
| M047 | Optional-stopping and peeking guard | X | Built | P1-SCI-A owns this idea; per this package's notes I added only the /data-analyze part: a peeking check that reads planned_n from preregistration/status.md and stops before a confirmatory test on fewer participants. |
| M048 | HPC submit guard and job-script linter | X | Built differently | Generic SLURM and PBS Pro/OpenPBS job templates in phase-brain-run/templates: resources from the smoke test, mail on end and failure, optional node-local scratch with copy-back, OMP threads, quoted placeholders (bash… |

## Lifecycle

| ID | Idea | Tier | Outcome | Note |
|---|---|---|---|---|
| G105 | Worktree-aware memory routing | X | Not built | neuroflow creates no worktrees (autoresearch branches are history/ snapshots), and silent path rewrites are riskier than the gitignored session lines they would save. |
| G112 | Reconcile Claude Code's own memories with the research record | X | Built differently | New core rule 'Decisions belong in project memory', plus one line in the always-loaded static .claude/CLAUDE.md block: decisions go to .neuroflow/reasoning/, not auto-memory. |
| G210 | Durability map and research-record vault | X | Built differently | Unpushed commits and last-commit age are doctor lines; no vault. |
| M001 | Phase contract gates | T2 | In the mod | Missing `requires:` inputs are named to the model and the person when a command starts (warn only); `produces`/`next` keys on commands. |
| M002 | Live project-state section in the system prompt | T1 | In the mod | One stable system-prompt section (project, phase, mode, where the truth lives); nothing volatile. |
| M003 | Suppress stale neuroflow instruction blocks; code writes the mirrors | T0 | Built | Removed the ~/.claude/CLAUDE.md step (the root cause) and every copilot-instructions/AGENTS.md mirror. |
| M004 | Command-start context digest | T1 | In the mod | A capped digest of the integrity facts a command reads first follows it as it starts. |
| M005 | Per-phase context packs | X | Folded into another | Folded into M004 and the core rule to re-read project memory after a compaction. |
| M006 | Session log and flow.md written from tool activity | T1 | In the mod | Missing session lines and flow.md rows filled after a command's turn, marked `(auto)`. |
| M007 | Bookkeeping write tools, append-only logs and a bounded decision audit | X | Built differently | Lifecycle profiles fix the git/idk/search exemption contradiction. |
| M008 | Turn-close bookkeeping receipt | X | Not built | Superseded by M006's gap filling; a receipt would misfire on writes made through scripts. |
| M009 | Decision drafter with one-key approval | T2 | In the mod | A decision drafted after a command that logged none, written only after a keep press; keep rate in the doctor. |
| M010 | Orientation from any subfolder and watchers for outside edits | T0 | Built | Walk-up rule added to core (Command lifecycle → Finding the project): first folder whose .neuroflow/ has project_config.md, stopping at the git root, never at or above home; ~/.neuroflow is never a project. |
| M011 | /phase map and phase switch done by code | T2 | In the mod | `/neuroflow:phase` opens a picker (arrows and Enter, or a click); a phase name switches at once and is logged. |
| M012 | Scoped removal of permission friction for bookkeeping | X | Built differently | No permission bypass in the mod; `/neuroflow` can write a native, scoped allow rule instead. |
| M013 | Frustration and fails monitor in code, silent during /idk | X | Built differently | The model stays the detector, in any language. |
| M014 | Lifecycle profiles in command frontmatter | T0 | Built | Core now holds the C6 keys (Command frontmatter standard) and a Lifecycle profiles table (full/light/quiet) that replaces the scattered exceptions; the end-of-command MUSTs follow the profile. |
| M015 | Frontmatter contract enforcement | X | Not built | Enforcing reads/writes as a contract misfires: Bash writes are invisible and core mandates writes no command declares. |

## Live science

| ID | Idea | Tier | Outcome | Note |
|---|---|---|---|---|
| G110 | DataLad-aware provenance | T2 | Built | DataLad note in /data and the bids skill: record .datalad/; use datalad get/run/unlock/rerun instead of a parallel log; on Windows (adjusted branch) 'locked' is no read-only guarantee. |
| G212 | HPC login-node awareness | T2 | In the mod | Heavy compute on an HPC login node asks first; the footer says `login node`. |
| M114 | Long-job runner with run registry and completion wake-up | T2 | Built | Long-run convention in phase-brain-run references/long-runs.md: run_in_background in-session; detached nohup or Start-Process launch that writes <log>.exitcode; preflight; .neuroflow/<phase>/runs.md registry. |
| M115 | LSL and Neon stream monitor | X | Built differently | lsl_check.py: lists resolved streams without opening inlets; only --stream names are measured (rate, gaps, clock offset, latency); prints a multicast/firewall hint. |
| M116 | Recording session cockpit | X | Not built | An XL console on an early-access API during live participant sessions is the wrong place; if ever, a standalone app. |
| M117 | Live scope pane | X | Not built | Vendor viewers and mne-lsl StreamViewer beat a terminal scope. |
| M118 | Montage signal-quality board | X | Not built | Amplifiers already show impedance maps. |
| M119 | Marker-to-photodiode timing validator | T2 | Built | timing_check.py: marker-to-photodiode latency from XDF (pyxdf optional, lazy) or CSV. |
| M120 | Neon cockpit over the Companion HTTP API | X | Not built | The Neon Companion app already shows device status; the existing pupil-labs skill scripts remain. |
| M121 | BrainFlow probe, LSL bridge and synthetic board | X | Not built | The acquisition path must not depend on a hot-reloading session. |
| M122 | Replay mode for hardware-free development | X | Built differently | No replay script. |
| M123 | Preprocessing QC matrix | T2 | Built | qc_table.py builds the subject x metric QC table (markdown and CSV) from per-subject *_qc.json files. |
| M124 | ICA component review pane | X | Built differently | ICA decisions section: the person decides in MNE's interactive views; decisions go to a per-subject *_ica_components.tsv (component/status/status_description/decided_by) that the pipeline reads; n_ica_excluded goes… |
| M125 | Environment manifest and run records written by code | T2 | Built | nf_provenance.py is an importable helper: start/finish or a with-block, declared seeds, and a fallback that still records crashes and missing finish(). |
| M126 | Brain-build smoke lab and smoke tests | X | Built differently | smoke_test.py run/status/check: metrics contract, NaN/runaway/silence and custom *_ok checks, and a smoke record tied to a hash of the model code (results/optimize/compiled folders excluded). |
| M127 | Simulation sanity alarms and spike rasters | X | Built differently | run_sim.py gets in-script guards (non-zero exit with a reason) and writes statistics (rate, CV, Fano, dominant frequency) to a metrics JSON. |
| M128 | Sweep executor and optimizer dashboard with smoke-test gate | T3 | Built | sweep_run.py runs a declared grid and/or explicit points as processes behind a smoke gate (the first or declared smoke configs must exit 0 with a finite metric). |
| M129 | nfview sidecar protocol for terminal science plots | X | Not built | Scripts already save PNGs the model can read. |
| M130 | PsychoPy pilot harness with frame telemetry | X | Built differently | psychopy_audit.py --csv checks a run afterwards. |
| M131 | Closed-loop latency budget monitor | X | Built differently | lsl_check.py --budget-ms reports p50/p95/max latency with a --log CSV. |
| M132 | Institutional memory for errors | X | Not built | Not built: fails/ holds complaints, not fixes. |

## Moonshot

| ID | Idea | Tier | Outcome | Note |
|---|---|---|---|---|
| M188 | $.neuroflow noun: a platform for lab mods | X | Not built | The versioned `.neuroflow/` file format is the extension point, not an API on the engine. |
| M189 | Memory-native compaction (experimental) | X | Not built | Rebuilding the transcript from sparse memory logs is lossier than the engine summary. |
| M190 | Blind analysis mode: outcome statistics masked | X | Not built | Output masking leaks through many paths. |
| M191 | Label-coded blinding for preprocessing decisions | T3 | Built | blind_labels.py blind writes coded copies of *_events.tsv and participants.tsv with random codes. |
| M192 | Forking-paths ledger with an on-demand multiverse | T3 | Built | multiverse.py runs a declared specification grid (dry-run first). |
| M193 | Persistent AI lab-mates with project memory | X | Not built | review-neuro already has statistics and methods reviewers; three new agents and a /lab command are new scope nobody asked for. |
| M194 | Clean-room reproduction gate | T3 | Built | cleanroom.py clones at the recorded commit, then builds the environment from --requirements (venv), --python or --current-python. |
| M195 | Autoresearch branch tournament in worktrees | X | Not built | Breaks autoresearch's one-agent design and its history/ snapshot model, which is not git. |
| M196 | Interactive raw and spike browser as a Client module | X | Not built | MNE raw.plot()/mne-qt-browser over X11 or VNC, or annotate_* functions plus an MNE Report, beat a braille terminal browser. |
| M197 | Drag-and-drop Kanban in the terminal | X | Not built | Not built: /tasks --move already does this in one line; drag-and-drop in a terminal is fragile. |
| M198 | Overnight lab shift with a morning briefing | X | Folded into another | Folded into M220: the overnight budget brake is max_iterations / max_wall_clock / max_cost; report.md (STOPPED line plus open questions) is the morning briefing; /loop covers pacing. |

## Onboarding

| ID | Idea | Tier | Outcome | Note |
|---|---|---|---|---|
| M155 | One-call project scaffold | T0 | Built | New skills/neuroflow-core/scripts/scaffold.py: idempotent and never overwrites. |
| M156 | First-run onboarding and post-setup checklist | X | Built differently | AskUserQuestion for mode, modality and consent, plus a printed post-setup checklist ([x]/[ ]) at the end of /neuroflow. |
| M157 | Command choreography: next-step suggestions and routing | T2 | In the mod | After a command's turn its first `next:` command is offered as the next prompt. |
| M158 | Lab onboarding checklist pane | X | Built differently | New read-only /hive --doctor table with a fix command per row: gh auth, hive cache is a git clone and up to date, sync.json kept local, handle in the roster, project linked, flowie private and fully pushed with an… |
| M159 | Update notifier, what's-new view and derived plugin_version | X | Not built | The marketplace's own update path covers notification; `plugin_version` records which version last wrote a project. |

## Other

| ID | Idea | Tier | Outcome | Note |
|---|---|---|---|---|
| M199 | Lab-level research telemetry via OpenTelemetry | X | Not built | No telemetry. |
| M200 | Compute ledger and infrastructure acknowledgement | X | Built differently | Acknowledgements line in /paper --submit (item 7): wording for compute, core facilities, repositories and gateways comes from provider terms or project notes, never invented. |

## Personalization

| ID | Idea | Tier | Outcome | Note |
|---|---|---|---|---|
| G213 | Language-aware detectors | T0 | Built | Generalized per C9 in core 'Language and neutrality': the model detects signals, mode values and intent in any language; tables are examples ('or the equivalent in the person's language'); never English-only keyword… |
| M143 | Flowie profile as live context with a surface-once ledger | T2 | In the mod | A capped digest of a linked flowie profile (no identity, contact or wellbeing) as a stable section. |
| M144 | Personality modes you can see before you send | T0 | Built | Modes switch only on an explicit 'mode: X' or '--mode X' prefix; mode words in ordinary text ('critical period', 'be careful') never switch. |
| M145 | /idk quiet and sanctuary mode | T0 | Built | /idk now has lifecycle: quiet and writes: []: no monitoring, no session log, no fails/wiki/reasoning writes, no issue URLs. |
| M146 | One-keystroke wellbeing check-in band | T3 | In the mod | An opt-in, self-reported wellbeing check-in on the band; nothing inferred. |
| M147 | Private wellbeing trends and opt-in pace nudges | X | Not built | Not built: the audience is tiny and it only makes sense if wellbeing tracking turns out to be used. |
| M148 | Per-phase effort and model routing | X | Not built | Agent frontmatter and Agent-tool parameters already route models; pinning a judge model in critic frontmatter breaks on custom gateways and changes quality without anyone noticing. |
| M149 | Capture an idea mid-turn | T2 | In the mod | `idea: …` and `/notes --idea` go straight to the ideas inbox. |
| M150 | Phone-aware answers and renderings | X | Not built | Not built: phone use is rare. |
| M151 | Phone companion: status card, approvals and quick capture | X | Not built | Not built: it is an XL multi-surface build, approving tool permissions from a phone is impossible, and answers.md already works over Remote Control. |
| M152 | Interview coach with candidate-data protection | X | Built differently | Candidate notes go only to ~/.neuroflow/private/interviews/: never the repo, .neuroflow/, flowie, a hive or the session log. |
| M153 | Quiz with real scoring and spaced repetition | X | Not built | Not built: it rebuilds Anki for a rarely used command, and /quiz is not in this package. |
| M154 | Weekly review with a personal usage ledger | X | Not built | Not built: the cost figure is notional and no API provides active minutes; booking AI cost into grants is ruled out by M224. |

## Plugin dev

| ID | Idea | Tier | Outcome | Note |
|---|---|---|---|---|
| G122 | Mod-off parity runs | X | Charter rule | Rule written in neuroflow-develop under 'The hooks module': no duty moves into code, and any duty that does must ship with a check that the prose path still meets it with the module off. |
| G125 | Skill-routing observatory and eval capture for the maintainer | X | Built differently | New check V9 fails when a skill folder has a command's name; today that is autoresearch, setup and wiki until the C13 rename. |
| G206 | Guard door-coverage matrix in CI | X | Built differently | The doors guards cannot close are listed in the mod page instead of a test matrix. |
| M173 | Maintainer mode with live validation in the plugin repo | X | Built differently | neuroflow-develop documents an optional Stop hook for each maintainer's own .claude/settings.local.json. |
| M174 | Release cockpit (/nf-release) | X | Built differently | New scripts/automation/bump_version.py bumps the patch version in the four places (or --set, --sync, --check, --dry-run). |
| M175 | Plugin-repo guards: version bump and generated files | X | Built differently | V7 and the pre-push hook now share one list of files that need no version bump (repo_checks; tests/ added to it). |
| M176 | Test suite with a virtual .neuroflow filesystem | T0 | Built | Mod tests run with an in-memory `.neuroflow/` filesystem and Windows path fixtures (`claude plugin test`). |
| M177 | Staged rollout with userConfig runtime off\|observe\|on | T0 | Built | Settings `runtime: off \| observe \| on` (default observe) and `guards: warn \| enforce`. |
| M178 | Repo-local neuroflow-dev mod | T0 | Built | The mod is developed in the repository and loaded with `--plugin-dir`. |
| M179 | Propagation nudges for new commands, skills and agents | X | Built differently | New check V10, run on every PR: every command, skill and agent needs a README row and a mkdocs nav entry, commands and agents must appear in mind.js, and README, nav and mind.js links must resolve. |
| M180 | /nf-new scaffolder with overlap audit | X | Built differently | neuroflow-develop now has propagation checklists for new commands, skills and agents, and its command template includes the C6 keys. |
| M181 | Hot-reload dev loop and dormancy for duplicate copies | X | Built differently | neuroflow-develop Local development now says to run /reload-plugins instead of restarting, offers installing from the working copy (marketplace source './'), and warns against loading two copies at once. |
| M182 | Hook trace pane and one-turn event spy | X | Not built | Not built: premature, since no live module exists to debug. |
| M183 | Context-budget and skill-listing audit | X | Built differently | Acted on the findings instead of building a gauge (/context already shows this): Miro leaves the manifest (integrator request), the notebooklm skill description is shortened from about 523 to about 330 characters, and… |
| M184 | Maintainer inbox: CI, bot reports and agent-PR intake | X | Built differently | New neuroflow-develop section 'Reviewing a contributor PR': fetch the PR into a worktree, run validate_pr.py --base origin/main and the unit tests, read the diff, and merge by hand. |
| M185 | Capability policy and PR capability diff | T0 | Built | `hooks/mod/policy.json` and `mod_policy.py`: anything new the mod does fails CI until reviewed. |
| M186 | API drift radar | T0 | Built | A weekly canary runs the mod's checks on the newest Claude Code release. |
| M187 | Nightly headless smoke tests on fixture projects | X | Not built | Not built: nothing owned by the mod exists yet to assert, and a paid nightly claude -p job would be flaky. |

## Privacy safety

| ID | Idea | Tier | Outcome | Note |
|---|---|---|---|---|
| G103 | Data-route gate: model reads of participant data are transfers | T2 | In the mod | Reads of participant data follow `ai_processing` in the ethics record. |
| G113 | Participant erasure sweep | T2 | Built | /ethics --erase: record the request in erasure-log.md (pseudonymous ID, no names); the person runs the sweep in their own terminal; checklist covers raw/BIDS, derivatives, .neuroflow, git history, Claude Code local… |
| G114 | Cross-plugin data firewall | X | Not built | Other plugins can read files on their own; a firewall would block only polite routes. |
| G126 | Going-public audit | T2 | Built | New history_audit.py scans every commit (git log --all, rev-list --objects, cat-file --batch). |
| G207 | Sharing tiers for memory paths and destinations | T0 | Built | Core 'Sharing tiers' has the C5 table, the scaffold .gitignore lines, and the EGRESS-CONFIRM rule with its marker. |
| M049 | Referee confidentiality gate | T0 | Built | (Part assigned in package notes.) /ideation and phase-ideation: Zotero writes (items, collections, notes, tags, attachments) happen only after the person confirms that write in the same turn, never by default… |
| M050 | Integrations setup with secure secrets and real activation | T0 | Built | /setup never asks for a token, key or client secret in chat. |
| M051 | Secret scrubbing at every door | X | Folded into another | Folded into M050: /setup no longer has users paste tokens into chat, reads integrations.json by key names only, and stores no secrets. |
| M052 | Deterministic PII guard on shared writes | T2 | Built | New pii_scan.py finds emails (ignoring reserved/noreply domains, addresses already in project_config.md, and an allowlist), international phone numbers, ID patterns from the user's config only (none hard-coded;… |
| M053 | Read-side participant-data airlock | X | Built differently | Data minimisation instead of an airlock. |
| M054 | Egress guard with binary header de-identification | T2 | Built | New header_scan.py (stdlib) checks EDF/EDF+/BDF patient and recording subfields (a BIDS sub-label code counts as a pseudonym), BrainVision DataFile/MarkerFile pointers and free text, NIfTI-1/2 (.nii/.nii.gz)… |
| M055 | Exporter that excludes before copying, with archive readiness | T0 | Built | New skills/phase-output/scripts/export.py. |
| M056 | Git guard: staging scan, destructive-command preview, alias scope | T1 | In the mod | `git clean -x`, staging local-only files and work-discarding commands are stopped or asked about. |
| M057 | Share dialogs showing what leaves the machine | X | Built differently | Before acting, an AskUserQuestion with the exact outgoing content in the option preview: the NotebookLM upload list or research query, the /output dry-run plan with held-back reasons, and the flowie sync question. |
| M058 | Hive share outbox via pull requests | X | Built differently | Every hive push is now committed by path, pulled with rebase first and pushed only after an explicit yes. |
| M059 | Profile slicing and profile-leak guard | X | Not built | Theatre: the profile is read by the main loop, not handed to paper-writer, and verbatim shingle matching misses paraphrase; phase-flowie is outside this package. |
| M060 | Personal layer: preferences and consent out of git | T0 | Built | Core section 'Personal layer — ~/.neuroflow/user.yaml': consents and preferences live only there; consent is read only from there; a project default_mode is a team default that a personal value overrides. |
| M061 | Stimulation safety guard with human arming | X | Charter rule | Rule 'no software check, hook or guard is a stimulation-safety interlock; a person starts stimulation; hardware limits, approved protocol and lab procedures protect' in /experiment, /tool-build, /tool-validate and the… |

## Refactor

| ID | Idea | Tier | Outcome | Note |
|---|---|---|---|---|
| G104 | Multi-session write safety for .neuroflow memory | X | Charter rule | Mod-charter rule: no journals or leader election. |
| G117 | Person-presence contract for -p, SDK, desktop and scheduled turns | T0 | Charter rule | Charter: headless means no UI and no questions; guards still deny. |
| G121 | Side-effect ledger with undo and clean disable | X | Charter rule | Charter: no side effects outside the project and the person's own files, so nothing to undo. |
| M160 | Machine-readable integrity state contract | T0 | Built | C2 writers in this package: /ethics writes ethics/status.md frontmatter (set_by semantics, legacy migration); freeze.py writes preregistration/status.md. |
| M161 | Context diet: slice heavy skills and trim the listing | T0 | Built | Done now: the V9 lint reports the three shadowed skills (autoresearch, setup, wiki). |
| M162 | Runtime capability handshake | X | Not built | No duty is delegated to the mod. |
| M163 | Code-answered commands with CI exit codes | T2 | In the mod | `/phase`, `/dashboard`, `/tasks`, `/doctor` and paper status views answered in code, with the prose as fallback. |
| M164 | Generated command manifest and single rules file | X | Folded into another | Covered by M210. |
| M165 | Rule provenance markers | T1 | Built | New check V8. |
| M166 | Feature-module architecture | X | Not built | The engine already nests features, budgets hooks and catches failures; one file per feature is enough. |
| M167 | Typed ProjectSnapshot | T1 | In the mod | A typed snapshot mirrors the `.neuroflow/` files, reloaded when they change; never a second source of truth. |
| M168 | Machine-readable project_config contract and /neuroflow:migrate | T0 | Built | C1 contract text is in core. |
| M169 | Dual-runtime hooks: ruff and flowie ported, shell kept for other hosts | X | Built differently | Shell hooks are kept. |
| M170 | UI kit, screen-space budget and surface tests | X | Not built | No UI kit; the screen budget is a charter rule. |
| M171 | Fan-out protocols as engine Workflow scripts | X | Not built | It would add a third orchestration dialect with same-session-only resume. |
| M172 | nf-sidecar helper and progress protocol | X | Not built | This package uses portable per-skill scripts instead. |

## Tools agents

| ID | Idea | Tier | Outcome | Note |
|---|---|---|---|---|
| M085 | Literature acquisition engine | T0 | Built | Search protocol and scholar rewritten against paper-search-mcp-nodejs 0.3.3 (checked in its dist code): get_platform_status health check; search_crossref / search_semantic_scholar / search_arxiv MCP calls replace raw… |
| M086 | Worker-critic engine run by the mod | X | Built differently | Subagent-waits-for-user bug fixed in prose. |
| M087 | Revise in place by resuming the same agents | T2 | Built | worker-critic Revision mode 'Resume, don't respawn': SendMessage to the round-1 writer and critic agent ids, with a fresh-spawn fallback; the 3-round cap is unchanged. |
| M088 | literature-review as checkpointed protocol spawns | T2 | Built | Removed the reference to a critic agent that does not exist. |
| M089 | review-neuro fan-out in code with progress board and cost preflight | X | Built differently | review-neuro Phase 1 runs at most 4 agents at once, 2 on a custom gateway with a per-key limit (a custom_llm entry, or ANTHROPIC_BASE_URL pointing at a non-Anthropic host). |
| M090 | Tool and agent catalogue curation per phase | X | Built differently | paper-writer frontmatter now sets tools: Read, Glob, Grep (it never writes files; the orchestrator saves). |
| M091 | Context-complete subagents | X | Not built | Agents already read their own context, and injecting house rules into subagents would duplicate session and flow writes. |
| M092 | ask_user bridge and interview engine | T2 | Built | New core rule 'Asking questions': fixed choices use AskUserQuestion (2–4 options, recommended first, tool adds Other). |
| M093 | Wiki tools: page write, lint and branch-safe sync | T0 | Built | Wiki Git sync rewritten: fast-forward-only pull of the current branch from its own upstream (never rebase onto main), no '\|\| true' (conflicts and divergence are reported, never left half-rebased), commits limited to… |
| M094 | Autoresearch transaction tools | T2 | Built | `ar.py` keeps the loop's transaction bookkeeping; the driver reads its status. |
| M095 | Instrument perception tools | X | Not built | Outside P1-LIT: it needs new hardware scripts (pylsl, pupil-labs) under skills/phase-tool-validate, which this package does not own. |
| M096 | Deterministic PsychoPy paradigm audit | T2 | Built | psychopy_audit.py: AST audit of Coder .py and XML audit of .psyexp. |
| M097 | Promote session tasks to the durable board | X | Built differently | Core end step 7: if real research TodoWrite or task items are still open, offer /tasks --add once; never add them unasked. |
| M098 | Zero-turn /git status, alias previews and pair credit | T1 | In the mod | A `/git` alias cannot run git verbs beyond its endpoint. |
| M099 | Finance ledger computed in code | X | Built differently | Fixed the expense table schema (date\|grant\|category\|budget_line\|amount\|currency\|description\|reference, append-only) and added a '## Budget lines' table to budget files. |
| M100 | Poster compile-in-the-loop with pixel critique | T2 | Built | /poster Step 5 compiles (latexmk, with a pdflatex fallback) and renders page 1 at 40 dpi (pdftoppm, mutool or magick) before every critic round, passing the log summary and PNG path. |

## User idea

| ID | Idea | Tier | Outcome | Note |
|---|---|---|---|---|
| U1 | Auto paper: /paper --auto on\|off (living paper skeleton) | T2 | In the mod | Living paper skeleton in prose (`/paper --auto`); the mod answers `--auto status` with a pane and a sync key. |
| U2 | Auto wiki: the project wiki fills itself from sessions, and related pages surface while you work | T2 | In the mod | Auto wiki as a review queue: the mod drafts at most two cards after a logged decision, the person accepts or skips, `/wiki --add` writes. |
| U3 | Paper X-ray (per-sentence paper analysis) | T2 | In the mod | Paper X-ray in prose (`/paper --xray`); the mod shows the findings as a pane to accept or reject, and runs the script checks. |
| U4 | Annotating figure viewer (circle regions on figures) | T3 | Built differently | A figure check in `/data-analyze` with text findings in `figure-notes.md`; no viewer: terminals cannot show figures or take pointer input reliably. |

## Visibility ui

| ID | Idea | Tier | Outcome | Note |
|---|---|---|---|---|
| G118 | Accessible equivalents for every visual | T0 | Charter rule | Charter: every visual has a text form; glyph, word and colour together. |
| G120 | Deliverable viewer for desktop and phone | X | Not built | Its touchpoints (poster, paper, preregistration, data-preprocess and phase commands) belong to other packages. |
| M062 | Phase and mode in the footer, session title and startup notice | T1 | In the mod | Footer label `neuroflow · phase · mode`; no session-title rewrite. |
| M063 | Exception-only status line, health pane and doctor | T1 | In the mod | Exception-only status line and `/neuroflow:doctor` answered in code, with the portable `doctor.py`. |
| M064 | Deadlines and gates band | T1 | Folded into another | Merged into M080's band and the dashboard's deadlines tab. |
| M065 | Slash menu curation and phase-aware typeahead | T2 | In the mod | The slash menu marks the current and the next phase. |
| M066 | Research-aware autocomplete | X | Not built | A per-keystroke hook for a small gain; @-mentions already complete wiki and task paths. |
| M067 | Branded greeting with live version and research vocabulary | X | Not built | No greeting: the mod stays quiet by default. |
| M068 | End-of-command decision band | X | Not built | It only swaps typing Y for pressing a digit and adds a stray-digit hazard; the prose prompt is kept. |
| M069 | On-demand project dashboard pane | T1 | In the mod | `/neuroflow:dashboard`: phase map, deadlines, integrity, tasks and the autoresearch loop. |
| M070 | Native Kanban board pane | T2 | In the mod | `/neuroflow:tasks` opens the project board as a pane; cards move by key press. |
| M071 | Grant word counts and section board | X | Built differently | Grant word counts come from a tool (wc -w), page limits are checked in the funder template, and section drafts are saved to draft-*.md. |
| M072 | Writing boards for worker-critic loops | X | Built differently | critic-log gets one block per section (worker-critic format); /paper already asks the person after the third rejection. |
| M073 | Research-aware transcript rows | X | Not built | It re-skins rows the engine already annotates, and collapsed receipts cannot honour ctrl+o. |
| M074 | Lab-notebook pane with hover provenance | X | Not built | It would be a pane for files already open in Obsidian or an editor, and its key features only work fullscreen; /notes and /write-report cover capture and narrative. |
| M075 | Inline figure previews per surface | X | Not built | Windows Terminal shows alt text instead of images. |
| M076 | Figure gallery pane | X | Built differently | Figure check added to the /paper --submit pre-submission checks: cited figures exist, are cited in order and meet the journal's format rules; uncited figure files are listed. |
| M077 | Parsed scientific CLI output: digests for the model, tables for the person | T2 | Built | bids_digest.py turns bids-validator --json (schema validator and legacy 1.x layouts) into counts per issue code with first locations, plus a summary that omits participant age/sex. |
| M078 | Context, rate-limit and spend meter | X | Not built | Duplicates the status line, /cost and Claude Code's own limit warnings, and per-phase spend is only notional. |
| M079 | Talk preview, lint and rehearsal coach | X | Built differently | The Limitations slide now draws only on preregistration deviations and recorded analysis or manuscript limitations, never on .neuroflow/fails/. |
| M080 | Welcome-back and My Day band | T1 | In the mod | One quiet band above the prompt: deadlines, meetings, drafted decisions, the loop being driven; letter hotkeys. |
| M081 | Selection clipper | X | Not built | Not built: selecting text already copies it, so pasting into /tasks --add or /notes does the same; it would also only work in the fullscreen terminal. |
| M082 | Meeting radar | T2 | In the mod | The band names the next meeting (prepare, notes) and a past one left unclosed (close). |
| M083 | Live progress in the model's Bash rows | X | Built differently | The ~10-minute rule lives in long-runs.md plus pointers in the phase skills: use run_in_background or a detached launch with progress lines. |
| M084 | Autoresearch dashboard pane (retires server.py) | T2 | In the mod | The dashboard's loop tab: iteration, best snapshot, a quality sparkline and open questions. |
