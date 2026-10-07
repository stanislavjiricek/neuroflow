// Capture and checks — small helpers around the commands, each cheap and deterministic.
//  - M001: a command's `requires:` (C6) that are missing are named to the model and the person — warn-only
//  - M157: after a command's turn, its first `next:` command is proposed as the next prompt (ghost text)
//  - M034: a scholar run's closing [REPORT downloaded=… files=… stubs=…] line is checked against the disk
//  - M101: a reminder when pinned literature queries in .neuroflow/ideation/watch.md go unchecked for a week
// Zero-turn note and idea capture (M104, M149) and the citation trigger (M030, G107, G101) live here too.
import { atom, read } from 'claude-code'
import type { EngineInterface, On } from 'claude-code'

import { asList, parseYamlSubset, splitFrontmatter } from '../lib/frontmatter'
import type { NfIo } from '../lib/io'
import type { NfOptions } from '../lib/options'
import { join } from '../lib/paths'

const scopeAtom = atom({ plugin: 'neuroflow', key: 'scope' } as const, null)
const activeCommandAtom = atom({ plugin: 'neuroflow', key: 'activeCommand' } as const, null)

export type CommandKeys = { requires: string[]; next: string[] }

/** The C6 keys of a command file's frontmatter. */
export const commandKeys = (text: string | null): CommandKeys => {
  const { block } = splitFrontmatter(text ?? '')
  const fm = block === null ? {} : parseYamlSubset(block)
  return { requires: asList(fm.requires), next: asList(fm.next).map(name => name.replace(/^\/?(neuroflow:)?/, '')) }
}

export type ScholarReport = { downloaded: number; files: string[]; stubs: number }

/** The last `[REPORT downloaded=<n> files=<paths|none> stubs=<m>]` line of a scholar reply (agents/scholar.md). */
export const parseScholarReport = (text: string): ScholarReport | null => {
  const lines = text.split(/\r?\n/).filter(line => /^\[REPORT\s+downloaded=/.test(line.trim()))
  const last = lines[lines.length - 1]
  if (last === undefined) return null
  const match = /^\[REPORT\s+downloaded=(\d+)\s+files=(.*?)\s+stubs=(\d+)\]$/.exec(last.trim())
  if (match === null) return null
  const files = match[2].trim() === 'none' ? [] : match[2].split(',').map(file => file.trim()).filter(Boolean)
  return { downloaded: Number(match[1]), files, stubs: Number(match[3]) }
}

/** What does not hold in a scholar report, given which listed files exist and how each starts. */
export const scholarProblems = (report: ScholarReport, found: Readonly<Record<string, { exists: boolean; head: string | null }>>): string[] => {
  const problems: string[] = []
  if (report.files.length !== report.downloaded) problems.push(`the report says ${report.downloaded} download(s) but lists ${report.files.length} file(s)`)
  for (const file of report.files) {
    const where = found[file]
    if (!/^\.neuroflow\/ideation\/papers\/[^/]+\/[^/]+\.(pdf|txt)$/i.test(file)) problems.push(`${file} is not a .pdf or .txt under .neuroflow/ideation/papers/<stem>/`)
    if (where === undefined || !where.exists) problems.push(`${file} does not exist`)
    else if (/\.pdf$/i.test(file) && where.head !== null && !where.head.startsWith('%PDF-')) problems.push(`${file} is not a PDF (it does not start with %PDF-)`)
  }
  return problems
}

/** Pinned watch-list queries whose `Last checked` date is more than `days` old (ideation → Standing queries). */
export const staleWatchQueries = (watchMd: string, nowMs: number, days = 7): { count: number; oldest: number } => {
  let count = 0
  let oldest = 0
  for (const line of watchMd.split(/\r?\n/)) {
    const cells = line.split('|').map(cell => cell.trim())
    if (cells.length < 6 || !/^\d{4}-\d{2}-\d{2}$/.test(cells[4] ?? '')) continue
    const [y, m, d] = cells[4].split('-').map(Number)
    const age = Math.floor((nowMs - new Date(y, m - 1, d).getTime()) / 86_400_000)
    if (age > days) {
      count += 1
      oldest = Math.max(oldest, age)
    }
  }
  return { count, oldest }
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

const keysOf = async ($: EngineInterface, name: string): Promise<CommandKeys> =>
  commandKeys(await ioOf($).read(join($.plugin.root, 'commands', `${name}.md`)))

export const registerCapture = (on: On, _opts: NfOptions): void => {
  // M001: name missing `requires:` — to the model as a note after the command's prompt, to the person as a toast.
  on('command.run', { command: /^neuroflow:/ }, async ($, e, next) => {
    const result = await next(e)
    const scope = await read($, scopeAtom)
    if (!scope?.isActive || scope.root === null || result.ref === undefined) return result
    const { requires } = await keysOf($, e.command.slice('neuroflow:'.length))
    const missing: string[] = []
    for (const path of requires) if (!(await ioOf($).exists(join(scope.root, path.replace(/\{[^}]+\}/g, ''))))) missing.push(path)
    if (missing.length === 0) return result
    if (!scope.isHeadless) $.ui.toast(`neuroflow: /${e.command} usually starts from ${missing.join(', ')} — not found`)
    const note = `neuroflow: this command expects ${missing.join(', ')}, which does not exist yet. Say so, offer the command that produces it, and continue only if the person wants to (requires: is advisory, never a block).`
    return { ...result, context: [...(result.context ?? []), note] }
  }).catch(($, e, next) => next(e))

  // M157: propose the command's first `next:` as the next prompt, after its turn completed normally.
  on('turn.complete', { reason: 'answer', isAborted: false }, async ($, e, next) => {
    const result = await next(e)
    const scope = await read($, scopeAtom)
    const command = await read($, activeCommandAtom)
    if (!scope?.isActive || scope.isHeadless || command === null || command.lifecycle === 'quiet' || e.agentId !== undefined) return result
    const { next: following } = await keysOf($, command.name)
    if (following.length > 0) await $.prompt.suggest({ text: `/neuroflow:${following[0]} ` }).catch(() => undefined)
    return result
  }).catch(($, e, next) => next(e))

  // M034: check the scholar subagent's REPORT line against the disk; tell the model what does not hold.
  on('tool.call', { tool: 'Agent' }, async ($, e, next) => {
    const result = await next(e)
    const input = e as unknown as { subagent_type?: string }
    if (!/scholar$/.test(input.subagent_type ?? '') || result.deny !== undefined) return result
    const scope = await read($, scopeAtom)
    if (!scope?.isActive || scope.root === null) return result
    const text = typeof result.text === 'string' ? result.text : JSON.stringify(result.result ?? '')
    const report = parseScholarReport(text)
    if (report === null) {
      return { ...result, context: [...(result.context ?? []), 'neuroflow: the scholar reply has no [REPORT downloaded=… files=… stubs=…] line, so its download claims were not checked against the disk.'] }
    }
    const found: Record<string, { exists: boolean; head: string | null }> = {}
    for (const file of report.files) {
      const path = join(scope.root, file)
      const exists = await ioOf($).exists(path)
      const head = exists && /\.pdf$/i.test(file) ? await $.fs.read(path, { as: 'bytes' }).then(bytes => atob((bytes as { base64: string }).base64.slice(0, 12)), () => null) : null
      found[file] = { exists, head }
    }
    const problems = scholarProblems(report, found)
    if (problems.length === 0) return result
    if (!scope.isHeadless) $.ui.toast(`neuroflow: the scholar report does not match the disk (${problems.length} problem(s))`)
    return { ...result, context: [...(result.context ?? []), `neuroflow check of the scholar report: ${problems.join('; ')}. Correct the download summary before relying on it.`] }
  }).catch(($, e, next) => next(e))

  // M101: once per interactive session, remind about pinned queries not checked for a week (no searches run).
  on('session.start', { isInteractive: true }, async ($, e, next) => {
    const result = await next(e)
    const scope = await read($, scopeAtom)
    if (!scope?.isActive || scope.root === null) return result
    const watch = await ioOf($).read(join(scope.root, '.neuroflow/ideation/watch.md'))
    if (watch === null) return result
    const stale = staleWatchQueries(watch, await $.clock.now())
    if (stale.count > 0) $.ui.toast(`neuroflow: ${stale.count} pinned literature quer${stale.count === 1 ? 'y' : 'ies'} not checked for ${stale.oldest} days — /neuroflow:ideation can check them`)
    return result
  }).catch(($, e, next) => next(e))
}
