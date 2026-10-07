import type { On } from 'claude-code'
import { describe, expect, mock, test } from 'claude-code/testing'

import type { NfSnapshot } from '../../../types'
import { setActivePhase } from '../lib/config'
import { nextPhase, phaseMap, pickerOrder } from '../lib/phases'
import { bandItems, freezeCandidates, parseOpenQuestions, parseRunning, sparkline, tabLines } from '../features/views'
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
  taskCounts: null,
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
    expect(items.map(item => item.text)).toEqual(['neuroflow 0.2.10 is installed — this project is on 0.2.9 · /neuroflow:migrate'])
    expect(items[0].actions?.map(action => [action.command, action.args, action.hotkey])).toEqual([['neuroflow:migrate', '', 'm']])
    expect(bandItems(snapshot({ pluginVersion: null }), true)[0].text).toContain('this project is on an older version')
    expect(bandItems(snapshot({ pluginVersion: '0.2.23' }), false).some(item => item.text.includes('is installed'))).toBe(false)
    expect(bandItems(snapshot({ runningVersion: null, pluginVersion: '0.2.1' }), false).some(item => item.text.includes('is installed'))).toBe(false)
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
      taskCounts: { inbox: 2, ready: 1, active: 1, review: 0, meeting: 0, done: 4, archive: 0 },
    })
    expect(tabLines('phase', snap, null)[0].text).toBe('✔ ideation  ✔ preregistration  ✔ data  ● data-analyze  ○ paper')
    expect(tabLines('integrity', snap, null)[0].text).toBe('✔ ethics approved · expires 2027-06-30')
    expect(tabLines('tasks', snap, null)[0].text).toBe('inbox 2 · ready 1 · active 1 · review 0 · meeting 0 · done 4 · archive 0')
    expect(tabLines('deadlines', snap, null)[0].dim).toBe(true)
    expect(tabLines('loop', snap, null)[0].text).toBe('No autoresearch loops.')
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
    expect(JSON.stringify(await ui.drawn())).toContain('neuroflow 0.2.22 is installed — this project is on 0.2.21 · /neuroflow:migrate')
    await ui.press({ key: 'nf-migrate' })
    expect(ran).toEqual(['neuroflow:migrate'])
    await ui.unmount()
  })
})

describe('phase switching', () => {
  const project = '/work/proj'
  const setup = (on: On) => {
    const fs = fakeFs(on, {
      [`${project}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nproject_name: Oddball\nactive_phase: data\nrecommended_phases: [data, data-analyze, paper]\n---\n# Notes\n',
    }, project)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: new Date(2026, 9, 7, 9, 30).getTime() })
    mock.store(on)
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('ui.open', () => ({ value: { isPlaced: true } }))
    on('ui.close', () => ({ value: undefined }))
    on('ui.toast', () => ({ value: undefined }))
    return fs
  }

  test('/neuroflow:phase <name> switches at once and logs it', { options: { runtime: 'observe' } }, async ($, on) => {
    const fs = setup(on)
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

  test('the picker switches on a pick', { options: { runtime: 'observe' } }, async ($, on) => {
    const fs = setup(on)
    await $.session.start({ cwd: project, surface: 'terminal', isInteractive: true })
    const opened = await $.command.run({ command: 'neuroflow:phase', args: '' })
    expect(opened.text).toContain('Phase picker open')
    for (const surface of ['terminal', 'desktop'] as const) {
      const ui = await $.ui.mount({
        plugin: 'neuroflow', surface, component: 'Pane', requestId: 'nf-phase',
        props: { title: 'Switch phase', isFocused: true, bodyColumns: 60, placement: 'inline', scroll: { offset: 0, bodyRows: 12 }, view: {} },
      } as never)
      expect(JSON.stringify(await ui.drawn())).toContain('data-analyze — analysis  (recommended)')
      await ui.unmount()
    }
    const ui = await $.ui.mount({
      plugin: 'neuroflow', surface: 'terminal', component: 'Pane', requestId: 'nf-phase',
      props: { title: 'Switch phase', isFocused: true, bodyColumns: 60, placement: 'inline', scroll: { offset: 0, bodyRows: 12 }, view: {} },
    } as never)
    await ui.select({ key: 'nf-phase-select', value: 'data-analyze' })
    expect(fs.files[`${project}/.neuroflow/project_config.md`]).toContain('active_phase: data-analyze\n')
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

  const setUp = (on: On, answer: string): { asked: string[]; ran: string[][] } => {
    const seen = { asked: [] as string[], ran: [] as string[][] }
    fakeFs(on, files, root)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: new Date(2026, 9, 7, 12, 0).getTime() })
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
    await ui.press({ key: 'nf-dash-freeze' })
    expect(seen.asked[0]).toContain('prereg-osf.md')
    const argv = seen.ran.find(item => item.includes('freeze')) ?? []
    expect(argv).toContain('.neuroflow/preregistration/prereg-osf.md')
    expect(argv).not.toContain('.neuroflow/preregistration/review-report.md')
    expect(argv.slice(argv.indexOf('--set-by'), argv.indexOf('--set-by') + 2)).toEqual(['--set-by', 'person'])
  })

  test('any answer but the exact yes freezes nothing', { options: { runtime: 'observe' } }, async ($, on) => {
    const seen = setUp(on, 'Not now')
    await $.session.start({ cwd: root, surface: 'terminal', isInteractive: true })
    await $.command.run({ command: 'neuroflow:dashboard', args: 'integrity' })
    const ui = await $.ui.mount(pane as never)
    await ui.press({ key: 'nf-dash-freeze' })
    expect(seen.ran.filter(item => item.includes('freeze'))).toEqual([])
  })
})
