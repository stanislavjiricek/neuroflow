import { describe, expect, mock, test } from 'claude-code/testing'

import type { NfSnapshot } from '../../../types'
import {
  ALIAS_ALLOWS,
  DEFAULT_STRUCTURE,
  LOCAL_ONLY,
  afterEdit,
  denyText,
  isHeavy,
  participantRoute,
  readViolations,
  shellViolations,
  structureFrom,
  uncoveredLocalOnly,
  writeViolations,
} from '../features/guards'
import { fakeFs } from './fakefs'

const snap = (over: Partial<NfSnapshot> = {}): NfSnapshot => ({
  root: '/work/proj',
  nfSchema: 1,
  dialect: 'frontmatter',
  pluginVersion: null,
  runningVersion: null,
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
  flowieProfiles: [],
  wikiCapture: null,
  wikiPending: 0,
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
    expect(shellViolations('git add .neuroflow/paper/xray-results.jsonl', snap(), ctx)[0].rule).toBe('GIT-NO-SECRETS')
    expect(shellViolations('git add .neuroflow/wiki/.pending/p300-window.md', snap(), ctx)[0].rule).toBe('GIT-NO-SECRETS')
    expect(shellViolations('git add -A', snap(), { gitignore: LOCAL_ONLY.slice(0, 4).join('\n'), isLoginNode: false })[0].message).toContain('xray')
    expect(shellViolations('git add -A && git commit -m x', snap(), ctx)).toEqual([])
    expect(shellViolations('git add -A', snap(), { gitignore: '', isLoginNode: false })[0].message).toContain('.gitignore does not exclude')
  })

  test('a broad git add asks while .gitignore misses local-only files; an ignored .neuroflow/ covers them all', () => {
    const covering = [
      '.neuroflow/',
      '/.neuroflow/',
      '.neuroflow',
      '.neuroflow/*',
      '.neuroflow/**',
      '# project memory\n.neuroflow/\n!.neuroflow/sessions/', // nothing comes back out of an ignored folder
      '.neuroflow/**\n!.neuroflow/**/',
      LOCAL_ONLY.join('\r\n'),
    ]
    for (const gitignore of covering) {
      expect([gitignore, uncoveredLocalOnly(gitignore)]).toEqual([gitignore, []])
      expect([gitignore, shellViolations('git add .', snap(), { gitignore, isLoginNode: false })]).toEqual([gitignore, []])
    }
    expect(uncoveredLocalOnly('# .neuroflow/')).toEqual(LOCAL_ONLY)
    expect(uncoveredLocalOnly('.neuroflow/*\n!.neuroflow/sessions/')).toEqual(['.neuroflow/sessions/'])
    expect(uncoveredLocalOnly('sessions/\nreview/\nintegrations.json\nflowie/\n.neuroflow/paper/xray-results.jsonl\n.pending/')).toEqual(['.neuroflow/paper/xray-*'])
    const dot = shellViolations('git add .', snap(), { gitignore: '', isLoginNode: false })
    expect(dot.map(v => [v.rule, v.level])).toEqual([['GIT-NO-SECRETS', 'ask']])
    for (const part of ['`git add .` would stage', '/neuroflow:migrate', 'git reset -q --']) expect(dot[0].message).toContain(part)
    expect(shellViolations('git add -u', snap(), { gitignore: '.neuroflow/sessions/', isLoginNode: false })[0].message).toContain('`git add -u` would stage')
    // naming a local-only path is still denied, whatever .gitignore says
    expect(shellViolations('git add .neuroflow/sessions/2026-10-07.md', snap(), { gitignore: '.neuroflow/', isLoginNode: false }).map(v => [v.rule, v.level])).toEqual([['GIT-NO-SECRETS', 'deny']])
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

  // commands/git.md → Steps: every alias reads the repo state (step 1), then runs its own steps up to its endpoint.
  const readState = ['git status --short', 'git log --oneline -5', 'git branch --show-current', 'git remote -v', 'git rev-list --count --left-right @{upstream}...HEAD 2>/dev/null || echo "no upstream"']
  const stage = ['git config --get filter.nbstripout.clean', 'git add .', 'git diff --cached --name-only', 'git reset -q -- .neuroflow/sessions/2026-10-07.md']
  const commit = ['git diff --cached --name-only', 'git reset -q -- .neuroflow/integrations.json', 'git diff --cached --stat', 'git diff --cached', 'git commit -m "feat: add the ERP figure"']
  const prescribed: Record<string, string[]> = {
    a: stage,
    c: commit,
    ac: [...stage, ...commit],
    acp: [...stage, ...commit, 'git push --set-upstream origin feat/erp'],
    p: ['git push', 'git stash', 'git pull --rebase', 'git stash pop'],
    pl: ['git stash', 'git pull', 'git stash pop'],
    ps: ['git push', 'git push --set-upstream origin feat/erp'],
    b: ['git branch', 'git checkout -b feat/erp', 'git checkout main', 'git branch -d feat/old'],
    pr: ['git push --set-upstream origin feat/erp', 'git log main..HEAD --oneline', 'which gh', 'gh pr create --title "feat: erp" --body "Adds the ERP figure."'],
  }

  test('each /git alias runs what commands/git.md prescribes without a violation', () => {
    expect(Object.keys(prescribed).sort()).toEqual(Object.keys(ALIAS_ALLOWS).sort())
    for (const [alias, steps] of Object.entries(prescribed)) {
      for (const command of [...readState, ...steps]) {
        expect([alias, command, shellViolations(command, snap(), { ...ctx, gitAlias: alias })]).toEqual([alias, command, []])
      }
    }
  })

  test('listings pass every alias; creating, deleting or renaming a ref outside its alias does not', () => {
    const scope = (command: string, alias: string): string[] => shellViolations(command, snap(), { ...ctx, gitAlias: alias }).map(v => v.rule)
    const listings = [
      'git branch',
      'git branch -a -vv',
      "git branch --list 'feat/*'",
      'git branch -l feat*',
      'git branch --merged main',
      'git branch --contains HEAD~3',
      "git branch --format '%(refname:short)'",
      'git branch --sort=-committerdate',
      'echo "on $(git branch --show-current)"',
      'git tag',
      "git tag -l 'v1.*'",
      'git stash list',
      'git stash show -p stash@{0}',
    ]
    for (const listing of listings) expect([listing, scope(listing, 'a')]).toEqual([listing, []])
    expect(scope('git branch feature-x', 'a')).toEqual(['GIT-ALIAS-SCOPE'])
    expect(scope('git branch -D feat/old', 'ac')).toEqual(['GIT-ALIAS-SCOPE'])
    expect(scope('git branch -m feat/new', 'c')).toEqual(['GIT-ALIAS-SCOPE'])
    expect(scope('git branch -r -d origin/feat/old', 'pl')).toEqual(['GIT-ALIAS-SCOPE'])
    expect(scope('git branch --unset-upstream', 'ps')).toEqual(['GIT-ALIAS-SCOPE'])
    expect(scope('git branch -u origin/main', 'p')).toEqual(['GIT-ALIAS-SCOPE'])
    expect(scope('git tag v1.0', 'acp')).toEqual(['GIT-ALIAS-SCOPE'])
    expect(scope('git stash', 'a')).toEqual(['GIT-ALIAS-SCOPE'])
    expect(scope('git stash pop', 'ps')).toEqual(['GIT-ALIAS-SCOPE'])
    // unstaging is part of /git c, moving history is not; throwing work away is asked about whatever the alias
    expect(shellViolations('git reset --hard HEAD~1', snap(), { ...ctx, gitAlias: 'c' }).map(v => [v.rule, v.level])).toEqual([['GIT-NO-SECRETS', 'ask'], ['GIT-ALIAS-SCOPE', 'deny']])
    expect(shellViolations('git reset --hard HEAD~1', snap(), { ...ctx, gitAlias: 'a' }).map(v => [v.rule, v.level])).toEqual([['GIT-NO-SECRETS', 'ask']])
  })

  test('/git c only unstages, /git p and pl only stash and pop; a lone & starts a new command', () => {
    const scope = (command: string, alias: string): string[] => shellViolations(command, snap(), { ...ctx, gitAlias: alias }).map(v => v.rule)
    expect(scope('git reset -q -- .neuroflow/sessions/x.md', 'c')).toEqual([])
    expect(scope('git reset --soft HEAD~1', 'c')).toEqual(['GIT-ALIAS-SCOPE'])
    expect(scope('git reset HEAD~3', 'c')).toEqual(['GIT-ALIAS-SCOPE'])
    for (const alias of ['p', 'pl']) {
      for (const ok of ['git stash', 'git stash push -m wip', 'git stash pop', 'git stash list']) expect([alias, ok, scope(ok, alias)]).toEqual([alias, ok, []])
      for (const bad of ['git stash drop', 'git stash clear']) expect([alias, bad, scope(bad, alias)]).toEqual([alias, bad, ['GIT-ALIAS-SCOPE']])
    }
    expect(scope('git branch --list & git push', 'c')).toEqual(['GIT-ALIAS-SCOPE'])
    expect(scope('git status 2>&1 | head', 'c')).toEqual([])
  })

  test('every broad git add asks while local-only lines are missing; a forced one is denied', () => {
    const bare = { gitignore: '', isLoginNode: false }
    for (const command of ['git add -- .', 'git add -v .', 'git add :/', 'git add -Av', 'git add --all']) {
      expect([command, shellViolations(command, snap(), bare).map(v => [v.rule, v.level])]).toEqual([command, [['GIT-NO-SECRETS', 'ask']]])
    }
    for (const command of ['git add -f .', 'git add --force -A']) {
      expect([command, shellViolations(command, snap(), ctx).map(v => [v.rule, v.level])]).toEqual([command, [['GIT-NO-SECRETS', 'deny']]])
    }
    expect(shellViolations('git add src/analysis.py', snap(), bare)).toEqual([])
  })

  // commands/flowie.md → Git operations pattern, commands/migrate.md 5.1, commands/phase.md, wiki-protocol: the flowie
  // is the person's own repository, staged by path. Only the project's .neuroflow/flowie/ is local-only.
  test('staging in the flowie by path goes through; its integrations.json and a project\'s local-only folders do not', () => {
    const home = { ...ctx, home: '/home/me' }
    const rules = (command: string, context: Parameters<typeof shellViolations>[2] = home): string[][] => shellViolations(command, snap(), context).map(v => [v.rule, v.level])
    const steps = [
      'git -C ~/.neuroflow/flowie -c core.quotepath=off status --porcelain --untracked-files=all',
      'git -C ~/.neuroflow/flowie add -- "wellbeing/log.md" "wellbeing/2026-10-08.json"',
      'git -C ~/.neuroflow/flowie commit -m "sync: before migrate" -- "wellbeing/log.md" "wellbeing/2026-10-08.json"',
      'git -C ~/.neuroflow/flowie pull --rebase --autostash && git -C ~/.neuroflow/flowie push',
      'git -C ~/.neuroflow/flowie add -- tasks/inbox/plan.md',
      'git -C ~/.neuroflow/flowie add wiki/ && git -C ~/.neuroflow/flowie commit -m "wiki: P300 window" -- wiki/',
      'git -C ~/.neuroflow/flowie add projects/projects.json "projects/oddball.md" && git -C ~/.neuroflow/flowie commit -m "phase: oddball → data" && git -C ~/.neuroflow/flowie pull --rebase && git -C ~/.neuroflow/flowie push || true',
      'git -C "$HOME/.neuroflow/flowie" add -- notes/idea.md',
      'git -C ${HOME}/.neuroflow/flowie add -- notes/idea.md',
      'git -C "$env:USERPROFILE\\.neuroflow\\flowie" add -- notes/idea.md',
      'git -C %USERPROFILE%\\.neuroflow\\flowie add -- notes/idea.md',
      'git -C /home/me/.neuroflow/flowie add -- notes/idea.md',
      'git --git-dir=/home/me/.neuroflow/flowie/.git --work-tree=/home/me/.neuroflow/flowie add -- notes/idea.md',
      'git -C ~/.neuroflow/hives/example-lab add -- tasks/inbox/plan.md',
    ]
    for (const command of steps) expect([command, rules(command)]).toEqual([command, []])
    const windows = { ...ctx, home: 'C:\\Users\\me' }
    for (const command of ['git -C "C:\\Users\\me\\.neuroflow\\flowie" add -- notes/idea.md', 'git -C C:/Users/me/.neuroflow/flowie add -- notes/idea.md', 'git -C /c/Users/me/.neuroflow/flowie add -- notes/idea.md']) {
      expect([command, rules(command, windows)]).toEqual([command, []])
    }
    expect(rules('git -C ~/.neuroflow/flowie add -- integrations.json')).toEqual([['GIT-NO-SECRETS', 'deny']])
    // A project's own .neuroflow/, wherever it is — under the home folder too — keeps its local-only folders.
    const project = [
      'git add .neuroflow/flowie/profile.md',
      'git -C .neuroflow/flowie add profile.md',
      'git -C /work/proj add /work/proj/.neuroflow/flowie/profile.md',
      'git add /home/me/studies/oddball/.neuroflow/flowie/profile.md',
      'git -C /home/meg/.neuroflow/flowie add -- profile.md',
      'git add "$PWD/.neuroflow/sessions/2026-10-07.md"',
      'git -C ~/studies/oddball add .neuroflow/sessions/2026-10-07.md',
    ]
    for (const command of project) expect([command, rules(command)]).toEqual([command, [['GIT-NO-SECRETS', 'deny']]])
    // The home folder's own path is known only from the environment; without it, such a path counts as a project's.
    expect(rules('git -C /home/me/.neuroflow/flowie add -- notes/idea.md', ctx)).toEqual([['GIT-NO-SECRETS', 'deny']])
    // A broad add in the flowie asks whatever the project's .gitignore says: the flowie is staged by path.
    for (const command of ['git -C ~/.neuroflow/flowie add -A', 'git -C "$HOME/.neuroflow/flowie" add .']) {
      expect([command, rules(command)]).toEqual([command, [['GIT-NO-SECRETS', 'ask']]])
    }
    expect(rules('git -C ~/.neuroflow/flowie add -f -A')).toEqual([['GIT-NO-SECRETS', 'deny']])
  })

  test('raw data, frozen files, uploads', () => {
    expect(shellViolations('rm -rf sourcedata/sub-03', snap(), ctx)[0].rule).toBe('RAW-READONLY')
    expect(shellViolations('Remove-Item .\\sourcedata\\sub-03 -Recurse', snap(), ctx)[0].rule).toBe('RAW-READONLY')
    expect(shellViolations('ls sourcedata', snap(), ctx)).toEqual([])
    expect(shellViolations("sed -i 's/48/40/' .neuroflow/preregistration/prereg-osf.md", snap(), ctx)[0].rule).toBe('PREREG-FROZEN')
    expect(shellViolations('notebooklm source add paper.pdf', snap(), ctx)[0].level).toBe('ask')
  })

  test('a raw root matches on path boundaries, never inside another name', () => {
    const raw = snap({ rawRoots: ['raw/'] })
    const rules = (command: string, s: NfSnapshot): string[] => shellViolations(command, s, ctx).map(v => v.rule)
    for (const command of ['rm figures/draw_plot.png', 'mv results/rawdata.csv results/old/', 'echo done > raw_counts.txt']) {
      expect([command, rules(command, raw)]).toEqual([command, []])
    }
    for (const command of ['rm -rf sourcedata_old/', 'git checkout -b sourcedata-fix']) {
      expect([command, rules(command, snap())]).toEqual([command, []])
    }
    for (const command of ['rm raw/sub-01.eeg', 'truncate -s 0 ./raw/sub-01/beh.tsv', 'echo x >> raw/notes.txt', 'Remove-Item -Path:raw\\sub-01 -Recurse']) {
      expect([command, rules(command, raw)]).toEqual([command, ['RAW-READONLY']])
    }
  })

  test('moving or copying a new recording into a raw root adds it; changing one, or moving it out, is denied', () => {
    const rules = (command: string): string[] => shellViolations(command, snap(), ctx).map(v => v.rule)
    const additions = [
      'mv ~/Downloads/sub-02.eeg sourcedata/sub-02/',
      'mv -t sourcedata/sub-02/ ~/Downloads/sub-02.vhdr ~/Downloads/sub-02.vmrk',
      'Move-Item -Path C:\\Users\\me\\Downloads\\sub-02.eeg -Destination .\\sourcedata\\sub-02\\',
      'cp ~/Downloads/sub-02.eeg sourcedata/sub-02/',
      'Copy-Item D:\\lab\\sub-02 .\\sourcedata\\ -Recurse',
      'mv ~/Downloads/sub-02.eeg sourcedata/sub-02/ 2>/dev/null',
    ]
    for (const command of additions) expect([command, rules(command)]).toEqual([command, []])
    const changes = [
      'mv sourcedata/sub-01/x.eeg derivatives/',
      'mv sourcedata/sub-01/a.vhdr sourcedata/sub-01/b.vhdr',
      'Move-Item .\\sourcedata\\sub-01 .\\archive\\',
      'git mv sourcedata/sub-01 sourcedata/sub-001',
      'echo x > ./sourcedata/sub-01/beh.tsv',
      "sed -i.bak 's/a/b/' sourcedata/sub-01/events.tsv",
      'Set-Content -Path sourcedata/sub-01/beh.tsv -Value x',
      '/bin/rm -rf sourcedata*',
      'git checkout -- sourcedata/sub-01/beh.tsv',
    ]
    for (const command of changes) expect([command, rules(command).includes('RAW-READONLY')]).toEqual([command, true])
  })

  test('what a shell is told to run, a subshell and backticks are checked too; a move onto a recording is a change', () => {
    const rules = (command: string): string[] => shellViolations(command, snap(), ctx).map(v => v.rule)
    const changes = [
      'bash -c "rm -rf sourcedata"',
      "sh -c 'rm -rf sourcedata/sub-01'",
      'powershell -Command "Remove-Item -Recurse -Force sourcedata"',
      'cmd /c "del /s /q sourcedata"',
      '(cd /work/proj && rm -rf sourcedata)',
      'echo `rm -rf sourcedata`',
      'mv ~/Downloads/fixed.eeg sourcedata/sub-01/sub-01_task-rest_eeg.eeg',
      'Move-Item -Force fixed.eeg sourcedata/sub-01/sub-01_task-rest_eeg.eeg',
    ]
    for (const command of changes) expect([command, rules(command).includes('RAW-READONLY')]).toEqual([command, true])
    for (const command of ['bash -c "ls sourcedata"', 'sh -c "cp ~/new.eeg sourcedata/sub-03/"', 'git commit -m "never rm -rf sourcedata"']) {
      expect([command, rules(command)]).toEqual([command, []])
    }
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

  test('a broad git add without the .gitignore lines asks the person under enforce', { options: { runtime: 'on', guards: 'enforce' } }, async ($, on) => {
    fakeFs(on, files, root)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: 0 })
    on('session.start', ($, e) => ({ cwd: e.cwd }))
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
    await $.session.start({ cwd: root, surface: 'terminal', isInteractive: true })
    const blocked = await $.tool.call({ tool: 'Bash', command: 'git add .' } as never)
    expect(ran).toBe(0)
    expect(asked[0]).toContain('`git add .` would stage local-only files')
    expect(JSON.stringify(blocked)).toContain('nf-rule: GIT-NO-SECRETS')
    answer = 'Allow — I confirm this myself'
    await $.tool.call({ tool: 'Bash', command: 'git add .' } as never)
    expect(ran).toBe(1)
  })

  test('under enforce, staging in the flowie by path runs; staging the project\'s local-only folder does not', { options: { runtime: 'on', guards: 'enforce' } }, async ($, on) => {
    fakeFs(on, files, root)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: 0 })
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    let ran = 0
    on('tool.call', () => {
      ran += 1
      return { result: 'ok', text: 'ok' }
    })
    await $.session.start({ cwd: root, surface: 'terminal', isInteractive: true })
    // the second names the home folder by its path, which the guard learns from HOME
    for (const command of ['git -C ~/.neuroflow/flowie add -- "wellbeing/log.md"', 'git -C /home/me/.neuroflow/flowie add -- notes/idea.md']) {
      await $.tool.call({ tool: 'Bash', command } as never)
    }
    expect(ran).toBe(2)
    const denied = await $.tool.call({ tool: 'Bash', command: 'git add .neuroflow/flowie/profile.md' } as never)
    expect(ran).toBe(2)
    expect(JSON.stringify(denied)).toContain('nf-rule: GIT-NO-SECRETS')
  })

  test('a /git alias reading the repo state draws no warning; a step past its endpoint does', { options: { runtime: 'observe' } }, async ($, on) => {
    fakeFs(on, files, root)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: 0 })
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('command.run', () => ({ text: '', ref: 1 }))
    on('tool.call', () => ({ result: 'ok', text: 'ok' }))
    const said: string[] = []
    on('ui.toast', ($, e) => {
      said.push(JSON.stringify(e))
      return { value: undefined }
    })
    on('ui.notice', ($, e) => {
      said.push(JSON.stringify(e))
      return { value: undefined }
    })
    await $.session.start({ cwd: root, surface: 'terminal', isInteractive: true })
    await $.command.run({ command: 'neuroflow:git', args: 'ac' })
    await $.tool.call({ tool: 'Bash', command: 'git branch --show-current', tool_use_id: 'state' } as never)
    expect(said).toEqual([])
    await $.tool.call({ tool: 'Bash', command: 'git push', tool_use_id: 'push' } as never)
    expect(said.join(' ')).toContain('would block')
  })
})
