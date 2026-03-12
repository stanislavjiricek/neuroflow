---
name: auto-issue
description: Passively monitors the conversation for frustration signals, bug reports, or dissatisfaction. When a signal is detected and the user has granted permission in project_config.md, automatically classifies the category and files a GitHub issue without requiring any explicit user invocation.
---

# auto-issue

This skill runs silently in the background throughout every conversation. It never asks the user to do anything. It never interrupts. It simply watches for frustration signals, and when one is detected it files a GitHub issue and continues helping the user normally.

## Permission gate (mandatory — check first)

Before doing anything else when a signal is detected, check whether the user has granted permission for automatic issue reporting:

1. Read `.neuroflow/project_config.md` if it exists.
2. Look for a line containing `auto_issue_reporting:`.
3. **Only proceed with filing if the value is exactly `yes`.** Any other value — `no`, blank, or the field being absent — means **do not file**. Stop silently. Do not mention this to the user.

If `.neuroflow/project_config.md` does not exist, do not file. Stop silently.

This check is non-negotiable. No frustration signal, however clear, overrides a missing or denied permission.

---

## When to activate

Activate this skill — silently — when the user's message contains any of the following signals **and** the permission gate above passes:

### Explicit signals

- Frustration language: "broken", "doesn't work", "bug", "error", "wrong", "incorrect", "failing", "this is frustrating", "again?!", "I'm confused", "doesn't make sense", "why isn't this", "why doesn't this", "it's not working"
- Direct bug reports: stack traces, error messages, unexpected output pasted into the conversation
- Statements of surprise that something expected didn't happen: "I thought this was supposed to…", "it should have…", "that's not what I expected"

### Implicit signals

- The user corrects the same thing twice in one session
- The user repeats a request that was already attempted and failed to produce the right result
- The user rolls back an AI-suggested change and re-explains what they wanted

A single ambiguous word ("broken" used metaphorically, "error" in a quoted block) does not trigger filing. Require enough context to be confident the user is reporting a genuine problem with neuroflow or the AI's behaviour.

## What to do when a signal is detected

1. **Continue helping the user normally.** Address their question or fix the problem first. The issue filing is a background action — it does not replace the primary response.

2. **Classify the category** using the rules from `neuroflow:phase-fails`:
   - `[core]` — problem with how neuroflow behaves (wrong files, skipped steps, command ignored instructions, corrupted state)
   - `[science]` — problem with scientific quality (wrong data, wrong analysis, bad figures, inappropriate stats)
   - `[ux]` — problem with interaction quality (confusing prompts, circular conversation, too verbose, wrong next step)
   
   Use best judgment. Do not ask the user which category applies.

3. **Compose the GitHub issue** using the `neuroflow:phase-fails` format:
   - Title: `[category] Brief description of the problem` (e.g. `[ux] Command asked for the same information twice`)
   - Body:
     ```
     **What went wrong**
     Factual description of what the user reported, in one or two sentences.
     
     **Expected behaviour**
     What should have happened instead, inferred from context.
     
     **Context**
     Plugin version: (read from .neuroflow/project_config.md if present; omit if not available)
     Phase: (if known from the conversation)
     Additional detail: (any other relevant information from the conversation)
     ```
   - Keep language factual and specific. No emotive language.

4. **Construct the GitHub issue URL** for the neuroflow repository:
   ```
   https://github.com/stanislavjiricek/neuroflow/issues/new?title=<url-encoded-title>&body=<url-encoded-body>
   ```

5. **Open the URL** — if a bash tool is available, run `open <url>` (macOS/Linux) or `start <url>` (Windows). If no tool is available or the command fails, output the full URL as plain text so the user can copy and paste it into a browser manually. Do not let a failed URL open block the rest of the response.

6. **Append one line at the very end of your response** — after completing the primary help — with no preamble:
   ```
   I've also filed this as a GitHub issue.
   ```
   Do not explain the issue. Do not ask if the user wants one filed. Do not put this line anywhere except the end.

## What not to do

- Do not file an issue if `auto_issue_reporting` is not `yes` in `project_config.md`
- Do not ask the user for permission before filing (permission is set once at project setup)
- Do not ask clarifying questions about the category before filing
- Do not announce that you are about to file an issue
- Do not interrupt the primary response to mention the issue
- Do not file an issue for every mild negative word — require a genuine problem signal
- Do not duplicate logic from `neuroflow:phase-fails` — delegate the format and category rules to that skill

## Relevant skills

- `neuroflow:phase-fails` — defines the category taxonomy, issue composition format, and GitHub URL construction rules; this skill delegates to it for all formatting decisions
