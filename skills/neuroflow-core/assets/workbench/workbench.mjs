// neuroflow workbench — the page's logic (neuroflow-core → Workbench snapshot).
//
// Pure functions only: no DOM, no network, no imports. `workbench.py stage` inlines this file into
// workbench.html (dropping the `export` keywords), and tests/workbench/workbench.test.mjs runs it under
// `node --test` against the golden snapshot workbench.py writes, so the exporter and the page read one format.
// The page renders what the snapshot says and turns gestures into intent documents; every rule about what an
// intent may do lives in workbench.py, which Claude Code runs before anything reaches git.

export const SNAP_SCHEMA = 1
export const INTENT_SCHEMA = 1
export const PREFS_SCHEMA = 1
export const CLAIM_TTL_MS = 30 * 60 * 1000
export const RECENT_MS = 24 * 60 * 60 * 1000
export const APPLY_COMMAND = '/neuroflow:tasks --apply-web'
export const SETUP_COMMAND = '/neuroflow:dashboard --web'

// ── database paths: data/users/{the viewer's own id}/… (Claude's ArtifactData writes data/users/me/…) ────

const SEGMENT = /^(?!\.\.?$)[A-Za-z0-9_\-.~:@+]{1,200}$/

export function validSegment(text) {
  return typeof text === 'string' && SEGMENT.test(text)
}

export function segments(path) {
  return String(path).split('/').length
}

export function isDocumentPath(path) {
  return segments(path) % 2 === 0 && String(path).split('/').every(validSegment)
}

export function isCollectionPath(path) {
  return segments(path) % 2 === 1 && String(path).split('/').every(validSegment)
}

/** The viewer's own collection: one meta document per level, and the preferences. */
export function userRoot(uid) {
  return `data/users/${uid}`
}

export function metaPath(uid, level) {
  return `data/users/${uid}/${level}`
}

export function partsPath(uid, level) {
  return `data/users/${uid}/${level}/parts`
}

export function intentsPath(uid) {
  return `data/users/${uid}/inbox/intents`
}

export function prefsPath(uid) {
  return `data/users/${uid}/prefs`
}

/** A level key as workbench.py writes it: flowie, hive+{org}+{repo}, project+{card id or host+owner+repo}. */
export function validLevelKey(key) {
  return typeof key === 'string' && key !== 'prefs' && key !== 'inbox' && /^[a-z0-9_\-.~+]{1,200}$/.test(key) &&
    (key === 'flowie' || key.startsWith('hive+') || key.startsWith('project+'))
}

/**
 * A fresh intent id, `i-{8}-{12}` from random letters and digits only: valid as a document id, and silent about when
 * the person clicked — the id travels into hive commits as a Neuroflow-Intent trailer. Order comes from created_at.
 */
export function newIntentId(random) {
  const text = String(random || '').toLowerCase().replace(/[^0-9a-z]/g, '').padEnd(20, '0').slice(0, 20)
  return `i-${text.slice(0, 8)}-${text.slice(8)}`
}

// ── dates in the viewer's own calendar ─────────────────────────────────────────────────────────────

export function localDate(nowMs) {
  const d = new Date(nowMs)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/** Days from `today` to `date` (both YYYY-MM-DD); negative when it has passed; null when either is not a date. */
export function daysUntil(date, today) {
  const re = /^(\d{4})-(\d{2})-(\d{2})/
  const a = re.exec(String(date || ''))
  const b = re.exec(String(today || ''))
  if (!a || !b) return null
  const t = Date.UTC(+a[1], +a[2] - 1, +a[3])
  const n = Date.UTC(+b[1], +b[2] - 1, +b[3])
  return Math.round((t - n) / 86400000)
}

export function isOverdue(due, today, closed) {
  const days = daysUntil(due, today)
  return !closed && days !== null && days < 0
}

export function relativeAge(iso, nowMs) {
  const then = Date.parse(iso || '')
  if (Number.isNaN(then)) return 'at an unknown time'
  const minutes = Math.round((nowMs - then) / 60000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes} min ago`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours} h ago`
  const days = Math.round(hours / 24)
  return `${days} day${days === 1 ? '' : 's'} ago`
}

// ── a level, assembled from its meta and parts ──────────────────────────────────────────────────────

/**
 * The level as the page draws it, from its meta document and its part documents. A meta from a newer neuroflow
 * is not guessed at; parts that do not match the hashes the meta lists mean an export is still being written.
 */
export function assembleLevel(meta, partDocs) {
  if (!meta || typeof meta !== 'object') return { status: 'invalid', reason: 'no level document' }
  if (typeof meta.snap_schema !== 'number' || meta.snap_schema > SNAP_SCHEMA) {
    return { status: 'newer', reason: 'written by a newer neuroflow — update neuroflow where you run Claude Code' }
  }
  const byId = new Map()
  for (const doc of partDocs || []) if (doc && typeof doc.part === 'string') byId.set(doc.part, doc)
  const listed = Array.isArray(meta.parts) ? meta.parts : []
  for (const entry of listed) {
    const doc = byId.get(entry.id)
    if (!doc || doc.sha256 !== entry.sha256) return { status: 'updating', reason: 'an export is being written' }
  }
  const core = byId.get('core') || {}
  const cards = []
  const pages = []
  for (const entry of listed) {
    const doc = byId.get(entry.id)
    if (Array.isArray(doc.cards)) cards.push(...doc.cards)
    if (Array.isArray(doc.pages)) pages.push(...doc.pages)
  }
  return {
    status: 'ready',
    level: {
      key: meta.level,
      kind: meta.kind,
      label: meta.label || meta.level,
      meta,
      columns: Array.isArray(core.columns) ? core.columns : [],
      people: Array.isArray(core.people) ? core.people : [],
      registry: Array.isArray(core.registry) ? core.registry : [],
      panel: core.panel && typeof core.panel === 'object' ? core.panel : {},
      phases: Array.isArray(core.phases) ? core.phases : [],
      card: core.card || null,
      cards,
      pages,
    },
  }
}

const KIND_RANK = { flowie: 0, hive: 1, project: 2 }

/** The tabs in the person's order: the order they chose, then the flowie, the hives and the projects by name. */
export function levelOrder(metas, prefs) {
  const keys = Object.keys(metas || {}).filter(validLevelKey)
  const chosen = (prefs && Array.isArray(prefs.order) ? prefs.order : []).filter(key => keys.includes(key))
  const hidden = new Set(prefs && Array.isArray(prefs.hidden) ? prefs.hidden : [])
  const rest = keys
    .filter(key => !chosen.includes(key))
    .sort((a, b) => (KIND_RANK[metas[a].kind] ?? 3) - (KIND_RANK[metas[b].kind] ?? 3) || String(metas[a].label || a).localeCompare(String(metas[b].label || b)))
  return [...chosen, ...rest].filter(key => !hidden.has(key))
}

// ── intents: what the page queued and what became of it ────────────────────────────────────────────

function createdOrder(a, b) {
  return String(a.created_at || '').localeCompare(String(b.created_at || '')) || String(a.id).localeCompare(String(b.id))
}

/**
 * The intents whose effect the page still draws over the snapshot: not finished, not contained in the snapshot
 * (the export lists the ids its files already hold), and not cancelled by a cancel that waits too.
 */
export function activeIntents(intents, level, meta) {
  const applied = meta && meta.applied && typeof meta.applied === 'object' ? meta.applied : {}
  const all = (intents || []).filter(item => item && item.level === level)
  const failed = new Set(all.filter(item => item.status === 'done' && item.outcome && ['rejected', 'conflict', 'cancelled'].includes(item.outcome.result)).map(item => item.id))
  const mine = all.filter(item => item.status !== 'done' && !(item.id in applied)).sort(createdOrder)
  const dropped = new Set(mine.filter(item => item.op === 'cancel' && item.target && item.target.intent).map(item => item.target.intent))
  for (const item of mine) if (item.cancel_requested_at) dropped.add(item.id)
  // a link whose earlier link is cancelled or failed will be rejected ("depends on …"): it is not drawn either
  for (const item of mine) if (item.after && (dropped.has(item.after) || failed.has(item.after))) dropped.add(item.id)
  return mine.filter(item => item.op !== 'cancel' && !dropped.has(item.id))
}

/** Intents of the level waiting for Claude Code (cancels included): for the counts and the command line. */
export function waitingIntents(intents, level) {
  return (intents || []).filter(item => item && item.status !== 'done' && (level === undefined || item.level === level))
}

function claimState(item, nowMs) {
  if (item.status !== 'claimed') return { state: 'pending' }
  const claim = item.claim && typeof item.claim === 'object' ? item.claim : {}
  const at = Date.parse(claim.claimed_at || '')
  const stale = !Number.isNaN(at) && nowMs - at > CLAIM_TTL_MS
  return { state: stale ? 'stale' : 'claimed', by: claim.machine || 'another machine', at: claim.claimed_at || null }
}

/** One sentence for an intent's outcome, as the page shows it. */
export function outcomeText(outcome) {
  if (!outcome || typeof outcome !== 'object') return ''
  switch (outcome.result) {
    case 'applied': {
      const where = { worktree: 'in the project\'s working tree, not committed', committed: 'committed, not pushed', pushed: 'pushed', merged: 'merged' }
      return outcome.note && /no change/.test(outcome.note) ? 'applied: no change' : `applied${outcome.state ? ` — ${where[outcome.state] || outcome.state}` : ''}`
    }
    case 'coalesced': return 'merged into a later move of the same card'
    case 'conflict': return `not applied: ${outcome.reason || 'the task changed'}`
    case 'rejected': return `not applied: ${outcome.reason || 'rejected'}`
    case 'cancelled': return outcome.by === 'release' ? 'cancelled on the workbench' : 'cancelled'
    default: return String(outcome.result || '')
  }
}

/** Finished intents of the last day whose outcome the person may want to see (conflicts and rejections first). */
export function recentOutcomes(intents, level, nowMs, maxAgeMs = RECENT_MS) {
  return (intents || [])
    .filter(item => item && item.level === level && item.status === 'done' && item.outcome)
    .filter(item => {
      const at = Date.parse(item.outcome.at || '')
      return !Number.isNaN(at) && nowMs - at <= maxAgeMs
    })
    .sort((a, b) => Number(['conflict', 'rejected'].includes(b.outcome.result)) - Number(['conflict', 'rejected'].includes(a.outcome.result)) || createdOrder(b, a))
}

// ── the board ──────────────────────────────────────────────────────────────────────────────────────

function cardKeyOf(card) {
  return card.isNew ? `intent:${card.addId}` : `slug:${card.slug}`
}

/**
 * The board as the page draws it: the snapshot's cards with the waiting intents laid over them in creation
 * order — a moved card shows in its new column with a pending mark, an added card shows where it was added.
 * Overdue and "this project" come from the viewer's own date and the project the person focuses.
 */
export function boardModel(level, intents, options = {}) {
  const today = options.today || '0000-00-00'
  const focus = options.focusProject || null
  const filter = options.filter || {}
  const hidden = new Set(options.hiddenColumns || [])
  const nowMs = options.nowMs ?? 0
  const columns = (level.columns || []).map(column => ({ ...column }))
  const known = new Set(columns.map(column => column.id))
  const cards = new Map()
  for (const raw of level.cards || []) {
    if (!known.has(raw.column)) {
      known.add(raw.column)
      columns.push({ id: raw.column, label: raw.column, closed: false, archive: false, extra: true })
    }
    const card = { ...raw, isNew: false, pending: null, movable: raw.readable !== false && !raw.legacy, originalColumn: raw.column }
    cards.set(cardKeyOf(card), card)
  }
  for (const item of activeIntents(intents, level.key, level.meta)) {
    const claim = claimState(item, nowMs)
    if (item.op === 'add') {
      const fields = item.fields || {}
      const card = {
        slug: null, addId: item.id, isNew: true, title: String(fields.title || ''), owner: fields.owner || null, due: fields.due || null,
        project: fields.project || null, tags: Array.isArray(fields.tags) ? fields.tags : [], blocked_by: [], column: item.to || 'inbox',
        notes: '', movable: true, originalColumn: null, pending: { ids: [item.id], last: item.id, ...claim },
      }
      cards.set(cardKeyOf(card), card)
      continue
    }
    if (item.op !== 'move' || !item.target) continue
    const key = item.target.intent ? `intent:${item.target.intent}` : `slug:${item.target.slug}`
    const card = cards.get(key)
    if (!card) continue
    card.column = item.to
    card.pending = { ids: [...(card.pending ? card.pending.ids : []), item.id], last: item.id, ...claim, from: card.originalColumn }
  }
  const recent = new Map()
  for (const item of recentOutcomes(intents, level.key, nowMs)) {
    if (!['conflict', 'rejected'].includes(item.outcome.result) || !item.target || !item.target.slug) continue
    if (!recent.has(item.target.slug)) recent.set(item.target.slug, item)
  }
  const text = String(filter.text || '').trim().toLowerCase()
  const shown = [...cards.values()].filter(card => {
    if (text && !`${card.title} ${card.slug || ''} ${(card.tags || []).join(' ')}`.toLowerCase().includes(text)) return false
    if (filter.owner && card.owner !== filter.owner) return false
    if (filter.project && card.project !== filter.project) return false
    if (filter.tag && !(card.tags || []).includes(filter.tag)) return false
    if (filter.overdue && !isOverdue(card.due, today, columnClosed(columns, card.column))) return false
    return true
  })
  const out = columns
    .filter(column => !hidden.has(column.id))
    .map(column => {
      const list = shown
        .filter(card => card.column === column.id)
        .map(card => ({
          ...card,
          key: cardKeyOf(card),
          overdue: isOverdue(card.due, today, column.closed),
          mine: focus !== null && card.project === focus,
          outcome: card.slug && recent.has(card.slug) && !card.pending ? recent.get(card.slug).outcome : null,
        }))
        .sort((a, b) => Number(b.mine) - Number(a.mine) || Number(b.overdue) - Number(a.overdue) ||
          String(a.due || '9999').localeCompare(String(b.due || '9999')) || String(a.title).localeCompare(String(b.title)))
      const limit = options.wip && Number(options.wip[column.id]) > 0 ? Number(options.wip[column.id]) : null
      return { ...column, cards: list, count: list.length, wip: limit, overLimit: limit !== null && list.length > limit }
    })
  const pending = waitingIntents(intents, level.key).length
  return { columns: out, pending, total: shown.length }
}

function columnClosed(columns, id) {
  const column = columns.find(item => item.id === id)
  return Boolean(column && column.closed)
}

/** Groups of a column's cards for swimlanes: by project or by owner; one unnamed group without grouping. */
export function lanes(cards, groupBy) {
  if (groupBy !== 'project' && groupBy !== 'owner') return [{ name: null, cards }]
  const groups = new Map()
  for (const card of cards) {
    const name = card[groupBy] || null
    if (!groups.has(name)) groups.set(name, [])
    groups.get(name).push(card)
  }
  return [...groups.entries()]
    .sort((a, b) => (a[0] === null) - (b[0] === null) || String(a[0]).localeCompare(String(b[0])))
    .map(([name, list]) => ({ name, cards: list }))
}

// ── gestures → intents (the page writes these; Claude Code checks and applies them) ───────────────────

function stamp(nowMs) {
  return new Date(nowMs).toISOString()
}

/**
 * The intent for moving `card` (a board card, as boardModel drew it) to column `to`; null when it would not move
 * or cannot be moved. A card that already waits for a move or was added on the board is chained with `after`, and
 * an added card is named by its add, since it has no slug until Claude Code adds it.
 */
export function makeMove({ level, card, to, nowMs, id }) {
  if (!card || !card.movable || !to || to === card.column) return null
  const intent = {
    intent_schema: INTENT_SCHEMA, op: 'move', level, from: card.column, to, created_at: stamp(nowMs), status: 'pending',
    target: card.isNew ? { intent: card.addId } : { slug: card.slug },
  }
  if (!card.isNew) intent.base = card.sha256
  if (card.pending && card.pending.last) intent.after = card.pending.last
  return withId(intent, id)
}

/** The intent for a card added on the board. */
export function makeAdd({ level, fields, to, nowMs, id }) {
  const title = String((fields && fields.title) || '').trim().slice(0, 200)
  if (!title) return null
  const clean = { title }
  for (const key of ['owner', 'due', 'phase', 'project']) {
    const value = fields && typeof fields[key] === 'string' ? fields[key].trim() : ''
    if (value) clean[key] = value
  }
  if (clean.due && !/^\d{4}-\d{2}-\d{2}$/.test(clean.due)) delete clean.due
  const tags = fields && Array.isArray(fields.tags) ? fields.tags.map(tag => String(tag).trim()).filter(Boolean) : []
  if (tags.length) clean.tags = tags
  return withId({ intent_schema: INTENT_SCHEMA, op: 'add', level, fields: clean, to: to || 'inbox', created_at: stamp(nowMs), status: 'pending' }, id)
}

/** Undo: a cancel of the card's last waiting intent (an intent is never deleted, so a claim cannot race it). */
export function makeCancel({ level, target, nowMs, id }) {
  if (!target) return null
  return withId({ intent_schema: INTENT_SCHEMA, op: 'cancel', level, target: { intent: target }, created_at: stamp(nowMs), status: 'pending' }, id)
}

/** The page's release of a claim that never finished: Claude Code reads it and cancels the intent. */
export function releasePatch(nowMs) {
  return { cancel_requested_at: stamp(nowMs) }
}

function withId(intent, id) {
  return { ...intent, id }
}

/** The document the page writes for an intent (its id is the document id, not a field). */
export function intentDocument(intent) {
  const { id, ...doc } = intent
  return doc
}

/** The column to the left or right of `column` on the board (for the keyboard move); null at the edge. */
export function neighbourColumn(columns, column, step) {
  const ids = columns.filter(item => !item.archive).map(item => item.id)
  const at = ids.indexOf(column)
  if (at < 0) return null
  const next = at + step
  return next >= 0 && next < ids.length ? ids[next] : null
}

// ── freshness: what the export saw, and what it could not ────────────────────────────────────────────

/** The tab's label, word for word as workbench.py's freshness() writes it; `time` formats the timestamps. */
export function freshnessLabel(meta, time = value => value) {
  const src = (meta && meta.source) || {}
  const machine = meta && meta.machine
  if (!src.git) return `files as they are on ${machine || 'this machine'} (no git), exported ${time(meta && meta.exported_at)}`
  const head = String(src.head || '?').slice(0, 7)
  let text = `${meta.working_tree ? 'working tree' : 'clone'} on ${src.branch || '?'} @ ${head}`
  if (src.uncommitted_tasks) text += ` + ${src.uncommitted_tasks} uncommitted task change${src.uncommitted_tasks === 1 ? '' : 's'}`
  text += ` · upstream fetched ${src.fetched_at ? time(src.fetched_at) : 'never'}`
  return `${text} · from ${machine || 'an unnamed machine'}`
}

// ── preferences ────────────────────────────────────────────────────────────────────────────────────

export function defaultPrefs() {
  return {
    prefs_schema: PREFS_SCHEMA, theme: 'system', density: 'comfortable', order: [], hidden: [], default_level: null,
    views: {}, fields: { owner: true, due: true, project: true, tags: true, notes: false }, hidden_columns: {}, wip: {},
    group_by: 'none', focus_project: null, show_archive: false,
  }
}

const ONE_OF = { theme: ['system', 'dark', 'light'], density: ['comfortable', 'compact'], group_by: ['none', 'project', 'owner'] }

/** The stored preferences, every field checked; anything odd falls back to the default. */
export function normalizePrefs(doc) {
  const out = defaultPrefs()
  if (!doc || typeof doc !== 'object') return out
  for (const [key, values] of Object.entries(ONE_OF)) if (values.includes(doc[key])) out[key] = doc[key]
  for (const key of ['order', 'hidden']) if (Array.isArray(doc[key])) out[key] = doc[key].filter(validLevelKey)
  if (validLevelKey(doc.default_level)) out.default_level = doc.default_level
  if (typeof doc.focus_project === 'string' && doc.focus_project.length <= 200) out.focus_project = doc.focus_project
  if (typeof doc.show_archive === 'boolean') out.show_archive = doc.show_archive
  if (doc.fields && typeof doc.fields === 'object') for (const key of Object.keys(out.fields)) if (typeof doc.fields[key] === 'boolean') out.fields[key] = doc.fields[key]
  if (doc.views && typeof doc.views === 'object') {
    for (const [key, view] of Object.entries(doc.views)) if (validLevelKey(key) && ['board', 'projects', 'wiki', 'level'].includes(view)) out.views[key] = view
  }
  if (doc.hidden_columns && typeof doc.hidden_columns === 'object') {
    for (const [key, list] of Object.entries(doc.hidden_columns)) if (validLevelKey(key) && Array.isArray(list)) out.hidden_columns[key] = list.filter(validSegment)
  }
  if (doc.wip && typeof doc.wip === 'object') {
    for (const [key, limits] of Object.entries(doc.wip)) {
      if (!validLevelKey(key) || !limits || typeof limits !== 'object') continue
      const clean = {}
      for (const [column, n] of Object.entries(limits)) if (validSegment(column) && Number.isInteger(n) && n > 0 && n < 1000) clean[column] = n
      out.wip[key] = clean
    }
  }
  return out
}

export function prefsEqual(a, b) {
  return JSON.stringify(normalizePrefs(a)) === JSON.stringify(normalizePrefs(b))
}

// ── markdown → a token tree (the page builds elements from it with textContent; no HTML is ever parsed) ──

/**
 * Inline tokens: text, strong, em, code, link (http and https only), wikilink ([[id|label]] as workbench.py
 * resolved it; an empty id did not resolve) and the exporter's "local file, not mirrored" marker.
 */
export function parseInline(text) {
  const out = []
  const source = String(text || '')
  const re = /\[\[([^\[\]|\n]*)\|([^\[\]\n]*)\]\]|\[local file, not mirrored: ([^\]\n]*)\]|`([^`\n]+)`|\*\*([^*\n]+)\*\*|__([^_\n]+)__|\*([^*\n]+)\*|(?<![\w])_([^_\n]+)_(?![\w])|\[([^\[\]\n]+)\]\(([^()\s]+)\)|(https?:\/\/[^\s<>()]+[^\s<>().,;:!?'")\]])/g
  let last = 0
  let match
  while ((match = re.exec(source)) !== null) {
    if (match.index > last) out.push({ type: 'text', text: source.slice(last, match.index) })
    if (match[2] !== undefined && match[0].startsWith('[[')) out.push({ type: 'wikilink', target: match[1], label: match[2] || match[1] })
    else if (match[3] !== undefined) out.push({ type: 'local', name: match[3] })
    else if (match[4] !== undefined) out.push({ type: 'code', text: match[4] })
    else if (match[5] !== undefined || match[6] !== undefined) out.push({ type: 'strong', children: parseInline(match[5] ?? match[6]) })
    else if (match[7] !== undefined || match[8] !== undefined) out.push({ type: 'em', children: parseInline(match[7] ?? match[8]) })
    else if (match[9] !== undefined) {
      const href = safeHref(match[10])
      out.push(href ? { type: 'link', href, children: parseInline(match[9]) } : { type: 'text', text: match[0] })
    } else if (match[11] !== undefined) out.push({ type: 'link', href: match[11], children: [{ type: 'text', text: match[11] }] })
    last = re.lastIndex
  }
  if (last < source.length) out.push({ type: 'text', text: source.slice(last) })
  return out
}

/** Only absolute http(s) links leave the page; anything else (javascript:, data:, relative paths) stays text. */
export function safeHref(url) {
  const text = String(url || '').trim()
  return /^https?:\/\/[^\s]+$/i.test(text) ? text : null
}

/** A table's delimiter row: cells of one or more dashes, each with an optional colon at either end (`|:-|:-:|`, `---|---`). */
export function isDelimiterRow(line) {
  const text = String(line || '').trim()
  if (!text.includes('-')) return false
  return text.replace(/^\|/, '').replace(/\|$/, '').split('|').every(cell => /^:?-+:?$/.test(cell.trim()))
}

/**
 * Block tokens: heading, paragraph, list (nested by indent), code, quote, table, hr. Every pass takes at least one
 * line, so any text ends: a line no other block claims becomes a paragraph, and a `|` line starts a table only when
 * a delimiter row follows it.
 */
export function parseMarkdown(text) {
  const lines = String(text || '').replace(/\r\n?/g, '\n').split('\n')
  const blocks = []
  let i = 0
  const isBlank = line => line.trim() === ''
  const startsTable = at => /^\s*\|/.test(lines[at]) && at + 1 < lines.length && isDelimiterRow(lines[at + 1])
  const startsBlock = at => /^(#{1,6})\s/.test(lines[at]) || /^\s*(```|~~~|>)/.test(lines[at]) || /^\s*([-*+]|\d+[.)])\s+/.test(lines[at]) || startsTable(at)
  while (i < lines.length) {
    const line = lines[i]
    if (isBlank(line)) { i += 1; continue }
    const fence = /^\s*(```|~~~)/.exec(line)
    if (fence) {
      const body = []
      i += 1
      while (i < lines.length && !lines[i].trim().startsWith(fence[1])) { body.push(lines[i]); i += 1 }
      i += 1
      blocks.push({ type: 'code', text: body.join('\n') })
      continue
    }
    const heading = /^(#{1,6})\s+(.*?)\s*#*\s*$/.exec(line)
    if (heading) { blocks.push({ type: 'heading', level: heading[1].length, inline: parseInline(heading[2]) }); i += 1; continue }
    if (/^\s*([-*_])(\s*\1){2,}\s*$/.test(line)) { blocks.push({ type: 'hr' }); i += 1; continue }
    if (/^\s*>/.test(line)) {
      const body = []
      while (i < lines.length && /^\s*>/.test(lines[i])) { body.push(lines[i].replace(/^\s*>\s?/, '')); i += 1 }
      blocks.push({ type: 'quote', blocks: parseMarkdown(body.join('\n')) })
      continue
    }
    if (startsTable(i)) {
      const cells = row => row.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map(cell => parseInline(cell.trim()))
      const header = cells(line)
      const rows = []
      i += 2
      while (i < lines.length && /^\s*\|/.test(lines[i])) { rows.push(cells(lines[i])); i += 1 }
      blocks.push({ type: 'table', header, rows })
      continue
    }
    if (/^\s*([-*+]|\d+[.)])\s+/.test(line)) {
      const items = []
      while (i < lines.length && (/^\s*([-*+]|\d+[.)])\s+/.test(lines[i]) || (/^\s{2,}\S/.test(lines[i]) && items.length))) {
        const item = /^(\s*)([-*+]|\d+[.)])\s+(.*)$/.exec(lines[i])
        const task = item && /^\[( |x|X)\]\s/.test(item[3]) ? item[3][1] !== ' ' : null
        if (item) items.push({ depth: Math.floor(item[1].replace(/\t/g, '  ').length / 2), ordered: /\d/.test(item[2]), inline: parseInline(task === null ? item[3] : item[3].slice(4)), task })
        else items[items.length - 1].inline.push({ type: 'text', text: ` ${lines[i].trim()}` })
        i += 1
      }
      blocks.push({ type: 'list', ordered: items[0].ordered, items: nestItems(items) })
      continue
    }
    // a paragraph: this line (whatever it starts with — no block above claimed it), then the lines up to the next block
    const body = [line.trim()]
    i += 1
    while (i < lines.length && !isBlank(lines[i]) && !startsBlock(i)) {
      body.push(lines[i].trim())
      i += 1
    }
    blocks.push({ type: 'paragraph', inline: parseInline(body.join(' ')) })
  }
  return blocks
}

function nestItems(items) {
  const root = []
  const stack = [{ depth: -1, children: root }]
  for (const item of items) {
    const node = { inline: item.inline, task: item.task, ordered: item.ordered, children: [] }
    while (stack.length > 1 && stack[stack.length - 1].depth >= item.depth) stack.pop()
    stack[stack.length - 1].children.push(node)
    stack.push({ depth: item.depth, children: node.children })
  }
  return root
}

// ── the wiki ───────────────────────────────────────────────────────────────────────────────────────

const TYPE_ORDER = ['concept', 'method', 'entity', 'source', 'synthesis']

/** The index grouped by page type, filtered by a search over titles, tags and summaries. */
export function wikiIndex(pages, query) {
  const text = String(query || '').trim().toLowerCase()
  const groups = new Map()
  for (const page of pages || []) {
    const hay = `${page.title} ${(page.tags || []).join(' ')} ${page.summary || ''}`.toLowerCase()
    if (text && !hay.includes(text)) continue
    const type = page.type || 'other'
    if (!groups.has(type)) groups.set(type, [])
    groups.get(type).push(page)
  }
  const rank = type => (TYPE_ORDER.indexOf(type) < 0 ? TYPE_ORDER.length : TYPE_ORDER.indexOf(type))
  return [...groups.entries()]
    .sort((a, b) => rank(a[0]) - rank(b[0]) || a[0].localeCompare(b[0]))
    .map(([type, list]) => ({ type, pages: list.sort((a, b) => String(a.title).localeCompare(String(b.title))) }))
}

/** The earliest created_at among the items; null when none has a readable one. */
function earliest(stamps) {
  let best = null
  for (const stamp of stamps) {
    const at = Date.parse(stamp || '')
    if (!Number.isNaN(at) && (best === null || at < best.at)) best = { at, stamp }
  }
  return best ? best.stamp : null
}

/**
 * What the tab bar says about each level: its name, kind, the changes still waiting (an undone one is not) and when
 * the oldest of them was made.
 */
export function tabSummary(metas, intents) {
  const out = {}
  for (const [key, meta] of Object.entries(metas || {})) {
    const waiting = activeIntents(intents, key, meta)
    out[key] = { label: meta.label || key, kind: meta.kind, waiting: waiting.length, oldest: earliest(waiting.map(item => item.created_at)) }
  }
  return out
}

/** The changes waiting for Claude Code across the levels this workbench shows. */
export function waitingCount(metas, intents) {
  return Object.values(tabSummary(metas, intents)).reduce((sum, item) => sum + item.waiting, 0)
}

/** When the oldest change still waiting for Claude Code was made, across the levels; null when none waits. */
export function oldestWaiting(metas, intents) {
  return earliest(Object.values(tabSummary(metas, intents)).map(item => item.oldest))
}

/** The project phase map in neuroflow's glyph legend: ◉ the current one, ● a phase with a folder, ○ one not started — each with its word. */
export function phaseMap(panel) {
  const order = Array.isArray(panel.recommended_phases) && panel.recommended_phases.length ? panel.recommended_phases : (panel.visited || [])
  const visited = new Set(panel.visited || [])
  return order.map(phase => ({
    phase,
    state: phase === panel.active_phase ? 'current' : visited.has(phase) ? 'visited' : 'not started',
    glyph: phase === panel.active_phase ? '◉' : visited.has(phase) ? '●' : '○',
  }))
}

/** Dated rows still ahead, with the days left from the viewer's own date. */
export function upcomingDates(panel, today) {
  const rows = Array.isArray(panel.dates) ? panel.dates : []
  const out = rows.map(row => ({ ...row, days: daysUntil(row.date, today) })).filter(row => row.days !== null && row.days >= 0)
  if (panel.ethics && panel.ethics.expires) {
    const days = daysUntil(panel.ethics.expires, today)
    if (days !== null && days >= 0 && !out.some(row => row.date === panel.ethics.expires)) out.push({ date: panel.ethics.expires, what: 'ethics approval expires', gates: null, days })
  }
  return out.sort((a, b) => a.days - b.days)
}
