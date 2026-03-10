---
title: Quickstart
---

# Quickstart

Get from zero to a running neuroflow project in under five minutes.

---

## Step 1 — Install

```bash
claude plugin marketplace add stanislavjiricek/neuroflow
claude plugin install neuroflow@neuroflow
```

→ [Full installation guide](installation.md)

---

## Step 2 — Open your project

Navigate to your project folder (or any empty folder to start fresh) and open Claude Code:

```bash
cd ~/my-eeg-study
claude
```

---

## Step 3 — Run `/start`

Type this in Claude Code:

```
/neuroflow:start
```

If this is a **new project**, neuroflow will:

1. Scan your folder for signals (BIDS data, scripts, manuscript files, etc.)
2. Ask you a few short questions about your project
3. Create `.neuroflow/` — the shared project memory

If you already have a `.neuroflow/` folder, it will show your current phase and status instead.

!!! example "Example session"
    ```
    You: /neuroflow:start

    Claude: I found a `paradigm/` folder with PsychoPy scripts and a `scripts/` folder
            with Python preprocessing code. This looks like an EEG study in progress.

            What are you working on? (one or two sentences)

    You: An auditory oddball study on attention in healthy adults. I need to preprocess
         the EEG and run ERP analysis.

    Claude: Got it. Setting up neuroflow project memory...

            ✅ Created .neuroflow/
            ✅ Active phase: data-preprocess

            Next step: run /neuroflow:data-preprocess
    ```

---

## Step 4 — Set up integrations (optional)

neuroflow can search PubMed and use Miro for visual collaboration. Run the setup wizard:

```
/neuroflow:setup
```

This stores credentials in `.neuroflow/integrations.json` (git-ignored).

---

## Step 5 — Follow the pipeline

Run the command for your current phase:

=== "Ideation"

    ```
    /neuroflow:ideation
    ```

    Brainstorm a research question, search the literature, or write a project proposal.

=== "Preprocessing"

    ```
    /neuroflow:data-preprocess
    ```

    Build and run an EEG/fMRI preprocessing pipeline with filtering, ICA, and QC.

=== "Analysis"

    ```
    /neuroflow:data-analyze
    ```

    Run ERPs, time-frequency analysis, connectivity, decoding, or GLM.

=== "Writing"

    ```
    /neuroflow:paper-write
    ```

    Generate a manuscript draft from your results and figures.

---

## Key concepts

| Concept | What it is |
|---|---|
| **Project memory** | `.neuroflow/` folder — every command reads and writes here |
| **Commands** | `/neuroflow:<name>` — the main way you interact with neuroflow |
| **Skills** | Domain knowledge Claude loads automatically for each phase |
| **Agents** | Autonomous subprocesses for focused tasks (e.g. literature search) |

---

## What's next?

- [Browse all commands →](commands/index.md)
- [Understand project memory →](concepts/project-memory.md)
- [Configure integrations →](integrations.md)

