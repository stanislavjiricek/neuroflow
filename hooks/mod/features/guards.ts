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
//   nf-rule: GIT-NO-SECRETS     `git clean -x`, staging local-only files; asks before `git add -A` without the .gitignore lines or in the flowie
//   nf-rule: GIT-ALIAS-SCOPE    git verbs beyond the running /git alias's endpoint (listings such as `git branch --show-current` are fine)
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

/** Local-only paths (neuroflow-core → Sharing tiers) that must never be staged, as the scaffold's .gitignore lines. */
export const LOCAL_ONLY = ['.neuroflow/sessions/', '.neuroflow/review/', '.neuroflow/integrations.json', '.neuroflow/flowie/', '.neuroflow/paper/xray-*', '.neuroflow/wiki/.pending/']

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

/** A shell segment's git subcommand, after git's own options. */
const GIT_COMMAND = /\bgit(?:\s+(?:-C\s+(?:"[^"]*"|'[^']*'|\S+)|-c\s+\S+|--no-pager|--git-dir=\S+|--work-tree=\S+))*\s+([a-z][a-z-]*)\b/

/** The git subcommand of a shell segment (`git -C dir add …` → add), or null when it runs no git. */
export const gitVerb = (segment: string): string | null => GIT_COMMAND.exec(segment)?.[1] ?? null

/**
 * Git verbs a /git alias may run (commands/git.md → Steps; alias scope is final): its endpoint and the
 * steps its prose takes on the way — unstaging local-only paths (`reset`), the stash offered before a pull.
 */
export const ALIAS_ALLOWS: Readonly<Record<string, readonly string[]>> = {
  a: ['add', 'reset', 'status', 'diff'],
  c: ['commit', 'reset', 'status', 'diff'],
  ac: ['add', 'reset', 'commit', 'status', 'diff'],
  acp: ['add', 'reset', 'commit', 'push', 'status', 'diff'],
  p: ['push', 'pull', 'fetch', 'stash', 'status'],
  pl: ['pull', 'fetch', 'stash', 'status'],
  ps: ['push', 'status'],
  b: ['branch', 'checkout', 'switch', 'status'],
  pr: ['push', 'status', 'diff', 'log'],
}

/** The verbs alias scope watches: everything that changes the index, history, refs or a remote — not their listings (isGitListing). */
const GUARDED_VERBS = ['add', 'commit', 'push', 'pull', 'fetch', 'merge', 'rebase', 'reset', 'checkout', 'switch', 'branch', 'tag', 'stash', 'cherry-pick', 'revert']

/** `git reset` that only unstages paths (`git reset -q -- <path>`): no mode flag, no commit to move to. */
const unstagesOnly = (args: readonly string[]): boolean => {
  const cut = args.indexOf('--')
  return cut >= 0 && cut + 1 < args.length && args.slice(0, cut).every(arg => /^(-q|--quiet|HEAD)$/.test(arg))
}

/** `git stash` as the pull steps use it: stash, push, pop, apply, list or show — never drop or clear. */
const stashesOnly = (args: readonly string[]): boolean => args.length === 0 || args[0].startsWith('-') || /^(push|pop|apply|list|show)$/.test(args[0])

/** Verbs an alias may run only in the form its prose takes (`c` unstages, `p` and `pl` stash before pulling). */
const ALIAS_FORMS: Readonly<Record<string, Readonly<Record<string, (args: readonly string[]) => boolean>>>> = {
  c: { reset: unstagesOnly },
  p: { stash: stashesOnly },
  pl: { stash: stashesOnly },
}

/** `git add` that stages everything: `.`, `:/`, `-A` / `--all`, `-u` / `--update` (also inside combined flags). */
const broadAdd = (args: readonly string[]): boolean =>
  args.some(arg => /^(\.|\.\/|:\/|:\(top\)|--all|--update)$/.test(arg) || /^-[a-zA-Z]*[Au][a-zA-Z]*$/.test(arg))

/** `git add -f` / `--force`: it stages ignored files too. */
const forcedAdd = (args: readonly string[]): boolean => args.some(arg => arg === '--force' || /^-[a-zA-Z]*f[a-zA-Z]*$/.test(arg))

/** The local-only paths a `git add` must never name (neuroflow-core → Sharing tiers). */
const LOCAL_NAMED = /(integrations\.json|\.neuroflow[\\/](sessions|review|flowie)\b|\.neuroflow[\\/]paper[\\/]xray-\S*|\.neuroflow[\\/]wiki[\\/]\.pending\b|user\.yaml)/i

/** How a shell command names the home folder: `~`, `$HOME`, `${HOME}`, `$env:USERPROFILE` (PowerShell), `%USERPROFILE%` (cmd). */
const HOME_REFS = ['~', '\\$\\{?HOME\\}?', '\\$\\{?env:(?:HOME|USERPROFILE)\\}?', '%(?:HOME|USERPROFILE)%']

/** The home folder's own path as a command may spell it: either slash, and a drive as `C:` or as Git Bash's `/c`. */
const homePaths = (home: string | null | undefined): string[] => {
  const path = toSlash(home ?? '').replace(/\/+$/, '')
  if (path === '') return []
  const drive = /^([A-Za-z]):(\/.*)?$/.exec(path)
  const msys = /^\/([A-Za-z])(\/.*)?$/.exec(path)
  const spellings = [path, ...(drive === null ? [] : [`/${drive[1]}${drive[2] ?? ''}`]), ...(msys === null ? [] : [`${msys[1]}:${msys[2] ?? ''}`])]
  return spellings.map(spelling => escapeRe(spelling).replace(/\//g, '[\\\\/]+'))
}

/**
 * The person's own `~/.neuroflow/` at the start of a shell word (`below`: a folder in it). It holds their flowie,
 * a repository whose files are committed and pushed, and their hive clones; only a project's `.neuroflow/` has the
 * local-only folders. Without the home folder's path, only `~`, `$HOME` and the like are recognised.
 */
const homeNeuroflow = (home: string | null | undefined, flags: string, below = ''): RegExp =>
  new RegExp(`(^|[\\s"'=])(?:${[...HOME_REFS, ...homePaths(home)].join('|')})[\\\\/]+\\.neuroflow${below}(?=[\\\\/"'\\s]|$)`, flags)

/** Whether a git segment runs in the person's flowie: `git -C ~/.neuroflow/flowie …`. */
const inHomeFlowie = (segment: string, home: string | null | undefined): boolean => {
  const match = GIT_COMMAND.exec(segment)
  return match !== null && homeNeuroflow(home, 'i', '[\\\\/]+flowie').test(match[0])
}

/** Where one shell command ends and the next begins: `&&`, `||`, `;`, `|`, a new line, or a lone `&` (not `&>`, `>&`, `2>&1`). */
const SEGMENTS = /&&|\|\||;|\||\r?\n|(?<![&>])&(?![&>])/

/** The commands of a shell line, one per segment. */
const segmentsOf = (line: string): string[] => line.split(SEGMENTS).map(part => part.trim()).filter(Boolean)

/** The words of a shell segment (best effort, nothing expanded): quotes removed, output redirections and their targets left out. */
const shellWords = (segment: string): string[] => {
  const tokens = segment.match(/(?:"[^"]*"|'[^']*'|[^\s"'])+/g) ?? []
  const words: string[] = []
  for (let i = 0; i < tokens.length; i += 1) {
    const redirect = /^(?:\d*|&|\*)>>?(&?)(.*)$/.exec(tokens[i])
    if (redirect === null) words.push(tokens[i].replace(/"([^"]*)"|'([^']*)'/g, '$1$2'))
    else if (redirect[1] === '' && redirect[2] === '') i += 1 // `> file`: the target is the next word
  }
  return words
}

/** The words after a segment's git subcommand. */
const gitArgs = (segment: string): string[] => {
  const match = GIT_COMMAND.exec(segment)
  return match === null ? [] : shellWords(segment.slice(match.index + match[0].length))
}

/**
 * The flags of `git branch` and `git tag` that only list or filter. Anything else (-d, -m, -u, -f,
 * --unset-upstream, -a for a tag…) creates, moves or deletes a ref. `listMode` flags turn the remaining
 * words into patterns; `valued` flags take the next word as their value.
 */
const LISTINGS: Readonly<Record<string, { flags: RegExp; listMode: RegExp; valued: RegExp }>> = {
  branch: {
    flags: /^(-[arvlqi]+|--(show-current|list|all|remotes|verbose|quiet|ignore-case|color|no-color|column|no-column|abbrev|no-abbrev|omit-empty|sort|format|contains|no-contains|with|without|merged|no-merged|points-at))$/,
    listMode: /^(-[a-z]*l[a-z]*|--(list|contains|no-contains|with|without|merged|no-merged|points-at))$/,
    valued: /^--(sort|format|points-at)$/,
  },
  tag: {
    flags: /^(-(?=[iln])[il]*(n\d*)?|--(list|ignore-case|color|no-color|column|no-column|omit-empty|sort|format|contains|no-contains|with|without|merged|no-merged|points-at))$/,
    listMode: /^(-[a-z\d]*[ln][a-z\d]*|--(list|contains|no-contains|with|without|merged|no-merged|points-at))$/,
    valued: /^--(sort|format|points-at)$/,
  },
}

/**
 * Whether a guarded git verb only lists or shows (`args`: the words after it), which is no step beyond any
 * alias's endpoint: `git branch` and `git tag` with no name to create (bare, or in list mode, where the
 * words are patterns), `git stash list` and `git stash show`.
 */
export const isGitListing = (verb: string, args: readonly string[]): boolean => {
  // a trailing `)` or backtick closes a command substitution: $(git branch --show-current)
  const words = args.map(arg => arg.replace(/[)`]+$/, '')).filter(arg => arg !== '')
  if (verb === 'stash') return words[0] === 'list' || words[0] === 'show'
  const form = LISTINGS[verb]
  if (form === undefined) return false
  let listMode = false
  let named = false
  for (let i = 0; i < words.length; i += 1) {
    const word = words[i]
    if (word === '--') {
      named = named || i + 1 < words.length
      break
    }
    if (!word.startsWith('-')) {
      named = true
      continue
    }
    const cut = word.indexOf('=')
    const flag = cut < 0 ? word : word.slice(0, cut)
    if (!form.flags.test(flag)) return false
    if (form.listMode.test(flag)) listMode = true
    if (cut < 0 && form.valued.test(flag)) i += 1
  }
  return listMode || !named
}

const escapeRe = (text: string): string => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

/** A pattern for a project-relative folder that matches either slash. */
const pathPattern = (root: string): string => escapeRe(trimRoot(root)).replace(/\//g, '[\\\\/]')

/**
 * A raw root inside one shell word, on path boundaries: `sourcedata`, `./sourcedata/x`, `/abs/sourcedata/x`,
 * `-Path:sourcedata`, `sourcedata*` — never `sourcedata_old/`, nor `draw_plot.png` for a root `raw/`.
 */
const rawWord = (root: string): RegExp => new RegExp(`(^|[\\\\/=:*?({\`])${pathPattern(root)}(?=[\\\\/*?[)}\`]|$)`, 'i')

type IgnoreRule = { negated: boolean; folderOnly: boolean; pattern: RegExp }

/** A gitignore glob as a regular expression: `*` and `?` stay inside one folder, `**` spans folders, `[…]` is a class. */
const globSource = (glob: string): string => {
  let out = ''
  for (let i = 0; i < glob.length; i += 1) {
    const char = glob[i]
    const close = char === '[' ? glob.indexOf(']', i + 2) : -1
    if (char === '*' && glob[i + 1] === '*' && (i === 0 || glob[i - 1] === '/') && (i + 2 === glob.length || glob[i + 2] === '/')) {
      // `**/` is any number of folders, none too; a trailing `/**` is everything inside
      out += i + 2 === glob.length ? '.*' : '(?:.*/)?'
      i += i + 2 === glob.length ? 1 : 2
    } else if (char === '*') {
      out += '[^/]*'
    } else if (char === '?') {
      out += '[^/]'
    } else if (close > 0) {
      out += `[${glob.slice(i + 1, close).replace(/^!/, '^').replace(/\\/g, '\\\\')}]`
      i = close
    } else {
      if (char === '\\' && i + 1 < glob.length) i += 1
      out += escapeRe(glob[i])
    }
  }
  return out
}

/**
 * The rules of the project's .gitignore, in order (gitignore(5)): comments skipped, `!` negates, a trailing
 * `/` matches folders only, and a slash before the end anchors a pattern to the project root.
 */
const ignoreRules = (text: string): IgnoreRule[] =>
  text.split(/\r?\n/).flatMap(raw => {
    let line = raw.trimEnd()
    if (line === '' || line.startsWith('#')) return []
    const negated = line.startsWith('!')
    if (negated) line = line.slice(1)
    const folderOnly = line.endsWith('/')
    line = line.replace(/\/+$/, '')
    const anchored = line.includes('/')
    line = line.replace(/^\//, '')
    if (line === '') return []
    const body = globSource(line)
    return [{ negated, folderOnly, pattern: new RegExp(anchored ? `^${body}$` : `^(?:.*/)?${body}$`) }]
  })

/** Whether git ignores the file `path` (project-relative): the last matching rule decides, and nothing inside an ignored folder can be brought back. */
const isIgnored = (rules: readonly IgnoreRule[], path: string): boolean => {
  const parts = path.split('/')
  for (let depth = 1; depth <= parts.length; depth += 1) {
    const sub = parts.slice(0, depth).join('/')
    const isFolder = depth < parts.length
    const last = rules.filter(rule => (isFolder || !rule.folderOnly) && rule.pattern.test(sub)).at(-1)
    if (last !== undefined && !last.negated) return true
  }
  return false
}

/**
 * The LOCAL_ONLY lines a .gitignore does not cover. Ignoring a folder above one covers it (`.neuroflow/`,
 * `/.neuroflow`, `.neuroflow/*`, `.neuroflow/**`); a narrower line (`*.md`, one session file) does not.
 */
export const uncoveredLocalOnly = (gitignore: string): string[] => {
  const rules = ignoreRules(gitignore)
  // a file name no narrower line would match stands for everything the local-only line names
  return LOCAL_ONLY.filter(line => !isIgnored(rules, line.endsWith('/') ? `${line}nf-any` : line.replace(/\*$/, 'nf-any')))
}

/** The files a segment's output redirections write to (`> f`, `2>>f`, `&> "f"`); `2>&1` writes none. */
const redirectTargets = (segment: string): string[] =>
  [...segment.matchAll(/(?<!>)>{1,2}\s*("[^"]*"|'[^']*'|[^\s"'<>;&|]+)/g)].map(match => match[1].replace(/^["']|["']$/g, ''))

/** Commands that change, rename or delete the files they name. */
const CHANGES = /^(rm|rmdir|del|erase|ren|rename|Remove-Item|Rename-Item|Set-Content|Out-File|truncate|shred)$/i

/** Commands that move files: a move takes its sources away and adds at its destination. */
const MOVES = /^(mv|move|Move-Item)$/i

/** The command a word names: `/bin/rm` → rm, `$(rm` → rm, `move.exe` → move. */
const commandName = (word: string): string => word.replace(/^[$({`]+/, '').replace(/^.*[\\/]/, '').replace(/\.exe$/i, '')

/**
 * A move's paths: what it takes away (`sources`) and where they go (`destination`, from `-t`,
 * `--target-directory` or `-Destination`, else the last path; `folder` when it can only be a folder).
 */
const moveParts = (args: readonly string[]): { sources: string[]; destination: string | null; folder: boolean } => {
  const paths: string[] = []
  let destination: string | null = null
  let folder = false
  for (let i = 0; i < args.length; i += 1) {
    const target = /^(?:-t|--target-directory)(?:=(.*))?$/.exec(args[i])
    const named = target ?? /^-Destination(?::(.*))?$/i.exec(args[i])
    if (named !== null) {
      destination = named[1] ?? args[i + 1] ?? ''
      folder = target !== null // -t names a folder; -Destination may name a file
      if (named[1] === undefined) i += 1 // the destination is the next word
    } else if (!args[i].startsWith('-')) {
      paths.push(args[i])
    }
  }
  if (destination !== null) return { sources: paths, destination, folder }
  return { sources: paths.slice(0, -1), destination: paths.at(-1) ?? null, folder: false }
}

/**
 * Whether a segment changes something under a raw root (`words`: shellWords; `targets`: redirectTargets):
 * writes into it by redirection, edits, renames or deletes a path in it, moves one out of it or onto a file
 * in it, or discards one through git. A copy, or a move into a folder there (a path ending in `/`, or
 * `-t`), adds a recording — allowed, like a new file written there. A quoted command line (`bash -c "…"`,
 * `powershell -Command "…"`, `cmd /c "…"`) is checked as a command line of its own.
 */
const changesRaw = (words: readonly string[], targets: readonly string[], inRoot: RegExp, verb: string | null, depth = 0): boolean => {
  if (targets.some(target => inRoot.test(target))) return true
  if ((verb === 'clean' || verb === 'checkout' || verb === 'restore') && words.some(word => inRoot.test(word))) return true
  const direct = words.some((word, at) => {
    const name = commandName(word)
    const rest = words.slice(at + 1)
    if (CHANGES.test(name)) return rest.some(arg => inRoot.test(arg))
    if (MOVES.test(name)) {
      const move = moveParts(rest)
      // Onto a path that names a file there, a move may replace a recording: only a folder destination adds one.
      const ontoFile = move.destination !== null && inRoot.test(move.destination) && !move.folder && !/[\\/]$/.test(move.destination)
      return ontoFile || move.sources.some(source => inRoot.test(source))
    }
    return name === 'sed' && rest.some(arg => /^(-[a-zA-Z]*i|--in-place)/.test(arg)) && rest.some(arg => inRoot.test(arg))
  })
  if (direct || depth >= 3) return direct
  // Only what a shell is told to run (`-c`, `-Command`, `/c`, `eval`) — not a commit message that names a command.
  return words.some((word, at) => at > 0 && /\s/.test(word) && /^(-[il]?c|-Command|\/[ck]|eval)$/i.test(words[at - 1]) &&
    segmentsOf(word).some(sub => changesRaw(shellWords(sub), redirectTargets(sub), inRoot, gitVerb(sub), depth + 1)))
}

const READ_VERBS = /^(cat|head|tail|less|more|type|Get-Content|gc|xxd|od|strings|bat|zcat)$/i

/** What a shell command would break (best effort: it cannot see inside the scripts it starts). */
export const shellViolations = (
  command: string,
  snap: NfSnapshot,
  context: { gitignore: string | null; isLoginNode: boolean; gitAlias?: string | null; home?: string | null },
): Violation[] => {
  const gitAlias = context.gitAlias ?? null
  const routeDenied = participantRoute(snap) === 'deny'
  const out: Violation[] = []
  for (const segment of segmentsOf(command)) {
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
      const args = gitArgs(segment)
      const form = ALIAS_FORMS[gitAlias]?.[verb]
      const inScope = allowed !== undefined && allowed.includes(verb) && (form === undefined || form(args))
      if (allowed !== undefined && GUARDED_VERBS.includes(verb) && !inScope && !isGitListing(verb, args)) {
        out.push({ rule: 'GIT-ALIAS-SCOPE', level: 'deny', message: `/git ${gitAlias} stops at its endpoint — \`git ${verb}${form !== undefined && allowed.includes(verb) ? ` ${args.join(' ')}` : ''}\` is beyond it; ask the person for a new instruction` })
      }
    }
    if (gitAlias !== null && /\bgh\s+pr\s+create\b/.test(segment) && gitAlias !== 'pr') {
      out.push({ rule: 'GIT-ALIAS-SCOPE', level: 'deny', message: `/git ${gitAlias} does not open pull requests — ask the person for a new instruction` })
    }
    if (verb === 'add') {
      // The home `.neuroflow/` is left out of this match: `~/.neuroflow/flowie` is the person's flowie repository,
      // not the project's local-only `.neuroflow/flowie/` (the flowie's integrations.json is still local-only).
      const named = LOCAL_NAMED.exec(segment.replace(homeNeuroflow(context.home, 'gi'), '$1~'))
      const args = gitArgs(segment)
      if (named !== null) {
        out.push({ rule: 'GIT-NO-SECRETS', level: 'deny', message: `${named[1]} is local-only (sessions, confidential reviews, paper X-rays, wiki cards awaiting review, personal settings) and must never be committed` })
      } else if (broadAdd(args) && forcedAdd(args)) {
        out.push({ rule: 'GIT-NO-SECRETS', level: 'deny', message: `\`${segment.slice(0, 80)}\` stages ignored files too, local-only ones included — stage the files you mean by name` })
      } else if (broadAdd(args) && inHomeFlowie(segment, context.home)) {
        // The project's .gitignore says nothing about the flowie, whose files are staged by path (/flowie → Git operations pattern).
        out.push({ rule: 'GIT-NO-SECRETS', level: 'ask', message: `\`${segment.slice(0, 80)}\` stages everything in your flowie — stage the files you mean by name, never integrations.json` })
      } else if (broadAdd(args)) {
        // An ask, not a denial: /git a stages everything and then takes each local-only path back out.
        const missing = uncoveredLocalOnly(context.gitignore ?? '')
        if (missing.length > 0) {
          out.push({
            rule: 'GIT-NO-SECRETS',
            level: 'ask',
            message: `\`${segment.slice(0, 80)}\` would stage local-only files: .gitignore does not exclude ${missing.join(', ')} — add those lines (/neuroflow:migrate adds them), or take each one back out after staging (git reset -q -- <path>)`,
          })
        }
      }
    }
    const argv = shellWords(segment)
    const targets = redirectTargets(segment)
    for (const root of rawRootsOf(snap)) {
      if (trimRoot(root) === '') continue
      if (changesRaw(argv, targets, rawWord(root), verb)) {
        out.push({ rule: 'RAW-READONLY', level: 'deny', message: `this command would change, move or delete files under ${root}, a read-only raw-data folder (raw_roots) — write derivatives elsewhere; new recordings may be added` })
      }
    }
    if (routeDenied) {
      const words = segment.split(/\s+/).map(word => word.replace(/^["']|["']$/g, ''))
      if (words.length > 1 && READ_VERBS.test(words[0])) {
        for (const root of rawRootsOf(snap)) {
          const inRoot = rawWord(root)
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
    const home = gitignore !== null ? ((await ioOf($).home()) ?? null) : null
    const loginNode = isHeavy(command) ? await isLoginNode($) : false
    const violations = shellViolations(command, snap, { gitignore, isLoginNode: loginNode, gitAlias: await read($, gitAliasAtom), home })
    return decide($, e.tool_use_id, violations, opts, scope.isHeadless, toasted, () => next(e)) as ReturnType<typeof next>
  }).catch(($, e, next) => (next.called ? next(e) : mayEnforce(opts) ? { deny: 'neuroflow: a guard could not check this command — try again, or set the neuroflow mod to observe' } : next(e)))
}
