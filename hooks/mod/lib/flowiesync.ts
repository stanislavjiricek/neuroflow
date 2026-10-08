// The mod's own flowie syncs (charter: mod-run git only in the mod's own caches).
//
// A UI closure never runs git. The wellbeing band's Input closure lives only as long as the drawing that holds
// it (the engine keeps an Input's handle "for the lifetime of the drawing"), and the band redraws without the
// field as soon as today's entry exists; so the closure queues the sync, writes the entry and returns. The queue
// lives in $.store, so a sync a session could not run is not lost, and it is flushed from hook dispatches, which
// run to their end: the end of a main-loop turn, the session's start, and the zero-turn idea capture right after
// it queued its own. Every attempt and its outcome is one line of ~/.neuroflow/flowie-sync.log.
import type { NfFlowieSync, NfFlowieSyncEntry } from '../../../types'
import type { NfIo, NfRun } from './io'
import { appendLine } from './memory'

/** The $.store key of the queue. */
export const SYNC_QUEUE = 'flowie.syncQueue'

export const NO_SYNC: NfFlowieSync = { pending: [], failure: null, isHeld: false }

const isEntry = (item: unknown): item is NfFlowieSyncEntry => {
  const entry = item as Partial<NfFlowieSyncEntry> | null
  return entry !== null && typeof entry === 'object' && Array.isArray(entry.paths) && entry.paths.every(path => typeof path === 'string') && typeof entry.message === 'string' && typeof entry.at === 'number'
}

/** The queue as stored; anything malformed under the key reads as nothing queued. */
export const asQueue = (value: unknown): NfFlowieSyncEntry[] => (Array.isArray(value) ? value.filter(isEntry) : [])

/** The queue with `entry` added: one entry per commit message, its paths merged and its time the latest. */
export const enqueue = (queue: readonly NfFlowieSyncEntry[], entry: NfFlowieSyncEntry): NfFlowieSyncEntry[] => {
  const same = queue.find(item => item.message === entry.message)
  if (same === undefined) return [...queue, entry]
  return queue.map(item => (item === same ? { paths: [...new Set([...item.paths, ...entry.paths])], message: item.message, at: Math.max(item.at, entry.at) } : item))
}

/** What stays queued once `done` is settled: what was queued, or queued again, since that copy of the queue was read. */
export const afterFlush = (current: readonly NfFlowieSyncEntry[], done: readonly NfFlowieSyncEntry[]): NfFlowieSyncEntry[] =>
  current.filter(item => !done.some(old => old.message === item.message && old.at === item.at && item.paths.every(path => old.paths.includes(path))))

/**
 * `synced`: drop the entries. `failed`: keep them and hold — no new attempt until something new is queued or the
 * next session starts (phase-flowie: no retry loop). `skipped`: nothing to sync (the files are gone): drop them.
 */
export type FlushOutcome = 'synced' | 'failed' | 'skipped'

export type FlushResult = { outcome: FlushOutcome; detail: string; line: string }

/** The band's state after a flush (or after queueing, with `result` null). */
export const syncState = (queue: readonly NfFlowieSyncEntry[], result: FlushResult | null): NfFlowieSync => ({
  pending: queue.map(entry => entry.message),
  failure: result?.outcome === 'failed' ? result.detail : null,
  isHeld: result?.outcome === 'failed',
})

const firstLine = (run: NfRun): string => (`${run.stderr}\n${run.stdout}`.trim().split(/\r?\n/)[0] ?? '').trim().slice(0, 160)

/** ISO time to the second, as the auto-sync hook writes it. */
const stamp = (ms: number): string => new Date(ms).toISOString().replace(/\.\d{3}Z$/, 'Z')

/** Git's answers for a commit that had nothing to commit (the file was already committed): no failure. */
const NOTHING = /nothing to commit|nothing added to commit|no changes added to commit/i

const flowieOf = (home: string): string => `${home}/.neuroflow/flowie`

/** Runs git in the flowie. Never throws: a call that throws, synchronously or not, reads as a failed run. */
const git = async (io: NfIo, flowie: string, args: readonly string[], timeoutMs = 30_000): Promise<NfRun> => {
  try {
    // No credential prompt can hold the sync: a missing login fails the push, which is logged.
    return await io.run(['git', '-C', flowie, ...args], { timeoutMs, env: { GIT_TERMINAL_PROMPT: '0', GCM_INTERACTIVE: 'never' } })
  } catch (error) {
    return { exitCode: 1, stdout: '', stderr: error instanceof Error ? error.message : String(error) }
  }
}

/**
 * Commits the queued files by path, pulls with rebase and pushes, as the flowie Sync step does (commands/flowie.md →
 * Git operations pattern), and logs the attempt: `{time} synced: {paths} (mod)`, or what stopped it. Never throws.
 * Not run (failed, kept) when the repository uses git hooks or LFS — $.process.run runs git with repo hooks off — or
 * while a rebase or merge is in progress.
 */
export const flushFlowie = async (io: NfIo, home: string, queue: readonly NfFlowieSyncEntry[]): Promise<FlushResult> => {
  const flowie = flowieOf(home)
  // What the log line names: the queued paths, then the ones actually committed once that is known.
  let paths = [...new Set(queue.flatMap(entry => entry.paths))]
  /** `what` heads the log line (the auto-sync hook's words); `why` is git's first line; `detail` what the band says. */
  const finish = async (outcome: FlushOutcome, what: string, why = '', detail = why === '' ? what : `${what} — ${why}`): Promise<FlushResult> => {
    const line = `${stamp(await io.now())} ${what}: ${paths.join(' ')} (mod)${why === '' ? '' : ` — ${why}`}`
    await appendLine(io, `${home}/.neuroflow/flowie-sync.log`, line)
    return { outcome, detail, line }
  }
  const inMiddle = async (): Promise<boolean> =>
    (await io.exists(`${flowie}/.git/rebase-merge`)) || (await io.exists(`${flowie}/.git/rebase-apply`)) || (await io.exists(`${flowie}/.git/MERGE_HEAD`))
  if (!(await io.exists(`${flowie}/.git`))) return finish('skipped', 'skipped (no flowie repository)', '', 'no flowie repository here')
  if (await inMiddle()) return finish('failed', 'skipped (rebase or merge in progress)', '', 'a rebase or merge is in progress in your flowie')
  const hooksPath = (await git(io, flowie, ['config', '--get', 'core.hooksPath'], 10_000)).stdout.trim()
  const hooks = (await io.list(`${flowie}/.git/hooks`)).filter(entry => !entry.name.endsWith('.sample'))
  const attributes = (await io.read(`${flowie}/.gitattributes`)) ?? ''
  if (hooksPath !== '' || hooks.length > 0 || /filter=lfs/.test(attributes)) {
    return finish('failed', 'skipped (git hooks or LFS)', '', 'this flowie uses git hooks or LFS, which the mod does not run')
  }
  const committed: string[] = []
  for (const entry of queue) {
    // A path the writer has not written (it queues before it writes) is no failure: there is nothing to sync yet.
    const present: string[] = []
    for (const path of entry.paths) if (await io.exists(`${flowie}/${path}`)) present.push(path)
    if (present.length === 0) continue
    committed.push(...present.filter(path => !committed.includes(path)))
    const add = await git(io, flowie, ['add', '--', ...present], 15_000)
    if (add.exitCode !== 0) return finish('failed', 'commit failed', firstLine(add))
    const commit = await git(io, flowie, ['commit', '-m', entry.message, '--', ...present], 15_000)
    if (commit.exitCode !== 0 && !NOTHING.test(`${commit.stdout}\n${commit.stderr}`)) return finish('failed', 'commit failed', firstLine(commit))
  }
  if (committed.length === 0) return finish('skipped', 'skipped (no queued file exists)', '', 'the files it queued are gone')
  paths = committed
  const pull = await git(io, flowie, ['pull', '--rebase'])
  if (pull.exitCode !== 0) {
    // Never leave a half-finished rebase (commands/flowie.md → Git operations pattern).
    if (await inMiddle()) await git(io, flowie, ['rebase', '--abort'], 15_000)
    return finish('failed', 'pull failed', firstLine(pull))
  }
  const push = await git(io, flowie, ['push'])
  if (push.exitCode !== 0) return finish('failed', 'push failed', firstLine(push))
  return finish('synced', 'synced')
}

/**
 * Whether a sync that ran elsewhere (/neuroflow:flowie --sync, the auto-sync hook, the person's own git) settled
 * the queue: nothing of its files left to commit, nothing left to push. Local git only, no network.
 */
export const isSettled = async (io: NfIo, home: string, queue: readonly NfFlowieSyncEntry[]): Promise<boolean> => {
  const flowie = flowieOf(home)
  const status = await git(io, flowie, ['status', '--porcelain', '--', ...new Set(queue.flatMap(entry => entry.paths))], 10_000)
  if (status.exitCode !== 0 || status.stdout.trim() !== '') return false
  const ahead = await git(io, flowie, ['rev-list', '--count', '@{u}..HEAD'], 10_000)
  return ahead.exitCode === 0 && ahead.stdout.trim() === '0'
}
