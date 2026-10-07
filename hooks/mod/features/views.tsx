// Views — the project at a glance, drawn by code at zero tokens (charter: quiet by default).
//  - the band above the prompt (M080, M064, M214): one line of what needs attention, letter hotkeys only
//  - the dashboard pane (M069, M084): phase map, deadlines, integrity, tasks, autoresearch loop
//  - /neuroflow:phase answered in code (M163, M011): a picker — arrows and Enter, or a click
//  - /neuroflow:dashboard opens the pane
// Without the mod, commands/phase.md and commands/dashboard.md do the same in prose.
import { atom, read, update } from 'claude-code'
import type { EngineInterface, On } from 'claude-code'

import type { NfDashboardTab, NfLoopView, NfSnapshot } from '../../../types'
import { setActivePhase } from '../lib/config'
import type { NfIo } from '../lib/io'
import { appendLine, isoDate, sessionLine, sessionLogPath } from '../lib/memory'
import type { NfOptions } from '../lib/options'
import { join, resolveFrom } from '../lib/paths'
import { PHASES, isPhase, nextPhase, phaseMap, pickerOrder } from '../lib/phases'
import { loadSnapshot } from '../lib/project'

const scopeAtom = atom({ plugin: 'neuroflow', key: 'scope' } as const, null)
const snapshotAtom = atom({ plugin: 'neuroflow', key: 'snapshot' } as const, null)
const activeCommandAtom = atom({ plugin: 'neuroflow', key: 'activeCommand' } as const, null)
const tabAtom = atom({ plugin: 'neuroflow', key: 'dashboardTab' } as const, 'phase')
const bandHiddenAtom = atom({ plugin: 'neuroflow', key: 'bandHidden' } as const, false)
const loopViewAtom = atom({ plugin: 'neuroflow', key: 'loopView' } as const, null)
const pickerNoteAtom = atom({ plugin: 'neuroflow', key: 'pickerNote' } as const, null)
const draftAtom = atom({ plugin: 'neuroflow', key: 'draftedDecision' } as const, null)

const DASHBOARD = 'nf-dashboard'
const PICKER = 'nf-phase'
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
export type BandItem = { level: 'alert' | 'warn' | 'info'; glyph: string; text: string }

export const when = (days: number): string => (days === 0 ? 'today' : days === 1 ? 'tomorrow' : `in ${days} days`)

/** What the band may show, most urgent first. Quiet mode keeps alerts and warnings only. */
export const bandItems = (snap: NfSnapshot, quiet: boolean): BandItem[] => {
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
  if (!quiet) {
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

/** The dashboard body for one tab, as plain lines (the text form every surface can show). */
export const tabLines = (tab: NfDashboardTab, snap: NfSnapshot, loop: NfLoopView | null): Line[] => {
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
  if (tab === 'tasks') {
    if (snap.taskCounts === null) return [{ text: 'No task board yet — /neuroflow:tasks', dim: true }]
    const counts = Object.entries(snap.taskCounts).map(([column, count]) => `${column} ${count}`).join(' · ')
    return [{ text: counts }, { text: 'Work the board with /neuroflow:tasks', dim: true }]
  }
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
  list: path => $.fs.list(path).then(entries => entries.map(entry => ({ name: entry.name, isDir: entry.kind === 'directory' })), () => []),
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
  const path = join(scope.root, '.neuroflow/project_config.md')
  const before = await io.read(path)
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

const selectTab = async ($: EngineInterface, tab: NfDashboardTab): Promise<void> => {
  await update($, tabAtom, () => tab)
  if (tab === 'loop') await loadLoopView($)
}

const openDashboard = async ($: EngineInterface, tab?: string): Promise<void> => {
  const wanted = TABS.find(item => item.id === tab)
  if (wanted !== undefined) await selectTab($, wanted.id)
  else if ((await read($, tabAtom)) === 'loop') await loadLoopView($)
  await $.ui.open({ id: DASHBOARD, title: 'neuroflow' })
}

const openPicker = async ($: EngineInterface): Promise<void> => {
  await update($, pickerNoteAtom, () => null)
  await $.ui.open({ id: PICKER, title: 'Switch phase', focus: true, closeOnEscape: true, rows: 12 })
}

const isPersonThere = async ($: EngineInterface): Promise<boolean> => (await $.session.surfaces()).length > 0

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

const TONE_COLOR: Record<Tone, 'error' | 'warning' | 'success' | 'suggestion' | 'subtle'> = {
  error: 'error',
  warning: 'warning',
  success: 'success',
  suggestion: 'suggestion',
  subtle: 'subtle',
}

export const registerViews = (on: On, opts: NfOptions): void => {
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

  // The band: one line of what needs attention; nothing when nothing does.
  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (opts.band === 'off' || e.props.hasSurvey) return next(e)
    const scope = await read($, scopeAtom)
    if (!scope?.isActive || scope.isHeadless) return next(e)
    if ((await read($, activeCommandAtom))?.lifecycle === 'quiet') return next(e)
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
    // Hidden for today: the press sets the state (redraw now) and the store (kept across sessions).
    const isHidden = (await read($, bandHiddenAtom)) || (await $.store.get(BAND_HIDDEN_ON)) === isoDate(await $.clock.now())
    if (isHidden) return next(e)
    const snap = await read($, snapshotAtom)
    if (snap === null) return next(e)
    const items = bandItems(snap, opts.band === 'quiet')
    if (items.length === 0) return next(e)
    const shown = items.slice(0, opts.band === 'quiet' ? 1 : 2)
    const more = items.length - shown.length
    const { Box, Button, Text } = $.ui.resolve(e)
    return (
      <Box flexDirection="row" flexWrap="wrap" columnGap={2}>
        {shown.map(item => (
          <Text color={item.level === 'alert' ? 'error' : item.level === 'warn' ? 'warning' : 'suggestion'} wrap="truncate-end">
            {item.glyph} {item.text}
          </Text>
        ))}
        {more > 0 ? <Text dimColor>+{more} more</Text> : null}
        <Button key="nf-band-dashboard" label="dashboard" hotkey="d" plain onPress={() => openDashboard($)} />
        <Button
          key="nf-band-hide"
          label="hide today"
          hotkey="x"
          plain
          onPress={async () => {
            await $.store.set(BAND_HIDDEN_ON, isoDate(await $.clock.now()))
            await update($, bandHiddenAtom, () => true)
          }}
        />
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
    const lines = tabLines(tab, snap, await read($, loopViewAtom))
    const title = `${snap.projectName ?? 'neuroflow project'} · ${snap.phase ?? 'no phase'}${snap.mode ? ` · ${snap.mode}` : ''}`
    return (
      <Box flexDirection="column" gap={1}>
        <Text bold wrap="truncate-end">{title}</Text>
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
