// Pure layout helpers for the mod's views (no `$`): widths and heights, text cut to a width with an ellipsis, the
// rules under the dashboard's tabs, the phase flow line, the dates ruler, the board's grid and its pages, and what the
// one-row band above the prompt has room for. Widths are terminal cells, one per character of the glyphs the views use
// (Box Drawing, Geometric Shapes, Arrows: no emoji, no wide glyphs). The look is skills/neuroflow-develop → Visual style.
import { COMPACT_BELOW } from './keys'
import type { View } from './keys'

/**
 * The terminal as a drawing last measured it. Render hooks see `e.viewport`; a command that opens a pane does not,
 * so the views remember it here. The one piece of module state in this file: a measurement, never research or UI
 * state, and a fresh module (a reload) simply starts without one.
 */
let measured: number | null = null

export const rememberViewport = (viewport: { rows: number } | undefined): void => {
  if (viewport !== undefined && Number.isFinite(viewport.rows) && viewport.rows > 0) measured = viewport.rows
}

export const measuredRows = (): number | null => measured

// ── widths and heights ────────────────────────────────────────────────────────────────────────

/** neuroflow's mark in the terminal: the ring in one glyph, before the wordmark and on the band. */
export const MARK = '◌'

/** The lowercase wordmark, in the text colour and never bold. */
export const WORDMARK = 'neuroflow'

/** Under this many body cells a view is narrow (a dock beside the transcript, a phone): stacked, lists, no ruler. */
export const NARROW_BELOW = 56

/** From this many body cells a view is wide (a 100-column terminal and up): side by side where it helps. */
export const WIDE_FROM = 90

export type WidthClass = 'narrow' | 'medium' | 'wide'

/** The width class of a view's body (its `bodyColumns`): narrow under 56 cells, medium 56–89, wide from 90. */
export const widthClass = (columns: number): WidthClass => (columns < NARROW_BELOW ? 'narrow' : columns < WIDE_FROM ? 'medium' : 'wide')

/** A terminal under COMPACT_BELOW rows (24 over SSH): the views drop their blank rows and summaries. */
export const isCompact = (rows: number | null | undefined): boolean => rows !== null && rows !== undefined && rows < COMPACT_BELOW

/** The body columns a view asks for when it opens docked beside a fullscreen transcript (a request the engine caps). */
const DOCK: Readonly<Record<Exclude<View, 'band'>, number>> = {
  dashboard: 64,
  board: 84,
  wiki: 64,
  xray: 72,
  paper: 64,
  picker: 56,
}

export const paneColumns = (view: Exclude<View, 'band'>): number => DOCK[view]

// ── text ──────────────────────────────────────────────────────────────────────────────────────

/** Cells a text takes: one per character (the views draw no wide glyphs and no emoji). */
export const cells = (text: string): number => Array.from(text).length

/** The text cut to `width` cells, ending in `…` when it was cut; never mid-way through a character. */
export const fit = (text: string, width: number): string => {
  const chars = Array.from(text)
  if (chars.length <= width) return text
  if (width <= 0) return ''
  if (width === 1) return '…'
  return `${chars.slice(0, width - 1).join('').trimEnd()}…`
}

/** The text fitted to `width` cells and padded with spaces to exactly that width. */
export const pad = (text: string, width: number): string => {
  const cut = fit(text, Math.max(0, width))
  return `${cut}${' '.repeat(Math.max(0, width - cells(cut)))}`
}

/**
 * `left` and `right` on one line of `width` cells, `right` against the right edge: `left` gives way first (cut with
 * `…`), at least `gap` spaces between them; when even `right` does not fit, `right` cut to the width.
 */
export const align = (left: string, right: string, width: number, gap = 2): string => {
  if (right === '') return fit(left, width)
  if (cells(right) + gap >= width) return fit(right, width)
  const room = width - cells(right) - gap
  const shown = fit(left, room)
  return `${shown}${' '.repeat(width - cells(shown) - cells(right))}${right}`
}

// ── rules and tabs ────────────────────────────────────────────────────────────────────────────

/** A rule `width` cells long: `─`, heavy (`━`) over the `length` cells from `from` (the shown tab). */
export const rule = (width: number, from = 0, length = 0): string =>
  Array.from({ length: Math.max(0, width) }, (_, at) => (at >= from && at < from + length ? '━' : '─')).join('')

/** Cells between the dashboard's tabs, widest first: the strip takes the widest that keeps it on one row. */
const TAB_GAPS = [3, 2, 1] as const

export type TabStrip = { gap: number; fits: boolean; rule: string }

/**
 * The dashboard's tab row as drawn (`1: now`, …) in `width` cells: the widest gap of 3, 2 or 1 that keeps every tab
 * on one row, and the rule under it with a heavy segment under the shown tab. Where no gap fits (a narrow dock) the
 * row wraps with gaps of 1 and the rule is plain: the shown tab is the one drawn at full strength.
 */
export const tabStrip = (labels: readonly string[], active: number, width: number): TabStrip => {
  const total = (gap: number): number => labels.reduce((sum, label) => sum + cells(label), 0) + gap * Math.max(0, labels.length - 1)
  const gap = TAB_GAPS.find(candidate => total(candidate) <= width)
  if (gap === undefined) return { gap: 1, fits: false, rule: rule(width) }
  const from = labels.slice(0, Math.max(0, active)).reduce((sum, label) => sum + cells(label) + gap, 0)
  return { gap, fits: true, rule: rule(width, from, cells(labels[active] ?? '')) }
}

// ── the phase flow line ───────────────────────────────────────────────────────────────────────

/** Under this many cells per phase the flow line gives way to the word list. */
export const FLOW_MIN_CELL = 9

export type FlowNode = { short: string; glyph: string }

export type FlowLine = {
  /** The line up to and including the current phase (or the last visited one): drawn at full strength. */
  head: string
  /** The rest of the line, still to come: drawn dim. */
  tail: string
  /** Each phase's short name under its glyph. */
  labels: string
}

/**
 * The phases as a line of glyphs joined by `━` up to the phase at `travelled` and by `─` after it, each glyph at the
 * start of an equal cell, with the names under them: `●━━━━━━━━●━━━━━━━━◉────────→`. Null when the width leaves under
 * FLOW_MIN_CELL cells a phase: the views show the word list instead (lib/phases.ts → phaseMap).
 */
export const flowLine = (nodes: readonly FlowNode[], travelled: number, width: number): FlowLine | null => {
  if (nodes.length === 0) return null
  const cell = Math.floor(width / nodes.length)
  if (cell < FLOW_MIN_CELL) return null
  const last = nodes.length - 1
  const parts = nodes.map((node, at) => `${node.glyph}${at < last ? (at < travelled ? '━' : '─').repeat(cell - 1) : ''}`)
  const split = Math.max(0, Math.min(last, travelled)) + 1
  const lastRoom = width - last * cell
  const labels = nodes.map((node, at) => (at < last ? pad(fit(node.short, cell - 1), cell) : fit(node.short, lastRoom))).join('')
  // The current glyph ends the head; the connector after it opens the tail.
  const after = Array.from(parts[split - 1] ?? '').slice(1).join('')
  return {
    head: travelled < 0 ? '' : parts.slice(0, split).join('').replace(/[━─]+$/, ''),
    tail: travelled < 0 ? parts.join('') : `${after}${parts.slice(split).join('')}`,
    labels: labels.trimEnd(),
  }
}

// ── the dates ruler ───────────────────────────────────────────────────────────────────────────

/** A date on the ruler: days from today, its glyph, its urgency (0 the most urgent, which wins a shared cell). */
export type RulerMark = { days: number; glyph: string; rank: number }

export type Ruler = { axis: string; marks: string; days: number }

/** Fewer days than this and the ruler is left out: the list says it all. */
export const RULER_MIN_DAYS = 14

const RULER_LEAD = 'today '

/**
 * The dates ruler in `width` cells: `today ┼──────┬──────┬ … +63 d`, one cell a day and a `┬` at each week, as many
 * whole weeks as fit (at most a year); and under it each date's glyph on its day, the most urgent where two share a
 * cell. Dates past the ruler's end are left to the list. Null when under RULER_MIN_DAYS days fit.
 */
export const ruler = (width: number, marks: readonly RulerMark[]): Ruler | null => {
  // The lead, the ┼ of today, and room for the widest end label (` +364 d`).
  const room = width - cells(RULER_LEAD) - 1 - 7
  const days = Math.min(364, Math.floor(room / 7) * 7)
  if (days < RULER_MIN_DAYS) return null
  const axis = `${RULER_LEAD}┼${Array.from({ length: days }, (_, at) => ((at + 1) % 7 === 0 ? '┬' : '─')).join('')} +${days} d`
  const row: { glyph: string; rank: number }[] = Array.from({ length: days + 1 }, () => ({ glyph: ' ', rank: Number.POSITIVE_INFINITY }))
  for (const mark of marks) {
    if (mark.days > days) continue
    const slot = row[Math.max(0, Math.round(mark.days))]
    if (slot !== undefined && mark.rank < slot.rank) {
      slot.glyph = mark.glyph
      slot.rank = mark.rank
    }
  }
  return { axis, marks: `${' '.repeat(cells(RULER_LEAD))}${row.map(slot => slot.glyph).join('')}`.trimEnd(), days }
}

// ── the board ─────────────────────────────────────────────────────────────────────────────────

/** Cards a board column shows at a time (commands/tasks.md → Rendering: at most five, `+N more` underneath). */
export const BOARD_PAGE = 5

/** A column narrower than this and the board is drawn as a list, grouped by column. */
export const BOARD_MIN_COLUMN = 18

/** A column wider than this would only add blank cells. */
export const BOARD_MAX_COLUMN = 36

/** Cells between two columns of the grid. */
export const BOARD_GAP = 1

export type BoardLayout = { kind: 'grid'; columnWidth: number } | { kind: 'list' }

/** Columns side by side when each gets BOARD_MIN_COLUMN cells (at most BOARD_MAX_COLUMN); a list otherwise. */
export const boardLayout = (width: number, columns: number): BoardLayout => {
  const count = Math.max(1, columns)
  const columnWidth = Math.min(BOARD_MAX_COLUMN, Math.floor((width - BOARD_GAP * (count - 1)) / count))
  return columnWidth >= BOARD_MIN_COLUMN ? { kind: 'grid', columnWidth } : { kind: 'list' }
}

export type Page<T> = { shown: T[]; from: number; to: number; total: number; before: number; after: number }

/**
 * The page of `size` items that holds the item at `at` (the first page when `at` is outside), with 1-based `from`
 * and `to` and how many items come before and after it.
 */
export const pageOf = <T>(items: readonly T[], at: number, size = BOARD_PAGE): Page<T> => {
  const start = at >= 0 && at < items.length ? Math.floor(at / size) * size : 0
  const shown = items.slice(start, start + size)
  return {
    shown,
    from: shown.length === 0 ? 0 : start + 1,
    to: start + shown.length,
    total: items.length,
    before: start,
    after: Math.max(0, items.length - start - shown.length),
  }
}

/** What a column says under its page: `+2 more` on the first page (the prose's words), `6–7 of 7` on a later one. */
export const pageNote = (page: Page<unknown>): string | null =>
  page.before === 0 ? (page.after > 0 ? `+${page.after} more` : null) : `${page.from}–${page.to} of ${page.total}`

// ── the band ──────────────────────────────────────────────────────────────────────────────────

/** Cells between the parts of the band's row. */
export const BAND_GAP = 2

/** The most urgent item keeps at least this many cells; optional parts give way first. */
export const BAND_MIN_ITEM = 24

/** A second item shows from this width up (a normal band); below, it is counted in `+N more`. */
export const BAND_SECOND_ITEM = 110

export type BandPlanInput = {
  /** The band's `bodyColumns`: its width less the engine's `[-]`. */
  columns: number
  /** Items the band may show, most urgent first (one in a quiet band, two in a normal one). */
  items: number
  /** Every item that needs attention, shown or not. */
  total: number
  /** What each Button draws: `d: dashboard` (hotkey, colon, label). */
  buttons: readonly string[]
  /** The same Buttons with their short labels (`x: hide`), drawn when the full ones leave the item too little room. */
  short?: readonly string[]
  /** The chord teaching hint, or null once learned. */
  hint: string | null
  /** Cells before the items: the mark and the space after it. */
  lead?: number
}

/** `short`: the Buttons' short labels, and `+N` for `+N more`. */
export type BandPlan = { items: number; more: number; hint: boolean; short: boolean }

/** What the band says for the items it does not show: `+2 more`, or `+2` in its short form. */
export const moreLabel = (more: number, short: boolean): string => (more <= 0 ? '' : short ? `+${more}` : `+${more} more`)

/**
 * What fits on the band's one row, by priority: the mark, the first item always (it truncates at its end) and its
 * keys always; then the second item, from BAND_SECOND_ITEM cells and while each item keeps BAND_MIN_ITEM; the short
 * labels when the full ones would leave the first item under BAND_MIN_ITEM; then the chord hint, while the items
 * shown keep that room with it. What is not shown is counted in `+N more`.
 */
export const bandPlan = (input: BandPlanInput): BandPlan => {
  const width = (labels: readonly string[]): number => labels.reduce((sum, label) => sum + cells(label), 0) + Math.max(0, labels.length - 1) * BAND_GAP
  const room = (items: number, hint: boolean, short: boolean): number => {
    const more = moreLabel(input.total - items, short)
    const keys = width(short ? (input.short ?? input.buttons) : input.buttons)
    const parts = [keys, cells(more), hint && input.hint !== null ? cells(input.hint) : 0].filter(cell => cell > 0)
    const used = parts.reduce((sum, cell) => sum + cell, 0) + parts.length * BAND_GAP + (input.lead ?? 0)
    // What the shown items share, less the gap between two of them.
    return input.columns - used - (items > 1 ? BAND_GAP : 0)
  }
  let items = Math.max(1, Math.min(input.items, input.total))
  if (items > 1 && (input.columns < BAND_SECOND_ITEM || room(items, false, false) < items * BAND_MIN_ITEM)) items = 1
  const short = input.short !== undefined && room(items, false, false) < items * BAND_MIN_ITEM
  const hint = input.hint !== null && room(items, true, short) >= items * BAND_MIN_ITEM
  return { items, more: Math.max(0, input.total - items), hint, short }
}
