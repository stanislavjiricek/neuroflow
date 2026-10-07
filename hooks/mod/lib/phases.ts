// The canonical phase list (neuroflow-core → Phase taxonomy) and the pure logic the phase picker and
// the dashboard's phase map share. Keep PHASES in the order the taxonomy gives.

export type PhaseInfo = { id: string; label: string }

export const PHASES: readonly PhaseInfo[] = [
  { id: 'ideation', label: 'question & literature' },
  { id: 'preregistration', label: 'hypotheses & plan' },
  { id: 'grant-proposal', label: 'funding' },
  { id: 'finance', label: 'budget' },
  { id: 'experiment', label: 'paradigm design' },
  { id: 'tool-build', label: 'build tools' },
  { id: 'tool-validate', label: 'validate tools' },
  { id: 'data', label: 'acquisition & BIDS' },
  { id: 'data-preprocess', label: 'preprocessing' },
  { id: 'data-analyze', label: 'analysis' },
  { id: 'brain-build', label: 'model building' },
  { id: 'brain-optimize', label: 'model fitting' },
  { id: 'brain-run', label: 'simulations' },
  { id: 'paper', label: 'manuscript' },
  { id: 'review', label: 'peer review' },
  { id: 'poster', label: 'poster' },
  { id: 'write-report', label: 'reports' },
  { id: 'output', label: 'export & archive' },
  { id: 'notes', label: 'notes (any time)' },
]

export const isPhase = (id: string): boolean => PHASES.some(phase => phase.id === id)

export type PhaseState = 'current' | 'visited' | 'recommended' | 'other'

export const phaseState = (id: string, current: string | null, visited: readonly string[], recommended: readonly string[]): PhaseState =>
  id === current ? 'current' : visited.includes(id) ? 'visited' : recommended.includes(id) ? 'recommended' : 'other'

/** Picker order: the current phase, then the recommended ones (in their order), then the rest canonically. */
export const pickerOrder = (current: string | null, recommended: readonly string[]): PhaseInfo[] => {
  const first = PHASES.filter(phase => phase.id === current)
  const rec = recommended.filter(id => id !== current && isPhase(id)).map(id => PHASES.find(phase => phase.id === id) as PhaseInfo)
  const rest = PHASES.filter(phase => phase.id !== current && !recommended.includes(phase.id))
  return [...first, ...rec, ...rest]
}

/** The phase after `current` among the recommended ones (or canonically), for "next" hints. */
export const nextPhase = (current: string | null, recommended: readonly string[]): string | null => {
  const chain = recommended.length > 0 ? recommended.filter(isPhase) : PHASES.map(phase => phase.id)
  const at = current === null ? -1 : chain.indexOf(current)
  return at >= 0 && at + 1 < chain.length ? chain[at + 1] : null
}

const GLYPH: Record<PhaseState, string> = { current: '●', visited: '✔', recommended: '○', other: '·' }

/** The one-line phase map: `✔ ideation ✔ preregistration ● data-analyze ○ paper`. */
export const phaseMap = (current: string | null, visited: readonly string[], recommended: readonly string[]): string => {
  const ids = recommended.length > 0 ? recommended.filter(isPhase) : PHASES.map(phase => phase.id).filter(id => id === current || visited.includes(id))
  const all = current !== null && !ids.includes(current) ? [...ids, current] : ids
  return all.map(id => `${GLYPH[phaseState(id, current, visited, recommended)]} ${id}`).join('  ')
}
