// Capture and checks — small helpers around the commands, each cheap and deterministic.
//  - M001: a command's `requires:` (C6) that are missing are named to the model and the person — warn-only
//  - M157: after a command's turn, its first `next:` command is proposed as the next prompt (ghost text)
//  - M034: a scholar run's closing [REPORT downloaded=… files=… stubs=…] line is checked against the disk
//  - M101: a reminder when pinned literature queries in .neuroflow/ideation/watch.md go unchecked for a week
// Zero-turn note and idea capture (M104, M149) and the citation trigger (M030, G107, G101) live here too.
import { atom, read, update } from 'claude-code'
import type { EngineInterface, On } from 'claude-code'

import { asList, parseYamlSubset, splitFrontmatter } from '../lib/frontmatter'
import type { NfIo } from '../lib/io'
import { appendLine, sessionLine, sessionLogPath } from '../lib/memory'
import type { NfOptions } from '../lib/options'
import { join } from '../lib/paths'

const scopeAtom = atom({ plugin: 'neuroflow', key: 'scope' } as const, null)
const snapshotAtom = atom({ plugin: 'neuroflow', key: 'snapshot' } as const, null)
const activeCommandAtom = atom({ plugin: 'neuroflow', key: 'activeCommand' } as const, null)
const captureAtom = atom({ plugin: 'neuroflow', key: 'capture' } as const, null)

/** The flag a /notes or /meeting --notes live capture writes (phase-notes → Live capture); empty = off. */
export const CAPTURE_FLAG = '.neuroflow/notes/.capturing'

/** One inbox line, exactly as /notes --idea writes it. */
export const ideaLine = (ms: number, phase: string | null, text: string): string => {
  const d = new Date(ms)
  const two = (n: number): string => String(n).padStart(2, '0')
  return `- ${d.getFullYear()}-${two(d.getMonth() + 1)}-${two(d.getDate())} ${two(d.getHours())}:${two(d.getMinutes())} [${phase ?? 'none'}] ${text.trim()}`
}

/** `{path}` or `{path}#Notes` from the capture flag; null when capture is off. */
export const captureTarget = (flag: string | null): { path: string; section: string | null } | null => {
  const line = (flag ?? '').split(/\r?\n/)[0].trim()
  if (line === '') return null
  const [path, section] = line.split('#')
  return { path: path.trim(), section: section ? `## ${section.trim()}` : null }
}

/** Messages that end or bypass capture and go to the model: commands and done/finish. */
export const isCaptureExit = (text: string): boolean => /^\s*\//.test(text) || /^\s*(done|finish(ed)?)\s*[.!]?\s*$/i.test(text)

/** The document with `entry` appended at the end of `heading`'s section (before the next `## `), or at the end. */
export const appendToSection = (doc: string, heading: string | null, entry: string): string => {
  const body = doc.endsWith('\n') || doc === '' ? doc : `${doc}\n`
  if (heading === null) return `${body}${entry}\n`
  const lines = body.split('\n')
  const at = lines.findIndex(line => line.trim() === heading)
  if (at < 0) return `${body}\n${heading}\n\n${entry}\n`
  let end = lines.findIndex((line, index) => index > at && /^##\s/.test(line))
  if (end < 0) end = lines.length - 1
  while (end > at + 1 && lines[end - 1].trim() === '') end -= 1
  lines.splice(end, 0, entry)
  return lines.join('\n')
}

/** Count of `[HH:MM]` entries in a capture target (or its section). */
export const captureCount = (doc: string, heading: string | null): number => {
  const lines = doc.split(/\r?\n/)
  const start = heading === null ? 0 : lines.findIndex(line => line.trim() === heading)
  if (start < 0) return 0
  let count = 0
  for (const line of lines.slice(start + (heading === null ? 0 : 1))) {
    if (heading !== null && /^##\s/.test(line)) break
    if (/^\[\d{2}:\d{2}\]\s/.test(line)) count += 1
  }
  return count
}

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
  list: path => $.fs.list(path).then(entries => entries.map(entry => ({ name: entry.name, isDir: entry.kind === 'dir' || String(entry.kind) === 'directory' })), () => []),
  write: (path, text) => $.fs.write(path, text),
  home: async () => (await $.env.get('HOME')) ?? (await $.env.get('USERPROFILE')),
  now: () => $.clock.now(),
  run: (argv, init) => $.process.run(argv, init),
  pluginRoot: $.plugin.root,
})

const keysOf = async ($: EngineInterface, name: string): Promise<CommandKeys> =>
  commandKeys(await ioOf($).read(join($.plugin.root, 'commands', `${name}.md`)))

/**
 * Commits one file in the personal flowie repository and syncs it (the mod's own cache — charter: mod git
 * only there). Skipped when the repository has git hooks or LFS, which $.process.run would bypass.
 */
const syncFlowie = async ($: EngineInterface, flowie: string, file: string, message: string): Promise<string> => {
  const git = (args: readonly string[]) =>
    $.process.run(['git', '-C', flowie, ...args], { timeoutMs: 30_000 }).catch(error => ({ exitCode: 1, stdout: '', stderr: String(error) }))
  const hooksPath = (await git(['config', '--get', 'core.hooksPath'])).stdout.trim()
  const hooks = (await ioOf($).list(`${flowie}/.git/hooks`)).filter(entry => !entry.name.endsWith('.sample'))
  const attributes = (await ioOf($).read(`${flowie}/.gitattributes`)) ?? ''
  if (hooksPath !== '' || hooks.length > 0 || /filter=lfs/.test(attributes)) return 'saved locally — this flowie repository uses git hooks or LFS, so sync it with /neuroflow:flowie --sync'
  for (const args of [['add', '--', file], ['commit', '-m', message, '--', file], ['pull', '--rebase'], ['push']]) {
    const run = await git(args)
    if (run.exitCode !== 0 && !(args[0] === 'commit' && /nothing to commit/i.test(`${run.stdout}${run.stderr}`))) {
      const home = (await ioOf($).home()) ?? ''
      const first = `${run.stderr}${run.stdout}`.trim().split(/\r?\n/)[0] ?? ''
      await appendLine(ioOf($), `${home}/.neuroflow/flowie-sync.log`, `${new Date(await $.clock.now()).toISOString()} git ${args[0]} failed: ${first}`)
      return 'saved locally; the sync failed and was logged — /neuroflow:flowie --sync resolves it'
    }
  }
  return 'synced'
}

/** Appends one idea to the inbox (flowie when set up, else the project), exactly as /notes --idea does. */
const saveIdea = async ($: EngineInterface, text: string): Promise<string> => {
  const scope = await read($, scopeAtom)
  const snap = await read($, snapshotAtom)
  const io = ioOf($)
  const home = (await io.home()) ?? ''
  const flowie = `${home}/.neuroflow/flowie`
  const toFlowie = home !== '' && (await io.exists(`${flowie}/.git`))
  if (!toFlowie && (scope?.root === null || scope === null)) return 'No inbox here: set up flowie, or run this inside a neuroflow project.'
  const path = toFlowie ? `${flowie}/ideas-inbox.md` : join(scope?.root as string, '.neuroflow/notes/ideas-inbox.md')
  if (!(await io.exists(path))) await io.write(path, '# Ideas inbox\n\n')
  const now = await io.now()
  await appendLine(io, path, ideaLine(now, snap?.phase ?? null, text))
  const count = ((await io.read(path)) ?? '').split(/\r?\n/).filter(line => line.startsWith('- ')).length
  if (scope?.root) await appendLine(io, sessionLogPath(scope.root, now), sessionLine(now, 'notes', `idea captured (${toFlowie ? 'flowie inbox' : 'project inbox'})`))
  const synced = toFlowie ? ` · ${await syncFlowie($, flowie, 'ideas-inbox.md', 'idea: inbox')}` : ' · project inbox (shared with collaborators)'
  return `Idea saved — inbox: ${count}${synced}`
}

/** Appends one live-capture message to the target named by the capture flag; returns the entry count. */
const captureMessage = async ($: EngineInterface, root: string, target: { path: string; section: string | null }, text: string): Promise<number> => {
  const io = ioOf($)
  const path = join(root, target.path)
  const now = new Date(await io.now())
  const stamp = `[${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}]`
  const doc = (await io.read(path)) ?? ''
  const next = appendToSection(doc, target.section, `${stamp} ${text.replace(/\r\n/g, '\n').trimEnd()}`)
  await io.write(path, next)
  const after = (await io.read(path)) ?? ''
  if (!after.includes(`${stamp} ${text.replace(/\r\n/g, '\n').trimEnd()}`)) throw new Error('the capture did not land in the file')
  return captureCount(after, target.section)
}

export const registerCapture = (on: On, _opts: NfOptions): void => {
  // M149: `/neuroflow:notes --idea "…"` saves the idea without a model turn.
  on('command.run', { command: 'neuroflow:notes' }, async ($, e, next) => {
    const match = /^--idea\s+(.+)$/s.exec(e.args.trim())
    if (match === null) return next(e)
    const text = match[1].trim().replace(/^["“](.*)["”]$/s, '$1')
    return { text: await saveIdea($, text) }
  }).catch(($, e, next) => next(e))

  // M149 + M104: typed messages the person sends — `idea: …` goes to the inbox, and while a live capture
  // runs every message is written to the notes verbatim instead of reaching the model.
  on('prompt.submit', { origin: { kind: ['composer', 'bridge'] } }, async ($, e, next) => {
    const scope = await read($, scopeAtom)
    if (!scope?.isActive || scope.root === null || (await read($, activeCommandAtom))?.lifecycle === 'quiet') return next(e)
    const idea = /^\s*idea:\s*(.+)$/is.exec(e.text)
    if (idea !== null) {
      try {
        return { drop: await saveIdea($, idea[1]) }
      } catch {
        return { drop: 'neuroflow: the idea could not be saved — nothing was sent to the model; try again or use /neuroflow:notes --idea' }
      }
    }
    const target = captureTarget(await ioOf($).read(join(scope.root, CAPTURE_FLAG)))
    if (target === null) {
      if ((await read($, captureAtom)) !== null) await update($, captureAtom, () => null)
      return next(e)
    }
    if (isCaptureExit(e.text)) return next(e)
    try {
      const count = await captureMessage($, scope.root, target, e.text)
      await update($, captureAtom, () => ({ target: target.path, count }))
      return { drop: `✓ ${count}` }
    } catch {
      // Note text must never reach the model as an instruction: drop it, visibly.
      return { drop: `neuroflow: could not write this note to ${target.path} — it was NOT sent to the model; try again` }
    }
  }).catch(($, e, next) => next(e))

  // M001: name missing `requires:` — to the model as a note on the command's prompt, to the person as a toast. A
  // command that opens a prompt drops an answer a hook gives after next(), so the note rides on prompt.submit, which
  // follows command.run for the same run with the slash command as its text. Only commands a person typed or a
  // headless run gave (the context notes in context.ts take every origin).
  on('prompt.submit', { origin: { kind: ['composer', 'bridge', 'sdk'] } }, async ($, e, next) => {
    const typed = /^\s*\/(?:neuroflow:)?([a-z0-9-]+)/i.exec(e.text) // with or without the plugin prefix, as context.ts
    if (typed === null) return next(e)
    const scope = await read($, scopeAtom)
    const command = await read($, activeCommandAtom)
    if (!scope?.isActive || scope.root === null || command === null || command.name !== typed[1].toLowerCase()) return next(e)
    const { requires } = await keysOf($, command.name)
    const missing: string[] = []
    for (const path of requires) if (!(await ioOf($).exists(join(scope.root, path.replace(/\{[^}]+\}/g, ''))))) missing.push(path)
    if (missing.length === 0) return next(e)
    if (!scope.isHeadless) $.ui.toast(`neuroflow: /neuroflow:${command.name} usually starts from ${missing.join(', ')} — not found`)
    const note = `neuroflow: this command expects ${missing.join(', ')}, which does not exist yet. Say so, offer the command that produces it, and continue only if the person wants to (requires: is advisory, never a block).`
    return next({ ...e, context: [...(e.context ?? []), note] })
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
