// Pure layout helpers for the mod's views (no `$`): text cut to a width with an ellipsis, and what the one-row
// band above the prompt has room for. Widths are terminal cells, one per character of the glyphs the views use.

/**
 * The terminal's height as a drawing last measured it. Render hooks see `e.viewport`; a command that opens a
 * pane does not, so the views remember it here. The one piece of module state in this file: a measurement, never
 * research or UI state, and a fresh module (a reload) simply starts without one.
 */
let measured: number | null = null

export const rememberViewport = (viewport: { rows: number } | undefined): void => {
  if (viewport !== undefined && Number.isFinite(viewport.rows) && viewport.rows > 0) measured = viewport.rows
}

export const measuredRows = (): number | null => measured

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
  /** The chord teaching hint, or null once learned. */
  hint: string | null
}

export type BandPlan = { items: number; more: number; hint: boolean }

/**
 * What fits on the band's one row: the first item always (it truncates at its end) and its keys always; then the
 * second item, from BAND_SECOND_ITEM cells and while each item keeps BAND_MIN_ITEM; then the chord hint, while the
 * items shown keep that room with it. What is not shown is counted in `+N more`.
 */
export const bandPlan = (input: BandPlanInput): BandPlan => {
  const keys = input.buttons.reduce((sum, label) => sum + cells(label), 0) + Math.max(0, input.buttons.length - 1) * BAND_GAP
  const room = (items: number, hint: boolean): number => {
    const more = input.total - items
    const parts = [keys, more > 0 ? cells(`+${more} more`) : 0, hint && input.hint !== null ? cells(input.hint) : 0].filter(width => width > 0)
    const used = parts.reduce((sum, width) => sum + width, 0) + parts.length * BAND_GAP
    // What the shown items share, less the gap between two of them.
    return input.columns - used - (items > 1 ? BAND_GAP : 0)
  }
  let items = Math.max(1, Math.min(input.items, input.total))
  if (items > 1 && (input.columns < BAND_SECOND_ITEM || room(items, false) < items * BAND_MIN_ITEM)) items = 1
  const hint = input.hint !== null && room(items, true) >= items * BAND_MIN_ITEM
  return { items, more: Math.max(0, input.total - items), hint }
}
