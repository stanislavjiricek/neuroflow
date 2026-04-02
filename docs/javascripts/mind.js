/* ── Neuroflow Mind — interactive universe visualization ──────────────────── */
/* Activated only on the /mind page. Uses D3 v7 (loaded dynamically).        */

(function () {
  "use strict";

  /* ── Graph data ──────────────────────────────────────────────────────────── */
  var NODES = [
    /* ── Core ── */
    {
      id: "core", label: ".neuroflow/", type: "core",
      tags: ["memory"],
      desc: "Shared project memory — the brain that all commands read and write. Stores reasoning logs, session notes, phase folders, and configuration across every session.",
      url: "concepts/project-memory/"
    },

    /* ── Commands ── */
    { id: "cmd-neuroflow",       label: "/neuroflow",       type: "command", phase: "utility",        tags: ["memory","human"],           desc: "Main entry point. Greets you, scans the project, runs the setup interview, and creates the .neuroflow/ memory structure.",                                         url: "commands/neuroflow/" },
    { id: "cmd-setup",           label: "/setup",           type: "command", phase: "utility",        tags: ["memory","human"],           desc: "Reconfigure project settings — updates project_config.md and prompts for any missing metadata.",                                                                  url: "commands/setup/" },
    { id: "cmd-phase",           label: "/phase",           type: "command", phase: "utility",        tags: ["memory"],                   desc: "Show or switch the current research phase. Updates project_config.md and refreshes the flow index.",                                                               url: "commands/phase/" },
    { id: "cmd-search",          label: "/search",          type: "command", phase: "utility",        tags: ["literature","memory"],      desc: "Search PubMed and bioRxiv for relevant literature using PICO queries via the scholar agent.",                                                                      url: "commands/search/" },
    { id: "cmd-sentinel",        label: "/sentinel",        type: "command", phase: "utility",        tags: ["memory"],                   desc: "Audit your project memory — checks for completeness, consistency, and stale entries across all .neuroflow/ subfolders.",                                           url: "commands/sentinel/" },
    { id: "cmd-git",             label: "/git",             type: "command", phase: "utility",        tags: ["code","memory"],            desc: "Version control integration — commit, branch, tag, and review diffs for your research project.",                                                                   url: "commands/git/" },
    { id: "cmd-output",          label: "/output",          type: "command", phase: "output",         tags: ["memory","code"],            desc: "Output project memory or the whole project — pack it as a zip archive or copy it to a target location for sharing, archiving, or handoff.",                      url: "commands/output/" },
    { id: "cmd-interview",       label: "/interview",       type: "command", phase: "utility",        tags: ["human"],                    desc: "Run an interactive interview to capture or update project context stored in project_config.md.",                                                                   url: "commands/interview/" },
    { id: "cmd-quiz",            label: "/quiz",            type: "command", phase: "utility",        tags: ["human","literature"],       desc: "Test your neuroscience knowledge with AI-generated spaced-repetition quizzes tailored to your research domain.",                                                   url: "commands/quiz/" },
    { id: "cmd-fails",           label: "/fails",           type: "command", phase: "utility",        tags: ["human","memory"],           desc: "Log and review failed experiments or analysis attempts. Structured failure reports help avoid repeating mistakes.",                                                 url: "commands/fails/" },
    { id: "cmd-idk",             label: "/idk",             type: "command", phase: "utility",        tags: ["human"],                    desc: "Express and document uncertainty — flags knowledge gaps in project memory so they can be resolved later.",                                                         url: "commands/idk/" },
    { id: "cmd-pipeline",        label: "/pipeline",        type: "command", phase: "utility",        tags: ["memory","code"],            desc: "Multi-step orchestration — chain commands in sequence with optional --nomistake brutal-review mode.",                                                              url: "commands/pipeline/" },
    { id: "cmd-ideation",        label: "/ideation",        type: "command", phase: "ideation",       tags: ["literature","human"],       desc: "Brainstorm research questions, search PubMed and bioRxiv via the scholar agent, and formalize a project proposal.",                                                url: "commands/ideation/" },
    { id: "cmd-preregistration", label: "/preregistration", type: "command", phase: "preregistration",tags: ["writing","stats"],          desc: "Formalize hypotheses and analysis plan before data collection. Generates OSF-compatible preregistration documents.",                                                 url: "commands/preregistration/" },
    { id: "cmd-grant-proposal",  label: "/grant-proposal",  type: "command", phase: "grant-proposal", tags: ["writing"],                  desc: "Write a full grant application — specific aims, significance, innovation, approach, budget, and timeline.",                                                       url: "commands/grant-proposal/" },
    { id: "cmd-finance",         label: "/finance",         type: "command", phase: "finance",        tags: ["writing"],                  desc: "Research budget tracking and financial planning — personnel, equipment, consumables, indirect costs.",                                                              url: "commands/finance/" },
    { id: "cmd-experiment",      label: "/experiment",      type: "command", phase: "experiment",     tags: ["eeg","code"],               desc: "Design a PsychoPy paradigm, define recording parameters, and configure LSL hardware integration for your modality.",                                               url: "commands/experiment/" },
    { id: "cmd-tool-build",      label: "/tool-build",      type: "command", phase: "tool-build",     tags: ["code","eeg"],               desc: "Build custom analysis tools and scripts — MNE pipelines, custom classifiers, or domain-specific utilities.",                                                       url: "commands/tool-build/" },
    { id: "cmd-tool-validate",   label: "/tool-validate",   type: "command", phase: "tool-validate",  tags: ["code","stats"],             desc: "Validate analysis tools with unit tests, benchmarks, and synthetic data to ensure correctness before use on real data.",                                           url: "commands/tool-validate/" },
    { id: "cmd-data",            label: "/data",            type: "command", phase: "data",           tags: ["eeg","fmri","memory"],      desc: "Locate, inventory, validate BIDS structure, and convert raw data formats. Generates a data intake report.",                                                        url: "commands/data/" },
    { id: "cmd-data-preprocess", label: "/data-preprocess", type: "command", phase: "data-preprocess",tags: ["eeg","fmri","code"],        desc: "Build and run a preprocessing pipeline — filtering, ICA, epoching, artifact rejection, and QC reports.",                                                           url: "commands/data-preprocess/" },
    { id: "cmd-data-analyze",    label: "/data-analyze",    type: "command", phase: "data-analyze",   tags: ["stats","ml","eeg"],         desc: "ERPs, time-frequency, connectivity, decoding, GLM — with built-in stats auditing for reproducibility.",                                                           url: "commands/data-analyze/" },
    { id: "cmd-paper",           label: "/paper",           type: "command", phase: "paper",          tags: ["writing","stats"],          desc: "Unified manuscript command — drafts each section with paper-writer, then runs it through paper-critic in a brutal write→critique loop before saving.",              url: "commands/paper/" },
    { id: "cmd-review",          label: "/review",          type: "command", phase: "review",         tags: ["writing","stats"],          desc: "Peer reviewer command — you are the referee. Reads a colleague's paper and produces a structured six-area referee report via the review-neuro skill.",          url: "commands/review/" },
    { id: "cmd-notes",           label: "/notes",           type: "command", phase: "notes",          tags: ["human","memory"],           desc: "Capture session notes, meeting minutes, and ad-hoc observations in structured format to .neuroflow/notes/.",                                                       url: "commands/notes/" },
    { id: "cmd-write-report",    label: "/write-report",    type: "command", phase: "write-report",   tags: ["writing","memory"],         desc: "Generate a project status or phase summary report from .neuroflow/ contents.",                                                                                    url: "commands/write-report/" },
    { id: "cmd-brain-build",     label: "/brain-build",     type: "command", phase: "brain-build",    tags: ["brain-sim","code"],         desc: "Build a computational neural model with NEURON, Brian2, NetPyNE, or NEST.",                                                                                       url: "commands/brain-build/" },
    { id: "cmd-brain-optimize",  label: "/brain-optimize",  type: "command", phase: "brain-optimize", tags: ["brain-sim","stats"],        desc: "Tune model parameters to match experimental data — sensitivity analysis, fitting algorithms.",                                                                     url: "commands/brain-optimize/" },
    { id: "cmd-brain-run",       label: "/brain-run",       type: "command", phase: "brain-run",      tags: ["brain-sim","code"],         desc: "Execute neural simulations and collect output metrics, logs, and visualizations.",                                                                                 url: "commands/brain-run/" },
    { id: "cmd-flowie",          label: "/flowie",          type: "command", phase: "flowie",         tags: ["human","memory"],           desc: "Personal research OS — link a private GitHub repo as identity profile + Kanban task board + project registry with phase tracking. Supports --tasks (board/add/move/done), --projects (list/add), --sync, --link, --init, --identify.",     url: "commands/flowie/" },
    { id: "cmd-hive",            label: "/hive",            type: "command", phase: "hive",           tags: ["memory","human"],           desc: "Connect neuroflow to a shared team GitHub org repo for research direction coordination and explicit knowledge sharing. Never auto-shares personal project data.",                                         url: "commands/hive/" },
    { id: "cmd-slideshow",       label: "/slideshow",       type: "command", phase: "slideshow",      tags: ["writing","human"],          desc: "Build a presentation from selected project areas — pick phases, figures, and key findings, then get a structured slide deck ready to export.",                   url: "commands/slideshow/" },
    { id: "cmd-poster",          label: "/poster",          type: "command", phase: "poster",         tags: ["writing","human"],          desc: "Generate a LaTeX conference poster from project memory — five templates (A0/A1, portrait/landscape, US size), QR code support, and iterative poster-critic review loop.",  url: "commands/poster/" },
    { id: "cmd-autoresearch",    label: "/autoresearch",    type: "command", phase: "utility",        tags: ["memory","code"],            desc: "Infinite improvement loop — point at any files and a worker-evaluator cycle runs indefinitely: one change per iteration, keep or revert, live dashboard at localhost:8765.", url: "commands/autoresearch/" },

    /* ── Skills ── */
    { id: "sk-core",          label: "neuroflow-core",         type: "skill", tags: ["memory"],              desc: "Core lifecycle rules — what every command must read, write, and follow across all phases.",                                           url: "skills/neuroflow-core/SKILL/" },
    { id: "sk-develop",       label: "neuroflow-develop",      type: "skill", tags: ["code","memory"],       desc: "Development guide — how to add new skills, commands, agents, and hooks to the neuroflow plugin.",                                    url: "skills/neuroflow-develop/SKILL/" },
    { id: "sk-creator",       label: "skill-creator",          type: "skill", tags: ["code"],                desc: "Guide for creating and structuring new neuroflow skills, including overlap audits and frontmatter conventions.",                     url: "skills/skill-creator/SKILL/" },
    { id: "sk-ideation",      label: "phase-ideation",         type: "skill", tags: ["literature"],          desc: "Neuroscience ideation best practices — hypothesis formation, literature strategy, feasibility assessment.",                          url: "skills/phase-ideation/SKILL/" },
    { id: "sk-prereg",        label: "phase-preregistration",  type: "skill", tags: ["writing","stats"],     desc: "Preregistration guidelines — OSF templates, CONSORT, STROBE, AsPredicted formats.",                                                url: "skills/phase-preregistration/SKILL/" },
    { id: "sk-grant",         label: "phase-grant-proposal",   type: "skill", tags: ["writing"],             desc: "Grant writing strategy — NIH R01/R21, ERC, Wellcome Trust, DFG formats and review criteria.",                                       url: "skills/phase-grant-proposal/SKILL/" },
    { id: "sk-finance",       label: "phase-finance",          type: "skill", tags: ["writing"],             desc: "Research budget planning and financial compliance — personnel costs, equipment, indirect rates.",                                     url: "skills/phase-finance/SKILL/" },
    { id: "sk-experiment",    label: "phase-experiment",       type: "skill", tags: ["eeg","code"],          desc: "Experiment design — PsychoPy paradigms, LSL hardware integration, BIDS recording parameters.",                                      url: "skills/phase-experiment/SKILL/" },
    { id: "sk-tool-build",    label: "phase-tool-build",       type: "skill", tags: ["code","eeg"],          desc: "Tool development — MNE pipelines, custom analysis scripts, code quality, and documentation.",                                       url: "skills/phase-tool-build/SKILL/" },
    { id: "sk-tool-validate", label: "phase-tool-validate",    type: "skill", tags: ["code","stats"],        desc: "Validation strategies — unit tests, benchmarks, synthetic data, and edge-case coverage.",                                           url: "skills/phase-tool-validate/SKILL/" },
    { id: "sk-data",          label: "phase-data",             type: "skill", tags: ["eeg","fmri","memory"], desc: "Data management — BIDS structure, provenance tracking, format conversion (EDF, BrainVision, NWB).",                                 url: "skills/phase-data/SKILL/" },
    { id: "sk-data-pre",      label: "phase-data-preprocess",  type: "skill", tags: ["eeg","fmri","code"],   desc: "Preprocessing — filtering, ICA, epoching, artifact rejection, channel interpolation, QC.",                                          url: "skills/phase-data-preprocess/SKILL/" },
    { id: "sk-data-analyze",  label: "phase-data-analyze",     type: "skill", tags: ["stats","ml"],          desc: "Analysis methods — ERPs, TFR, connectivity, decoding, GLM, and statistical testing.",                                               url: "skills/phase-data-analyze/SKILL/" },
    { id: "sk-paper",         label: "phase-paper",            type: "skill", tags: ["writing"],             desc: "Unified paper phase — write→critique loop guidance, section order, critic rubric, and critic-log conventions.",                     url: "skills/phase-paper/SKILL/" },
    { id: "sk-phase-review",  label: "phase-review",           type: "skill", tags: ["writing","stats"],     desc: "Peer reviewer orientation — external referee posture, journal calibration, delegation to review-neuro, output to reviews/ folder.", url: "skills/phase-review/SKILL/" },
    { id: "sk-notes",         label: "phase-notes",            type: "skill", tags: ["human"],               desc: "Note-taking conventions — structured session logs, meeting minutes, and observation formats.",                                       url: "skills/phase-notes/SKILL/" },
    { id: "sk-write-report",  label: "phase-write-report",     type: "skill", tags: ["writing"],             desc: "Report generation — executive summaries, phase milestone reports, and stakeholder-ready formats.",                                  url: "skills/phase-write-report/SKILL/" },
    { id: "sk-brain-build",   label: "phase-brain-build",      type: "skill", tags: ["brain-sim"],           desc: "Neural simulation model building — NEURON, Brian2, NetPyNE, NEST, tvb-library model definitions.",                                  url: "skills/phase-brain-build/SKILL/" },
    { id: "sk-brain-opt",     label: "phase-brain-optimize",   type: "skill", tags: ["brain-sim","stats"],   desc: "Model optimization — parameter tuning, sensitivity analysis, fitting algorithms.",                                                  url: "skills/phase-brain-optimize/SKILL/" },
    { id: "sk-brain-run",     label: "phase-brain-run",        type: "skill", tags: ["brain-sim"],           desc: "Simulation execution — runtime configs, parallel runs, output collection and checkpointing.",                                       url: "skills/phase-brain-run/SKILL/" },
    { id: "sk-git",           label: "phase-git",              type: "skill", tags: ["code"],                desc: "Version control conventions — branching strategy, commit message standards, tagging releases.",                                      url: "skills/phase-git/SKILL/" },
    { id: "sk-pipeline",      label: "phase-pipeline",         type: "skill", tags: ["code","memory"],       desc: "Pipeline orchestration — multi-step workflows, dependency ordering, --nomistake strict mode.",                                       url: "skills/phase-pipeline/SKILL/" },
    { id: "sk-search",        label: "phase-search",           type: "skill", tags: ["literature"],          desc: "Literature search — PubMed PICO queries, bioRxiv preprints, synthesis and citation management.",                                    url: "skills/phase-search/SKILL/" },
    { id: "sk-output",        label: "phase-output",           type: "skill", tags: ["code","memory"],       desc: "Output conventions - ZIP archives, folder copies, shareable exports; always excludes credentials and session logs.",                                    url: "skills/phase-output/SKILL/" },
    { id: "sk-fails",         label: "phase-fails",            type: "skill", tags: ["human"],               desc: "Failure logging — structured failure reports, root-cause analysis, lessons learned.",                                               url: "skills/phase-fails/SKILL/" },
    { id: "sk-quiz",          label: "phase-quiz",             type: "skill", tags: ["human"],               desc: "Quiz generation — spaced repetition, domain-specific neuroscience questions, progress tracking.",                                   url: "skills/phase-quiz/SKILL/" },
    { id: "sk-review-neuro",  label: "review-neuro",           type: "skill", tags: ["writing","stats"],     desc: "Expert neuroscience manuscript review — rigorous scientific critique of methods, statistics, and interpretation.",                  url: "skills/review-neuro/SKILL/" },
    { id: "sk-flowie",        label: "phase-flowie",           type: "skill", tags: ["human","memory"],     desc: "Personal research OS skill — read/apply flowie profile, Kanban task context, write rules for .neuroflow/flowie/, GitHub sync protocol, and cross-phase personalization.",                          url: "skills/phase-flowie/SKILL/" },
    { id: "sk-hive",          label: "phase-hive",             type: "skill", tags: ["memory","human"],     desc: "Team-level knowledge layer — connects a researcher's neuroflow project to a shared GitHub org repo for coordinating directions, sharing findings, and team-aware recommendations.",                 url: "skills/phase-hive/SKILL/" },
    { id: "sk-slideshow",     label: "phase-slideshow",        type: "skill", tags: ["writing"],            desc: "Presentation guidance — slide structure decisions, format selection, and audience calibration for building slide decks from project memory.",                                                        url: "skills/phase-slideshow/SKILL/" },
    { id: "sk-poster",        label: "phase-poster",           type: "skill", tags: ["writing"],            desc: "LaTeX poster generation — five conference templates (A0/A1, portrait/landscape, US size), QR code blocks, content extraction from project memory, and compilation instructions.",                 url: "skills/phase-poster/SKILL/" },
    { id: "sk-notebooklm",   label: "notebooklm",             type: "skill", tags: ["literature","human"], desc: "Google NotebookLM integration — create notebooks, add sources, generate podcasts, quizzes, infographics, slide decks, and mind maps from research materials.",                                    url: "skills/notebooklm/SKILL/" },
    { id: "sk-pupil-labs",   label: "pupil-labs-neon",        type: "skill", tags: ["eeg","code"],         desc: "Pupil Labs Neon real-time eye-tracking — connect to Neon glasses and collect live gaze, video, and IMU streams via the Real-time API.",                                                               url: "skills/pupil-labs-neon-realtime/SKILL/" },
    { id: "sk-worker-critic",label: "worker-critic",          type: "skill", tags: ["code"],               desc: "Worker-critic agentic loop — orchestrator coordinates a worker and a critic across up to 3 revision cycles to produce a vetted output for any phase.",                                              url: "skills/worker-critic/SKILL/" },
    { id: "sk-humanizer",    label: "humanizer",              type: "skill", tags: ["writing"],            desc: "Remove AI writing signatures from prose — varied rhythm, natural register, no AI tells. Use when any text needs to read as genuinely human-authored.",                                            url: "skills/humanizer/SKILL/" },
    { id: "sk-setup",          label: "setup",                  type: "skill", tags: ["memory","human"],  desc: "Configure neuroflow integrations — PubMed, Miro, Google Workspace, and custom LLM providers. Use when setting up credentials, checking integration status, or connecting external services.",  url: "skills/setup/SKILL/" },
    { id: "sk-autoresearch",   label: "autoresearch",           type: "skill", tags: ["memory","code"],   desc: "Autoresearch protocol — never-stop loop rules, per-phase criteria, three-layer criteria init, evaluator format, and embedded dashboard server template.",                                    url: "skills/autoresearch/SKILL/" },

    /* ── Agents ── */
    { id: "ag-scholar",      label: "scholar",          type: "agent", tags: ["literature"],         desc: "Literature search specialist — sequential PubMed → bioRxiv pipeline, paper synthesis, batch PDF downloads.",                                                                             url: "concepts/agents/" },
    { id: "ag-sentinel",     label: "sentinel",         type: "agent", tags: ["memory"],             desc: "Audit specialist — project memory completeness, phase consistency, stale-entry detection.",                                                                                              url: "concepts/agents/" },
    { id: "ag-sentinel-dev", label: "sentinel-dev",     type: "agent", tags: ["code","memory"],      desc: "Dev audit specialist — plugin integrity checks, overlap detection, version consistency.",                                                                                                url: "concepts/agents/" },
    { id: "ag-flowie",       label: "flowie",           type: "agent", tags: ["human","memory"],     desc: "Personal identity agent — reads flowie profile and surfaces active tasks for the current project at session start; shapes assistance to the user's intellectual fingerprint.",          url: "concepts/agents/" },
    { id: "ag-paper-writer", label: "paper-writer",     type: "agent", tags: ["writing"],            desc: "Manuscript writer — drafts neuroscience manuscript sections from upstream project memory inside a brutal write→critique loop with the paper-critic agent.",                             url: "concepts/agents/" },
    { id: "ag-paper-critic", label: "paper-critic",     type: "agent", tags: ["writing","stats"],    desc: "Hyper-critical manuscript reviewer — applies full six-area review-neuro methodology to every draft and returns APPROVED or REJECTED with zero tolerance for overclaims.",               url: "concepts/agents/" },
    { id: "ag-lit-review",   label: "literature-review",type: "agent", tags: ["literature"],         desc: "Literature review specialist — runs 12 sequential analytical lenses on downloaded papers using the worker-critic loop to ensure rigour. Scoped to the ideation phase.",                url: "concepts/agents/" },
    { id: "ag-poster-critic",label: "poster-critic",    type: "agent", tags: ["writing"],            desc: "Conference poster critic — audits every LaTeX poster draft across five areas; returns APPROVED or REJECTED with specific, actionable feedback; operates inside the /poster loop.",      url: "concepts/agents/" },
    { id: "ag-autoresearch", label: "autoresearch",     type: "agent", tags: ["memory","code"],      desc: "Infinite loop controller — coordinates the worker-evaluator cycle, keeps or reverts each iteration against history snapshots, manages results.md and the dashboard. Never stops.",      url: "concepts/agents/" }
  ];

  var LINKS = [
    /* Every command reads/writes core */
    { source: "cmd-neuroflow",       target: "core", type: "rw" },
    { source: "cmd-setup",           target: "core", type: "rw" },
    { source: "sk-setup",            target: "cmd-setup", type: "uses" },
    { source: "cmd-phase",           target: "core", type: "rw" },
    { source: "cmd-search",          target: "core", type: "rw" },
    { source: "cmd-sentinel",        target: "core", type: "rw" },
    { source: "cmd-git",             target: "core", type: "rw" },
    { source: "cmd-output",          target: "core", type: "rw" },
    { source: "cmd-flowie",          target: "core", type: "rw" },
    { source: "cmd-hive",            target: "core", type: "rw" },
    { source: "cmd-slideshow",       target: "core", type: "r"  },
    { source: "cmd-poster",          target: "core", type: "rw" },
    { source: "cmd-interview",       target: "core", type: "rw" },
    { source: "cmd-quiz",            target: "core", type: "r"  },
    { source: "cmd-fails",           target: "core", type: "rw" },
    { source: "cmd-idk",             target: "core", type: "rw" },
    { source: "cmd-pipeline",        target: "core", type: "r"  },
    { source: "cmd-ideation",        target: "core", type: "rw" },
    { source: "cmd-preregistration", target: "core", type: "rw" },
    { source: "cmd-grant-proposal",  target: "core", type: "rw" },
    { source: "cmd-finance",         target: "core", type: "rw" },
    { source: "cmd-experiment",      target: "core", type: "rw" },
    { source: "cmd-tool-build",      target: "core", type: "rw" },
    { source: "cmd-tool-validate",   target: "core", type: "rw" },
    { source: "cmd-data",            target: "core", type: "rw" },
    { source: "cmd-data-preprocess", target: "core", type: "rw" },
    { source: "cmd-data-analyze",    target: "core", type: "rw" },
    { source: "cmd-paper",           target: "core", type: "rw" },
    { source: "cmd-review",          target: "core", type: "rw" },
    { source: "cmd-notes",           target: "core", type: "rw" },
    { source: "cmd-write-report",    target: "core", type: "rw" },
    { source: "cmd-brain-build",     target: "core", type: "rw" },
    { source: "cmd-brain-optimize",  target: "core", type: "rw" },
    { source: "cmd-brain-run",       target: "core", type: "rw" },

    /* Commands ↔ Skills */
    { source: "sk-core",          target: "cmd-neuroflow",       type: "uses" },
    { source: "sk-core",          target: "cmd-setup",           type: "uses" },
    { source: "sk-core",          target: "cmd-phase",           type: "uses" },
    { source: "sk-develop",       target: "cmd-neuroflow",       type: "uses" },
    { source: "sk-ideation",      target: "cmd-ideation",        type: "uses" },
    { source: "sk-prereg",        target: "cmd-preregistration", type: "uses" },
    { source: "sk-grant",         target: "cmd-grant-proposal",  type: "uses" },
    { source: "sk-finance",       target: "cmd-finance",         type: "uses" },
    { source: "sk-experiment",    target: "cmd-experiment",      type: "uses" },
    { source: "sk-tool-build",    target: "cmd-tool-build",      type: "uses" },
    { source: "sk-tool-validate", target: "cmd-tool-validate",   type: "uses" },
    { source: "sk-data",          target: "cmd-data",            type: "uses" },
    { source: "sk-data-pre",      target: "cmd-data-preprocess", type: "uses" },
    { source: "sk-data-analyze",  target: "cmd-data-analyze",    type: "uses" },
    { source: "sk-paper",         target: "cmd-paper",           type: "uses" },
    { source: "sk-phase-review",  target: "cmd-review",          type: "uses" },
    { source: "sk-notes",         target: "cmd-notes",           type: "uses" },
    { source: "sk-write-report",  target: "cmd-write-report",    type: "uses" },
    { source: "sk-brain-build",   target: "cmd-brain-build",     type: "uses" },
    { source: "sk-brain-opt",     target: "cmd-brain-optimize",  type: "uses" },
    { source: "sk-brain-run",     target: "cmd-brain-run",       type: "uses" },
    { source: "sk-git",           target: "cmd-git",             type: "uses" },
    { source: "sk-pipeline",      target: "cmd-pipeline",        type: "uses" },
    { source: "sk-search",        target: "cmd-search",          type: "uses" },
    { source: "sk-output",        target: "cmd-output",          type: "uses" },
    { source: "sk-fails",          target: "cmd-fails",           type: "uses" },
    { source: "sk-quiz",           target: "cmd-quiz",            type: "uses" },
    { source: "sk-flowie",         target: "cmd-flowie",          type: "uses" },
    { source: "sk-hive",           target: "cmd-hive",            type: "uses" },
    { source: "sk-slideshow",      target: "cmd-slideshow",       type: "uses" },
    { source: "sk-poster",         target: "cmd-poster",          type: "uses" },

    /* Commands → Agents (spawns) */
    { source: "cmd-ideation",        target: "ag-scholar",       type: "spawns" },
    { source: "cmd-search",          target: "ag-scholar",       type: "spawns" },
    { source: "cmd-sentinel",        target: "ag-sentinel",      type: "spawns" },
    { source: "cmd-flowie",          target: "ag-flowie",        type: "spawns" },
    { source: "cmd-paper",           target: "ag-paper-writer",  type: "spawns" },
    { source: "cmd-paper",           target: "ag-paper-critic",  type: "spawns" },
    { source: "cmd-poster",          target: "ag-poster-critic", type: "spawns" },
    { source: "cmd-ideation",        target: "ag-lit-review",    type: "spawns" },
    { source: "cmd-autoresearch",    target: "ag-autoresearch",  type: "spawns" },

    /* Autoresearch */
    { source: "cmd-autoresearch",    target: "core",              type: "rw" },
    { source: "sk-autoresearch",     target: "cmd-autoresearch",  type: "uses" },

    /* Pipeline orchestrates many commands */
    { source: "cmd-pipeline", target: "cmd-ideation",        type: "orchestrates" },
    { source: "cmd-pipeline", target: "cmd-data-preprocess", type: "orchestrates" },
    { source: "cmd-pipeline", target: "cmd-data-analyze",    type: "orchestrates" },
    { source: "cmd-pipeline", target: "cmd-paper",         type: "orchestrates" }
  ];

  /* ── Visual config ───────────────────────────────────────────────────────── */
  var TYPE_CONFIG = {
    core:    { color: "#ce93d8", glow: "#9c27b0", radius: 28, ring: 0 },
    command: { color: "#7c4dff", glow: "#651fff", radius: 12, ring: 1 },
    skill:   { color: "#26c6da", glow: "#00acc1", radius: 9,  ring: 2 },
    agent:   { color: "#66bb6a", glow: "#43a047", radius: 9,  ring: 3 }
  };

  /* ── Tag receptor colors ─────────────────────────────────────────────────── */
  /* Each tag is shown as a small colored dot (receptor) on the node surface.  */
  var TAG_CONFIG = {
    "memory":    { color: "#ce93d8", label: "memory" },
    "literature":{ color: "#ffd54f", label: "literature" },
    "eeg":       { color: "#26c6da", label: "EEG / ephys" },
    "fmri":      { color: "#ef5350", label: "fMRI / imaging" },
    "brain-sim": { color: "#ec407a", label: "brain simulation" },
    "stats":     { color: "#ffa726", label: "statistics" },
    "ml":        { color: "#42a5f5", label: "machine learning" },
    "code":      { color: "#66bb6a", label: "code / tools" },
    "writing":   { color: "#ab47bc", label: "scientific writing" },
    "human":     { color: "#ff7043", label: "human interaction" }
  };

  var LINK_COLORS = {
    rw:           "rgba(206,147,216,0.45)",
    r:            "rgba(206,147,216,0.25)",
    uses:         "rgba(38,198,218,0.35)",
    spawns:       "rgba(102,187,106,0.4)",
    orchestrates: "rgba(255,183,77,0.35)"
  };

  /* ── Phase / cluster layout ───────────────────────────────────────────────── */
  /* Clockwise degrees from 12 o'clock for each research phase.
     Nodes are pulled toward their phase angle in concentric arcs
     (commands inner, skills middle, agents outer).
     Cycle: utility → ideation → … → review → back to utility.        */
  var PHASE_ANGLES = {
    "ideation":        15,
    "preregistration": 42,
    "grant-proposal":  65,
    "finance":         88,
    "experiment":      112,
    "tool-build":      135,
    "tool-validate":   158,
    "data":            180,
    "data-preprocess": 202,
    "data-analyze":    224,
    "brain-build":     248,
    "brain-optimize":  262,
    "brain-run":       276,
    "paper":           298,
    "notes":           310,
    "write-report":    318,
    "review":          332,
    "slideshow":       338,
    "poster":          341,
    "output":          344,
    "utility":         350,
    "hive":            355,
    "flowie":          359
  };

  /* Phase for each skill / agent node (commands already carry d.phase) */
  var NODE_PHASE_MAP = {
    "sk-core":          "utility",
    "sk-develop":       "utility",
    "sk-creator":       "utility",
    "sk-setup":         "utility",
    "sk-ideation":      "ideation",
    "sk-prereg":        "preregistration",
    "sk-grant":         "grant-proposal",
    "sk-finance":       "finance",
    "sk-experiment":    "experiment",
    "sk-tool-build":    "tool-build",
    "sk-tool-validate": "tool-validate",
    "sk-data":          "data",
    "sk-data-pre":      "data-preprocess",
    "sk-data-analyze":  "data-analyze",
    "sk-paper":         "paper",
    "sk-phase-review":  "review",
    "sk-notes":         "notes",
    "sk-write-report":  "write-report",
    "sk-brain-build":   "brain-build",
    "sk-brain-opt":     "brain-optimize",
    "sk-brain-run":     "brain-run",
    "sk-git":           "utility",
    "sk-pipeline":      "utility",
    "sk-search":        "utility",
    "sk-output":        "output",
    "sk-fails":         "utility",
    "sk-quiz":          "utility",
    "sk-review-neuro":  "review",
    "ag-ideation":      "ideation",
    "sk-notebooklm":    "utility",
    "sk-pupil-labs":    "experiment",
    "sk-worker-critic": "utility",
    "ag-flowie":        "flowie",
    "ag-orchestrator":  "utility",
    "ag-paper-writer":  "paper",
    "ag-paper-critic":  "paper",
    "ag-lit-review":    "ideation",
    "sk-poster":        "poster",
    "ag-poster-critic": "poster"
  };

  /* ── State ───────────────────────────────────────────────────────────────── */
  var simulation = null;
  var selectedId = null;

  /* ── Main init (called after D3 loaded) ─────────────────────────────────── */
  function initMindGraph() {
    var root = document.getElementById("nf-mind-root");
    if (!root) return;

    /* Clear any previous render (instant-nav support) — remove only the SVG
       and panel so the topbar / back-to-docs buttons are preserved. */
    root.querySelectorAll("svg, #nf-mind-panel").forEach(function(el) { el.remove(); });

    var W = root.clientWidth  || window.innerWidth;
    var H = root.clientHeight || window.innerHeight - 60;

    /* ── SVG setup ── */
    var svg = d3.select(root).append("svg")
      .attr("width",  "100%")
      .attr("height", "100%")
      .attr("viewBox", "0 0 " + W + " " + H)
      .style("display", "block");

    /* ── Defs: glow filters ── */
    var defs = svg.append("defs");

    function addGlow(id, color, blur, strength) {
      var f = defs.append("filter").attr("id", id).attr("x", "-50%").attr("y", "-50%").attr("width", "200%").attr("height", "200%");
      f.append("feGaussianBlur").attr("in", "SourceGraphic").attr("stdDeviation", blur).attr("result", "blur");
      var feMerge = f.append("feMerge");
      for (var i = 0; i < strength; i++) feMerge.append("feMergeNode").attr("in", "blur");
      feMerge.append("feMergeNode").attr("in", "SourceGraphic");
    }

    addGlow("glow-core",    "#9c27b0", 10, 3);
    addGlow("glow-command", "#651fff", 6,  2);
    addGlow("glow-skill",   "#00acc1", 5,  2);
    addGlow("glow-agent",   "#43a047", 5,  2);
    addGlow("glow-select",  "#ffffff", 8,  4);

    /* ── Starfield background ── */
    var bg = svg.append("g").attr("class", "nf-stars");
    var rng = mulberry32(42);
    for (var s = 0; s < 220; s++) {
      bg.append("circle")
        .attr("cx", rng() * W)
        .attr("cy", rng() * H)
        .attr("r",  rng() * 1.4 + 0.2)
        .attr("fill", "rgba(255,255,255," + (rng() * 0.35 + 0.05) + ")");
    }

    /* ── Legend ── */
    var legend = svg.append("g").attr("transform", "translate(20,20)");
    var legendItems = [
      { type: "core",    label: "project memory" },
      { type: "command", label: "commands" },
      { type: "skill",   label: "skills" },
      { type: "agent",   label: "agents" }
    ];
    legendItems.forEach(function(item, i) {
      var g = legend.append("g").attr("transform", "translate(0," + (i * 22) + ")");
      g.append("circle").attr("r", 6).attr("cx", 7).attr("cy", 7)
        .attr("fill", TYPE_CONFIG[item.type].color)
        .attr("filter", "url(#glow-" + item.type + ")");
      g.append("text").attr("x", 18).attr("y", 11)
        .attr("fill", "rgba(255,255,255,0.65)")
        .attr("font-size", "11px")
        .attr("font-family", "Inter, sans-serif")
        .text(item.label);
    });

    /* ── Tag receptor legend (top-right) ── */
    var tagKeys = Object.keys(TAG_CONFIG);
    var tagLegend = svg.append("g").attr("transform", "translate(" + (W - 145) + ",20)");
    tagLegend.append("text")
      .attr("x", 0).attr("y", 0)
      .attr("fill", "rgba(255,255,255,0.4)")
      .attr("font-size", "10px")
      .attr("font-family", "Inter, sans-serif")
      .attr("font-weight", "600")
      .attr("letter-spacing", "0.08em")
      .text("DOMAIN TAGS");
    tagKeys.forEach(function(key, i) {
      var g = tagLegend.append("g").attr("transform", "translate(0," + (14 + i * 18) + ")");
      g.append("circle").attr("r", 3.5).attr("cx", 4).attr("cy", 5)
        .attr("fill", TAG_CONFIG[key].color)
        .attr("opacity", 0.9);
      g.append("text").attr("x", 13).attr("y", 9)
        .attr("fill", "rgba(255,255,255,0.5)")
        .attr("font-size", "10px")
        .attr("font-family", "Inter, sans-serif")
        .text(TAG_CONFIG[key].label);
    });

    /* ── Link type hint ── */
    var hint = svg.append("g").attr("transform", "translate(20," + (H - 90) + ")");
    var hintItems = [
      { color: LINK_COLORS.rw,           label: "reads & writes" },
      { color: LINK_COLORS.uses,         label: "skill used by command" },
      { color: LINK_COLORS.spawns,       label: "spawns agent" },
      { color: LINK_COLORS.orchestrates, label: "orchestrates" }
    ];
    hintItems.forEach(function(item, i) {
      var g = hint.append("g").attr("transform", "translate(0," + (i * 18) + ")");
      g.append("line").attr("x1", 0).attr("y1", 7).attr("x2", 22).attr("y2", 7)
        .attr("stroke", item.color).attr("stroke-width", 2);
      g.append("text").attr("x", 28).attr("y", 11)
        .attr("fill", "rgba(255,255,255,0.5)")
        .attr("font-size", "10px")
        .attr("font-family", "Inter, sans-serif")
        .text(item.label);
    });

    /* ── Build graph data ── */
    var nodeMap = {};
    var nodes = NODES.map(function(n) {
      var nd = Object.assign({}, n);
      nodeMap[n.id] = nd;
      return nd;
    });

    var links = LINKS.map(function(l) {
      return { source: l.source, target: l.target, type: l.type };
    });

    /* ── Cluster layout helpers ── */
    /* Orbit radii scale with the smaller viewport dimension so nodes always
       fit on screen; commands innermost, skills middle, agents outermost.  */
    var viewportR = Math.min(W, H) / 2;

    function nodePhase(d) {
      return NODE_PHASE_MAP[d.id] || d.phase || "utility";
    }

    function clusterAngleRad(d) {
      var ph = nodePhase(d);
      var deg = PHASE_ANGLES[ph] !== undefined ? PHASE_ANGLES[ph] : PHASE_ANGLES["utility"];
      /* Convert clockwise-from-12 degrees → SVG radians (0 = right, CW = +) */
      return (deg - 90) * Math.PI / 180;
    }

    function clusterRadius(d) {
      if (d.type === "core")    return 0;
      if (d.type === "command") return viewportR * 0.48;
      if (d.type === "skill")   return viewportR * 0.70;
      if (d.type === "agent")   return viewportR * 0.90;
      return viewportR * 0.70;
    }

    function clusterX(d) {
      if (d.type === "core") return W / 2;
      return W / 2 + clusterRadius(d) * Math.cos(clusterAngleRad(d));
    }

    function clusterY(d) {
      if (d.type === "core") return H / 2;
      return H / 2 + clusterRadius(d) * Math.sin(clusterAngleRad(d));
    }

    /* Pre-position nodes near their cluster target so layout is stable
       from the very first frame (uses a seeded RNG for reproducibility). */
    var rng2 = mulberry32(99);
    nodes.forEach(function(d) {
      if (d.type !== "core") {
        d.x = clusterX(d) + (rng2() - 0.5) * 20;
        d.y = clusterY(d) + (rng2() - 0.5) * 20;
      }
    });

    /* ── Force simulation ── */
    simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id(function(d) { return d.id; }).distance(function(d) {
        if (d.type === "rw" || d.type === "r") return 70;
        if (d.type === "uses")     return 65;
        if (d.type === "spawns")   return 60;
        return 90;
      }).strength(0.7))
      .force("charge", d3.forceManyBody().strength(function(d) {
        return d.type === "core" ? -500 : -60;
      }))
      /* Per-node attraction toward phase cluster target — replaces forceCenter */
      .force("x", d3.forceX(function(d) { return clusterX(d); }).strength(0.22))
      .force("y", d3.forceY(function(d) { return clusterY(d); }).strength(0.22))
      /* Tighter collision buffer (8 vs previous 10) — nodes intentionally
         pack closer within a cluster; forceX/Y prevents runaway separation. */
      .force("collision", d3.forceCollide().radius(function(d) {
        return TYPE_CONFIG[d.type].radius + 8;
      }))
      .alphaDecay(0.018)
      .velocityDecay(0.38);

    /* Fix core at center */
    var coreNode = nodeMap["core"];
    coreNode.fx = W / 2;
    coreNode.fy = H / 2;

    /* ── Draw links ── */
    var linkG = svg.append("g").attr("class", "nf-links");
    var linkSel = linkG.selectAll("line")
      .data(links)
      .enter().append("line")
      .attr("stroke", function(d) { return LINK_COLORS[d.type] || "rgba(255,255,255,0.2)"; })
      .attr("stroke-width", function(d) {
        return (d.type === "rw") ? 1.5 : 1;
      })
      .attr("stroke-dasharray", function(d) {
        return d.type === "uses" ? "4,3" : null;
      })
      .attr("class", "nf-link");

    /* ── Draw nodes ── */
    var nodeG = svg.append("g").attr("class", "nf-nodes");
    var nodeSel = nodeG.selectAll("g.nf-node")
      .data(nodes)
      .enter().append("g")
      .attr("class", "nf-node")
      .style("cursor", "pointer")
      .call(d3.drag()
        .on("start", dragStarted)
        .on("drag",  dragged)
        .on("end",   dragEnded))
      .on("click",     onNodeClick)
      .on("mouseover", onNodeOver)
      .on("mouseout",  onNodeOut);

    /* Outer glow ring (hidden by default, shown on hover/select) */
    nodeSel.append("circle")
      .attr("class", "nf-node-ring")
      .attr("r", function(d) { return TYPE_CONFIG[d.type].radius + 6; })
      .attr("fill", "none")
      .attr("stroke", function(d) { return TYPE_CONFIG[d.type].color; })
      .attr("stroke-width", 1.5)
      .attr("opacity", 0);

    /* Main circle */
    nodeSel.append("circle")
      .attr("class", "nf-node-circle")
      .attr("r", function(d) { return TYPE_CONFIG[d.type].radius; })
      .attr("fill", function(d) { return TYPE_CONFIG[d.type].color; })
      .attr("filter", function(d) { return "url(#glow-" + d.type + ")"; })
      .attr("opacity", 0.92);

    /* Core pulse ring */
    nodeSel.filter(function(d) { return d.type === "core"; })
      .append("circle")
      .attr("class", "nf-core-pulse")
      .attr("r", 28)
      .attr("fill", "none")
      .attr("stroke", "#ce93d8")
      .attr("stroke-width", 1.5)
      .attr("opacity", 0.5);

    /* ── Tag receptor dots ── */
    /* For each node, draw small colored dots evenly around the outer edge
       of the main circle — one dot per tag, like membrane receptors.        */
    /* TAG_START_ANGLE: -π/2 rotates the first dot to the 12 o'clock
       position in SVG coordinates (where 0 rad = 3 o'clock).               */
    var TAG_START_ANGLE = -Math.PI / 2;
    nodeSel.each(function(d) {
      var tags = d.tags || [];
      if (!tags.length) return;
      var n = tags.length;
      var nodeR = TYPE_CONFIG[d.type].radius;
      /* Receptor dots sit just outside the node circle */
      var dotR = d.type === "core" ? 5 : 3;
      var orbitR = nodeR + dotR + 2;
      tags.forEach(function(tag, i) {
        var angle = TAG_START_ANGLE + (i / n) * 2 * Math.PI;
        var cx = Math.cos(angle) * orbitR;
        var cy = Math.sin(angle) * orbitR;
        var tagCfg = TAG_CONFIG[tag] || { color: "#ffffff" };
        d3.select(this).append("circle")
          .attr("class", "nf-tag-dot")
          .attr("cx", cx)
          .attr("cy", cy)
          .attr("r", dotR)
          .attr("fill", tagCfg.color)
          .attr("stroke", "rgba(0,0,0,0.4)")
          .attr("stroke-width", 0.5)
          .attr("opacity", 0.9)
          .attr("pointer-events", "none");
      });
    });

    /* Labels — offset clears both the node circle and any receptor dots.
       dot orbit max = radius + 2*dotR + 2 ≈ radius+8, so radius+14 is safe. */
    nodeSel.append("text")
      .attr("class", "nf-node-label")
      .attr("dy", function(d) {
        /* Receptor dot orbit sits at nodeR + dotR + 2; add clearance */
        var dotR = d.type === "core" ? 5 : 3;
        return TYPE_CONFIG[d.type].radius + dotR + 6;
      })
      .attr("text-anchor", "middle")
      .attr("font-size", function(d) { return d.type === "core" ? "13px" : "10px"; })
      .attr("font-weight", function(d) { return d.type === "core" ? "700" : "500"; })
      .attr("font-family", "Inter, JetBrains Mono, monospace")
      .attr("fill", function(d) { return d.type === "core" ? "#e1bee7" : "rgba(255,255,255,0.72)"; })
      .attr("pointer-events", "none")
      .text(function(d) { return d.label; });

    /* ── Info panel ── */
    var panel = document.createElement("div");
    panel.id = "nf-mind-panel";
    panel.className = "nf-mind-panel";
    panel.innerHTML = '<div class="nf-mind-panel-inner">' +
      '<button class="nf-mind-close" aria-label="Close panel">✕</button>' +
      '<span class="nf-mind-panel-type"></span>' +
      '<h3 class="nf-mind-panel-title"></h3>' +
      '<p class="nf-mind-panel-desc"></p>' +
      '<div class="nf-mind-panel-tags"></div>' +
      '<div class="nf-mind-panel-connections"></div>' +
      '<a class="nf-mind-panel-link md-button md-button--primary" href="#" target="_self">View docs →</a>' +
      '</div>';
    root.appendChild(panel);

    panel.querySelector(".nf-mind-close").addEventListener("click", function() {
      closePanel();
    });

    /* ── Zoom & pan ── */
    var zoom = d3.zoom()
      .scaleExtent([0.3, 3])
      .on("zoom", function(event) {
        linkG.attr("transform", event.transform);
        nodeG.attr("transform", event.transform);
      });
    svg.call(zoom);

    /* ── Tick ── */
    simulation.on("tick", function() {
      linkSel
        .attr("x1", function(d) { return d.source.x; })
        .attr("y1", function(d) { return d.source.y; })
        .attr("x2", function(d) { return d.target.x; })
        .attr("y2", function(d) { return d.target.y; });

      nodeSel.attr("transform", function(d) {
        return "translate(" + d.x + "," + d.y + ")";
      });
    });

    /* ── Core pulse animation ── */
    animatePulse();

    /* ── Helpers ── */

    function onNodeClick(event, d) {
      event.stopPropagation();
      if (selectedId === d.id) {
        closePanel();
        return;
      }
      selectedId = d.id;
      showPanel(d);
      highlightConnected(d.id);
    }

    function onNodeOver(event, d) {
      if (selectedId) return;
      d3.select(this).select(".nf-node-ring").attr("opacity", 0.6);
      d3.select(this).select(".nf-node-circle").attr("opacity", 1);
      highlightConnected(d.id);
    }

    function onNodeOut(event, d) {
      if (selectedId) return;
      d3.select(this).select(".nf-node-ring").attr("opacity", 0);
      resetHighlight();
    }

    function highlightConnected(nodeId) {
      var connectedIds = new Set([nodeId]);
      var connectedLinkTypes = {};

      links.forEach(function(l) {
        var srcId = l.source.id || l.source;
        var tgtId = l.target.id || l.target;
        if (srcId === nodeId || tgtId === nodeId) {
          connectedIds.add(srcId);
          connectedIds.add(tgtId);
          connectedLinkTypes[srcId + "__" + tgtId] = l.type;
        }
      });

      nodeSel.each(function(d) {
        var connected = connectedIds.has(d.id);
        d3.select(this).select(".nf-node-circle")
          .transition().duration(200)
          .attr("opacity", connected ? 1 : 0.15);
        d3.select(this).select(".nf-node-label")
          .transition().duration(200)
          .attr("opacity", connected ? 1 : 0.15);
        d3.select(this).select(".nf-node-ring")
          .attr("opacity", d.id === nodeId ? 0.7 : (connected ? 0.35 : 0));
      });

      linkSel.transition().duration(200)
        .attr("opacity", function(l) {
          var srcId = l.source.id || l.source;
          var tgtId = l.target.id || l.target;
          return (srcId === nodeId || tgtId === nodeId) ? 1 : 0.05;
        })
        .attr("stroke-width", function(l) {
          var srcId = l.source.id || l.source;
          var tgtId = l.target.id || l.target;
          return (srcId === nodeId || tgtId === nodeId) ? 2.5 : 1;
        });
    }

    function resetHighlight() {
      nodeSel.each(function(d) {
        d3.select(this).select(".nf-node-circle").transition().duration(200).attr("opacity", 0.92);
        d3.select(this).select(".nf-node-label").transition().duration(200).attr("opacity", 1);
        d3.select(this).select(".nf-node-ring").attr("opacity", 0);
      });
      linkSel.transition().duration(200).attr("opacity", 1).attr("stroke-width", function(d) {
        return d.type === "rw" ? 1.5 : 1;
      });
    }

    function showPanel(d) {
      var cfg = TYPE_CONFIG[d.type];
      var typeLabels = { core: "PROJECT MEMORY", command: "COMMAND", skill: "SKILL", agent: "AGENT" };

      panel.querySelector(".nf-mind-panel-type").textContent = typeLabels[d.type] || d.type.toUpperCase();
      panel.querySelector(".nf-mind-panel-type").style.color = cfg.color;
      panel.querySelector(".nf-mind-panel-title").textContent = d.label;
      panel.querySelector(".nf-mind-panel-desc").textContent = d.desc;

      /* Tags */
      var tagsDiv = panel.querySelector(".nf-mind-panel-tags");
      var tags = d.tags || [];
      if (tags.length) {
        var tagHtml = '<p class="nf-conn-heading">Domain tags</p><div class="nf-tag-pills">';
        tags.forEach(function(tag) {
          var tagCfg = TAG_CONFIG[tag] || { color: "#fff", label: tag };
          tagHtml += '<span class="nf-tag-pill" style="border-color:' + tagCfg.color + ';color:' + tagCfg.color + '">' +
            '<span class="nf-tag-dot-sm" style="background:' + tagCfg.color + '"></span>' +
            tagCfg.label + '</span>';
        });
        tagHtml += '</div>';
        tagsDiv.innerHTML = tagHtml;
      } else {
        tagsDiv.innerHTML = "";
      }

      /* Connections list */
      var connDiv = panel.querySelector(".nf-mind-panel-connections");
      var connectedNodes = [];
      links.forEach(function(l) {
        var srcId = l.source.id || l.source;
        var tgtId = l.target.id || l.target;
        var other = null;
        var rel = "";
        if (srcId === d.id) { other = nodeMap[tgtId]; rel = relLabel(l.type, "out"); }
        else if (tgtId === d.id) { other = nodeMap[srcId]; rel = relLabel(l.type, "in"); }
        if (other) connectedNodes.push({ node: other, rel: rel });
      });

      if (connectedNodes.length) {
        var html = '<p class="nf-conn-heading">Connections (' + connectedNodes.length + ')</p><ul class="nf-conn-list">';
        connectedNodes.forEach(function(cn) {
          html += '<li><span style="color:' + TYPE_CONFIG[cn.node.type].color + '">◆</span> ' +
            '<span class="nf-conn-rel">' + cn.rel + '</span> ' +
            '<strong>' + cn.node.label + '</strong></li>';
        });
        html += '</ul>';
        connDiv.innerHTML = html;
      } else {
        connDiv.innerHTML = "";
      }

      /* Doc link — build relative URL from base */
      var base = document.querySelector("base") ? document.querySelector("base").href : "/";
      var link = panel.querySelector(".nf-mind-panel-link");
      if (d.url) {
        /* Determine site root by stripping /mind/ path segment */
        var currentPath = window.location.pathname;
        var siteRoot = currentPath.replace(/\/mind\/?$/, "/");
        link.href = siteRoot + d.url;
        link.style.display = "";
      } else {
        link.style.display = "none";
      }

      panel.classList.add("nf-mind-panel--open");
    }

    function closePanel() {
      selectedId = null;
      panel.classList.remove("nf-mind-panel--open");
      resetHighlight();
    }

    function relLabel(type, dir) {
      if (type === "rw")   return dir === "out" ? "reads & writes" : "read & written by";
      if (type === "r")    return dir === "out" ? "reads" : "read by";
      if (type === "uses") return dir === "out" ? "skill informs" : "guided by skill";
      if (type === "spawns") return dir === "out" ? "spawns" : "spawned by";
      if (type === "orchestrates") return dir === "out" ? "orchestrates" : "orchestrated by";
      return type;
    }

    /* Click on empty area closes panel */
    svg.on("click", function() {
      if (selectedId) closePanel();
    });

    /* ── Drag ── */
    function dragStarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      if (d.type !== "core") { d.fx = d.x; d.fy = d.y; }
    }
    function dragged(event, d) {
      if (d.type !== "core") { d.fx = event.x; d.fy = event.y; }
    }
    function dragEnded(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      if (d.type !== "core") { d.fx = null; d.fy = null; }
    }

    /* ── Pulse animation ── */
    function animatePulse() {
      svg.selectAll(".nf-core-pulse")
        .transition().duration(2000).ease(d3.easeSinInOut)
        .attr("r", 48).attr("opacity", 0)
        .transition().duration(0)
        .attr("r", 28).attr("opacity", 0.5)
        .on("end", animatePulse);
    }
  }

  /* ── Seeded PRNG for deterministic stars ─────────────────────────────────── */
  function mulberry32(seed) {
    return function() {
      seed |= 0; seed = seed + 0x6D2B79F5 | 0;
      var t = Math.imul(seed ^ seed >>> 15, 1 | seed);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }

  /* ── D3 loader ───────────────────────────────────────────────────────────── */
  function loadD3AndInit() {
    if (!document.getElementById("nf-mind-root")) return;
    if (window.d3) { initMindGraph(); return; }

    /* Determine the base path of the site so the local bundle path resolves
       correctly whether the site is served from / or a sub-path (e.g. /neuroflow/). */
    var base = document.querySelector("base");
    var basePath = base ? base.href : "/";
    /* Strip trailing slash so we can append cleanly */
    basePath = basePath.replace(/\/$/, "");

    var s = document.createElement("script");
    /* Try local bundle first; fall back to CDN if it 404s */
    s.src = basePath + "/javascripts/d3.min.js";
    s.onload = initMindGraph;
    s.onerror = function() {
      var fallback = document.createElement("script");
      fallback.src = "https://d3js.org/d3.v7.min.js";
      fallback.onload = initMindGraph;
      fallback.onerror = function() {
        var root = document.getElementById("nf-mind-root");
        if (root) {
          root.innerHTML = '<p style="color:#ef9a9a;padding:2rem;font-family:Inter,sans-serif;">Failed to load the visualization library. Please reload while online.</p>';
        }
      };
      document.head.appendChild(fallback);
    };
    document.head.appendChild(s);
  }

  /* ── Hook into Material instant navigation ───────────────────────────────── */
  if (typeof document$ !== "undefined") {
    document$.subscribe(loadD3AndInit);
  } else {
    document.addEventListener("DOMContentLoaded", loadD3AndInit);
  }
})();
