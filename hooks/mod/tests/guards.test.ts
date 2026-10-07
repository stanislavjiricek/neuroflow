import { describe, expect, mock, test } from 'claude-code/testing'

import type { NfSnapshot } from '../../../types'
import { LOCAL_ONLY, denyText, readViolations, shellViolations, writeViolations } from '../features/guards'
import { fakeFs } from './fakefs'

const snap = (over: Partial<NfSnapshot> = {}): NfSnapshot => ({
  root: '/work/proj',
  nfSchema: 1,
  dialect: 'frontmatter',
  projectName: 'X',
  phase: 'data',
  mode: null,
  recommendedPhases: [],
  rawRoots: ['sourcedata/'],
  paperAuto: false,
  ethics: null,
  prereg: { status: 'frozen', setBy: 'person', setAt: null, frozenAt: '2026-10-01', files: { '.neuroflow/preregistration/prereg-osf.md': 'abc' }, plannedN: 48 },
  deadlines: [],
  phasesVisited: [],
  taskCounts: null,
  loops: [],
  problems: [],
  loadedAt: 0,
  ...over,
})

describe('write rules', () => {
  test('frozen prereg and raw data are denied, with the rule id', () => {
    const frozen = writeViolations('.neuroflow/preregistration/prereg-osf.md', snap(), 'x', null)
    expect(frozen[0].rule).toBe('PREREG-FROZEN')
    expect(denyText(frozen[0])).toContain('[nf-rule: PREREG-FROZEN]')
    const raw = writeViolations('sourcedata/sub-01/eeg/sub-01_task-x_eeg.vhdr', snap(), 'x', null)
    expect(raw[0].rule).toBe('RAW-READONLY')
    expect(raw[0].message).toContain('BrainVision')
    expect(writeViolations('derivatives/sub-01/x.fif', snap(), 'x', null)).toEqual([])
  })

  test('a frozen marker the model set does not lock anything', () => {
    const notByPerson = snap({ prereg: { status: 'frozen', setBy: 'model', setAt: null, frozenAt: null, files: { '.neuroflow/preregistration/prereg-osf.md': 'abc' }, plannedN: null } })
    expect(writeViolations('.neuroflow/preregistration/prereg-osf.md', notByPerson, 'x', null)).toEqual([])
  })

  test('writing set_by: person asks the person', () => {
    const ask = writeViolations('.neuroflow/ethics/status.md', snap(), '---\nstatus: approved\nset_by: person\n---\n', '---\nstatus: pending\nset_by: model\n---\n')
    expect(ask.map(v => [v.rule, v.level])).toEqual([['INTEGRITY-MARKER', 'ask']])
    const unchanged = writeViolations('.neuroflow/ethics/status.md', snap(), '---\nstatus: approved\nset_by: person\nexpires: 2027\n---\n', '---\nstatus: approved\nset_by: person\n---\n')
    expect(unchanged).toEqual([])
  })

  test('memory purity only warns', () => {
    const odd = writeViolations('.neuroflow/my-notes/x.md', snap(), 'x', null)
    expect(odd.map(v => [v.rule, v.level])).toEqual([['MEMORY-PURITY', 'warn']])
    expect(writeViolations('.neuroflow/data-analyze/plan.md', snap(), 'x', null)).toEqual([])
    expect(writeViolations('.neuroflow/poster/poster.pdf', snap(), 'x', null)[0].message).toContain('deliverable')
  })
})

describe('read rule', () => {
  test('participant data is off limits only when the ethics record says so', () => {
    const none = snap({ ethics: { status: 'approved', setBy: 'person', setAt: null, approvalId: null, expires: null, aiProcessing: 'none' } })
    expect(readViolations('sourcedata/sub-01/beh.tsv', none)[0].rule).toBe('PARTICIPANT-ROUTE')
    expect(readViolations('participants.tsv', none)[0].rule).toBe('PARTICIPANT-ROUTE')
    expect(readViolations('scripts/analysis/x.py', none)).toEqual([])
    expect(readViolations('sourcedata/sub-01/beh.tsv', snap())).toEqual([])
  })
})

describe('shell rules', () => {
  const ctx = { gitignore: LOCAL_ONLY.join('\n'), isLoginNode: false }

  test('git', () => {
    expect(shellViolations('git clean -fdx', snap(), ctx)[0].rule).toBe('GIT-NO-SECRETS')
    expect(shellViolations('git clean -n', snap(), ctx)).toEqual([])
    expect(shellViolations('git add .neuroflow/sessions/2026-10-07.md', snap(), ctx)[0].rule).toBe('GIT-NO-SECRETS')
    expect(shellViolations('git add -A && git commit -m x', snap(), ctx)).toEqual([])
    expect(shellViolations('git add -A', snap(), { gitignore: '', isLoginNode: false })[0].message).toContain('.gitignore does not exclude')
  })

  test('raw data, frozen files, uploads, login nodes', () => {
    expect(shellViolations('rm -rf sourcedata/sub-03', snap(), ctx)[0].rule).toBe('RAW-READONLY')
    expect(shellViolations('Remove-Item .\\sourcedata\\sub-03 -Recurse', snap(), ctx)[0].rule).toBe('RAW-READONLY')
    expect(shellViolations('ls sourcedata', snap(), ctx)).toEqual([])
    expect(shellViolations("sed -i 's/48/40/' .neuroflow/preregistration/prereg-osf.md", snap(), ctx)[0].rule).toBe('PREREG-FROZEN')
    expect(shellViolations('notebooklm source add paper.pdf', snap(), ctx)[0].level).toBe('ask')
    expect(shellViolations('python scripts/analysis/connectivity.py', snap(), { ...ctx, isLoginNode: true })[0].rule).toBe('LOGIN-NODE')
    expect(shellViolations('python scripts/analysis/connectivity.py', snap(), ctx)).toEqual([])
  })
})

describe('guards in a session', () => {
  const root = '/work/proj'
  const files = {
    [`${root}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nactive_phase: data\nraw_roots: [sourcedata/]\n---\n',
    [`${root}/.neuroflow/preregistration/status.md`]: '---\nstatus: frozen\nfiles:\n  .neuroflow/preregistration/prereg-osf.md: abc\nset_by: person\n---\n',
    [`${root}/.neuroflow/preregistration/prereg-osf.md`]: '# Prereg',
  }
  const write = { tool: 'Write', file_path: `${root}/.neuroflow/preregistration/prereg-osf.md`, content: '# changed' }

  test('enforce denies the write before the tool runs', { options: { runtime: 'on', guards: 'enforce' } }, async ($, on) => {
    fakeFs(on, files, root)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: 0 })
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    let ran = false
    on('tool.call', () => {
      ran = true
      return { result: 'written', text: 'ok' }
    })
    await $.session.start({ cwd: root, surface: 'terminal', isInteractive: true })
    const result = await $.tool.call(write as never)
    expect(ran).toBe(false)
    expect(JSON.stringify(result)).toContain('nf-rule: PREREG-FROZEN')
  })

  test('observe lets it through and only says so', { options: { runtime: 'observe' } }, async ($, on) => {
    fakeFs(on, files, root)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: 0 })
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    const said: string[] = []
    on('ui.toast', ($, e) => {
      said.push(JSON.stringify(e))
      return { value: undefined }
    })
    on('ui.notice', ($, e) => {
      said.push(JSON.stringify(e))
      return { value: undefined }
    })
    let ran = false
    on('tool.call', () => {
      ran = true
      return { result: 'written', text: 'ok' }
    })
    await $.session.start({ cwd: root, surface: 'terminal', isInteractive: true })
    await $.tool.call(write as never)
    expect(ran).toBe(true)
    expect(said.join(' ')).toContain('would block')
  })
})
