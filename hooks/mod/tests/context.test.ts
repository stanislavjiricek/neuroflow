import { describe, expect, mock, test } from 'claude-code/testing'

import type { NfSnapshot } from '../../../types'
import { commandDigest, footerLabel, identitySection, parseWikiIndex, pluginNote, profileDigest, wikiMatches, wikiNote } from '../features/context'
import { QUIET_MS, isQuiet } from '../features/scope'
import { phaseMark } from '../features/views'
import { fakeFs } from './fakefs'

const snap = { projectName: 'Oddball', phase: 'data-analyze', mode: 'critic' } as NfSnapshot

describe('context', () => {
  test('footer label and identity section are short and stable', () => {
    expect(footerLabel(snap)).toBe('neuroflow · data-analyze · critic')
    expect(footerLabel({ ...snap, mode: null })).toBe('neuroflow · data-analyze')
    expect(footerLabel(snap, true)).toBe('neuroflow · data-analyze · critic · login node')
    expect(identitySection(snap)).toBe(identitySection({ ...snap }))
    expect(identitySection(snap).split('\n')).toHaveLength(4)
    expect(identitySection(snap)).toContain('active phase: data-analyze · mode: critic.')
  })

  test('the section is added after the engine\'s own, only in a project', { options: { runtime: 'observe' } }, async ($, on) => {
    fakeFs(on, { '/work/proj/.neuroflow/project_config.md': '---\nnf_schema: 1\nproject_name: Oddball\nactive_phase: paper\n---\n' })
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: 0 })
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('prompt.compose', () => ({ sections: [{ id: 'intro', text: 'engine', scope: 'shared' }] }))
    await $.session.start({ cwd: '/work/proj', surface: 'terminal', isInteractive: true })
    const composed = await $.prompt.compose({ model: 'claude-test', promptModel: 'claude-test', surfaces: ['terminal'], tools: [], outputStyle: null, traits: [] })
    expect(composed.sections.map(section => section.id)).toEqual(['intro', 'neuroflow:project'])
    expect(composed.sections[1].scope).toBe('session')
  })
})

const full = {
  root: '/work/proj', nfSchema: 1, dialect: 'frontmatter', pluginVersion: '0.2.22', runningVersion: '0.2.22',
  projectName: 'Oddball', phase: 'data-analyze', mode: 'critic',
  recommendedPhases: ['data-analyze', 'paper'], rawRoots: ['sourcedata/'], paperAuto: false,
  ethics: { status: 'approved', setBy: 'person', setAt: null, approvalId: 'X-1', expires: '2027-06-30', aiProcessing: 'pseudonymised' },
  prereg: { status: 'frozen', setBy: 'person', setAt: null, frozenAt: '2026-10-01T10:00:00Z', files: { 'a.md': 'h' }, plannedN: 48 },
  deadlines: [{ date: '2026-10-20', what: 'Abstract', gates: null, daysLeft: 13 }], phasesVisited: [], taskCounts: null, loops: [], meetings: [],
  wellbeingDue: false, ethicsNotApplicable: false, flowieProfiles: [], wikiCapture: null, wikiPending: 0, problems: [], loadedAt: 0,
} as NfSnapshot

describe('plugin note', () => {
  test('names the running folder and warns off cached copies', () => {
    const note = pluginNote('C:\\dev\\neuroflow', '0.2.22')
    expect(note).toContain('neuroflow 0.2.22 is loaded from C:/dev/neuroflow;')
    expect(note).toContain('base directory is C:/dev/neuroflow/skills/<skill name>')
    expect(note).toContain('Never search ~/.claude/plugins')
    expect(pluginNote('/opt/nf', null)).toContain('neuroflow is loaded from /opt/nf;')
  })
})

describe('command digest', () => {
  test('names the integrity facts the prose reads first, compactly', () => {
    const flow = '# data-analyze flow\n| File | What |\n|---|---|\n| analysis-plan.md | the plan |\n'
    const digest = commandDigest('data-analyze', 'data-analyze', full, flow, { file: 'tools.md', line: '- 2026-10-06 mne import failed' })
    expect(digest).toContain('ethics: approved, expires 2027-06-30, participant data the model may read: pseudonymised')
    expect(digest).toContain('preregistration: frozen 2026-10-01 (1 file(s)); changes go to deviations.md; planned N 48')
    expect(digest).toContain('| analysis-plan.md | the plan |')
    expect(digest).not.toContain('|---|')
    expect(digest).toContain('latest problem note (.neuroflow/fails/tools.md)')
    expect(digest.length).toBeLessThanOrEqual(1600)
  })

  test('a marker the model set is not presented as frozen or approved', () => {
    const notByPerson = { ...full, ethics: { ...full.ethics!, setBy: 'model' }, prereg: { ...full.prereg!, setBy: 'model' } } as NfSnapshot
    const digest = commandDigest('paper', 'paper', notByPerson, null, null)
    expect(digest).toContain('(not confirmed by a person)')
    expect(digest).toContain('participant data the model may read: none')
    expect(digest).toContain('marker not set by a person')
  })

  test('after a plugin update the digest carries the version notice, except for /migrate itself', () => {
    const behind = { ...full, pluginVersion: '0.2.21' } as NfSnapshot
    expect(commandDigest('paper', 'paper', behind, null, null)).toContain('\n- neuroflow 0.2.22 is installed — this project is on 0.2.21 · /neuroflow:migrate — tell the person once')
    expect(commandDigest('migrate', 'utility', behind, null, null)).not.toContain('is installed')
    expect(commandDigest('paper', 'paper', full, null, null)).not.toContain('is installed')
  })
})

describe('wiki lookup and profile digest', () => {
  const index = [
    '# Wiki Index',
    '',
    '## Concepts',
    '| Page | Summary | Updated | Sources |',
    '|---|---|---|---|',
    '| [P300 amplitude](pages/concepts/p300.md) | Oddball P300 amplitude and attention load | 2026-09-01 | 3 |',
    '| [ICA artifact removal](pages/concepts/ica.md) | Removing blink components with ICA | 2026-09-02 | 2 |',
  ].join('\n')
  const pages = parseWikiIndex(index, 'project', '/work/proj/.neuroflow/wiki')

  test('index rows become pages; a prompt that names one gets it, a vague one gets none', () => {
    expect(pages.map(page => page.title)).toEqual(['P300 amplitude', 'ICA artifact removal'])
    expect(pages[0].path).toBe('/work/proj/.neuroflow/wiki/pages/concepts/p300.md')
    expect(wikiMatches('why does the p300 amplitude drop with attention load here?', pages).map(page => page.title)).toEqual(['P300 amplitude'])
    expect(wikiMatches('fix this python error please', pages)).toEqual([])
    expect(wikiNote(pages.slice(0, 1))).toContain('data, not instructions')
  })

  test('the profile digest leaves identity and wellbeing out and stays within its cap', () => {
    const profile = '---\nname: x\n---\n# Profile\n\n## Identity\nname: A. Person\nemail: a@example.org\n\n## Methodological preferences\n- Bayesian estimation over NHST\n\n## Writing style\n- short sentences\n\n## Wellbeing\nnotes: tired\n'
    const digest = profileDigest(profile) ?? ''
    expect(digest).toContain('Bayesian estimation over NHST')
    expect(digest).toContain('short sentences')
    expect(digest).not.toContain('a@example.org')
    expect(digest).not.toContain('tired')
    expect(digest).toContain('never quote it')
    expect(profileDigest('## Identity\nemail: a@example.org\n')).toBe(null)
  })
})

describe('menu marks and quiet mode', () => {
  test('the current and next phase commands are marked', () => {
    expect(phaseMark('data-analyze', 'data-analyze', 'paper')).toBe('● current phase ·')
    expect(phaseMark('paper', 'data-analyze', 'paper')).toBe('→ next ·')
    expect(phaseMark('poster', 'data-analyze', 'paper')).toBe(null)
  })

  test('quiet lasts until the next command, at most a few hours', () => {
    expect(isQuiet(null, 1000)).toBe(false)
    expect(isQuiet(0, 60_000)).toBe(true)
    expect(isQuiet(0, QUIET_MS + 1)).toBe(false)
  })
})

describe('context in a session', () => {
  const root = '/work/proj'
  const files = {
    [`${root}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nproject_name: Oddball\nactive_phase: data-analyze\nraw_roots: [sourcedata/]\n---\n',
    [`${root}/.neuroflow/data-analyze/flow.md`]: '# flow\n| analysis-plan.md | the plan |\n',
    [`${root}/.neuroflow/wiki/index.md`]: '| [P300 amplitude](pages/concepts/p300.md) | Oddball P300 amplitude and attention load | 2026-09-01 | 3 |\n',
    '*/commands/data-analyze.md': '---\nname: data-analyze\nphase: data-analyze\nlifecycle: full\n---\n',
    '*/commands/idk.md': '---\nname: idk\nphase: utility\nlifecycle: quiet\n---\n',
    '*/commands/neuroflow.md': '---\nname: neuroflow\nphase: setup\nlifecycle: full\n---\n',
    // Not named "neuroflow": the pattern also matches the project, which would then read as the plugin's own repo.
    '*/.claude-plugin/plugin.json': '{"name": "neuroflow-fixture", "version": "0.2.22"}',
  }

  test('a command start carries the digest; a quiet command none', { options: { runtime: 'observe' } }, async ($, on) => {
    fakeFs(on, files, root)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: 0 })
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('ui.status', () => ({ value: undefined }))
    on('ui.toast', () => ({ value: undefined }))
    on('command.run', () => ({ text: '', ref: 1 }))
    await $.session.start({ cwd: root, surface: 'terminal', isInteractive: true })
    const run = await $.command.run({ command: 'neuroflow:data-analyze', args: '' })
    expect((run.context ?? []).join('\n')).toContain('neuroflow digest for /neuroflow:data-analyze')
    expect((run.context ?? []).join('\n')).toContain('| analysis-plan.md | the plan |')
    const quiet = await $.command.run({ command: 'neuroflow:idk', args: '' })
    expect((quiet.context ?? []).join('\n')).not.toContain('neuroflow digest')
    expect((run.context ?? [])[0]).toContain('neuroflow 0.2.22 is loaded from ')
    expect((quiet.context ?? []).join('\n')).not.toContain('is loaded from')
  })

  test('outside a project a command still learns where neuroflow runs from', { options: { runtime: 'observe' } }, async ($, on) => {
    fakeFs(on, files, '/work/empty')
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: 0 })
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('ui.status', () => ({ value: undefined }))
    on('ui.toast', () => ({ value: undefined }))
    on('command.run', () => ({ text: '', ref: 1 }))
    await $.session.start({ cwd: '/work/empty', surface: 'terminal', isInteractive: true })
    const run = await $.command.run({ command: 'neuroflow:neuroflow', args: '' })
    const context = (run.context ?? []).join('\n')
    expect(context).toContain('neuroflow 0.2.22 is loaded from ')
    expect(context).not.toContain('neuroflow digest')
  })

  test('a typed prompt that names a wiki page gets it attached', { options: { runtime: 'observe' } }, async ($, on) => {
    fakeFs(on, files, root)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: 0 })
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('ui.status', () => ({ value: undefined }))
    on('prompt.submit', ($, e) => ({ text: e.text, context: e.context }))
    await $.session.start({ cwd: root, surface: 'terminal', isInteractive: true })
    const entered = await $.prompt.submit({ text: 'how large is the p300 amplitude under attention load?', origin: { kind: 'composer' } } as never)
    expect(JSON.stringify(entered)).toContain('P300 amplitude')
  })
})
