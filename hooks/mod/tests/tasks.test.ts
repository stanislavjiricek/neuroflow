import type { On } from 'claude-code'
import { describe, expect, mock, test } from 'claude-code/testing'

import {
  DEFAULT_COLUMNS,
  hiveFolderOf,
  legacyColumn,
  levelArgs,
  levelCardLine,
  levelSummary,
  linkedProject,
  loadTaskView,
  locationKey,
  moveCommand,
  moveTargets,
  openingLevel,
  orderHives,
  originUrl,
  registryProject,
  repoKey,
  topCards,
  userHives,
} from '../lib/tasks'
import { boardRingTarget, cardKeys, firstTarget, taskLines } from '../features/views'
import { buttons, elements, lines } from './drawn'
import { fakeFs } from './fakefs'
import type { FakeFs } from './fakefs'
import { memIo } from './memio'

const HOME = '/home/me'
const ROOT = '/work/oddball'
const task = (title: string, extra = ''): string => `---\ntitle: ${title}\nstatus: x\n${extra}created: 2026-09-01\n---\nnotes\n`

/** A project, a flowie and three hive clones, as the person's machine holds them. */
const FILES: Record<string, string> = {
  [`${ROOT}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nproject_name: Oddball\nactive_phase: data\n---\n',
  [`${ROOT}/.neuroflow/tasks/active/rerun-ica.md`]: task('Rerun ICA', 'owner: li\ndue: 2026-10-01\n'),
  [`${ROOT}/.git/config`]: '[core]\n\tbare = false\n[remote "upstream"]\n\turl = https://github.com/someone/else.git\n[remote "origin"]\n\turl = git@github.com:example-lab/oddball-eeg.git\n',
  [`${HOME}/.neuroflow/flowie/.git/HEAD`]: 'ref: refs/heads/main\n',
  [`${HOME}/.neuroflow/flowie/tasks/inbox/read-paper.md`]: task('Read paper', 'due: 2026-10-20\nproject: Oddball EEG\n'),
  [`${HOME}/.neuroflow/flowie/tasks/active/write-intro.md`]: task('Write intro', 'due: 2026-10-02\nproject: Thesis\n'),
  [`${HOME}/.neuroflow/flowie/tasks/review/check-stats.md`]: task('Check stats', 'due: 2026-10-03\nproject: Oddball EEG\n'),
  [`${HOME}/.neuroflow/flowie/tasks/review/.flow`]: '# review\n',
  // Done tasks are counted, never read: these are not even task files.
  [`${HOME}/.neuroflow/flowie/tasks/done/old-1.md`]: 'not a task file',
  [`${HOME}/.neuroflow/flowie/tasks/done/old-2.md`]: 'not a task file',
  [`${HOME}/.neuroflow/flowie/projects/projects.json`]: JSON.stringify({
    projects: [
      { id: 'Thesis', repos: ['/work/thesis'] },
      { id: 'Oddball EEG', repos: [{ url: 'https://github.com/Example-Lab/oddball-eeg', description: 'analysis' }] },
    ],
  }),
  // A hive task's `project:` names the lab project of the hive's own registry, which lists this repo under its own
  // id; the flowie's name for the project means nothing there.
  [`${HOME}/.neuroflow/hives/lab-team/projects/projects.json`]: JSON.stringify({
    projects: [{ id: 'oddball-lab', repos: [{ url: 'https://github.com/example-lab/oddball-eeg.git' }] }, { id: 'other-lab', repos: [] }],
  }),
  [`${HOME}/.neuroflow/hives/lab-team/tasks/meeting/agenda-item.md`]: task('Agenda item', 'project: oddball-lab\nowner: jana\n'),
  [`${HOME}/.neuroflow/hives/lab-team/tasks/inbox/review-poster.md`]: task('Review poster', 'project: Oddball EEG\n'),
  [`${HOME}/.neuroflow/hives/another-team/tasks/inbox/.gitkeep`]: '',
  [`${HOME}/.neuroflow/hives/alpha-team/tasks/done/shipped.md`]: task('Shipped'),
  [`${HOME}/.neuroflow/hives/no-tasks/hive.md`]: '# a hive without a board\n',
  [`${HOME}/.neuroflow/user.yaml`]: 'flowie_handle: me\nhives:\n  - repo: example-lab/hive\n    local: ~/.neuroflow/hives/lab-team\n\n# a comment\nwriting_style: plain\n',
}

const TODAY = '2026-10-07'

describe('which levels and in which order', () => {
  test('user.yaml lists hives as org/repo strings or as maps with a local folder (neuroflow-core → Personal layer)', () => {
    expect(userHives('hives: [example-lab/hive, "other-org/team-hive"]\n')).toEqual(['example-lab-hive', 'other-org-team-hive'])
    expect(userHives('name: x\nhives:\n  - example-lab/hive\n  - https://github.com/acme/brains.git\nother: 1\n')).toEqual(['example-lab-hive', 'acme-brains'])
    expect(userHives('hives:\n- repo: example-lab/hive\n  local: C:\\Users\\me\\.neuroflow\\hives\\lab-team\n- repo: acme/brains\n')).toEqual(['lab-team', 'acme-brains'])
    // Keys the contract does not define are not read.
    expect(userHives('hives:\n  - url: https://github.com/acme/brains\n  - name: lab\n    path: /somewhere/else\n')).toEqual([])
    expect(userHives('hives: []\n')).toEqual([])
    expect(userHives('flowie_handle: me\n')).toEqual([])
    expect(userHives(null)).toEqual([])
    expect(hiveFolderOf({ repo: 'git@github.com:acme/brains.git', local: null })).toBe('acme-brains')
    expect(hiveFolderOf({ repo: 'lab-team', local: null })).toBe('lab-team')
  })

  test('listed hives first, in their order, then the others alphabetically', () => {
    expect(orderHives(['zeta', 'Alpha', 'lab-team', 'beta'], ['lab-team', 'missing', 'zeta'])).toEqual(['lab-team', 'zeta', 'Alpha', 'beta'])
  })
})

describe('this project', () => {
  test('one repository, many spellings; nothing fuzzier', () => {
    const key = locationKey('git@github.com:Example-Lab/oddball-eeg.git', HOME)
    expect(locationKey('https://github.com/example-lab/oddball-eeg', HOME)).toBe(key)
    expect(locationKey('https://user@github.com/example-lab/oddball-eeg.git/', HOME)).toBe(key)
    expect(locationKey('ssh://git@github.com/example-lab/oddball-eeg.git', HOME)).toBe(key)
    expect(locationKey('https://github.com/example-lab/oddball', HOME)).not.toBe(key)
    expect(locationKey('C:\\Work\\Oddball\\', HOME)).toBe(locationKey('c:/work/oddball', HOME))
    expect(locationKey('~/code/oddball', HOME)).toBe('/home/me/code/oddball')
    expect(locationKey('/work/Oddball', HOME)).not.toBe(locationKey('/work/oddball', HOME))
    expect(originUrl(FILES[`${ROOT}/.git/config`])).toBe('git@github.com:example-lab/oddball-eeg.git')
    expect(originUrl('[core]\n\tbare = false\n')).toBe(null)
  })

  test('local-projects.json first, then a projects.json repo that is this folder or its origin', async () => {
    expect(await linkedProject(memIo(FILES, { home: HOME }), ROOT, HOME)).toBe('Oddball EEG')
    const local = memIo({ ...FILES, [`${HOME}/.neuroflow/local-projects.json`]: JSON.stringify({ projects: [{ name: 'Pilot', path: '/work/oddball/' }] }) }, { home: HOME })
    expect(await linkedProject(local, ROOT, HOME)).toBe('Pilot')
    const byFolder = memIo({ ...FILES, [`${HOME}/.neuroflow/flowie/projects/projects.json`]: JSON.stringify({ projects: [{ id: 'Thesis', repos: ['/work/oddball'] }] }) }, { home: HOME })
    expect(await linkedProject(byFolder, ROOT, HOME)).toBe('Thesis')
    const none = memIo({ ...FILES, [`${ROOT}/.git/config`]: '[remote "origin"]\n\turl = https://github.com/example-lab/other.git\n' }, { home: HOME })
    expect(await linkedProject(none, ROOT, HOME)).toBe(null)
    // A worktree's .git file leads to the main repository's config, and its origin.
    const worktree = memIo({
      ...FILES,
      '/work/wt/.git': 'gitdir: /work/oddball/.git/worktrees/wt\n',
      '/work/oddball/.git/worktrees/wt/commondir': '../..\n',
      '/work/wt/.neuroflow/project_config.md': '---\nnf_schema: 1\n---\n',
    }, { home: HOME })
    expect(await linkedProject(worktree, '/work/wt', HOME)).toBe('Oddball EEG')
  })
})

describe('the task view', () => {
  test('every level counted; this project first, overdue first, then by due date', async () => {
    const view = await loadTaskView(memIo(FILES, { home: HOME }), ROOT, HOME, TODAY)
    expect(view.levels.map(level => level.id)).toEqual(['project', 'flowie', 'hive:lab-team', 'hive:alpha-team', 'hive:another-team'])
    // This project's name per level: one card id everywhere (the flowie's link here), except a hive whose own
    // registry lists this repo under another name (written before one card per project).
    expect(view.levels.map(level => level.project)).toEqual([null, 'Oddball EEG', 'oddball-lab', 'Oddball EEG', 'Oddball EEG'])
    expect(view.card).toBe('Oddball EEG')
    expect(levelSummary(view)).toBe('project 1 · flowie 3 (2 Oddball EEG) · lab-team 2 (1 oddball-lab) · alpha-team 0 · another-team 0')
    // At hive level the flowie's name marks nothing: no name guessing across registries.
    expect(view.levels[2]?.board.columns.find(column => column.id === 'inbox')?.cards.map(card => [card.slug, card.isMine])).toEqual([['review-poster', false]])
    const flowie = view.levels[1]
    expect(flowie.board.done).toBe(2)
    expect(flowie.board.columns.map(column => column.id)).toEqual(['inbox', 'active', 'review'])
    expect(topCards(view).map(({ level, card }) => `${level.name}:${card.slug}`)).toEqual([
      'project:rerun-ica',
      'flowie:check-stats',
      'flowie:read-paper',
      'lab-team:agenda-item',
      'flowie:write-intro',
    ])
    expect(openingLevel(view)).toBe('project')
  })

  test('a flowie pointer leads to the hive card, whose other repositories show from the cache, read-only', async () => {
    const io = memIo({
      [`${ROOT}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\n---\n',
      [`${ROOT}/.git/config`]: '[remote "origin"]\n\turl = git@github.com:example-lab/oddball-eeg.git\n',
      [`${HOME}/.neuroflow/flowie/projects/projects.json`]: JSON.stringify({ projects: [{ id: 'Oddball', ref: 'hive:example-lab/hive' }] }),
      [`${HOME}/.neuroflow/flowie/tasks/inbox/read.md`]: task('Read', 'project: Oddball\n'),
      [`${HOME}/.neuroflow/hives/lab-team/projects/projects.json`]: JSON.stringify({
        projects: [{ id: 'Oddball', repos: ['https://github.com/example-lab/oddball-eeg', { url: 'https://github.com/Example-Lab/oddball-analysis.git' }, 'C:/Users/me/oddball'] }],
      }),
      [`${HOME}/.neuroflow/hives/lab-team/tasks/inbox/plan.md`]: task('Plan', 'project: Oddball\n'),
      [`${HOME}/.neuroflow/boards/github.com/example-lab/oddball-analysis/.neuroflow/tasks/active/rerun.md`]: task('Rerun', 'owner: li\n'),
      [`${HOME}/.neuroflow/boards/github.com/example-lab/oddball-analysis/.neuroflow-fetched`]: '2026-10-18T20:00:00Z\n',
    }, { home: HOME })
    const view = await loadTaskView(io, ROOT, HOME, TODAY)
    expect([view.card, view.hasRemote]).toEqual(['Oddball', true])
    expect(view.levels.map(level => [level.id, level.project, level.mine])).toEqual([
      ['project', null, 0],
      ['flowie', 'Oddball', 1],
      ['hive:lab-team', 'Oddball', 1],
      ['remote:github.com/example-lab/oddball-analysis', 'Oddball', 1],
    ])
    const remote = view.levels[3]
    expect([remote.kind, remote.name, remote.fetched]).toEqual(['remote', 'example-lab/oddball-analysis', '2026-10-18T20:00:00Z'])
    expect(levelCardLine(remote.top[0], remote.kind)).toBe('Rerun @li')
    expect(levelSummary(view)).toBe('project 0 · flowie 1 (1 Oddball) · lab-team 1 (1 Oddball) · example-lab/oddball-analysis 1')
    expect(repoKey('git@github.com:Example-Lab/Oddball.git')).toBe('github.com/example-lab/oddball')
    expect(repoKey('C:/Users/me/oddball')).toBe(null)
  })

  test('the pane opens where the work is', async () => {
    const empty = { ...FILES }
    delete empty[`${ROOT}/.neuroflow/tasks/active/rerun-ica.md`]
    const view = await loadTaskView(memIo(empty, { home: HOME }), ROOT, HOME, TODAY)
    expect(openingLevel(view)).toBe('flowie')
    const unlinked = await loadTaskView(memIo({ ...empty, [`${ROOT}/.git/config`]: '' }, { home: HOME }), ROOT, HOME, TODAY)
    expect(unlinked.levels.every(level => level.project === null)).toBe(true)
    expect(levelSummary(unlinked)).toBe('project 0 · flowie 3 · lab-team 2 · alpha-team 0 · another-team 0')
    expect(openingLevel(unlinked)).toBe('flowie')
    const alone = await loadTaskView(memIo({ [`${ROOT}/.neuroflow/project_config.md`]: '---\n---\n' }, { home: HOME }), ROOT, HOME, TODAY)
    expect(alone.levels.map(level => level.id)).toEqual(['project'])
    expect(openingLevel(alone)).toBe('project')
  })

  test('legacy flat task files count in the column their status names', async () => {
    const io = memIo({
      [`${HOME}/.neuroflow/flowie/tasks/12-old-style.md`]: '---\ntitle: Old style\nstatus: active\nproject: Oddball EEG\n---\n',
      [`${HOME}/.neuroflow/flowie/tasks/13-gone.md`]: '---\ntitle: Gone\nstatus: archived\n---\n',
      [`${HOME}/.neuroflow/flowie/tasks/README.md`]: '# not a task\n',
    }, { home: HOME })
    const view = await loadTaskView(io, ROOT, HOME, TODAY)
    const flowie = view.levels.find(level => level.kind === 'flowie')
    expect(flowie?.open).toBe(1)
    expect(flowie?.board.archived).toBe(1)
    expect(flowie?.board.columns.find(column => column.id === 'active')?.cards[0].title).toBe('Old style')
  })

  test('a legacy file with a closed status is never open, whatever the board calls its closed columns', async () => {
    const custom = [
      { id: 'todo', label: 'todo', archive: false },
      { id: 'doing', label: 'doing', archive: false },
      { id: 'finished', label: 'finished', archive: true },
    ]
    expect(legacyColumn('archived', custom)?.id).toBe('finished')
    expect(legacyColumn('done', custom)?.id).toBe('finished')
    expect(legacyColumn('Doing', custom)?.id).toBe('doing')
    expect(legacyColumn('someday', custom)?.id).toBe('todo')
    expect(legacyColumn(null, custom)?.id).toBe('todo')
    expect(legacyColumn('done', DEFAULT_COLUMNS)?.id).toBe('done')
    expect(legacyColumn('archived', DEFAULT_COLUMNS)?.id).toBe('archive')
    expect(legacyColumn('archived', custom.slice(0, 2))).toBe(null)
    const io = memIo({
      [`${HOME}/.neuroflow/flowie/tasks/config.json`]: JSON.stringify({ columns: custom }),
      [`${HOME}/.neuroflow/flowie/tasks/todo/new-style.md`]: task('New style'),
      [`${HOME}/.neuroflow/flowie/tasks/1-open.md`]: '---\ntitle: Open\nstatus: doing\n---\n',
      [`${HOME}/.neuroflow/flowie/tasks/2-archived.md`]: '---\ntitle: Archived\nstatus: archived\n---\n',
      [`${HOME}/.neuroflow/flowie/tasks/3-done.md`]: '---\ntitle: Done\nstatus: done\n---\n',
      // A board with open columns only: a closed legacy file is counted as done, never drawn.
      [`${HOME}/.neuroflow/hives/lab/tasks/config.json`]: JSON.stringify({ columns: custom.slice(0, 2) }),
      [`${HOME}/.neuroflow/hives/lab/tasks/4-done.md`]: '---\ntitle: Done too\nstatus: done\n---\n',
    }, { home: HOME })
    const view = await loadTaskView(io, ROOT, HOME, TODAY)
    const flowie = view.levels.find(level => level.kind === 'flowie')
    expect([flowie?.open, flowie?.board.archived, flowie?.board.done]).toEqual([2, 2, 0])
    const hive = view.levels.find(level => level.kind === 'hive')
    expect([hive?.open, hive?.board.done]).toEqual([0, 1])
  })

  test('the tasks tab: a line of counts, then the first cards, each tagged with its level', async () => {
    const lines = taskLines(await loadTaskView(memIo(FILES, { home: HOME }), ROOT, HOME, TODAY))
    expect(lines.map(line => line.text)).toEqual([
      'project 1 · flowie 3 (2 Oddball EEG) · lab-team 2 (1 oddball-lab) · alpha-team 0 · another-team 0',
      '[project] ⚠ Rerun ICA @li due 10-01',
      '[flowie] ◆ ⚠ Check stats due 10-03',
      '[flowie] ◆ Read paper due 10-20',
      '[lab-team] ◆ Agenda item @jana',
      '[flowie] ⚠ Write intro due 10-02',
      '◆ this project (Oddball EEG, oddball-lab) · ⚠ overdue · /neuroflow:tasks opens the boards (digits pick the level)',
    ])
    expect(lines[1].tone).toBe('warning')
  })

  test('a move names the level the way /tasks takes it', () => {
    expect(moveCommand({ kind: 'project', name: 'project' }, 'rerun-ica', 'review')).toBe('/neuroflow:tasks --move rerun-ica review')
    expect(moveCommand({ kind: 'flowie', name: 'flowie' }, 'read-paper', 'active')).toBe('/neuroflow:tasks --level flowie --move read-paper active')
    expect(levelArgs({ kind: 'hive', name: 'lab-team' })).toBe(' --level hive --hive lab-team')
  })
})

describe('the boards in a session', () => {
  const pane = (requestId: string, rows = 24) => ({
    plugin: 'neuroflow', surface: 'terminal', component: 'Pane', requestId,
    props: { title: requestId, isFocused: true, bodyColumns: 140, placement: 'inline', scroll: { offset: 0, bodyRows: rows }, view: {} },
  })

  type Seen = { filled: string[]; ran: string[]; toasts: string[]; fs: FakeFs; clock: ReturnType<typeof mock.clock> }
  const setUp = (on: On, files: Record<string, string> = FILES): Seen => {
    const fs = fakeFs(on, files, ROOT)
    mock.env(on, { HOME })
    const clock = mock.clock(on, { now: new Date(2026, 9, 7, 9, 0).getTime() })
    mock.store(on)
    const seen: Seen = { filled: [], ran: [], toasts: [], fs, clock }
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('ui.open', () => ({ value: { isPlaced: true } }))
    on('ui.close', () => ({ value: undefined }))
    on('ui.toast', ($, e) => {
      seen.toasts.push(JSON.stringify(e))
      return { value: undefined }
    })
    on('ui.status', () => ({ value: undefined }))
    // The person's Tab, as the engine raises it; the kit has no ring of its own, so the mod's $.ui.focus calls
    // are not answered there (their target is checked purely: boardRingTarget).
    on('ui.focus', () => ({}))
    on('turn.complete', () => ({ text: 'done' }))
    on('command.run', ($, e) => {
      seen.ran.push(`${e.command} ${e.args}`.trim())
      return { text: '', ref: 1 }
    })
    on('prompt.fill', ($, e) => {
      seen.filled.push(e.text)
      return { isFilled: true, text: e.text, cursor: e.text.length }
    })
    return seen
  }

  test('the dashboard\'s tasks tab shows every level', { options: { runtime: 'observe' } }, async ($, on) => {
    setUp(on)
    await $.session.start({ cwd: ROOT, surface: 'terminal', isInteractive: true })
    await $.command.run({ command: 'neuroflow:dashboard', args: 'tasks' } as never)
    const ui = await $.ui.mount(pane('nf-dashboard') as never)
    const drawn = JSON.stringify(await ui.drawn())
    expect(drawn).toContain('project 1 · flowie 3 (2 Oddball EEG) · lab-team 2 (1 oddball-lab) · alpha-team 0 · another-team 0')
    // The first cards in columns: marks, title, due date, level.
    const rows = lines(await ui.drawn())
    for (const cell of ['◆ ⚠', 'Check stats', 'due 10-03', 'flowie']) expect(rows).toContain(cell)
    expect(rows).toContain('◆ this project (Oddball EEG, oddball-lab) · ⚠ overdue')
    await ui.unmount()
  })

  test('/neuroflow:tasks: digits pick the level; Enter on a card and a target runs the move at project and flowie level and only fills a hive\'s', { options: { runtime: 'observe' } }, async ($, on) => {
    const { filled, ran, toasts, clock } = setUp(on)
    await $.session.start({ cwd: ROOT, surface: 'terminal', isInteractive: true })
    expect((await $.command.run({ command: 'neuroflow:tasks', args: '' } as never)).text).toContain('Task boards open')
    const ui = await $.ui.mount(pane('nf-board') as never)
    const project = await ui.drawn()
    expect(JSON.stringify(project)).toContain('level: project')
    // The shown level is text; every other is a digit key, shown as `2: flowie 3 (◆ 2)`: this project's share marked.
    expect(JSON.stringify(project)).toContain('1: project 1')
    expect(lines(project)[0]).toBe('◌ tasks')
    expect(buttons(project).filter(button => button.key.startsWith('nf-level-')).map(button => `${button.hotkey}: ${button.label}`)).toEqual([
      '2: flowie 3 (◆ 2)',
      '3: lab-team 2 (◆ 1)',
      '4: alpha-team 0',
      '5: another-team 0',
    ])
    // The ring starts on the first card, so Enter acts on it at once.
    expect(buttons(project).filter(button => button.autoFocus).map(button => button.key)).toEqual(['nf-card-rerun-ica'])
    // Keys typed through the open do nothing.
    await ui.press({ key: 'nf-level-flowie' })
    expect(JSON.stringify(await ui.drawn())).toContain('level: project')
    await clock.advance(500)
    await ui.press({ key: 'nf-level-flowie' })
    const flowie = JSON.stringify(await ui.drawn())
    expect(flowie).toContain('level: flowie')
    expect(flowie).toContain('◆ ⚠ Check stats due 10-03')
    expect(flowie).toContain('◆ Oddball EEG (this project)')
    await ui.press({ key: 'nf-card-check-stats' })
    // The picked card is marked; its targets are the board's other open columns and done.
    const picked = await ui.drawn()
    expect(buttons(picked).find(button => button.key === 'nf-card-check-stats')?.label).toContain('▸ ◆ ⚠ Check stats')
    expect(buttons(picked).filter(button => button.key.startsWith('nf-move-')).map(button => button.label)).toEqual(['inbox', 'ready', 'active', 'meeting', 'done'])
    await ui.press({ key: 'nf-move-done' })
    expect(ran).toEqual(['neuroflow:tasks --level flowie --move check-stats done'])
    await ui.press({ key: 'nf-level-hive:lab-team' })
    const hive = JSON.stringify(await ui.drawn())
    expect(hive).toContain('level: lab-team')
    // The hive names this project by its own registry: the lab project's id, not the flowie's name.
    expect(hive).toContain('◆ oddball-lab (this project)')
    expect(hive).toContain('◆ Agenda item @jana')
    expect(hive).not.toContain('◆ Review poster')
    await ui.press({ key: 'nf-card-agenda-item' })
    await ui.press({ key: 'nf-move-inbox' })
    // A push to the team's repository is the person's to send (charter rule 16): the move only goes into the prompt.
    expect(filled).toEqual(['/neuroflow:tasks --level hive --hive lab-team --move agenda-item inbox'])
    expect(ran).toHaveLength(1)
    expect(toasts.join(' ')).toContain('the move is in the prompt — Esc, then Enter sends it')
    await ui.press({ key: 'nf-level-project' })
    // x cancels a pick: nothing moves.
    await ui.press({ key: 'nf-card-rerun-ica' })
    await ui.press({ key: 'nf-board-cancel' })
    expect(buttons(await ui.drawn()).some(button => button.key.startsWith('nf-move-'))).toBe(false)
    expect(ran).toHaveLength(1)
    await ui.press({ key: 'nf-card-rerun-ica' })
    await ui.press({ key: 'nf-move-review' })
    expect(ran).toEqual(['neuroflow:tasks --level flowie --move check-stats done', 'neuroflow:tasks --move rerun-ica review'])
    expect(filled).toHaveLength(1)
    await ui.unmount()
  })

  test('h, j, k and l: card to card on the grid, target to target once a card is picked, nothing on a read-only board', async () => {
    const view = await loadTaskView(memIo(FILES, { home: HOME }), ROOT, HOME, TODAY)
    const flowie = view.levels.find(level => level.id === 'flowie')
    if (flowie === undefined) throw new Error('no flowie level')
    // flowie: inbox [read-paper] · active [write-intro] · review [check-stats]
    expect(cardKeys(flowie)).toEqual([['nf-card-read-paper'], ['nf-card-write-intro'], ['nf-card-check-stats']])
    expect(boardRingTarget(flowie, null, null, 'down')).toBe('nf-card-read-paper')
    expect(boardRingTarget(flowie, null, 'nf-card-read-paper', 'right')).toBe('nf-card-write-intro')
    expect(boardRingTarget(flowie, null, 'nf-card-check-stats', 'right')).toBe('nf-card-check-stats')
    expect(boardRingTarget(flowie, null, 'nf-card-write-intro', 'left')).toBe('nf-card-read-paper')
    expect(boardRingTarget(flowie, null, 'nf-card-write-intro', 'down')).toBe('nf-card-write-intro')
    // Picked: the other open columns and done, in board order; the ring starts on the column after the card's.
    expect(moveTargets(flowie.board, 'active')).toEqual(['inbox', 'ready', 'review', 'meeting', 'done'])
    expect(firstTarget(flowie.board, 'active')).toBe('review')
    expect(firstTarget(flowie.board, 'review')).toBe('meeting')
    expect(boardRingTarget(flowie, 'write-intro', 'nf-move-review', 'down')).toBe('nf-move-meeting')
    expect(boardRingTarget(flowie, 'write-intro', 'nf-move-review', 'left')).toBe('nf-move-ready')
    expect(boardRingTarget(flowie, 'write-intro', 'nf-move-done', 'right')).toBe('nf-move-done')
    // Still on the card (the ring did not reach a target): the first target.
    expect(boardRingTarget(flowie, 'write-intro', 'nf-card-write-intro', 'down')).toBe('nf-move-inbox')
    expect(boardRingTarget({ kind: 'remote', board: flowie.board }, null, null, 'down')).toBe(null)
    expect(cardKeys({ kind: 'remote', board: flowie.board })).toEqual([])
  })

  test('a column past five cards: j walks on into the next five; h and l land on the same row of the neighbour\'s first five', () => {
    const card = (slug: string) => ({ slug, title: slug, owner: null, due: null, overdue: false, project: null, isMine: true })
    const level = {
      kind: 'project' as const,
      board: {
        columns: [
          { id: 'inbox', label: 'inbox', cards: ['a', 'b'].map(card), total: 2 },
          { id: 'ready', label: 'ready', cards: Array.from({ length: 7 }, (_, at) => card(`step-${at + 1}`)), total: 7 },
          { id: 'active', label: 'active', cards: Array.from({ length: 6 }, (_, at) => card(`run-${at + 1}`)), total: 6 },
        ],
        openColumns: ['inbox', 'ready', 'active'],
        done: 0,
        archived: 0,
      },
    }
    expect(boardRingTarget(level, null, 'nf-card-step-5', 'down')).toBe('nf-card-step-6')
    expect(boardRingTarget(level, null, 'nf-card-step-6', 'up')).toBe('nf-card-step-5')
    expect(boardRingTarget(level, null, 'nf-card-step-7', 'down')).toBe('nf-card-step-7')
    // From the sixth card (the second page's first row) to the first row of the neighbour, which shows its first five.
    expect(boardRingTarget(level, null, 'nf-card-step-6', 'right')).toBe('nf-card-run-1')
    expect(boardRingTarget(level, null, 'nf-card-step-7', 'left')).toBe('nf-card-b')
    expect(boardRingTarget(level, null, 'nf-card-step-4', 'right')).toBe('nf-card-run-4')
  })

  test('the board\'s keys: digits for the other levels, h/j/k/l, r and q; the person\'s Tab is followed; nothing breaks without a ring', { options: { runtime: 'observe' } }, async ($, on) => {
    const { clock } = setUp(on)
    await $.session.start({ cwd: ROOT, surface: 'terminal', isInteractive: true })
    await $.command.run({ command: 'neuroflow:tasks', args: '' } as never)
    const ui = await $.ui.mount(pane('nf-board') as never)
    await clock.advance(500)
    await ui.press({ key: 'nf-level-flowie' })
    const keys = Object.fromEntries(buttons(await ui.drawn()).filter(button => button.hotkey !== undefined).map(button => [button.key, button.hotkey]))
    expect(keys).toEqual({
      'nf-level-project': '1',
      'nf-level-hive:lab-team': '3',
      'nf-level-hive:alpha-team': '4',
      'nf-level-hive:another-team': '5',
      'nf-nav-left': 'h',
      'nf-nav-right': 'l',
      'nf-nav-down': 'j',
      'nf-nav-up': 'k',
      'nf-board-refresh': 'r',
      'nf-board-close': 'q',
    })
    // The person's own Tab moves the ring (the engine raises ui.focus); j, k, h and l go on from there.
    await $.ui.focus({ component: 'Pane', requestId: 'nf-board', plugin: 'neuroflow', element: 'nf-card-write-intro', origin: { kind: 'person' } } as never)
    for (const key of ['nf-nav-left', 'nf-nav-right', 'nf-nav-down', 'nf-nav-up']) await ui.press({ key })
    // A card picked, x shows up to cancel it.
    await ui.press({ key: 'nf-card-write-intro' })
    expect(buttons(await ui.drawn()).find(button => button.key === 'nf-board-cancel')?.hotkey).toBe('x')
    await ui.unmount()
  })

  test('the board in the new look: round columns with UPPERCASE headers and counts, a list where a column would get under 18 cells', { options: { runtime: 'observe' } }, async ($, on) => {
    setUp(on)
    await $.session.start({ cwd: ROOT, surface: 'terminal', isInteractive: true })
    await $.command.run({ command: 'neuroflow:tasks', args: '' } as never)
    const ui = await $.ui.mount(pane('nf-board') as never)
    const tree = await ui.drawn()
    const boxes = elements(tree, 'Box').filter(box => box.props.borderStyle !== undefined)
    expect(boxes.map(box => box.props.borderStyle)).toEqual(['round', 'round'])
    expect(lines(tree)).toEqual(expect.arrayContaining(['INBOX', 'ACTIVE', '0', '1', 'done 0 · archived 0 · level: project']))
    await ui.unmount()
    // Two columns in 44 cells still make a grid; in 34 they would get 16 cells each.
    const roomy = await $.ui.mount({ ...pane('nf-board'), props: { ...pane('nf-board').props, bodyColumns: 44 } } as never)
    expect(elements(await roomy.drawn(), 'Box').filter(box => box.props.borderStyle === 'round').length).toBe(2)
    await roomy.unmount()
    const dock = await $.ui.mount({ ...pane('nf-board'), props: { ...pane('nf-board').props, bodyColumns: 34 } } as never)
    const list = await dock.drawn()
    expect(elements(list, 'Box').some(box => box.props.borderStyle !== undefined)).toBe(false)
    expect(lines(list)).toEqual(expect.arrayContaining(['INBOX · 0', 'ACTIVE · 1']))
    expect(buttons(list).find(button => button.key === 'nf-card-rerun-ica')?.label).toBe('  ⚠ Rerun ICA @li due 10-01')
    await dock.unmount()
  })

  test('a column shows five cards at a time: j past the fifth turns its page, k turns it back', { options: { runtime: 'observe' } }, async ($, on) => {
    const files = { ...FILES, ...Object.fromEntries(Array.from({ length: 7 }, (_, at) => [`${ROOT}/.neuroflow/tasks/ready/step-${at + 1}.md`, task(`Step ${at + 1}`, `due: 2026-11-0${at + 1}\n`)])) }
    const { clock } = setUp(on, files)
    await $.session.start({ cwd: ROOT, surface: 'terminal', isInteractive: true })
    await $.command.run({ command: 'neuroflow:tasks', args: '' } as never)
    const ui = await $.ui.mount(pane('nf-board') as never)
    await clock.advance(500)
    const cards = async () => buttons(await ui.drawn()).filter(button => button.key.startsWith('nf-card-step-')).map(button => button.key.slice('nf-card-step-'.length))
    expect(await cards()).toEqual(['1', '2', '3', '4', '5'])
    expect(lines(await ui.drawn())).toContain('  +2 more')
    await $.ui.focus({ component: 'Pane', requestId: 'nf-board', plugin: 'neuroflow', element: 'nf-card-step-5', origin: { kind: 'person' } } as never)
    await ui.press({ key: 'nf-nav-down' })
    expect(await cards()).toEqual(['6', '7'])
    expect(lines(await ui.drawn())).toContain('  6–7 of 7')
    await ui.press({ key: 'nf-nav-up' })
    expect(await cards()).toEqual(['1', '2', '3', '4', '5'])
    await ui.unmount()
  })

  test('the boards follow the files when a turn ends', { options: { runtime: 'observe' } }, async ($, on) => {
    const { fs } = setUp(on)
    await $.session.start({ cwd: ROOT, surface: 'terminal', isInteractive: true })
    await $.command.run({ command: 'neuroflow:tasks', args: '' } as never)
    const ui = await $.ui.mount(pane('nf-board') as never)
    expect(JSON.stringify(await ui.drawn())).toContain('1: project 1')
    // /tasks --move ran in the turn: the file is in done/ now.
    fs.files[`${ROOT}/.neuroflow/tasks/done/rerun-ica.md`] = fs.files[`${ROOT}/.neuroflow/tasks/active/rerun-ica.md`]
    delete fs.files[`${ROOT}/.neuroflow/tasks/active/rerun-ica.md`]
    await $.turn.complete({ reason: 'answer', answer: 'moved', durationMs: 1, isAborted: false, turnId: 't1' } as never)
    expect(JSON.stringify(await ui.drawn())).toContain('1: project 0')
    await ui.unmount()
  })

  test('the remote boards refresh when the boards open or on r, never when a turn ends, and wait after a failure', { options: { runtime: 'observe' } }, async ($, on) => {
    const files = {
      ...FILES,
      [`${HOME}/.neuroflow/flowie/projects/projects.json`]: JSON.stringify({
        projects: [{ id: 'Oddball EEG', repos: ['https://github.com/example-lab/oddball-eeg', 'https://github.com/example-lab/oddball-analysis'] }],
      }),
      [`${HOME}/.neuroflow/boards/github.com/example-lab/oddball-analysis/.neuroflow/tasks/active/rerun.md`]: task('Rerun cached'),
    }
    const { clock } = setUp(on, files)
    const refreshes: string[][] = []
    on('process.run', ($$, e) => {
      const argv = (e as unknown as { argv: string[] }).argv
      if (argv.some(arg => arg.endsWith('projects.py'))) refreshes.push(argv.slice(argv.findIndex(arg => arg.endsWith('projects.py')) + 1))
      return { value: { exitCode: 1, stdout: '{}', stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }
    })
    await $.session.start({ cwd: ROOT, surface: 'terminal', isInteractive: true })
    await $.command.run({ command: 'neuroflow:tasks', args: '' } as never)
    const ui = await $.ui.mount(pane('nf-board') as never)
    await new Promise(resolve => setTimeout(resolve, 30))
    expect(refreshes).toEqual([['refresh', '--project', 'Oddball EEG', '--root', ROOT, '--json']])
    expect(JSON.stringify(await ui.drawn())).toContain('example-lab/oddball-analysis 1')
    await $.turn.complete({ reason: 'answer', answer: 'x', durationMs: 1, isAborted: false, turnId: 't1' } as never)
    await new Promise(resolve => setTimeout(resolve, 30))
    expect(refreshes.length).toBe(1)
    // r after a failed refresh: the board is read again, the network is asked again only ten minutes later
    // (a refresh that went through could run again after one).
    await clock.advance(2 * 60_000)
    await ui.press({ key: 'nf-board-refresh' })
    await new Promise(resolve => setTimeout(resolve, 30))
    expect(refreshes.length).toBe(1)
    await clock.advance(7 * 60_000 + 59_000)
    await ui.press({ key: 'nf-board-refresh' })
    await new Promise(resolve => setTimeout(resolve, 30))
    expect(refreshes.length).toBe(1)
    await clock.advance(2_000)
    await ui.press({ key: 'nf-board-refresh' })
    await new Promise(resolve => setTimeout(resolve, 30))
    expect(refreshes.length).toBe(2)
    await ui.unmount()
  })

  test('repository keys follow projects.py: three safe parts, nothing that could leave the cache', () => {
    for (const url of ['https://nohost.invalid/../../victim', 'https://github.com/org', '-oProxyCommand=x', 'file:///C:/repo', 'https://github.com/a/b/c']) {
      expect(repoKey(url)).toBe(null)
    }
    expect(repoKey('HTTPS://GitHub.com/Example-Lab/Oddball.GIT')).toBe('github.com/example-lab/oddball')
    expect(repoKey('github.com/example-lab/oddball')).toBe('github.com/example-lab/oddball')
    // A registry that writes repos as one string links this repository too.
    const keys = new Set([locationKey('https://github.com/example-lab/oddball-eeg', HOME)])
    expect(registryProject(JSON.stringify({ projects: [{ id: 'Oddball', repos: 'git@github.com:example-lab/oddball-eeg.git' }] }), keys, HOME)).toBe('Oddball')
  })
})
