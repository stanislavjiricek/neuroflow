# Journal defaults — neuroscience areas

Default high-impact journal lists for eight neuroscience research areas.
Used by the `scholar` agent to rank literature search results and suggest journal fit.

---

## Eight neuroscience areas

| Area | Top peer-reviewed journals | Preferred preprint server |
|---|---|---|
| **EEG / MEG / electrophysiology** | Journal of Neuroscience, NeuroImage, Psychophysiology, Clinical Neurophysiology, Brain Topography | bioRxiv |
| **fMRI / neuroimaging** | NeuroImage, Human Brain Mapping, Cerebral Cortex, Nature Neuroscience, PNAS | bioRxiv |
| **Computational neuroscience** | PLoS Computational Biology, Journal of Computational Neuroscience, Neural Computation, eLife | bioRxiv |
| **Systems neuroscience / circuits** | Nature Neuroscience, Neuron, Current Biology, eLife, Journal of Neuroscience | bioRxiv |
| **Clinical neurophysiology** | Clinical Neurophysiology, Epilepsia, Brain, Neurology, Journal of Clinical Neurophysiology | medRxiv |
| **Cognitive neuroscience** | Nature Human Behaviour, Psychological Science, Neuropsychologia, Cognition, Journal of Cognitive Neuroscience | PsyArXiv / bioRxiv |
| **Network neuroscience** | Network Neuroscience, NeuroImage, Brain Connectivity, PLoS ONE | bioRxiv |
| **Information theory / causality** | Entropy, Physical Review E, Chaos, Network Neuroscience, PLoS Computational Biology | bioRxiv |

---

## How the scholar agent uses this table

1. After deduplicating search results, identify which area best matches the query topic.
2. Present results from the top journals in this table first (equal relevance → higher-ranked journal wins).
3. Append a **Journal fit** note to the results listing the top 2–3 journals for the matched area and the recommended preprint server.
4. If the query spans multiple areas (e.g. "computational fMRI"), apply both area lists and note the overlap.

---

## Project-level overrides

Users can add their own journal preferences at the project level by creating `.neuroflow/journal-preferences.md` in their project directory (see `skills/phase-search/references/user-journal-preferences.md` for the template). Project-level preferences take priority over this defaults table.
