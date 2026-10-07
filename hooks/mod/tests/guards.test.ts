import { describe, expect, mock, test } from 'claude-code/testing'

import type { NfSnapshot } from '../../../types'
import {
  DEFAULT_STRUCTURE,
  LOCAL_ONLY,
  afterEdit,
  denyText,
  isHeavy,
  participantRoute,
  readViolations,
  shellViolations,
  structureFrom,
  writeViolations,
} from '../features/guards'
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
  meetings: [],
  wellbeingDue: false,
  ethicsNotApplicable: false,
  problems: [],
  loadedAt: 0,
  ...over,
})

const ethics = (aiProcessing: string | null, setBy: string | null = 'person'): Partial<NfSnapshot> => ({
  ethics: { status: 'approved', setBy, setAt: null, approvalId: null, expires: null, aiProcessing },
})

const existing = { exists: true }
const created = { exists: false }

describe('write rules', () => {
  test('frozen prereg and existing raw files are denied, with the rule id', () => {
    const frozen = writeViolations('.neuroflow/preregistration/prereg-osf.md', snap(), 'x', null, existing)
    expect(frozen[0].rule).toBe('PREREG-FROZEN')
    expect(denyText(frozen[0])).toContain('[nf-rule: PREREG-FROZEN]')
    const raw = writeViolations('sourcedata/sub-01/eeg/sub-01_task-x_eeg.vhdr', snap(), 'x', null, existing)
    expect(raw[0].rule).toBe('RAW-READONLY')
    expect(raw[0].message).toContain('BrainVision')
    expect(writeViolations('derivatives/sub-01/x.fif', snap(), 'x', null, existing)).toEqual([])
  })

  test('new recordings may be added under a raw root', () => {
    expect(writeViolations('sourcedata/sub-09/beh/sub-09_task-x_beh.tsv', snap(), 'x', null, created)).toEqual([])
  })

  test('while raw_roots is unset, sourcedata/ is the raw folder', () => {
    expect(writeViolations('sourcedata/sub-01/beh.tsv', snap({ rawRoots: [] }), 'x', null, existing)[0].rule).toBe('RAW-READONLY')
    expect(writeViolations('recordings/sub-01.vhdr', snap({ rawRoots: ['recordings/'] }), 'x', null, existing)[0].rule).toBe('RAW-READONLY')
    expect(writeViolations('sourcedata/sub-01/beh.tsv', snap({ rawRoots: ['recordings/'] }), 'x', null, existing)).toEqual([])
    expect(shellViolations('rm sourcedata/sub-01/beh.tsv', snap({ rawRoots: [] }), { gitignore: null, isLoginNode: false })[0].rule).toBe('RAW-READONLY')
  })

  test('the deviation log is append-only while frozen', () => {
    const path = '.neuroflow/preregistration/deviations.md'
    const before = '# Deviations\n\n## 2026-10-02 — N changed\nReason: dropout.\n'
    expect(writeViolations(path, snap(), `${before}\n## 2026-10-05 — filter\nReason: line noise.\n`, before, existing)).toEqual([])
    const rewritten = writeViolations(path, snap(), before.replace('dropout', 'a typo'), before, existing)
    expect(rewritten.map(v => [v.rule, v.level])).toEqual([['PREREG-FROZEN', 'deny']])
    expect(writeViolations(path, snap({ prereg: null }), 'anything', before, existing)).toEqual([])
  })

  test('a frozen marker the model set does not lock anything', () => {
    const notByPerson = snap({ prereg: { status: 'frozen', setBy: 'model', setAt: null, frozenAt: null, files: { '.neuroflow/preregistration/prereg-osf.md': 'abc' }, plannedN: null } })
    expect(writeViolations('.neuroflow/preregistration/prereg-osf.md', notByPerson, 'x', null, existing)).toEqual([])
  })

  test('writing set_by: person asks the person', () => {
    const ask = writeViolations('.neuroflow/ethics/status.md', snap(), '---\nstatus: approved\nset_by: person\n---\n', '---\nstatus: pending\nset_by: model\n---\n', existing)
    expect(ask.map(v => [v.rule, v.level])).toEqual([['INTEGRITY-MARKER', 'ask']])
    const unchanged = writeViolations('.neuroflow/ethics/status.md', snap(), '---\nstatus: approved\nset_by: person\nexpires: 2027\n---\n', '---\nstatus: approved\nset_by: person\n---\n', existing)
    expect(unchanged).toEqual([])
  })

  test('memory purity only warns, against the documented structure', () => {
    const odd = writeViolations('.neuroflow/my-notes/x.md', snap(), 'x', null, created)
    expect(odd.map(v => [v.rule, v.level])).toEqual([['MEMORY-PURITY', 'warn']])
    expect(writeViolations('.neuroflow/data-analyze/plan.md', snap(), 'x', null, created)).toEqual([])
    expect(writeViolations('.neuroflow/poster/poster.pdf', snap(), 'x', null, created)[0].message).toContain('deliverable')
    const listed = { exists: false, structure: { rootFiles: ['project_config.md'], rootFolders: ['my-notes'] } }
    expect(writeViolations('.neuroflow/my-notes/x.md', snap(), 'x', null, listed)).toEqual([])
    expect(writeViolations('.neuroflow/timeline.md', snap(), 'x', null, listed)[0].rule).toBe('MEMORY-PURITY')
  })

  test('the structure comes from nf_check.py --structure when it answers', () => {
    expect(structureFrom(null)).toBe(null)
    expect(structureFrom({ documented: false, root_files: [], root_folders: [] })).toBe(null)
    const listed = structureFrom({ documented: true, root_files: ['flow.md'], root_folders: ['sessions'], phase_folders: ['data'] })
    expect(listed).toEqual({ rootFiles: ['flow.md', '.gitkeep'], rootFolders: ['sessions', 'data'] })
    expect(DEFAULT_STRUCTURE.rootFolders).toContain('data-analyze')
  })

  test('the file after an edit is what the rules compare', () => {
    expect(afterEdit({ content: 'new' }, 'old')).toBe('new')
    expect(afterEdit({ old_string: 'b', new_string: '$&$&' }, 'abc')).toBe('a$&$&c')
    expect(afterEdit({ old_string: 'a', new_string: 'x', replace_all: true }, 'aXa')).toBe('xXx')
    expect(afterEdit({ edits: [{ old_string: 'a', new_string: 'b' }, { old_string: 'b', new_string: 'c' }] }, 'a')).toBe('c')
    expect(afterEdit({ old_string: 'a', new_string: 'b' }, null)).toBe(null)
  })
})

describe('read rule', () => {
  test('participant data is off limits when the ethics record keeps it from the model', () => {
    const none = snap(ethics('none'))
    expect(readViolations('sourcedata/sub-01/beh.tsv', none)[0].level).toBe('deny')
    expect(readViolations('participants.tsv', none)[0].rule).toBe('PARTICIPANT-ROUTE')
    expect(readViolations('scripts/analysis/x.py', none)).toEqual([])
    expect(readViolations('sourcedata/sub-01/eeg/sub-01_task-x_eeg.json', none)).toEqual([])
    expect(readViolations('participants.tsv', none, true)).toEqual([])
  })

  test('a missing field or a model-set marker counts as none', () => {
    expect(participantRoute(snap(ethics(null)))).toBe('deny')
    expect(participantRoute(snap(ethics('identifiable', 'model')))).toBe('deny')
    expect(readViolations('sourcedata/x.tsv', snap(ethics('pseudonymised', 'model')))[0].message).toContain('not confirmed by a person')
  })

  test('approval, not-applicable and no record', () => {
    expect(readViolations('sourcedata/sub-01/beh.tsv', snap(ethics('pseudonymised')))).toEqual([])
    expect(readViolations('sourcedata/sub-01/beh.tsv', snap({ ethicsNotApplicable: true }))).toEqual([])
    const unknown = readViolations('sourcedata/sub-01/beh.tsv', snap())
    expect(unknown.map(v => [v.rule, v.level])).toEqual([['PARTICIPANT-ROUTE', 'warn']])
  })

  test('without raw_roots, sourcedata/ still holds participant data', () => {
    expect(readViolations('sourcedata/sub-01/beh.tsv', snap({ rawRoots: [], ...ethics('none') }))[0].level).toBe('deny')
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

  test('git -C forms, work-discarding commands, and alias scope', () => {
    expect(shellViolations('git -C ../other clean -xdf', snap(), ctx)[0].rule).toBe('GIT-NO-SECRETS')
    expect(shellViolations('git reset --hard HEAD~1', snap(), ctx)[0].level).toBe('ask')
    expect(shellViolations('git push --force origin main', snap(), ctx)[0].level).toBe('ask')
    expect(shellViolations('git reset -q -- .neuroflow/sessions/x.md', snap(), ctx)).toEqual([])
    const ac = { ...ctx, gitAlias: 'ac' }
    expect(shellViolations('git add . && git reset -q -- integrations.json && git commit -m "x"', snap(), ac)).toEqual([])
    expect(shellViolations('git push origin main', snap(), ac)[0].rule).toBe('GIT-ALIAS-SCOPE')
    expect(shellViolations('git -C . pull --rebase', snap(), ac)[0].rule).toBe('GIT-ALIAS-SCOPE')
    expect(shellViolations('git push', snap(), { ...ctx, gitAlias: 'acp' })).toEqual([])
    expect(shellViolations('gh pr create --fill', snap(), { ...ctx, gitAlias: 'acp' })[0].rule).toBe('GIT-ALIAS-SCOPE')
    expect(shellViolations('git push origin main', snap(), ctx)).toEqual([])
  })

  test('raw data, frozen files, uploads', () => {
    expect(shellViolations('rm -rf sourcedata/sub-03', snap(), ctx)[0].rule).toBe('RAW-READONLY')
    expect(shellViolations('Remove-Item .\\sourcedata\\sub-03 -Recurse', snap(), ctx)[0].rule).toBe('RAW-READONLY')
    expect(shellViolations('ls sourcedata', snap(), ctx)).toEqual([])
    expect(shellViolations("sed -i 's/48/40/' .neuroflow/preregistration/prereg-osf.md", snap(), ctx)[0].rule).toBe('PREREG-FROZEN')
    expect(shellViolations('notebooklm source add paper.pdf', snap(), ctx)[0].level).toBe('ask')
  })

  test('printing participant data follows the ethics record; sidecars and listings are fine', () => {
    const none = snap(ethics('none'))
    expect(shellViolations('cat sourcedata/sub-01/beh/sub-01_beh.tsv', none, ctx)[0].rule).toBe('PARTICIPANT-ROUTE')
    expect(shellViolations('head -5 ./sourcedata/sub-01/beh/sub-01_beh.tsv | wc -l', none, ctx)[0].rule).toBe('PARTICIPANT-ROUTE')
    expect(shellViolations('cat sourcedata/sub-01/eeg/sub-01_task-x_eeg.json', none, ctx)).toEqual([])
    expect(shellViolations('ls sourcedata/sub-01', none, ctx)).toEqual([])
    expect(shellViolations('cat sourcedata/sub-01/beh/sub-01_beh.tsv', snap(ethics('pseudonymised')), ctx)).toEqual([])
  })

  test('heavy compute on a login node asks', () => {
    const login = { ...ctx, isLoginNode: true }
    expect(shellViolations('python scripts/analysis/connectivity.py', snap(), login).map(v => [v.rule, v.level])).toEqual([['LOGIN-NODE', 'ask']])
    expect(shellViolations('python skills/phase-brain-run/scripts/sweep_run.py grid.json', snap(), login)[0].rule).toBe('LOGIN-NODE')
    expect(shellViolations('python scripts/analysis/connectivity.py', snap(), ctx)).toEqual([])
    expect(shellViolations('python -m pip install mne', snap(), login)).toEqual([])
    expect(isHeavy('sbatch job-slurm.sh')).toBe(false)
  })
})

describe('guards in a session', () => {
  const root = '/work/proj'
  const files = {
    [`${root}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nactive_phase: data\nraw_roots: [sourcedata/]\n---\n',
    [`${root}/.neuroflow/preregistration/status.md`]: '---\nstatus: frozen\nfiles:\n  .neuroflow/preregistration/prereg-osf.md: abc\nset_by: person\n---\n',
    [`${root}/.neuroflow/preregistration/prereg-osf.md`]: '# Prereg',
    [`${root}/sourcedata/sub-01/beh.tsv`]: 'id\tscore\n1\t3\n',
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

  test('a new file under a raw root goes through', { options: { runtime: 'on', guards: 'enforce' } }, async ($, on) => {
    fakeFs(on, files, root)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: 0 })
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    let ran = 0
    on('tool.call', () => {
      ran += 1
      return { result: 'written', text: 'ok' }
    })
    await $.session.start({ cwd: root, surface: 'terminal', isInteractive: true })
    await $.tool.call({ tool: 'Write', file_path: `${root}/sourcedata/sub-02/beh.tsv`, content: 'id\n2\n' } as never)
    expect(ran).toBe(1)
    const denied = await $.tool.call({ tool: 'Write', file_path: `${root}/sourcedata/sub-01/beh.tsv`, content: 'id\n9\n' } as never)
    expect(ran).toBe(1)
    expect(JSON.stringify(denied)).toContain('nf-rule: RAW-READONLY')
  })

  test('a changed frozen file shows on the status line at start', { options: { runtime: 'on' } }, async ($, on) => {
    fakeFs(on, files, root)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: 0 })
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('process.run', ($, e) => ({
      value: /freeze\.py/.test(JSON.stringify(e))
        ? { exitCode: 1, stdout: JSON.stringify({ status: 'frozen', findings: [{ kind: 'changed' }] }), stderr: '' }
        : { exitCode: 2, stdout: '', stderr: 'x' },
    }))
    const shown: string[] = []
    on('ui.status', ($, e) => {
      shown.push(JSON.stringify(e))
      return { value: undefined }
    })
    await $.session.start({ cwd: root, surface: 'terminal', isInteractive: true })
    expect(shown.join(' ')).toContain('frozen preregistration changed')
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
