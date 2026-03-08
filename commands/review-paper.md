---
description: Perform a comprehensive quality review of a neuroscience manuscript — scientific logic, methods completeness, statistics correctness, writing quality, figure consistency, and journal-specific requirements. Produces a structured review report.
argument-hint: [paper-path]
allowed-tools: [Read, Glob]
---

# /review-paper — Scientific Manuscript Review

You are performing a comprehensive peer-review-style quality check of a neuroscience manuscript.

**Paper path**: $ARGUMENTS

## Your Task

Review the manuscript thoroughly across 7 dimensions and produce a structured review report.

## Step 1: Load the Manuscript

1. If argument provided, read the file at that path
2. Otherwise, look for: `manuscript/main.tex`, `manuscript/*.tex`, `*.tex`, or `*.md` paper files
3. Also read any supporting materials: figures list, supplementary files

## Step 2: Conduct Multi-Level Review

### Level 1: Scientific Logic
- Does the paper make a coherent argument from Introduction to Conclusion?
- Are hypotheses clearly stated in Introduction?
- Do Results directly address those hypotheses?
- Does Discussion interpret (not re-list) the Results?
- Are claims proportional to evidence?
- Watch for: HARKing, selective reporting, circular reasoning

### Level 2: Methods Completeness
Check that every item in the Methods Completeness Checklist is present:
- Participants: N, age, sex, ethics, exclusion criteria
- Stimuli: all properties specified
- Recording: system, sampling rate, reference, impedance threshold
- Preprocessing: software + version, filter cutoffs, ICA details, epoch window, baseline, rejection threshold, % retained
- Analysis: exact time windows, electrodes/ROIs, statistical tests, correction method

### Level 3: Statistics Reporting
Every stat result must have: test statistic with df, exact p-value, effect size, direction
Flag any: "p < .05", "was significant" without numbers, missing effect sizes

### Level 4: Discussion Quality
- Are null results acknowledged?
- Are alternative explanations considered?
- Are limitations specific (not generic)?
- Do future directions make sense?

### Level 5: Writing Quality
Check: average sentence length, passive voice overuse, jargon without definition, consistent tense (past in Methods/Results, present in Discussion)

### Level 6: Figures and Tables
- Every figure cited in text?
- Captions self-explanatory?
- Error bars defined?
- Font sizes readable?

### Level 7: References
- All citations in reference list?
- All reference list items cited?
- DOIs present?

## Step 3: Produce Review Report

Print a structured report:

```
## 📄 Paper Review Report

**Paper**: [title from manuscript]
**Date**: [today]
**Reviewer**: neuroflow paper-review agent

---

### 🔴 Critical Issues (must fix before submission)
[Issues that would cause desk rejection or fundamental methodological problems]
1. ...

### 🟠 Major Issues (required revisions)
[Missing information, statistics errors, unclear reasoning]
1. ...

### 🟡 Minor Issues (recommended improvements)
[Style, clarity, formatting]
1. ...

### 🟢 Strengths
[What the paper does well]
- ...

### 📊 Statistics Checklist
- [ ] All t/F/z values reported with df
- [ ] All p-values exact (not just < .05)
- [ ] All effect sizes reported
- [ ] Correction for multiple comparisons described

### 📋 Methods Checklist
[List of present/missing items]

### Overall Assessment
[ ] Ready for submission
[ ] Minor revisions needed
[ ] Major revisions needed
[ ] Fundamental issues
```

## Notes

Do not suggest rewriting entire sections — focus on specific, actionable feedback.
For each critical issue, explain why it matters and suggest how to fix it.
