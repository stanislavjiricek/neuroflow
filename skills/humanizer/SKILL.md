---
name: humanizer
description: Remove AI writing signatures from prose. Makes text sound genuinely human-authored — varied rhythm, natural register, no AI tells. Use when drafting, editing, or reviewing any text that needs to read as if a person wrote it.
metadata:
  trigger: Writing prose, editing drafts, reviewing content for AI patterns
  replaces: stop-slop
---

# Humanizer

Transform AI-generated prose into text that reads as if a human wrote it. This goes beyond cutting filler — it addresses rhythm, register, word choice, and the structural patterns that mark AI output as synthetic.

---

## Step 1 — Strip AI signatures

Remove every word and phrase that signals machine authorship. No exceptions.

**Word blacklist** — replace or cut entirely:

| Banned word / phrase | Why it's a tell |
|---|---|
| delve, delving | No human writes "delve" unless they're writing a fantasy novel |
| comprehensive, robust, nuanced | Vague intensifiers that pad without adding meaning |
| crucial, pivotal, vital, essential | Overused AI emphasis words |
| seamlessly, effortlessly | Fake smoothness |
| leverage (as a verb) | Corporate-AI hybrid; use "use" or "apply" |
| notably, importantly, significantly | AI throat-clearing before a point |
| transformative, groundbreaking, revolutionary | Unjustified superlatives |
| in the realm of, in the landscape of | Pompous filler |
| it is worth noting, it is important to note | Cut entirely; just state the note |
| this highlights, this underscores, this demonstrates | Tell the reader what it shows, don't announce that it shows it |
| the [noun] landscape | Cliché geography metaphor |
| moving forward, going forward | Corporate filler |
| at the end of the day | Cliché |
| em dash (—) | Overused by AI; replace with comma, colon, or period |

**Structural blacklist:**

| Pattern | Replace with |
|---|---|
| `X not only A but also B` | `X does A and B` — or split into two sentences |
| `While X, Y` (contrast opener) | Rewrite without "while" — state X and Y as separate facts |
| `Not X — it's Y` contrasts | State Y directly; cut the negation |
| Three-part lists with parallel structure | Two items or prose; three identical grammatical units sound robotic |
| Sentences starting with "It is" / "There is" / "There are" | Rewrite with a concrete subject |
| Paragraph ending with punchy one-liner summary | Vary the ending; not every paragraph needs a mic-drop |
| Wh- sentence openers ("What this means is…") | Restructure |

---

## Step 2 — Fix rhythm

AI prose is metronomic. Every sentence is roughly the same length. Every paragraph has the same arc. Break it.

**Rules:**
- No three consecutive sentences of the same length (count syllables roughly)
- Mix: one short sentence (≤8 words), one medium (9–20 words), one long (21+ words) — in any order
- Allow a fragment when it lands. Like this.
- Vary paragraph endings: summary, implication, question, example, half-finished thought — not always the same type
- A paragraph can be one sentence. It can also be five.

---

## Step 3 — Calibrate register

Match the register to the context — but always push toward natural.

**Academic writing:**
- Formal but not stiff; hedges are fine when honest ("may suggest", "consistent with")
- First-person is allowed and often clearer ("We found" not "It was found")
- Avoid the false objectivity of passive voice when there's a real actor
- Technical terms stay; inflated vocabulary goes

**Grant / proposal writing:**
- Confident, not boastful
- Specific, not grandiose
- Short sentences in the Aims — every word is costing you space
- Reviewers have read ten proposals today; write for a tired reader

**General prose:**
- "You" beats "the reader" or "people"
- Contractions are fine when the prose is not highly formal
- A mild colloquialism once or twice signals a human wrote this

---

## Step 4 — Preserve voice

The goal is not to homogenize. It is to remove machine patterns while keeping what makes the writing individual.

- If the author has characteristic phrases or constructions that are not AI tells, keep them
- Do not make every sentence identical in structure (that's just a different kind of robotic)
- Ask: does this sentence sound like a specific person wrote it, or like a language model approximating a person?

---

## Quick checks before delivering

Run through each line:

- Any word from the blacklist? Replace or cut.
- Em dash anywhere? Remove.
- Three sentences same length in a row? Break one.
- Passive construction where there's a real actor? Name them.
- Sentence starts with "It is" / "There is"? Rewrite.
- "Not X, it's Y" contrast? State Y.
- Paragraph ends with punchy summary? Vary it.
- Does it still sound like a language model's idea of a human? Rewrite until it doesn't.

---

## Scoring

Rate 1–10 on each dimension. Below 35/50: revise.

| Dimension | Question |
|---|---|
| Naturalness | Does this read like a specific person's prose? |
| Rhythm | Varied, or metronomic? |
| Humanity | Free of AI tells? |
| Voice | Distinct, or generic? |
| Density | Any word that could be cut? |
