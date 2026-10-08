// Bookkeeping — fill the gaps the model left, never more (M006; charter: the prose still says to log).
// When a neuroflow command's turn ends and the model wrote no session line for it, or created files
// in a phase folder without listing them in that folder's flow.md, the mod adds the missing line or
// rows, marked "(auto)". Only with runtime `on`; never for `lifecycle: quiet` commands or subagent turns.
// Durable at once: written when the turn ends, never deferred to session end (charter rule 26).
// The decision drafter (M009) also lives here.
import { atom, read, update } from 'claude-code'
import type { EngineInterface, On } from 'claude-code'

import type { NfIo } from '../lib/io'
import { appendLine, clockTime, isoDate, sessionLine, sessionLogPath } from '../lib/memory'
import { mayWrite } from '../lib/options'
import type { NfOptions } from '../lib/options'
import { join, relativeTo } from '../lib/paths'

const scopeAtom = atom({ plugin: 'neuroflow', key: 'scope' } as const, null)
const activeCommandAtom = atom({ plugin: 'neuroflow', key: 'activeCommand' } as const, null)
const turnWritesAtom = atom({ plugin: 'neuroflow', key: 'turnWrites' } as const, [])
const baselineAtom = atom({ plugin: 'neuroflow', key: 'reasoningBaseline' } as const, null)
const draftAtom = atom({ plugin: 'neuroflow', key: 'draftedDecision' } as const, null)

/** Files a flow.md never lists: logs, indexes and placeholders. */
const UNLISTED = /(^|\/)(flow\.md|\.gitkeep|index\.md|log\.md)$/

/**
 * For files written under `.neuroflow/<folder>/`, the flow.md rows that are missing, grouped by the
 * flow.md that should list them. `flows` maps a flow.md path to its current text (null when absent).
 */
export const missingFlowRows = (
  root: string,
  writes: readonly string[],
  flows: Readonly<Record<string, string | null>>,
  command: string,
  date: string,
): Record<string, string[]> => {
  const out: Record<string, string[]> = {}
  for (const file of writes) {
    const rel = relativeTo(file, join(root, '.neuroflow'))
    if (rel === null || UNLISTED.test(rel)) continue
    const [folder, ...rest] = rel.split('/')
    if (rest.length === 0 || folder === 'sessions' || folder === 'reasoning') continue
    const flowPath = join(root, '.neuroflow', folder, 'flow.md')
    const listed = flows[flowPath] ?? ''
    const name = rest.join('/')
    const base = rest[rest.length - 1]
    if (listed.includes(name) || listed.includes(base)) continue
    const row = `| ${name} | Written by /neuroflow:${command} ${'(auto)'} | ${date} |`
    if (!(out[flowPath] ?? []).includes(row)) out[flowPath] = [...(out[flowPath] ?? []), row]
  }
  return out
}

/** True when the session log has a `## HH:MM — [tag]` line at or after `since` (HH:MM). */
export const hasSessionLineSince = (log: string, tags: readonly string[], since: string): boolean =>
  log.split(/\r?\n/).some(line => {
    const match = /^## (\d{2}:\d{2}) — \[([^\]]+)\]/.exec(line)
    return match !== null && match[1] >= since && tags.includes(match[2])
  })

const countLines = (text: string | null): number => (text ?? '').split(/\r?\n/).filter(line => line.trim() !== '').length

/** The decision drafter's instructions (M009): extract, never invent; one decision or none. */
export const DRAFT_SYSTEM = [
  "You read the end of a research assistant's work log and extract the single most significant research decision it records:",
  'a method, test, threshold, parameter, design or scope choice — with what was considered and rejected, when the text says so.',
  'Use only what the text states; never invent or infer a decision. Ignore routine actions (saving files, fixing typos, running scripts).',
  'Answer with JSON only: {"statement": "<one sentence>", "reasoning": "<one or two sentences>"}, or {"statement": null} when the text records no such decision.',
].join(' ')

/** Parses the drafter's reply; null when it found no decision or the reply is not usable. */
export const parseDraft = (text: string): { statement: string; reasoning: string } | null => {
  const match = /\{[\s\S]*\}/.exec(text)
  if (match === null) return null
  try {
    const value = JSON.parse(match[0]) as { statement?: unknown; reasoning?: unknown }
    if (typeof value.statement !== 'string' || value.statement.trim() === '') return null
    const reasoning = typeof value.reasoning === 'string' ? value.reasoning.trim() : ''
    return { statement: value.statement.trim().slice(0, 300), reasoning: reasoning.slice(0, 600) }
  } catch {
    return null
  }
}

const ioOf = ($: EngineInterface): NfIo => ({
  read: path => $.fs.read(path).then(text => (typeof text === 'string' ? text : null), () => null),
  exists: path => $.fs.exists(path).catch(() => false),
  list: path => $.fs.list(path).then(entries => entries.map(entry => ({ name: entry.name, isDir: entry.kind === 'directory' })), () => []),
  write: (path, text) => $.fs.write(path, text),
  home: async () => (await $.env.get('HOME')) ?? (await $.env.get('USERPROFILE')),
  now: () => $.clock.now(),
  run: (argv, init) => $.process.run(argv, init),
  pluginRoot: $.plugin.root,
})

export const registerBookkeeping = (on: On, opts: NfOptions): void => {
  // Remember how long the command's reasoning log was when it started (M009).
  on('command.run', { command: /^neuroflow:/ }, async ($, e, next) => {
    const scope = await read($, scopeAtom)
    const command = await read($, activeCommandAtom)
    if (scope?.isActive && scope.root !== null && command !== null && command.phase !== 'utility') {
      const path = join(scope.root, '.neuroflow/reasoning', `${command.phase}.jsonl`)
      const lines = countLines(await ioOf($).read(path))
      await update($, baselineAtom, () => ({ path, lines }))
    } else await update($, baselineAtom, () => null)
    return next(e)
  }).catch(($, e, next) => next(e))

  on('turn.complete', { reason: 'answer' }, async ($, e, next) => {
    const result = await next(e)
    if (!mayWrite(opts) || e.agentId !== undefined) return result
    const scope = await read($, scopeAtom)
    const command = await read($, activeCommandAtom)
    if (!scope?.isActive || scope.root === null || command === null || command.lifecycle === 'quiet') return result
    const writes = await read($, turnWritesAtom)
    if (command.lifecycle === 'light' && writes.length === 0) return result

    const io = ioOf($)
    const now = await io.now()
    const filled: string[] = []
    const logPath = sessionLogPath(scope.root, now)
    const log = (await io.read(logPath)) ?? ''
    const tags = [command.phase, command.name]
    if (!hasSessionLineSince(log, tags, clockTime(command.startedAt))) {
      const tag = command.phase === 'utility' ? command.name : command.phase
      const what = writes.length > 0 ? `/neuroflow:${command.name} wrote ${writes.length} file(s)` : `/neuroflow:${command.name} ran`
      if ((await appendLine(io, logPath, sessionLine(now, tag, what))) === 'written') filled.push('a session line')
    }

    const flowPaths = [...new Set(writes.map(file => relativeTo(file, join(scope.root as string, '.neuroflow'))).filter((rel): rel is string => rel !== null && rel.includes('/')).map(rel => join(scope.root as string, '.neuroflow', rel.split('/')[0], 'flow.md')))]
    const flows: Record<string, string | null> = {}
    for (const path of flowPaths) flows[path] = await io.read(path)
    const rows = missingFlowRows(scope.root, writes, flows, command.name, isoDate(now))
    for (const [flowPath, lines] of Object.entries(rows)) {
      if (flows[flowPath] === null) await io.write(flowPath, '| File / Folder | Description | Last changed |\n|---|---|---|\n')
      for (const line of lines) if ((await appendLine(io, flowPath, line)) === 'written') filled.push(`a flow row in ${flowPath.split('/').slice(-2, -1)[0]}/flow.md`)
    }
    if (filled.length > 0) $.ui.log(`neuroflow: filled ${filled.join(', ')} (auto)`)

    // M009: the command logged no decision — draft one for a person to keep or drop (never written unasked).
    const baseline = await read($, baselineAtom)
    await update($, baselineAtom, () => null)
    const isPersonThere = !scope.isHeadless && (await $.session.surfaces()).length > 0
    if (baseline !== null && command.lifecycle === 'full' && isPersonThere && (await read($, draftAtom)) === null && e.answer.trim().length > 200) {
      if (countLines(await io.read(baseline.path)) <= baseline.lines) {
        const reply = await $.model.complete({ model: await $.session.model(), system: DRAFT_SYSTEM, prompt: e.answer.slice(-8000), maxTokens: 400, timeoutMs: 30_000 })
        const draft = reply.isAnswered ? parseDraft(reply.text) : null
        if (draft !== null) {
          await update($, draftAtom, () => ({ path: baseline.path, phase: command.phase, command: command.name, ...draft, at: now }))
          $.ui.toast('neuroflow drafted a decision for the reasoning log — keep it (k) or drop it (n) in the band')
        }
      }
    }
    return result
  }).catch(($, e, next) => next(e))
}
