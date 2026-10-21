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

/** Short names, for the flow line and the one-line summary only: everything else names a phase by its id. */
const SHORT: Readonly<Record<string, string>> = {
  preregistration: 'prereg',
  'grant-proposal': 'grant',
  'tool-build': 'tools',
  'tool-validate': 'validate',
  'data-preprocess': 'preprocess',
  'data-analyze': 'analyze',
  'brain-build': 'model',
  'brain-optimize': 'fit',
  'brain-run': 'simulate',
  'write-report': 'report',
}

export const shortName = (id: string): string => SHORT[id] ?? id

export const isPhase = (id: string): boolean => PHASES.some(phase => phase.id === id)

export type PhaseState = 'current' | 'visited' | 'recommended' | 'other'

export const phaseState = (id: string, current: string | null, visited: readonly string[], recommended: readonly string[]): PhaseState =>
  id === current ? 'current' : visited.includes(id) ? 'visited' : recommended.includes(id) ? 'recommended' : 'other'

/**
 * The one glyph legend (skills/neuroflow-develop → Visual style), as /phase and the welcome ring draw it: ◉ the
 * current phase, ● a visited one, → a recommended one not visited yet, ○ one not started.
 */
export const PHASE_GLYPH: Readonly<Record<PhaseState, string>> = { current: '◉', visited: '●', recommended: '→', other: '○' }

/** The word that goes with each glyph, so a map reads the same without colour or glyphs. */
export const PHASE_WORD: Readonly<Record<PhaseState, string>> = { current: 'current', visited: 'visited', recommended: 'recommended next', other: 'not started' }

/**
 * A phase's mark where phases are listed one by one (the picker, the typeahead): its glyph and that glyph's word, and
 * `next` for the phase after the current one — `◉ current`, `→ next`, `→ recommended`, `● visited · next`, `○ not
 * started`. A recommended phase that is not the next one is `recommended`, never `recommended next`.
 */
export const phaseStateMark = (id: string, current: string | null, visited: readonly string[], recommended: readonly string[]): string => {
  const state = phaseState(id, current, visited, recommended)
  const isNext = state !== 'current' && id === nextPhase(current, recommended)
  if (state === 'recommended') return `${PHASE_GLYPH.recommended} ${isNext ? 'next' : 'recommended'}`
  return `${PHASE_GLYPH[state]} ${PHASE_WORD[state]}${isNext ? ' · next' : ''}`
}

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
  return at >= 0 ? (chain[at + 1] ?? null) : null
}

export type PhaseNode = { id: string; short: string; state: PhaseState; glyph: string }

/**
 * The phases a map draws, in order: the recommended ones (without them, the visited ones in canonical order), and
 * the current phase at the end when it is not among them.
 */
export const phaseNodes = (current: string | null, visited: readonly string[], recommended: readonly string[]): PhaseNode[] => {
  const ids = recommended.length > 0 ? recommended.filter(isPhase) : PHASES.map(phase => phase.id).filter(id => id === current || visited.includes(id))
  const all = current !== null && !ids.includes(current) ? [...ids, current] : ids
  return all.map(id => {
    const state = phaseState(id, current, visited, recommended)
    return { id, short: shortName(id), state, glyph: PHASE_GLYPH[state] }
  })
}

/** Where a map's travelled part ends: the current phase, else the last visited one; -1 when neither is drawn. */
export const travelledTo = (nodes: readonly PhaseNode[]): number => {
  const current = nodes.findIndex(node => node.state === 'current')
  if (current >= 0) return current
  return nodes.map(node => node.state).lastIndexOf('visited')
}

/** The one-line phase map, every phase by its id: `● ideation  ● preregistration  ◉ data-analyze  → paper`. */
export const phaseMap = (current: string | null, visited: readonly string[], recommended: readonly string[]): string =>
  phaseNodes(current, visited, recommended).map(node => `${node.glyph} ${node.id}`).join('  ')

/** The map with short names, for a summary row: `● ideation ─ ● prereg ─ ◉ analyze ─ → paper`. */
export const phaseSummary = (current: string | null, visited: readonly string[], recommended: readonly string[]): string =>
  phaseNodes(current, visited, recommended).map(node => `${node.glyph} ${node.short}`).join(' ─ ')

/** The legend of the glyphs a map draws, in legend order: `◉ current  ● visited  → recommended next`. */
export const phaseLegend = (nodes: readonly Pick<PhaseNode, 'state'>[]): string =>
  (['current', 'visited', 'recommended', 'other'] as const)
    .filter(state => nodes.some(node => node.state === state))
    .map(state => `${PHASE_GLYPH[state]} ${PHASE_WORD[state]}`)
    .join('  ')
