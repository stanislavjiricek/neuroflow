---
name: humanizer
description: Style editing for prose, on request. Cuts filler and inflated vocabulary, varies sentence rhythm, and matches the register, while keeping the author's voice and every fact, number, citation and hedge. Use only when the person asks to tighten, edit or restyle a text. Never used to hide AI involvement or evade AI-detection or disclosure rules.
metadata:
  trigger: The person asks for a style edit of prose (tighten, edit for style, humanize)
  replaces: stop-slop
---

# Humanizer

Edit prose for style: cut filler, deflate inflated wording, vary rhythm, and match the register, so the text reads like the author on a good day. This goes beyond deleting words — it addresses rhythm, register, word choice, and the stock structural patterns that make drafts generic.

---

## When to use — and what it is not

- **Only when the person asks** ("tighten this", "edit for style", "humanize this"). No command runs it automatically, and it is never a default step before a critic, a save or a submission.
- **A style edit, not a disguise.** It improves readability. It does not make AI-assisted text undetectable and must never be used or described as a way to evade AI detection or disclosure rules. AI assistance is declared: the AI-use statement in `/paper --submit` and the AI-use declaration in `/grant-proposal`.
- **Content is fixed.** Facts, numbers, statistics, citations, hedges and technical terms stay exactly as they are. If a sentence cannot be improved without changing what it claims, leave it.

---

## Step 1 — Cut filler and inflated wording

Cut or replace the words and patterns below. Exception: technical senses (next paragraph).

**Word blacklist** — replace or cut:

| Word / phrase | Why cut it |
|---|---|
| delve, delving | Rare outside fantasy novels; say "examine" or "look at" |
| comprehensive, robust, nuanced | Vague intensifiers that pad without adding meaning |
| crucial, pivotal, vital, essential | Overused emphasis words |
| seamlessly, effortlessly | Fake smoothness |
| leverage (as a verb) | Corporate jargon; use "use" or "apply" |
| notably, importantly, significantly | Throat-clearing before a point |
| transformative, groundbreaking, revolutionary | Unjustified superlatives |
| in the realm of, in the landscape of | Pompous filler |
| it is worth noting, it is important to note | Cut entirely; just state the note |
| this highlights, this underscores, this demonstrates | Tell the reader what it shows, don't announce that it shows it |
| the [noun] landscape | Cliché geography metaphor |
| moving forward, going forward | Corporate filler |
| at the end of the day | Cliché |
| em dash (—) | Overused; replace with comma, colon, or period |

**Technical senses are exempt.** Keep a listed word when it is the technical term, not emphasis: "significant" or "significantly" for a reported statistical test (name the test, or write "statistically significant" — the paper-critic and review-neuro require exactly that), "robust regression", "robust to outliers", "essential tremor", "critical period". Cut the word only where it is an intensifier.

**Structural blacklist:**

| Pattern | Replace with |
|---|---|
| `X not only A but also B` | `X does A and B` — or split into two sentences |
| `While X, Y` (contrast opener) | Rewrite without "while" — state X and Y as separate facts |
| `Not X — it's Y` contrasts | State Y directly; cut the negation |
| Three-part lists with parallel structure | Two items or prose; three identical grammatical units sound mechanical |
| Sentences starting with "It is" / "There is" / "There are" | Rewrite with a concrete subject |
| Paragraph ending with punchy one-liner summary | Vary the ending; not every paragraph needs a mic-drop |
| Wh- sentence openers ("What this means is…") | Restructure |

A temporal "while" ("while recording, we…") and a real three-item list (alpha, beta and gamma bands) are content, not patterns: keep them.

---

## Step 2 — Fix rhythm

Prose in which every sentence has the same length and every paragraph the same arc is tiring to read. Break it.

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
- A mild colloquialism is fine where the register allows it

---

## Step 4 — Preserve voice

The goal is not to homogenize. Cut the patterns above while keeping what makes the author's writing individual.

- If the author has characteristic phrases or constructions that are not on the lists above, keep them
- Do not make every sentence identical in structure (that's just a different kind of monotony)
- Ask: does this sentence sound like the author, or like generic filler?

---

## Quick checks before delivering

Run through each line:

- Any word from the blacklist used as emphasis? Replace or cut (technical senses stay).
- Em dash anywhere? Remove.
- Three sentences same length in a row? Break one.
- Passive construction where there's a real actor? Name them.
- Sentence starts with "It is" / "There is"? Rewrite.
- "Not X, it's Y" contrast? State Y.
- Paragraph ends with punchy summary? Vary it.
- Any fact, number, citation or hedge changed? Put it back.

---

## Scoring

Rate 1–10 on each dimension. Below 35/50: revise.

| Dimension | Question |
|---|---|
| Naturalness | Does this read like the author's own prose? |
| Rhythm | Varied, or metronomic? |
| Plainness | Free of the listed filler words and patterns? |
| Voice | Distinct, or generic? |
| Density | Any word that could be cut? |
