// Scope and snapshot — the plumbing every feature reads (charter: project-only activation).
// session.start decides whether the mod acts here and loads the typed snapshot of .neuroflow/;
// writes into .neuroflow/ and every turn's end refresh it; neuroflow commands are tracked so
// features know which command a turn belongs to and its lifecycle (neuroflow-core → C6).
//
// Pattern every feature file follows: `$` never leaves the file it is used in (the validator
// follows it only into functions declared in the same file), so each file builds its own NfIo
// with an `ioOf($)` like the one below and hands that to the shared helpers in ../lib.
import { atom, read, update } from 'claude-code'
import type { EngineInterface, On } from 'claude-code'

import { asString, parseYamlSubset, splitFrontmatter } from '../lib/frontmatter'
import type { NfIo } from '../lib/io'
import type { NfOptions } from '../lib/options'
import { isInside, join, resolveFrom } from '../lib/paths'
import { computeScope, loadSnapshot } from '../lib/project'

const WRITE_TOOLS = new Set(['Write', 'Edit', 'MultiEdit', 'NotebookEdit'])

// State references live in the file that reads them: the validator reads only literal references
// declared in the same file. The contract they follow is types/index.d.ts.
const scopeAtom = atom({ plugin: 'neuroflow', key: 'scope' } as const, null)
const snapshotAtom = atom({ plugin: 'neuroflow', key: 'snapshot' } as const, null)
const activeCommandAtom = atom({ plugin: 'neuroflow', key: 'activeCommand' } as const, null)
const turnWritesAtom = atom({ plugin: 'neuroflow', key: 'turnWrites' } as const, [])

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

/** Reloads the snapshot when the mod is active. Never throws. */
export const refreshSnapshot = async ($: EngineInterface): Promise<void> => {
  const scope = await read($, scopeAtom)
  if (!scope?.isActive || scope.root === null) return
  const snapshot = await loadSnapshot(ioOf($), scope.root)
  await update($, snapshotAtom, () => snapshot)
}

/** The lifecycle a neuroflow command declares in its frontmatter (C6); 'full' when unreadable. */
const commandLifecycle = async ($: EngineInterface, name: string): Promise<string> => {
  const text = await ioOf($).read(join($.plugin.root, 'commands', `${name}.md`))
  const { block } = splitFrontmatter(text ?? '')
  return asString(block === null ? null : parseYamlSubset(block).lifecycle) ?? 'full'
}

export const registerScope = (on: On, _opts: NfOptions): void => {
  on('session.start', async ($, e, next) => {
    // A person is present when something draws (the desktop app hosts the engine headless but
    // has a person and a surface), not only under the REPL. Features re-check before asking.
    const surfaces = await $.session.surfaces()
    const scope = await computeScope(ioOf($), e.cwd, e.isInteractive || surfaces.length > 0)
    await update($, scopeAtom, () => scope)
    await update($, turnWritesAtom, () => [])
    await update($, activeCommandAtom, () => null)
    if (scope.isActive) await refreshSnapshot($)
    return next(e)
  }).catch(($, e, next) => next(e))

  on('command.run', async ($, e, next) => {
    if (!e.command.startsWith('neuroflow:')) return next(e)
    const name = e.command.slice('neuroflow:'.length)
    const lifecycle = await commandLifecycle($, name)
    const startedAt = await $.clock.now()
    await update($, activeCommandAtom, () => ({ name, lifecycle, startedAt }))
    const result = await next(e)
    // Answered by a hook (no engine run behind it): no model turn follows, so the command is over.
    if (result.ref === undefined) await update($, activeCommandAtom, () => null)
    return result
  }).catch(($, e, next) => next(e))

  on('tool.call', async ($, e, next) => {
    const result = await next(e)
    if (!WRITE_TOOLS.has(String(e.tool)) || result.isError === true) return result
    const input = e as unknown as { file_path?: string; notebook_path?: string }
    const path = input.file_path ?? input.notebook_path
    const scope = await read($, scopeAtom)
    if (path === undefined || !scope?.isActive || scope.root === null) return result
    const absolute = resolveFrom(await $.session.cwd(), path)
    await update($, turnWritesAtom, list => (list.includes(absolute) ? list : [...list, absolute].slice(-200)))
    if (isInside(absolute, join(scope.root, '.neuroflow'))) await refreshSnapshot($)
    return result
  }).catch(($, e, next) => next(e))

  on('turn.complete', async ($, e, next) => {
    const result = await next(e)
    await refreshSnapshot($)
    await update($, turnWritesAtom, () => [])
    await update($, activeCommandAtom, () => null)
    return result
  }).catch(($, e, next) => next(e))
}
