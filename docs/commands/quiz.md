---
title: /quiz
---

# `/neuroflow:quiz`

**Neuroscience quiz — test your knowledge with flashcards, a pub quiz, or rapid-fire questions.**

`/quiz` runs an interactive neuroscience quiz covering any subfield or general neuroscience. Supports three modes.

---

## When to use it

- You want to review neuroscience concepts during a break
- You need printable flashcards for study or teaching
- You're organising a neuroscience-themed pub quiz night
- You want quick rapid-fire Q&A to test recall

---

## Three modes

=== "Flashcards"

    Generates a set of 10 question/answer cards (or as many as you request). Cards use precise scientific language calibrated to the chosen subfield.

    After generation, Claude asks if you want to save a printable layout — a Markdown file formatted for A4 printing (two-column table, front left, back right). Saved to the current working directory.

=== "Pub quiz"

    Generates 15 questions across three rounds of increasing difficulty:

    - **Round 1 — Warm-up:** accessible broad neuroscience facts
    - **Round 2 — Lab coat required:** more technical, methods and mechanisms
    - **Round 3 — Nobel territory:** advanced, cutting-edge, or Nobel Prize–linked discoveries

    Each question includes an answer and a one-sentence "fun fact" to read aloud. Claude also suggests 5 neuro-themed house rules for the event.

=== "Throw questions (default)"

    Rapid-fire Q&A — one question at a time. After each answer Claude gives immediate feedback (✅ / ❌), the correct answer, and a brief explanation. Keeps a running score shown after every 5 questions.

    Question formats vary: direct recall, multiple choice, true/false, fill-in-the-blank. Continue until you say "stop", "enough", or "quit".

---

## Subfield selection

After mode is confirmed, Claude asks:

> "Any particular area, or keep it general? Examples: neuroanatomy, EEG/oscillations, synaptic physiology, cognitive neuroscience, clinical neuroscience, neuroimaging, pharmacology, developmental neuroscience — or just say 'general'."

Default: **general neuroscience**.

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md` (if they exist) |
| Writes | `.neuroflow/sessions/YYYY-MM-DD.md` (if `.neuroflow/` exists), flashcard `.md` file (if saved) |

---

## Related commands

- [`/idk`](idk.md) — a quieter break if you need to decompress rather than quiz
