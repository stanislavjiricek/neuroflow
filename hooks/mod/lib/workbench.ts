// The claude.ai workbench as the mod sees it on this machine (neuroflow-core → Workbench snapshot).
//  - ~/.neuroflow/workbench/pending.json, which workbench.py writes when /neuroflow:tasks --apply-web or
//    /neuroflow:dashboard --web runs: the band offers the apply command and the board marks the cards it names.
//  - the person's recorded workbench (the flowie's workbench.json, else workbench_records in ~/.neuroflow/user.yaml)
//    and their workbench_levels: the EGRESS-CONFIRM guard on ArtifactData writes reads them.
// The mod never calls ArtifactData itself and never sends anything: it only reads these local files.
import { BAND } from './keys'
import type { NfWebPending } from '../../../types'
import type { NfIo } from './io'
import { join, toSlash } from './paths'

/** A folder in one spelling: forward slashes, no trailing slash, a drive-lettered (Windows) path in lower case. */
const folderKey = (path: string): string => {
  const slashed = toSlash(path.trim()).replace(/\/+$/, '')
  return /^[A-Za-z]:/.test(slashed) ? slashed.toLowerCase() : slashed
}

export const WEB_APPLY = '/neuroflow:tasks --apply-web'

const asObject = (value: unknown): Record<string, unknown> | null =>
  value !== null && typeof value === 'object' && !Array.isArray(value) ? (value as Record<string, unknown>) : null

/** pending.json as the board and the band read it; null when it is missing, unreadable or names nothing waiting. */
export const parsePending = (text: string | null): NfWebPending | null => {
  if (text === null) return null
  let data: Record<string, unknown> | null
  try {
    data = asObject(JSON.parse(text))
  } catch {
    return null
  }
  if (data === null) return null
  const levels = (Array.isArray(data.levels) ? data.levels : [])
    .map(asObject)
    .filter((level): level is Record<string, unknown> => level !== null && typeof level.level === 'string')
    .map(level => ({
      level: String(level.level),
      kind: typeof level.kind === 'string' ? level.kind : null,
      board: typeof level.board === 'string' ? level.board : null,
      root: typeof level.root === 'string' ? level.root : null,
      slugs: Array.isArray(level.slugs) ? level.slugs.filter((slug): slug is string => typeof slug === 'string') : [],
      count: typeof level.count === 'number' ? level.count : 0,
    }))
  const count = typeof data.count === 'number' ? data.count : levels.reduce((sum, level) => sum + level.count, 0)
  if (count <= 0) return null
  return {
    checkedAt: typeof data.checked_at === 'string' ? data.checked_at : null,
    oldest: typeof data.oldest === 'string' ? data.oldest : null,
    count,
    levels,
  }
}

/** Reads pending.json from the home folder; null when there is none. */
export const loadPending = async (io: NfIo, home: string | null): Promise<NfWebPending | null> =>
  home === null ? null : parsePending(await io.read(join(toSlash(home), '.neuroflow/workbench/pending.json')))

/** "10:14", the local time pending.json was written; "" when it does not say. */
export const pendingTime = (iso: string | null): string => {
  const at = Date.parse(iso ?? '')
  if (Number.isNaN(at)) return ''
  const d = new Date(at)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

/**
 * The slugs waiting for a web change on one of the mod's boards: `flowie`, `hive:{folder}` (the board ids
 * workbench.py writes into pending.json), or the project board when pending.json names this project's root.
 */
export const pendingSlugs = (pending: NfWebPending | null, board: { id: string; kind: string }, root: string): Set<string> => {
  const out = new Set<string>()
  for (const level of pending?.levels ?? []) {
    const here = board.kind === 'project'
      ? level.kind === 'project' && level.root !== null && folderKey(level.root) === folderKey(root)
      : level.board === board.id
    if (here) for (const slug of level.slugs) out.add(slug)
  }
  return out
}

/** How long the oldest waiting change has waited: "40 min", "5 h", "3 days"; "" when pending.json does not say. */
export const pendingAge = (iso: string | null, nowMs: number): string => {
  const at = Date.parse(iso ?? '')
  if (Number.isNaN(at)) return ''
  const minutes = Math.max(0, Math.round((nowMs - at) / 60000))
  if (minutes < 60) return `${minutes} min`
  const hours = Math.round(minutes / 60)
  if (hours < 48) return `${hours} h`
  return `${Math.round(hours / 24)} days`
}

/**
 * `3 workbench changes wait (oldest 2 days, as of 10:14) — /neuroflow:tasks --apply-web`: the line commands/tasks.md →
 * Rendering puts after a board's footer (the board's, after `↻`), and the band's item.
 */
export const pendingText = (pending: { count: number; oldest?: string | null; checkedAt: string | null }, nowMs: number): string => {
  const time = pendingTime(pending.checkedAt)
  const age = pendingAge(pending.oldest ?? null, nowMs)
  const note = [age ? `oldest ${age}` : '', time ? `as of ${time}` : ''].filter(Boolean).join(', ')
  return `${pending.count} workbench change${pending.count === 1 ? '' : 's'} wait${pending.count === 1 ? 's' : ''}${note ? ` (${note})` : ''} — ${WEB_APPLY}`
}

/** The band's line while workbench changes wait for Claude Code; its key fills the apply command into the prompt. */
export const pendingBandItem = (pending: NfWebPending | null, nowMs: number = Date.now()) => {
  if (pending === null || pending.count <= 0) return null
  return {
    level: 'warn' as const,
    glyph: '↻',
    text: pendingText(pending, nowMs),
    actions: [{ key: 'nf-web-apply', label: 'apply', hotkey: BAND.apply, command: 'neuroflow:tasks', args: '--apply-web', fill: true }],
  }
}

// ── the guard on ArtifactData writes (nf-rule: EGRESS-CONFIRM) ───────────────────────────────────

export type NfWorkbenchContext = { urls: string[]; levels: string[] }

/** A claude.ai artifact URL in one spelling: no query, fragment or trailing slash, host in lower case. */
export const normalUrl = (url: unknown): string => {
  const text = typeof url === 'string' ? url.trim() : ''
  const match = /^(https?):\/\/([^/?#]+)([^?#]*)/i.exec(text)
  if (match === null) return text
  return `${match[1].toLowerCase()}://${match[2].toLowerCase()}${match[3].replace(/\/+$/, '')}`
}

/** A top-level key of user.yaml: a JSON value (lists and maps go in as JSON), an inline [a, b] list, or a scalar. */
export const yamlKey = (text: string | null, key: string): unknown => {
  if (text === null) return null
  const lines = text.replace(/\r\n/g, '\n').split('\n')
  const at = lines.findIndex(line => line.startsWith(`${key}:`))
  if (at < 0) return null
  const raw = lines[at].slice(key.length + 1).trim()
  if (raw === '') {
    const items: string[] = []
    for (const line of lines.slice(at + 1)) {
      const item = /^\s*-\s+(.*?)\s*$/.exec(line)
      if (item === null) break
      items.push(item[1].replace(/^(["'])(.*)\1$/, '$2'))
    }
    return items
  }
  for (const candidate of [raw, raw.replace(/\s+#.*$/, '')]) {
    try {
      return JSON.parse(candidate)
    } catch {
      // not JSON: an inline list or a scalar
    }
  }
  const plain = raw.replace(/\s+#.*$/, '')
  if (plain.startsWith('[') && plain.endsWith(']')) return plain.slice(1, -1).split(',').map(part => part.trim().replace(/^(["'])(.*)\1$/, '$2')).filter(Boolean)
  return plain.replace(/^(["'])(.*)\1$/, '$2')
}

/** The recorded workbench URLs (every account's) and the levels the person mirrors. */
export const workbenchContext = async (io: NfIo, home: string | null): Promise<NfWorkbenchContext> => {
  if (home === null) return { urls: [], levels: [] }
  const base = join(toSlash(home), '.neuroflow')
  const userYaml = await io.read(join(base, 'user.yaml'))
  const records: unknown[] = []
  const fromYaml = yamlKey(userYaml, 'workbench_records')
  if (Array.isArray(fromYaml)) records.push(...fromYaml)
  try {
    const flowie = asObject(JSON.parse((await io.read(join(base, 'flowie/workbench.json'))) ?? 'null'))
    if (flowie !== null && Array.isArray(flowie.workbenches)) records.push(...flowie.workbenches)
  } catch {
    // no record in the flowie
  }
  const urls = records.map(asObject).filter((item): item is Record<string, unknown> => item !== null && typeof item.url === 'string').map(item => normalUrl(item.url))
  const levels = yamlKey(userYaml, 'workbench_levels')
  return { urls, levels: Array.isArray(levels) ? levels.filter((level): level is string => typeof level === 'string') : [] }
}

export type ArtifactDataWrite = { op: string; collection: string; doc_id: string; if_version?: number; data?: Record<string, unknown>; file_path?: string }
export type ArtifactDataInput = ArtifactDataWrite & { action?: string; url?: string; writes?: ArtifactDataWrite[] }

const WRITES = new Set(['set', 'update', 'delete', 'str_replace', 'batch'])
const INTENTS = 'data/users/me/inbox/intents'
const INTENT_FIELDS = new Set(['status', 'claim', 'outcome'])

/** The writes an ArtifactData call makes, one entry each (a batch's `writes`, or the call itself). */
export const artifactWrites = (input: ArtifactDataInput): ArtifactDataWrite[] => {
  if (!WRITES.has(String(input.action))) return []
  if (input.action === 'batch') return Array.isArray(input.writes) ? input.writes : []
  return [{ op: String(input.action), collection: String(input.collection ?? ''), doc_id: String(input.doc_id ?? ''), if_version: input.if_version, data: input.data, file_path: input.file_path }]
}

export type ArtifactViolation = { level: 'deny' | 'ask'; message: string }

/**
 * What an ArtifactData write would break (neuroflow-core → Workbench snapshot, EGRESS-CONFIRM): it may go without a
 * question only to the person's recorded workbench, under data/users/me, for a level they mirror. Claude never
 * creates an intent — only the page does, from a person's click — so a write that would create or rewrite one
 * is denied; Claude only updates an intent's status, claim and outcome, pinned with if_version. A delete sends
 * nothing out. `bodies` holds the parsed files of entries that name a file_path (null: unreadable).
 */
export const artifactViolations = (input: ArtifactDataInput, context: NfWorkbenchContext, bodies: ReadonlyMap<string, Record<string, unknown> | null>): ArtifactViolation[] => {
  const writes = artifactWrites(input)
  if (writes.length === 0) return []
  const out: ArtifactViolation[] = []
  const add = (violation: ArtifactViolation) => {
    if (!out.some(item => item.message === violation.message)) out.push(violation)
  }
  if (!context.urls.includes(normalUrl(input.url))) {
    add({ level: 'ask', message: 'this writes to a claude.ai artifact that is not your recorded neuroflow workbench' })
  }
  for (const write of writes) {
    const collection = String(write.collection ?? '').replace(/\/+$/, '')
    if (collection === INTENTS) {
      if (write.op === 'delete') continue
      if (write.op !== 'update' || typeof write.if_version !== 'number') {
        add({ level: 'deny', message: 'only the workbench page creates intents (a person\'s click); Claude Code only updates their status, claim and outcome, pinned with if_version' })
        continue
      }
      const body = write.data ?? (write.file_path !== undefined ? bodies.get(write.file_path) : undefined)
      if (body === null || body === undefined) {
        add({ level: 'ask', message: 'an update of a workbench intent could not be read to check it' })
      } else if (Object.keys(body).some(key => !INTENT_FIELDS.has(key))) {
        add({ level: 'deny', message: 'an update of a workbench intent may set only its status, claim and outcome — never what the click asked for' })
      }
      continue
    }
    const path = `${collection}/${write.doc_id}`.split('/')
    if (path.length < 4 || path[0] !== 'data' || path[1] !== 'users' || path[2] !== 'me') {
      add({ level: 'ask', message: 'this writes to the artifact outside data/users/me, where the store keeps your private workbench' })
      continue
    }
    if (write.op === 'delete' || (path.length === 4 && path[3] === 'prefs')) continue
    if (!context.levels.includes(path[3])) {
      add({ level: 'ask', message: `this uploads ${path[3]}, which is not one of your workbench_levels in ~/.neuroflow/user.yaml` })
    }
  }
  return out
}
