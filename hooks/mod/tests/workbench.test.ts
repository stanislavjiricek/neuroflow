// The claude.ai workbench in the mod (neuroflow-core → Workbench snapshot): pending.json on the band and the board,
// /neuroflow:dashboard --web left to the prose, and the EGRESS-CONFIRM guard on ArtifactData writes.
import type { On } from 'claude-code'
import { describe, expect, mock, test } from 'claude-code/testing'

import { bandActions, bandItems } from '../features/views'
import { cardLine, loadTaskView } from '../lib/tasks'
import {
  artifactViolations, folderKey, mirroredLevels, normalPath, normalUrl, parsePending, pendingAge, pendingBandItem, pendingSlugs, workbenchUrls, yamlKey,
} from '../lib/workbench'
import type { NfSnapshot } from '../../../types'
import { fakeFs } from './fakefs'
import { memIo } from './memio'

const HOME = '/home/me'
const ROOT = '/work/proj'
const URL = 'https://claude.ai/artifact/0123abcd'
const PENDING = JSON.stringify({
  checked_at: '2026-10-21T08:14:00Z', oldest: '2026-10-19T08:00:00Z', count: 3, command: '/neuroflow:tasks --apply-web',
  levels: [
    { level: 'hive+example-lab+hive', kind: 'hive', board: 'hive:lab-team', slugs: ['rerun-ica'], adds: 0, count: 1 },
    { level: 'project+oddball', kind: 'project', board: 'project', root: 'C:/Work/Proj', slugs: ['qc-report'], adds: 1, count: 2 },
  ],
})

const snapshot = (over: Partial<NfSnapshot> = {}): NfSnapshot => ({
  root: ROOT, nfSchema: 1, dialect: 'frontmatter', pluginVersion: '0.2.25', runningVersion: '0.2.25', projectName: 'Oddball',
  phase: 'data', mode: null, recommendedPhases: [], rawRoots: [], paperAuto: false, ethics: null, prereg: null, deadlines: [],
  phasesVisited: [], loops: [], meetings: [], wellbeingDue: false, ethicsNotApplicable: false, flowieProfiles: [], wikiCapture: null,
  wikiPending: 0, problems: [], loadedAt: 0, ...over,
})

/** A project, a hive clone with a board, pending.json naming both, and the person's recorded workbench. */
const FILES: Record<string, string> = {
  [`${ROOT}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nproject_name: Oddball\nactive_phase: data\n---\n',
  [`${ROOT}/.neuroflow/tasks/review/qc-report.md`]: '---\ntitle: QC report\nstatus: review\n---\n',
  [`${HOME}/.neuroflow/hives/lab-team/tasks/active/rerun-ica.md`]: '---\ntitle: Rerun ICA\nstatus: active\n---\n',
  [`${HOME}/.neuroflow/workbench/pending.json`]: PENDING.replace('C:/Work/Proj', ROOT),
  [`${HOME}/.neuroflow/user.yaml`]: `workbench: on\nworkbench_levels: ["flowie"]\nworkbench_records: [{"account": "home", "url": "${URL}"}]\n`,
}

const setUp = (on: On): void => {
  fakeFs(on, FILES, ROOT)
  mock.env(on, { HOME })
  mock.clock(on, { now: new Date(2026, 9, 21, 10, 0).getTime() })
  mock.store(on)
  on('session.start', ($, e) => ({ cwd: e.cwd }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('ui.toast', () => ({ value: undefined }))
  on('ui.status', () => ({ value: undefined }))
}

describe('pending.json', () => {
  test('is read as written, and names nothing when nothing waits', () => {
    const pending = parsePending(PENDING)
    expect(pending?.count).toBe(3)
    expect(pending?.levels.map(level => level.board)).toEqual(['hive:lab-team', 'project'])
    expect(parsePending(JSON.stringify({ count: 0, levels: [] }))).toBe(null)
    expect(parsePending('not json')).toBe(null)
    expect(parsePending(null)).toBe(null)
  })

  test('marks the cards of the board it names: a hive by its folder, the project by its root', () => {
    const pending = parsePending(PENDING)
    expect([...pendingSlugs(pending, { id: 'hive:lab-team', kind: 'hive' }, ROOT)]).toEqual(['rerun-ica'])
    expect([...pendingSlugs(pending, { id: 'hive:other', kind: 'hive' }, ROOT)]).toEqual([])
    expect([...pendingSlugs(pending, { id: 'project', kind: 'project' }, 'c:/work/proj/')]).toEqual(['qc-report'])
    expect([...pendingSlugs(pending, { id: 'project', kind: 'project' }, '/elsewhere')]).toEqual([])
  })

  test('the project root matches as it was reached or as it resolves, in any case on Windows', () => {
    const pending = parsePending(JSON.stringify({ count: 1, levels: [{ level: 'project+oddball', kind: 'project', board: 'project',
      root: 'C:/jn/oddball', roots: ['C:/jn/oddball', '//Lab-Server/Share/oddball'], slugs: ['qc-report'], count: 1 }] }))
    expect(pending?.levels[0].roots).toEqual(['C:/jn/oddball', '//Lab-Server/Share/oddball'])
    for (const root of ['C:\\JN\\Oddball', 'c:/jn/oddball/', '\\\\lab-server\\share\\Oddball']) {
      expect([...pendingSlugs(pending, { id: 'project', kind: 'project' }, root)]).toEqual(['qc-report'])
    }
    expect([...pendingSlugs(pending, { id: 'project', kind: 'project' }, 'C:/work/oddball')]).toEqual([])
    expect(folderKey('/Home/Jana/Proj')).toBe('/Home/Jana/Proj') // a POSIX path keeps its case
    expect(cardLine({ slug: 'x', title: 'X', owner: null, due: null, overdue: false, project: null, isMine: false, web: true })).toBe('↻ X')
  })

  test('the band says how many changes wait, since when, as of when, and its key fills the apply command', () => {
    const item = pendingBandItem(parsePending(PENDING), Date.parse('2026-10-21T09:00:00Z'))
    expect(item?.text.startsWith('3 workbench changes wait for Claude Code (oldest 2 days, as of ')).toBe(true)
    expect(item?.text.endsWith('— /neuroflow:tasks --apply-web')).toBe(true)
    expect(pendingAge('2026-10-21T08:20:00Z', Date.parse('2026-10-21T09:00:00Z'))).toBe('40 min')
    expect(pendingAge('2026-10-21T04:00:00Z', Date.parse('2026-10-21T09:00:00Z'))).toBe('5 h')
    expect(pendingAge(null, Date.parse('2026-10-21T09:00:00Z'))).toBe('')
    const items = bandItems(snapshot({ workbench: parsePending(PENDING) }), true)
    expect(items.map(entry => entry.glyph)).toEqual(['↻'])
    expect(bandActions(items).map(action => [action.key, action.hotkey, action.command, action.args, action.fill])).toEqual([
      ['nf-web-apply', 'a', 'neuroflow:tasks', '--apply-web', true]])
    expect(bandItems(snapshot({ workbench: null }), true)).toEqual([])
  })

  test('the boards mark the cards a workbench change waits for', async () => {
    const view = await loadTaskView(memIo(FILES), ROOT, HOME, '2026-10-21')
    const hive = view.levels.find(level => level.id === 'hive:lab-team')
    expect(hive?.board.columns.flatMap(column => column.cards).find(card => card.slug === 'rerun-ica')?.web).toBe(true)
    expect(view.levels.find(level => level.id === 'project')?.top.map(card => [card.slug, card.web])).toEqual([['qc-report', true]])
    expect(view.web?.count).toBe(3)
  })
})

describe('the ArtifactData guard (nf-rule: EGRESS-CONFIRM)', () => {
  const context = { urls: [normalUrl(URL)], levels: ['flowie', 'hive+example-lab+hive'] }
  const none = new Map<string, Record<string, unknown> | null>()
  const batch = (writes: unknown[], url = URL) => ({ action: 'batch', url, writes }) as never

  test('the recorded workbench, under data/users/me, for a mirrored level: no question', () => {
    expect(artifactViolations(batch([
      { op: 'set', collection: 'data/users/me/flowie/parts', doc_id: 'core', file_path: 'a.json' },
      { op: 'set', collection: 'data/users/me', doc_id: 'flowie', file_path: 'm.json', if_version: 3 },
      { op: 'delete', collection: 'data/users/me/hive+gone+hive/parts', doc_id: 'core', if_version: 2 },
      { op: 'set', collection: 'data/users/me', doc_id: 'prefs', data: { theme: 'dark' }, if_version: 1 },
      { op: 'update', collection: 'data/users/me/inbox/intents', doc_id: 'i-a-bbbb', data: { status: 'done', outcome: { result: 'applied' } }, if_version: 4 },
      { op: 'delete', collection: 'data/users/me/inbox/intents', doc_id: 'i-a-cccc', if_version: 9 },
    ], `${URL}/?x=1`), context, none)).toEqual([])
    expect(artifactViolations({ action: 'list', url: 'https://claude.ai/artifact/other', collection: 'x' } as never, context, none)).toEqual([])
  })

  test('another artifact, a path outside data/users/me or a level the person does not mirror: it asks', () => {
    const other = artifactViolations(batch([{ op: 'set', collection: 'data/users/me', doc_id: 'flowie', data: {} }], 'https://claude.ai/artifact/other'), context, none)
    expect(other.map(item => item.level)).toEqual(['ask'])
    expect(other[0].message).toContain('not your recorded neuroflow workbench')
    expect(artifactViolations(batch([{ op: 'set', collection: 'shared', doc_id: 'x', data: {} }]), context, none)[0].message).toContain('outside data/users/me')
    expect(artifactViolations(batch([{ op: 'set', collection: 'data/users/me/project+secret/parts', doc_id: 'core', data: {} }]), context, none)[0].message)
      .toContain('project+secret, which is not a level you mirror from this machine')
    // workbench.py did not answer (no Python, a timeout): which levels are mirrored is unknown, so an upload asks
    expect(artifactViolations(batch([{ op: 'set', collection: 'data/users/me/flowie/parts', doc_id: 'core', data: {} }]), { ...context, levels: null }, none))
      .toEqual([{ level: 'ask', message: 'this uploads flowie, and workbench.py could not say which levels you mirror from this machine' }])
  })

  test('the viewer\'s resolved id is the same place as me: an intent there is denied too, a mirrored level passes', () => {
    const uid = 'data/users/u_0123456789abcdefghijkl'
    expect(normalPath(`${uid}/inbox/intents/`)).toBe('data/users/me/inbox/intents')
    const levels = (write: unknown) => artifactViolations(batch([write]), context, none).map(item => item.level)
    expect(levels({ op: 'set', collection: `${uid}/inbox/intents`, doc_id: 'i-new-aaaa', data: { op: 'move' } })).toEqual(['deny'])
    expect(levels({ op: 'update', collection: `${uid}/inbox/intents`, doc_id: 'i-a-aaaa', data: { to: 'done' }, if_version: 2 })).toEqual(['deny'])
    expect(levels({ op: 'update', collection: `${uid}/inbox/intents`, doc_id: 'i-a-aaaa', data: { status: 'done' }, if_version: 2 })).toEqual([])
    expect(levels({ op: 'set', collection: `${uid}/flowie/parts`, doc_id: 'core', file_path: 'a.json' })).toEqual([])
    expect(levels({ op: 'set', collection: `${uid}/project+secret/parts`, doc_id: 'core', data: {} })).toEqual(['ask'])
  })

  test('Claude never creates or rewrites an intent: only the page does, from a click', () => {
    const intents = 'data/users/me/inbox/intents'
    const levels = (write: unknown) => artifactViolations(batch([write]), context, new Map([['f.json', { status: 'claimed', op: 'move' }]])).map(item => item.level)
    expect(levels({ op: 'set', collection: intents, doc_id: 'i-new-aaaa', data: { op: 'move' } })).toEqual(['deny'])
    expect(levels({ op: 'update', collection: intents, doc_id: 'i-new-aaaa', data: { status: 'claimed' } })).toEqual(['deny']) // no pin: a create
    expect(levels({ op: 'update', collection: intents, doc_id: 'i-a-aaaa', data: { to: 'done' }, if_version: 2 })).toEqual(['deny'])
    expect(levels({ op: 'update', collection: intents, doc_id: 'i-a-aaaa', file_path: 'f.json', if_version: 2 })).toEqual(['deny'])
    expect(levels({ op: 'str_replace', collection: intents, doc_id: 'i-a-aaaa', if_version: 2 })).toEqual(['deny'])
    expect(levels({ op: 'update', collection: intents, doc_id: 'i-a-aaaa', file_path: 'missing.json', if_version: 2 })).toEqual(['ask'])
  })

  test('the record comes from the flowie and user.yaml; the mirrored levels from workbench.py levels', async () => {
    const io = memIo({
      [`${HOME}/.neuroflow/user.yaml`]: 'workbench: on\nworkbench_levels: flowie\n'
        + 'workbench_records: [{"account": "home", "url": "https://claude.ai/artifact/aaa"}]\n',
      [`${HOME}/.neuroflow/flowie/workbench.json`]: JSON.stringify({ nf_schema: 1, workbenches: [{ account: 'lab', url: 'HTTPS://Claude.ai/artifact/bbb/' }] }),
    })
    expect(await workbenchUrls(io, HOME)).toEqual(['https://claude.ai/artifact/aaa', 'https://claude.ai/artifact/bbb'])
    expect(yamlKey('workbench_records:\n  - a\n  - "b"\nother: 1\n', 'workbench_records')).toEqual(['a', 'b'])
    // the guard never reads workbench_levels itself (a scalar, a comma list, `workbench: off`, a team's forbid):
    // workbench.py's rows decide, and only the mirrored ones count
    const rows = { levels: [{ level: 'flowie', mirrored: true }, { level: 'hive+x+y', mirrored: false, reason: 'the team forbids mirroring it' }] }
    const ran = memIo({}, { run: () => ({ exitCode: 0, stdout: JSON.stringify(rows), stderr: '' }) })
    expect(await mirroredLevels(ran, ROOT)).toEqual(['flowie'])
    expect(ran.ran[0].slice(1)).toEqual(['/plugin/skills/neuroflow-core/scripts/workbench.py', 'levels', '--json', '--root', ROOT])
    expect(await mirroredLevels(memIo({}), ROOT)).toBe(null) // no Python: unknown, and the guard asks
  })
})

describe('the workbench in a session', () => {
  test('the band\'s w fills /neuroflow:tasks --apply-web for the person to send', { options: { runtime: 'observe', band: 'quiet' } }, async ($, on) => {
    setUp(on)
    const filled: string[] = []
    const ran: string[] = []
    on('prompt.fill', ($, e) => {
      filled.push(e.text)
      return { isFilled: true, text: e.text, cursor: e.text.length }
    })
    on('command.run', ($, e) => {
      ran.push(e.command)
      return { text: '' }
    })
    await $.session.start({ cwd: ROOT, surface: 'terminal', isInteractive: true })
    const ui = await $.ui.mount({ plugin: 'neuroflow', surface: 'terminal', component: 'AbovePrompt', props: { hasSurvey: false, isWorking: false, maxRows: 4, bodyColumns: 140, scroll: { offset: 0, bodyRows: 4 }, view: {} } } as never)
    expect(JSON.stringify(await ui.drawn())).toContain('3 workbench changes wait for Claude Code')
    await ui.press({ key: 'nf-web-apply' })
    expect(filled).toEqual(['/neuroflow:tasks --apply-web'])
    expect(ran).toEqual([])
    await ui.unmount()
  })

  test('/neuroflow:dashboard --web reaches the prose; a bare /neuroflow:dashboard opens the pane', { options: { runtime: 'observe' } }, async ($, on) => {
    setUp(on)
    const prose: string[] = []
    on('command.run', ($, e) => {
      prose.push(`${e.command} ${e.args}`.trim())
      return { text: 'prose' }
    })
    await $.session.start({ cwd: ROOT, surface: 'terminal', isInteractive: true })
    expect((await $.command.run({ command: 'neuroflow:dashboard', args: '--web' } as never)).text).toBe('prose')
    expect((await $.command.run({ command: 'neuroflow:dashboard', args: '--web --status' } as never)).text).toBe('prose')
    expect((await $.command.run({ command: 'neuroflow:dashboard', args: '' } as never)).text).toContain('Dashboard open')
    expect(prose).toEqual(['neuroflow:dashboard --web', 'neuroflow:dashboard --web --status'])
  })

  test('under enforce, Claude creating an intent is denied before the tool runs; a status update goes through', { options: { runtime: 'on', guards: 'enforce' } }, async ($, on) => {
    setUp(on)
    let ran = 0
    on('tool.call', () => {
      ran += 1
      return { result: 'written', text: 'ok' }
    })
    await $.session.start({ cwd: ROOT, surface: 'terminal', isInteractive: true })
    const created = await $.tool.call({ tool: 'ArtifactData', action: 'set', url: URL, collection: 'data/users/me/inbox/intents', doc_id: 'i-x-aaaa', data: { op: 'move' } } as never)
    expect(ran).toBe(0)
    expect(JSON.stringify(created)).toContain('nf-rule: EGRESS-CONFIRM')
    await $.tool.call({ tool: 'ArtifactData', action: 'update', url: URL, collection: 'data/users/me/inbox/intents', doc_id: 'i-x-aaaa', data: { status: 'claimed', claim: { machine: 'laptop' } }, if_version: 3 } as never)
    expect(ran).toBe(1)
    await $.tool.call({ tool: 'ArtifactData', action: 'get', url: 'https://claude.ai/artifact/someone-else', collection: 'data/users/me', doc_id: 'flowie' } as never)
    expect(ran).toBe(2)
  })

  test('under enforce, the levels workbench.py mirrors decide: a hive the team forbids asks though user.yaml lists it', { options: { runtime: 'on', guards: 'enforce' } }, async ($, on) => {
    setUp(on)
    const asked: string[] = []
    let ran = 0
    let levelsRuns = 0
    on('process.run', ($, e) => {
      if (!/workbench\.py/.test(JSON.stringify(e))) return { value: { exitCode: 2, stdout: '', stderr: 'x' } }
      levelsRuns += 1
      return { value: { exitCode: 0, stdout: JSON.stringify({ levels: [{ level: 'flowie', mirrored: true },
        { level: 'hive+example-lab+hive', mirrored: false, reason: 'the team forbids mirroring it' }] }), stderr: '' } }
    })
    on('tool.call', ($, e) => {
      const input = e as unknown as { questions?: { question: string }[] }
      if (input.questions === undefined) {
        ran += 1
        return { result: 'ok', text: 'ok' }
      }
      asked.push(input.questions[0]?.question ?? '')
      return { result: { questions: input.questions, answers: { [input.questions[0]?.question ?? '']: 'Block it' } }, text: 'Block it' }
    })
    await $.session.start({ cwd: ROOT, surface: 'terminal', isInteractive: true })
    const upload = (key: string) => ({ tool: 'ArtifactData', action: 'batch', url: URL, writes: [{ op: 'set', collection: `data/users/me/${key}/parts`, doc_id: 'core', data: {} }] })
    await $.tool.call(upload('flowie') as never)
    expect([ran, asked]).toEqual([1, []])
    const blocked = await $.tool.call(upload('hive+example-lab+hive') as never)
    expect(ran).toBe(1)
    expect(asked[0]).toContain('hive+example-lab+hive, which is not a level you mirror from this machine')
    expect(JSON.stringify(blocked)).toContain('nf-rule: EGRESS-CONFIRM')
    await $.tool.call({ tool: 'ArtifactData', action: 'update', url: URL, collection: 'data/users/me/inbox/intents', doc_id: 'i-x-aaaa', data: { status: 'claimed' }, if_version: 3 } as never)
    expect(levelsRuns).toBe(2) // asked only for the writes that upload a level
  })

  test('under enforce, an upload to another artifact asks, and a no blocks it', { options: { runtime: 'on', guards: 'enforce' } }, async ($, on) => {
    setUp(on)
    const asked: string[] = []
    let answer = 'Block it'
    let ran = 0
    on('tool.call', ($, e) => {
      const input = e as unknown as { questions?: { question: string }[] }
      if (input.questions === undefined) {
        ran += 1
        return { result: 'ok', text: 'ok' }
      }
      const question = input.questions[0]?.question ?? ''
      asked.push(question)
      return { result: { questions: input.questions, answers: { [question]: answer } }, text: answer }
    })
    await $.session.start({ cwd: ROOT, surface: 'terminal', isInteractive: true })
    const write = { tool: 'ArtifactData', action: 'batch', url: 'https://claude.ai/artifact/someone-else', writes: [{ op: 'set', collection: 'data/users/me', doc_id: 'flowie', data: {} }] }
    const blocked = await $.tool.call(write as never)
    expect(ran).toBe(0)
    expect(asked[0]).toContain('not your recorded neuroflow workbench')
    expect(JSON.stringify(blocked)).toContain('nf-rule: EGRESS-CONFIRM')
    answer = 'Allow — I confirm this myself'
    await $.tool.call(write as never)
    expect(ran).toBe(1)
  })
})
