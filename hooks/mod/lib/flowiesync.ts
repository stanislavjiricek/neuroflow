// The mod's own flowie syncs (charter: mod-run git only in the mod's own caches).
//
// A UI closure never runs git. Why the band's wellbeing closure once wrote its entry and ran no git is not known
// for sure, and the engine types narrow it to hypotheses only: $.process.run threw synchronously, which the
// .catch chained on its promise never sees; or the closure's later $ calls stopped or failed once the band redrew
// without the field (the host keeps an Input's handle "for the lifetime of the drawing" — whether a closure that
// is running outlives it, the types do not say). The design holds whichever is true: a closure queues the sync,
// writes the file and returns. The queue lives in $.store, so a sync a session could not run is not lost, and it
// is flushed from hook dispatches: before a neuroflow command's turn, when a main-loop turn ends, and in the
// zero-turn idea capture right after it queued its own. Every attempt and its outcome is one line of
// ~/.neuroflow/flowie-sync.log; a flush that finds nothing to sync writes none.
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
 * next session (phase-flowie: no retry loop). `skipped`: nothing to sync (the files are gone, or the flowie is no
 * repository any more): drop them, log nothing — the log's lines are attempts, and every one but `synced` is a
 * failure /flowie and /doctor report.
 */
export type FlushOutcome = 'synced' | 'failed' | 'skipped'

/** `line` is what went into flowie-sync.log; null when nothing did (`skipped`). */
export type FlushResult = { outcome: FlushOutcome; detail: string; line: string | null }

/** The band's state after a flush (or after queueing, with `result` null). */
export const syncState = (queue: readonly NfFlowieSyncEntry[], result: FlushResult | null): NfFlowieSync => ({
  pending: queue.map(entry => entry.message),
  failure: result?.outcome === 'failed' ? result.detail : null,
  isHeld: result?.outcome === 'failed',
})

/**
 * Why a git run failed, in git's words: the first error, fatal, CONFLICT or rejected line — not the progress lines
 * a pull or push prints first (`From …`, `To …`) — else its first line.
 */
export const gitReason = (run: NfRun): string => {
  const lines = `${run.stderr}\n${run.stdout}`
    .split(/\r?\n/)
    .map(line => line.trim().replace(/\s+/g, ' '))
    .filter(line => line !== '')
  const reason = lines.find(line => /^(error|fatal):|CONFLICT|\[rejected\]|Updates were rejected/i.test(line)) ?? lines[0] ?? ''
  return reason.slice(0, 160)
}

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

/** The hook names git runs (githooks(5)); anything else in .git/hooks, a `.sample` included, is not a hook. */
const GIT_HOOKS = new Set([
  'applypatch-msg', 'pre-applypatch', 'post-applypatch', 'pre-commit', 'pre-merge-commit', 'prepare-commit-msg',
  'commit-msg', 'post-commit', 'pre-rebase', 'post-checkout', 'post-merge', 'pre-push', 'pre-receive', 'update',
  'proc-receive', 'post-receive', 'post-update', 'reference-transaction', 'push-to-checkout', 'pre-auto-gc',
  'post-rewrite', 'sendemail-validate', 'fsmonitor-watchman', 'post-index-change',
])

/**
 * What of git hooks or LFS the flowie repository itself configures, each named for the log (`hooksPath=…`,
 * `hooks: pre-commit`, `lfs`); empty when none. $.process.run runs git with `-c core.hooksPath=<null device>`
 * (seen on Windows as `\\.\NUL`, origin "command line:"), so a value from the command line is the engine's own
 * and never counts — only the repository's, the person's and the system's config do.
 */
export const repoHooksOrLfs = async (io: NfIo, flowie: string): Promise<string[]> => {
  const uses: string[] = []
  const config = await git(io, flowie, ['config', '--show-origin', '--get-all', 'core.hooksPath'], 10_000)
  const configured = config.stdout
    .split(/\r?\n/)
    .filter(line => line.includes('\t') && !/^command line:/i.test(line))
    .map(line => line.slice(line.indexOf('\t') + 1).trim())
  // The last value wins, as for git itself; a null device there turns hooks off.
  const hooksPath = configured[configured.length - 1] ?? ''
  if (hooksPath !== '' && !/^(\\\\\.\\nul|nul|\/dev\/null)$/i.test(hooksPath)) uses.push(`hooksPath=${hooksPath}`)
  const hooks = (await io.list(`${flowie}/.git/hooks`))
    .filter(entry => !entry.isDir)
    .map(entry => entry.name.replace(/^.*[\\/]/, ''))
    .filter(name => GIT_HOOKS.has(name.replace(/\.(exe|cmd|bat|ps1|sh)$/i, '').toLowerCase()))
  if (hooks.length > 0) uses.push(`hooks: ${hooks.sort().join(' ')}`)
  const attributes = `${(await io.read(`${flowie}/.gitattributes`)) ?? ''}\n${(await io.read(`${flowie}/.git/info/attributes`)) ?? ''}`
  if (/filter=lfs/.test(attributes)) uses.push('lfs')
  return uses
}

/**
 * Commits the queued files by path, pulls with rebase and pushes, as the flowie Sync step does (commands/flowie.md →
 * Git operations pattern), and logs the attempt: `{time} synced: {paths} (mod)`, or what stopped it. Never throws.
 * Not run (failed, kept) when the repository uses git hooks or LFS — $.process.run runs git with repo hooks off — or
 * while a rebase or merge is in progress. Nothing to sync (no repository, none of the files) is no attempt: no line.
 */
export const flushFlowie = async (io: NfIo, home: string, queue: readonly NfFlowieSyncEntry[]): Promise<FlushResult> => {
  const flowie = flowieOf(home)
  // What the log line names: the queued paths, then the ones actually committed once that is known.
  let paths = [...new Set(queue.flatMap(entry => entry.paths))]
  /** `what` heads the log line (the auto-sync hook's words); `why` is git's reason; `detail` what the band says. */
  const finish = async (outcome: FlushOutcome, what: string, why = '', detail = why === '' ? what : `${what} — ${why}`): Promise<FlushResult> => {
    const line = `${stamp(await io.now())} ${what}: ${paths.join(' ')} (mod)${why === '' ? '' : ` — ${why}`}`
    await appendLine(io, `${home}/.neuroflow/flowie-sync.log`, line)
    return { outcome, detail, line }
  }
  const nothing = (detail: string): FlushResult => ({ outcome: 'skipped', detail, line: null })
  const inMiddle = async (): Promise<boolean> =>
    (await io.exists(`${flowie}/.git/rebase-merge`)) || (await io.exists(`${flowie}/.git/rebase-apply`)) || (await io.exists(`${flowie}/.git/MERGE_HEAD`))
  if (!(await io.exists(`${flowie}/.git`))) return nothing('no flowie repository here')
  if (await inMiddle()) return finish('failed', 'skipped (rebase or merge in progress)', '', 'a rebase or merge is in progress in your flowie')
  // A file git still marks as conflicted (an autostash that could not go back) is never added: that would commit
  // its conflict markers. /flowie --sync resolves it with the person.
  const unmerged = await git(io, flowie, ['diff', '--name-only', '--diff-filter=U'], 10_000)
  if (unmerged.exitCode === 0 && unmerged.stdout.trim() !== '') {
    return finish('failed', 'skipped (unresolved conflict)', '', `your flowie has an unresolved conflict (${unmerged.stdout.trim().split(/\r?\n/)[0]})`)
  }
  const uses = await repoHooksOrLfs(io, flowie)
  if (uses.length > 0) {
    return finish('failed', `skipped (git hooks or LFS: ${uses.join(', ')})`, '', `this flowie uses git hooks or LFS (${uses.join(', ')}), which the mod does not run`)
  }
  const committed: string[] = []
  for (const entry of queue) {
    // A path the writer has not written (it queues before it writes) is no failure: there is nothing to sync yet.
    const present: string[] = []
    for (const path of entry.paths) if (await io.exists(`${flowie}/${path}`)) present.push(path)
    if (present.length === 0) continue
    committed.push(...present.filter(path => !committed.includes(path)))
    const add = await git(io, flowie, ['add', '--', ...present], 15_000)
    if (add.exitCode !== 0) return finish('failed', 'commit failed', gitReason(add))
    const commit = await git(io, flowie, ['commit', '-m', entry.message, '--', ...present], 15_000)
    if (commit.exitCode !== 0 && !NOTHING.test(`${commit.stdout}\n${commit.stderr}`)) return finish('failed', 'commit failed', gitReason(commit))
  }
  if (committed.length === 0) return nothing('the files it queued are gone')
  paths = committed
  // --autostash: a file held back elsewhere (the auto-sync hook's machine-local-path skip) never stops the pull.
  const pull = await git(io, flowie, ['pull', '--rebase', '--autostash'])
  if (pull.exitCode !== 0) {
    // Never leave a half-finished rebase (commands/flowie.md → Git operations pattern).
    if (await inMiddle()) await git(io, flowie, ['rebase', '--abort'], 15_000)
    return finish('failed', 'pull failed', gitReason(pull))
  }
  const push = await git(io, flowie, ['push'])
  if (push.exitCode !== 0) return finish('failed', 'push failed', gitReason(push))
  // The pull went through, but the uncommitted files it set aside may not have gone back cleanly: say so in the log,
  // which /flowie reports and /flowie --sync resolves with the person.
  const left = await git(io, flowie, ['diff', '--name-only', '--diff-filter=U'], 10_000)
  if (left.exitCode === 0 && left.stdout.trim() !== '') {
    await appendLine(io, `${home}/.neuroflow/flowie-sync.log`, `${stamp(await io.now())} autostash conflict: ${left.stdout.trim().split(/\r?\n/).join(' ')} (mod) — /flowie --sync`)
  }
  return finish('synced', 'synced')
}

/**
 * Whether `path` (a flowie file, e.g. today's wellbeing entry) is already on the flowie's upstream: a fetch, then
 * `git cat-file -e @{u}:{path}`. A fetch only reads remote refs: nothing leaves and the work tree is not touched —
 * the next pull (a command's, or /flowie --sync) brings the file down. `unknown` when the remote could not be asked
 * (offline, no upstream, no repository) or should not be (git hooks or LFS, which the mod does not run; a rebase or
 * merge in progress). Never throws.
 */
export const checkRemoteEntry = async (io: NfIo, home: string, path: string): Promise<'present' | 'absent' | 'unknown'> => {
  const flowie = flowieOf(home)
  if (!(await io.exists(`${flowie}/.git`))) return 'unknown'
  for (const marker of ['rebase-merge', 'rebase-apply', 'MERGE_HEAD']) if (await io.exists(`${flowie}/.git/${marker}`)) return 'unknown'
  // The repository's own hooks or LFS, read from its files (no git run before the fetch decides anything).
  const config = (await io.read(`${flowie}/.git/config`)) ?? ''
  const hooks = (await io.list(`${flowie}/.git/hooks`)).filter(entry => !entry.isDir && GIT_HOOKS.has(entry.name.replace(/^.*[\\/]/, '').replace(/\.(exe|cmd|bat|ps1|sh)$/i, '').toLowerCase()))
  const attributes = (await io.read(`${flowie}/.gitattributes`)) ?? ''
  if (/^\s*hookspath\s*=/im.test(config) || hooks.length > 0 || /filter=lfs/.test(attributes)) return 'unknown'
  const fetch = await git(io, flowie, ['fetch', '--quiet'], 20_000)
  if (fetch.exitCode !== 0) return 'unknown'
  const upstream = await git(io, flowie, ['rev-parse', '--verify', '--quiet', '@{u}'], 10_000)
  if (upstream.exitCode !== 0) return 'unknown'
  const there = await git(io, flowie, ['cat-file', '-e', `@{u}:${path}`], 10_000)
  return there.exitCode === 0 ? 'present' : 'absent'
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
