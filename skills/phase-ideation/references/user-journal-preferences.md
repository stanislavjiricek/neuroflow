# User journal preferences — template

Copy this file to `.neuroflow/journal-preferences.md` in your project directory to add project-specific journal preferences. These take priority over the defaults in `skills/phase-search/references/journal-defaults.md`.

> **Note:** This file is NOT auto-created by neuroflow. Create it manually when you have strong journal preferences for your project. It is NOT prompted from `/search`.

---

## My preferred journals for this project

Add rows for the area(s) relevant to your work. You can list 1–5 journals per area.

| Area | My preferred journals | Preprint preference |
|---|---|---|
| EEG / MEG / electrophysiology | | bioRxiv |
| fMRI / neuroimaging | | bioRxiv |
| Computational neuroscience | | bioRxiv |
| Systems neuroscience / circuits | | bioRxiv |
| Clinical neurophysiology | | medRxiv |
| Cognitive neuroscience | | PsyArXiv / bioRxiv |
| Network neuroscience | | bioRxiv |
| Information theory / causality | | bioRxiv |
| Other: | | |

---

## Notes

- Leave rows blank to fall back to the default journal list for that area.
- Add a row with "Other:" for areas not in the list.
- The `scholar` agent reads this file automatically when it is present at `.neuroflow/journal-preferences.md`.
