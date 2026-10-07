// Guards — seatbelts, not vaults (charter rules 9–13). Each rule enforces something the prose already
// states next to an <!-- nf-rule: ID --> marker; the reason the model gets names that id.
//
// The ladder: observe → warn → ask → deny. With runtime `observe` or guards `warn`, a guard only says
// what it would have blocked (a toast, and a note on the tool call). With runtime `on` and guards
// `enforce`, it denies — and only irreversible breaks are denied.
//
// Rules this file enforces (validate_pr V8 matches each to its prose marker):
//   nf-rule: PREREG-FROZEN      writes to a preregistration a person froze; deviations.md stays append-only
//   nf-rule: RAW-READONLY       changes to existing files under raw_roots (new recordings may be added)
//   nf-rule: GIT-NO-SECRETS     `git clean -x`, staging local-only files, `git add -A` without the .gitignore lines
//   nf-rule: GIT-ALIAS-SCOPE    git verbs beyond the running /git alias's endpoint
//   nf-rule: PARTICIPANT-ROUTE  the model reading participant data the ethics record keeps from it
//   nf-rule: LOGIN-NODE         heavy compute on an HPC login node (asks)
//   nf-rule: INTEGRITY-MARKER   the model writing `set_by: person` into an integrity status file (asks)
//   nf-rule: EGRESS-CONFIRM     uploads to outside services (asks)
//   nf-rule: MEMORY-PURITY      files outside the documented .neuroflow/ structure (warns only)
// Bash, PowerShell and scripts can reach around every rule here; that is why detection (hash checks,
// /sentinel) backs them, and why they are never called "enforced".
import { atom, read, update } from 'claude-code'
import type { EngineInterface, On } from 'claude-code'

import type { NfSnapshot } from '../../../types'
import type { NfIo } from '../lib/io'
import { mayEnforce } from '../lib/options'
import type { NfOptions } from '../lib/options'
import { fold, join, relativeTo, resolveFrom, toSlash } from '../lib/paths'
import { PHASES } from '../lib/phases'
import { parseJson, runScript } from '../lib/scripts'
import { statusLine } from './status'

const scopeAtom = atom({ plugin: 'neuroflow', key: 'scope' } as const, null)
const snapshotAtom = atom({ plugin: 'neuroflow', key: 'snapshot' } as const, null)
const degradedAtom = atom({ plugin: 'neuroflow', key: 'degraded' } as const, [])
const alertsAtom = atom({ plugin: 'neuroflow', key: 'statusAlerts' } as const, [])
const loginNodeAtom = atom({ plugin: 'neuroflow', key: 'loginNode' } as const, null)
const gitAliasAtom = atom({ plugin: 'neuroflow', key: 'gitAlias' } as const, null)
const structureAtom = atom({ plugin: 'neuroflow', key: 'memoryStructure' } as const, null)

export type RuleId =
  | 'PREREG-FROZEN'
  | 'RAW-READONLY'
  | 'GIT-NO-SECRETS'
  | 'GIT-ALIAS-SCOPE'
  | 'PARTICIPANT-ROUTE'
  | 'LOGIN-NODE'
  | 'INTEGRITY-MARKER'
  | 'EGRESS-CONFIRM'
  | 'MEMORY-PURITY'

export type Violation = { rule: RuleId; level: 'deny' | 'ask' | 'warn'; message: string }

export type Structure = { rootFiles: string[]; rootFolders: string[] }

/** Local-only paths (neuroflow-core → sharing tiers) that must never be staged. */
export const LOCAL_ONLY = ['.neuroflow/sessions/', '.neuroflow/review/', '.neuroflow/integrations.json', '.neuroflow/flowie/', '.neuroflow/paper/xray-', '.neuroflow/wiki/.pending/']

/** Used until nf_check.py --structure has answered (or when no Python is installed). */
export const DEFAULT_STRUCTURE: Structure = {
  rootFiles: ['project_config.md', 'flow.md', 'objectives.md', 'timeline.md', 'integrations.json', 'sentinel.md', 'journal-preferences.md', '.gitkeep'],
  rootFolders: [...PHASES.map(phase => phase.id), 'sessions', 'reasoning', 'tasks', 'wiki', 'fails', 'review', 'ethics', 'meetings', 'pipeline', 'slideshow'],
}

/** The structure from `nf_check.py --structure` (its NF6 whitelist), or null when it did not answer. */
export const structureFrom = (json: { documented?: boolean; root_files?: string[]; root_folders?: string[]; phase_folders?: string[] } | null): Structure | null => {
  if (json === null || json.documented !== true || !Array.isArray(json.root_files) || !Array.isArray(json.root_folders)) return null
  return { rootFiles: [...json.root_files, '.gitkeep'], rootFolders: [...json.root_folders, ...(json.phase_folders ?? [])] }
}

const DELIVERABLE = /\.(pdf|pptx?|docx?|xlsx?|png|jpe?g|gif|svg|html?|mp4|mov)$/i

const trimRoot = (root: string): string => toSlash(root).replace(/^\.\//, '').replace(/\/$/, '')

const under = (rel: string, root: string): boolean => {
  const r = trimRoot(root)
  return r !== '' && (fold(rel) === fold(r) || fold(rel).startsWith(`${fold(r)}/`))
}

/** The raw-data folders: raw_roots, or `sourcedata/` while none are set (commands/data.md → Convert). */
const rawRootsOf = (snap: NfSnapshot): string[] => (snap.rawRoots.length > 0 ? snap.rawRoots : ['sourcedata/'])

const setsPersonMarker = (text: string): boolean => /^set_by:\s*person\b/m.test(text)

const statusOf = (text: string | null): string => /^status:\s*(\S+)/m.exec(text ?? '')?.[1] ?? ''

/** What a write to `rel` (project-relative, forward slashes) would break. `newText` is the whole file after the write. */
export const writeViolations = (
  rel: string,
  snap: NfSnapshot,
  newText: string | null,
  oldText: string | null,
  context: { exists: boolean; structure?: Structure | null },
): Violation[] => {
  const out: Violation[] = []
  const prereg = snap.prereg
  const frozen = prereg?.status === 'frozen' && prereg.setBy === 'person'
  if (frozen && Object.keys(prereg?.files ?? {}).some(file => fold(file) === fold(rel))) {
    out.push({ rule: 'PREREG-FROZEN', level: 'deny', message: `${rel} belongs to the frozen preregistration — record the change in .neuroflow/preregistration/deviations.md instead (/neuroflow:preregistration → Deviation log)` })
  }
  if (frozen && fold(rel) === fold('.neuroflow/preregistration/deviations.md') && oldText !== null && newText !== null && !newText.startsWith(oldText.trimEnd())) {
    out.push({ rule: 'PREREG-FROZEN', level: 'deny', message: 'deviations.md is append-only while the preregistration is frozen — add a new entry at the end, never change an earlier one' })
  }
  const raw = rawRootsOf(snap).find(root => under(rel, root))
  if (raw !== undefined && context.exists) {
    const brainvision = /\.(vhdr|vmrk|eeg)$/i.test(rel)
      ? ' BrainVision files name each other inside, so copy or rename them with mne_bids.copyfiles.copyfile_brainvision() or write_raw_bids(), never by hand.'
      : ''
    out.push({ rule: 'RAW-READONLY', level: 'deny', message: `${rel} is an existing file under ${raw}, a read-only raw-data folder (raw_roots) — write derivatives elsewhere; new recordings may be added.${brainvision}` })
  }
  if (/^\.neuroflow\/(preregistration|ethics)\/status\.md$/i.test(rel) && newText !== null && setsPersonMarker(newText)) {
    if (oldText === null || !setsPersonMarker(oldText) || statusOf(oldText) !== statusOf(newText)) {
      out.push({ rule: 'INTEGRITY-MARKER', level: 'ask', message: `the model is recording "${statusOf(newText) || 'set'}" in ${rel} as set by a person` })
    }
  }
  if (rel.startsWith('.neuroflow/')) {
    const structure = context.structure ?? DEFAULT_STRUCTURE
    const parts = rel.split('/')
    if (parts.length === 2 && !structure.rootFiles.includes(parts[1])) {
      out.push({ rule: 'MEMORY-PURITY', level: 'warn', message: `${rel} is not part of the documented .neuroflow/ structure — put it in the phase folder it belongs to` })
    } else if (parts.length > 2 && !structure.rootFolders.includes(parts[1])) {
      out.push({ rule: 'MEMORY-PURITY', level: 'warn', message: `.neuroflow/${parts[1]}/ is not a documented .neuroflow/ folder — use a phase folder, or the phase's output_path for deliverables` })
    }
    if (DELIVERABLE.test(rel)) {
      out.push({ rule: 'MEMORY-PURITY', level: 'warn', message: `${rel} looks like a deliverable — deliverables belong in the phase's output_path, not in .neuroflow/` })
    }
  }
  return out
}

/**
 * Whether the ethics record lets the model read participant data (neuroflow-core → Participant data):
 * a missing field or a marker the model set counts as `none`; no record at all is unknown (a warning).
 */
export const participantRoute = (snap: NfSnapshot): 'deny' | 'allow' | 'unknown' => {
  if (snap.ethicsNotApplicable) return 'allow'
  const ethics = snap.ethics
  if (ethics === null) return 'unknown'
  if (ethics.setBy !== 'person' || ethics.aiProcessing === null || ethics.aiProcessing === 'none') return 'deny'
  return 'allow'
}

/** Participant data: recordings under the raw roots and participants.tsv rows. Sidecar JSON is metadata. */
export const isParticipantData = (rel: string, snap: NfSnapshot): boolean => {
  if (/\.json$/i.test(rel)) return false
  return rawRootsOf(snap).some(root => under(rel, root)) || /(^|\/)participants\.tsv$/i.test(rel)
}

/** What a read of `rel` would break. `headerOnly`: a table read for its column names, which is fine. */
export const readViolations = (rel: string, snap: NfSnapshot, headerOnly = false): Violation[] => {
  if (headerOnly || !isParticipantData(rel, snap)) return []
  const route = participantRoute(snap)
  if (route === 'allow') return []
  if (route === 'unknown') {
    return [{ rule: 'PARTICIPANT-ROUTE', level: 'warn', message: `${rel} is participant data and this project has no ethics record saying whether the AI model may read it — /neuroflow:ethics records it` }]
  }
  const recorded = snap.ethics?.setBy === 'person' ? snap.ethics?.aiProcessing ?? 'missing' : 'not confirmed by a person'
  return [{
    rule: 'PARTICIPANT-ROUTE',
    level: 'deny',
    message: `${rel} is participant data, and the ethics record does not let the AI model read it (ai_processing: ${recorded}) — write a script, let the person run it, and work from its aggregate output (/neuroflow:ethics → AI processing)`,
  }]
}

const HEAVY = [
  /\b(python3?|py|Rscript|julia|octave)\b[^;&|]*\b(scripts\/(analysis|preprocessing)|preprocess|analy[sz]e|simulat|run_sim|fit_|sweep)/i,
  /\b(sweep_run|multiverse|cleanroom)\.py\b/i,
  /\bmatlab\b[^;&|]*-batch\b/i,
  /\b(fmriprep|mriqc|qsiprep|recon-all|snakemake|nextflow)\b/i,
]

/** Whether a shell command looks like heavy compute (LOGIN-NODE). */
export const isHeavy = (command: string): boolean => HEAVY.some(pattern => pattern.test(command))

/** The git subcommand of a shell segment (`git -C dir add …` → add), or null when it runs no git. */
export const gitVerb = (segment: string): string | null =>
  /\bgit(?:\s+(?:-C\s+(?:"[^"]*"|'[^']*'|\S+)|-c\s+\S+|--no-pager|--git-dir=\S+|--work-tree=\S+))*\s+([a-z][a-z-]*)\b/.exec(segment)?.[1] ?? null

/** Git verbs a /git alias may run (commands/git.md → Shorthand aliases; alias scope is final). */
export const ALIAS_ALLOWS: Readonly<Record<string, readonly string[]>> = {
  a: ['add', 'reset', 'status', 'diff'],
  c: ['commit', 'status', 'diff'],
  ac: ['add', 'reset', 'commit', 'status', 'diff'],
  acp: ['add', 'reset', 'commit', 'push', 'status', 'diff'],
  p: ['push', 'pull', 'fetch', 'status'],
  pl: ['pull', 'fetch', 'status'],
  ps: ['push', 'status'],
  b: ['branch', 'checkout', 'switch', 'status'],
  pr: ['push', 'status', 'diff', 'log'],
}

/** The verbs alias scope watches: everything that changes the index, history or a remote. */
const GUARDED_VERBS = ['add', 'commit', 'push', 'pull', 'fetch', 'merge', 'rebase', 'reset', 'checkout', 'switch', 'branch', 'tag', 'stash', 'cherry-pick', 'revert']

const escapeRe = (text: string): string => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

/** A pattern for a project-relative folder that matches either slash. */
const pathPattern = (root: string): string => escapeRe(trimRoot(root)).replace(/\//g, '[\\\\/]')

const READ_VERBS = /^(cat|head|tail|less|more|type|Get-Content|gc|xxd|od|strings|bat|zcat)$/i

/** What a shell command would break (best effort: it cannot see inside the scripts it starts). */
export const shellViolations = (
  command: string,
  snap: NfSnapshot,
  context: { gitignore: string | null; isLoginNode: boolean; gitAlias?: string | null },
): Violation[] => {
  const gitAlias = context.gitAlias ?? null
  const routeDenied = participantRoute(snap) === 'deny'
  const out: Violation[] = []
  const segments = command.split(/&&|\|\||;|\||\r?\n/).map(part => part.trim()).filter(Boolean)
  for (const segment of segments) {
    const verb = gitVerb(segment)
    if (verb === 'clean' && /\s-[a-zA-Z]*[xX]/.test(segment)) {
      out.push({ rule: 'GIT-NO-SECRETS', level: 'deny', message: '`git clean -x` deletes ignored files — recordings, local credentials, caches. Use `git clean -n` to preview, then remove files by name' })
    }
    const discards =
      (verb === 'reset' && /\s--hard\b/.test(segment)) ||
      (verb === 'checkout' && /\s(--\s|\.(\s|$))/.test(segment)) ||
      (verb === 'push' && /\s(--force\b|-f\b|--force-with-lease\b)/.test(segment)) ||
      (verb === 'restore' && !/\s--staged\b/.test(segment))
    if (discards) {
      out.push({ rule: 'GIT-NO-SECRETS', level: 'ask', message: `\`${segment.slice(0, 80)}\` throws work away — check its dry run or what would be lost first` })
    }
    if (gitAlias !== null && verb !== null) {
      const allowed = ALIAS_ALLOWS[gitAlias]
      if (allowed !== undefined && GUARDED_VERBS.includes(verb) && !allowed.includes(verb)) {
        out.push({ rule: 'GIT-ALIAS-SCOPE', level: 'deny', message: `/git ${gitAlias} stops at its endpoint — \`git ${verb}\` is beyond it; ask the person for a new instruction` })
      }
    }
    if (gitAlias !== null && /\bgh\s+pr\s+create\b/.test(segment) && gitAlias !== 'pr') {
      out.push({ rule: 'GIT-ALIAS-SCOPE', level: 'deny', message: `/git ${gitAlias} does not open pull requests — ask the person for a new instruction` })
    }
    if (verb === 'add') {
      const named = /(integrations\.json|\.neuroflow[\\/](sessions|review|flowie)\b|\.neuroflow[\\/]paper[\\/]xray-\S*|\.neuroflow[\\/]wiki[\\/]\.pending\b|user\.yaml)/i.exec(segment)
      if (named !== null) {
        out.push({ rule: 'GIT-NO-SECRETS', level: 'deny', message: `${named[1]} is local-only (sessions, confidential reviews, paper X-rays, wiki cards awaiting review, personal settings) and must never be committed` })
      } else if (/\sadd\s+(-A\b|--all\b|\.(\s|$)|-u\b)/.test(segment)) {
        const ignored = context.gitignore ?? ''
        const missing = LOCAL_ONLY.filter(path => !ignored.includes(path))
        if (missing.length > 0) {
          out.push({ rule: 'GIT-NO-SECRETS', level: 'deny', message: `\`git add -A\` would stage local-only files: .gitignore does not exclude ${missing.join(', ')} — add those lines first (/neuroflow:migrate does it)` })
        }
      }
    }
    for (const root of rawRootsOf(snap)) {
      if (trimRoot(root) === '') continue
      const escaped = pathPattern(root)
      const destructive = new RegExp(`\\b(rm|rmdir|del|erase|mv|move|ren|rename|Remove-Item|Move-Item|Rename-Item|Set-Content|Out-File|truncate|shred)\\b[^;&|]*${escaped}`, 'i')
      const editInPlace = new RegExp(`\\bsed\\s+-i\\b[^;&|]*${escaped}`, 'i')
      const redirected = new RegExp(`>{1,2}\\s*["']?${escaped}`, 'i')
      const gitDiscard = (verb === 'clean' || verb === 'checkout' || verb === 'restore') && new RegExp(escaped, 'i').test(segment)
      if (destructive.test(segment) || editInPlace.test(segment) || redirected.test(segment) || gitDiscard) {
        out.push({ rule: 'RAW-READONLY', level: 'deny', message: `this command would change files under ${root}, a read-only raw-data folder (raw_roots)` })
      }
    }
    if (routeDenied) {
      const words = segment.split(/\s+/).map(word => word.replace(/^["']|["']$/g, ''))
      if (words.length > 1 && READ_VERBS.test(words[0])) {
        for (const root of rawRootsOf(snap)) {
          const inRoot = new RegExp(`(^|[\\\\/])${pathPattern(root)}([\\\\/]|$)`, 'i')
          if (words.slice(1).some(word => inRoot.test(word) && !/\.json$/i.test(word))) {
            out.push({ rule: 'PARTICIPANT-ROUTE', level: 'deny', message: `this command would show participant data under ${root} to the model, which the ethics record does not allow — run a script and work from its aggregate output` })
          }
        }
      }
    }
    if (snap.prereg?.status === 'frozen' && snap.prereg.setBy === 'person') {
      for (const file of Object.keys(snap.prereg.files)) {
        const escaped = escapeRe(file.split('/').pop() ?? file)
        if (new RegExp(`(\\bsed\\s+-i\\b[^;&|]*|>{1,2}\\s*["']?[^;&|]*|\\b(Set-Content|Out-File|Remove-Item|rm|mv)\\b[^;&|]*)${escaped}`, 'i').test(segment)) {
          out.push({ rule: 'PREREG-FROZEN', level: 'deny', message: `this command would change ${file}, part of the frozen preregistration — record a deviation instead` })
        }
      }
    }
    if (/\bnotebooklm\s+source\s+add\b/i.test(segment)) {
      out.push({ rule: 'EGRESS-CONFIRM', level: 'ask', message: 'this uploads files to NotebookLM (an outside service)' })
    }
    if (context.isLoginNode && isHeavy(segment)) {
      out.push({
        rule: 'LOGIN-NODE',
        level: 'ask',
        message: 'this looks like heavy compute on a cluster login node — submit it as a job (phase-brain-run templates: job-slurm.sh, job-pbs.sh; register it with runs.py add) or start an interactive job first (srun --pty bash / qsub -I)',
      })
    }
  }
  return out
}

/** The denial text: the reason, then the rule id so the person can find the prose that states it. */
export const denyText = (violation: Violation): string => `neuroflow: ${violation.message} [nf-rule: ${violation.rule}]`

type EditInput = {
  content?: string
  old_string?: string
  new_string?: string
  replace_all?: boolean
  edits?: { old_string: string; new_string: string; replace_all?: boolean }[]
}

const replaceIn = (text: string, from: string, to: string, all: boolean | undefined): string =>
  all === true ? text.split(from).join(to) : text.replace(from, () => to)

/** The whole file after a Write, Edit or MultiEdit, given the file before it (null when unknown). */
export const afterEdit = (input: EditInput, oldText: string | null): string | null => {
  if (typeof input.content === 'string') return input.content
  if (oldText === null) return null
  if (typeof input.old_string === 'string' && typeof input.new_string === 'string') return replaceIn(oldText, input.old_string, input.new_string, input.replace_all)
  if (Array.isArray(input.edits)) return input.edits.reduce((text, edit) => replaceIn(text, edit.old_string, edit.new_string, edit.replace_all), oldText)
  return null
}

// ── engine side ────────────────────────────────────────────────────────────────────────────────

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

/** Login node (LOGIN-NODE): a scheduler is on PATH and this process is not inside a job. Checked once. */
const isLoginNode = async ($: EngineInterface): Promise<boolean> => {
  const cached = await read($, loginNodeAtom)
  if (cached !== null) return cached
  let result = false
  const insideJob = (await $.env.get('SLURM_JOB_ID')) !== undefined || (await $.env.get('PBS_JOBID')) !== undefined
  if (!insideJob) {
    const found = await $.process.run(['sh', '-c', 'command -v sbatch qsub'], { timeoutMs: 5_000 }).then(run => run.stdout.trim(), () => '')
    result = found !== ''
  }
  await update($, loginNodeAtom, () => result)
  return result
}

/** Applies the ladder to a call's violations and returns the call's answer. */
const decide = async (
  $: EngineInterface,
  toolUseId: string | undefined,
  violations: readonly Violation[],
  opts: NfOptions,
  isHeadless: boolean,
  toasted: Set<string>,
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
    // The safe answer comes first and only the exact label allows: a dialog that resolves on its own
    // (the person away from the keyboard) must never let the call through.
    const allow = 'Allow — I confirm this myself'
    const answer = await $.ui
      .ask(`${ask.message.charAt(0).toUpperCase()}${ask.message.slice(1)}. Allow it?`, { options: ['Block it', allow], header: 'neuroflow' })
      .catch(() => '')
    return answer === allow ? proceed() : { deny: `${denyText(ask)} — the person declined, or nobody answered` }
  }
  for (const violation of violations) {
    if (toolUseId !== undefined) $.ui.notice(toolUseId, `neuroflow: ${violation.message}`)
  }
  // A warning toasts once per session; the note on the tool call stays every time.
  const first = violations[0]
  if (!isHeadless && !toasted.has(first.message)) {
    toasted.add(first.message)
    $.ui.toast(`neuroflow: ${first.message}`)
  }
  return proceed()
}

export const registerGuards = (on: On, opts: NfOptions): void => {
  const toasted = new Set<string>()

  // At start: the documented structure (MEMORY-PURITY), the login-node check (LOGIN-NODE), and a hash
  // check of a frozen preregistration (PREREG-FROZEN — detection backs the guard).
  on('session.start', { isInteractive: [true, false] }, async ($, e, next) => {
    const result = await next(e)
    const scope = await read($, scopeAtom)
    if (!scope?.isActive || scope.root === null) return result
    try {
      const io = ioOf($)
      const listed = await runScript(io, 'skills/neuroflow-core/scripts/nf_check.py', ['--structure'], { cwd: scope.root, timeoutMs: 20_000 })
      const structure = structureFrom(parseJson(listed.stdout))
      if (structure !== null) await update($, structureAtom, () => structure)
      await isLoginNode($)
      const snap = await read($, snapshotAtom)
      if (snap?.prereg?.status === 'frozen' && snap.prereg.setBy === 'person') {
        const verify = await runScript(io, 'skills/phase-preregistration/scripts/freeze.py', ['verify', '--root', scope.root, '--json'], { cwd: scope.root, timeoutMs: 30_000 })
        if (verify.exitCode === 1) {
          await update($, alertsAtom, list => [...list.filter(item => !item.includes('frozen preregistration')), '⚠ frozen preregistration changed — /neuroflow:preregistration'])
          $.ui.status(statusLine(snap, await read($, degradedAtom), await read($, alertsAtom)))
        }
      }
    } catch {
      // best effort: the guards fall back to the built-in structure, and /sentinel runs the same checks
    }
    return result
  }).catch(($, e, next) => next(e))

  // nf-rule: GIT-ALIAS-SCOPE — remember which /git alias this turn runs; its scope ends with the turn.
  on('command.run', { command: 'neuroflow:git' }, async ($, e, next) => {
    const alias = e.args.trim().split(/\s+/)[0] ?? ''
    await update($, gitAliasAtom, () => (alias in ALIAS_ALLOWS ? alias : null))
    return next(e)
  }).catch(($, e, next) => next(e))

  on('turn.complete', { reason: ['answer', 'aborted', 'error', 'refusal'] }, async ($, e, next) => {
    const result = await next(e)
    if (e.agentId === undefined) await update($, gitAliasAtom, () => null)
    return result
  }).catch(($, e, next) => next(e))

  // nf-rule: PREREG-FROZEN · nf-rule: RAW-READONLY · nf-rule: INTEGRITY-MARKER · nf-rule: MEMORY-PURITY
  on('tool.call', { tool: ['Write', 'Edit', 'MultiEdit', 'NotebookEdit'] }, async ($, e, next) => {
    const scope = await read($, scopeAtom)
    const snap = await read($, snapshotAtom)
    if (!scope?.isActive || scope.root === null || snap === null) return next(e)
    const input = e as unknown as EditInput & { file_path?: string; notebook_path?: string }
    const path = input.file_path ?? input.notebook_path
    if (path === undefined) return next(e)
    const absolute = resolveFrom(await $.session.cwd(), path)
    const stat = await $.fs.stat(absolute, { resolve: true }).catch(() => null)
    const rel = relativeTo(stat?.realPath ?? absolute, scope.root) ?? relativeTo(absolute, scope.root)
    if (rel === null) return next(e)
    // Old content only where a rule compares before and after (status markers, the deviation log).
    const oldText = /(status|deviations)\.md$/i.test(rel) ? await $.fs.read(absolute).then(text => (typeof text === 'string' ? text : null), () => null) : null
    const violations = writeViolations(rel, snap, afterEdit(input, oldText), oldText, { exists: stat !== null, structure: await read($, structureAtom) })
    return decide($, e.tool_use_id, violations, opts, scope.isHeadless, toasted, () => next(e)) as ReturnType<typeof next>
  }).catch(($, e, next) => (next.called ? next(e) : mayEnforce(opts) ? { deny: 'neuroflow: a guard could not check this write — try again, or set the neuroflow mod to observe' } : next(e)))

  // nf-rule: PARTICIPANT-ROUTE
  on('tool.call', { tool: ['Read', 'Grep', 'NotebookRead'] }, async ($, e, next) => {
    const scope = await read($, scopeAtom)
    const snap = await read($, snapshotAtom)
    if (!scope?.isActive || scope.root === null || snap === null) return next(e)
    const input = e as unknown as { file_path?: string; path?: string; notebook_path?: string; limit?: number; offset?: number }
    const path = input.file_path ?? input.path ?? input.notebook_path
    if (path === undefined) return next(e)
    const rel = relativeTo(resolveFrom(await $.session.cwd(), path), scope.root)
    if (rel === null) return next(e)
    const headerOnly = /\.(tsv|csv)$/i.test(rel) && input.limit === 1 && (input.offset ?? 0) <= 1
    return decide($, e.tool_use_id, readViolations(rel, snap, headerOnly), opts, scope.isHeadless, toasted, () => next(e)) as ReturnType<typeof next>
  }).catch(($, e, next) => (next.called ? next(e) : mayEnforce(opts) ? { deny: 'neuroflow: a guard could not check this read — try again, or set the neuroflow mod to observe' } : next(e)))

  // nf-rule: GIT-NO-SECRETS · nf-rule: RAW-READONLY · nf-rule: PARTICIPANT-ROUTE · nf-rule: PREREG-FROZEN · nf-rule: EGRESS-CONFIRM · nf-rule: LOGIN-NODE
  on('tool.call', { tool: ['Bash', 'PowerShell'] }, async ($, e, next) => {
    const scope = await read($, scopeAtom)
    const snap = await read($, snapshotAtom)
    if (!scope?.isActive || scope.root === null || snap === null) return next(e)
    const command = (e as unknown as { command?: string }).command ?? ''
    if (command === '') return next(e)
    const gitignore = /\bgit\b[^;&|]*\badd\b/.test(command) ? await $.fs.read(join(scope.root, '.gitignore')).then(text => (typeof text === 'string' ? text : ''), () => '') : null
    const loginNode = isHeavy(command) ? await isLoginNode($) : false
    const violations = shellViolations(command, snap, { gitignore, isLoginNode: loginNode, gitAlias: await read($, gitAliasAtom) })
    return decide($, e.tool_use_id, violations, opts, scope.isHeadless, toasted, () => next(e)) as ReturnType<typeof next>
  }).catch(($, e, next) => (next.called ? next(e) : mayEnforce(opts) ? { deny: 'neuroflow: a guard could not check this command — try again, or set the neuroflow mod to observe' } : next(e)))
}
