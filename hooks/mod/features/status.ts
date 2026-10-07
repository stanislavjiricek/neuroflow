// Status — the exception-only status line (M063) and the doctor (M063, G119, G210).
//  - The status line under the prompt says something only when something needs attention:
//    an expired approval, a date within 3 days, a marker not set by a person, a config the mod cannot
//    read, a feature that could not run. scope.ts shows it after every snapshot refresh.
//  - /neuroflow:doctor is answered in code when the mod is live (which itself proves the module
//    loaded) and runs the same portable checks the prose fallback runs: skills/neuroflow-core/scripts/doctor.py.
import { atom, read } from 'claude-code'
import type { EngineInterface, On } from 'claude-code'

import type { NfSnapshot } from '../../../types'
import type { NfIo } from '../lib/io'
import type { NfOptions } from '../lib/options'
import { parseJson, runScript } from '../lib/scripts'

const scopeAtom = atom({ plugin: 'neuroflow', key: 'scope' } as const, null)
const degradedAtom = atom({ plugin: 'neuroflow', key: 'degraded' } as const, [])

/** The Claude Code version the mod was last tested on; older builds may lack parts of the API. */
export const VERSION_FLOOR = '2.1.292'

const when = (days: number): string => (days === 0 ? 'today' : days === 1 ? 'tomorrow' : `in ${days} days`)

/** The status line text, or undefined when nothing needs attention. At most three items. */
export const statusLine = (snap: NfSnapshot, degraded: readonly string[], alerts: readonly string[] = []): string | undefined => {
  // Alerts features raised this session (a frozen file changed, a citation stopped resolving…) come first.
  const items: string[] = [...alerts]
  if (snap.ethics !== null && (snap.ethics.status === 'expired' || snap.ethics.status === 'withdrawn')) items.push(`⚠ ethics ${snap.ethics.status}`)
  const urgent = snap.deadlines.filter(deadline => deadline.daysLeft <= 3)
  if (urgent.length > 0) items.push(`⚠ ${urgent[0].what} ${when(urgent[0].daysLeft)}${urgent.length > 1 ? ` (+${urgent.length - 1})` : ''}`)
  const ethicsSoon = snap.deadlines.find(deadline => /ethic/i.test(deadline.what) && deadline.daysLeft > 3 && deadline.daysLeft <= 14)
  if (ethicsSoon !== undefined) items.push(`▸ ethics approval expires ${when(ethicsSoon.daysLeft)}`)
  if (snap.prereg?.status === 'frozen' && snap.prereg.setBy !== 'person') items.push('? prereg marker not set by a person')
  if (snap.problems.length > 0) items.push(`! ${snap.problems.length === 1 ? 'config needs attention' : `${snap.problems.length} config problems`} — /neuroflow:doctor`)
  if (degraded.length > 0) items.push(`! mod: ${degraded.length} feature(s) degraded — /neuroflow:doctor`)
  return items.length === 0 ? undefined : `neuroflow: ${items.slice(0, 3).join(' · ')}`
}

export type DoctorCheck = { id: string; status: 'ok' | 'info' | 'warn' | 'fail'; message: string }
export type DoctorReport = { checks: DoctorCheck[] }

const GLYPH: Record<DoctorCheck['status'], string> = { ok: '✔', info: '·', warn: '⚠', fail: '✖' }

/** Compares dotted versions ("2.1.292" ≥ "2.1.30"). */
export const atLeast = (version: string, floor: string): boolean => {
  const a = version.split(/[.-]/).map(part => Number.parseInt(part, 10) || 0)
  const b = floor.split(/[.-]/).map(part => Number.parseInt(part, 10) || 0)
  for (let i = 0; i < Math.max(a.length, b.length); i += 1) {
    if ((a[i] ?? 0) !== (b[i] ?? 0)) return (a[i] ?? 0) > (b[i] ?? 0)
  }
  return true
}

/** The doctor's report as text: the mod's own facts first, then the portable checks. */
export const doctorText = (modLines: readonly DoctorCheck[], report: DoctorReport | null, scriptError: string | null): string => {
  const checks = [...modLines, ...(report?.checks ?? [])]
  if (report === null) checks.push({ id: 'checks', status: 'warn', message: `portable checks did not run: ${scriptError ?? 'no output'}` })
  const worst = checks.some(check => check.status === 'fail') ? 'problems found' : checks.some(check => check.status === 'warn') ? 'some warnings' : 'all good'
  return [`neuroflow doctor — ${worst}`, ...checks.map(check => `${GLYPH[check.status]} ${check.message}`)].join('\n')
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

export const registerStatus = (on: On, opts: NfOptions): void => {
  on('command.run', { command: 'neuroflow:doctor' }, async ($, e, next) => {
    const scope = await read($, scopeAtom)
    if (scope === null) return next(e)
    const version = (await $.session.version()).version
    const degraded = await read($, degradedAtom)
    const modLines: DoctorCheck[] = [
      { id: 'mod', status: 'ok', message: `neuroflow mod is live — runtime ${opts.runtime}, guards ${opts.guards}, band ${opts.band}` },
      atLeast(version, VERSION_FLOOR)
        ? { id: 'claude-code', status: 'ok', message: `Claude Code ${version} (mod tested from ${VERSION_FLOOR})` }
        : { id: 'claude-code', status: 'warn', message: `Claude Code ${version} is older than ${VERSION_FLOOR}; update it, or set the mod's runtime to off` },
      scope.isActive
        ? { id: 'scope', status: 'ok', message: `project: ${scope.root}` }
        : { id: 'scope', status: 'info', message: `the mod is idle here: ${scope.reason}` },
      ...degraded.map(feature => ({ id: `degraded-${feature}`, status: 'warn' as const, message: `mod feature could not run: ${feature}` })),
    ]
    // The decision drafter's keep rate stays visible (G202: a drafter nobody keeps should be switched off).
    const kept = Number(await $.store.get('drafter.kept')) || 0
    const dropped = Number(await $.store.get('drafter.dropped')) || 0
    if (kept + dropped > 0) modLines.push({ id: 'drafter', status: 'info', message: `decision drafter: ${kept} of ${kept + dropped} drafts kept` })
    const target = scope.root ?? (await $.session.cwd())
    const run = await runScript(ioOf($), 'skills/neuroflow-core/scripts/doctor.py', ['--json', '--project', target], { timeoutMs: 60_000 })
    const report = parseJson<DoctorReport>(run.stdout)
    return { text: doctorText(modLines, report, report === null ? (run.stderr.trim().split('\n').pop() ?? null) : null) }
  }).catch(($, e, next) => next(e))
}
