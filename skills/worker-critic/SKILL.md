---
name: worker-critic
description: Worker-critic agentic loop protocol — orchestrator coordinates a worker agent and a critic agent across up to 3 revision cycles to produce a vetted output for any phase.
---

# worker-critic

The worker-critic skill defines the protocol for a structured multi-agent revision loop. The orchestrator manages the loop; the worker produces drafts; the critic evaluates them. The loop terminates on approval or after 3 iterations.

---

## Loop protocol

```
orchestrator → worker (Initial Draft mode)
worker       → draft v1
orchestrator → critic (draft v1 + rubric)
critic       → [STATUS: APPROVED] or [STATUS: REJECTED] + feedback

if APPROVED → done
if REJECTED → orchestrator → worker (Revision mode: draft v1 + feedback)
              worker → draft v2
              orchestrator → critic (draft v2)
              critic → [STATUS: APPROVED] or [STATUS: REJECTED] + feedback

if APPROVED → done
if REJECTED → orchestrator → worker (Revision mode: draft v2 + feedback)
              worker → draft v3
              orchestrator → critic (draft v3)
              critic → [STATUS: APPROVED] or [STATUS: REJECTED] + feedback

if APPROVED → done
if REJECTED (3rd rejection) → halt loop; present draft v3; append unresolved feedback to critic-log.md
```

---

## Max iterations

Strictly 3. The orchestrator tracks iteration count (1, 2, 3). On the 3rd rejection the orchestrator **halts the loop**, presents the current draft to the user as-is, and appends the unresolved critique to `.neuroflow/{phase}/critic-log.md`. It does not attempt a 4th revision.

---

## Critic output format

The critic response **must** begin with exactly one of:

```
[STATUS: APPROVED]
```

or

```
[STATUS: REJECTED]
```

**On APPROVED:**
A brief 1–2 sentence statement of why the draft passes. No further action required.

**On REJECTED:**
The status token is immediately followed by a bulleted list of specific, actionable fixes — no prose preamble before the bullets:

```
[STATUS: REJECTED]
- Fix X: [specific description of what is wrong and what the correct form should be]
- Fix Y: [specific description]
- Fix Z: [specific description]
```

**On subsequent rounds (iteration 2 and 3):**
The critic compares the new draft against the previously-rejected version. It confirms which items from the prior feedback were addressed and flags only items that remain unresolved. It must **not invent new requirements** — new issues may be noted but cannot be the sole basis for rejection if all prior feedback was addressed.

---

## Worker modes

### Initial Draft mode

Triggered on iteration 1. The worker receives the task parameters and rubric from the orchestrator and generates the best output it can without revision history.

Input format the orchestrator provides to the worker:

```
Task: {task description}
Phase: {active phase}
Rubric: {acceptance criteria derived from project_config.md, flow.md, and user-stated requirements}
Mode: Initial Draft
```

### Revision mode

Triggered on iterations 2 and 3. The worker receives the previous draft and the critic's specific feedback.

Input format the orchestrator provides to the worker:

```
Task: {task description}
Phase: {active phase}
Rubric: {rubric — same as iteration 1}
Mode: Revision
Previous Draft:
{draft from prior iteration}

Critic Feedback:
{bulleted feedback list from critic}
```

**Revision rules for the worker:**
- Address each bullet point specifically
- Maintain overall intent and structure from the previous draft — do not start from scratch
- Only change what the feedback requires; do not silently alter unrelated sections

---

## Loop state tracking

After each round, the orchestrator writes the iteration state to `.neuroflow/{phase}/critic-log.md`.

**File format:**

```markdown
# Critic Log — {phase}

## Iteration 1
- Status: REJECTED
- Summary: [one-sentence summary of the main feedback]

## Iteration 2
- Status: APPROVED

## Final: APPROVED after 2 iterations
```

If the loop halts at max iterations:

```markdown
## Iteration 3
- Status: REJECTED (LOOP HALTED — max iterations reached)
- Unresolved feedback:
  - [item 1]
  - [item 2]

## Final: HALTED after 3 iterations — unresolved critique appended above
```

---

## Integration

Any phase command or agent can activate the worker-critic loop by invoking the `worker-critic` skill. The orchestrator selects the appropriate phase agent as the worker automatically, based on the active phase in `.neuroflow/project_config.md`.

**Phase → worker agent mapping:**

| Phase | Worker agent |
|---|---|
| ideation | `ideation` |
| preregistration | `ideation` |
| grant-proposal | `grant-proposal` |
| finance | `grant-proposal` |
| experiment | `experiment` |
| tool-build | `tool-build` |
| tool-validate | `tool-validate` |
| data | `data` |
| data-preprocess | `data-preprocess` |
| data-analyze | `data-analyze` |
| paper-write | `paper-write` |
| paper-review | `paper-review` |
| notes | `notes` |
| write-report | `write-report` |
| brain-build | `brain-build` |
| brain-optimize | `brain-optimize` |
| brain-run | `brain-run` |

If the phase has no direct match, the orchestrator selects the closest available agent and notes the choice in `critic-log.md`.

---

## Termination conditions

The loop terminates when either of the following is reached:

**(a) APPROVED** — the critic returns `[STATUS: APPROVED]`; the orchestrator presents the final draft to the user and writes `APPROVED` to `critic-log.md`.

**(b) 3rd rejection** — the critic returns `[STATUS: REJECTED]` on iteration 3; the orchestrator halts the loop immediately, presents the current draft to the user, appends the unresolved feedback to `.neuroflow/{phase}/critic-log.md`, and informs the user that the loop has halted with outstanding critique.

---

## Rubric construction

The orchestrator constructs the rubric from:

1. `.neuroflow/project_config.md` — project goals, modality, target journal / funder / output
2. `.neuroflow/flow.md` — current phase context and open items
3. `.neuroflow/{phase}/flow.md` — phase-specific progress and constraints
4. User-stated acceptance criteria for the current task

The rubric is passed to both the worker (as task framing) and the critic (as the evaluation standard). It must be concrete and measurable — not a list of wishes.
