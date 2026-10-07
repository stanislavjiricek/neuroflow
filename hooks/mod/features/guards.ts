// Guards — seatbelts, not vaults (charter rules 9–13). Each rule enforces something the prose already
// states next to an <!-- nf-rule: ID --> marker; the reason the model gets names that id.
//
// The ladder: observe → warn → ask → deny. With runtime `observe` or guards `warn`, a guard only says
// what it would have blocked (a toast, and a line on the permission dialog when one is open). With
// runtime `on` and guards `enforce`, it denies — and only irreversible breaks are denied:
//   PREREG-FROZEN      writes to files of a preregistration a person froze
//   RAW-READONLY       writes and destructive shell verbs under the declared raw_roots
//   GIT-NO-SECRETS     `git clean -x`, staging local-only files, `git add -A` without the .gitignore lines
//   PARTICIPANT-ROUTE  the model reading participant data when the ethics record says ai_processing: none
//   LOGIN-NODE         heavy compute started on an HPC login node
// and two ask the person instead of denying:
//   INTEGRITY-MARKER   the model writing `set_by: person` into an integrity status file (only a person may)
//   EGRESS-CONFIRM     uploads to outside services (NotebookLM sources)
// MEMORY-PURITY only ever warns. Bash, PowerShell and scripts can reach around every rule here; that is
// why detection (hash checks, /sentinel) backs them, and why they are never called "enforced".
import { atom, read, update } from 'claude-code'
import type { EngineInterface, On } from 'claude-code'

import type { NfSnapshot } from '../../../types'
import { mayEnforce } from '../lib/options'
import type { NfOptions } from '../lib/options'
import { fold, relativeTo, resolveFrom, toSlash } from '../lib/paths'
import { PHASES } from '../lib/phases'

const scopeAtom = atom({ plugin: 'neuroflow', key: 'scope' } as const, null)
const snapshotAtom = atom({ plugin: 'neuroflow', key: 'snapshot' } as const, null)
const loginNodeAtom = atom({ plugin: 'neuroflow', key: 'loginNode' } as const, null)

export type RuleId =
  | 'PREREG-FROZEN'
  | 'RAW-READONLY'
  | 'GIT-NO-SECRETS'
  | 'PARTICIPANT-ROUTE'
  | 'LOGIN-NODE'
  | 'INTEGRITY-MARKER'
  | 'EGRESS-CONFIRM'
  | 'MEMORY-PURITY'

export type Violation = { rule: RuleId; level: 'deny' | 'ask' | 'warn'; message: string }

/** Local-only paths (neuroflow-core → sharing tiers) that must never be staged. */
export const LOCAL_ONLY = ['.neuroflow/sessions/', '.neuroflow/review/', '.neuroflow/integrations.json', '.neuroflow/flowie/']

const ROOT_FILES = new Set(['project_config.md', 'flow.md', 'objectives.md', 'timeline.md', 'integrations.json', '.gitkeep'])
const ROOT_DIRS = new Set([
  ...PHASES.map(phase => phase.id),
  'sessions', 'reasoning', 'tasks', 'wiki', 'fails', 'review', 'flowie', 'ethics', 'meetings', 'hive', 'interviews', 'ideas',
])
const DELIVERABLE = /\.(pdf|pptx?|docx?|xlsx?|png|jpe?g|gif|svg|html?|mp4|mov)$/i

const under = (rel: string, root: string): boolean => {
  const r = toSlash(root).replace(/^\.\//, '').replace(/\/$/, '')
  return r !== '' && (fold(rel) === fold(r) || fold(rel).startsWith(`${fold(r)}/`))
}

const setsPersonMarker = (text: string): boolean => /^set_by:\s*person\b/m.test(text)

/** What a write to `rel` (project-relative, forward slashes) would break. */
export const writeViolations = (rel: string, snap: NfSnapshot, newText: string | null, oldText: string | null): Violation[] => {
  const out: Violation[] = []
  const prereg = snap.prereg
  if (prereg?.status === 'frozen' && prereg.setBy === 'person' && Object.keys(prereg.files).some(file => fold(file) === fold(rel))) {
    out.push({ rule: 'PREREG-FROZEN', level: 'deny', message: `${rel} belongs to the frozen preregistration — record the change in .neuroflow/preregistration/deviations.md instead (/neuroflow:preregistration → Deviation log)` })
  }
  const raw = snap.rawRoots.find(root => under(rel, root))
  if (raw !== undefined) {
    const brainvision = /\.(vhdr|vmrk|eeg)$/i.test(rel) ? ' BrainVision files point at each other by name — rename or convert them with a BIDS converter (e.g. mne-bids), never by hand.' : ''
    out.push({ rule: 'RAW-READONLY', level: 'deny', message: `${rel} is under ${raw}, a read-only raw-data folder (raw_roots) — write derivatives elsewhere.${brainvision}` })
  }
  if (/^\.neuroflow\/(preregistration|ethics)\/status\.md$/i.test(rel) && newText !== null && setsPersonMarker(newText)) {
    const statusOf = (text: string | null): string => /^status:\s*(\S+)/m.exec(text ?? '')?.[1] ?? ''
    if (oldText === null || !setsPersonMarker(oldText) || statusOf(oldText) !== statusOf(newText)) {
      out.push({ rule: 'INTEGRITY-MARKER', level: 'ask', message: `the model is recording "${statusOf(newText) || 'set'}" in ${rel} as set by a person` })
    }
  }
  if (rel.startsWith('.neuroflow/')) {
    const parts = rel.split('/')
    if (parts.length === 2 && !ROOT_FILES.has(parts[1])) {
      out.push({ rule: 'MEMORY-PURITY', level: 'warn', message: `${rel} is not part of the documented .neuroflow/ structure` })
    } else if (parts.length > 2 && !ROOT_DIRS.has(parts[1])) {
      out.push({ rule: 'MEMORY-PURITY', level: 'warn', message: `.neuroflow/${parts[1]}/ is not a documented .neuroflow/ folder` })
    }
    if (DELIVERABLE.test(rel)) {
      out.push({ rule: 'MEMORY-PURITY', level: 'warn', message: `${rel} looks like a deliverable — deliverables belong in the phase's output_path, not in .neuroflow/` })
    }
  }
  return out
}

/** What a read of `rel` would break: participant data the ethics record keeps away from the model. */
export const readViolations = (rel: string, snap: NfSnapshot): Violation[] => {
  if (snap.ethics?.aiProcessing !== 'none') return []
  const isParticipantData = snap.rawRoots.some(root => under(rel, root)) || /(^|\/)participants\.tsv$/i.test(rel) || /(^|\/)sourcedata\//i.test(rel)
  return isParticipantData
    ? [{ rule: 'PARTICIPANT-ROUTE', level: 'deny', message: `${rel} is participant data, and the ethics record (ai_processing: none) does not allow the AI model to read it — run the analysis script and read its aggregate output instead` }]
    : []
}

const HEAVY = [
  /\b(python3?|py|Rscript|julia|octave)\b[^;&|]*\b(scripts\/(analysis|preprocessing)|preprocess|analy[sz]e|simulat|fit|sweep)/i,
  /\bmatlab\b[^;&|]*-batch\b/i,
  /\b(fmriprep|mriqc|qsiprep|recon-all|freesurfer|snakemake|nextflow|neuron|nest)\b/i,
]

/** What a shell command would break (best effort: it cannot see inside the scripts it starts). */
export const shellViolations = (
  command: string,
  snap: NfSnapshot,
  context: { gitignore: string | null; isLoginNode: boolean },
): Violation[] => {
  const out: Violation[] = []
  const segments = command.split(/&&|\|\||;|\r?\n/).map(part => part.trim()).filter(Boolean)
  for (const segment of segments) {
    if (/\bgit\s+clean\b/.test(segment) && /\s-[a-zA-Z]*[xX]/.test(segment)) {
      out.push({ rule: 'GIT-NO-SECRETS', level: 'deny', message: '`git clean -x` deletes ignored files — recordings, local credentials, caches. Use `git clean -n` to preview, then remove files by name' })
    }
    if (/\bgit\s+add\b/.test(segment)) {
      const named = /(integrations\.json|\.neuroflow[\\/](sessions|review|flowie)\b|user\.yaml)/i.exec(segment)
      if (named !== null) {
        out.push({ rule: 'GIT-NO-SECRETS', level: 'deny', message: `${named[1]} is local-only (sessions, confidential reviews, credentials) and must never be committed` })
      } else if (/\bgit\s+add\s+(-A\b|--all\b|\.(\s|$)|-u\b)/.test(segment)) {
        const ignored = context.gitignore ?? ''
        const missing = LOCAL_ONLY.filter(path => !ignored.includes(path))
        if (missing.length > 0) {
          out.push({ rule: 'GIT-NO-SECRETS', level: 'deny', message: `\`git add -A\` would stage local-only files: .gitignore does not exclude ${missing.join(', ')} — add those lines first (/neuroflow:migrate does it)` })
        }
      }
    }
    for (const root of snap.rawRoots) {
      const r = toSlash(root).replace(/^\.\//, '').replace(/\/$/, '')
      if (r === '') continue
      const escaped = r.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replace(/\//g, '[\\\\/]')
      const destructive = new RegExp(`\\b(rm|rmdir|del|erase|mv|move|ren|rename|Remove-Item|Move-Item|Rename-Item|Set-Content|Out-File|truncate|shred)\\b[^;&|]*${escaped}`, 'i')
      const redirected = new RegExp(`>{1,2}\\s*["']?${escaped}`, 'i')
      if (destructive.test(segment) || redirected.test(segment)) {
        out.push({ rule: 'RAW-READONLY', level: 'deny', message: `this command would change files under ${root}, a read-only raw-data folder (raw_roots)` })
      }
    }
    if (snap.prereg?.status === 'frozen' && snap.prereg.setBy === 'person') {
      for (const file of Object.keys(snap.prereg.files)) {
        const base = file.split('/').pop() ?? file
        const escaped = base.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
        if (new RegExp(`(\\bsed\\s+-i\\b[^;&|]*|>{1,2}\\s*["']?[^;&|]*|\\b(Set-Content|Out-File|Remove-Item|rm|mv)\\b[^;&|]*)${escaped}`, 'i').test(segment)) {
          out.push({ rule: 'PREREG-FROZEN', level: 'deny', message: `this command would change ${file}, part of the frozen preregistration — record a deviation instead` })
        }
      }
    }
    if (/\bnotebooklm\s+source\s+add\b/i.test(segment)) {
      out.push({ rule: 'EGRESS-CONFIRM', level: 'ask', message: 'this uploads files to NotebookLM (an outside service)' })
    }
    if (context.isLoginNode && HEAVY.some(pattern => pattern.test(segment))) {
      out.push({ rule: 'LOGIN-NODE', level: 'deny', message: 'this looks like heavy compute on a cluster login node — submit it as a job (sbatch / qsub) or start an interactive job (srun --pty / qsub -I)' })
    }
  }
  return out
}

/** The denial text: the reason, then the rule id so the person can find the prose that states it. */
export const denyText = (violation: Violation): string => `neuroflow: ${violation.message} [nf-rule: ${violation.rule}]`

// ── engine side ────────────────────────────────────────────────────────────────────────────────

/** Applies the ladder to a call's violations; returns the call's answer. */
const decide = async (
  $: EngineInterface,
  toolUseId: string | undefined,
  violations: readonly Violation[],
  opts: NfOptions,
  isHeadless: boolean,
  proceed: () => Promise<unknown>,
): Promise<unknown> => {
  if (violations.length === 0) return proceed()
  const enforce = mayEnforce(opts)
  const deny = violations.find(violation => violation.level === 'deny')
  if (deny !== undefined) {
    if (enforce) return { deny: denyText(deny) }
    if (!isHeadless) $.ui.toast(`neuroflow would block this (${opts.runtime === 'observe' ? 'observe mode' : 'guards: warn'}): ${deny.message}`)
    if (toolUseId !== undefined) $.ui.notice(toolUseId, `neuroflow: ${deny.message}`)
    return proceed()
  }
  const ask = violations.find(violation => violation.level === 'ask')
  if (ask !== undefined && enforce) {
    if (isHeadless || (await $.session.surfaces()).length === 0) return { deny: `${denyText(ask)} — nobody is here to confirm it` }
    const answer = await $.ui.ask(`${ask.message.charAt(0).toUpperCase()}${ask.message.slice(1)}. Allow it?`, {
      options: ['Allow — I confirm this myself', 'Block it'],
      header: 'neuroflow',
    })
    return answer.startsWith('Allow') ? proceed() : { deny: `${denyText(ask)} — the person declined` }
  }
  for (const violation of violations) {
    if (toolUseId !== undefined) $.ui.notice(toolUseId, `neuroflow: ${violation.message}`)
  }
  if (!isHeadless) $.ui.toast(`neuroflow: ${violations[0].message}`)
  return proceed()
}

/** Login node: a scheduler is installed, we are not inside a job, and the host name looks like a front end. */
const isLoginNode = async ($: EngineInterface): Promise<boolean> => {
  const cached = await read($, loginNodeAtom)
  if (cached !== null) return cached
  let result = false
  const insideJob = (await $.env.get('SLURM_JOB_ID')) !== undefined || (await $.env.get('PBS_JOBID')) !== undefined
  if (!insideJob) {
    const host = await $.process.run(['hostname'], { timeoutMs: 5_000 }).then(run => run.stdout.trim(), () => '')
    if (/(^|[-_.])(login|frontend|front|head|submit|ln\d+)/i.test(host)) {
      const sbatch = await $.process.run(['sbatch', '--version'], { timeoutMs: 5_000 }).then(run => run.exitCode === 0, () => false)
      const qsub = sbatch ? true : await $.process.run(['qstat', '--version'], { timeoutMs: 5_000 }).then(run => run.exitCode === 0, () => false)
      result = sbatch || qsub
    }
  }
  await update($, loginNodeAtom, () => result)
  return result
}

type WriteInput = { file_path?: string; notebook_path?: string; content?: string; new_string?: string; old_string?: string; edits?: { old_string: string; new_string: string }[] }

export const registerGuards = (on: On, opts: NfOptions): void => {
  on('tool.call', { tool: ['Write', 'Edit', 'MultiEdit', 'NotebookEdit'] }, async ($, e, next) => {
    const scope = await read($, scopeAtom)
    const snap = await read($, snapshotAtom)
    if (!scope?.isActive || scope.root === null || snap === null) return next(e)
    const input = e as unknown as WriteInput
    const path = input.file_path ?? input.notebook_path
    if (path === undefined) return next(e)
    const absolute = resolveFrom(await $.session.cwd(), path)
    const real = await $.fs.stat(absolute, { resolve: true }).then(stat => stat.realPath ?? absolute, () => absolute)
    const rel = relativeTo(real, scope.root) ?? relativeTo(absolute, scope.root)
    if (rel === null) return next(e)
    const oldText = /status\.md$/i.test(rel) ? await $.fs.read(absolute).then(text => (typeof text === 'string' ? text : null), () => null) : null
    const newText =
      input.content ?? (input.new_string !== undefined ? `${input.new_string}` : input.edits !== undefined ? input.edits.map(edit => edit.new_string).join('\n') : null)
    const combined = newText !== null && oldText !== null && input.content === undefined && input.old_string !== undefined ? oldText.replace(input.old_string, newText) : newText
    const violations = writeViolations(rel, snap, combined, oldText)
    return decide($, e.tool_use_id, violations, opts, scope.isHeadless, () => next(e)) as ReturnType<typeof next>
  }).catch(($, e, next) => (next.called ? next(e) : mayEnforce(opts) ? { deny: 'neuroflow: a guard could not check this write — try again, or set the neuroflow mod to observe' } : next(e)))

  on('tool.call', { tool: ['Read', 'Grep'] }, async ($, e, next) => {
    const scope = await read($, scopeAtom)
    const snap = await read($, snapshotAtom)
    if (!scope?.isActive || scope.root === null || snap === null || snap.ethics?.aiProcessing !== 'none') return next(e)
    const input = e as unknown as { file_path?: string; path?: string }
    const path = input.file_path ?? input.path
    if (path === undefined) return next(e)
    const rel = relativeTo(resolveFrom(await $.session.cwd(), path), scope.root)
    if (rel === null) return next(e)
    return decide($, e.tool_use_id, readViolations(rel, snap), opts, scope.isHeadless, () => next(e)) as ReturnType<typeof next>
  }).catch(($, e, next) => (next.called ? next(e) : mayEnforce(opts) ? { deny: 'neuroflow: a guard could not check this read — try again, or set the neuroflow mod to observe' } : next(e)))

  on('tool.call', { tool: ['Bash', 'PowerShell'] }, async ($, e, next) => {
    const scope = await read($, scopeAtom)
    const snap = await read($, snapshotAtom)
    if (!scope?.isActive || scope.root === null || snap === null) return next(e)
    const command = (e as unknown as { command?: string }).command ?? ''
    if (command === '') return next(e)
    const needsGitignore = /\bgit\s+add\b/.test(command)
    const gitignore = needsGitignore ? await $.fs.read(`${scope.root}/.gitignore`).then(text => (typeof text === 'string' ? text : ''), () => '') : null
    const loginNode = HEAVY.some(pattern => pattern.test(command)) ? await isLoginNode($) : false
    const violations = shellViolations(command, snap, { gitignore, isLoginNode: loginNode })
    return decide($, e.tool_use_id, violations, opts, scope.isHeadless, () => next(e)) as ReturnType<typeof next>
  }).catch(($, e, next) => (next.called ? next(e) : mayEnforce(opts) ? { deny: 'neuroflow: a guard could not check this command — try again, or set the neuroflow mod to observe' } : next(e)))
}
