// Views — the project at a glance, drawn by code at zero tokens (charter: quiet by default).
//  - the band above the prompt (M080, M064, M214): one row of what needs attention, letter hotkeys only, and the
//    engine's focus chord (^X Tab) next to them until the person has used it three times — ahead of the keys' long
//    words and a second item, wherever the first item keeps its room beside it
//  - the dashboard pane (M069, M084): now (every band item with its action), phase map, deadlines, integrity,
//    tasks, the autoresearch loop — tabs on the digits 1–6
//  - /neuroflow:phase answered in code (M163, M011): a picker — arrows and Enter, or a click
//  - /neuroflow:dashboard opens the pane; its integrity tab freezes, verifies and unfreezes a
//    preregistration on a person's key press and confirmation (M018), through freeze.py
//  - /neuroflow:tasks opens the task boards of every level — project, flowie, each hive (M070, M163); a move runs
//    on Enter and the person's yes at project and flowie level, and goes into the prompt at a hive's for the person
//    to send (rule 16)
// Every view a command opens takes the keyboard, keys typed through that open are dropped, and every hotkey comes
// from the one key map in lib/keys.ts. A pane holds the keys while the person may be typing for the prompt, so no
// letter there writes, consents or starts a model turn: those actions are Enter on their row (never right after
// another key: actOn) and ask first, the safe answer on top (confirm); the band, reached by ^X Tab, keeps its
// letters. Each draws the one look (skills/neuroflow-develop → Visual style) for the width
// and height it gets, from the pure helpers of lib/layout.ts; tabLines and the row helpers below are its text form.
// Without the mod, commands/phase.md, commands/dashboard.md and commands/tasks.md do the same in prose.
import { atom, read, update } from 'claude-code'
import type { EngineInterface, On } from 'claude-code'

import type { NfBoard, NfCard, NfDashboardTab, NfDraftedDecision, NfDrive, NfFlowieSync, NfLoopView, NfSnapshot, NfTaskLevel, NfTaskView } from '../../../types'
import { completions } from '../lib/complete'
import { setActivePhase } from '../lib/config'
import { NO_SYNC, SYNC_QUEUE, asQueue, checkRemoteEntry, enqueue, syncState } from '../lib/flowiesync'
import type { NfIo } from '../lib/io'
import { BAND, CHORD, DASH, DASHBOARD_TABS, DIGITS, KEYS_LEARNED, LEARNED_AFTER, NAV, gridNeighbour, isPastTypeThrough, lineNeighbour, paneRows, tabNeighbour, unfocusedHint } from '../lib/keys'
import type { Direction } from '../lib/keys'
import {
  BOARD_GAP,
  BOARD_PAGE,
  MARK,
  WORDMARK,
  bandItemWidths,
  bandPlan,
  boardLayout,
  cells,
  fit,
  flowLine,
  isCompact,
  labelCell,
  measuredRows,
  moreLabel,
  pad,
  pageNote,
  pageOf,
  paneColumns,
  rememberViewport,
  rule,
  ruler,
  tabStrip,
  widthClass,
} from '../lib/layout'
import { appendLine, isoDate, sessionLine, sessionLogPath } from '../lib/memory'
import type { NfOptions } from '../lib/options'
import { join, resolveFrom, toSlash } from '../lib/paths'
import { PHASES, PHASE_GLYPH, isPhase, nextPhase, phaseLegend, phaseMap, phaseNodes, phaseStateMark, phaseSummary, pickerOrder, travelledTo } from '../lib/phases'
import { KNOWN_SCHEMA, loadSnapshot, versionNotice } from '../lib/project'
import { parseJson, runScript } from '../lib/scripts'
import { MINE, levelArgs, levelCardLine, levelSummary, loadTaskView, moveCommand, moveTargets, openColumnsOf, openingLevel, topCards } from '../lib/tasks'
import { pendingBandItem, pendingText } from '../lib/workbench'
import { isQuiet } from './scope'

const scopeAtom = atom({ plugin: 'neuroflow', key: 'scope' } as const, null)
const snapshotAtom = atom({ plugin: 'neuroflow', key: 'snapshot' } as const, null)
const activeCommandAtom = atom({ plugin: 'neuroflow', key: 'activeCommand' } as const, null)
const tabAtom = atom({ plugin: 'neuroflow', key: 'dashboardTab' } as const, 'now')
const bandHiddenAtom = atom({ plugin: 'neuroflow', key: 'bandHidden' } as const, false)
const loopViewAtom = atom({ plugin: 'neuroflow', key: 'loopView' } as const, null)
const pickerNoteAtom = atom({ plugin: 'neuroflow', key: 'pickerNote' } as const, null)
const draftAtom = atom({ plugin: 'neuroflow', key: 'draftedDecision' } as const, null)
const driveAtom = atom({ plugin: 'neuroflow', key: 'drive' } as const, null)
const captureAtom = atom({ plugin: 'neuroflow', key: 'capture' } as const, null)
const taskViewAtom = atom({ plugin: 'neuroflow', key: 'taskView' } as const, null)
const boardLevelAtom = atom({ plugin: 'neuroflow', key: 'boardLevel' } as const, null)
const boardPickAtom = atom({ plugin: 'neuroflow', key: 'boardPick' } as const, null)
const quietAtom = atom({ plugin: 'neuroflow', key: 'quietSince' } as const, null)
const flowieSyncAtom = atom({ plugin: 'neuroflow', key: 'flowieSync' } as const, NO_SYNC)
const wellbeingCheckAtom = atom({ plugin: 'neuroflow', key: 'wellbeingCheck' } as const, null)
const openedAtAtom = atom({ plugin: 'neuroflow', key: 'openedAt' } as const, {})
const keyAtAtom = atom({ plugin: 'neuroflow', key: 'keyAt' } as const, {})
const keysLearnedAtom = atom({ plugin: 'neuroflow', key: 'keysLearned' } as const, null)
const paneRingAtom = atom({ plugin: 'neuroflow', key: 'paneRing' } as const, {})

const DASHBOARD = 'nf-dashboard'
const PROJECTS_SCRIPT = 'skills/neuroflow-core/scripts/projects.py'
const PICKER = 'nf-phase'
const BOARD = 'nf-board'
/** $.store key: the ISO date on which the person hid the band (a preference, not research state). */
const BAND_HIDDEN_ON = 'band.hiddenOn'
/** The band's elements its ring starts on when it takes the keys: never one that writes or consents. */
const BAND_TAKES: readonly string[] = ['nf-band-dashboard', 'nf-wellbeing']

// ── pure helpers (exported for tests) ──────────────────────────────────────────────────────────

export type Tone = 'error' | 'warning' | 'success' | 'suggestion' | 'subtle'
export type Line = { text: string; tone?: Tone; dim?: boolean }
/** A press on the band runs one neuroflow command (the person's explicit request); `fill` puts it in the prompt instead. */
export type BandAction = { key: string; label: string; hotkey: string; command: string; args: string; fill?: boolean }
export type BandItem = { level: 'alert' | 'warn' | 'info'; glyph: string; text: string; actions?: BandAction[] }

export const when = (days: number): string => (days === 0 ? 'today' : days === 1 ? 'tomorrow' : `in ${days} days`)

/** "in 45 min", "today 14:00", "tomorrow 09:30" for a meeting starting `minutes` after `nowMs`. */
export const meetingWhen = (minutes: number, date: string, nowMs: number): string => {
  const time = /T(\d{2}:\d{2})/.exec(date)?.[1] ?? ''
  if (minutes < 0) return 'now'
  if (minutes < 90) return `in ${minutes} min`
  const start = new Date(nowMs + minutes * 60_000)
  const now = new Date(nowMs)
  const sameDay = start.getFullYear() === now.getFullYear() && start.getMonth() === now.getMonth() && start.getDate() === now.getDate()
  return `${sameDay ? 'today' : 'tomorrow'}${time ? ` ${time}` : ''}`
}

/** The band's line for a flowie sync the mod queued that is still waiting or did not go through; null when none. */
export const flowieSyncItem = (sync: NfFlowieSync | null): BandItem | null => {
  if (sync === null) return null
  const actions = [{ key: 'nf-flowie-sync', label: 'sync', hotkey: BAND.sync, command: 'neuroflow:flowie', args: '--sync' }]
  if (sync.failure !== null) return { level: 'warn', glyph: '!', text: `flowie not synced: ${sync.failure} — /neuroflow:flowie --sync`, actions }
  if (sync.pending.length > 0) {
    return {
      level: 'warn',
      glyph: '↻',
      text: `flowie sync pending (${sync.pending.join(', ')}) — it runs before your next neuroflow command or when a turn ends, or /neuroflow:flowie --sync`,
      actions,
    }
  }
  return null
}

/**
 * Whether a key's command goes into the prompt instead of running: while a flowie sync of the mod's waits (queued,
 * not held). A neuroflow command pulls the flowie first, which a check-in's uncommitted files make fail; and a
 * command a key runs ($.command.run) does not reach the mod's own hooks — so in the engine's test kit, and the types
 * say only "every hook but the calling one" — so the hook that syncs first (capture.ts) may never see it. Sent with
 * Enter, the command passes that hook.
 */
export const keyFillsPrompt = (sync: NfFlowieSync | null): boolean => sync !== null && sync.pending.length > 0 && !sync.isHeld

/** What the band may show, most urgent first. Quiet mode keeps alerts and warnings only. */
export const bandItems = (snap: NfSnapshot, quiet: boolean, sync: NfFlowieSync | null = null): BandItem[] => {
  const items: BandItem[] = []
  const ethics = snap.ethics
  if (ethics !== null && (ethics.status === 'expired' || ethics.status === 'withdrawn')) {
    items.push({ level: 'alert', glyph: '⚠', text: `ethics approval ${ethics.status} — no data collection` })
  }
  for (const deadline of snap.deadlines) {
    if (deadline.daysLeft <= 3) items.push({ level: 'alert', glyph: '⚠', text: `${deadline.what} — ${when(deadline.daysLeft)}` })
    else if (deadline.daysLeft <= 14) {
      items.push({ level: /ethic/i.test(deadline.what) ? 'warn' : 'info', glyph: '▸', text: `${deadline.what} — ${when(deadline.daysLeft)}` })
    }
  }
  if (snap.prereg?.status === 'frozen' && snap.prereg.setBy !== 'person') {
    items.push({ level: 'warn', glyph: '?', text: 'the preregistration "frozen" marker was not set by a person' })
  }
  for (const problem of snap.problems) items.push({ level: 'warn', glyph: '!', text: problem })
  // Meetings (M082): the next one within a day, and a past one left unclosed with open action items.
  const upcoming = snap.meetings.find(meeting => !meeting.closed && meeting.startsIn >= -15 && meeting.startsIn <= 24 * 60)
  if (upcoming !== undefined) {
    items.push({
      level: upcoming.startsIn <= 120 ? 'warn' : 'info',
      glyph: '▸',
      text: `meeting "${upcoming.title}" ${meetingWhen(upcoming.startsIn, upcoming.date, snap.loadedAt)}`,
      actions: [
        { key: 'nf-meet-prepare', label: 'prepare', hotkey: BAND.prepare, command: 'neuroflow:meeting', args: `--prepare ${upcoming.slug}` },
        { key: 'nf-meet-notes', label: 'notes', hotkey: BAND.notes, command: 'neuroflow:meeting', args: `--notes ${upcoming.slug}` },
      ],
    })
  }
  const unclosed = snap.meetings.find(meeting => !meeting.closed && meeting.startsIn < -120 && meeting.openActions > 0)
  if (unclosed !== undefined) {
    items.push({
      level: 'warn',
      glyph: '!',
      text: `meeting "${unclosed.title}" not closed — ${unclosed.openActions} open action item(s)`,
      actions: [{ key: 'nf-meet-close', label: 'close meeting', hotkey: BAND.closeMeeting, command: 'neuroflow:meeting', args: `--close ${unclosed.slug}` }],
    })
  }
  // A flowie sync the mod queued (wellbeing, ideas) that has not gone through yet; ahead of the version notice,
  // because /neuroflow:migrate skips a flowie with uncommitted changes.
  const syncing = flowieSyncItem(sync)
  if (syncing !== null) items.push(syncing)
  // Clicks on the claude.ai workbench wait for Claude Code (pending.json); `a` fills /neuroflow:tasks --apply-web.
  const web = pendingBandItem(snap.workbench ?? null)
  if (web !== null) items.push(web)
  // After a plugin update, until /neuroflow:migrate has run (neuroflow-core → Command lifecycle, version notice).
  // It waits behind the time-bound items: a meeting within two hours keeps the one quiet-band seat and its keys.
  const behind = versionNotice(snap)
  if (behind !== null) {
    items.push({
      level: 'warn',
      glyph: '↑',
      text: behind,
      actions: [{ key: 'nf-migrate', label: 'migrate', hotkey: BAND.migrate, command: 'neuroflow:migrate', args: '' }],
    })
  }
  if (!quiet) {
    if (snap.wikiPending > 0) {
      items.push({
        level: 'info',
        glyph: '✎',
        text: `${snap.wikiPending} wiki card${snap.wikiPending === 1 ? '' : 's'} waiting for review`,
        actions: [{ key: 'nf-wiki-review', label: 'review', hotkey: BAND.review, command: 'neuroflow:wiki', args: '--review' }],
      })
    }
    for (const loop of snap.loops.filter(item => /running/i.test(item.status))) {
      items.push({ level: 'info', glyph: '↻', text: `autoresearch ${loop.name}: iteration ${loop.iterations}, best ${loop.best}` })
    }
    const next = nextPhase(snap.phase, snap.recommendedPhases)
    if (next !== null) items.push({ level: 'info', glyph: '→', text: `next phase: ${next}` })
  }
  const rank = { alert: 0, warn: 1, info: 2 } as const
  const sorted = [...items].sort((a, b) => rank[a.level] - rank[b.level])
  return quiet ? sorted.filter(item => item.level !== 'info') : sorted
}

/**
 * The keys the band offers for the items it shows: the first item's own, and the version notice's migrate key
 * wherever the notice stands among them (a key already taken is not offered twice).
 */
export const bandActions = (shown: readonly BandItem[]): BandAction[] => {
  const actions = [...(shown[0]?.actions ?? [])]
  for (const item of shown.slice(1)) {
    for (const action of item.actions ?? []) {
      if (action.key === 'nf-migrate' && !actions.some(taken => taken.key === action.key || taken.hotkey === action.hotkey)) actions.push(action)
    }
  }
  return actions
}

/**
 * What a row of the dashboard's now tab does on Enter: a neuroflow command run (`command`) or put in the prompt for
 * the person to send (`fill`, as the band's key for it does), or one of the band's own acts.
 */
export type NowAct =
  | { kind: 'command'; command: string; args: string }
  | { kind: 'fill'; command: string; args: string }
  | { kind: 'keep' }
  | { kind: 'drop' }
  | { kind: 'stop-drive' }
  | { kind: 'stop-capture' }
export type NowAction = { key: string; label: string; act: NowAct }
export type NowRow = { level: BandItem['level']; glyph: string; text: string; actions: NowAction[] }
/** What the band draws besides its items, read from state as the band reads it. */
export type NowLive = { draft: NfDraftedDecision | null; drive: NfDrive | null; capture: { target: string; count: number } | null }

/**
 * The dashboard's now tab: every item the band can show, whatever the quiet setting, each with its action — the
 * drafted decision, the loop being driven and a live note capture first, as on the band. The version notice is
 * the pane's Update line, above every tab. A pane that holds the keys must never turn typed words into a write, a
 * consent or a paid turn, so an action has no letter: it runs on Enter on its row, never an Enter that follows
 * another key within TYPE_THROUGH_MS, and asks first (runNow); j and k start on the tab's own name (NOW_START).
 */
export const nowRows = (snap: NfSnapshot, sync: NfFlowieSync | null, live: NowLive): NowRow[] => {
  const rows: NowRow[] = []
  if (live.draft !== null) {
    rows.push({
      level: 'warn',
      glyph: '✎',
      text: `decision drafted for ${live.draft.phase}: ${live.draft.statement}`,
      actions: [
        { key: 'nf-now-draft-keep', label: 'keep', act: { kind: 'keep' } },
        { key: 'nf-now-draft-drop', label: 'drop', act: { kind: 'drop' } },
      ],
    })
  }
  if (live.drive !== null) {
    rows.push({
      level: 'info',
      glyph: '↻',
      text: `driving autoresearch "${live.drive.name}" · turn ${live.drive.turns}${live.drive.errors > 0 ? ` · ${live.drive.errors} error(s) in a row` : ''}`,
      actions: [{ key: 'nf-now-drive-stop', label: 'stop', act: { kind: 'stop-drive' } }],
    })
  }
  if (live.capture !== null) {
    rows.push({
      level: 'warn',
      glyph: '✎',
      text: `capturing notes → ${live.capture.target} · ${live.capture.count} entr${live.capture.count === 1 ? 'y' : 'ies'} · messages are not sent to the model`,
      actions: [{ key: 'nf-now-capture-stop', label: 'stop', act: { kind: 'stop-capture' } }],
    })
  }
  const notice = versionNotice(snap)
  for (const item of bandItems(snap, false, sync)) {
    if (item.text === notice) continue
    rows.push({
      level: item.level,
      glyph: item.glyph,
      text: item.text,
      actions: (item.actions ?? []).map(action => ({
        key: `nf-now-${action.key.replace(/^nf-/, '')}`,
        label: action.label,
        act: { kind: action.fill ? 'fill' : 'command', command: action.command, args: action.args },
      })),
    })
  }
  if (snap.wellbeingDue) rows.push({ level: 'info', glyph: '·', text: 'wellbeing check-in due — the band asks for it, or /neuroflow:flowie --assess', actions: [] })
  return rows
}

/**
 * Where j and k start on the now tab while the ring is on none of its rows: the shown tab's own name (`1: now`),
 * which only reads the tab again. Never an action, so a j or k typed for the prompt leaves the ring on nothing
 * that writes.
 */
export const NOW_START = 'nf-tab-now'

/**
 * The now tab's stops in the order j and k walk them, as they stand from the top: the Update line's migrate, the
 * tab's name (where they start, NOW_START), then each row's actions. None when there is no action to reach.
 */
export const nowRingKeys = (rows: readonly NowRow[], isBehind: boolean): string[] => {
  const actions = rows.flatMap(row => row.actions.map(action => action.key))
  if (!isBehind && actions.length === 0) return []
  return [...(isBehind ? ['nf-dash-migrate'] : []), NOW_START, ...actions]
}

/** The keys of the cards a board draws, column by column; none on a read-only board, whose cards are text. */
export const cardKeys = (level: Pick<NfTaskLevel, 'kind' | 'board'>): string[][] =>
  level.kind === 'remote' ? [] : level.board.columns.map(column => column.cards.map(card => `nf-card-${card.slug}`))

/** The column of a card the board draws, or null. */
export const cardColumn = (board: NfBoard, slug: string): string | null =>
  board.columns.find(column => column.cards.some(card => card.slug === slug))?.id ?? null

/**
 * The board's foot: what is done and archived, the level, and a word for each mark its cards carry — `◆ Oddball EEG
 * (this project)` at flowie and hive level, `⚠ overdue` (commands/tasks.md → Rendering).
 */
export const boardFoot = (level: Pick<NfTaskLevel, 'kind' | 'name' | 'mine' | 'project' | 'board'>): string => {
  const marked = (level.kind === 'flowie' || level.kind === 'hive') && level.mine > 0 && level.project !== null
  const overdue = level.board.columns.some(column => column.cards.some(card => card.overdue))
  return [
    `done ${level.board.done}`,
    `archived ${level.board.archived}`,
    `level: ${level.name}`,
    ...(marked ? [`${MINE} ${level.project} (this project)`] : []),
    ...(overdue ? ['⚠ overdue'] : []),
  ].join(' · ')
}

/** The target the ring goes to once a card is picked: the column after the card's, else the first target. */
export const firstTarget = (board: NfBoard, from: string | null): string | null => {
  const ids = openColumnsOf(board)
  const targets = moveTargets(board, from)
  return ids.slice(from === null ? 0 : ids.indexOf(from) + 1).find(id => targets.includes(id)) ?? targets[0] ?? null
}

/**
 * Where h, j, k or l takes the board's ring from `at`: card to card on the board's grid; once a card is picked,
 * target to target (h and k back, j and l on). Null on a read-only board, whose cards are text.
 */
export const boardRingTarget = (level: Pick<NfTaskLevel, 'kind' | 'board'>, pick: string | null, at: string | null, direction: Direction): string | null => {
  if (level.kind === 'remote') return null
  if (pick === null && (direction === 'left' || direction === 'right')) {
    // Beside a column it lands on the same row of what the neighbour shows: its first page while the ring is elsewhere.
    const columns = cardKeys(level).filter(column => column.length > 0)
    const col = at === null ? -1 : columns.findIndex(column => column.includes(at))
    const here = columns[col]
    if (here === undefined || at === null) return columns[0]?.[0] ?? null
    const there = columns[direction === 'right' ? col + 1 : col - 1]
    return there === undefined ? at : (there[Math.min(there.length - 1, here.indexOf(at) % BOARD_PAGE)] ?? at)
  }
  if (pick === null) return gridNeighbour(cardKeys(level), at, direction)
  const keys = moveTargets(level.board, cardColumn(level.board, pick)).map(target => `nf-move-${target}`)
  return lineNeighbour(keys, at, direction === 'left' || direction === 'up' ? -1 : 1)
}

const BARS = '▁▂▃▄▅▆▇█'

/** A text sparkline of the last `width` values (works on every surface, read aloud as numbers). */
export const sparkline = (values: readonly number[], width = 24): string => {
  const tail = values.slice(-width)
  if (tail.length === 0) return ''
  const min = Math.min(...tail)
  const max = Math.max(...tail)
  return tail.map(value => BARS[max === min ? 3 : Math.round(((value - min) / (max - min)) * (BARS.length - 1))]).join('')
}

/** The "Running" column of an autoresearch results.md table. */
export const parseRunning = (resultsMd: string): number[] => {
  let column = -1
  const out: number[] = []
  for (const line of resultsMd.split(/\r?\n/)) {
    if (!line.trim().startsWith('|')) continue
    const cells = line.split('|').map(cell => cell.trim())
    if (column < 0) {
      column = cells.findIndex(cell => /^running$/i.test(cell))
      continue
    }
    const value = Number.parseFloat(cells[column] ?? '')
    if (Number.isFinite(value)) out.push(value)
  }
  return out
}

/** The bullet lines under "## Open questions" at the top of an autoresearch report.md. */
export const parseOpenQuestions = (reportMd: string, max = 3): string[] => {
  const out: string[] = []
  let inside = false
  for (const line of reportMd.split(/\r?\n/)) {
    if (/^##\s+open questions/i.test(line)) {
      inside = true
      continue
    }
    if (inside && /^##\s/.test(line)) break
    if (inside && /^\s*-\s+/.test(line)) out.push(line.replace(/^\s*-\s+/, '').replace(/\*\*/g, ''))
  }
  return out.slice(0, max)
}

const label = (id: string | null): string => PHASES.find(phase => phase.id === id)?.label ?? ''

const LEVEL_TONE: Record<BandItem['level'], Tone | undefined> = { alert: 'error', warn: 'warning', info: undefined }

/**
 * The tasks tab (commands/dashboard.md → Tasks): open tasks per level on one line, this project's share in
 * brackets, then the first open cards across levels — this project's first, overdue first, then by due date —
 * each tagged with its level. Every mark has a word in the last line.
 */
export const taskLines = (view: NfTaskView | null, max = 5): Line[] => {
  if (view === null) return [{ text: 'Reading the task boards…', dim: true }]
  const cards = topCards(view, max)
  const key = [...cardLegend(view, max), '/neuroflow:tasks opens the boards (digits pick the level)']
  return [
    { text: levelSummary(view) },
    ...(cards.length === 0
      ? [{ text: 'No open tasks.', dim: true }]
      : cards.map(({ level, card }) => ({ text: `[${level.name}] ${levelCardLine(card, level.kind)}`, tone: card.overdue ? ('warning' as Tone) : undefined }))),
    { text: key.join(' · '), dim: true },
  ]
}

/** The dashboard body for one tab, as plain lines (the text form every surface can show). */
export const tabLines = (tab: NfDashboardTab, snap: NfSnapshot, loop: NfLoopView | null, tasks: NfTaskView | null = null): Line[] => {
  if (tab === 'now') {
    const notice = versionNotice(snap)
    const items = bandItems(snap, false).filter(item => item.text !== notice)
    if (items.length === 0) return [{ text: 'Nothing needs your attention.', dim: true }]
    return items.map(item => ({
      text: `${item.glyph} ${item.text}${(item.actions ?? []).length > 0 ? ` — ${(item.actions ?? []).map(action => action.label).join(', ')}` : ''}`,
      tone: LEVEL_TONE[item.level],
    }))
  }
  if (tab === 'phase') {
    const nodes = phaseNodes(snap.phase, snap.phasesVisited, snap.recommendedPhases)
    const next = nextPhase(snap.phase, snap.recommendedPhases)
    return [
      { text: nodes.length === 0 ? 'No phases recorded yet.' : phaseMap(snap.phase, snap.phasesVisited, snap.recommendedPhases) },
      { text: `Current: ${snap.phase ?? 'none'}${snap.phase ? ` — ${label(snap.phase)}` : ''}` },
      ...(next !== null ? [{ text: `Next: /neuroflow:${next} — ${label(next)}`, dim: true }] : []),
      ...(nodes.length > 0 ? [{ text: phaseLegend(nodes), dim: true }] : []),
    ]
  }
  if (tab === 'deadlines') {
    if (snap.deadlines.length === 0) return [{ text: 'No upcoming dates in .neuroflow/timeline.md.', dim: true }]
    return snap.deadlines.slice(0, 12).map(deadline => ({
      text: `${deadline.daysLeft <= 3 ? '⚠' : deadline.daysLeft <= 14 ? '▸' : '·'} ${deadline.date}  ${deadline.what} — ${when(deadline.daysLeft)}${deadline.gates ? `  (gates ${deadline.gates})` : ''}`,
      tone: deadline.daysLeft <= 3 ? 'error' : deadline.daysLeft <= 14 ? 'warning' : undefined,
    }))
  }
  if (tab === 'integrity') {
    const lines: Line[] = []
    const ethics = snap.ethics
    if (ethics === null) lines.push({ text: '· ethics: no status yet — /neuroflow:ethics', dim: true })
    else {
      const ok = ethics.status === 'approved' && ethics.setBy === 'person'
      lines.push({
        text: `${ok ? '✔' : '⚠'} ethics ${ethics.status}${ethics.expires ? ` · expires ${ethics.expires}` : ''}${ethics.setBy !== 'person' ? ' · not set by a person' : ''}`,
        tone: ok ? 'success' : 'warning',
      })
      if (ethics.aiProcessing !== null) lines.push({ text: `  participant data the model may read: ${ethics.aiProcessing}`, dim: true })
    }
    const prereg = snap.prereg
    if (prereg === null) lines.push({ text: '· preregistration: none frozen', dim: true })
    else if (prereg.status === 'frozen') {
      const trusted = prereg.setBy === 'person'
      lines.push({
        text: `${trusted ? '■' : '?'} preregistration frozen${prereg.frozenAt ? ` ${prereg.frozenAt.slice(0, 10)}` : ''} · ${Object.keys(prereg.files).length} file(s)${trusted ? '' : ' · marker not set by a person'}`,
        tone: trusted ? 'success' : 'warning',
      })
      if (prereg.plannedN !== null) lines.push({ text: `  planned N: ${prereg.plannedN}`, dim: true })
    } else lines.push({ text: `· preregistration: ${prereg.status}`, dim: true })
    lines.push({ text: snap.rawRoots.length > 0 ? `■ read-only raw data: ${snap.rawRoots.join(', ')}` : '· no raw-data folders declared (raw_roots)', dim: snap.rawRoots.length === 0 })
    for (const problem of snap.problems) lines.push({ text: `! ${problem}`, tone: 'warning' })
    return lines
  }
  if (tab === 'tasks') return taskLines(tasks)
  if (loop === null) return [{ text: snap.loops.length === 0 ? 'No autoresearch loops.' : 'Loading the loop…', dim: true }]
  const last = loop.running.length > 0 ? loop.running[loop.running.length - 1] : null
  return [
    { text: `${loop.name} (${loop.phase}) · ${loop.status} · iteration ${loop.iterations} · best ${loop.best}` },
    { text: loop.running.length > 0 ? `quality ${sparkline(loop.running)}  ${last !== null && last !== undefined && last > 0 ? '+' : ''}${last ?? ''}` : 'no iterations recorded yet', dim: loop.running.length === 0 },
    ...(loop.questions.length > 0
      ? [{ text: 'Open questions:', tone: 'warning' as Tone }, ...loop.questions.map(question => ({ text: `  ${question}` }))]
      : [{ text: 'No open questions.', dim: true }]),
    { text: 'Answer in the session (A3: …) or in the loop\'s answers.md.', dim: true },
  ]
}

// ── the dashboard's rows as the pane lays them out (pure; tabLines above stays the plain-text form) ──

/** Right of the wordmark: project · phase · mode. */
export const dashboardTitle = (snap: NfSnapshot): string =>
  `${snap.projectName ?? 'neuroflow project'} · ${snap.phase ?? 'no phase'}${snap.mode ? ` · ${snap.mode}` : ''}`

/** A date's mark (commands/dashboard.md → Dates): ⚠ within three days, ▸ within 14, · later; rank 0 is the most urgent. */
export const dateMark = (daysLeft: number): { glyph: string; tone?: Tone; rank: number } =>
  daysLeft <= 3 ? { glyph: '⚠', tone: 'error', rank: 0 } : daysLeft <= 14 ? { glyph: '▸', tone: 'warning', rank: 1 } : { glyph: '·', rank: 2 }

/** A row under an UPPERCASE dim label: `PHASE   ● ideation ─ ◉ analyze ─ → paper`. */
export type LabelRow = { label: string; value: string; tone?: Tone; dim?: boolean }

/** A running loop (or the first one) as one line, with its sparkline once its results are read. */
export const loopSummary = (loop: NfSnapshot['loops'][number], view: NfLoopView | null): string =>
  `${loop.name} · ${loop.status} · iteration ${loop.iterations} · best ${loop.best}${view !== null && view.name === loop.name && view.running.length > 0 ? `  ${sparkline(view.running, 12)}` : ''}`

/** The now tab's summary under what needs attention, as commands/dashboard.md's block has it: PHASE, TASKS, LOOP. */
export const nowSummary = (snap: NfSnapshot, tasks: NfTaskView | null, loop: NfLoopView | null): LabelRow[] => {
  const phase = phaseSummary(snap.phase, snap.phasesVisited, snap.recommendedPhases)
  const running = snap.loops.find(item => /running/i.test(item.status)) ?? snap.loops[0]
  return [
    { label: 'PHASE', value: phase === '' ? 'no phases recorded yet' : phase, dim: phase === '' },
    { label: 'TASKS', value: tasks === null ? 'reading the task boards…' : levelSummary(tasks), dim: tasks === null },
    ...(running === undefined ? [] : [{ label: 'LOOP', value: loopSummary(running, loop) }]),
  ]
}

/** One row of the integrity tab: a glyph, what it is, its state, who set it, and the lines under it. */
export type IntegrityRow = { glyph: string; tone?: Tone; name: string; value: string; note: string | null; more: string[]; dim?: boolean }

/**
 * The integrity tab (commands/dashboard.md → Integrity): ethics, the preregistration and the raw data. An approved
 * or frozen marker a person did not set reads `?` and "not set by a person".
 */
export const integrityRows = (snap: NfSnapshot): IntegrityRow[] => {
  const rows: IntegrityRow[] = []
  const ethics = snap.ethics
  if (ethics === null) {
    rows.push(
      snap.ethicsNotApplicable
        ? { glyph: '·', name: 'ethics', value: 'not applicable: no participant data', note: null, more: [], dim: true }
        : { glyph: '·', name: 'ethics', value: 'no status yet — /neuroflow:ethics', note: null, more: [], dim: true },
    )
  } else {
    const byPerson = ethics.setBy === 'person'
    const ended = ethics.status === 'expired' || ethics.status === 'withdrawn'
    const approved = ethics.status === 'approved'
    rows.push({
      glyph: ended ? '⚠' : approved ? (byPerson ? '✔' : '?') : '·',
      tone: ended ? 'error' : approved ? (byPerson ? 'success' : 'warning') : undefined,
      name: 'ethics',
      value: `${ethics.status}${ethics.expires ? ` · expires ${ethics.expires}` : ''}`,
      note: approved ? (byPerson ? 'set by a person' : 'not set by a person') : null,
      more: ethics.aiProcessing !== null ? [`model may read: ${ethics.aiProcessing}`] : [],
    })
  }
  const prereg = snap.prereg
  if (prereg === null) rows.push({ glyph: '·', name: 'preregistration', value: 'none frozen', note: null, more: [], dim: true })
  else if (prereg.status === 'frozen') {
    const byPerson = prereg.setBy === 'person'
    const count = Object.keys(prereg.files).length
    rows.push({
      glyph: byPerson ? '■' : '?',
      tone: byPerson ? 'success' : 'warning',
      name: 'preregistration',
      value: `frozen${prereg.frozenAt ? ` ${prereg.frozenAt.slice(0, 10)}` : ''} · ${count} file${count === 1 ? '' : 's'}`,
      note: byPerson ? 'set by a person' : 'not set by a person',
      more: prereg.plannedN !== null ? [`planned N: ${prereg.plannedN}`] : [],
    })
  } else rows.push({ glyph: '·', name: 'preregistration', value: prereg.status, note: null, more: [], dim: true })
  rows.push(
    snap.rawRoots.length > 0
      ? { glyph: '■', name: 'raw data', value: `read-only: ${snap.rawRoots.join(', ')}`, note: null, more: [] }
      : { glyph: '·', name: 'raw data', value: 'no folders declared (raw_roots)', note: null, more: [], dim: true },
  )
  return rows
}

/** One row of the deadlines tab: its mark, the date, what, when, and the phase it gates. */
export type DateRow = { glyph: string; tone?: Tone; rank: number; days: number; date: string; what: string; when: string; gates: string | null }

export const dateRows = (snap: NfSnapshot, max = 12): DateRow[] =>
  snap.deadlines.slice(0, max).map(deadline => ({
    ...dateMark(deadline.daysLeft),
    days: deadline.daysLeft,
    date: deadline.date,
    what: deadline.what,
    when: when(deadline.daysLeft),
    gates: deadline.gates,
  }))

/** One row of the tasks tab: its marks (◆ ⚠ ↻), the title, owner, due date and level. */
export type CardRow = { marks: string; title: string; owner: string; due: string; level: string; overdue: boolean }

export const cardRows = (view: NfTaskView, max = 5): CardRow[] =>
  topCards(view, max).map(({ level, card }) => ({
    marks: [card.isMine && level.kind !== 'project' && level.kind !== 'remote' ? MINE : '', card.overdue ? '⚠' : '', card.web ? '↻' : ''].filter(Boolean).join(' '),
    title: card.title,
    owner: card.owner ? `@${card.owner}` : '',
    due: card.due ? `due ${card.due.slice(5)}` : '',
    level: level.name,
    overdue: card.overdue,
  }))

/** What the marks on the first cards mean, one phrase each: `◆ this project (Oddball EEG) · ⚠ overdue`. */
export const cardLegend = (view: NfTaskView, max = 5): string[] => {
  const cards = topCards(view, max)
  // This project's name at each level its marked cards come from (the flowie's and a hive's may differ).
  const names = [...new Set(cards.filter(({ level, card }) => card.isMine && (level.kind === 'flowie' || level.kind === 'hive')).map(({ level }) => level.project))].filter(
    (name): name is string => name !== null,
  )
  return [
    ...(names.length > 0 ? [`${MINE} this project (${names.join(', ')})`] : []),
    ...(cards.some(({ card }) => card.overdue) ? ['⚠ overdue'] : []),
    ...(cards.some(({ card }) => card.web === true) ? ['↻ a workbench change waits'] : []),
  ]
}

/** The dates ruler's mark row in runs: blanks as they are, each mark with its tone (⚠ error, ▸ warning, · dim). */
export const markRuns = (marks: string): { text: string; tone?: Tone; dim?: boolean }[] =>
  marks
    .split(/([⚠▸·])/)
    .filter(part => part !== '')
    .map(part => (part === '⚠' ? { text: part, tone: 'error' as Tone } : part === '▸' ? { text: part, tone: 'warning' as Tone } : part === '·' ? { text: part, dim: true } : { text: part }))

// ── engine side ────────────────────────────────────────────────────────────────────────────────

const ioOf = ($: EngineInterface): NfIo => ({
  read: path => $.fs.read(path).then(text => (typeof text === 'string' ? text : null), () => null),
  exists: path => $.fs.exists(path).catch(() => false),
  list: path => $.fs.list(path).then(entries => entries.map(entry => ({ name: entry.name, isDir: entry.kind === 'dir' || String(entry.kind) === 'directory' })), () => []),
  write: (path, text) => $.fs.write(path, text),
  home: async () => (await $.env.get('HOME')) ?? (await $.env.get('USERPROFILE')),
  now: () => $.clock.now(),
  run: (argv, init) => $.process.run(argv, init),
  pluginRoot: $.plugin.root,
})

const reload = async ($: EngineInterface, root: string): Promise<void> => {
  const snapshot = await loadSnapshot(ioOf($), root)
  await update($, snapshotAtom, () => snapshot)
}

/**
 * Forgets where a pane's ring stood: it is on none of the pane's elements now (an open, a tab change, one of the
 * engine's own stops), so j, k, h and l start again where they start from nothing.
 */
const forgetRing = ($: EngineInterface, pane: string): Promise<unknown> =>
  update($, paneRingAtom, ring => {
    const { [pane]: _forgotten, ...rest } = ring
    return rest
  })

/**
 * A pane opens asking for the keys: from now, keys typed within TYPE_THROUGH_MS are taken as typed through, and its
 * ring starts afresh — on nothing, or on the element drawn `autoFocus` (whose take the ui.focus hook records).
 */
const markOpened = async ($: EngineInterface, id: string): Promise<void> => {
  const now = await $.clock.now()
  await update($, openedAtAtom, opened => ({ ...opened, [id]: now }))
  await forgetRing($, id)
}

/** Notes a key of a pane — a press, or a move of its ring the mod made: an Enter on an action right after it is dropped. */
const noteKey = async ($: EngineInterface, id: string): Promise<void> => {
  const now = await $.clock.now()
  await update($, keyAtAtom, keys => ({ ...keys, [id]: now }))
}

/**
 * A press handler for one of a pane's keys (a tab or a level, h, j, k, l, r, q, x, the views it opens): dropped while
 * typed through a focused open (lib/keys.ts → TYPE_THROUGH_MS), so a person who presses Enter on the command and keeps
 * typing never acts there. Every press is noted for the guard of the actions (actOn).
 */
const act =
  ($: EngineInterface, id: string, run: () => unknown) =>
  async (): Promise<void> => {
    const now = await $.clock.now()
    const opened = (await read($, openedAtAtom))[id]
    await noteKey($, id)
    if (!isPastTypeThrough(now, opened)) return
    await run()
  }

/**
 * A press handler for an action — a now-tab row, the Update line's migrate, a card, a move target, freeze — which has
 * no letter: Enter on it with the ring there, or a click. Dropped while typed through the open and within
 * TYPE_THROUGH_MS of the pane's last key or ring move: `ok⏎` typed for the prompt moves the ring with its `k`, and its
 * Enter must not press what the ring then stands on. An action that writes, consents or starts a model turn asks
 * first besides (confirm). A move of the ring by the person (Tab, a click) is not counted: a click is that move and
 * the press at once.
 */
const actOn =
  ($: EngineInterface, id: string, run: () => unknown) =>
  async (): Promise<void> => {
    const now = await $.clock.now()
    const opened = (await read($, openedAtAtom))[id]
    const last = (await read($, keyAtAtom))[id]
    await noteKey($, id)
    if (!isPastTypeThrough(now, opened, last)) return
    await run()
  }

/**
 * Asks before an action of a pane writes, consents or starts a model turn: the engine's question dialog with the safe
 * answer first, so a stray Enter there answers no. Only the exact yes acts — a dismissed dialog, an answer typed under
 * "Other" and a run with nobody to ask all mean no.
 */
const confirm = async ($: EngineInterface, question: string, no: string, yes: string, header: string): Promise<boolean> =>
  (await $.ui.ask(question, { options: [no, yes], header }).catch(() => no)) === yes

/**
 * The deadlines tab's gates column: as wide as its longest `gates …` text, but never more than 22 cells or a quarter of
 * the pane, so free text in timeline.md cannot squeeze the date names to nothing; a longer text is cut at its end.
 */
export const gatesColumnWidth = (rows: readonly { gates: string | null }[], width: number, size: string): number =>
  size === 'narrow' ? 0 : Math.min(Math.max(0, ...rows.map(row => (row.gates ? cells(`gates ${row.gates}`) : 0))), 22, Math.floor(width / 4))

/** The question before a key's command runs: a model turn the person starts. */
export const runQuestion = (command: string, args: string): string =>
  `Run /${command}${args === '' ? '' : ` ${args}`} now? It starts a model turn.`

/** Moves the pane's focus ring onto one of its elements and remembers it there (j, k, h, l; a picked card). */
const focusRing = async ($: EngineInterface, pane: string, key: string): Promise<void> => {
  const result = await $.ui.focus({ requestId: pane, key }).catch((): { deny?: string } => ({ deny: 'no ring' }))
  await noteKey($, pane)
  if (result.deny === undefined) await update($, paneRingAtom, ring => ({ ...ring, [pane]: key }))
}

/**
 * j and k in a list of rows: the next or the previous one from where the ring is; while it is on none of them, the
 * harmless `start` (lib/keys.ts → lineNeighbour). The ring is moved even onto the element the mod last recorded:
 * should the record be stale, the move mends it.
 */
const stepRing = async ($: EngineInterface, pane: string, keys: readonly string[], step: 1 | -1, start?: string): Promise<void> => {
  const at = (await read($, paneRingAtom))[pane] ?? null
  const to = lineNeighbour(keys, at, step, start)
  if (to !== null) await focusRing($, pane, to)
}

/**
 * Moves the ring on the board, the drawing first: the card is remembered before the ring moves, so a card past a
 * column's first five is drawn (its page turned) before the engine's ring goes onto it; where the ring cannot move
 * (the pane does not hold the keys), the remembered card still marks where h, j, k and l go on from.
 */
const ringTo = async ($: EngineInterface, pane: string, key: string): Promise<void> => {
  await update($, paneRingAtom, ring => ({ ...ring, [pane]: key }))
  await $.ui.focus({ requestId: pane, key }).catch(() => ({ deny: 'no ring' }))
  await noteKey($, pane)
}

/** Sets the active phase as the person asked: config, session log, reasoning log, snapshot. */
const switchPhase = async ($: EngineInterface, phase: string, via: string): Promise<string> => {
  const scope = await read($, scopeAtom)
  if (scope?.root === null || scope === null) return 'No neuroflow project here.'
  const io = ioOf($)
  const snap = await read($, snapshotAtom)
  if (snap !== null && snap.nfSchema !== null && snap.nfSchema > KNOWN_SCHEMA) {
    return `This project uses config schema ${snap.nfSchema}, newer than this plugin knows (${KNOWN_SCHEMA}) — update neuroflow before switching phases.`
  }
  const path = join(scope.root, '.neuroflow/project_config.md')
  const before = await io.read(path)
  // active_phase only: plugin_version is the version the project was last brought up to date to, written only by the
  // scaffold and /neuroflow:migrate (neuroflow-core → the config contract), so the version notice stays until then.
  const after = before === null ? null : setActivePhase(before, phase)
  if (after === null) return 'This project_config.md format cannot be edited safely — run /neuroflow:migrate first.'
  if (after !== before) await io.write(path, after)
  const now = await io.now()
  await appendLine(io, sessionLogPath(scope.root, now), sessionLine(now, 'phase', `Active phase → ${phase} (${via})`))
  const entry = JSON.stringify({
    statement: `Active phase set to ${phase}`,
    source: `mod:${via} | ${isoDate(now)}`,
    reasoning: `Chosen by the person in the ${via}.`,
    at: new Date(now).toISOString(),
    drafted_by: 'mod',
    approved_by: 'person',
  })
  await appendLine(io, join(scope.root, '.neuroflow/reasoning/general.jsonl'), entry)
  await reload($, scope.root)
  // The slash menu marks the current and next phase (M065); its cached descriptions are stale now.
  await $.ui.invalidate('command.describe')
  // The prose records a switch on the project's cards (commands/phase.md, steps 7 and 8: the flowie, and a team
  // card after the person's yes); the mod does not write there, so it hands that to /neuroflow:phase --sync.
  const home = await io.home()
  const linked =
    (snap?.flowieProfiles.length ?? 0) > 0 ||
    (home ? (await loadTaskView(io, scope.root, toSlash(home), isoDate(now)).catch(() => null))?.card != null : false)
  if (linked && (await isPersonThere($))) {
    await $.prompt.fill({ text: '/neuroflow:phase --sync' })
    return `Active phase is now ${phase}. Press Enter to record it on your flowie and the team's card (/neuroflow:phase --sync).`
  }
  return `Active phase is now ${phase}.`
}

const loadLoopView = async ($: EngineInterface): Promise<void> => {
  const snap = await read($, snapshotAtom)
  if (snap === null) return
  const loop = snap.loops.find(item => /running/i.test(item.status)) ?? snap.loops[0]
  if (loop === undefined) {
    await update($, loopViewAtom, () => null)
    return
  }
  const io = ioOf($)
  const dir = resolveFrom(snap.root, loop.location)
  const results = (await io.read(join(dir, 'results.md'))) ?? ''
  const report = (await io.read(join(dir, 'report.md'))) ?? ''
  const view: NfLoopView = {
    name: loop.name,
    phase: loop.phase,
    status: loop.status,
    iterations: loop.iterations,
    best: loop.best,
    running: parseRunning(results),
    questions: parseOpenQuestions(report),
  }
  await update($, loopViewAtom, () => view)
}

/**
 * Reads every level's task board (commands/tasks.md → Levels) into state: the project's, the flowie's and each
 * hive clone's, as the local files are — the mod never pulls, writes or moves a task file.
 */
const loadTasks = async ($: EngineInterface, refresh = false): Promise<void> => {
  const scope = await read($, scopeAtom)
  if (scope?.root === null || scope === null) return
  const io = ioOf($)
  const home = await io.home()
  const view = await loadTaskView(io, scope.root, home ? toSlash(home) : null, isoDate(await io.now()))
  await update($, taskViewAtom, () => view)
  if (refresh && view.hasRemote && view.card) void refreshRemoteBoards($, view.card, scope.root).catch(() => undefined)
}

/** When the remote boards may be refreshed again, per card: a minute after a refresh, ten after one that failed. */
const remoteNext = new Map<string, number>()
let remoteRefreshing: Promise<void> | null = null

/**
 * The boards of this project's other repositories (neuroflow-core → Project registry) come from the cache projects.py
 * keeps in ~/.neuroflow/boards/: when the person opens the tasks, it is refreshed from their remotes in the background
 * (a shallow, sparse fetch of .neuroflow/tasks/ only — nothing leaves), and the boards are read again once it is done.
 */
const refreshRemoteBoards = ($: EngineInterface, card: string, root: string): Promise<void> => {
  if (remoteRefreshing !== null) return remoteRefreshing
  const run = (async () => {
    const now = await $.clock.now()
    if (now < (remoteNext.get(card) ?? 0)) return
    remoteNext.set(card, now + 60_000)
    // --root: this repository needs no cache. Its git runs with hooks off and no prompt (projects.py).
    const result = await runScript(ioOf($), PROJECTS_SCRIPT, ['refresh', '--project', card, '--root', root, '--json'], { timeoutMs: 180_000 })
    if (result.exitCode !== 0) remoteNext.set(card, (await $.clock.now()) + 10 * 60_000)
    await loadTasks($, false)
  })()
  remoteRefreshing = run.finally(() => {
    remoteRefreshing = null
  })
  return remoteRefreshing
}

/**
 * What a tab needs read before it draws: the loop's files, every level's board. The now tab's summary reads the
 * loop and, without waiting for them (its TASKS row says so meanwhile), the local boards.
 */
const loadTab = async ($: EngineInterface, tab: NfDashboardTab): Promise<void> => {
  if (tab === 'loop' || tab === 'now') await loadLoopView($)
  if (tab === 'tasks') await loadTasks($, true)
  if (tab === 'now') void loadTasks($, false).catch(() => undefined)
}

/** Shows a tab. The ring was on the last tab's rows or on a tab key: j and k start on this one afresh. */
const selectTab = async ($: EngineInterface, tab: NfDashboardTab): Promise<void> => {
  await update($, tabAtom, () => tab)
  await forgetRing($, DASHBOARD)
  await loadTab($, tab)
}

/** r on the dashboard: the project's files and the shown tab's read again. */
const rereadDashboard = async ($: EngineInterface): Promise<void> => {
  const scope = await read($, scopeAtom)
  if (scope !== null && scope.root !== null) await reload($, scope.root)
  await loadTab($, await read($, tabAtom))
}

/**
 * Opens the dashboard holding the keys (a request the engine grants over an empty prompt; again on an open one,
 * which focuses it). Without a tab, on the one it showed last — the now tab in a fresh session.
 */
const openDashboard = async ($: EngineInterface, tab?: string): Promise<void> => {
  const wanted = DASHBOARD_TABS.find(item => item.id === tab)
  if (wanted !== undefined) await selectTab($, wanted.id)
  else await loadTab($, await read($, tabAtom))
  await markOpened($, DASHBOARD)
  await $.ui.open({ id: DASHBOARD, title: 'neuroflow', focus: true, rows: paneRows('dashboard', measuredRows()), columns: paneColumns('dashboard') })
}

const openPicker = async ($: EngineInterface): Promise<void> => {
  await update($, pickerNoteAtom, () => null)
  await markOpened($, PICKER)
  await $.ui.open({ id: PICKER, title: 'Switch phase', focus: true, closeOnEscape: true, rows: paneRows('picker', measuredRows()), columns: paneColumns('picker') })
}

/**
 * From the dashboard to another view (g, b): the engine gives the keys to a pane only from the prompt, never from a
 * pane that holds them, so the dashboard closes first and the next view opens holding the keys.
 */
const handOver = async ($: EngineInterface, open: () => Promise<void>): Promise<void> => {
  await $.ui.close({ id: DASHBOARD })
  await open()
}

const isPersonThere = async ($: EngineInterface): Promise<boolean> => (await $.session.surfaces()).length > 0

/**
 * Opens the board pane holding the keys, on the level commands/tasks.md names: the project's when it has open
 * tasks, else the first level with open tasks of this project, else the first with any open tasks.
 */
const openBoard = async ($: EngineInterface): Promise<void> => {
  await loadTasks($, true)
  const view = await read($, taskViewAtom)
  await update($, boardPickAtom, () => null)
  await update($, boardLevelAtom, () => (view === null ? null : openingLevel(view)))
  await markOpened($, BOARD)
  await $.ui.open({ id: BOARD, title: 'tasks', focus: true, rows: paneRows('board', measuredRows()), columns: paneColumns('board') })
}

/** The level the board shows. */
const shownLevel = async ($: EngineInterface): Promise<NfTaskLevel | undefined> => {
  const view = await read($, taskViewAtom)
  const shown = await read($, boardLevelAtom)
  return view?.levels.find(item => item.id === shown) ?? view?.levels[0]
}

/** A level's digit: that level's board, the ring on its first card. */
const showLevel = async ($: EngineInterface, id: string): Promise<void> => {
  await update($, boardPickAtom, () => null)
  await update($, boardLevelAtom, () => id)
  const level = await shownLevel($)
  const first = level === undefined ? null : (cardKeys(level).find(column => column.length > 0)?.[0] ?? null)
  if (first !== null) await ringTo($, BOARD, first)
}

/** Enter on a card picks it to move (again: puts it back); the ring goes to the next column's target. */
const pickCard = async ($: EngineInterface, slug: string): Promise<void> => {
  const level = await shownLevel($)
  if (level === undefined || level.kind === 'remote') return
  if ((await read($, boardPickAtom)) === slug) {
    await update($, boardPickAtom, () => null)
    return
  }
  await update($, boardPickAtom, () => slug)
  const to = firstTarget(level.board, cardColumn(level.board, slug))
  if (to !== null) await ringTo($, BOARD, `nf-move-${to}`)
}

/** x while a card is picked: nothing moves, the ring goes back to the card. */
const cancelPick = async ($: EngineInterface): Promise<void> => {
  const pick = await read($, boardPickAtom)
  await update($, boardPickAtom, () => null)
  if (pick !== null) await ringTo($, BOARD, `nf-card-${pick}`)
}

/**
 * h, j, k and l on the board: card to card, j past a column's fifth card turning its page; once a card is picked,
 * target to target (boardRingTarget).
 */
const boardStep = async ($: EngineInterface, direction: Direction): Promise<void> => {
  const level = await shownLevel($)
  if (level === undefined) return
  const at = (await read($, paneRingAtom))[BOARD] ?? null
  const to = boardRingTarget(level, await read($, boardPickAtom), at, direction)
  if (to !== null) await ringTo($, BOARD, to)
}

/**
 * The question before a move runs at project or flowie level, where /tasks moves the file at once (and at flowie
 * level commits and syncs it): `Move "Rerun ICA" to review? /neuroflow:tasks --move rerun-ica review runs now.`
 */
export const moveQuestion = (level: Pick<NfTaskLevel, 'kind' | 'name'>, slug: string, title: string, target: string): string =>
  `Move "${title}" to ${target}? ${moveCommand(level, slug, target)} runs now${level.kind === 'flowie' ? ' and syncs your flowie' : ''}.`

/**
 * Enter on a move target. At project and flowie level the move runs after the person's yes (runKey, with the safe
 * answer first: the board holds the keys while the person may type); at a hive's it only goes into the prompt: the
 * push to the team's repository is the person's to send (rule 16). A move not made leaves the card picked.
 */
const runMove = async ($: EngineInterface, level: NfTaskLevel, slug: string, target: string): Promise<void> => {
  if (level.kind === 'hive') {
    await update($, boardPickAtom, () => null)
    const text = moveCommand(level, slug, target)
    const filled = await $.prompt.fill({ text }).then(
      result => result.isFilled,
      () => false,
    )
    $.ui.toast(
      filled
        ? 'neuroflow: the move is in the prompt — Esc, then Enter sends it; /tasks shows what goes to the hive and pushes only after your yes'
        : `neuroflow: a hive move is yours to send — type ${text}`,
    )
    return
  }
  const title = level.board.columns.flatMap(column => column.cards).find(card => card.slug === slug)?.title ?? slug
  const args = `${levelArgs(level).trim()} --move ${slug} ${target}`.trim()
  if (await runKey($, 'neuroflow:tasks', args, { question: moveQuestion(level, slug, title, target), yes: 'Move it', header: 'Tasks' })) {
    await update($, boardPickAtom, () => null)
  }
}

const hideBandToday = async ($: EngineInterface): Promise<void> => {
  await $.store.set(BAND_HIDDEN_ON, isoDate(await $.clock.now()))
  await update($, bandHiddenAtom, () => true)
}

/** What a pane asks before a key's command runs (confirm): the question, its yes and the dialog's chip. */
type Ask = { question: string; yes: string; header: string }

/**
 * A key's neuroflow command (the band's, the dashboard's, a board move): run — or, while a flowie sync of the mod's
 * waits, put in the prompt for the person to send, so the sync runs before it (keyFillsPrompt). The band or pane
 * keeps the keys after the press, so Esc comes first. A prompt box that does not take the text runs the command as
 * before. From a pane, which holds the keys while the person may type, the command runs only after `ask` is answered
 * yes; the band, which holds them only after ^X Tab, runs it at once. True when it ran or went into the prompt.
 */
const runKey = async ($: EngineInterface, command: string, args: string, ask?: Ask): Promise<boolean> => {
  if (keyFillsPrompt(await read($, flowieSyncAtom))) {
    const text = `/${command}${args === '' ? '' : ` ${args}`}`
    const filled = await $.prompt.fill({ text }).then(
      result => result.isFilled,
      () => false,
    )
    if (filled) {
      $.ui.toast(`neuroflow: ${text} is in the prompt — Esc, then Enter runs it; your flowie sync goes first`)
      return true
    }
  }
  if (ask !== undefined && !(await confirm($, ask.question, 'Not now', ask.yes, ask.header))) return false
  await $.command.run({ command, args })
  return true
}

/** The pane's ask before a command runs: `Run /… now? It starts a model turn.` */
const runAsk = (command: string, args: string): Ask => ({ question: runQuestion(command, args), yes: 'Run it', header: 'neuroflow' })

/** Stops the loop being driven (the band's x, the now tab's stop): the current iteration finishes, none starts. */
const stopDriving = async ($: EngineInterface): Promise<void> => {
  const drive = await read($, driveAtom)
  if (drive === null) return
  await update($, driveAtom, () => null)
  const root = (await read($, scopeAtom))?.root
  const now = await $.clock.now()
  if (root) await appendLine(ioOf($), sessionLogPath(root, now), sessionLine(now, `autoresearch/${drive.name}`, `driver stopped after ${drive.turns} turn(s): stopped by the person`))
  $.ui.toast(`neuroflow: stopped driving "${drive.name}" — the current iteration finishes, no new one starts`)
}

/** Ends a live note capture as typing `done` does (the band's x, the now tab's stop). */
const endCapture = async ($: EngineInterface): Promise<void> => {
  await $.prompt.submit({ text: 'done' })
}

/**
 * A key whose command the person sends themselves (the workbench's apply, which may ask about a hive push): the band's
 * and the now tab's. The band or pane keeps the keys after the press, so Esc comes before the Enter that sends it.
 */
const fillKey = async ($: EngineInterface, command: string, args: string): Promise<void> => {
  const text = `/${command}${args === '' ? '' : ` ${args}`}`
  const filled = await $.prompt.fill({ text }).then(result => result.isFilled, () => false)
  $.ui.toast(filled ? `neuroflow: ${text} is in the prompt — Esc, then Enter sends it` : `neuroflow: run ${text} to apply your workbench changes`)
}

/** The check this session runs (one at a time): a second caller waits for the first. */
let wellbeingChecking: Promise<void> | null = null

/**
 * Before the band asks for today's wellbeing entry (#253): is it already on the flowie remote, made on another
 * machine? Only when the person collects wellbeing and today's entry is missing here. The band does not ask while
 * the check runs; `present` keeps it from asking (the next pull brings the entry down); `absent` or `unknown`
 * (offline, no upstream) lets it ask as before. A fetch only reads: nothing leaves.
 */
const checkWellbeingRemote = ($: EngineInterface, band: NfOptions['band']): Promise<void> => {
  if (wellbeingChecking !== null) return wellbeingChecking
  const run = (async () => {
    // Only where the band could ask: an active project, a person at a surface, the band on, not hidden today.
    const scope = await read($, scopeAtom)
    if (!scope?.isActive || scope.isHeadless || band === 'off') return
    if ((await read($, bandHiddenAtom)) || (await $.store.get(BAND_HIDDEN_ON)) === isoDate(await $.clock.now())) return
    const io = ioOf($)
    const home = toSlash((await io.home()) ?? '')
    if (home === '') return
    const today = isoDate(await io.now())
    const done = await read($, wellbeingCheckAtom)
    if (done !== null && done.date === today && done.state !== 'pending') return
    const wellbeing = `${home}/.neuroflow/flowie/wellbeing`
    const config = await io.read(`${wellbeing}/config.json`)
    if (config === null || !/"collect"\s*:\s*true/.test(config) || (await io.exists(`${wellbeing}/${today}.json`))) return
    await update($, wellbeingCheckAtom, () => ({ date: today, state: 'pending' as const }))
    const state = await checkRemoteEntry(io, home, `wellbeing/${today}.json`).catch(() => 'unknown' as const)
    await update($, wellbeingCheckAtom, () => ({ date: today, state }))
    if (state === 'present') await update($, snapshotAtom, snap => (snap === null ? snap : { ...snap, wellbeingDue: false }))
  })()
  wellbeingChecking = run.finally(() => {
    wellbeingChecking = null
  })
  return wellbeingChecking
}

/** Three whole numbers 1–10 and optional notes after them ("3 6 7 slept badly"), or null. */
export const parseWellbeing = (value: string): { anxiety: number; energy: number; happiness: number; notes: string } | null => {
  const match = /^\s*(\d{1,2})[\s,/]+(\d{1,2})[\s,/]+(\d{1,2})\s*(.*)$/s.exec(value)
  if (match === null) return null
  const [anxiety, energy, happiness] = [match[1], match[2], match[3]].map(Number)
  if (anxiety === undefined || energy === undefined || happiness === undefined) return null
  if (![anxiety, energy, happiness].every(score => Number.isInteger(score) && score >= 1 && score <= 10)) return null
  return { anxiety, energy, happiness, notes: (match[4] ?? '').trim() }
}

/**
 * Writes today's self-reported entry exactly as /flowie --assess does, queues its sync to the private flowie
 * repository (the mod's own cache) and returns. Scores go only into the file: never into state, toasts or context.
 *
 * It runs git nowhere. This is the band Input's closure; when an earlier version ran the sync here, the entry was
 * written once but no git ran and no log line came, which left the flowie dirty (and a dirty flowie makes
 * /neuroflow:migrate leave it out). Why is a hypothesis, not a fact the engine types state: a synchronous throw
 * of $.process.run, or the closure's later $ calls stopping or failing after the band redrew without the field
 * (the host keeps the Input's handle "for the lifetime of the drawing"). So the sync is queued in $.store before
 * the entry is written and runs from a hook dispatch: before the next neuroflow command's turn, or at a turn's
 * end (capture.ts, lib/flowiesync.ts). A closure that stops anywhere after the queueing loses nothing; one that
 * goes on queues again once both files are written, in case a sync ran in between.
 */
const saveWellbeing = async ($: EngineInterface, value: string): Promise<void> => {
  const entry = parseWellbeing(value)
  if (entry === null) {
    $.ui.toast('neuroflow: three whole numbers from 1 to 10, e.g. 3 6 7 (notes may follow)')
    return
  }
  let step: 'read' | 'queue' | 'write' | 'show' = 'read'
  try {
    const io = ioOf($)
    const home = toSlash((await io.home()) ?? '')
    const flowie = `${home}/.neuroflow/flowie`
    if (home === '' || !(await io.exists(`${flowie}/.git`))) return
    const now = await io.now()
    const today = isoDate(now)
    const sync = { paths: [`wellbeing/${today}.json`, 'wellbeing/.flow'], message: `wellbeing: ${today}`, at: now }
    step = 'queue'
    await $.store.set(SYNC_QUEUE, enqueue(asQueue(await $.store.get(SYNC_QUEUE)), sync))
    step = 'write'
    await io.write(`${flowie}/wellbeing/${today}.json`, `${JSON.stringify({ date: today, ...entry }, null, 2)}\n`)
    await appendLine(io, `${flowie}/wellbeing/.flow`, `| ${today}.json | wellbeing entry |`)
    $.ui.toast(`neuroflow: wellbeing logged for ${today} — it syncs to your flowie before your next neuroflow command or when a turn ends`)
    // The band may redraw without the field from here on; the sync queued above already covers the entry.
    step = 'show'
    const queue = enqueue(asQueue(await $.store.get(SYNC_QUEUE)), { ...sync, at: await io.now() })
    await $.store.set(SYNC_QUEUE, queue)
    await update($, flowieSyncAtom, () => syncState(queue, null))
    await update($, snapshotAtom, snap => (snap === null ? snap : { ...snap, wellbeingDue: false }))
  } catch (error) {
    const why = (error instanceof Error ? error.message : String(error)).slice(0, 120)
    if (step !== 'show') $.ui.toast(`neuroflow: wellbeing not saved — ${step === 'write' ? 'the entry could not be written' : step === 'queue' ? 'its sync could not be queued' : 'the flowie folder could not be read'} (${why}); /neuroflow:flowie --assess records it`)
  }
}

/** Keep (a person's press) writes the drafted decision to the reasoning log; drop discards it. Both are counted. */
const settleDraft = async ($: EngineInterface, keep: boolean): Promise<void> => {
  const draft = await read($, draftAtom)
  if (draft === null) return
  if (keep) {
    const entry = JSON.stringify({
      statement: draft.statement,
      source: `command:${draft.command} | ${isoDate(draft.at)}`,
      reasoning: draft.reasoning,
      at: new Date(draft.at).toISOString(),
      drafted_by: 'mod',
      approved_by: 'person',
    })
    await appendLine(ioOf($), draft.path, entry)
    await $.store.set('drafter.kept', (Number(await $.store.get('drafter.kept')) || 0) + 1)
    $.ui.toast('neuroflow: decision kept in the reasoning log')
  } else {
    await $.store.set('drafter.dropped', (Number(await $.store.get('drafter.dropped')) || 0) + 1)
  }
  await update($, draftAtom, () => null)
}

/**
 * Enter on a now-tab row: the band's own act for it, after the person's yes in the engine's question dialog, the safe
 * answer first — the pane holds the keys while the person may be typing for the prompt (confirm). Only the workbench's
 * apply goes ahead without a question: it puts its command in the prompt, for the person to send.
 */
const runNow = async ($: EngineInterface, now: NowAct): Promise<void> => {
  if (now.kind === 'fill') {
    await fillKey($, now.command, now.args)
    return
  }
  if (now.kind === 'command') {
    await runKey($, now.command, now.args, runAsk(now.command, now.args))
    return
  }
  if (now.kind === 'keep' || now.kind === 'drop') {
    const draft = await read($, draftAtom)
    if (draft === null) return
    const keep = now.kind === 'keep'
    const yes = keep
      ? await confirm($, `Keep "${draft.statement}" in the reasoning log, as a decision you approved?`, 'Not now', 'Keep it', 'Decision')
      : await confirm($, `Drop the drafted decision "${draft.statement}"? It is not written anywhere.`, 'Keep it waiting', 'Drop it', 'Decision')
    if (yes) await settleDraft($, keep)
    return
  }
  if (now.kind === 'stop-drive') {
    const drive = await read($, driveAtom)
    if (drive !== null && (await confirm($, `Stop driving "${drive.name}"? The current iteration finishes; no new one starts.`, 'Keep driving', 'Stop it', 'Autoresearch'))) {
      await stopDriving($)
    }
    return
  }
  if (await confirm($, 'End the note capture? Your next messages go to the model again.', 'Keep capturing', 'End it', 'Notes')) await endCapture($)
}

/**
 * The phase picker's options, in picker order: each phase's id and label first (a typed letter finds the phase by its
 * name), then its glyph from the one legend and its state in words — current, next, recommended, visited, not
 * started — in one column, as the typeahead marks it (phaseStateMark); `short` for the mobile buttons.
 */
export const pickerOptions = (
  current: string | null,
  visited: readonly string[],
  recommended: readonly string[],
): { value: string; label: string; short: string }[] => {
  const rows = pickerOrder(current, recommended).map(phase => ({
    value: phase.id,
    text: `${phase.id} — ${phase.label}`,
    mark: phaseStateMark(phase.id, current, visited, recommended),
  }))
  const width = Math.max(0, ...rows.map(row => cells(row.text)))
  return rows.map(row => ({ value: row.value, label: `${pad(row.text, width)}  ${row.mark}`, short: `${row.value} · ${row.mark}` }))
}

/** M065 — the mark a phase command gets in the slash menu: the current phase and the recommended next one. */
export const phaseMark = (command: string, current: string | null, next: string | null): string | null =>
  command === current ? `${PHASE_GLYPH.current} current phase ·` : command === next ? `${PHASE_GLYPH.recommended} next ·` : null

/** The files a freeze covers (commands/preregistration.md → Freeze): the prereg documents, not the review reports. */
export const freezeCandidates = (names: readonly string[]): string[] =>
  names.filter(name => /^(prereg-.+|registered-report)\.md$/i.test(name)).sort()

const FREEZE_SCRIPT = 'skills/phase-preregistration/scripts/freeze.py'

/** Logs a freeze or unfreeze the person did in the dashboard: a session line and a reasoning entry. */
const logIntegrityAction = async ($: EngineInterface, root: string, statement: string, reasoning: string): Promise<void> => {
  const io = ioOf($)
  const now = await io.now()
  await appendLine(io, sessionLogPath(root, now), sessionLine(now, 'preregistration', `${statement} (dashboard)`))
  const entry = JSON.stringify({ statement, source: `mod:dashboard | ${isoDate(now)}`, reasoning, at: new Date(now).toISOString(), drafted_by: 'mod', approved_by: 'person' })
  await appendLine(io, join(root, '.neuroflow/reasoning/preregistration.jsonl'), entry)
}

/**
 * M018 — freezing is a person's action: a key press here, then an explicit confirmation, runs the same
 * freeze.py the prose runs, with `--set-by person`. The model cannot press keys, so this marker is honest.
 */
const freezeFromDashboard = async ($: EngineInterface): Promise<void> => {
  const scope = await read($, scopeAtom)
  if (scope === null || scope.root === null) return
  const root = scope.root
  const io = ioOf($)
  const names = (await io.list(join(root, '.neuroflow/preregistration'))).filter(entry => !entry.isDir).map(entry => entry.name)
  const files = freezeCandidates(names)
  if (files.length === 0) {
    $.ui.toast('neuroflow: no prereg-*.md document in .neuroflow/preregistration/ to freeze — /neuroflow:preregistration writes it')
    return
  }
  // The safe answer comes first and only the exact label acts: a dialog that resolves on its own
  // (the person away from the keyboard) must never freeze anything.
  const confirm = 'Freeze — I froze it myself'
  const answer = await $.ui
    .ask(`Freeze ${files.join(', ')}? The files are hashed and get a FROZEN banner; later changes go to deviations.md.`, {
      options: ['Not now', confirm],
      header: 'Freeze',
    })
    .catch(() => '')
  if (answer !== confirm) return
  const run = await runScript(io, FREEZE_SCRIPT, ['freeze', ...files.map(name => `.neuroflow/preregistration/${name}`), '--set-by', 'person', '--root', root, '--json'], { cwd: root })
  if (!run.ok) {
    $.ui.toast(`neuroflow: the freeze did not run — ${(run.stderr.trim().split('\n').pop() ?? '') || 'no output'}`)
    return
  }
  await logIntegrityAction($, root, `Preregistration frozen: ${files.join(', ')}`, 'Frozen by the person with a key press and a confirmation in the dashboard.')
  await reload($, root)
  $.ui.toast(`neuroflow: preregistration frozen (${files.length} file${files.length === 1 ? '' : 's'})`)
}

/** Unfreezing is a person's action too, with a reason that goes into deviations.md (freeze.py logs it). */
const unfreezeFromDashboard = async ($: EngineInterface): Promise<void> => {
  const scope = await read($, scopeAtom)
  if (scope === null || scope.root === null) return
  const root = scope.root
  const keep = 'Keep it frozen'
  const reason = await $.ui
    .ask('Unfreeze the preregistration? It goes back to draft, and the unfreeze is logged in deviations.md with the old hashes. Why? (pick or type a reason)', {
      options: [keep, 'Fix an error before the registry submission', 'The registry asked for changes'],
      header: 'Unfreeze',
    })
    .catch(() => keep)
  if (reason.trim() === '' || reason === keep) return
  const run = await runScript(ioOf($), FREEZE_SCRIPT, ['unfreeze', '--set-by', 'person', '--reason', reason, '--root', root, '--json'], { cwd: root })
  if (!run.ok) {
    $.ui.toast(`neuroflow: the unfreeze did not run — ${(run.stderr.trim().split('\n').pop() ?? '') || 'no output'}`)
    return
  }
  await logIntegrityAction($, root, 'Preregistration unfrozen', `Unfrozen by the person in the dashboard: ${reason}`)
  await reload($, root)
  $.ui.toast('neuroflow: preregistration back to draft — freeze it again when it is final')
}

/** Re-hashes the frozen files now (freeze.py verify) and says what it found. */
const verifyFromDashboard = async ($: EngineInterface): Promise<void> => {
  const scope = await read($, scopeAtom)
  if (scope === null || scope.root === null) return
  const run = await runScript(ioOf($), FREEZE_SCRIPT, ['verify', '--root', scope.root, '--json'], { cwd: scope.root })
  const report = parseJson<{ findings?: { kind: string; path: string }[] }>(run.stdout)
  if (report === null) {
    $.ui.toast(`neuroflow: verify did not run — ${run.stderr.trim() || 'no output'}`)
    return
  }
  const findings = report.findings ?? []
  $.ui.toast(findings.length === 0 ? 'neuroflow: every frozen file matches its hash' : `neuroflow: ${findings.map(item => `${item.kind} ${item.path}`).join('; ')} — /neuroflow:preregistration`)
}

const TONE_COLOR: Record<Tone, 'error' | 'warning' | 'success' | 'suggestion' | 'subtle'> = {
  error: 'error',
  warning: 'warning',
  success: 'success',
  suggestion: 'suggestion',
  subtle: 'subtle',
}

export const registerViews = (on: On, opts: NfOptions): void => {
  // Typeahead for the typed paths into the views (lib/complete.ts): code only, from the state the mod holds — no
  // file is read while the person types (charter rule 20). The engine's own rows stay first.
  on('prompt.autocomplete', async ($, e, next) => {
    const result = await next(e)
    const scope = await read($, scopeAtom)
    if (!scope?.isActive) return result
    const snap = await read($, snapshotAtom)
    const rows = completions(e, { phase: snap?.phase ?? null, visited: snap?.phasesVisited ?? [], recommended: snap?.recommendedPhases ?? [], tasks: await read($, taskViewAtom) })
    return rows.length === 0 ? result : { suggestions: [...result.suggestions, ...rows] }
  }).catch(($, e, next) => next(e))

  // M065: the current phase's command and the recommended next one are marked in the slash menu.
  on('command.describe', { command: /^neuroflow:/ }, async ($, e, next) => {
    const result = await next(e)
    const scope = await read($, scopeAtom)
    const snap = await read($, snapshotAtom)
    if (!scope?.isActive || snap === null || result.isHidden) return result
    const mark = phaseMark(e.command.slice('neuroflow:'.length), snap.phase, nextPhase(snap.phase, snap.recommendedPhases))
    return mark === null ? result : { ...result, description: `${mark} ${result.description}` }
  }).catch(($, e, next) => next(e))

  // /neuroflow:phase — bare: the picker; a phase name: switch at once; anything else: the prose flow.
  on('command.run', { command: 'neuroflow:phase' }, async ($, e, next) => {
    const scope = await read($, scopeAtom)
    if (!scope?.isActive) return next(e)
    const arg = e.args.trim()
    if (arg !== '' && isPhase(arg)) return { text: await switchPhase($, arg, 'phase command') }
    if (arg !== '' || !(await isPersonThere($))) return next(e)
    await openPicker($)
    return { text: 'Phase picker open — ↓ or Enter opens the list, ↑↓ move, Enter switches after a yes, Esc closes. (Any argument runs the full /phase flow.)' }
  }).catch(($, e, next) => next(e))

  on('command.run', { command: 'neuroflow:dashboard' }, async ($, e, next) => {
    const scope = await read($, scopeAtom)
    // --web (the claude.ai workbench) asks, previews and uploads: the prose runs it (commands/dashboard.md → --web).
    if (!scope?.isActive || /(^|\s)--web(\s|$)/.test(e.args) || !(await isPersonThere($))) return next(e)
    await openDashboard($, e.args.trim())
    return { text: 'Dashboard open — 1–6 tabs, h/l previous/next, r reread, q close, Esc back to the prompt.' }
  }).catch(($, e, next) => next(e))

  // /neuroflow:tasks — bare: the task boards of every level as a pane (M070, M163); anything else: the prose flow.
  on('command.run', { command: 'neuroflow:tasks' }, async ($, e, next) => {
    const scope = await read($, scopeAtom)
    if (!scope?.isActive || e.args.trim() !== '' || !(await isPersonThere($))) return next(e)
    await openBoard($)
    return { text: 'Task boards open — digits pick the level, h/j/k/l or Tab reach a card, Enter picks it and Enter on a column moves it (after a yes), q closes. (Any argument runs the full /tasks flow.)' }
  }).catch(($, e, next) => next(e))

  on('ui.render', { component: 'Pane', requestId: BOARD }, async ($, e) => {
    rememberViewport(e.viewport)
    const { Box, Button, Text } = $.ui.resolve(e)
    const view = await read($, taskViewAtom)
    if (view === null) return <Text dimColor>Reading the task boards…</Text>
    const shownId = await read($, boardLevelAtom)
    const level = view.levels.find(item => item.id === shownId) ?? view.levels[0]
    if (level === undefined) return <Text dimColor>No task board here yet — /neuroflow:tasks --add "title" starts one.</Text>
    const board = level.board
    const width = e.props.bodyColumns
    const size = widthClass(width)
    const term = e.surface === 'terminal'
    const compact = isCompact(e.viewport?.rows ?? measuredRows())
    const space = compact ? 0 : 1
    const isRemote = level.kind === 'remote'
    const pick = isRemote ? null : await read($, boardPickAtom)
    const picked = pick === null ? null : (board.columns.flatMap(column => column.cards).find(card => card.slug === pick) ?? null)
    const grid = cardKeys(level)
    const first = grid.find(column => column.length > 0)?.[0] ?? null
    // Each column shows the five cards around the ring (or the picked card); the others their first five.
    const ring = (await read($, paneRingAtom))[BOARD] ?? null
    const near = ring !== null && ring.startsWith('nf-card-') ? ring.slice('nf-card-'.length) : pick
    const pageFor = (cards: readonly NfCard[]) => pageOf(cards, near === null ? -1 : cards.findIndex(card => card.slug === near))
    const run = (fn: () => unknown) => act($, BOARD, fn)
    // A card and a move target are pressed by Enter: not right after another key (actOn), and a move asks first.
    const runOn = (fn: () => unknown) => actOn($, BOARD, fn)
    const keysHere = e.surface !== 'terminal' || e.props.isFocused
    const canStep = first !== null
    const layout = boardLayout(width, board.columns.length)
    /** A card as the board draws it: ▸ when picked, this project's ◆, ⚠ overdue, ↻ a web change; cut with `…`. */
    const card = (item: NfCard, room: number): JSX.Element =>
      isRemote ? (
        <Text wrap="truncate-end">{fit(`  ${levelCardLine(item, level.kind)}`, room)}</Text>
      ) : (
        <Button
          key={`nf-card-${item.slug}`}
          label={fit(`${item.slug === pick ? '▸' : ' '} ${levelCardLine(item, level.kind)}`, room)}
          plain
          {...(picked === null && `nf-card-${item.slug}` === first ? { autoFocus: true as const } : {})}
          onPress={runOn(() => pickCard($, item.slug))}
        />
      )
    const note = (page: ReturnType<typeof pageFor>): JSX.Element | null => {
      const text = pageNote(page)
      return text === null ? null : <Text dimColor>{`  ${text}`}</Text>
    }
    const columns =
      layout.kind === 'grid' ? (
        <Box flexDirection="row" columnGap={BOARD_GAP}>
          {board.columns.map(column => {
            const page = pageFor(column.cards)
            const inner = layout.columnWidth - 4
            return (
              <Box key={`nf-col-${column.id}`} flexDirection="column" width={layout.columnWidth} borderStyle="round" borderDimColor paddingX={1}>
                <Box flexDirection="row" justifyContent="space-between" columnGap={1}>
                  <Box flexShrink={1}>
                    <Text dimColor wrap="truncate-end">
                      {column.label.toUpperCase()}
                    </Text>
                  </Box>
                  <Box flexShrink={0}>
                    <Text dimColor>{String(column.total)}</Text>
                  </Box>
                </Box>
                {page.shown.map(item => card(item, inner))}
                {note(page)}
              </Box>
            )
          })}
        </Box>
      ) : (
        // A narrow dock: the columns one under the other, each with its count.
        <Box flexDirection="column">
          {board.columns.map((column, at) => {
            const page = pageFor(column.cards)
            return (
              <Box key={`nf-col-${column.id}`} flexDirection="column" marginTop={at === 0 ? 0 : space}>
                <Text dimColor wrap="truncate-end">{`${column.label.toUpperCase()} · ${column.total}`}</Text>
                {page.shown.map(item => card(item, width))}
                {note(page)}
              </Box>
            )
          })}
        </Box>
      )
    const levelName = (item: NfTaskLevel): string =>
      `${item.name} ${item.open}${(item.kind === 'flowie' || item.kind === 'hive') && item.mine > 0 && item.project !== null ? ` (${MINE} ${item.mine})` : ''}${item.kind === 'remote' ? ' (read-only)' : ''}`
    const now = await $.clock.now()
    return (
      <Box flexDirection="column">
        <Box flexDirection="row" columnGap={3}>
          <Box flexShrink={0}>
            <Text>{`${MARK} tasks`}</Text>
          </Box>
          <Box flexDirection="row" flexWrap="wrap" columnGap={3} flexShrink={1}>
            {view.levels.map((item, at) => {
              const digit = DIGITS[at]
              const name = levelName(item)
              if (item.id === level.id) return <Text>{digit === undefined ? name : `${digit}: ${name}`}</Text>
              return <Button key={`nf-level-${item.id}`} label={name} {...(digit === undefined ? {} : { hotkey: digit })} plain dimColor onPress={run(() => showLevel($, item.id))} />
            })}
          </Box>
        </Box>
        <Box flexDirection="column" marginTop={space}>
          {columns}
        </Box>
        {isRemote ? (
          <Text dimColor wrap="wrap">{`Read-only: a copy of ${level.name}'s board${level.fetched ? `, fetched ${level.fetched}` : ''}. Move its tasks in that repository.`}</Text>
        ) : null}
        {picked !== null ? (
          <Box flexDirection="row" flexWrap="wrap" columnGap={2} marginTop={space}>
            <Text>{`move "${fit(picked.title, size === 'narrow' ? 18 : 32)}" →`}</Text>
            {moveTargets(board, cardColumn(board, picked.slug)).map(target => (
              <Button key={`nf-move-${target}`} label={target} plain onPress={runOn(() => runMove($, level, picked.slug, target))} />
            ))}
            <Button key="nf-board-cancel" label="cancel" hotkey={NAV.cancel} plain dimColor onPress={run(() => cancelPick($))} />
          </Box>
        ) : null}
        <Box flexDirection="column" marginTop={space}>
          <Text dimColor wrap="wrap">{boardFoot(level)}</Text>
          {view.web ? (
            <Text color="warning" wrap="wrap">{`↻ ${pendingText(view.web, now)}`}</Text>
          ) : null}
        </Box>
        {term && !compact ? (
          <Text dimColor wrap="truncate-end">
            {rule(width)}
          </Text>
        ) : null}
        <Box flexDirection="column" marginTop={term ? 0 : 1}>
          {keysHere ? (
            <Box flexDirection={size === 'narrow' ? 'column' : 'row'} justifyContent="space-between" columnGap={2}>
              <Box flexDirection="row" flexWrap="wrap" columnGap={2} flexShrink={1}>
                {canStep
                  ? [
                      <Button key="nf-nav-left" label="◂" hotkey={NAV.left} plain dimColor onPress={run(() => boardStep($, 'left'))} />,
                      <Button key="nf-nav-right" label="▸" hotkey={NAV.right} plain dimColor onPress={run(() => boardStep($, 'right'))} />,
                      <Button key="nf-nav-down" label="▾" hotkey={NAV.down} plain dimColor onPress={run(() => boardStep($, 'down'))} />,
                      <Button key="nf-nav-up" label="▴" hotkey={NAV.up} plain dimColor onPress={run(() => boardStep($, 'up'))} />,
                    ]
                  : null}
                <Button key="nf-board-refresh" label="reread" hotkey={NAV.reread} plain dimColor onPress={run(() => loadTasks($, true))} />
                <Button key="nf-board-close" label="close" hotkey={NAV.close} plain dimColor role="dismiss" onPress={run(() => $.ui.close({ id: BOARD }))} />
              </Box>
              {term ? (
                <Box flexShrink={0}>
                  <Text dimColor>{!canStep ? 'esc: prompt' : picked !== null ? 'enter: move there · esc: prompt' : 'enter: pick · esc: prompt'}</Text>
                </Box>
              ) : null}
            </Box>
          ) : (
            <Text dimColor wrap="truncate-end">
              {unfocusedHint('/neuroflow:tasks')}
            </Text>
          )}
        </Box>
      </Box>
    )
  }).catch(($, e, next) => next(e))

  // The boards and the tasks tab follow the files: once read this session, they are read again as each turn
  // ends (a /tasks --move the board ran has run by then). Only the local files are read, never pulled.
  on('turn.complete', { reason: ['answer', 'aborted', 'error', 'refusal'] }, async ($, e, next) => {
    const result = await next(e)
    if (e.agentId === undefined && (await read($, taskViewAtom)) !== null) await loadTasks($).catch(() => undefined)
    // The wellbeing remote check, if the one the session's start began did not finish (#253).
    if (e.agentId === undefined && (await read($, wellbeingCheckAtom))?.state === 'pending') void checkWellbeingRemote($, opts.band).catch(() => undefined)
    return result
  }).catch(($, e, next) => next(e))

  // As an interactive session starts: whether today's wellbeing entry is already on the flowie remote (#253). Not
  // awaited, so the first prompt never waits for the network; the band does not ask until it knows. And how often
  // the band has taken the keys so far ($.store holds it across sessions; the state mirrors it for drawing).
  on('session.start', { isInteractive: true }, async ($, e, next) => {
    const result = await next(e)
    void checkWellbeingRemote($, opts.band).catch(() => undefined)
    const learned = Number(await $.store.get(KEYS_LEARNED).catch(() => 0)) || 0
    await update($, keysLearnedAtom, () => learned)
    return result
  }).catch(($, e, next) => next(e))

  // Where the focus ring is in the dashboard and the boards, so j, k, h and l move it on from there: every move is
  // recorded, onto a row or anywhere else (a tab key, the legend), and one onto an engine stop forgets it, so the
  // record never points at a row the ring has left. The panes and the nf- keys are the mod's own, whatever name the
  // engine gives the plugin's copy.
  on('ui.focus', { requestId: [DASHBOARD, BOARD] }, async ($, e, next) => {
    const result = await next(e)
    if (result.deny !== undefined) return result
    const element = e.element
    if (element === undefined) await forgetRing($, e.requestId)
    else await update($, paneRingAtom, ring => ({ ...ring, [e.requestId]: element }))
    return result
  }).catch(($, e, next) => next(e))

  // The band takes the keys (^X Tab, or a click) with its ring on the element it starts on (an autoFocus, raised
  // under the plugin's origin): counted, so the band stops teaching the chord once it has been used LEARNED_AFTER times.
  on('ui.focus', { component: 'AbovePrompt' }, async ($, e, next) => {
    const result = await next(e)
    const element = e.element
    if (result.deny === undefined && e.origin.kind === 'plugin' && element !== undefined && BAND_TAKES.includes(element)) {
      const before = (await read($, keysLearnedAtom)) ?? (Number(await $.store.get(KEYS_LEARNED).catch(() => 0)) || 0)
      if (before < LEARNED_AFTER) {
        await $.store.set(KEYS_LEARNED, before + 1).catch(() => undefined)
        await update($, keysLearnedAtom, () => before + 1)
      }
    }
    return result
  }).catch(($, e, next) => next(e))

  // The band: one row of what needs attention; nothing when nothing does.
  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    rememberViewport(e.viewport)
    if (opts.band === 'off' || e.props.hasSurvey) return next(e)
    const scope = await read($, scopeAtom)
    if (!scope?.isActive || scope.isHeadless) return next(e)
    if ((await read($, activeCommandAtom))?.lifecycle === 'quiet' || isQuiet(await read($, quietAtom), await $.clock.now())) return next(e)
    const { Box, Button, Text } = $.ui.resolve(e)
    const columns = e.props.bodyColumns
    // The band's keys work once it holds the keyboard: the engine's chord says how, until it has been used.
    const hint = e.surface === 'terminal' && ((await read($, keysLearnedAtom)) ?? 0) < LEARNED_AFTER ? `${CHORD}: keys` : null
    /** A band key: drawn as `k: text` (a plain Button), measured by the same words before anything is drawn. */
    type Key = { element: string; hotkey: string; text: string; short?: string; onPress: () => unknown; autoFocus?: true }
    const key = (element: string, hotkey: string, text: string, onPress: () => unknown, short?: string): Key => ({ element, hotkey, text, onPress, ...(short === undefined ? {} : { short }) })
    const labels = (keys: readonly Key[], short = false): string[] => keys.map(item => `${item.hotkey}: ${short ? (item.short ?? item.text) : item.text}`)
    // The ring starts here when the band takes the keys: it writes and consents to nothing.
    const dashboard = (tab: NfDashboardTab): Key => ({ ...key('nf-band-dashboard', BAND.dashboard, 'dashboard', () => openDashboard($, tab)), autoFocus: true })
    /** The ring mark and the space after it, before the items. */
    const lead = cells(MARK) + 1
    const plan = (offered: number, total: number, keys: readonly Key[]) =>
      bandPlan({ columns, items: offered, total, buttons: labels(keys), short: keys.some(item => item.short !== undefined) ? labels(keys, true) : undefined, hint, lead })
    /**
     * One row as wide as the band (bandPlan), by priority: the mark; the first item, whole where it can be, cut at its
     * end; its keys; the chord hint while it is taught; a second item; and the keys and `+N more` in full words, which
     * give way to their short ones (`x: hide`, `+2`) first.
     */
    const row = (items: readonly { text: string; color: 'error' | 'warning' | 'suggestion' }[], total: number, keys: readonly Key[]): JSX.Element => {
      const fits = plan(items.length, total, keys)
      const shown = items.slice(0, fits.items)
      const widths = bandItemWidths(fits.room, shown.map(item => item.text))
      const more = moreLabel(fits.more, fits.short)
      return (
        <Box flexDirection="row" columnGap={2}>
          {/* The items keep the widths bandPlan gave them, and give way first should a surface measure a glyph wider. */}
          <Box flexDirection="row" columnGap={1} flexShrink={1}>
            <Text dimColor>{MARK}</Text>
            <Box flexDirection="row" columnGap={2} flexShrink={1}>
              {shown.map((item, at) => (
                <Box width={widths[at] ?? 0} flexShrink={1}>
                  <Text color={item.color} wrap="truncate-end">
                    {item.text}
                  </Text>
                </Box>
              ))}
            </Box>
          </Box>
          {more !== '' ? (
            <Box flexShrink={0}>
              <Text dimColor>{more}</Text>
            </Box>
          ) : null}
          <Box flexDirection="row" columnGap={2} flexShrink={0}>
            {keys.map(item => (
              <Button
                key={item.element}
                label={fits.short ? (item.short ?? item.text) : item.text}
                hotkey={item.hotkey}
                plain
                {...(item.autoFocus ? { autoFocus: true as const } : {})}
                onPress={item.onPress}
              />
            ))}
          </Box>
          {fits.hint ? (
            <Box flexShrink={0}>
              <Text dimColor>{hint}</Text>
            </Box>
          ) : null}
        </Box>
      )
    }
    // A drafted decision waits for a person's keep or drop (M009); it outranks everything else. Its keys are never
    // where the ring starts: the dashboard is.
    const draft = await read($, draftAtom)
    if (draft !== null) {
      return row([{ text: `✎ decision drafted for ${draft.phase}: ${draft.statement}`, color: 'suggestion' }], 1, [
        key('nf-draft-keep', BAND.keep, 'keep', () => settleDraft($, true)),
        key('nf-draft-drop', BAND.drop, 'drop', () => settleDraft($, false)),
        dashboard('now'),
      ])
    }
    // A driven autoresearch loop always shows, with its stop control (charter: no paid turns without one).
    const drive = await read($, driveAtom)
    if (drive !== null) {
      return row(
        [{ text: `↻ driving autoresearch "${drive.name}" · turn ${drive.turns}${drive.errors > 0 ? ` · ${drive.errors} error(s) in a row` : ''}`, color: 'suggestion' }],
        1,
        [key('nf-drive-stop', BAND.dismiss, 'stop', () => stopDriving($)), dashboard('loop')],
      )
    }
    // A live note capture shows while it runs: messages go to the notes, not to the model. x ends it as `done` does.
    const capture = await read($, captureAtom)
    if (capture !== null) {
      return row(
        [{ text: `✎ capturing notes → ${capture.target} · ${capture.count} entr${capture.count === 1 ? 'y' : 'ies'} · messages are not sent to the model`, color: 'warning' }],
        1,
        [key('nf-capture-done', BAND.dismiss, 'stop', () => endCapture($))],
      )
    }
    // Hidden for today: the press sets the state (redraw now) and the store (kept across sessions).
    const isHidden = (await read($, bandHiddenAtom)) || (await $.store.get(BAND_HIDDEN_ON)) === isoDate(await $.clock.now())
    if (isHidden) return next(e)
    const snap = await read($, snapshotAtom)
    if (snap === null) return next(e)
    const items = bandItems(snap, opts.band === 'quiet', await read($, flowieSyncAtom))
    // Self-reported wellbeing (M146, opt-in in flowie): one field, no scores kept anywhere but the file. The ring
    // starts in the field, so ^X Tab and the scores are all it takes.
    const idle = (await read($, activeCommandAtom)) === null
    const check = await read($, wellbeingCheckAtom)
    const today = isoDate(await $.clock.now())
    const askable = check === null || check.date !== today || check.state === 'absent' || check.state === 'unknown'
    if (snap.wellbeingDue && askable && idle && e.surface !== 'mobile' && items[0]?.level !== 'alert') {
      const { Input } = $.ui.resolve(e)
      const ask = columns >= 100 ? 'wellbeing today — anxiety, energy, happiness (1–10):' : 'wellbeing 1–10: anxiety energy happiness'
      return (
        <Box flexDirection="row" columnGap={2}>
          <Box flexDirection="row" columnGap={1} flexShrink={1}>
            <Text dimColor>{MARK}</Text>
            <Text color="suggestion" wrap="truncate-end">
              {ask}
            </Text>
          </Box>
          <Input key="nf-wellbeing" placeholder="e.g. 3 6 7" submitLabel="save" autoFocus onSubmit={(value: string) => saveWellbeing($, value)} />
          <Box flexShrink={0}>
            <Button key="nf-band-hide" label="not today" hotkey={BAND.dismiss} plain onPress={() => hideBandToday($)} />
          </Box>
          {hint !== null && columns >= 100 ? (
            <Box flexShrink={0}>
              <Text dimColor>{hint}</Text>
            </Box>
          ) : null}
        </Box>
      )
    }
    if (items.length === 0) return next(e)
    const offered = items.slice(0, opts.band === 'quiet' ? 1 : 2)
    const fixed = (shown: readonly BandItem[]): Key[] => [
      ...bandActions(shown).map(action => key(action.key, action.hotkey, action.label, () => (action.fill ? fillKey($, action.command, action.args) : runKey($, action.command, action.args)))),
      dashboard('now'),
      key('nf-band-hide', BAND.dismiss, 'hide today', () => hideBandToday($), 'hide'),
    ]
    // A second item stays only where it fits beside the keys it would bring; the first always shows.
    const shown = offered.slice(0, plan(offered.length, items.length, fixed(offered)).items)
    return row(
      shown.map(item => ({ text: `${item.glyph} ${item.text}`, color: item.level === 'alert' ? 'error' : item.level === 'warn' ? 'warning' : 'suggestion' })),
      items.length,
      fixed(shown),
    )
  }).catch(($, e, next) => next(e))

  on('ui.render', { component: 'Pane', requestId: DASHBOARD }, async ($, e) => {
    rememberViewport(e.viewport)
    const { Box, Button, Text } = $.ui.resolve(e)
    const snap = await read($, snapshotAtom)
    if (snap === null) {
      const scope = await read($, scopeAtom)
      return <Text dimColor>neuroflow: {scope === null ? 'not started yet' : scope.reason}</Text>
    }
    const tab = await read($, tabAtom)
    const width = e.props.bodyColumns
    const size = widthClass(width)
    // Rules, the flow line and the ruler line up cell by cell: the terminal draws them, where every glyph is a cell.
    const term = e.surface === 'terminal'
    // A short terminal (24 rows over SSH): no blank rows, no summary, the title on the mark's line.
    const compact = isCompact(e.viewport?.rows ?? measuredRows())
    const space = compact ? 0 : 1
    const keysHere = e.surface !== 'terminal' || e.props.isFocused
    const run = (fn: () => unknown) => act($, DASHBOARD, fn)
    // The now tab's rows, migrate, freeze and unfreeze are pressed by Enter: not right after another key (actOn),
    // and each asks first.
    const runOn = (fn: () => unknown) => actOn($, DASHBOARD, fn)
    const color = (tone: Tone | undefined) => (tone === undefined ? undefined : TONE_COLOR[tone])
    const frozenByPerson = snap.prereg?.status === 'frozen' && snap.prereg.setBy === 'person'
    // The prose dashboard's Update line (commands/dashboard.md): here too, also after the band was hidden for today.
    const behind = versionNotice(snap)
    const rows =
      tab === 'now' ? nowRows(snap, await read($, flowieSyncAtom), { draft: await read($, draftAtom), drive: await read($, driveAtom), capture: await read($, captureAtom) }) : []
    const ringKeys = tab === 'now' ? nowRingKeys(rows, behind !== null) : []
    /**
     * Rows under UPPERCASE dim labels, the labels in a column `labelWidth` cells wide; a label is cut a cell short of
     * it (labelCell), so a long one never runs into its value.
     */
    const labelled = (items: readonly LabelRow[], labelWidth: number): JSX.Element => (
      <Box flexDirection="column">
        {items.map(item => (
          <Box flexDirection="row">
            <Box width={labelWidth} flexShrink={0}>
              <Text dimColor wrap="truncate-end">
                {labelCell(item.label, labelWidth)}
              </Text>
            </Box>
            <Box flexShrink={1}>
              <Text color={color(item.tone)} dimColor={item.dim === true} wrap="wrap">
                {item.value}
              </Text>
            </Box>
          </Box>
        ))}
      </Box>
    )
    let body: JSX.Element
    if (tab === 'now') {
      // Every item the band can show, its glyph in its colour; an action runs on Enter, never on a letter.
      const attention =
        rows.length === 0 ? (
          <Text dimColor>Nothing needs your attention.</Text>
        ) : (
          <Box flexDirection="column">
            {rows.map(row => (
              <Box flexDirection="row" justifyContent="space-between" columnGap={2}>
                <Box flexShrink={1}>
                  <Text wrap="truncate-end">
                    <Text color={color(LEVEL_TONE[row.level])}>{row.glyph}</Text>
                    {` ${row.text}`}
                  </Text>
                </Box>
                {row.actions.length > 0 ? (
                  <Box flexDirection="row" columnGap={2} flexShrink={0}>
                    {row.actions.map(action => (
                      <Button key={action.key} label={action.label} plain onPress={runOn(() => runNow($, action.act))} />
                    ))}
                  </Box>
                ) : null}
              </Box>
            ))}
          </Box>
        )
      const summary = compact ? [] : nowSummary(snap, await read($, taskViewAtom), await read($, loopViewAtom))
      body =
        size === 'wide' && summary.length > 0 ? (
          <Box flexDirection="row" columnGap={4}>
            <Box flexDirection="column" flexGrow={1} flexShrink={1}>
              <Text dimColor>NEEDS ATTENTION</Text>
              {attention}
            </Box>
            <Box flexDirection="column" width={Math.max(30, Math.min(52, Math.round(width * 0.38)))} flexShrink={0}>
              <Text dimColor>AT A GLANCE</Text>
              {labelled(summary, 7)}
            </Box>
          </Box>
        ) : (
          <Box flexDirection="column">
            {attention}
            {summary.length > 0 ? <Box marginTop={1}>{labelled(summary, 7)}</Box> : null}
          </Box>
        )
    } else if (tab === 'phase') {
      // The ring unrolled: a flow line on the terminal where each phase gets nine cells, else the word list.
      const nodes = phaseNodes(snap.phase, snap.phasesVisited, snap.recommendedPhases)
      const flow = term ? flowLine(nodes, travelledTo(nodes), width) : null
      const next = nextPhase(snap.phase, snap.recommendedPhases)
      body = (
        <Box flexDirection="column">
          {nodes.length === 0 ? (
            <Text dimColor>No phases recorded yet.</Text>
          ) : flow !== null ? (
            <Box flexDirection="column">
              <Text wrap="truncate-end">
                {flow.head === '' ? null : flow.head}
                <Text dimColor>{flow.tail}</Text>
              </Text>
              <Text dimColor wrap="truncate-end">
                {flow.labels}
              </Text>
            </Box>
          ) : (
            <Text wrap="wrap">{phaseMap(snap.phase, snap.phasesVisited, snap.recommendedPhases)}</Text>
          )}
          <Box marginTop={space}>
            {labelled(
              [
                { label: 'NOW', value: snap.phase ? `${snap.phase} — ${label(snap.phase)}` : 'no phase set', dim: !snap.phase },
                ...(next !== null ? [{ label: 'NEXT', value: `/neuroflow:${next} — ${label(next)}` }] : []),
              ],
              7,
            )}
          </Box>
          <Box marginTop={space} flexDirection="row" flexWrap="wrap" justifyContent="space-between" columnGap={2}>
            <Text dimColor>{phaseLegend(nodes)}</Text>
            <Button key="nf-dash-switch" label="go to phase…" hotkey={DASH.goPhase} plain onPress={run(() => handOver($, () => openPicker($)))} />
          </Box>
        </Box>
      )
    } else if (tab === 'deadlines') {
      // A ruler of the coming weeks with each date's mark on its day, then the dates as a list.
      const dates = dateRows(snap)
      const scale = term && size !== 'narrow' && dates.length > 0 ? ruler(width, dates) : null
      const gatesWidth = gatesColumnWidth(dates, width, size)
      body =
        dates.length === 0 ? (
          <Text dimColor>No upcoming dates in .neuroflow/timeline.md.</Text>
        ) : (
          <Box flexDirection="column">
            {scale !== null ? (
              <Box flexDirection="column" marginBottom={space}>
                <Text dimColor wrap="truncate-end">
                  {scale.axis}
                </Text>
                <Text wrap="truncate-end">
                  {markRuns(scale.marks).map(part =>
                    part.tone !== undefined ? <Text color={TONE_COLOR[part.tone]}>{part.text}</Text> : part.dim ? <Text dimColor>{part.text}</Text> : part.text,
                  )}
                </Text>
              </Box>
            ) : null}
            {dates.map(row => (
              <Box flexDirection="row" columnGap={2}>
                <Box flexShrink={0}>
                  <Text color={color(row.tone)} dimColor={row.tone === undefined}>
                    {row.glyph}
                  </Text>
                </Box>
                <Box flexShrink={0}>
                  <Text dimColor>{row.date}</Text>
                </Box>
                <Box flexGrow={1} flexShrink={1}>
                  <Text wrap="truncate-end">{row.what}</Text>
                </Box>
                <Box flexShrink={0} width={11}>
                  <Text color={color(row.tone)} dimColor={row.tone === undefined} wrap="truncate-end">
                    {row.when}
                  </Text>
                </Box>
                {gatesWidth > 0 ? <Box flexShrink={0} width={gatesWidth}>{row.gates ? <Text dimColor wrap="truncate-end">{`gates ${row.gates}`}</Text> : null}</Box> : null}
              </Box>
            ))}
          </Box>
        )
    } else if (tab === 'integrity') {
      // A glyph, what it is, its state, and who set it (a word with every mark: rule 8).
      const name = 16
      body = (
        <Box flexDirection="column">
          {integrityRows(snap).map(item => (
            <Box flexDirection="column">
              <Box flexDirection="row" columnGap={1}>
                <Box flexShrink={0}>
                  <Text color={color(item.tone)} dimColor={item.dim === true}>
                    {item.glyph}
                  </Text>
                </Box>
                <Box flexShrink={0} width={name}>
                  <Text dimColor={item.dim === true}>{item.name}</Text>
                </Box>
                <Box flexGrow={1} flexShrink={1}>
                  <Text dimColor={item.dim === true} wrap="truncate-end">
                    {item.value}
                  </Text>
                </Box>
                {item.note !== null && size !== 'narrow' ? (
                  <Box flexShrink={0}>
                    <Text color={item.note.startsWith('not ') ? 'warning' : undefined} dimColor={!item.note.startsWith('not ')}>
                      {item.note}
                    </Text>
                  </Box>
                ) : null}
              </Box>
              {[...item.more, ...(item.note !== null && size === 'narrow' ? [item.note] : [])].map(line => (
                <Box flexDirection="row">
                  <Box flexShrink={0} width={name + 3} />
                  <Box flexShrink={1}>
                    <Text dimColor wrap="truncate-end">
                      {line}
                    </Text>
                  </Box>
                </Box>
              ))}
            </Box>
          ))}
          {snap.problems.map(problem => (
            <Text color="warning" wrap="wrap">{`! ${problem}`}</Text>
          ))}
          <Box marginTop={space} flexDirection="row" flexWrap="wrap" columnGap={3}>
            {frozenByPerson
              ? [
                  <Button key="nf-dash-verify" label="verify hashes" hotkey={DASH.verify} plain onPress={run(() => verifyFromDashboard($))} />,
                  <Button key="nf-dash-unfreeze" label="unfreeze…" plain onPress={runOn(() => unfreezeFromDashboard($))} />,
                ]
              : [
                  <Button
                    key="nf-dash-freeze"
                    label={snap.prereg?.status === 'frozen' ? 'confirm freeze…' : 'freeze prereg…'}
                    plain
                    onPress={runOn(() => freezeFromDashboard($))}
                  />,
                ]}
          </Box>
        </Box>
      )
    } else if (tab === 'tasks') {
      // The levels on one line, then the first open cards in columns: marks, title, owner, due date, level.
      const view = await read($, taskViewAtom)
      if (view === null) body = <Text dimColor>Reading the task boards…</Text>
      else {
        const cards = cardRows(view)
        const marksWidth = Math.max(0, ...cards.map(card => cells(card.marks)))
        const ownerWidth = size === 'narrow' ? 0 : Math.min(14, Math.max(0, ...cards.map(card => cells(card.owner))))
        const levelWidth = Math.min(18, Math.max(0, ...cards.map(card => cells(card.level))))
        body = (
          <Box flexDirection="column">
            <Text wrap="wrap">{levelSummary(view)}</Text>
            <Box flexDirection="column" marginTop={space}>
              {cards.length === 0 ? (
                <Text dimColor>No open tasks.</Text>
              ) : (
                cards.map(card => (
                  <Box flexDirection="row" columnGap={2}>
                    {marksWidth > 0 ? (
                      <Box flexShrink={0} width={marksWidth}>
                        {card.marks !== '' ? <Text color={card.overdue ? 'warning' : undefined}>{card.marks}</Text> : null}
                      </Box>
                    ) : null}
                    <Box flexGrow={1} flexShrink={1}>
                      <Text wrap="truncate-end">{card.title}</Text>
                    </Box>
                    {ownerWidth > 0 ? (
                      <Box flexShrink={0} width={ownerWidth}>
                        <Text dimColor wrap="truncate-end">
                          {card.owner}
                        </Text>
                      </Box>
                    ) : null}
                    <Box flexShrink={0} width={9}>
                      <Text color={card.overdue ? 'warning' : undefined} dimColor={!card.overdue}>
                        {card.due}
                      </Text>
                    </Box>
                    <Box flexShrink={0} width={levelWidth}>
                      <Text dimColor wrap="truncate-end">
                        {card.level}
                      </Text>
                    </Box>
                  </Box>
                ))
              )}
            </Box>
            <Box marginTop={space} flexDirection="row" flexWrap="wrap" justifyContent="space-between" columnGap={2}>
              <Text dimColor wrap="wrap">
                {cardLegend(view).join(' · ')}
              </Text>
              <Button key="nf-dash-boards" label="boards" hotkey={DASH.boards} plain onPress={run(() => handOver($, () => openBoard($)))} />
            </Box>
          </Box>
        )
      }
    } else {
      // The loop: where it stands, its quality as a sparkline as wide as the pane allows, its open questions.
      const loop = await read($, loopViewAtom)
      if (loop === null) body = <Text dimColor>{snap.loops.length === 0 ? 'No autoresearch loops.' : 'Loading the loop…'}</Text>
      else {
        const last = loop.running.length > 0 ? loop.running[loop.running.length - 1] : undefined
        const spark = Math.max(8, Math.min(48, width - 15 - 10))
        body = (
          <Box flexDirection="column">
            {labelled(
              [
                { label: loop.name, value: `${loop.phase} · ${loop.status} · iteration ${loop.iterations} · best ${loop.best}` },
                loop.running.length > 0
                  ? { label: 'quality', value: `${sparkline(loop.running, spark)}  ${last !== undefined && last > 0 ? '+' : ''}${last ?? ''}` }
                  : { label: 'quality', value: 'no iterations recorded yet', dim: true },
              ],
              15,
            )}
            <Box flexDirection="column" marginTop={space}>
              <Text dimColor>OPEN QUESTIONS</Text>
              {loop.questions.length > 0 ? loop.questions.map(question => <Text wrap="wrap">{question}</Text>) : <Text dimColor>none</Text>}
            </Box>
            <Box marginTop={space}>
              <Text dimColor wrap="wrap">
                Answer in the session (A3: …) or in the loop's answers.md.
              </Text>
            </Box>
          </Box>
        )
      }
    }
    // The tabs: the shown one as text at full strength, every other a dim key; a heavy segment of the rule under it.
    const strip = tabStrip(
      DASHBOARD_TABS.map(item => `${item.digit}: ${item.label}`),
      Math.max(0, DASHBOARD_TABS.findIndex(item => item.id === tab)),
      width,
    )
    const heavyFrom = strip.rule.indexOf('━')
    const heavyTo = strip.rule.lastIndexOf('━') + 1
    // The quiet legend: the keys as dim buttons, their words in full where the pane is wide, Enter and Esc on the right.
    const full = size === 'wide'
    const legend = keysHere ? (
      <Box flexDirection={size === 'narrow' ? 'column' : 'row'} justifyContent="space-between" columnGap={2}>
        <Box flexDirection="row" flexWrap="wrap" columnGap={2} flexShrink={1}>
          <Button key="nf-nav-left" label={full ? '‹ tab' : '‹'} hotkey={NAV.left} plain dimColor onPress={run(() => selectTab($, tabNeighbour(tab, -1)))} />
          <Button key="nf-nav-right" label={full ? 'tab ›' : '›'} hotkey={NAV.right} plain dimColor onPress={run(() => selectTab($, tabNeighbour(tab, 1)))} />
          {ringKeys.length > 0
            ? [
                <Button key="nf-nav-down" label={full ? '▾ row' : '▾'} hotkey={NAV.down} plain dimColor onPress={run(() => stepRing($, DASHBOARD, ringKeys, 1, NOW_START))} />,
                <Button key="nf-nav-up" label={full ? '▴ row' : '▴'} hotkey={NAV.up} plain dimColor onPress={run(() => stepRing($, DASHBOARD, ringKeys, -1, NOW_START))} />,
              ]
            : null}
          <Button key="nf-dash-reread" label="reread" hotkey={NAV.reread} plain dimColor onPress={run(() => rereadDashboard($))} />
          <Button key="nf-dash-close" label="close" hotkey={NAV.close} plain dimColor role="dismiss" onPress={run(() => $.ui.close({ id: DASHBOARD }))} />
        </Box>
        {term ? (
          <Box flexShrink={0}>
            <Text dimColor>{ringKeys.length > 0 ? 'enter: act · esc: prompt' : tab === 'integrity' ? 'tab, enter: act · esc: prompt' : 'esc: prompt'}</Text>
          </Box>
        ) : null}
      </Box>
    ) : (
      <Text dimColor wrap="truncate-end">
        {unfocusedHint('/neuroflow:dashboard')}
      </Text>
    )
    return (
      <Box flexDirection="column">
        {compact || size === 'narrow' ? (
          <Text wrap="truncate-end">
            {`${MARK} ${WORDMARK}`}
            <Text dimColor>{` · ${dashboardTitle(snap)}`}</Text>
          </Text>
        ) : (
          <Box flexDirection="row" justifyContent="space-between" columnGap={2}>
            <Box flexShrink={0}>
              <Text>{`${MARK} ${WORDMARK}`}</Text>
            </Box>
            <Box flexShrink={1}>
              <Text dimColor wrap="truncate-end">
                {dashboardTitle(snap)}
              </Text>
            </Box>
          </Box>
        )}
        {behind !== null ? (
          <Box flexDirection="row" justifyContent="space-between" columnGap={2}>
            <Box flexShrink={1}>
              <Text color={TONE_COLOR.warning} wrap={compact ? 'truncate-end' : 'wrap'}>{`↑ ${behind}`}</Text>
            </Box>
            <Box flexShrink={0}>
              <Button key="nf-dash-migrate" label="migrate" plain onPress={runOn(() => runKey($, 'neuroflow:migrate', '', runAsk('neuroflow:migrate', '')))} />
            </Box>
          </Box>
        ) : null}
        <Box flexDirection="row" flexWrap="wrap" columnGap={strip.gap} marginTop={behind !== null ? space : 0}>
          {DASHBOARD_TABS.map(item =>
            item.id === tab ? (
              // The shown tab at full strength, a key with no letter: Enter on it reads the tab again. On now it is
              // where j and k start (NOW_START), so a typed j or k never puts the ring on an action.
              <Button key={`nf-tab-${item.id}`} label={`${item.digit}: ${item.label}`} plain onPress={run(() => rereadDashboard($))} />
            ) : (
              <Button key={`nf-tab-${item.id}`} label={item.label} hotkey={item.digit} plain dimColor onPress={run(() => selectTab($, item.id))} />
            ),
          )}
        </Box>
        {term ? (
          heavyFrom < 0 ? (
            <Text dimColor wrap="truncate-end">
              {strip.rule}
            </Text>
          ) : (
            <Text wrap="truncate-end">
              <Text dimColor>{strip.rule.slice(0, heavyFrom)}</Text>
              {strip.rule.slice(heavyFrom, heavyTo)}
              <Text dimColor>{strip.rule.slice(heavyTo)}</Text>
            </Text>
          )
        ) : null}
        <Box flexDirection="column" marginTop={space}>
          {body}
        </Box>
        {term && !compact ? (
          <Box marginTop={space}>
            <Text dimColor wrap="truncate-end">
              {rule(width)}
            </Text>
          </Box>
        ) : null}
        <Box flexDirection="column" marginTop={term ? 0 : 1}>
          {legend}
        </Box>
      </Box>
    )
  }).catch(($, e, next) => next(e))

  on('ui.render', { component: 'Pane', requestId: PICKER }, async ($, e) => {
    rememberViewport(e.viewport)
    const snap = await read($, snapshotAtom)
    const note = await read($, pickerNoteAtom)
    const options = pickerOptions(snap?.phase ?? null, snap?.phasesVisited ?? [], snap?.recommendedPhases ?? [])
    const pick = async (value: string): Promise<void> => {
      // An Enter typed through the open would switch to the highlighted phase: dropped (lib/keys.ts).
      if (!isPastTypeThrough(await $.clock.now(), (await read($, openedAtAtom))[PICKER])) return
      // A switch is recorded as the person's choice (project_config.md and a reasoning entry): asked, safe answer first.
      if (!(await confirm($, `Make ${value} the active phase? It is recorded as your choice.`, 'Not now', `Switch to ${value}`, 'phase'))) return
      const message = await switchPhase($, value, 'phase picker')
      if (message.startsWith('Active phase')) {
        await $.ui.close({ id: PICKER })
        $.ui.toast(`neuroflow: ${message}`)
      } else await update($, pickerNoteAtom, () => message)
    }
    if (e.surface === 'mobile') {
      const { Box, Button, Text } = $.ui.resolve(e)
      return (
        <Box flexDirection="column">
          {options.slice(0, 8).map(option => (
            <Button key={`nf-pick-${option.value}`} label={option.short} onPress={() => pick(option.value)} />
          ))}
          {note !== null ? <Text color="warning">{note}</Text> : null}
        </Box>
      )
    }
    const { Box, Select, Text } = $.ui.resolve(e)
    const width = e.props.bodyColumns
    const term = e.surface === 'terminal'
    const compact = isCompact(e.viewport?.rows ?? measuredRows())
    return (
      <Box flexDirection="column">
        <Box flexDirection="row" justifyContent="space-between" columnGap={2}>
          <Box flexShrink={0}>
            <Text>{`${MARK} switch phase`}</Text>
          </Box>
          <Box flexShrink={1}>
            <Text dimColor wrap="truncate-end">{`now: ${snap?.phase ?? 'none'}`}</Text>
          </Box>
        </Box>
        {term ? (
          <Text dimColor wrap="truncate-end">
            {rule(width)}
          </Text>
        ) : null}
        <Box flexDirection="column" marginY={compact || !term ? 0 : 1}>
          <Select
            key="nf-phase-select"
            label="Phase  "
            options={options.map(option => ({ value: option.value, label: option.label }))}
            value={snap?.phase ?? undefined}
            autoFocus
            onSelect={value => {
              void pick(value)
            }}
          />
          {note !== null ? <Text color="warning">{note}</Text> : null}
        </Box>
        {term && !compact ? (
          <Text dimColor wrap="truncate-end">
            {rule(width)}
          </Text>
        ) : null}
        {!term ? null : e.props.isFocused ? (
          <Box flexDirection={widthClass(width) === 'narrow' ? 'column' : 'row'} justifyContent="space-between" columnGap={2}>
            <Box flexShrink={1}>
              <Text dimColor wrap="wrap">
                ↓ or enter: open · ↑↓: move · a letter: jump · enter: switch (asks)
              </Text>
            </Box>
            <Box flexShrink={0}>
              <Text dimColor>esc: close</Text>
            </Box>
          </Box>
        ) : (
          <Text dimColor wrap="truncate-end">
            {unfocusedHint('/neuroflow:phase')}
          </Text>
        )}
      </Box>
    )
  }).catch(($, e, next) => next(e))
}
