// The one key registry of the neuroflow mod: every hotkey a view draws, by view, with what it means.
// A letter means the same thing in every view that offers it, so a person learns each key once. The map is
// frozen: later changes to the look move things around, never a letter. Pure (no `$`): views import it, tests
// check it, and docs/concepts/mods.md → Keyboard and SSH lists the same tables.
//
// Charter rule 7: letters only in the band above the prompt, where a digit typed into an empty prompt could
// press a button; digits only in panes, which hold the keys only after the person gave them (a command, ^X Tab).
import type { NfDashboardTab } from '../../../types'

/** What a key does. One meaning per key across every view. */
export type Meaning =
  | 'left' | 'down' | 'up' | 'right' | 'reread' | 'close' | 'yes' | 'no' | 'cancel'
  | 'dashboard' | 'prepare' | 'notes' | 'close meeting' | 'migrate' | 'review' | 'sync'
  | 'go to phase' | 'boards' | 'freeze' | 'verify' | 'unfreeze' | 'pick'

/**
 * Moving and deciding, in every pane: h/l the previous or next tab, column or target; j/k the next or previous row,
 * card, finding or wiki card; y yes (keep, accept); n no (drop, skip, reject); x cancel or stop; r reread; q close.
 * Enter acts on the element the engine's ring is on; Esc gives the keys back to the prompt (both the engine's).
 */
export const NAV = { left: 'h', down: 'j', up: 'k', right: 'l', reread: 'r', close: 'q', yes: 'y', no: 'n', cancel: 'x' } as const

/** The band above the prompt: letters only. Its y, n and x mean what they mean in a pane. */
export const BAND = {
  dashboard: 'd',
  prepare: 'p',
  notes: 'o',
  closeMeeting: 'c',
  migrate: 'm',
  review: 'w',
  sync: 's',
  keep: NAV.yes,
  drop: NAV.no,
  /** hide today, not today, stop driving, stop the note capture */
  dismiss: NAV.cancel,
} as const

/** The dashboard's own actions, beside the tab digits and the NAV keys. */
export const DASH = { goPhase: 'g', boards: 'b', freeze: 'f', verify: 'v', unfreeze: 'u' } as const

/** The living-paper pane: s syncs the skeleton now (a model turn), as the band's s syncs the flowie. */
export const PAPER = { sync: BAND.sync } as const

/** Digits pick a dashboard tab or a board level, in focused panes only. */
export const DIGITS = ['1', '2', '3', '4', '5', '6', '7', '8', '9'] as const

/** The dashboard's tabs in digit order; the ids are what `/neuroflow:dashboard <tab>` takes. */
export const DASHBOARD_TABS: readonly { id: NfDashboardTab; digit: string; label: string }[] = [
  { id: 'now', digit: '1', label: 'now' },
  { id: 'phase', digit: '2', label: 'phase' },
  { id: 'deadlines', digit: '3', label: 'deadlines' },
  { id: 'integrity', digit: '4', label: 'integrity' },
  { id: 'tasks', digit: '5', label: 'tasks' },
  { id: 'loop', digit: '6', label: 'loop' },
]

export type View = 'band' | 'dashboard' | 'board' | 'wiki' | 'xray' | 'paper' | 'picker'

const picks = (count: number): Record<string, Meaning> => Object.fromEntries(DIGITS.slice(0, count).map(digit => [digit, 'pick' as Meaning]))

/** Every hotkey each view may draw, and what it means there. A Button with any other hotkey is a bug. */
export const VIEW_KEYS: Readonly<Record<View, Readonly<Record<string, Meaning>>>> = {
  band: {
    [BAND.dashboard]: 'dashboard',
    [BAND.prepare]: 'prepare',
    [BAND.notes]: 'notes',
    [BAND.closeMeeting]: 'close meeting',
    [BAND.migrate]: 'migrate',
    [BAND.review]: 'review',
    [BAND.sync]: 'sync',
    [BAND.keep]: 'yes',
    [BAND.drop]: 'no',
    [BAND.dismiss]: 'cancel',
  },
  dashboard: {
    ...picks(DASHBOARD_TABS.length),
    [NAV.left]: 'left',
    [NAV.right]: 'right',
    [NAV.down]: 'down',
    [NAV.up]: 'up',
    [NAV.reread]: 'reread',
    [NAV.close]: 'close',
    [DASH.goPhase]: 'go to phase',
    [DASH.boards]: 'boards',
    [DASH.freeze]: 'freeze',
    [DASH.verify]: 'verify',
    [DASH.unfreeze]: 'unfreeze',
  },
  board: {
    ...picks(DIGITS.length),
    [NAV.left]: 'left',
    [NAV.right]: 'right',
    [NAV.down]: 'down',
    [NAV.up]: 'up',
    [NAV.reread]: 'reread',
    [NAV.close]: 'close',
    [NAV.cancel]: 'cancel',
  },
  wiki: { [NAV.yes]: 'yes', [NAV.no]: 'no', [NAV.down]: 'down', [NAV.up]: 'up', [NAV.close]: 'close' },
  xray: { [NAV.yes]: 'yes', [NAV.no]: 'no', [NAV.down]: 'down', [NAV.up]: 'up', [NAV.close]: 'close' },
  paper: { [PAPER.sync]: 'sync', [NAV.reread]: 'reread', [NAV.close]: 'close' },
  // The picker is a dialog around the engine's Select: arrows, Enter, a letter to jump, Esc.
  picker: {},
}

// ── opening a view ────────────────────────────────────────────────────────────────────────────

/** Keys typed this soon after a view opened holding the keys are dropped: typed through, not meant for it. */
export const TYPE_THROUGH_MS = 400

/** True once a press may act: the view was not opened holding the keys, or long enough ago. */
export const isPastTypeThrough = (now: number, openedAt: number | undefined): boolean => openedAt === undefined || now - openedAt >= TYPE_THROUGH_MS

/** The engine's focus chord, as the band and the pane footers teach it (Claude Code's own default binding). */
export const CHORD = '^X Tab'

/** `$.store` key: how often the band took the keys; the band stops teaching the chord at LEARNED_AFTER. */
export const KEYS_LEARNED = 'keys.learned'
export const LEARNED_AFTER = 3

/** Body rows a view asks for when it opens inline (a request the engine caps): fewer on a short terminal. */
const ROWS: Readonly<Record<Exclude<View, 'band'>, readonly [number, number]>> = {
  dashboard: [18, 10],
  board: [16, 10],
  wiki: [12, 9],
  xray: [16, 10],
  paper: [14, 9],
  picker: [12, 9],
}

/** Under this many terminal rows (24 over SSH, say) a view asks for its compact height. */
export const COMPACT_BELOW = 30

export const paneRows = (view: Exclude<View, 'band'>, viewportRows: number | null): number =>
  ROWS[view][viewportRows !== null && viewportRows < COMPACT_BELOW ? 1 : 0]

// ── moving the ring ───────────────────────────────────────────────────────────────────────────

/** The tab after (`1`) or before (`-1`) the shown one, wrapping around. */
export const tabNeighbour = (tab: NfDashboardTab, step: 1 | -1): NfDashboardTab => {
  const at = Math.max(0, DASHBOARD_TABS.findIndex(item => item.id === tab))
  return DASHBOARD_TABS[(at + step + DASHBOARD_TABS.length) % DASHBOARD_TABS.length]?.id ?? tab
}

/** In a list of element keys, the one after (`1`) or before (`-1`) `current`; the first when the ring is elsewhere. */
export const lineNeighbour = (keys: readonly string[], current: string | null, step: 1 | -1): string | null => {
  const at = current === null ? -1 : keys.indexOf(current)
  if (at < 0) return keys[0] ?? null
  return keys[Math.min(keys.length - 1, Math.max(0, at + step))] ?? null
}

export type Direction = 'left' | 'right' | 'up' | 'down'

/**
 * In columns of element keys (a board's cards), the one beside `current`: up and down within its column, left
 * and right to the neighbouring column that has any, at the same row or its last. The first key when the ring is
 * on none of them; `current` itself at an edge.
 */
export const gridNeighbour = (columns: readonly (readonly string[])[], current: string | null, direction: Direction): string | null => {
  const filled = columns.filter(column => column.length > 0)
  const col = current === null ? -1 : filled.findIndex(column => column.includes(current))
  const here = filled[col]
  if (here === undefined || current === null) return filled[0]?.[0] ?? null
  const row = here.indexOf(current)
  if (direction === 'down') return here[Math.min(here.length - 1, row + 1)] ?? current
  if (direction === 'up') return here[Math.max(0, row - 1)] ?? current
  const there = filled[direction === 'right' ? col + 1 : col - 1]
  if (there === undefined) return current
  return there[Math.min(there.length - 1, row)] ?? current
}
