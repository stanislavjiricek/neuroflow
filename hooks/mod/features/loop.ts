// Loop — the autoresearch driver (M103): one iteration per turn, caps enforced between turns.
// `/neuroflow:autoresearch drive <name>` starts it; every turn runs exactly one iteration, and after
// each answered turn the mod asks the loop's own bookkeeping script (skills/autoresearch/scripts/ar.py
// status — the single executable home of caps, plateau and snapshot logic) whether the next iteration
// may start. It stops at a cap, after max_consecutive_errors errored turns, when the person interrupts a
// turn (Esc), refuses, or presses stop (band key s, or `/neuroflow:autoresearch stop`). Charter: no
// paid turn without a visible cap and a stop control; never restarted without the person.
import { atom, read, update } from 'claude-code'
import type { EngineInterface, On } from 'claude-code'

import type { NfDrive } from '../../../types'
import type { NfIo } from '../lib/io'
import { appendLine, sessionLine, sessionLogPath } from '../lib/memory'
import type { NfOptions } from '../lib/options'
import { resolveFrom } from '../lib/paths'
import { parseJson, runScript } from '../lib/scripts'

const scopeAtom = atom({ plugin: 'neuroflow', key: 'scope' } as const, null)
const snapshotAtom = atom({ plugin: 'neuroflow', key: 'snapshot' } as const, null)
const driveAtom = atom({ plugin: 'neuroflow', key: 'drive' } as const, null)

const AR = 'skills/autoresearch/scripts/ar.py'

/** The prompt each driven turn starts with. */
export const iterationPrompt = (drive: Pick<NfDrive, 'name' | 'location'>, turn: number): string =>
  [
    `Continue the autoresearch loop "${drive.name}" (folder: ${drive.location}) — driven turn ${turn}.`,
    'Run exactly ONE iteration: one full pass of the "## Iteration checklist" in its program.md, with the bookkeeping through ar.py,',
    'then end your turn. Do not start another iteration: the neuroflow mod starts the next one and enforces the caps.',
  ].join(' ')

/** A `max_cost` value in USD ("20 USD", "$20", "20"), or null when absent, n/a or not money. */
export const costCapUsd = (raw: unknown): number | null => {
  if (typeof raw !== 'string') return null
  const match = /^\s*\$?\s*(\d+(?:\.\d+)?)\s*(usd|\$)?\s*$/i.exec(raw)
  return match === null ? null : Number(match[1])
}

export type ArStatus = { findings?: { kind: string; detail: string }[]; caps?: { max_consecutive_errors?: string; max_cost?: string }; iterations?: number }

/** What stops the drive after an answered turn, from ar.py's status (exit code + JSON) and the measured cost. */
export const stopReason = (exitCode: number, status: ArStatus | null, spentUsd: number | null, capUsd: number | null): string | null => {
  if (exitCode === 2 || status === null) return 'the loop bookkeeping (ar.py status) could not run'
  if (exitCode === 1) {
    const findings = status.findings ?? []
    return findings.length > 0 ? findings.map(item => `${item.kind}: ${item.detail}`).join('; ') : 'ar.py status reported findings'
  }
  if (capUsd !== null && spentUsd !== null && spentUsd >= capUsd) return `max_cost reached (${spentUsd.toFixed(2)} of ${capUsd} USD this run)`
  return null
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

const costNow = async ($: EngineInterface): Promise<number | null> => (await $.session.usage().catch(() => null))?.cost?.usd ?? null

/** Ends the drive: state cleared, a session line written, the person told why. */
const stopDrive = async ($: EngineInterface, why: string): Promise<void> => {
  const drive = await read($, driveAtom)
  if (drive === null) return
  await update($, driveAtom, () => null)
  const scope = await read($, scopeAtom)
  if (scope?.root) {
    const now = await $.clock.now()
    await appendLine(ioOf($), sessionLogPath(scope.root, now), sessionLine(now, `autoresearch/${drive.name}`, `driver stopped after ${drive.turns} turn(s): ${why}`))
  }
  $.ui.toast(`neuroflow: autoresearch "${drive.name}" stopped — ${why}`)
}

/**
 * Starts driving a loop. Returns the refusal text, or null when the drive is set up — the markdown
 * command then runs and its turn is iteration 1 (a prompt cannot be submitted from command.run).
 */
const startDrive = async ($: EngineInterface, name: string, opts: NfOptions): Promise<string | null> => {
  if (opts.runtime !== 'on') return 'The driver starts turns, so it needs the neuroflow mod runtime set to on. Run the loop in prose with /neuroflow:autoresearch instead.'
  if ((await read($, driveAtom)) !== null) return 'A loop is already being driven — stop it first (/neuroflow:autoresearch stop).'
  const scope = await read($, scopeAtom)
  const snap = await read($, snapshotAtom)
  if (!scope?.isActive || scope.root === null || snap === null) return 'No neuroflow project here.'
  const loop = snap.loops.find(item => item.name === name) ?? (name === '' && snap.loops.length === 1 ? snap.loops[0] : undefined)
  if (loop === undefined) {
    const names = snap.loops.map(item => item.name).join(', ') || 'none registered'
    return `Which loop? /neuroflow:autoresearch drive <name> — loops: ${names}.`
  }
  const folder = resolveFrom(scope.root, loop.location)
  const begun = await runScript(ioOf($), AR, ['begin', folder, '--json'], { cwd: scope.root, timeoutMs: 60_000 })
  const begin = parseJson<ArStatus>(begun.stdout)
  if (begun.exitCode !== 0 || begin === null) {
    const why = stopReason(begun.exitCode, begin, null, null) ?? 'ar.py begin failed'
    return `Not started: ${why}. Fix it (the loop's program.md or ar.py) and run drive again.`
  }
  const maxErrors = Number.parseInt(begin.caps?.max_consecutive_errors ?? '3', 10) || 3
  const drive: NfDrive = {
    name: loop.name,
    phase: loop.phase,
    folder,
    location: loop.location,
    startedAt: await $.clock.now(),
    turns: 1,
    errors: 0,
    maxErrors,
    maxCostUsd: costCapUsd(begin.caps?.max_cost),
    costAtStart: await costNow($),
  }
  await update($, driveAtom, () => drive)
  await appendLine(ioOf($), sessionLogPath(scope.root, drive.startedAt), sessionLine(drive.startedAt, `autoresearch/${loop.name}`, 'driver started — one iteration per turn'))
  $.ui.toast(`neuroflow: driving "${loop.name}" — one iteration per turn until a cap, ${maxErrors} errored turns in a row, or your stop (s in the band, Esc, or /neuroflow:autoresearch stop)`)
  return null
}

export const registerLoop = (on: On, opts: NfOptions): void => {
  on('command.run', { command: 'neuroflow:autoresearch' }, async ($, e, next) => {
    const [verb, ...rest] = e.args.trim().split(/\s+/)
    if (verb === 'drive') {
      const refusal = await startDrive($, rest.join(' '), opts)
      return refusal === null ? next(e) : { text: refusal }
    }
    if (verb === 'stop') {
      const drive = await read($, driveAtom)
      if (drive === null) return { text: 'No loop is being driven.' }
      await stopDrive($, 'stopped by the person')
      return { text: `Stopped driving "${drive.name}". The current iteration, if any, finishes; no new one starts.` }
    }
    return next(e)
  }).catch(($, e, next) => next(e))

  on('turn.complete', { reason: ['answer', 'aborted', 'error', 'refusal'] }, async ($, e, next) => {
    const result = await next(e)
    const drive = await read($, driveAtom)
    if (drive === null || e.agentId !== undefined) return result
    if (e.reason === 'aborted' || e.isAborted) {
      await stopDrive($, 'you interrupted the turn')
      return result
    }
    if (e.reason === 'refusal') {
      await stopDrive($, 'the model refused the turn')
      return result
    }
    if (e.reason === 'error') {
      const errors = drive.errors + 1
      if (errors >= drive.maxErrors) {
        await stopDrive($, `${errors} turns in a row ended in an error`)
        return result
      }
      await update($, driveAtom, () => ({ ...drive, errors, turns: drive.turns + 1 }))
      await $.prompt.submit({ text: iterationPrompt(drive, drive.turns + 1) })
      return result
    }
    const scope = await read($, scopeAtom)
    const run = await runScript(ioOf($), AR, ['status', drive.folder, '--json'], { cwd: scope?.root ?? undefined, timeoutMs: 60_000 })
    const spent = drive.costAtStart === null ? null : ((await costNow($)) ?? drive.costAtStart) - drive.costAtStart
    const why = stopReason(run.exitCode, parseJson<ArStatus>(run.stdout), spent, drive.maxCostUsd)
    if (why !== null) {
      await stopDrive($, why)
      return result
    }
    if ((await read($, driveAtom)) === null) return result // stopped by a press while the status ran
    await update($, driveAtom, () => ({ ...drive, errors: 0, turns: drive.turns + 1 }))
    await $.prompt.submit({ text: iterationPrompt(drive, drive.turns + 1) })
    return result
  }).catch(($, e, next) => next(e))
}
