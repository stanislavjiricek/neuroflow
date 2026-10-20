---
title: Overview
---

# A complete research system for neuroscience teams

neuroflow is a plugin for Claude Code. Its commands, skills and agents carry a study from the first question to the published paper, and on to the next one, while one memory keeps what was planned, decided and done: for you, for the project and for the team.

It is built for neuroscientists who work with EEG, iEEG, fMRI, eye tracking, ECG and other physiological signals, in cognitive, clinical and preclinical research.

<!-- The intro video. Paths are relative to the built page, overview/index.html (use_directory_urls,
     the MkDocs default). The mp4 is not in git: the docs deploy downloads it from the intro-video
     release (docs/maintenance/automation.md). -->

<figure class="nf-video" id="intro-video">
<video controls preload="none" playsinline width="1920" height="1080" poster="../assets/video/poster-en.jpg" aria-label="The neuroflow intro, 4 minutes 33 seconds">
<source src="../assets/video/neuroflow-en.mp4" type="video/mp4">
<a href="https://github.com/stanislavjiricek/neuroflow/releases/download/intro-video/neuroflow-en.mp4">Download the intro video (MP4, 20 MB)</a>
</video>
<figcaption>The intro, 4:33: why neuroflow, how to install it, and how to set up your flowie, your hive and your first project. The captions are part of the picture; the voice is synthetic, and the terminal shots are reconstructions, not screen recordings. <a href="https://github.com/stanislavjiricek/neuroflow/releases/download/intro-video/neuroflow-en.mp4">Download the MP4</a> (20 MB).</figcaption>
</figure>

## The cycle

Nineteen phases, each a slash command with its own folder in project memory. Start wherever your work is: every command reads the memory first and picks up where the last one stopped.

| Stage | Phases |
|---|---|
| Question | [ideation](commands/ideation.md) · [preregistration](commands/preregistration.md) |
| Funding | [grant-proposal](commands/grant-proposal.md) · [finance](commands/finance.md) |
| Instruments | [experiment](commands/experiment.md) · [tool-build](commands/tool-build.md) · [tool-validate](commands/tool-validate.md) |
| Data | [data](commands/data.md) · [data-preprocess](commands/data-preprocess.md) · [data-analyze](commands/data-analyze.md) |
| Models | [brain-build](commands/brain-build.md) · [brain-optimize](commands/brain-optimize.md) · [brain-run](commands/brain-run.md) |
| Writing | [paper](commands/paper.md) · [review](commands/review.md) · [poster](commands/poster.md) · [write-report](commands/write-report.md) |
| Sharing | [output](commands/output.md) · [notes](commands/notes.md) |

## Common paths

- **A full study** — `/ideation` → `/preregistration` → `/experiment` → `/data` → `/data-preprocess` → `/data-analyze` → `/paper`
- **Data you already have** — `/data` → `/data-preprocess` → `/data-analyze` → `/paper`
- **A research tool** — `/ideation` → `/tool-build` → `/tool-validate`, then a methods paper if you want one
- **A computational model** — `/ideation` → `/brain-build` → `/brain-optimize` → `/brain-run`, with the data track feeding the fit
- **A review or a grant** — `/ideation` → `/paper` or `/grant-proposal`

[`/pipeline`](commands/pipeline.md) runs a planned sequence one step at a time.

## Memory at three levels

- **You** — a private flowie repository: your profile and writing style, your ideas, your own task board and wiki, across all your projects.
- **The project** — `.neuroflow/` inside the project's repository: its configuration, objectives, timeline, task board, meetings, every decision with its reason, and its wiki.
- **The team** — a hive repository for the lab: members, research directions, a team board and a shared wiki.

Nothing personal leaves your machine or your profile without your explicit yes — except syncing your own private flowie repository, which you set up once. → [Three levels](concepts/memory.md)

## Rules that hold

- A frozen preregistration is never edited; every change goes to `deviations.md`.
- Raw data stays as it was recorded.
- No data collection before the ethics approval is recorded, and participant data reaches the model only when the approval allows it.
- Uploads, pushes and exports happen only after you confirm them — except syncing your own private flowie repository, which you set up once.
- Every decision is logged with its reason, in the phase it was made.

The rules are written in the commands themselves and hold in every session. → [Project memory](concepts/project-memory.md)

## The harness

The neuroflow mod is an optional Claude Code hooks module that ships with the plugin. With it, the project shows itself: a dashboard and a task board as live panes, a status line for what needs attention, a band above the prompt, and guards that warn about — or, with `runtime: on` and `guards: enforce`, block — breaks of the rules above. Everything also works without it. → [The neuroflow mod](concepts/mods.md)

## Install

```
/plugin install neuroflow --marketplace stanislavjiricek/neuroflow
```

Then open your project folder in Claude Code and run `/neuroflow:neuroflow`. → [Installation](installation.md)

## How it works

```
.neuroflow/
├── project_config.md   the project's facts: active phase, collaborators, rules
├── flow.md             an index of every folder
├── objectives.md       the aims, checked before major sections are saved
├── timeline.md         milestones and deadlines
├── reasoning/          decisions with their reasons, one JSON line each
├── sessions/           daily logs, kept on your machine
├── tasks/              the project's task board
├── meetings/           agendas, notes and action items
├── wiki/               the project's shared knowledge
├── ethics/  preregistration/  finance/
└── {phase}/            one folder for each phase you work in
```

Every command reads `project_config.md` and `flow.md` first and writes back what it did. → [Project memory](concepts/project-memory.md)
