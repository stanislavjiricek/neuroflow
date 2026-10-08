// Views — the project at a glance, drawn by code at zero tokens (charter: quiet by default).
//  - the band above the prompt (M080, M064, M214): one line of what needs attention, letter hotkeys only
//  - the dashboard pane (M069, M084): phase map, deadlines, integrity, tasks, autoresearch loop
//  - /neuroflow:phase answered in code (M163, M011): a picker — arrows and Enter, or a click
//  - /neuroflow:dashboard opens the pane; its integrity tab freezes, verifies and unfreezes a
//    preregistration on a person's key press and confirmation (M018), through freeze.py
//  - /neuroflow:tasks opens the task boards of every level — project, flowie, each hive (M070, M163)
// Without the mod, commands/phase.md, commands/dashboard.md and commands/tasks.md do the same in prose.
import { atom, read, update } from 'claude-code'
import type { EngineInterface, On } from 'claude-code'

import type { NfDashboardTab, NfFlowieSync, NfLoopView, NfSnapshot, NfTaskView } from '../../../types'
import { setActivePhase } from '../lib/config'
import { NO_SYNC, SYNC_QUEUE, asQueue, enqueue, syncState } from '../lib/flowiesync'
import type { NfIo } from '../lib/io'
import { appendLine, isoDate, sessionLine, sessionLogPath } from '../lib/memory'
import type { NfOptions } from '../lib/options'
import { join, resolveFrom, toSlash } from '../lib/paths'
import { PHASES, isPhase, nextPhase, phaseMap, pickerOrder } from '../lib/phases'
import { KNOWN_SCHEMA, loadSnapshot, versionNotice } from '../lib/project'
import { parseJson, runScript } from '../lib/scripts'
import { MINE, levelCardLine, levelSummary, loadTaskView, moveCommand, openingLevel, topCards } from '../lib/tasks'
import { isQuiet } from './scope'

const scopeAtom = atom({ plugin: 'neuroflow', key: 'scope' } as const, null)
const snapshotAtom = atom({ plugin: 'neuroflow', key: 'snapshot' } as const, null)
const activeCommandAtom = atom({ plugin: 'neuroflow', key: 'activeCommand' } as const, null)
const tabAtom = atom({ plugin: 'neuroflow', key: 'dashboardTab' } as const, 'phase')
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

const DASHBOARD = 'nf-dashboard'
const PICKER = 'nf-phase'
const BOARD = 'nf-board'
/** $.store key: the ISO date on which the person hid the band (a preference, not research state). */
const BAND_HIDDEN_ON = 'band.hiddenOn'

const TABS: readonly { id: NfDashboardTab; label: string; hotkey: string }[] = [
  { id: 'phase', label: 'phase', hotkey: 'p' },
  { id: 'deadlines', label: 'deadlines', hotkey: 'd' },
  { id: 'integrity', label: 'integrity', hotkey: 'i' },
  { id: 'tasks', label: 'tasks', hotkey: 't' },
  { id: 'loop', label: 'loop', hotkey: 'l' },
]

// ── pure helpers (exported for tests) ──────────────────────────────────────────────────────────

export type Tone = 'error' | 'warning' | 'success' | 'suggestion' | 'subtle'
export type Line = { text: string; tone?: Tone; dim?: boolean }
/** A press on the band runs one neuroflow command (the person's explicit request). */
export type BandAction = { key: string; label: string; hotkey: string; command: string; args: string }
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
  const actions = [{ key: 'nf-flowie-sync', label: 'sync', hotkey: 's', command: 'neuroflow:flowie', args: '--sync' }]
  if (sync.failure !== null) return { level: 'warn', glyph: '!', text: `flowie not synced: ${sync.failure} — /neuroflow:flowie --sync`, actions }
  if (sync.pending.length > 0) {
    return { level: 'warn', glyph: '↻', text: `flowie sync pending (${sync.pending.join(', ')}) — it runs when a turn ends, or /neuroflow:flowie --sync`, actions }
  }
  return null
}

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
        { key: 'nf-meet-prepare', label: 'prepare', hotkey: 'p', command: 'neuroflow:meeting', args: `--prepare ${upcoming.slug}` },
        { key: 'nf-meet-notes', label: 'notes', hotkey: 'o', command: 'neuroflow:meeting', args: `--notes ${upcoming.slug}` },
      ],
    })
  }
  const unclosed = snap.meetings.find(meeting => !meeting.closed && meeting.startsIn < -120 && meeting.openActions > 0)
  if (unclosed !== undefined) {
    items.push({
      level: 'warn',
      glyph: '!',
      text: `meeting "${unclosed.title}" not closed — ${unclosed.openActions} open action item(s)`,
      actions: [{ key: 'nf-meet-close', label: 'close', hotkey: 'c', command: 'neuroflow:meeting', args: `--close ${unclosed.slug}` }],
    })
  }
  // A flowie sync the mod queued (wellbeing, ideas) that has not gone through yet; ahead of the version notice,
  // because /neuroflow:migrate skips a flowie with uncommitted changes.
  const syncing = flowieSyncItem(sync)
  if (syncing !== null) items.push(syncing)
  // After a plugin update, until /neuroflow:migrate has run (neuroflow-core → Command lifecycle, version notice).
  // It waits behind the time-bound items: a meeting within two hours keeps the one quiet-band seat and its keys.
  const behind = versionNotice(snap)
  if (behind !== null) {
    items.push({
      level: 'warn',
      glyph: '↑',
      text: behind,
      actions: [{ key: 'nf-migrate', label: 'migrate', hotkey: 'm', command: 'neuroflow:migrate', args: '' }],
    })
  }
  if (!quiet) {
    if (snap.wikiPending > 0) {
      items.push({
        level: 'info',
        glyph: '✎',
        text: `${snap.wikiPending} wiki card${snap.wikiPending === 1 ? '' : 's'} waiting for review`,
        actions: [{ key: 'nf-wiki-review', label: 'review', hotkey: 'w', command: 'neuroflow:wiki', args: '--review' }],
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

/**
 * The tasks tab (commands/dashboard.md → Tasks): open tasks per level on one line, this project's share in
 * brackets, then the first open cards across levels — this project's first, overdue first, then by due date —
 * each tagged with its level. Every mark has a word in the last line.
 */
export const taskLines = (view: NfTaskView | null, max = 5): Line[] => {
  if (view === null) return [{ text: 'Reading the task boards…', dim: true }]
  const cards = topCards(view, max)
  const marked = cards.some(({ level, card }) => card.isMine && level.kind !== 'project')
  const overdue = cards.some(({ card }) => card.overdue)
  const key = [
    ...(marked && view.linkedProject !== null ? [`${MINE} this project (${view.linkedProject})`] : []),
    ...(overdue ? ['⚠ overdue'] : []),
    '/neuroflow:tasks opens the boards (v switches level)',
  ]
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
  if (tab === 'phase') {
    const map = phaseMap(snap.phase, snap.phasesVisited, snap.recommendedPhases)
    const next = nextPhase(snap.phase, snap.recommendedPhases)
    return [
      { text: map === '' ? 'No phases recorded yet.' : map },
      { text: `Current: ${snap.phase ?? 'none'}${snap.phase ? ` — ${label(snap.phase)}` : ''}` },
      ...(next !== null ? [{ text: `Next: /neuroflow:${next} — ${label(next)}`, dim: true }] : []),
      { text: '● current  ✔ visited  ○ recommended', dim: true },
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
    { text: loop.running.length > 0 ? `quality ${sparkline(loop.running)}  ${last !== null && last > 0 ? '+' : ''}${last ?? ''}` : 'no iterations recorded yet', dim: loop.running.length === 0 },
    ...(loop.questions.length > 0
      ? [{ text: 'Open questions:', tone: 'warning' as Tone }, ...loop.questions.map(question => ({ text: `  ${question}` }))]
      : [{ text: 'No open questions.', dim: true }]),
    { text: 'Answer in the session (A3: …) or in the loop\'s answers.md.', dim: true },
  ]
}

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
const loadTasks = async ($: EngineInterface): Promise<void> => {
  const scope = await read($, scopeAtom)
  if (scope?.root === null || scope === null) return
  const io = ioOf($)
  const home = await io.home()
  const view = await loadTaskView(io, scope.root, home ? toSlash(home) : null, isoDate(await io.now()))
  await update($, taskViewAtom, () => view)
}

const selectTab = async ($: EngineInterface, tab: NfDashboardTab): Promise<void> => {
  await update($, tabAtom, () => tab)
  if (tab === 'loop') await loadLoopView($)
  if (tab === 'tasks') await loadTasks($)
}

const openDashboard = async ($: EngineInterface, tab?: string): Promise<void> => {
  const wanted = TABS.find(item => item.id === tab)
  if (wanted !== undefined) await selectTab($, wanted.id)
  else {
    const current = await read($, tabAtom)
    if (current === 'loop') await loadLoopView($)
    if (current === 'tasks') await loadTasks($)
  }
  await $.ui.open({ id: DASHBOARD, title: 'neuroflow' })
}

const openPicker = async ($: EngineInterface): Promise<void> => {
  await update($, pickerNoteAtom, () => null)
  await $.ui.open({ id: PICKER, title: 'Switch phase', focus: true, closeOnEscape: true, rows: 12 })
}

const isPersonThere = async ($: EngineInterface): Promise<boolean> => (await $.session.surfaces()).length > 0

/**
 * Opens the board pane on the level commands/tasks.md names: the project's when it has open tasks, else the first
 * level with open tasks of this project, else the first with any open tasks.
 */
const openBoard = async ($: EngineInterface): Promise<void> => {
  await loadTasks($)
  const view = await read($, taskViewAtom)
  await update($, boardPickAtom, () => null)
  await update($, boardLevelAtom, () => (view === null ? null : openingLevel(view)))
  await $.ui.open({ id: BOARD, title: 'tasks' })
}

/** The board pane's level switch: the next level after the shown one, back to the first after the last. */
const nextLevel = async ($: EngineInterface): Promise<void> => {
  const view = await read($, taskViewAtom)
  if (view === null || view.levels.length === 0) return
  const shown = await read($, boardLevelAtom)
  const at = view.levels.findIndex(level => level.id === shown)
  await update($, boardPickAtom, () => null)
  await update($, boardLevelAtom, () => view.levels[(at + 1) % view.levels.length].id)
}

const hideBandToday = async ($: EngineInterface): Promise<void> => {
  await $.store.set(BAND_HIDDEN_ON, isoDate(await $.clock.now()))
  await update($, bandHiddenAtom, () => true)
}

/** Three whole numbers 1–10 and optional notes after them ("3 6 7 slept badly"), or null. */
export const parseWellbeing = (value: string): { anxiety: number; energy: number; happiness: number; notes: string } | null => {
  const match = /^\s*(\d{1,2})[\s,/]+(\d{1,2})[\s,/]+(\d{1,2})\s*(.*)$/s.exec(value)
  if (match === null) return null
  const [anxiety, energy, happiness] = [match[1], match[2], match[3]].map(Number)
  if (![anxiety, energy, happiness].every(score => Number.isInteger(score) && score >= 1 && score <= 10)) return null
  return { anxiety, energy, happiness, notes: match[4].trim() }
}

/**
 * Writes today's self-reported entry exactly as /flowie --assess does, queues its sync to the private flowie
 * repository (the mod's own cache) and returns. Scores go only into the file: never into state, toasts or context.
 *
 * It runs git nowhere: this is the band Input's closure, whose handle the engine keeps only for the lifetime of
 * the drawing, and the band redraws without the field as soon as the entry exists. A closure that ran the sync
 * here could stop between two git calls and leave the entry written, no git run, no log line and the flowie dirty
 * (a dirty flowie also makes /neuroflow:migrate skip it). So the sync is queued in $.store before the entry is
 * written — before anything can redraw the band — and runs from a hook dispatch: the next turn's end or the next
 * session's start (capture.ts, lib/flowiesync.ts). A closure that stops anywhere after that loses nothing; one that
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
    $.ui.toast(`neuroflow: wellbeing logged for ${today} — it syncs to your flowie when a turn ends`)
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

/** M065 — the mark a phase command gets in the slash menu: the current phase and the recommended next one. */
export const phaseMark = (command: string, current: string | null, next: string | null): string | null =>
  command === current ? '● current phase ·' : command === next ? '→ next ·' : null

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
    return { text: 'Phase picker open — ↑↓ and Enter, or click. Esc closes it. (Any argument runs the full /phase flow.)' }
  }).catch(($, e, next) => next(e))

  on('command.run', { command: 'neuroflow:dashboard' }, async ($, e, next) => {
    const scope = await read($, scopeAtom)
    if (!scope?.isActive || !(await isPersonThere($))) return next(e)
    await openDashboard($, e.args.trim())
    return { text: 'Dashboard open — p phase · d deadlines · i integrity · t tasks · l loop.' }
  }).catch(($, e, next) => next(e))

  // /neuroflow:tasks — bare: the task boards of every level as a pane (M070, M163); anything else: the prose flow.
  on('command.run', { command: 'neuroflow:tasks' }, async ($, e, next) => {
    const scope = await read($, scopeAtom)
    if (!scope?.isActive || e.args.trim() !== '' || !(await isPersonThere($))) return next(e)
    await openBoard($)
    return {
      text: 'Task boards open — project, flowie and each hive, v switches the level; pick a card, then the column to move it to. (Any argument runs the full /tasks flow: --list, --add, --move, --level, --hive.)',
    }
  }).catch(($, e, next) => next(e))

  on('ui.render', { component: 'Pane', requestId: BOARD }, async ($, e) => {
    const { Box, Button, Text } = $.ui.resolve(e)
    const view = await read($, taskViewAtom)
    if (view === null) return <Text dimColor>Reading the task boards…</Text>
    const shown = await read($, boardLevelAtom)
    const level = view.levels.find(item => item.id === shown) ?? view.levels[0]
    if (level === undefined) return <Text dimColor>No task board here yet — /neuroflow:tasks --add "title" starts one.</Text>
    const board = level.board
    const pick = await read($, boardPickAtom)
    const width = Math.max(14, Math.floor((e.props.bodyColumns - 2) / Math.max(1, board.columns.length)))
    const marked = level.kind !== 'project' && level.mine > 0 && view.linkedProject !== null
    return (
      <Box flexDirection="column" gap={1}>
        <Box flexDirection="row" flexWrap="wrap" columnGap={1}>
          <Text>level:</Text>
          {view.levels.map(item => (
            <Button
              key={`nf-level-${item.id}`}
              label={item.id === level.id ? `[${item.name} ${item.open}]` : `${item.name} ${item.open}`}
              variant={item.id === level.id ? 'primary' : 'secondary'}
              onPress={async () => {
                await update($, boardPickAtom, () => null)
                await update($, boardLevelAtom, () => item.id)
              }}
            />
          ))}
          {view.levels.length > 1 ? <Button key="nf-level-next" label="next level" hotkey="v" onPress={() => nextLevel($)} /> : null}
        </Box>
        <Box flexDirection="row">
          {board.columns.map(column => (
            <Box key={`nf-col-${column.id}`} flexDirection="column" width={width} borderStyle="single" paddingX={1}>
              <Text bold wrap="truncate-end">{column.label} {column.total}</Text>
              {column.cards.map(card => (
                <Button
                  key={`nf-card-${card.slug}`}
                  label={levelCardLine(card, level.kind).slice(0, width - 4)}
                  plain
                  variant={pick === card.slug ? 'primary' : 'secondary'}
                  onPress={() => update($, boardPickAtom, () => (pick === card.slug ? null : card.slug))}
                />
              ))}
              {column.total > column.cards.length ? <Text dimColor>+{column.total - column.cards.length} more</Text> : null}
            </Box>
          ))}
        </Box>
        {pick !== null ? (
          <Box flexDirection="row" flexWrap="wrap" columnGap={1}>
            <Text>move {pick} to:</Text>
            {[...board.columns.map(column => column.id), 'done'].map(target => (
              <Button
                key={`nf-move-${target}`}
                label={target}
                onPress={async () => {
                  await $.prompt.fill({ text: moveCommand(level, pick, target) })
                  await update($, boardPickAtom, () => null)
                  $.ui.toast('neuroflow: press Enter to move it — /tasks moves the file and records it')
                }}
              />
            ))}
          </Box>
        ) : null}
        <Box flexDirection="row" flexWrap="wrap" columnGap={1}>
          <Text dimColor>{`done: ${board.done} · archived: ${board.archived} · level: ${level.name}${marked ? ` · ${MINE} ${view.linkedProject} (this project)` : ''}`}</Text>
          <Button key="nf-board-refresh" label="refresh" hotkey="r" onPress={() => loadTasks($)} />
          <Button key="nf-board-close" label="close" hotkey="c" role="dismiss" onPress={() => $.ui.close({ id: BOARD })} />
        </Box>
      </Box>
    )
  }).catch(($, e, next) => next(e))

  // The boards and the tasks tab follow the files: once read this session, they are read again as each turn
  // ends (a /tasks --move the board filled in has run by then). Only the local files are read, never pulled.
  on('turn.complete', { reason: ['answer', 'aborted', 'error', 'refusal'] }, async ($, e, next) => {
    const result = await next(e)
    if (e.agentId === undefined && (await read($, taskViewAtom)) !== null) await loadTasks($).catch(() => undefined)
    return result
  }).catch(($, e, next) => next(e))

  // The band: one line of what needs attention; nothing when nothing does.
  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (opts.band === 'off' || e.props.hasSurvey) return next(e)
    const scope = await read($, scopeAtom)
    if (!scope?.isActive || scope.isHeadless) return next(e)
    if ((await read($, activeCommandAtom))?.lifecycle === 'quiet' || isQuiet(await read($, quietAtom), await $.clock.now())) return next(e)
    // A drafted decision waits for a person's keep or drop (M009); it outranks everything else.
    const draft = await read($, draftAtom)
    if (draft !== null) {
      const { Box, Button, Text } = $.ui.resolve(e)
      return (
        <Box flexDirection="row" flexWrap="wrap" columnGap={2}>
          <Text color="suggestion" wrap="truncate-end">✎ decision drafted for {draft.phase}: {draft.statement}</Text>
          <Button key="nf-draft-keep" label="keep" hotkey="k" plain onPress={() => settleDraft($, true)} />
          <Button key="nf-draft-drop" label="drop" hotkey="n" plain onPress={() => settleDraft($, false)} />
        </Box>
      )
    }
    // A driven autoresearch loop always shows, with its stop control (charter: no paid turns without one).
    const drive = await read($, driveAtom)
    if (drive !== null) {
      const { Box, Button, Text } = $.ui.resolve(e)
      return (
        <Box flexDirection="row" flexWrap="wrap" columnGap={2}>
          <Text color="suggestion" wrap="truncate-end">
            ↻ driving autoresearch "{drive.name}" · turn {drive.turns}
            {drive.errors > 0 ? ` · ${drive.errors} error(s) in a row` : ''}
          </Text>
          <Button
            key="nf-drive-stop"
            label="stop"
            hotkey="s"
            plain
            onPress={async () => {
              await update($, driveAtom, () => null)
              const root = (await read($, scopeAtom))?.root
              const now = await $.clock.now()
              if (root) await appendLine(ioOf($), sessionLogPath(root, now), sessionLine(now, `autoresearch/${drive.name}`, `driver stopped after ${drive.turns} turn(s): stopped by the person`))
              $.ui.toast(`neuroflow: stopped driving "${drive.name}" — the current iteration finishes, no new one starts`)
            }}
          />
          <Button key="nf-band-dashboard" label="dashboard" hotkey="d" plain onPress={() => openDashboard($, 'loop')} />
        </Box>
      )
    }
    // A live note capture shows while it runs: messages go to the notes, not to the model.
    const capture = await read($, captureAtom)
    if (capture !== null) {
      const { Box, Button, Text } = $.ui.resolve(e)
      return (
        <Box flexDirection="row" flexWrap="wrap" columnGap={2}>
          <Text color="warning" wrap="truncate-end">
            ● capturing notes → {capture.target} · {capture.count} entr{capture.count === 1 ? 'y' : 'ies'} · messages are not sent to the model
          </Text>
          <Button key="nf-capture-done" label="done" hotkey="e" plain onPress={() => $.prompt.submit({ text: 'done' }).then(() => undefined)} />
        </Box>
      )
    }
    // Hidden for today: the press sets the state (redraw now) and the store (kept across sessions).
    const isHidden = (await read($, bandHiddenAtom)) || (await $.store.get(BAND_HIDDEN_ON)) === isoDate(await $.clock.now())
    if (isHidden) return next(e)
    const snap = await read($, snapshotAtom)
    if (snap === null) return next(e)
    const items = bandItems(snap, opts.band === 'quiet', await read($, flowieSyncAtom))
    // Self-reported wellbeing (M146, opt-in in flowie): one field, no scores kept anywhere but the file.
    const idle = (await read($, activeCommandAtom)) === null
    if (snap.wellbeingDue && idle && e.surface !== 'mobile' && items[0]?.level !== 'alert') {
      const { Box, Button, Input, Text } = $.ui.resolve(e)
      return (
        <Box flexDirection="row" flexWrap="wrap" columnGap={2}>
          <Text color="suggestion">wellbeing today — anxiety, energy, happiness (1–10):</Text>
          <Input key="nf-wellbeing" placeholder="e.g. 3 6 7" submitLabel="save" onSubmit={(value: string) => saveWellbeing($, value)} />
          <Button key="nf-band-hide" label="not today" hotkey="x" plain onPress={() => hideBandToday($)} />
        </Box>
      )
    }
    if (items.length === 0) return next(e)
    const shown = items.slice(0, opts.band === 'quiet' ? 1 : 2)
    const more = items.length - shown.length
    const actions = bandActions(shown)
    const { Box, Button, Text } = $.ui.resolve(e)
    return (
      <Box flexDirection="row" flexWrap="wrap" columnGap={2}>
        {shown.map(item => (
          <Text color={item.level === 'alert' ? 'error' : item.level === 'warn' ? 'warning' : 'suggestion'} wrap="truncate-end">
            {item.glyph} {item.text}
          </Text>
        ))}
        {more > 0 ? <Text dimColor>+{more} more</Text> : null}
        {actions.map(action => (
          <Button key={action.key} label={action.label} hotkey={action.hotkey} plain onPress={() => $.command.run({ command: action.command, args: action.args }).then(() => undefined)} />
        ))}
        <Button key="nf-band-dashboard" label="dashboard" hotkey="d" plain onPress={() => openDashboard($)} />
        <Button key="nf-band-hide" label="hide today" hotkey="x" plain onPress={() => hideBandToday($)} />
      </Box>
    )
  }).catch(($, e, next) => next(e))

  on('ui.render', { component: 'Pane', requestId: DASHBOARD }, async ($, e) => {
    const { Box, Button, Text } = $.ui.resolve(e)
    const snap = await read($, snapshotAtom)
    if (snap === null) {
      const scope = await read($, scopeAtom)
      return <Text dimColor>neuroflow: {scope === null ? 'not started yet' : scope.reason}</Text>
    }
    const tab = await read($, tabAtom)
    const lines = tabLines(tab, snap, await read($, loopViewAtom), tab === 'tasks' ? await read($, taskViewAtom) : null)
    const frozenByPerson = snap.prereg?.status === 'frozen' && snap.prereg.setBy === 'person'
    const title = `${snap.projectName ?? 'neuroflow project'} · ${snap.phase ?? 'no phase'}${snap.mode ? ` · ${snap.mode}` : ''}`
    // The prose dashboard's Update line (commands/dashboard.md): here too, also after the band was hidden for today.
    const behind = versionNotice(snap)
    return (
      <Box flexDirection="column" gap={1}>
        <Text bold wrap="truncate-end">{title}</Text>
        {behind !== null ? <Text color={TONE_COLOR.warning} wrap="wrap">{`↑ ${behind}`}</Text> : null}
        <Box flexDirection="row" flexWrap="wrap" columnGap={1}>
          {TABS.map(item => (
            <Button
              key={`nf-tab-${item.id}`}
              label={item.id === tab ? `[${item.label}]` : item.label}
              hotkey={item.hotkey}
              variant={item.id === tab ? 'primary' : 'secondary'}
              onPress={() => selectTab($, item.id)}
            />
          ))}
        </Box>
        <Box flexDirection="column">
          {lines.map(line => (
            <Text color={line.tone ? TONE_COLOR[line.tone] : undefined} dimColor={line.dim === true} wrap="truncate-end">
              {line.text}
            </Text>
          ))}
        </Box>
        <Box flexDirection="row" columnGap={1}>
          {tab === 'phase' ? <Button key="nf-dash-switch" label="switch phase" hotkey="s" onPress={() => openPicker($)} /> : null}
          {tab === 'loop' ? <Button key="nf-dash-refresh" label="refresh" hotkey="r" onPress={() => loadLoopView($)} /> : null}
          {tab === 'tasks' ? <Button key="nf-dash-boards" label="boards" hotkey="b" onPress={() => openBoard($)} /> : null}
          {tab === 'tasks' ? <Button key="nf-dash-tasks-refresh" label="refresh" hotkey="r" onPress={() => loadTasks($)} /> : null}
          {tab === 'integrity' && !frozenByPerson ? (
            <Button key="nf-dash-freeze" label={snap.prereg?.status === 'frozen' ? 'confirm freeze…' : 'freeze prereg…'} hotkey="f" onPress={() => freezeFromDashboard($)} />
          ) : null}
          {tab === 'integrity' && frozenByPerson ? <Button key="nf-dash-verify" label="verify" hotkey="v" onPress={() => verifyFromDashboard($)} /> : null}
          {tab === 'integrity' && frozenByPerson ? <Button key="nf-dash-unfreeze" label="unfreeze…" hotkey="u" onPress={() => unfreezeFromDashboard($)} /> : null}
          {behind !== null ? (
            <Button key="nf-dash-migrate" label="migrate" hotkey="m" onPress={() => $.command.run({ command: 'neuroflow:migrate', args: '' }).then(() => undefined)} />
          ) : null}
          <Button key="nf-dash-close" label="close" hotkey="c" role="dismiss" onPress={() => $.ui.close({ id: DASHBOARD })} />
        </Box>
      </Box>
    )
  }).catch(($, e, next) => next(e))

  on('ui.render', { component: 'Pane', requestId: PICKER }, async ($, e) => {
    const snap = await read($, snapshotAtom)
    const note = await read($, pickerNoteAtom)
    const order = pickerOrder(snap?.phase ?? null, snap?.recommendedPhases ?? [])
    const tag = (id: string): string =>
      id === snap?.phase ? '  (current)' : snap?.recommendedPhases.includes(id) ? '  (recommended)' : snap?.phasesVisited.includes(id) ? '  (visited)' : ''
    const pick = async (value: string): Promise<void> => {
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
          {order.slice(0, 8).map(phase => <Button key={`nf-pick-${phase.id}`} label={`${phase.id}${tag(phase.id)}`} onPress={() => pick(phase.id)} />)}
          {note !== null ? <Text color="warning">{note}</Text> : null}
        </Box>
      )
    }
    const { Box, Select, Text } = $.ui.resolve(e)
    return (
      <Box flexDirection="column">
        <Select
          key="nf-phase-select"
          label="Phase "
          options={order.map(phase => ({ value: phase.id, label: `${phase.id} — ${phase.label}${tag(phase.id)}` }))}
          value={snap?.phase ?? undefined}
          autoFocus
          onSelect={value => {
            void pick(value)
          }}
        />
        {note !== null ? <Text color="warning">{note}</Text> : null}
        <Text dimColor>↑↓ move · Enter switch · Esc close</Text>
      </Box>
    )
  }).catch(($, e, next) => next(e))
}
