import type { On } from 'claude-code'
import { describe, expect, mock, test } from 'claude-code/testing'

import type { NfMeeting, NfSnapshot } from '../../../types'
import { setActivePhase } from '../lib/config'
import { nextPhase, phaseMap, pickerOrder } from '../lib/phases'
import {
  bandActions,
  bandItems,
  pickerOptions,
  cardLegend,
  cardRows,
  dashboardTitle,
  dateMark,
  dateRows,
  freezeCandidates,
  integrityRows,
  loopSummary,
  markRuns,
  moveQuestion,
  NOW_START,
  nowRingKeys,
  nowRows,
  nowSummary,
  parseOpenQuestions,
  parseRunning,
  runQuestion,
  sparkline,
  tabLines,
} from '../features/views'
import { VIEW_KEYS, lineNeighbour } from '../lib/keys'
import { answerAsks } from './ask'
import type { Asked } from './ask'
import { buttons, elements, hotkeys, keyProblems, lines } from './drawn'
import { fakeFs } from './fakefs'

const snapshot = (over: Partial<NfSnapshot> = {}): NfSnapshot => ({
  root: '/work/proj',
  nfSchema: 1,
  dialect: 'frontmatter',
  pluginVersion: '0.2.22',
  runningVersion: '0.2.22',
  projectName: 'Oddball',
  phase: 'data-analyze',
  mode: 'critic',
  recommendedPhases: ['ideation', 'preregistration', 'data', 'data-analyze', 'paper'],
  rawRoots: [],
  paperAuto: false,
  ethics: null,
  prereg: null,
  deadlines: [],
  phasesVisited: ['ideation', 'preregistration', 'data', 'data-analyze'],
  loops: [],
  meetings: [],
  wellbeingDue: false,
  ethicsNotApplicable: false,
  flowieProfiles: [],
  wikiCapture: null,
  wikiPending: 0,
  problems: [],
  loadedAt: 0,
  ...over,
})

describe('band items', () => {
  test('alerts first; quiet keeps only alerts and warnings', () => {
    const snap = snapshot({
      deadlines: [
        { date: '2026-10-08', what: 'Abstract', gates: 'paper', daysLeft: 1 },
        { date: '2026-10-19', what: 'ethics approval expires', gates: null, daysLeft: 12 },
        { date: '2026-10-20', what: 'Lab retreat', gates: null, daysLeft: 13 },
      ],
      prereg: { status: 'frozen', setBy: 'model', setAt: null, frozenAt: null, files: {}, plannedN: null },
    })
    const quiet = bandItems(snap, true)
    expect(quiet.map(item => item.level)).toEqual(['alert', 'warn', 'warn'])
    expect(quiet[0].text).toBe('Abstract — tomorrow')
    const normal = bandItems(snap, false)
    expect(normal.some(item => item.text === 'next phase: paper')).toBe(true)
    expect(normal.some(item => item.text.startsWith('Lab retreat'))).toBe(true)
  })

  test('nothing to say means no band', () => {
    expect(bandItems(snapshot(), true)).toEqual([])
  })

  test('after a plugin update the band names /neuroflow:migrate until the project is migrated', () => {
    const items = bandItems(snapshot({ pluginVersion: '0.2.9', runningVersion: '0.2.10' }), true)
    // The same sentence the prose says (neuroflow-core → Command lifecycle, version notice).
    expect(items.map(item => item.text)).toEqual(['neuroflow 0.2.10 is installed; this project is on 0.2.9 — run /neuroflow:migrate to bring the project, your flowie and the team hive up to date'])
    expect(items[0].actions?.map(action => [action.command, action.args, action.hotkey])).toEqual([['neuroflow:migrate', '', 'm']])
    expect(bandItems(snapshot({ pluginVersion: null }), true)[0].text).toContain('this project is on an older version')
    expect(bandItems(snapshot({ pluginVersion: '0.2.23' }), false).some(item => item.text.includes('is installed'))).toBe(false)
    expect(bandItems(snapshot({ runningVersion: null, pluginVersion: '0.2.1' }), false).some(item => item.text.includes('is installed'))).toBe(false)
  })

  test('the version notice waits behind the meetings: one within two hours keeps the quiet seat and its keys', () => {
    const now = new Date(2026, 9, 7, 13, 0).getTime()
    const soon: NfMeeting = { level: 'project', slug: 'lab-2026-10-07', title: 'Lab meeting', date: '2026-10-07T14:00:00', startsIn: 60, closed: false, openActions: 0 }
    const open: NfMeeting = { level: 'project', slug: 'pi-2026-10-06', title: 'PI check-in', date: '2026-10-06T10:00:00', startsIn: -27 * 60, closed: false, openActions: 2 }
    const quiet = bandItems(snapshot({ pluginVersion: '0.2.21', meetings: [open, soon], loadedAt: now }), true)
    expect(quiet.map(item => item.text)).toEqual([
      'meeting "Lab meeting" in 60 min',
      'meeting "PI check-in" not closed — 2 open action item(s)',
      'neuroflow 0.2.22 is installed; this project is on 0.2.21 — run /neuroflow:migrate to bring the project, your flowie and the team hive up to date',
    ])
    // The quiet band shows the first item and its keys only.
    expect(quiet[0].actions?.map(action => action.key)).toEqual(['nf-meet-prepare', 'nf-meet-notes'])
    // A meeting later in the day is information: the notice takes the seat again.
    const later = bandItems(snapshot({ pluginVersion: '0.2.21', meetings: [{ ...soon, startsIn: 180 }], loadedAt: now }), true)
    expect(later.map(item => item.actions?.[0]?.key)).toEqual(['nf-migrate'])
  })

  test('the migrate key comes with the version notice wherever the band shows it', () => {
    const now = new Date(2026, 9, 7, 13, 0).getTime()
    const soon: NfMeeting = { level: 'project', slug: 'lab-2026-10-07', title: 'Lab meeting', date: '2026-10-07T14:00:00', startsIn: 60, closed: false, openActions: 0 }
    const items = bandItems(snapshot({ pluginVersion: '0.2.21', meetings: [soon], loadedAt: now }), false)
    // Second in a normal band: the meeting's keys first, then m.
    expect(bandActions(items.slice(0, 2)).map(action => `${action.key} ${action.hotkey}`)).toEqual(['nf-meet-prepare p', 'nf-meet-notes o', 'nf-migrate m'])
    // Not shown (the quiet band's one seat is the meeting's): no m.
    expect(bandActions(items.slice(0, 1)).map(action => action.key)).toEqual(['nf-meet-prepare', 'nf-meet-notes'])
    // Other items' keys still come only with the first item.
    const wiki = bandItems(snapshot({ wikiPending: 2, deadlines: [{ date: '2026-10-08', what: 'Abstract', gates: null, daysLeft: 1 }] }), false)
    expect(bandActions(wiki.slice(0, 2))).toEqual([])
  })
})

describe('loop parsing', () => {
  test('reads the Running column and open questions', () => {
    const results = '| # | Verdict | Δ | Running | Decision |\n|---|---|---|---|---|\n| 000 | — | 0 | 0 | KEPT |\n| 001 | BETTER | +3 | 3 | KEPT |\n| 002 | WORSE | -1 | 3 | REVERTED |\n| 003 | BETTER | +2 | 5 | KEPT |\n'
    expect(parseRunning(results)).toEqual([0, 3, 3, 5])
    expect(sparkline([0, 3, 3, 5])).toBe('▁▅▅█')
    const report = '# Report\n\n## Open questions for you\n- **Q7** — delete the third control? (iter 46)\n- **Q3** — eLife or Nature Neuro?\n\n## This round\n- not a question\n'
    expect(parseOpenQuestions(report)).toEqual(['Q7 — delete the third control? (iter 46)', 'Q3 — eLife or Nature Neuro?'])
  })
})

describe('dashboard lines', () => {
  test('every tab has a text form', () => {
    const snap = snapshot({
      ethics: { status: 'approved', setBy: 'person', setAt: null, approvalId: null, expires: '2027-06-30', aiProcessing: 'pseudonymised' },
    })
    expect(tabLines('phase', snap, null)[0].text).toBe('● ideation  ● preregistration  ● data  ◉ data-analyze  → paper')
    expect(tabLines('phase', snap, null).map(line => line.text).slice(-1)).toEqual(['◉ current  ● visited  → recommended next'])
    expect(tabLines('integrity', snap, null)[0].text).toBe('✔ ethics approved · expires 2027-06-30')
    // The tasks tab reads every level's board when it opens; until then it says so.
    expect(tabLines('tasks', snap, null)[0]).toEqual({ text: 'Reading the task boards…', dim: true })
    expect(tabLines('deadlines', snap, null)[0].dim).toBe(true)
    expect(tabLines('loop', snap, null)[0].text).toBe('No autoresearch loops.')
    expect(tabLines('now', snap, null)).toEqual([{ text: '→ next phase: paper', tone: undefined }])
  })

  test('the now tab lists every band item, whatever the quiet setting, each with its action and no letter', () => {
    const now = new Date(2026, 9, 7, 13, 0).getTime()
    const soon: NfMeeting = { level: 'project', slug: 'lab-2026-10-07', title: 'Lab meeting', date: '2026-10-07T14:00:00', startsIn: 60, closed: false, openActions: 0 }
    const snap = snapshot({ pluginVersion: '0.2.21', meetings: [soon], wikiPending: 2, wellbeingDue: true, loadedAt: now, deadlines: [{ date: '2026-10-08', what: 'Abstract', gates: 'paper', daysLeft: 1 }] })
    const draft = { path: '/work/proj/.neuroflow/reasoning/data-analyze.jsonl', phase: 'data-analyze', command: 'data-analyze', statement: 'Use FDR', reasoning: 'r', at: now }
    const rows = nowRows(snap, { pending: ['wellbeing: 2026-10-07'], failure: null, isHeld: false }, { draft, drive: null, capture: null })
    expect(rows.map(row => `${row.glyph} ${row.text} | ${row.actions.map(action => `${action.key} ${action.label}`).join(', ')}`)).toEqual([
      '✎ decision drafted for data-analyze: Use FDR | nf-now-draft-keep keep, nf-now-draft-drop drop',
      '⚠ Abstract — tomorrow | ',
      '▸ meeting "Lab meeting" in 60 min | nf-now-meet-prepare prepare, nf-now-meet-notes notes',
      '↻ flowie sync pending (wellbeing: 2026-10-07) — it runs before your next neuroflow command or when a turn ends, or /neuroflow:flowie --sync | nf-now-flowie-sync sync',
      '✎ 2 wiki cards waiting for review | nf-now-wiki-review review',
      '→ next phase: paper | ',
      '· wellbeing check-in due — the band asks for it, or /neuroflow:flowie --assess | ',
    ])
    // The version notice is the pane's Update line, above every tab: not a row, but the first stop of j and k, above
    // the tab's own name, where they start.
    expect(rows.some(row => row.text.includes('is installed'))).toBe(false)
    const ring = nowRingKeys(rows, true)
    expect(ring.slice(0, 4)).toEqual(['nf-dash-migrate', NOW_START, 'nf-now-draft-keep', 'nf-now-draft-drop'])
    expect(rows.find(row => row.actions.some(action => action.key === 'nf-now-meet-prepare'))?.actions[0]?.act).toEqual({ kind: 'command', command: 'neuroflow:meeting', args: '--prepare lab-2026-10-07' })
    // From no ring (and from any element that is not a stop) j and k land on the tab's name, never on an action: a
    // typed `ok` leaves the ring where Enter only reads the tab again.
    for (const at of [null, 'nf-tab-phase', 'nf-dash-reread']) {
      expect(lineNeighbour(ring, at, 1, NOW_START), String(at)).toBe(NOW_START)
      expect(lineNeighbour(ring, at, -1, NOW_START), String(at)).toBe(NOW_START)
    }
    // From there a second j reaches the first action, and k the Update line's migrate above it.
    expect(lineNeighbour(ring, NOW_START, 1, NOW_START)).toBe('nf-now-draft-keep')
    expect(lineNeighbour(ring, NOW_START, -1, NOW_START)).toBe('nf-dash-migrate')
    // Nothing to reach, nothing to walk: no j and k.
    expect(nowRingKeys([{ level: 'info', glyph: '→', text: 'next phase: paper', actions: [] }], false)).toEqual([])
  })

  test('every action from a pane asks first: a move names its command, a key\'s command says it starts a model turn', () => {
    expect(runQuestion('neuroflow:meeting', '--prepare lab-2026-10-07')).toBe('Run /neuroflow:meeting --prepare lab-2026-10-07 now? It starts a model turn.')
    expect(runQuestion('neuroflow:migrate', '')).toBe('Run /neuroflow:migrate now? It starts a model turn.')
    expect(moveQuestion({ kind: 'project', name: 'project' }, 'rerun-ica', 'Rerun ICA', 'review')).toBe('Move "Rerun ICA" to review? /neuroflow:tasks --move rerun-ica review runs now.')
    expect(moveQuestion({ kind: 'flowie', name: 'flowie' }, 'check-stats', 'Check stats', 'done')).toBe('Move "Check stats" to done? /neuroflow:tasks --level flowie --move check-stats done runs now and syncs your flowie.')
  })
})

describe('the dashboard\'s rows', () => {
  test('title, dates, integrity: a glyph, a word and who set it with every state', () => {
    const snap = snapshot({
      deadlines: [
        { date: '2026-10-08', what: 'Abstract', gates: 'paper', daysLeft: 1 },
        { date: '2026-10-19', what: 'ethics approval expires', gates: null, daysLeft: 12 },
        { date: '2026-12-01', what: 'Lab retreat', gates: null, daysLeft: 55 },
      ],
      ethics: { status: 'approved', setBy: 'model', setAt: null, approvalId: null, expires: '2027-06-30', aiProcessing: 'pseudonymised' },
      prereg: { status: 'frozen', setBy: 'person', setAt: null, frozenAt: '2026-10-01T10:00', files: { 'a.md': 'x', 'b.md': 'y' }, plannedN: 24 },
      rawRoots: ['sourcedata/'],
    })
    expect(dashboardTitle(snap)).toBe('Oddball · data-analyze · critic')
    expect([dateMark(0), dateMark(3), dateMark(4), dateMark(14), dateMark(15)].map(mark => `${mark.glyph}${mark.rank}`)).toEqual(['⚠0', '⚠0', '▸1', '▸1', '·2'])
    expect(dateRows(snap).map(row => `${row.glyph} ${row.date} ${row.what} | ${row.when} | ${row.gates ?? ''}`)).toEqual([
      '⚠ 2026-10-08 Abstract | tomorrow | paper',
      '▸ 2026-10-19 ethics approval expires | in 12 days | ',
      '· 2026-12-01 Lab retreat | in 55 days | ',
    ])
    expect(integrityRows(snap).map(row => [row.glyph, row.name, row.value, row.note, row.more.join('; ')])).toEqual([
      // Approved, but not by a person: `?` and the words (commands/dashboard.md → Integrity).
      ['?', 'ethics', 'approved · expires 2027-06-30', 'not set by a person', 'model may read: pseudonymised'],
      ['■', 'preregistration', 'frozen 2026-10-01 · 2 files', 'set by a person', 'planned N: 24'],
      ['■', 'raw data', 'read-only: sourcedata/', null, ''],
    ])
    const none = integrityRows(snapshot({ ethicsNotApplicable: true }))
    expect(none.map(row => `${row.glyph} ${row.name}: ${row.value}`)).toEqual([
      '· ethics: not applicable: no participant data',
      '· preregistration: none frozen',
      '· raw data: no folders declared (raw_roots)',
    ])
    expect(integrityRows(snapshot({ ethics: { status: 'expired', setBy: 'person', setAt: null, approvalId: null, expires: null, aiProcessing: null } }))[0]).toMatchObject({ glyph: '⚠', tone: 'error' })
  })

  test('the ruler\'s marks keep their colours; the loop and the now tab\'s summary read as one line each', () => {
    expect(markRuns('       ⚠   ▸ ·')).toEqual([
      { text: '       ' },
      { text: '⚠', tone: 'error' },
      { text: '   ' },
      { text: '▸', tone: 'warning' },
      { text: ' ' },
      { text: '·', dim: true },
    ])
    const loop = { phase: 'data-analyze', name: 'connectivity', location: 'loops/connectivity/', iterations: '23', best: 'v019', status: 'running' }
    const view = { name: 'connectivity', phase: 'data-analyze', status: 'running', iterations: '23', best: 'v019', running: [0, 3, 3, 5], questions: [] }
    expect(loopSummary(loop, view)).toBe('connectivity · running · iteration 23 · best v019  ▁▅▅█')
    expect(loopSummary(loop, null)).toBe('connectivity · running · iteration 23 · best v019')
    const summary = nowSummary(snapshot({ loops: [loop] }), null, view)
    expect(summary.map(row => `${row.label} ${row.value}`)).toEqual([
      'PHASE ● ideation ─ ● prereg ─ ● data ─ ◉ analyze ─ → paper',
      'TASKS reading the task boards…',
      'LOOP connectivity · running · iteration 23 · best v019  ▁▅▅█',
    ])
    expect(nowSummary(snapshot(), null, null).map(row => row.label)).toEqual(['PHASE', 'TASKS'])
  })

  test('the tasks tab\'s cards in columns, and what their marks mean', () => {
    const card = (slug: string, over: Record<string, unknown> = {}) => ({ slug, title: slug, owner: null, due: null, overdue: false, project: null, isMine: false, ...over })
    const level = (id: string, kind: 'project' | 'flowie' | 'hive', cards: ReturnType<typeof card>[], project: string | null = null) => ({
      id, kind, name: id, project, open: cards.length, mine: cards.filter(item => item.isMine).length, top: cards,
      board: { columns: [], openColumns: [], done: 0, archived: 0 },
    })
    const view = {
      levels: [
        level('project', 'project', [card('rerun-ica', { title: 'Rerun ICA', owner: 'jana', due: '2026-10-01', overdue: true, isMine: true })]),
        level('flowie', 'flowie', [card('read', { title: 'Read the review', due: '2026-10-20', isMine: true, web: true })], 'Oddball EEG'),
      ],
    } as never
    expect(cardRows(view).map(row => [row.marks, row.title, row.owner, row.due, row.level])).toEqual([
      ['⚠', 'Rerun ICA', '@jana', 'due 10-01', 'project'],
      ['◆ ↻', 'Read the review', '', 'due 10-20', 'flowie'],
    ])
    expect(cardLegend(view)).toEqual(['◆ this project (Oddball EEG)', '⚠ overdue', '↻ a workbench change waits'])
  })
})

describe('phases', () => {
  test('picker puts current, then recommended, then the rest', () => {
    const order = pickerOrder('data', ['ideation', 'data', 'paper']).map(phase => phase.id)
    expect(order.slice(0, 3)).toEqual(['data', 'ideation', 'paper'])
    expect(order.length).toBe(19)
    expect(nextPhase('data', ['ideation', 'data', 'paper'])).toBe('paper')
    expect(phaseMap(null, [], [])).toBe('')
  })

  test('the picker\'s options: the phase by its name first, then the legend\'s glyph and the state in words, in one column', () => {
    const options = pickerOptions('data', ['ideation', 'data'], ['ideation', 'data', 'paper', 'output'])
    const words = options.slice(0, 5).map(option => [option.label.replace(/ {2,}/, ' | '), option.short])
    expect(words).toEqual([
      ['data — acquisition & BIDS | ◉ current', 'data · ◉ current'],
      ['ideation — question & literature | ● visited', 'ideation · ● visited'],
      ['paper — manuscript | → next', 'paper · → next'],
      ['output — export & archive | → recommended', 'output · → recommended'],
      ['preregistration — hypotheses & plan | ○ not started', 'preregistration · ○ not started'],
    ])
    // The marks start in one column: after the longest label (preregistration's) and two spaces.
    expect(new Set(options.map(option => option.label.search(/ {2}[◉●→○] /)))).toEqual(new Set([35]))
  })

  test('setActivePhase edits only the one line', () => {
    const fm = '---\nnf_schema: 1\nactive_phase: data   # canonical\nproject_name: X\n---\n# Notes\n'
    expect(setActivePhase(fm, 'paper')).toBe('---\nnf_schema: 1\nactive_phase: paper   # canonical\nproject_name: X\n---\n# Notes\n')
    expect(setActivePhase('---\nnf_schema: 1\n---\nbody\n', 'paper')).toBe('---\nnf_schema: 1\nactive_phase: paper\n---\nbody\n')
    expect(setActivePhase('# Project config\nactive_phase: setup\n', 'ideation')).toBe('# Project config\nactive_phase: ideation\n')
    expect(setActivePhase('**Phase:** data\n', 'paper')).toBe(null)
    expect(setActivePhase('---\r\nactive_phase: a\r\n---\r\n', 'b')).toBe('---\r\nactive_phase: b\r\n---\r\n')
  })
})

describe('engine', () => {
  test('the band draws the most urgent item on terminal and desktop', { options: { runtime: 'observe', band: 'quiet' } }, async ($, on) => {
    const project = '/work/proj'
    fakeFs(on, {
      [`${project}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nproject_name: Oddball\nactive_phase: data\n---\n',
      [`${project}/.neuroflow/timeline.md`]: '| Date | What | Gates |\n|---|---|---|\n| 2026-10-08 | Abstract deadline | paper |\n',
    }, project)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: new Date(2026, 9, 7, 9, 0).getTime() })
    mock.store(on)
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    await $.session.start({ cwd: project, surface: 'terminal', isInteractive: true })
    for (const surface of ['terminal', 'desktop'] as const) {
      const ui = await $.ui.mount({
        plugin: 'neuroflow',
        surface,
        component: 'AbovePrompt',
        props: { hasSurvey: false, isWorking: false, maxRows: 4, bodyColumns: 100, scroll: { offset: 0, bodyRows: 4 }, view: {} },
      } as never)
      const text = JSON.stringify(await ui.drawn())
      expect(text).toContain('Abstract deadline — tomorrow')
      await ui.unmount()
    }
  })

  test('the version notice stays in the band; its key runs /neuroflow:migrate', { options: { runtime: 'observe', band: 'quiet' } }, async ($, on) => {
    const project = '/work/proj'
    fakeFs(on, {
      [`${project}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nproject_name: Oddball\nactive_phase: data\nplugin_version: 0.2.21\n---\n',
      // Not named "neuroflow": the pattern also matches the project, which would then read as the plugin's own repo.
      '*/.claude-plugin/plugin.json': '{"name": "neuroflow-fixture", "version": "0.2.22"}',
    }, project)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: new Date(2026, 9, 7, 9, 0).getTime() })
    mock.store(on)
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    const ran: string[] = []
    on('command.run', ($, e) => {
      ran.push(e.command)
      return { text: '' }
    })
    await $.session.start({ cwd: project, surface: 'terminal', isInteractive: true })
    const ui = await $.ui.mount({
      plugin: 'neuroflow',
      surface: 'terminal',
      component: 'AbovePrompt',
      props: { hasSurvey: false, isWorking: false, maxRows: 4, bodyColumns: 120, scroll: { offset: 0, bodyRows: 4 }, view: {} },
    } as never)
    expect(JSON.stringify(await ui.drawn())).toContain('neuroflow 0.2.22 is installed; this project is on 0.2.21 — run /neuroflow:migrate')
    await ui.press({ key: 'nf-migrate' })
    expect(ran).toEqual(['neuroflow:migrate'])
    await ui.unmount()
  })

  test('a meeting within two hours keeps the quiet band and its keys; the version notice waits', { options: { runtime: 'observe', band: 'quiet' } }, async ($, on) => {
    const project = '/work/proj'
    fakeFs(on, {
      [`${project}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nproject_name: Oddball\nactive_phase: data\nplugin_version: 0.2.21\n---\n',
      [`${project}/.neuroflow/meetings/lab-2026-10-07.md`]: '---\ntitle: Lab meeting\ndate: 2026-10-07T10:00\n---\n',
      '*/.claude-plugin/plugin.json': '{"name": "neuroflow-fixture", "version": "0.2.22"}',
    }, project)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: new Date(2026, 9, 7, 9, 0).getTime() })
    mock.store(on)
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    const ran: string[] = []
    on('command.run', ($, e) => {
      ran.push(`${e.command} ${e.args}`)
      return { text: '' }
    })
    await $.session.start({ cwd: project, surface: 'terminal', isInteractive: true })
    const ui = await $.ui.mount({
      plugin: 'neuroflow',
      surface: 'terminal',
      component: 'AbovePrompt',
      props: { hasSurvey: false, isWorking: false, maxRows: 4, bodyColumns: 120, scroll: { offset: 0, bodyRows: 4 }, view: {} },
    } as never)
    const drawn = JSON.stringify(await ui.drawn())
    expect(drawn).toContain('Lab meeting')
    expect(drawn).toContain('in 60 min')
    expect(drawn).not.toContain('is installed')
    await ui.press({ key: 'nf-meet-prepare' })
    expect(ran).toEqual(['neuroflow:meeting --prepare lab-2026-10-07'])
    await ui.unmount()
  })

  test('a normal band showing the version notice second still offers m', { options: { runtime: 'observe', band: 'normal' } }, async ($, on) => {
    const project = '/work/proj'
    fakeFs(on, {
      [`${project}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nproject_name: Oddball\nactive_phase: data\nplugin_version: 0.2.21\n---\n',
      [`${project}/.neuroflow/timeline.md`]: '| Date | What | Gates |\n|---|---|---|\n| 2026-10-08 | Abstract deadline | paper |\n',
      '*/.claude-plugin/plugin.json': '{"name": "neuroflow-fixture", "version": "0.2.22"}',
    }, project)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: new Date(2026, 9, 7, 9, 0).getTime() })
    mock.store(on)
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    const ran: string[] = []
    on('command.run', ($, e) => {
      ran.push(e.command)
      return { text: '' }
    })
    await $.session.start({ cwd: project, surface: 'terminal', isInteractive: true })
    const ui = await $.ui.mount({
      plugin: 'neuroflow',
      surface: 'terminal',
      component: 'AbovePrompt',
      props: { hasSurvey: false, isWorking: false, maxRows: 4, bodyColumns: 160, scroll: { offset: 0, bodyRows: 4 }, view: {} },
    } as never)
    const drawn = JSON.stringify(await ui.drawn())
    expect(drawn).toContain('Abstract deadline — tomorrow')
    expect(drawn).toContain('this project is on 0.2.21')
    await ui.press({ key: 'nf-migrate' })
    expect(ran).toEqual(['neuroflow:migrate'])
    await ui.unmount()
  })

  test('folders the engine lists (kind "dir") are phases visited on the dashboard', { options: { runtime: 'observe' } }, async ($, on) => {
    const project = '/work/proj'
    fakeFs(on, {
      [`${project}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nproject_name: Oddball\nactive_phase: data\n---\n',
      [`${project}/.neuroflow/ideation/flow.md`]: '# ideation\n',
      [`${project}/.neuroflow/preregistration/flow.md`]: '# preregistration\n',
    }, project)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: new Date(2026, 9, 7, 9, 0).getTime() })
    mock.store(on)
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('ui.open', () => ({ value: { isPlaced: true } }))
    on('ui.status', () => ({ value: undefined }))
    await $.session.start({ cwd: project, surface: 'terminal', isInteractive: true })
    await $.command.run({ command: 'neuroflow:dashboard', args: 'phase' } as never)
    const ui = await $.ui.mount({
      plugin: 'neuroflow',
      surface: 'terminal',
      component: 'Pane',
      requestId: 'nf-dashboard',
      props: { title: 'neuroflow', isFocused: true, bodyColumns: 120, placement: 'inline', scroll: { offset: 0, bodyRows: 16 }, view: {} },
    } as never)
    // The phase tab unrolls the ring: a flow line, travelled (heavy) up to the current phase, a name under each glyph.
    const flow = lines(await ui.drawn())
    expect(flow).toContain(`●${'━'.repeat(39)}●${'━'.repeat(39)}◉`)
    expect(flow.some(line => /^ideation +prereg +data$/.test(line))).toBe(true)
    expect(flow).toContain('◉ current  ● visited')
    await ui.unmount()
  })

  test('the dashboard pane carries the Update line and a migrate key, like the prose dashboard', { options: { runtime: 'observe' } }, async ($, on) => {
    const project = '/work/proj'
    fakeFs(on, {
      [`${project}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nproject_name: Oddball\nactive_phase: data\nplugin_version: 0.2.21\n---\n',
      '*/.claude-plugin/plugin.json': '{"name": "neuroflow-fixture", "version": "0.2.22"}',
    }, project)
    mock.env(on, { HOME: '/home/me' })
    const clock = mock.clock(on, { now: new Date(2026, 9, 7, 9, 0).getTime() })
    mock.store(on)
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('ui.open', () => ({ value: undefined }))
    on('ui.toast', () => ({ value: undefined }))
    on('ui.status', () => ({ value: undefined }))
    const ran: string[] = []
    on('command.run', ($, e) => {
      ran.push(e.command)
      return { text: '' }
    })
    const dialog = answerAsks(on)
    await $.session.start({ cwd: project, surface: 'terminal', isInteractive: true })
    await $.command.run({ command: 'neuroflow:dashboard', args: '' })
    const ui = await $.ui.mount({
      plugin: 'neuroflow',
      surface: 'terminal',
      component: 'Pane',
      requestId: 'nf-dashboard',
      props: { title: 'neuroflow', isFocused: true, bodyColumns: 120, placement: 'inline', scroll: { offset: 0, bodyRows: 16 }, view: {} },
    } as never)
    expect(JSON.stringify(await ui.drawn())).toContain('↑ neuroflow 0.2.22 is installed; this project is on 0.2.21 — run /neuroflow:migrate')
    // An Enter typed through the open does not migrate, nor asks. The migrate key has no letter.
    await ui.press({ key: 'nf-dash-migrate' })
    expect(ran).toEqual([])
    expect(dialog.asked).toEqual([])
    expect(buttons(await ui.drawn()).find(button => button.key === 'nf-dash-migrate')?.hotkey).toBe(undefined)
    // One after it asks first, the safe answer on top: a stray Enter in the dialog migrates nothing.
    await clock.advance(500)
    await ui.press({ key: 'nf-dash-migrate' })
    expect(dialog.asked).toEqual([{ question: 'Run /neuroflow:migrate now? It starts a model turn.', options: ['Not now', 'Run it'], header: 'neuroflow' }])
    expect(ran).toEqual([])
    // The person's yes runs it.
    dialog.answer(() => 'Run it')
    await clock.advance(500)
    await ui.press({ key: 'nf-dash-migrate' })
    expect(ran).toContain('neuroflow:migrate')
    await ui.unmount()
  })
})

describe('keyboard first', () => {
  const project = '/work/proj'
  const FILES = {
    [`${project}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nproject_name: Oddball\nactive_phase: data\nplugin_version: 0.2.21\nrecommended_phases: [data, data-analyze, paper]\n---\n',
    // Not named "neuroflow": the pattern also matches the project, which would then read as the plugin's own repo.
    '*/.claude-plugin/plugin.json': '{"name": "neuroflow-fixture", "version": "0.2.22"}',
    [`${project}/.neuroflow/meetings/lab-2026-10-07.md`]: '---\ntitle: Lab meeting\ndate: 2026-10-07T14:00\n---\n',
    [`${project}/.neuroflow/tasks/active/rerun-ica.md`]: '---\ntitle: Rerun ICA\nstatus: active\n---\n',
  }
  type Seen = { opens: Record<string, unknown>[]; closes: string[]; ran: string[]; store: Map<string, unknown>; clock: ReturnType<typeof mock.clock>; dialog: ReturnType<typeof answerAsks> }
  const setUp = (on: On, stored: Record<string, unknown> = {}): Seen => {
    fakeFs(on, FILES, project)
    mock.env(on, { HOME: '/home/me' })
    const seen: Seen = {
      opens: [], closes: [], ran: [], store: new Map(Object.entries(stored)), clock: mock.clock(on, { now: new Date(2026, 9, 7, 13, 0).getTime() }),
      // Every question is answered as a stray Enter would answer it, unless the test answers otherwise.
      dialog: answerAsks(on),
    }
    on('store.get', ($, e) => ({ value: seen.store.get(e.key) }))
    on('store.set', ($, e) => {
      seen.store.set(e.key, e.value)
      return { value: undefined }
    })
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('ui.open', ($, e) => {
      seen.opens.push({ ...e })
      return { value: { isPlaced: true } }
    })
    on('ui.close', ($, e) => {
      seen.closes.push(e.id)
      return { value: undefined }
    })
    on('ui.status', () => ({ value: undefined }))
    on('ui.toast', () => ({ value: undefined }))
    on('ui.focus', () => ({}))
    on('command.run', ($, e) => {
      seen.ran.push(`${e.command} ${e.args}`.trim())
      return { text: '', ref: 1 }
    })
    return seen
  }
  const pane = (requestId: string, isFocused = true, surface = 'terminal') => ({
    plugin: 'neuroflow', surface, component: 'Pane', requestId,
    props: { title: requestId, isFocused, bodyColumns: 116, placement: 'inline', scroll: { offset: 0, bodyRows: 18 }, view: {} },
  })
  const band = (bodyColumns: number, surface = 'terminal', rows?: number) => ({
    plugin: 'neuroflow', surface, component: 'AbovePrompt',
    props: { hasSurvey: false, isWorking: false, maxRows: 4, bodyColumns, scroll: { offset: 0, bodyRows: 4 }, view: {} },
    ...(rows === undefined ? {} : { viewport: { columns: bodyColumns + 5, rows } }),
  })

  test('every view a command opens asks for the keys and for its rows; running the command again asks again', { options: { runtime: 'observe' } }, async ($, on) => {
    const seen = setUp(on)
    await $.session.start({ cwd: project, surface: 'terminal', isInteractive: true })
    // A drawing measured a tall terminal: each view asks for its full height.
    await (await $.ui.mount(band(116, 'terminal', 40) as never)).unmount()
    await $.command.run({ command: 'neuroflow:dashboard', args: '' })
    await $.command.run({ command: 'neuroflow:dashboard', args: 'phase' })
    await $.command.run({ command: 'neuroflow:tasks', args: '' })
    await $.command.run({ command: 'neuroflow:phase', args: '' })
    expect(seen.opens.map(open => [open.id, open.focus, open.rows])).toEqual([
      ['nf-dashboard', true, 18],
      ['nf-dashboard', true, 18],
      ['nf-board', true, 16],
      ['nf-phase', true, 12],
    ])
    // Esc gives the keys back and leaves a pane open; only the picker, a dialog, closes on Esc — and has no q.
    expect(seen.opens.map(open => open.closeOnEscape)).toEqual([undefined, undefined, undefined, true])
    expect(Object.entries(VIEW_KEYS).filter(([, keys]) => keys.q === 'close').map(([view]) => view)).toEqual(['dashboard', 'board', 'wiki', 'xray', 'paper'])
    // Docked beside a fullscreen transcript, each view asks for its width too.
    expect(seen.opens.map(open => open.columns)).toEqual([64, 64, 84, 56])
    // 24 rows over SSH: the compact height, so the transcript keeps room.
    await (await $.ui.mount(band(75, 'terminal', 24) as never)).unmount()
    await $.command.run({ command: 'neuroflow:dashboard', args: '' })
    await $.command.run({ command: 'neuroflow:tasks', args: '' })
    expect(seen.opens.slice(4).map(open => [open.id, open.rows])).toEqual([['nf-dashboard', 10], ['nf-board', 10]])
  })

  test('the dashboard opens on now; keys typed through the open do nothing, and a now row acts only on Enter and a yes', { options: { runtime: 'observe' } }, async ($, on) => {
    const seen = setUp(on)
    await $.session.start({ cwd: project, surface: 'terminal', isInteractive: true })
    const opened = await $.command.run({ command: 'neuroflow:dashboard', args: '' })
    expect(opened.text).toBe('Dashboard open — 1–6 tabs, h/l previous/next, r reread, q close, Esc back to the prompt.')
    const ui = await $.ui.mount(pane('nf-dashboard') as never)
    const now = await ui.drawn()
    // The shown tab is a key with no letter, at full strength: where j and k start.
    expect(buttons(now).find(button => button.key === 'nf-tab-now')).toEqual({ key: 'nf-tab-now', label: '1: now', plain: true })
    expect(lines(now)).toContain('▸ meeting "Lab meeting" in 60 min')
    expect(keyProblems(now, 'dashboard')).toEqual([])
    // Writing and consenting actions have no letter there: Enter on the row, never a bare key.
    for (const key of ['nf-now-meet-prepare', 'nf-now-meet-notes', 'nf-dash-migrate']) expect(buttons(now).find(button => button.key === key)?.hotkey, key).toBe(undefined)
    expect(hotkeys(now)).toEqual(['2', '3', '4', '5', '6', 'h', 'l', 'j', 'k', 'r', 'q'])
    await ui.press({ key: 'nf-now-meet-prepare' })
    await seen.clock.advance(100)
    await ui.press({ key: 'nf-now-meet-prepare' })
    expect(seen.ran).toEqual([])
    expect(seen.dialog.asked).toEqual([])
    // Past the open and the last key: it asks, the safe answer first, and a stray Enter there runs nothing.
    await seen.clock.advance(400)
    await ui.press({ key: 'nf-now-meet-prepare' })
    expect(seen.dialog.asked.map(asked => [asked.question, asked.options])).toEqual([['Run /neuroflow:meeting --prepare lab-2026-10-07 now? It starts a model turn.', ['Not now', 'Run it']]])
    expect(seen.ran).toEqual([])
    seen.dialog.answer(() => 'Run it')
    await seen.clock.advance(500)
    await ui.press({ key: 'nf-now-meet-prepare' })
    expect(seen.ran).toEqual(['neuroflow:meeting --prepare lab-2026-10-07'])
    // Digits pick a tab, h and l step through them, wrapping.
    await ui.press({ key: 'nf-tab-phase' })
    expect(JSON.stringify(await ui.drawn())).toContain('2: phase')
    await ui.press({ key: 'nf-nav-right' })
    expect(JSON.stringify(await ui.drawn())).toContain('3: deadlines')
    await ui.press({ key: 'nf-nav-left' })
    await ui.press({ key: 'nf-nav-left' })
    await ui.press({ key: 'nf-nav-left' })
    expect(JSON.stringify(await ui.drawn())).toContain('6: loop')
    // j and k exist only where there are rows to walk.
    expect(hotkeys(await ui.drawn())).not.toContain('j')
    await ui.press({ key: 'nf-dash-close' })
    expect(seen.closes).toEqual(['nf-dashboard'])
    await ui.unmount()
  })

  test('from the dashboard, b and g hand the keys over: the dashboard closes, the boards or the picker open holding them', { options: { runtime: 'observe' } }, async ($, on) => {
    const seen = setUp(on)
    await $.session.start({ cwd: project, surface: 'terminal', isInteractive: true })
    await $.command.run({ command: 'neuroflow:dashboard', args: 'tasks' })
    const ui = await $.ui.mount(pane('nf-dashboard') as never)
    await seen.clock.advance(500)
    await ui.press({ key: 'nf-dash-boards' })
    expect(seen.closes).toEqual(['nf-dashboard'])
    expect(seen.opens.map(open => [open.id, open.focus])).toEqual([['nf-dashboard', true], ['nf-board', true]])
    await ui.unmount()
    // The boards hold the keys now: a 2 picks their second level and g is none of theirs, so the picker is reached
    // from the dashboard opened again (the live check says so).
    expect([VIEW_KEYS.board['2'], VIEW_KEYS.board.g]).toEqual(['pick', undefined])
    await $.command.run({ command: 'neuroflow:dashboard', args: 'phase' })
    const again = await $.ui.mount(pane('nf-dashboard') as never)
    expect(buttons(await again.drawn()).find(button => button.key === 'nf-dash-switch')).toMatchObject({ hotkey: 'g', label: 'go to phase…', plain: true })
    await seen.clock.advance(500)
    await again.press({ key: 'nf-dash-switch' })
    expect(seen.closes).toEqual(['nf-dashboard', 'nf-dashboard'])
    expect(seen.opens.slice(-1).map(open => [open.id, open.focus])).toEqual([['nf-phase', true]])
    await again.unmount()
  })

  test('a pane that does not hold the keys says how to give them to it (on the terminal): its command first, then where ^X Tab lands', { options: { runtime: 'observe' } }, async ($, on) => {
    setUp(on)
    await $.session.start({ cwd: project, surface: 'terminal', isInteractive: true })
    await $.command.run({ command: 'neuroflow:dashboard', args: '' })
    await $.command.run({ command: 'neuroflow:tasks', args: '' })
    await $.command.run({ command: 'neuroflow:phase', args: '' })
    // The band here shows the meeting with its keys: ^X Tab lands on the band first, where x would hide the band and
    // not cancel a pick. The command is the sure way back into the pane; a narrow foot cuts the chord first.
    const shown = await $.ui.mount(band(116) as never)
    expect(hotkeys(await shown.drawn())).toEqual(['p', 'o', 'd', 'x'])
    await shown.unmount()
    for (const [id, command] of [['nf-dashboard', '/neuroflow:dashboard'], ['nf-board', '/neuroflow:tasks'], ['nf-phase', '/neuroflow:phase']] as const) {
      const ui = await $.ui.mount(pane(id, false) as never)
      const drawn = await ui.drawn()
      expect(lines(drawn)).toContain(`${command} gives it the keys · ^X Tab reaches it after the band`)
      expect(JSON.stringify(drawn)).not.toContain('esc: prompt')
      await ui.unmount()
    }
    // A desktop has no chord to teach: its pane draws its keys as buttons to click.
    const desktop = await $.ui.mount(pane('nf-dashboard', false, 'desktop') as never)
    expect(JSON.stringify(await desktop.drawn())).not.toContain('^X Tab')
    expect(hotkeys(await desktop.drawn())).toContain('q')
    await desktop.unmount()
  })

  test('the band teaches ^X Tab until it has taken the keys three times; a person moving the ring is no take', { options: { runtime: 'observe', band: 'quiet' } }, async ($, on) => {
    const seen = setUp(on)
    await $.session.start({ cwd: project, surface: 'terminal', isInteractive: true })
    const ui = await $.ui.mount(band(116) as never)
    const first = await ui.drawn()
    expect(JSON.stringify(first)).toContain('^X Tab: keys')
    // The ring starts on d when the band takes the keys; the meeting's keys and the dashboard's are letters.
    expect(buttons(first).filter(button => button.autoFocus).map(button => button.key)).toEqual(['nf-band-dashboard'])
    expect(hotkeys(first)).toEqual(['p', 'o', 'd', 'x'])
    expect(keyProblems(first, 'band')).toEqual([])
    const take = { component: 'AbovePrompt', requestId: 'band', plugin: 'neuroflow', element: 'nf-band-dashboard', origin: { kind: 'plugin', name: 'neuroflow' } }
    await $.ui.focus(take as never)
    await $.ui.focus(take as never)
    await $.ui.focus({ ...take, element: 'nf-meet-prepare', origin: { kind: 'person' } } as never)
    expect(JSON.stringify(await ui.drawn())).toContain('^X Tab: keys')
    expect(seen.store.get('keys.learned')).toBe(2)
    await $.ui.focus(take as never)
    expect(seen.store.get('keys.learned')).toBe(3)
    expect(JSON.stringify(await ui.drawn())).not.toContain('^X Tab')
    await ui.unmount()
    // The desktop has no chord: no hint there, ever.
    const desktop = await $.ui.mount(band(116, 'desktop') as never)
    expect(JSON.stringify(await desktop.drawn())).not.toContain('^X Tab')
    await desktop.unmount()
  })

  test('a person who learned the chord in an earlier session sees no hint; the band\'s d opens the dashboard on now', { options: { runtime: 'observe', band: 'quiet' } }, async ($, on) => {
    const seen = setUp(on, { 'keys.learned': 3 })
    await $.session.start({ cwd: project, surface: 'terminal', isInteractive: true })
    await $.command.run({ command: 'neuroflow:dashboard', args: 'loop' })
    const ui = await $.ui.mount(band(116) as never)
    expect(JSON.stringify(await ui.drawn())).not.toContain('^X Tab')
    await ui.press({ key: 'nf-band-dashboard' })
    expect(seen.opens.map(open => [open.id, open.focus])).toEqual([['nf-dashboard', true], ['nf-dashboard', true]])
    await ui.unmount()
    const dashboard = await $.ui.mount(pane('nf-dashboard') as never)
    expect(JSON.stringify(await dashboard.drawn())).toContain('1: now')
    await dashboard.unmount()
  })

  test('the band on one row: the mark first, the most urgent item, and short words where its keys would crowd it at 75 cells', { options: { runtime: 'observe', band: 'quiet' } }, async ($, on) => {
    setUp(on, { 'keys.learned': 3 })
    await $.session.start({ cwd: project, surface: 'terminal', isInteractive: true })
    // 80 columns: the meeting's two keys, d and x leave the item too little room in full words.
    const narrow = await $.ui.mount(band(75) as never)
    const tight = await narrow.drawn()
    expect(lines(tight).slice(0, 3)).toEqual(['◌', '▸ meeting "Lab meeting" in 60 min', '+1'])
    expect(buttons(tight).map(button => `${button.hotkey}: ${button.label}`)).toEqual(['p: prepare', 'o: notes', 'd: dashboard', 'x: hide'])
    await narrow.unmount()
    // 120 columns: the full words and `+1 more`.
    const wide = await $.ui.mount(band(116) as never)
    const roomy = await wide.drawn()
    expect(lines(roomy).slice(0, 3)).toEqual(['◌', '▸ meeting "Lab meeting" in 60 min', '+1 more'])
    expect(buttons(roomy).map(button => button.label)).toEqual(['prepare', 'notes', 'dashboard', 'hide today'])
    await wide.unmount()
  })
})

describe('the band at 80 columns, before the chord is learned', () => {
  const project = '/work/proj'
  const config = (version: string) => `---\nnf_schema: 1\nproject_name: Oddball\nactive_phase: data\nplugin_version: ${version}\n---\n`
  const setUp = (on: On, files: Record<string, string>, stored: Record<string, unknown> = {}) => {
    // Not named "neuroflow": the pattern also matches the project, which would then read as the plugin's own repo.
    fakeFs(on, { ...files, '*/.claude-plugin/plugin.json': '{"name": "neuroflow-fixture", "version": "0.2.22"}' }, project)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: new Date(2026, 9, 7, 9, 0).getTime() })
    const store = new Map(Object.entries(stored))
    on('store.get', ($, e) => ({ value: store.get(e.key) }))
    on('store.set', ($, e) => {
      store.set(e.key, e.value)
      return { value: undefined }
    })
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('ui.status', () => ({ value: undefined }))
  }
  const band = (bodyColumns: number) => ({
    plugin: 'neuroflow', surface: 'terminal', component: 'AbovePrompt',
    props: { hasSurvey: false, isWorking: false, maxRows: 4, bodyColumns, scroll: { offset: 0, bodyRows: 4 }, view: {} },
  })
  /** The keys as drawn, `k: label`. */
  const keys = (tree: unknown): string[] => buttons(tree).map(button => `${button.hotkey}: ${button.label}`)

  test('the version notice alone: m, d and x: hide, and ^X Tab: keys says how to press them', { options: { runtime: 'observe', band: 'quiet' } }, async ($, on) => {
    setUp(on, { [`${project}/.neuroflow/project_config.md`]: config('0.2.21') })
    await $.session.start({ cwd: project, surface: 'terminal', isInteractive: true })
    const narrow = await $.ui.mount(band(75) as never)
    const tight = await narrow.drawn()
    expect(keys(tight)).toEqual(['m: migrate', 'd: dashboard', 'x: hide'])
    expect(lines(tight)).toContain('^X Tab: keys')
    await narrow.unmount()
    // At 120 columns the full words come back beside the hint.
    const wide = await $.ui.mount(band(115) as never)
    const roomy = await wide.drawn()
    expect(keys(roomy)).toEqual(['m: migrate', 'd: dashboard', 'x: hide today'])
    expect(lines(roomy)).toContain('^X Tab: keys')
    await wide.unmount()
  })

  test('an alert and one more: `+1` and `x: hide` keep the hint on the row', { options: { runtime: 'observe', band: 'quiet' } }, async ($, on) => {
    setUp(on, {
      [`${project}/.neuroflow/project_config.md`]: config('0.2.21'),
      [`${project}/.neuroflow/timeline.md`]: '| Date | What | Gates |\n|---|---|---|\n| 2026-10-08 | Abstract deadline | paper |\n',
    })
    await $.session.start({ cwd: project, surface: 'terminal', isInteractive: true })
    const narrow = await $.ui.mount(band(75) as never)
    const tight = await narrow.drawn()
    expect(lines(tight)).toEqual(['◌', '⚠ Abstract deadline — tomorrow', '+1', '^X Tab: keys'])
    expect(keys(tight)).toEqual(['d: dashboard', 'x: hide'])
    await narrow.unmount()
  })

  test('learned: no hint, and the long words wherever they leave the item its room', { options: { runtime: 'observe', band: 'quiet' } }, async ($, on) => {
    setUp(on, {
      [`${project}/.neuroflow/project_config.md`]: config('0.2.21'),
      [`${project}/.neuroflow/timeline.md`]: '| Date | What | Gates |\n|---|---|---|\n| 2026-10-08 | Abstract deadline | paper |\n',
    }, { 'keys.learned': 3 })
    await $.session.start({ cwd: project, surface: 'terminal', isInteractive: true })
    const narrow = await $.ui.mount(band(75) as never)
    const tight = await narrow.drawn()
    expect(lines(tight)).toEqual(['◌', '⚠ Abstract deadline — tomorrow', '+1 more'])
    expect(keys(tight)).toEqual(['d: dashboard', 'x: hide today'])
    await narrow.unmount()
  })
})

describe('phase switching', () => {
  const project = '/work/proj'
  const setup = (on: On) => {
    const fs = fakeFs(on, {
      [`${project}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nproject_name: Oddball\nactive_phase: data\nrecommended_phases: [data, data-analyze, paper]\n---\n# Notes\n',
    }, project)
    mock.env(on, { HOME: '/home/me' })
    const clock = mock.clock(on, { now: new Date(2026, 9, 7, 9, 30).getTime() })
    mock.store(on)
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('ui.open', () => ({ value: { isPlaced: true } }))
    on('ui.close', () => ({ value: undefined }))
    on('ui.toast', () => ({ value: undefined }))
    return { fs, clock }
  }

  test('/neuroflow:phase <name> switches at once and logs it', { options: { runtime: 'observe' } }, async ($, on) => {
    const { fs } = setup(on)
    await $.session.start({ cwd: project, surface: 'terminal', isInteractive: true })
    const result = await $.command.run({ command: 'neuroflow:phase', args: 'paper' })
    expect(result.text).toBe('Active phase is now paper.')
    expect(fs.files[`${project}/.neuroflow/project_config.md`]).toContain('active_phase: paper\n')
    expect(fs.files[`${project}/.neuroflow/project_config.md`]).toContain('# Notes')
    expect(fs.files[`${project}/.neuroflow/sessions/2026-10-07.md`]).toBe('## 09:30 — [phase] Active phase → paper (phase command) (auto)\n')
    const decision = JSON.parse(fs.files[`${project}/.neuroflow/reasoning/general.jsonl`].trim())
    expect(decision.statement).toBe('Active phase set to paper')
    expect(decision.approved_by).toBe('person')
  })

  test('a switch in a project linked to a flowie hands /neuroflow:phase --sync to the prompt', { options: { runtime: 'observe' } }, async ($, on) => {
    fakeFs(on, {
      [`${project}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nproject_name: Oddball\nactive_phase: data\nflowie_profiles:\n  - handle: me\n    repo: me/flowie\n---\n',
    }, project)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: new Date(2026, 9, 7, 9, 30).getTime() })
    mock.store(on)
    on('session.start', ($$, e) => ({ cwd: e.cwd }))
    on('ui.toast', () => ({ value: undefined }))
    const filled: string[] = []
    on('prompt.fill', ($$, e) => {
      filled.push(e.text)
      return { isFilled: true, text: e.text, cursor: e.text.length }
    })
    await $.session.start({ cwd: project, surface: 'terminal', isInteractive: true })
    const result = await $.command.run({ command: 'neuroflow:phase', args: 'paper' })
    expect(result.text).toContain('Press Enter to record it on your flowie')
    expect(filled).toEqual(['/neuroflow:phase --sync'])
  })

  test('the picker switches on a pick', { options: { runtime: 'observe' } }, async ($, on) => {
    const { fs, clock } = setup(on)
    await $.session.start({ cwd: project, surface: 'terminal', isInteractive: true })
    const opened = await $.command.run({ command: 'neuroflow:phase', args: '' })
    expect(opened.text).toContain('Phase picker open')
    for (const surface of ['terminal', 'desktop'] as const) {
      const ui = await $.ui.mount({
        plugin: 'neuroflow', surface, component: 'Pane', requestId: 'nf-phase',
        props: { title: 'Switch phase', isFocused: true, bodyColumns: 60, placement: 'inline', scroll: { offset: 0, bodyRows: 12 }, view: {} },
      } as never)
      // The one legend's glyph, the id and label, and the state words in one column.
      const options = (elements(await ui.drawn(), 'Select')[0]?.props.options ?? []) as { value: string; label: string }[]
      expect(options.find(option => option.value === 'data-analyze')?.label).toMatch(/^data-analyze — analysis +→ next$/)
      expect(options.find(option => option.value === 'data')?.label).toMatch(/^data — acquisition & BIDS +◉ current$/)
      expect(lines(await ui.drawn())[0]).toBe('◌ switch phase')
      await ui.unmount()
    }
    const ui = await $.ui.mount({
      plugin: 'neuroflow', surface: 'terminal', component: 'Pane', requestId: 'nf-phase',
      props: { title: 'Switch phase', isFocused: true, bodyColumns: 60, placement: 'inline', scroll: { offset: 0, bodyRows: 12 }, view: {} },
    } as never)
    // The legend says how the list works; an Enter typed through the open switches nothing.
    expect(lines(await ui.drawn())).toEqual(expect.arrayContaining(['↓ or enter: open · ↑↓: move · a letter: jump · enter: switch', 'esc: close', 'now: data']))
    await ui.select({ key: 'nf-phase-select', value: 'data-analyze' })
    expect(fs.files[`${project}/.neuroflow/project_config.md`]).toContain('active_phase: data\n')
    await clock.advance(500)
    await ui.select({ key: 'nf-phase-select', value: 'data-analyze' })
    expect(fs.files[`${project}/.neuroflow/project_config.md`]).toContain('active_phase: data-analyze\n')
  })

  test('a switch writes active_phase only: plugin_version and the version notice stay', { options: { runtime: 'observe', band: 'quiet' } }, async ($, on) => {
    const config = '---\nnf_schema: 1\nproject_name: Oddball\nactive_phase: data\nplugin_version: 0.2.21\n---\n# Notes\n'
    const fs = fakeFs(on, {
      [`${project}/.neuroflow/project_config.md`]: config,
      // Not named "neuroflow": the pattern also matches the project, which would then read as the plugin's own repo.
      '*/.claude-plugin/plugin.json': '{"name": "neuroflow-fixture", "version": "0.2.22"}',
    }, project)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: new Date(2026, 9, 7, 9, 30).getTime() })
    mock.store(on)
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('ui.toast', () => ({ value: undefined }))
    await $.session.start({ cwd: project, surface: 'terminal', isInteractive: true })
    expect((await $.command.run({ command: 'neuroflow:phase', args: 'paper' })).text).toBe('Active phase is now paper.')
    // Only /neuroflow:migrate raises plugin_version (neuroflow-core → the config contract).
    expect(fs.files[`${project}/.neuroflow/project_config.md`]).toBe(config.replace('active_phase: data', 'active_phase: paper'))
    const ui = await $.ui.mount({
      plugin: 'neuroflow',
      surface: 'terminal',
      component: 'AbovePrompt',
      props: { hasSurvey: false, isWorking: false, maxRows: 4, bodyColumns: 120, scroll: { offset: 0, bodyRows: 4 }, view: {} },
    } as never)
    expect(JSON.stringify(await ui.drawn())).toContain('neuroflow 0.2.22 is installed; this project is on 0.2.21 — run /neuroflow:migrate')
    await ui.unmount()
  })

  test('without a project the markdown command runs', { options: { runtime: 'observe' } }, async ($, on) => {
    fakeFs(on, {}, '/tmp/nothing')
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: 0 })
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    let ranProse = false
    on('command.run', ($, e) => {
      ranProse = true
      return { text: 'prose' }
    })
    await $.session.start({ cwd: '/tmp/nothing', surface: 'terminal', isInteractive: true })
    expect((await $.command.run({ command: 'neuroflow:phase', args: '' })).text).toBe('prose')
    expect(ranProse).toBe(true)
  })
})

describe('integrity actions in the dashboard', () => {
  test('the documents a freeze covers', () => {
    expect(freezeCandidates(['status.md', 'prereg-osf.md', 'review-report.md', 'deviations.md', 'registered-report.md', 'flow.md']))
      .toEqual(['prereg-osf.md', 'registered-report.md'])
  })

  const root = '/work/proj'
  const files = {
    [`${root}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nactive_phase: preregistration\n---\n',
    [`${root}/.neuroflow/preregistration/prereg-osf.md`]: '# Prereg',
    [`${root}/.neuroflow/preregistration/review-report.md`]: '# Review',
  }
  const pane = { plugin: 'neuroflow', surface: 'terminal', component: 'Pane', requestId: 'nf-dashboard', props: { title: 'neuroflow', isFocused: true, bodyColumns: 80, placement: 'inline', scroll: { offset: 0, bodyRows: 16 }, view: {} } }

  const setUp = (on: On, answer: string): { asked: string[]; ran: string[][]; clock: ReturnType<typeof mock.clock> } => {
    fakeFs(on, files, root)
    mock.env(on, { HOME: '/home/me' })
    const seen = { asked: [] as string[], ran: [] as string[][], clock: mock.clock(on, { now: new Date(2026, 9, 7, 12, 0).getTime() }) }
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('ui.toast', () => ({ value: undefined }))
    on('ui.status', () => ({ value: undefined }))
    on('ui.open', () => ({ value: undefined }))
    on('tool.call', ($, e) => {
      const input = e as unknown as { tool: string; questions?: { question: string }[] }
      const question = input.questions?.[0]?.question ?? ''
      seen.asked.push(question)
      return { result: { questions: input.questions ?? [], answers: { [question]: answer } }, text: answer }
    })
    on('process.run', ($, e) => {
      const argv = (e as unknown as { argv: string[] }).argv
      if (/freeze\.py/.test(argv.join(' '))) seen.ran.push(argv)
      return { value: { exitCode: /freeze\.py/.test(argv.join(' ')) ? 0 : 2, stdout: '{"status": "frozen"}', stderr: '' } }
    })
    return seen
  }

  test('a key press and an explicit yes freeze the prereg documents as the person', { options: { runtime: 'observe' } }, async ($, on) => {
    const seen = setUp(on, 'Freeze — I froze it myself')
    await $.session.start({ cwd: root, surface: 'terminal', isInteractive: true })
    await $.command.run({ command: 'neuroflow:dashboard', args: 'integrity' })
    const ui = await $.ui.mount(pane as never)
    expect(JSON.stringify(await ui.drawn())).toContain('freeze prereg…')
    // A person's marker is set on Enter (or a click), never on a letter that could be a word typed for the prompt.
    expect(buttons(await ui.drawn()).find(button => button.key === 'nf-dash-freeze')).toEqual({ key: 'nf-dash-freeze', label: 'freeze prereg…', plain: true })
    expect(hotkeys(await ui.drawn())).not.toContain('f')
    await seen.clock.advance(500)
    await ui.press({ key: 'nf-dash-freeze' })
    expect(seen.asked[0]).toContain('prereg-osf.md')
    const argv = seen.ran.find(item => item.includes('freeze')) ?? []
    expect(argv).toContain('.neuroflow/preregistration/prereg-osf.md')
    expect(argv).not.toContain('.neuroflow/preregistration/review-report.md')
    expect(argv.slice(argv.indexOf('--set-by'), argv.indexOf('--set-by') + 2)).toEqual(['--set-by', 'person'])
  })

  test('any answer but the exact yes freezes nothing; an Enter right after another key does not even ask', { options: { runtime: 'observe' } }, async ($, on) => {
    const seen = setUp(on, 'Not now')
    await $.session.start({ cwd: root, surface: 'terminal', isInteractive: true })
    await $.command.run({ command: 'neuroflow:dashboard', args: 'integrity' })
    const ui = await $.ui.mount(pane as never)
    await seen.clock.advance(500)
    // `r` typed, and Enter at once: typed through.
    await ui.press({ key: 'nf-dash-reread' })
    await ui.press({ key: 'nf-dash-freeze' })
    expect(seen.asked).toEqual([])
    await seen.clock.advance(500)
    await ui.press({ key: 'nf-dash-freeze' })
    expect(seen.asked[0]).toContain('prereg-osf.md')
    expect(seen.ran.filter(item => item.includes('freeze'))).toEqual([])
  })
})

describe('the dashboard in the new look', () => {
  const project = '/work/proj'
  const FILES = {
    [`${project}/.neuroflow/project_config.md`]:
      '---\nnf_schema: 1\nproject_name: Oddball\nactive_phase: data-analyze\ndefault_mode: critic\nrecommended_phases: [ideation, preregistration, data, data-analyze, paper]\n---\n',
    [`${project}/.neuroflow/timeline.md`]: '| Date | What | Gates |\n|---|---|---|\n| 2026-10-08 | Abstract deadline | paper |\n| 2026-10-19 | Lab retreat | |\n',
    [`${project}/.neuroflow/meetings/lab-2026-10-07.md`]: '---\ntitle: Lab meeting\ndate: 2026-10-07T14:00\n---\n',
    [`${project}/.neuroflow/ideation/flow.md`]: '# ideation\n',
    [`${project}/.neuroflow/preregistration/flow.md`]: '# preregistration\n',
    [`${project}/.neuroflow/data/flow.md`]: '# data\n',
  }
  const setUp = (on: On) => {
    fakeFs(on, FILES, project)
    mock.env(on, { HOME: '/home/me' })
    const clock = mock.clock(on, { now: new Date(2026, 9, 7, 13, 0).getTime() })
    mock.store(on)
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('ui.open', () => ({ value: { isPlaced: true } }))
    on('ui.status', () => ({ value: undefined }))
    on('ui.focus', () => ({}))
    on('command.run', () => ({ text: '', ref: 1 }))
    return clock
  }
  const pane = (bodyColumns: number, surface = 'terminal', rows?: number) => ({
    plugin: 'neuroflow', surface, component: 'Pane', requestId: 'nf-dashboard',
    props: { title: 'neuroflow', isFocused: true, bodyColumns, placement: 'inline', scroll: { offset: 0, bodyRows: 18 }, view: {} },
    ...(rows === undefined ? {} : { viewport: { columns: bodyColumns + 4, rows } }),
  })

  test('at 76 and 116 cells: the mark and the wordmark, the tabs over a rule heavy under the shown one, the legend', { options: { runtime: 'observe' } }, async ($, on) => {
    const clock = setUp(on)
    await $.session.start({ cwd: project, surface: 'terminal', isInteractive: true })
    await $.command.run({ command: 'neuroflow:dashboard', args: '' })
    const medium = await $.ui.mount(pane(76, 'terminal', 40) as never)
    const rows = lines(await medium.drawn())
    expect(rows.slice(0, 2)).toEqual(['◌ neuroflow', 'Oddball · data-analyze · critic'])
    // The shown tab reads `1: now` at full strength, a key with no letter; the others are dim digit keys.
    expect(buttons(await medium.drawn()).find(button => button.key === 'nf-tab-now')).toEqual({ key: 'nf-tab-now', label: '1: now', plain: true })
    expect(rows).toContain(`${'━'.repeat(6)}${'─'.repeat(70)}`)
    expect(rows).toContain('▸ meeting "Lab meeting" in 60 min')
    // The summary under what needs attention, its labels UPPERCASE; side by side only where the pane is wide.
    expect(rows).toContain('PHASE')
    expect(rows).not.toContain('NEEDS ATTENTION')
    expect(rows).toContain('enter: act · esc: prompt')
    expect(buttons(await medium.drawn()).find(button => button.key === 'nf-nav-left')?.label).toBe('‹')
    await clock.advance(500)
    await medium.press({ key: 'nf-tab-deadlines' })
    expect(lines(await medium.drawn())).toContain(`${'─'.repeat(20)}${'━'.repeat(12)}${'─'.repeat(44)}`)
    await medium.press({ key: 'nf-tab-now' })
    await medium.unmount()
    const wide = await $.ui.mount(pane(116, 'terminal', 40) as never)
    const glance = lines(await wide.drawn())
    expect(glance).toContain('NEEDS ATTENTION')
    expect(glance).toContain('AT A GLANCE')
    expect(buttons(await wide.drawn()).find(button => button.key === 'nf-nav-left')?.label).toBe('‹ tab')
    expect(keyProblems(await wide.drawn(), 'dashboard')).toEqual([])
    await wide.unmount()
  })

  test('narrow (a 44-cell dock) and compact (24 rows): the title on the mark\'s line, a plain rule, no summary when short', { options: { runtime: 'observe' } }, async ($, on) => {
    setUp(on)
    await $.session.start({ cwd: project, surface: 'terminal', isInteractive: true })
    await $.command.run({ command: 'neuroflow:dashboard', args: '' })
    const narrow = await $.ui.mount(pane(44, 'terminal', 40) as never)
    const dock = lines(await narrow.drawn())
    expect(dock[0]).toBe('◌ neuroflow · Oddball · data-analyze · critic')
    expect(dock).toContain('─'.repeat(44))
    expect(dock).toContain('PHASE')
    await narrow.unmount()
    const short = await $.ui.mount(pane(76, 'terminal', 24) as never)
    const ssh = lines(await short.drawn())
    expect(ssh[0]).toBe('◌ neuroflow · Oddball · data-analyze · critic')
    expect(ssh).not.toContain('PHASE')
    // No closing rule above the legend: every row goes to what needs attention.
    expect(ssh.filter(line => /^─+$/.test(line))).toEqual([])
    await short.unmount()
  })

  test('the deadlines tab: a ruler with week ticks on the terminal, the dates as a list on every surface', { options: { runtime: 'observe' } }, async ($, on) => {
    setUp(on)
    await $.session.start({ cwd: project, surface: 'terminal', isInteractive: true })
    await $.command.run({ command: 'neuroflow:dashboard', args: 'deadlines' })
    const terminal = await $.ui.mount(pane(76) as never)
    const drawn = lines(await terminal.drawn())
    expect(drawn).toContain(`today ┼${'──────┬'.repeat(8)} +56 d`)
    // Tomorrow's deadline sits on day 1, the retreat in twelve days on day 12.
    expect(drawn).toContain(`${' '.repeat(7)}⚠${' '.repeat(10)}▸`)
    for (const cell of ['2026-10-08', 'Abstract deadline', 'tomorrow', 'gates paper', 'in 12 days']) expect(drawn).toContain(cell)
    await terminal.unmount()
    const desktop = await $.ui.mount(pane(76, 'desktop') as never)
    expect(lines(await desktop.drawn()).some(line => line.startsWith('today ┼'))).toBe(false)
    expect(lines(await desktop.drawn())).toContain('Abstract deadline')
    await desktop.unmount()
  })

  test('the phase tab: the ring unrolled into a flow line where each phase has nine cells, the word list elsewhere', { options: { runtime: 'observe' } }, async ($, on) => {
    setUp(on)
    await $.session.start({ cwd: project, surface: 'terminal', isInteractive: true })
    await $.command.run({ command: 'neuroflow:dashboard', args: 'phase' })
    const terminal = await $.ui.mount(pane(76) as never)
    const drawn = lines(await terminal.drawn())
    expect(drawn).toContain(`●${'━'.repeat(14)}●${'━'.repeat(14)}●${'━'.repeat(14)}◉${'─'.repeat(14)}→`)
    expect(drawn).toContain('◉ current  ● visited  → recommended next')
    expect(drawn).toContain('NEXT')
    await terminal.unmount()
    // Five phases in 44 cells leave eight a phase: the word list.
    const narrow = await $.ui.mount(pane(44) as never)
    expect(lines(await narrow.drawn())).toContain('● ideation  ● preregistration  ● data  ◉ data-analyze  → paper')
    await narrow.unmount()
  })
})

describe('words typed into a dashboard that holds the keys', () => {
  const project = '/work/proj'
  /** Every row of the now tab that writes, consents or starts a turn: a drafted decision, a meeting, the version notice, wiki cards. */
  const FILES = {
    [`${project}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nproject_name: Oddball\nactive_phase: data-analyze\nplugin_version: 0.2.21\n---\n',
    // Not named "neuroflow": the pattern also matches the project, which would then read as the plugin's own repo.
    '*/.claude-plugin/plugin.json': '{"name": "neuroflow-fixture", "version": "0.2.22"}',
    '*/commands/data-analyze.md': '---\nname: data-analyze\nphase: data-analyze\nlifecycle: full\n---\n',
    [`${project}/.neuroflow/sessions/2026-10-07.md`]: '## 10:00 — [data-analyze] plan written\n',
    [`${project}/.neuroflow/meetings/lab-2026-10-07.md`]: '---\ntitle: Lab meeting\ndate: 2026-10-07T11:30\n---\n',
    [`${project}/.neuroflow/wiki/.pending/2026-10-07-fdr.md`]: '---\ntitle: FDR\nstatus: pending\n---\nbody\n',
  }
  const PANE = {
    plugin: 'neuroflow', surface: 'terminal', component: 'Pane', requestId: 'nf-dashboard',
    props: { title: 'neuroflow', isFocused: true, bodyColumns: 116, placement: 'inline', scroll: { offset: 0, bodyRows: 18 }, view: {} },
  }

  test('"ok" and Enter, typed for the prompt into a freshly opened dashboard past its open guard, write and run nothing', { options: { runtime: 'on' } }, async ($, on) => {
    const fs = fakeFs(on, FILES, project)
    mock.env(on, { HOME: '/home/me' })
    const clock = mock.clock(on, { now: new Date(2026, 9, 7, 10, 30).getTime() })
    mock.store(on)
    on('session.start', ($$, e) => ({ cwd: e.cwd }))
    on('session.model', () => ({ value: 'claude-test' }))
    on('turn.complete', () => ({ text: 'done' }))
    on('ui.status', () => ({ value: undefined }))
    on('ui.toast', () => ({ value: undefined }))
    on('ui.log', () => ({ value: undefined }))
    on('ui.open', () => ({ value: { isPlaced: true } }))
    on('ui.focus', () => ({}))
    const ran: string[] = []
    on('command.run', ($$, e) => {
      ran.push(`${e.command} ${e.args}`.trim())
      return { text: '', ref: 1 }
    })
    const filled: string[] = []
    on('prompt.fill', ($$, e) => {
      filled.push(e.text)
      return { isFilled: true, text: e.text, cursor: e.text.length }
    })
    on('model.complete', () => ({
      value: {
        isAnswered: true,
        text: '{"statement": "Use FDR (BH) across electrodes", "reasoning": "Bonferroni was too conservative."}',
        usage: { input_tokens: 10, output_tokens: 10, cache_creation_input_tokens: 0, cache_read_input_tokens: 0 },
      },
    }))
    // Each question is answered as a stray Enter would answer it: with its first option.
    const dialog = answerAsks(on)
    await $.session.start({ cwd: project, surface: 'terminal', isInteractive: true })
    // A command turn that logged no decision: the mod drafts one, kept only on the person's yes.
    await $.command.run({ command: 'neuroflow:data-analyze', args: '' })
    await $.turn.complete({ reason: 'answer', answer: 'We compared Bonferroni and FDR. '.repeat(10), durationMs: 1, isAborted: false, turnId: 't1' } as never)
    await $.command.run({ command: 'neuroflow:dashboard', args: '' })
    ran.length = 0
    const ui = await $.ui.mount(PANE as never)
    const tree = await ui.drawn()
    expect(lines(tree)).toContain('✎ decision drafted for data-analyze: Use FDR (BH) across electrodes')
    const before = JSON.stringify(fs.files)
    // The now tab's stops as drawn, from the top: the Update line's migrate, the tab's own name, each row's actions.
    const ring = buttons(tree).map(button => button.key).filter(key => key === 'nf-dash-migrate' || key === NOW_START || key.startsWith('nf-now-'))
    expect(ring.slice(0, 3)).toEqual(['nf-dash-migrate', NOW_START, 'nf-now-draft-keep'])
    expect(ring).toEqual(expect.arrayContaining(['nf-now-draft-drop', 'nf-now-meet-prepare', 'nf-now-meet-notes', 'nf-now-wiki-review']))
    const actions = ring.filter(key => key !== NOW_START)
    // Typed a second and a half after the open, past its guard: `o` is no key of the pane, `k` moves the ring.
    await clock.advance(1500)
    expect(hotkeys(tree)).not.toContain('o')
    expect(hotkeys(tree)).toContain('k')
    await ui.press({ key: 'nf-nav-up' })
    // The kit has no ring of its own, so Enter is pressed where the mod sends the ring from none: the tab's own name.
    const enterOn = lineNeighbour(ring, null, -1, NOW_START)
    expect(enterOn).toBe(NOW_START)
    await ui.press({ key: enterOn ?? '' })
    // Whatever the ring had stood on, an Enter right after the `k` presses nothing.
    for (const key of actions) await ui.press({ key })
    // "okay" typed slowly: the Enter comes 600 ms after the `k`, and still only reads the tab again.
    await clock.advance(300)
    await ui.press({ key: 'nf-nav-up' })
    await clock.advance(600)
    await ui.press({ key: lineNeighbour(ring, null, -1, NOW_START) ?? '' })
    expect(ran).toEqual([])
    expect(filled).toEqual([])
    expect(dialog.asked).toEqual([])
    expect(JSON.stringify(fs.files)).toBe(before)
    // And had the ring been walked onto an action, a late Enter only asks — the safe answer first, which is what a
    // stray Enter in the dialog picks: still nothing is written, kept, migrated, synced or prepared.
    for (const key of actions) {
      await clock.advance(500)
      await ui.press({ key })
    }
    expect(dialog.asked.map(asked => asked.options[0])).toEqual(['Not now', 'Not now', 'Keep it waiting', 'Not now', 'Not now', 'Not now'])
    expect(dialog.asked.map(asked => asked.question)).toEqual([
      'Run /neuroflow:migrate now? It starts a model turn.',
      'Keep "Use FDR (BH) across electrodes" in the reasoning log, as a decision you approved?',
      'Drop the drafted decision "Use FDR (BH) across electrodes"? It is not written anywhere.',
      'Run /neuroflow:meeting --prepare lab-2026-10-07 now? It starts a model turn.',
      'Run /neuroflow:meeting --notes lab-2026-10-07 now? It starts a model turn.',
      'Run /neuroflow:wiki --review now? It starts a model turn.',
    ])
    expect(ran).toEqual([])
    expect(JSON.stringify(fs.files)).toBe(before)
    expect(lines(await ui.drawn())).toContain('✎ decision drafted for data-analyze: Use FDR (BH) across electrodes')
    await ui.unmount()
  })
})
