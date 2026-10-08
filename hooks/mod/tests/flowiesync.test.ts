import type { On } from 'claude-code'
import { describe, expect, mock, test } from 'claude-code/testing'

import type { NfFlowieSyncEntry } from '../../../types'
import { SYNC_QUEUE, afterFlush, asQueue, enqueue, flushFlowie, gitReason, isSettled, syncState } from '../lib/flowiesync'
import type { NfIo, NfRun } from '../lib/io'
import { bandItems, keyFillsPrompt } from '../features/views'
import { fakeFs } from './fakefs'
import { memIo } from './memio'

const HOME = '/home/me'
const FLOWIE = `${HOME}/.neuroflow/flowie`
const LOG = `${HOME}/.neuroflow/flowie-sync.log`
const NOW = Date.UTC(2026, 9, 7, 7, 30)
const ok: NfRun = { exitCode: 0, stdout: '', stderr: '' }

const wellbeing: NfFlowieSyncEntry = { paths: ['wellbeing/2026-10-07.json', 'wellbeing/.flow'], message: 'wellbeing: 2026-10-07', at: 1 }

/** An NfIo over files in memory whose git answers come from `answer`; every call and its options are kept. */
const gitIo = (files: Record<string, string>, answer: (args: readonly string[]) => NfRun | Promise<NfRun>) => {
  const calls: { args: string[]; env?: Record<string, string> }[] = []
  const base = memIo(files, { home: HOME, now: NOW })
  const io: NfIo & { files: Record<string, string> } = {
    ...base,
    run: (argv, init) => {
      calls.push({ args: argv.slice(3), env: init.env })
      return answer(argv.slice(3)) as Promise<NfRun>
    },
  }
  return { io, calls }
}

const repo = {
  [`${FLOWIE}/.git/HEAD`]: 'ref: refs/heads/main\n',
  [`${FLOWIE}/.git/hooks/pre-commit.sample`]: '#!/bin/sh\n',
  [`${FLOWIE}/wellbeing/2026-10-07.json`]: '{}\n',
  [`${FLOWIE}/wellbeing/.flow`]: '| 2026-10-07.json | wellbeing entry |\n',
}

describe('the queue', () => {
  test('one entry per commit message, paths merged; what was queued again stays after a flush', () => {
    const first = enqueue([], { paths: ['ideas-inbox.md'], message: 'idea: inbox', at: 1 })
    const twice = enqueue(first, { paths: ['ideas-inbox.md'], message: 'idea: inbox', at: 5 })
    expect(twice).toEqual([{ paths: ['ideas-inbox.md'], message: 'idea: inbox', at: 5 }])
    const both = enqueue(twice, wellbeing)
    expect(both.map(entry => entry.message)).toEqual(['idea: inbox', 'wellbeing: 2026-10-07'])
    // An idea captured while the flush of `first` ran is still to be synced.
    expect(afterFlush(both, first)).toEqual(both)
    expect(afterFlush(both, both)).toEqual([])
    expect(asQueue([{ paths: 'x' }, null, wellbeing, 'junk'])).toEqual([wellbeing])
    expect(asQueue(undefined)).toEqual([])
    expect(syncState(both, null)).toEqual({ pending: ['idea: inbox', 'wellbeing: 2026-10-07'], failure: null, isHeld: false })
  })
})

describe('a flush', () => {
  test('commits each entry by path, pulls, pushes, with no credential prompt, and logs the attempt', async () => {
    const { io, calls } = gitIo(repo, args => (args[0] === 'config' ? { exitCode: 1, stdout: '', stderr: '' } : ok))
    const result = await flushFlowie(io, HOME, [wellbeing])
    expect(result.outcome).toBe('synced')
    expect(calls.map(call => call.args.join(' '))).toEqual([
      'config --get core.hooksPath',
      'add -- wellbeing/2026-10-07.json wellbeing/.flow',
      'commit -m wellbeing: 2026-10-07 -- wellbeing/2026-10-07.json wellbeing/.flow',
      'pull --rebase',
      'push',
    ])
    expect(calls.every(call => call.env?.GIT_TERMINAL_PROMPT === '0')).toBe(true)
    expect(io.files[LOG]).toBe('2026-10-07T07:30:00Z synced: wellbeing/2026-10-07.json wellbeing/.flow (mod)\n')
  })

  test('a failed push is logged with git\'s words and keeps the queue', async () => {
    const { io } = gitIo(repo, args => (args[0] === 'push' ? { exitCode: 128, stdout: '', stderr: 'fatal: unable to access the remote\nmore' } : args[0] === 'commit' ? { exitCode: 1, stdout: 'nothing to commit, working tree clean', stderr: '' } : ok))
    const result = await flushFlowie(io, HOME, [wellbeing])
    expect(result).toEqual({
      outcome: 'failed',
      detail: 'push failed — fatal: unable to access the remote',
      line: '2026-10-07T07:30:00Z push failed: wellbeing/2026-10-07.json wellbeing/.flow (mod) — fatal: unable to access the remote',
    })
    expect(io.files[LOG]).toContain('push failed')
    expect(syncState([wellbeing], result)).toEqual({ pending: ['wellbeing: 2026-10-07'], failure: 'push failed — fatal: unable to access the remote', isHeld: true })
  })

  test('a git call that throws synchronously is a failed step, logged — never an escape', async () => {
    const { io } = gitIo(repo, () => {
      throw new Error('process API unavailable')
    })
    const result = await flushFlowie(io, HOME, [wellbeing])
    expect(result.outcome).toBe('failed')
    expect(result.detail).toBe('commit failed — process API unavailable')
    expect(io.files[LOG]).toContain('commit failed: wellbeing/2026-10-07.json wellbeing/.flow (mod) — process API unavailable')
  })

  test('not run with git hooks or LFS or during a rebase (kept for /flowie --sync); only files that exist are committed', async () => {
    const hooked = gitIo({ ...repo, [`${FLOWIE}/.git/hooks/pre-commit`]: '#!/bin/sh\n' }, () => ok)
    const skipped = await flushFlowie(hooked.io, HOME, [wellbeing])
    expect([skipped.outcome, skipped.detail]).toEqual(['failed', 'this flowie uses git hooks or LFS, which the mod does not run'])
    expect(hooked.calls.map(call => call.args[0])).toEqual(['config'])
    expect(hooked.io.files[LOG]).toContain('skipped (git hooks or LFS): wellbeing/2026-10-07.json wellbeing/.flow (mod)')
    const lfs = gitIo({ ...repo, [`${FLOWIE}/.gitattributes`]: '*.bin filter=lfs diff=lfs\n' }, () => ok)
    expect((await flushFlowie(lfs.io, HOME, [wellbeing])).outcome).toBe('failed')
    const rebasing = gitIo({ ...repo, [`${FLOWIE}/.git/rebase-merge/head-name`]: 'x' }, () => ok)
    expect((await flushFlowie(rebasing.io, HOME, [wellbeing])).outcome).toBe('failed')
    expect(rebasing.calls).toEqual([])
    const partial: Record<string, string> = { ...repo }
    delete partial[`${FLOWIE}/wellbeing/.flow`]
    const half = gitIo(partial, () => ok)
    expect((await flushFlowie(half.io, HOME, [wellbeing])).line).toBe('2026-10-07T07:30:00Z synced: wellbeing/2026-10-07.json (mod)')
    expect(half.calls[1].args.join(' ')).toBe('add -- wellbeing/2026-10-07.json')
    const gone = gitIo({ [`${FLOWIE}/.git/HEAD`]: 'x' }, () => ok)
    const nothing = await flushFlowie(gone.io, HOME, [wellbeing])
    expect(nothing.outcome).toBe('skipped')
    expect(syncState([], nothing)).toEqual({ pending: [], failure: null, isHeld: false })
  })

  test('nothing to sync is no attempt: no log line, which /flowie and /doctor would count as a failure', async () => {
    const gone = gitIo({ [`${FLOWIE}/.git/HEAD`]: 'x' }, () => ok)
    expect(await flushFlowie(gone.io, HOME, [wellbeing])).toEqual({ outcome: 'skipped', detail: 'the files it queued are gone', line: null })
    expect(gone.io.files[LOG]).toBeUndefined()
    const norepo = gitIo({}, () => ok)
    expect((await flushFlowie(norepo.io, HOME, [wellbeing])).line).toBe(null)
    expect(norepo.io.files[LOG]).toBeUndefined()
    expect(norepo.calls).toEqual([])
  })

  test('the reason is git\'s error line, not the progress line a pull or push prints first', async () => {
    expect(gitReason({ exitCode: 1, stdout: '', stderr: 'From github.com:me/flowie\n * branch            main       -> FETCH_HEAD\nAuto-merging wellbeing/.flow\nCONFLICT (content): Merge conflict in wellbeing/.flow\nerror: could not apply 1a2b3c4... wellbeing: 2026-10-07\n' }))
      .toBe('CONFLICT (content): Merge conflict in wellbeing/.flow')
    expect(gitReason({ exitCode: 1, stdout: '', stderr: 'To github.com:me/flowie.git\n ! [rejected]        main -> main (fetch first)\nerror: failed to push some refs to \'github.com:me/flowie.git\'\n' }))
      .toBe('! [rejected] main -> main (fetch first)')
    expect(gitReason({ exitCode: 1, stdout: '', stderr: 'error: cannot pull with rebase: You have unstaged changes.\nerror: Please commit or stash them.\n' })).toBe('error: cannot pull with rebase: You have unstaged changes.')
    expect(gitReason({ exitCode: 128, stdout: 'some output\n', stderr: '' })).toBe('some output')
    const { io } = gitIo(repo, args => (args[0] === 'pull' ? { exitCode: 1, stdout: '', stderr: 'From github.com:me/flowie\nfatal: unable to access the remote: Could not resolve host\n' } : ok))
    expect((await flushFlowie(io, HOME, [wellbeing])).detail).toBe('pull failed — fatal: unable to access the remote: Could not resolve host')
  })

  test('a sync that ran elsewhere settles a held queue: nothing left to commit or push, asked locally', async () => {
    let ahead = '1'
    const { io, calls } = gitIo(repo, args => (args[0] === 'rev-list' ? { exitCode: 0, stdout: `${ahead}\n`, stderr: '' } : ok))
    expect(await isSettled(io, HOME, [wellbeing])).toBe(false)
    ahead = '0'
    expect(await isSettled(io, HOME, [wellbeing])).toBe(true)
    expect(calls.map(call => call.args.join(' ')).slice(0, 2)).toEqual(['status --porcelain -- wellbeing/2026-10-07.json wellbeing/.flow', 'rev-list --count @{u}..HEAD'])
    const dirty = gitIo(repo, args => (args[0] === 'status' ? { exitCode: 0, stdout: ' M wellbeing/.flow\n', stderr: '' } : { exitCode: 0, stdout: '0\n', stderr: '' }))
    expect(await isSettled(dirty.io, HOME, [wellbeing])).toBe(false)
  })

  test('a pull that stops on a conflict has its rebase aborted', async () => {
    const files = { ...repo }
    const { io, calls } = gitIo(files, args => {
      if (args[0] === 'pull') {
        io.files[`${FLOWIE}/.git/rebase-merge/head-name`] = 'x'
        return { exitCode: 1, stdout: '', stderr: 'CONFLICT (content): Merge conflict in wellbeing/.flow' }
      }
      return ok
    })
    const result = await flushFlowie(io, HOME, [wellbeing])
    expect(result.outcome).toBe('failed')
    expect(calls.map(call => call.args.join(' ')).slice(-2)).toEqual(['pull --rebase', 'rebase --abort'])
  })
})

describe('the band line', () => {
  test('a pending or failed sync points at /neuroflow:flowie --sync, in quiet mode too', () => {
    const snap = { ethics: null, prereg: null, deadlines: [], problems: [], loops: [], meetings: [], phase: null, recommendedPhases: [], loadedAt: 0, pluginVersion: null, runningVersion: null, wikiPending: 0 } as never
    const pending = bandItems(snap, true, { pending: ['wellbeing: 2026-10-07'], failure: null, isHeld: false })
    expect(pending.map(item => item.text)).toEqual(['flowie sync pending (wellbeing: 2026-10-07) — it runs before your next neuroflow command or when a turn ends, or /neuroflow:flowie --sync'])
    expect(pending[0].actions?.map(action => `${action.command} ${action.args} ${action.hotkey}`)).toEqual(['neuroflow:flowie --sync s'])
    const failed = bandItems(snap, true, { pending: ['idea: inbox'], failure: 'push failed — fatal: unable to access the remote', isHeld: true })
    expect(failed[0].text).toBe('flowie not synced: push failed — fatal: unable to access the remote — /neuroflow:flowie --sync')
    expect(bandItems(snap, true, { pending: [], failure: null, isHeld: false })).toEqual([])
  })
})

// ── in a session ──────────────────────────────────────────────────────────────────────────────

const ROOT = '/work/proj'
const BAND = {
  plugin: 'neuroflow',
  surface: 'terminal',
  component: 'AbovePrompt',
  props: { hasSurvey: false, isWorking: false, maxRows: 4, bodyColumns: 160, scroll: { offset: 0, bodyRows: 4 }, view: {} },
}
const IDEAS = {
  [`${ROOT}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nproject_name: Oddball\nactive_phase: data\n---\n',
  [`${FLOWIE}/.git/HEAD`]: 'ref: refs/heads/main\n',
  [`${FLOWIE}/ideas-inbox.md`]: '# Ideas inbox\n\n',
}
/** With the self-reported check-in switched on and today's entry missing, the band offers the field. */
const FILES = { ...IDEAS, [`${FLOWIE}/wellbeing/config.json`]: '{"collect": true}\n' }
const TURN = { reason: 'answer', answer: 'done', durationMs: 1, isAborted: false, turnId: 't1' }

/** $.store in memory, kept where the test can look. */
const memStore = (on: On, initial: Record<string, unknown> = {}): Map<string, unknown> => {
  const map = new Map(Object.entries(initial))
  on('store.get', ($, e) => ({ value: map.get(e.key) }))
  on('store.set', ($, e) => {
    map.set(e.key, e.value)
    return { value: undefined }
  })
  on('store.delete', ($, e) => {
    map.delete(e.key)
    return { value: undefined }
  })
  on('store.keys', () => ({ value: [...map.keys()] }))
  return map
}

type Session = { git: string[]; toasts: string[]; ran: string[]; store: Map<string, unknown>; clock: ReturnType<typeof mock.clock> }

const session = (on: On, answer: (args: readonly string[]) => NfRun | Promise<NfRun> = () => ok, stored: Record<string, unknown> = {}): Session => {
  const seen: Session = {
    git: [],
    toasts: [],
    ran: [],
    store: memStore(on, stored),
    clock: mock.clock(on, { now: new Date(2026, 9, 7, 9, 30).getTime() }),
  }
  mock.env(on, { HOME })
  on('session.start', ($, e) => ({ cwd: e.cwd }))
  on('ui.toast', ($, e) => {
    seen.toasts.push(JSON.stringify(e))
    return { value: undefined }
  })
  on('ui.status', () => ({ value: undefined }))
  on('ui.render', () => ({ type: 'Text', children: ['(the engine draws its own band)'] }) as never)
  on('turn.complete', () => ({ text: 'done' }))
  on('command.run', ($, e) => {
    seen.ran.push(`${e.command} ${e.args}`.trim())
    return { text: '', ref: 1 }
  })
  on('process.run', async ($, e) => {
    const argv = (e as unknown as { argv: string[] }).argv
    if (argv[0] !== 'git') return { value: { exitCode: 2, stdout: '', stderr: 'not here', isStdoutTruncated: false, isStderrTruncated: false } }
    seen.git.push(argv.slice(3).join(' '))
    return { value: { ...(await answer(argv.slice(3))), isStdoutTruncated: false, isStderrTruncated: false } }
  })
  return seen
}

describe('the wellbeing band', () => {
  test('saving runs no git; the sync is queued, shown, and runs when the turn ends', { options: { runtime: 'observe', band: 'quiet' } }, async ($, on) => {
    const fs = fakeFs(on, FILES, ROOT)
    const seen = session(on, args => (args[0] === 'config' ? { exitCode: 1, stdout: '', stderr: '' } : ok))
    await $.session.start({ cwd: ROOT, surface: 'terminal', isInteractive: true })
    const ui = await $.ui.mount<'terminal', 'AbovePrompt'>(BAND as never)
    expect(JSON.stringify(await ui.drawn())).toContain('wellbeing today')
    await ui.input({ key: 'nf-wellbeing', text: '3 6 7 slept badly' })
    expect(seen.git).toEqual([])
    expect(JSON.parse(fs.files[`${FLOWIE}/wellbeing/2026-10-07.json`])).toEqual({ date: '2026-10-07', anxiety: 3, energy: 6, happiness: 7, notes: 'slept badly' })
    expect(fs.files[`${FLOWIE}/wellbeing/.flow`]).toBe('| 2026-10-07.json | wellbeing entry |\n')
    expect(asQueue(seen.store.get(SYNC_QUEUE)).map(entry => entry.message)).toEqual(['wellbeing: 2026-10-07'])
    // The field is gone; the band says the sync is pending (no score anywhere but the file).
    const after = JSON.stringify(await ui.drawn())
    expect(after).not.toContain('wellbeing today')
    expect(after).toContain('flowie sync pending (wellbeing: 2026-10-07)')
    expect(after).not.toContain('slept badly')
    expect(seen.toasts.join(' ')).toContain('wellbeing logged for 2026-10-07')
    expect(seen.toasts.join(' ')).not.toContain('slept badly')
    expect(JSON.stringify([...seen.store.values()])).not.toContain('slept badly')
    await $.turn.complete(TURN as never)
    expect(seen.git).toEqual([
      'config --get core.hooksPath',
      'add -- wellbeing/2026-10-07.json wellbeing/.flow',
      'commit -m wellbeing: 2026-10-07 -- wellbeing/2026-10-07.json wellbeing/.flow',
      'pull --rebase',
      'push',
    ])
    expect(fs.files[LOG]).toMatch(/^\S+Z synced: wellbeing\/2026-10-07\.json wellbeing\/\.flow \(mod\)\n$/)
    expect(asQueue(seen.store.get(SYNC_QUEUE))).toEqual([])
    expect(JSON.stringify(await ui.drawn())).not.toContain('flowie sync pending')
    await ui.unmount()
  })

  test('the band redraws without the field while the closure is cut off: the entry still syncs', { options: { runtime: 'observe', band: 'quiet' } }, async ($, on) => {
    // The closure's drawing is replaced once the entry exists, and its last steps may never run: here it stops for
    // good inside its write of wellbeing/.flow. Before the fix, the same stop left the flowie dirty with no git run.
    let release: () => void = () => undefined
    const gate = new Promise<void>(resolve => {
      release = resolve
    })
    on('fs.write', { path: /wellbeing[\\/]\.flow$/ }, async ($, e, next) => {
      await gate
      return next(e)
    })
    const fs = fakeFs(on, FILES, ROOT)
    const seen = session(on)
    await $.session.start({ cwd: ROOT, surface: 'terminal', isInteractive: true })
    const ui = await $.ui.mount<'terminal', 'AbovePrompt'>(BAND as never)
    const saving = ui.input({ key: 'nf-wellbeing', text: '4 5 6' })
    await seen.clock.settle()
    expect(fs.files[`${FLOWIE}/wellbeing/2026-10-07.json`]).toBeDefined()
    expect(fs.files[`${FLOWIE}/wellbeing/.flow`]).toBeUndefined()
    // A turn ends: the snapshot shows today's entry, the band is drawn without the field, the queued sync runs.
    await $.turn.complete(TURN as never)
    expect(JSON.stringify(await ui.drawn())).not.toContain('wellbeing today')
    expect(seen.git).toContain('add -- wellbeing/2026-10-07.json')
    expect(seen.git).toContain('push')
    expect(fs.files[LOG]).toContain('synced: wellbeing/2026-10-07.json (mod)')
    // Should the closure come back after all, the .flow line it then writes is queued again, not left dirty.
    release()
    await saving
    expect(asQueue(seen.store.get(SYNC_QUEUE)).map(entry => entry.message)).toEqual(['wellbeing: 2026-10-07'])
    await $.turn.complete(TURN as never)
    expect(seen.git.filter(line => line.startsWith('add'))).toEqual(['add -- wellbeing/2026-10-07.json', 'add -- wellbeing/2026-10-07.json wellbeing/.flow'])
    expect(asQueue(seen.store.get(SYNC_QUEUE))).toEqual([])
    await ui.unmount()
  })
})

describe('idea capture and the queue in a session', () => {
  test('an idea syncs at once; a failed sync is logged, shown and held — no retry loop — until a sync elsewhere settles it', { options: { runtime: 'observe', band: 'quiet' } }, async ($, on) => {
    const fs = fakeFs(on, IDEAS, ROOT)
    let offline = false
    let pushedElsewhere = false
    const seen = session(on, args => {
      if (args[0] === 'push' && offline) return { exitCode: 128, stdout: '', stderr: 'fatal: could not resolve host' }
      if (args[0] === 'config') return { exitCode: 1, stdout: '', stderr: '' }
      if (args[0] === 'rev-list') return { exitCode: 0, stdout: pushedElsewhere ? '0\n' : '1\n', stderr: '' }
      return ok
    })
    on('prompt.submit', ($, e) => ({ text: e.text }))
    await $.session.start({ cwd: ROOT, surface: 'terminal', isInteractive: true })
    const first = await $.prompt.submit({ text: 'idea: try CSD instead', origin: { kind: 'composer' } } as never)
    expect(JSON.stringify(first)).toContain('Idea saved — inbox: 1 · synced')
    expect(seen.git.slice(-3)).toEqual(['commit -m idea: inbox -- ideas-inbox.md', 'pull --rebase', 'push'])
    offline = true
    const second = await $.prompt.submit({ text: 'idea: a second cohort', origin: { kind: 'composer' } } as never)
    expect(JSON.stringify(second)).toContain('the sync did not go through (push failed — fatal: could not resolve host) and was logged')
    expect(fs.files[LOG]).toContain('push failed: ideas-inbox.md (mod) — fatal: could not resolve host')
    const ui = await $.ui.mount<'terminal', 'AbovePrompt'>(BAND as never)
    expect(JSON.stringify(await ui.drawn())).toContain('flowie not synced: push failed — fatal: could not resolve host')
    // No retry loop: a turn's end only asks git, locally, whether a sync elsewhere settled it.
    const before = seen.git.length
    await $.turn.complete(TURN as never)
    expect(seen.git.slice(before)).toEqual(['status --porcelain -- ideas-inbox.md', 'rev-list --count @{u}..HEAD'])
    // The band's key runs /neuroflow:flowie --sync, which commits and pushes; at the next turn's end the line goes.
    await ui.press({ key: 'nf-flowie-sync' })
    expect(seen.ran).toContain('neuroflow:flowie --sync')
    pushedElsewhere = true
    await $.turn.complete(TURN as never)
    expect(seen.git.filter(line => line === 'push')).toHaveLength(2)
    expect(asQueue(seen.store.get(SYNC_QUEUE))).toEqual([])
    expect(JSON.stringify(await ui.drawn())).not.toContain('flowie not synced')
    expect(fs.files[LOG].trim().split('\n').map(line => line.split(' ')[1])).toEqual(['synced:', 'push'])
    await ui.unmount()
  })

  test('a new idea after a failure tries again at once', { options: { runtime: 'observe' } }, async ($, on) => {
    fakeFs(on, IDEAS, ROOT)
    let offline = true
    const seen = session(on, args => (args[0] === 'push' && offline ? { exitCode: 128, stdout: '', stderr: 'fatal: could not resolve host' } : ok))
    on('prompt.submit', ($, e) => ({ text: e.text }))
    await $.session.start({ cwd: ROOT, surface: 'terminal', isInteractive: true })
    await $.prompt.submit({ text: 'idea: one', origin: { kind: 'composer' } } as never)
    offline = false
    const again = await $.prompt.submit({ text: 'idea: two', origin: { kind: 'composer' } } as never)
    expect(JSON.stringify(again)).toContain('inbox: 2 · synced')
    expect(seen.git.filter(line => line === 'push')).toHaveLength(2)
    expect(asQueue(seen.store.get(SYNC_QUEUE))).toEqual([])
  })

  test('as a session starts only local git runs: what an earlier session queued shows as pending, and the next turn\'s end runs it', { options: { runtime: 'observe', band: 'quiet' } }, async ($, on) => {
    const fs = fakeFs(on, { ...IDEAS, [`${FLOWIE}/wellbeing/2026-10-06.json`]: '{}\n' }, ROOT)
    // It failed in that session (held there); a new session tries it again.
    const seen = session(on, args => (args[0] === 'rev-list' ? { exitCode: 0, stdout: '1\n', stderr: '' } : ok), {
      [SYNC_QUEUE]: [{ paths: ['wellbeing/2026-10-06.json'], message: 'wellbeing: 2026-10-06', at: 1 }],
    })
    await $.session.start({ cwd: ROOT, surface: 'terminal', isInteractive: true })
    // The first prompt waits for session.start: nothing networked there, nothing committed.
    expect(seen.git).toEqual(['status --porcelain -- wellbeing/2026-10-06.json', 'rev-list --count @{u}..HEAD'])
    const ui = await $.ui.mount<'terminal', 'AbovePrompt'>(BAND as never)
    expect(JSON.stringify(await ui.drawn())).toContain('flowie sync pending (wellbeing: 2026-10-06)')
    await $.turn.complete(TURN as never)
    expect(seen.git.slice(2)).toEqual(['config --get core.hooksPath', 'add -- wellbeing/2026-10-06.json', 'commit -m wellbeing: 2026-10-06 -- wellbeing/2026-10-06.json', 'pull --rebase', 'push'])
    expect(asQueue(seen.store.get(SYNC_QUEUE))).toEqual([])
    expect(fs.files[LOG]).toContain('synced: wellbeing/2026-10-06.json (mod)')
    expect(JSON.stringify(await ui.drawn())).not.toContain('flowie sync pending')
    await ui.unmount()
  })

  test('a queued sync that a sync elsewhere settled is dropped as the session starts', { options: { runtime: 'observe', band: 'quiet' } }, async ($, on) => {
    fakeFs(on, { ...IDEAS, [`${FLOWIE}/wellbeing/2026-10-06.json`]: '{}\n' }, ROOT)
    const seen = session(on, args => (args[0] === 'rev-list' ? { exitCode: 0, stdout: '0\n', stderr: '' } : ok), {
      [SYNC_QUEUE]: [{ paths: ['wellbeing/2026-10-06.json'], message: 'wellbeing: 2026-10-06', at: 1 }],
    })
    await $.session.start({ cwd: ROOT, surface: 'terminal', isInteractive: true })
    expect(asQueue(seen.store.get(SYNC_QUEUE))).toEqual([])
    await $.turn.complete(TURN as never)
    expect(seen.git).toEqual(['status --porcelain -- wellbeing/2026-10-06.json', 'rev-list --count @{u}..HEAD'])
  })
})

// ── before a neuroflow command ────────────────────────────────────────────────────────────────

/** The project on an older neuroflow than the one running: the band and the dashboard offer m. */
const BEHIND = {
  ...FILES,
  [`${ROOT}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nproject_name: Oddball\nactive_phase: data\nplugin_version: 0.2.21\n---\n',
  // Not named "neuroflow": the pattern also matches the project, which would then read as the plugin's own repo.
  '*/.claude-plugin/plugin.json': '{"name": "neuroflow-fixture", "version": "0.2.22"}',
  '*/commands/idk.md': '---\nname: idk\nphase: utility\nlifecycle: quiet\n---\n',
}
const DASHBOARD = {
  plugin: 'neuroflow',
  surface: 'terminal',
  component: 'Pane',
  requestId: 'nf-dashboard',
  props: { title: 'neuroflow', isFocused: true, bodyColumns: 160, placement: 'inline', scroll: { offset: 0, bodyRows: 16 }, view: {} },
}
const SYNC = [
  'config --get core.hooksPath',
  'add -- wellbeing/2026-10-07.json wellbeing/.flow',
  'commit -m wellbeing: 2026-10-07 -- wellbeing/2026-10-07.json wellbeing/.flow',
  'pull --rebase',
  'push',
]
const noHooks = (args: readonly string[]): NfRun => (args[0] === 'config' ? { exitCode: 1, stdout: '', stderr: '' } : ok)

describe('the sync before a neuroflow command', () => {
  test('a check-in, then /neuroflow:migrate typed before any turn ends: commit, pull and push run before its turn', { options: { runtime: 'observe', band: 'quiet' } }, async ($, on) => {
    // The morning that was reported: the command's `git pull --rebase` met the check-in's uncommitted files.
    const fs = fakeFs(on, BEHIND, ROOT)
    const seen = session(on, noHooks)
    const reached: { text: string; git: string[] }[] = []
    on('prompt.submit', ($, e) => {
      reached.push({ text: e.text, git: [...seen.git] })
      return { text: e.text }
    })
    await $.session.start({ cwd: ROOT, surface: 'terminal', isInteractive: true })
    const ui = await $.ui.mount<'terminal', 'AbovePrompt'>(BAND as never)
    await ui.input({ key: 'nf-wellbeing', text: '3 6 7' })
    expect(seen.git).toEqual([])
    // A prompt that is no command leaves the sync to its turn's end; so do a command typed over a running turn and a quiet one.
    await $.prompt.submit({ text: 'what changed in the analysis?', origin: { kind: 'composer' } } as never)
    await $.command.run({ command: 'neuroflow:migrate', args: '' } as never)
    await $.prompt.submit({ text: '/neuroflow:migrate', origin: { kind: 'composer' }, turnId: 't0' } as never)
    await $.command.run({ command: 'neuroflow:idk', args: '' } as never)
    await $.prompt.submit({ text: '/neuroflow:idk', origin: { kind: 'composer' } } as never)
    expect(seen.git).toEqual([])
    // Typed while no turn runs: the sync goes first, then the command reaches the model.
    await $.command.run({ command: 'neuroflow:migrate', args: '' } as never)
    await $.prompt.submit({ text: '/neuroflow:migrate', origin: { kind: 'composer' } } as never)
    expect(reached[reached.length - 1]).toEqual({ text: '/neuroflow:migrate', git: SYNC })
    expect(asQueue(seen.store.get(SYNC_QUEUE))).toEqual([])
    expect(fs.files[LOG]).toMatch(/synced: wellbeing\/2026-10-07\.json wellbeing\/\.flow \(mod\)\n$/)
    await ui.unmount()
  })

  test('while a sync waits, m on the band and on the dashboard puts /neuroflow:migrate in the prompt; once synced, m runs it', { options: { runtime: 'observe', band: 'normal' } }, async ($, on) => {
    // A key's command does not pass the mod's own hooks: sent with Enter, it does.
    fakeFs(on, BEHIND, ROOT)
    const seen = session(on, noHooks)
    const filled: string[] = []
    on('prompt.fill', ($, e) => {
      filled.push(e.text)
      return { isFilled: true, text: e.text, cursor: e.text.length }
    })
    on('ui.open', () => ({ value: { isPlaced: true } }))
    await $.session.start({ cwd: ROOT, surface: 'terminal', isInteractive: true })
    const ui = await $.ui.mount<'terminal', 'AbovePrompt'>(BAND as never)
    await ui.input({ key: 'nf-wellbeing', text: '3 6 7' })
    const drawn = JSON.stringify(await ui.drawn())
    expect(drawn).toContain('flowie sync pending (wellbeing: 2026-10-07)')
    expect(drawn).toContain('this project is on 0.2.21')
    await ui.press({ key: 'nf-migrate' })
    expect(filled).toEqual(['/neuroflow:migrate'])
    expect(seen.toasts.join(' ')).toContain('press Enter to run it — your flowie sync goes first')
    await $.command.run({ command: 'neuroflow:dashboard', args: '' } as never)
    const pane = await $.ui.mount<'terminal', 'Pane'>(DASHBOARD as never)
    await pane.press({ key: 'nf-dash-migrate' })
    expect(filled).toEqual(['/neuroflow:migrate', '/neuroflow:migrate'])
    expect(seen.ran).toEqual([])
    expect(seen.git).toEqual([])
    // A turn ends: the sync runs, and the keys run the command again.
    await $.turn.complete(TURN as never)
    expect(seen.git).toEqual(SYNC)
    await ui.press({ key: 'nf-migrate' })
    await pane.press({ key: 'nf-dash-migrate' })
    expect(seen.ran).toEqual(['neuroflow:migrate', 'neuroflow:migrate'])
    expect(filled).toHaveLength(2)
    await pane.unmount()
    await ui.unmount()
  })

  test('only a waiting sync turns a key into a prompt: a held one does not', () => {
    expect(keyFillsPrompt({ pending: ['wellbeing: 2026-10-07'], failure: null, isHeld: false })).toBe(true)
    expect(keyFillsPrompt({ pending: ['idea: inbox'], failure: 'push failed — fatal: could not resolve host', isHeld: true })).toBe(false)
    expect(keyFillsPrompt({ pending: [], failure: null, isHeld: false })).toBe(false)
    expect(keyFillsPrompt(null)).toBe(false)
  })

  test('two flushes never run at once: a command typed while a turn\'s end still syncs waits for that sync', { options: { runtime: 'observe', band: 'quiet' } }, async ($, on) => {
    fakeFs(on, FILES, ROOT)
    let release: () => void = () => undefined
    const gate = new Promise<void>(resolve => {
      release = resolve
    })
    let isFirstPull = true
    const seen = session(on, async args => {
      if (args[0] === 'pull' && isFirstPull) {
        isFirstPull = false
        await gate
      }
      return noHooks(args)
    })
    const reached: string[][] = []
    on('prompt.submit', ($, e) => {
      reached.push([...seen.git])
      return { text: e.text }
    })
    await $.session.start({ cwd: ROOT, surface: 'terminal', isInteractive: true })
    const ui = await $.ui.mount<'terminal', 'AbovePrompt'>(BAND as never)
    await ui.input({ key: 'nf-wellbeing', text: '3 6 7' })
    const ending = $.turn.complete(TURN as never)
    await seen.clock.settle()
    expect(seen.git).toEqual(SYNC.slice(0, 4))
    await $.command.run({ command: 'neuroflow:migrate', args: '' } as never)
    const sending = $.prompt.submit({ text: '/neuroflow:migrate', origin: { kind: 'composer' } } as never)
    await seen.clock.settle()
    // The command waits; no second git run starts beside the first.
    expect(reached).toEqual([])
    expect(seen.git).toEqual(SYNC.slice(0, 4))
    release()
    await ending
    await sending
    expect(reached).toEqual([SYNC])
    expect(seen.git).toEqual(SYNC)
    await ui.unmount()
  })
})
