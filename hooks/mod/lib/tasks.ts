// The task boards, read exactly as commands/tasks.md defines them: one file per task at
// tasks/{column}/{slug}.md, the folder is the column, columns from tasks/config.json or the defaults.
// Three levels share the format (commands/tasks.md → Levels): the project's .neuroflow/tasks/, the
// person's flowie and every hive clone. The mod only reads them, from the local clones as they are:
// it never pulls, writes or moves a task file.
import type { NfBoard, NfCard, NfTaskLevel, NfTaskView } from '../../../types'
import { asList, asString, parseYamlSubset, splitFrontmatter } from './frontmatter'
import type { NfIo } from './io'
import { dirname, isWindowsPath, join, resolveFrom, toSlash } from './paths'

export type Column = { id: string; label: string; archive: boolean }

export const DEFAULT_COLUMNS: readonly Column[] = ['inbox', 'ready', 'active', 'review', 'meeting', 'done', 'archive'].map(id => ({
  id,
  label: id,
  archive: id === 'archive',
}))

/** Columns from tasks/config.json (`columns[].id`, `label`, `archive`), else the defaults. */
export const columnsFromConfig = (configJson: string | null): readonly Column[] => {
  if (configJson === null) return DEFAULT_COLUMNS
  try {
    const parsed = JSON.parse(configJson) as { columns?: { id?: unknown; label?: unknown; archive?: unknown }[] }
    const columns = (parsed.columns ?? [])
      .filter(column => typeof column.id === 'string' && column.id !== '')
      .map(column => ({ id: String(column.id), label: typeof column.label === 'string' ? column.label : String(column.id), archive: column.archive === true }))
    return columns.length > 0 ? columns : DEFAULT_COLUMNS
  } catch {
    return DEFAULT_COLUMNS
  }
}

/** Done and archive columns are counted, never drawn or read card by card. */
const isClosed = (column: Column): boolean => column.id === 'done' || column.archive

/** One task file as a card; `today` is YYYY-MM-DD. Legacy keys (assignee, responsible) read as owner. */
export const parseTask = (text: string, slug: string, today: string, isDone: boolean): NfCard => {
  const { block } = splitFrontmatter(text)
  const fm = block === null ? {} : parseYamlSubset(block)
  const due = asString(fm.due)
  const owner = asString(fm.owner) ?? asString(fm.assignee) ?? asString(fm.responsible) ?? asList(fm.owner)[0] ?? null
  return {
    slug,
    title: asString(fm.title) ?? slug,
    owner,
    due: due !== null && /^\d{4}-\d{2}-\d{2}$/.test(due) ? due : null,
    overdue: !isDone && due !== null && /^\d{4}-\d{2}-\d{2}$/.test(due) && due < today,
    project: asString(fm.project)?.trim() || null,
    isMine: false,
  }
}

/** This project's cards first, then overdue ones, then by due date (undated last). */
export const byPriority = (a: NfCard, b: NfCard): number =>
  Number(b.isMine) - Number(a.isMine) || Number(b.overdue) - Number(a.overdue) || (a.due ?? '9999').localeCompare(b.due ?? '9999')

/** The board as the Rendering rules say: board order, this project's and overdue cards first, done/archive counted not drawn. */
export const buildBoard = (columns: readonly Column[], cards: Readonly<Record<string, NfCard[]>>): NfBoard => {
  const drawn = columns.filter(column => !isClosed(column))
  const done = (cards.done ?? []).length
  const archived = columns.filter(column => column.archive).reduce((sum, column) => sum + (cards[column.id] ?? []).length, 0)
  return {
    columns: drawn
      .map(column => {
        const list = [...(cards[column.id] ?? [])].sort(byPriority)
        return { id: column.id, label: column.label, cards: list.slice(0, 5), total: list.length }
      })
      .filter(column => column.total > 0 || column.id === 'inbox' || column.id === 'active'),
    done,
    archived,
  }
}

/** A card as one text line: `⚠ rerun-ica @li due 08-20`. */
export const cardLine = (card: NfCard): string =>
  `${card.overdue ? '⚠ ' : ''}${card.title}${card.owner ? ` @${card.owner}` : ''}${card.due ? ` due ${card.due.slice(5)}` : ''}`

/** The mark of this project's cards on flowie and hive boards (the prose's rendering rules use the same). */
export const MINE = '◆'

/** A card as the board and the dashboard draw it at its level: this project's cards marked on flowie and hive boards. */
export const levelCardLine = (card: NfCard, kind: NfTaskLevel['kind']): string => `${card.isMine && kind !== 'project' ? `${MINE} ` : ''}${cardLine(card)}`

// ── levels ────────────────────────────────────────────────────────────────────────────────────

export type LevelRef = { id: string; kind: NfTaskLevel['kind']; name: string; dir: string }

const unquote = (raw: string): string => raw.trim().replace(/^(["'])(.*)\1$/, '$2')

/** The hive folder an entry of user.yaml's `hives:` names: `org/repo` → `org-repo`; with `local:`, its last folder. */
export const hiveFolderOf = (entry: { repo: string | null; local: string | null }): string | null => {
  if (entry.local) {
    const parts = toSlash(entry.local.trim()).split('/').filter(Boolean)
    return parts[parts.length - 1] ?? null
  }
  if (!entry.repo) return null
  const path = entry.repo
    .trim()
    .replace(/^[a-z][a-z0-9+.-]*:\/\/[^/]+\//i, '')
    .replace(/^[\w.-]+@[\w.-]+:/, '')
    .replace(/\.git$/i, '')
  const parts = path.split('/').filter(Boolean)
  if (parts.length === 0) return null
  return parts.length === 1 ? parts[0] : `${parts[parts.length - 2]}-${parts[parts.length - 1]}`
}

/** The hives `hives:` lists in ~/.neuroflow/user.yaml (neuroflow-core → Personal layer), as folder names in its order. */
export const userHives = (userYaml: string | null): string[] => {
  if (userYaml === null) return []
  const lines = userYaml.replace(/\r\n/g, '\n').split('\n')
  const at = lines.findIndex(line => /^hives\s*:/.test(line))
  if (at < 0) return []
  const entries: { repo: string | null; local: string | null }[] = []
  const rest = lines[at].replace(/^hives\s*:/, '').replace(/\s+#.*$/, '').trim()
  if (rest !== '') {
    for (const part of rest.replace(/^\[/, '').replace(/\]$/, '').split(',')) {
      const value = unquote(part)
      if (value !== '') entries.push({ repo: value, local: null })
    }
  } else {
    let current: { repo: string | null; local: string | null } | null = null
    for (const line of lines.slice(at + 1)) {
      if (line.trim() === '' || line.trim().startsWith('#')) continue
      if (!/^\s/.test(line) && !line.startsWith('-')) break
      const item = /^\s*-\s*(.*)$/.exec(line)
      const body = (item === null ? line : item[1]).replace(/\s+#.*$/, '').trim()
      if (item !== null) {
        current = { repo: null, local: null }
        entries.push(current)
      }
      if (current === null) continue
      const pair = /^(repo|local)\s*:\s*(.*)$/.exec(body)
      if (pair === null) {
        // A bare entry is the `org/repo` string; another key of a map entry is not the contract's, and is skipped.
        if (item !== null && body !== '' && !/^[\w-]+\s*:(?!\/\/)/.test(body)) current.repo = unquote(body)
      } else if (pair[1] === 'local') current.local = unquote(pair[2]) || null
      else current.repo = unquote(pair[2]) || null
    }
  }
  return entries.map(hiveFolderOf).filter((name): name is string => name !== null)
}

/** Hive folders in board order: the ones user.yaml lists first, in its order, then the others alphabetically. */
export const orderHives = (folders: readonly string[], listed: readonly string[]): string[] => {
  const first: string[] = []
  for (const name of listed) {
    const folder = folders.find(item => item.toLowerCase() === name.toLowerCase())
    if (folder !== undefined && !first.includes(folder)) first.push(folder)
  }
  const others = folders.filter(folder => !first.includes(folder)).sort((a, b) => (a.toLowerCase() < b.toLowerCase() ? -1 : a.toLowerCase() > b.toLowerCase() ? 1 : 0))
  return [...first, ...others]
}

/** The levels to read, in board order: project, flowie (with a tasks/ folder), every hive clone with tasks/. */
export const taskLevels = async (io: NfIo, root: string, home: string | null): Promise<LevelRef[]> => {
  const refs: LevelRef[] = [{ id: 'project', kind: 'project', name: 'project', dir: join(root, '.neuroflow') }]
  if (home === null) return refs
  const base = join(toSlash(home), '.neuroflow')
  if (await io.exists(join(base, 'flowie/tasks'))) refs.push({ id: 'flowie', kind: 'flowie', name: 'flowie', dir: join(base, 'flowie') })
  // Any entry with a tasks/ folder: a clone may be a symbolic link, which $.fs.list does not call a folder.
  const folders: string[] = []
  for (const entry of await io.list(join(base, 'hives'))) {
    if (await io.exists(join(base, 'hives', entry.name, 'tasks'))) folders.push(entry.name)
  }
  for (const name of orderHives(folders, userHives(await io.read(join(base, 'user.yaml'))))) {
    refs.push({ id: `hive:${name}`, kind: 'hive', name, dir: join(base, 'hives', name) })
  }
  return refs
}

/**
 * The column of a legacy flat task file (`tasks/{id}-{slug}.md`): the one its `status` names — `archived` is the
 * archive column, `done` the done column, whatever a board's config calls them. A closed status never lands in an
 * open column: on a board with no closed column for it, null (counted as done, not drawn). Any other status the
 * board lacks reads as its first open column.
 */
export const legacyColumn = (status: string | null, columns: readonly Column[]): Column | null => {
  const id = (status ?? '').trim().toLowerCase()
  const named = columns.find(column => column.id.toLowerCase() === id)
  if (named !== undefined) return named
  const archive = columns.find(column => column.archive)
  const done = columns.find(column => column.id === 'done')
  if (id === 'archived' || id === 'archive') return archive ?? done ?? null
  if (id === 'done') return done ?? archive ?? null
  return columns.find(column => !isClosed(column)) ?? columns[0] ?? null
}

/**
 * Reads one level's board: open cards parsed, done and archive counted (their files are not read). `linked` is
 * this project's name at the level (its tasks' `project:`), null at project level or without a link.
 */
export const loadLevel = async (io: NfIo, ref: LevelRef, today: string, linked: string | null): Promise<NfTaskLevel> => {
  const dir = join(ref.dir, 'tasks')
  const columns = columnsFromConfig(await io.read(join(dir, 'config.json')))
  const cards: Record<string, NfCard[]> = Object.fromEntries(columns.map(column => [column.id, [] as NfCard[]]))
  const counted = (slug: string): NfCard => ({ slug, title: slug, owner: null, due: null, overdue: false, project: null, isMine: false })
  const read = (text: string, slug: string): NfCard => {
    const card = parseTask(text, slug, today, false)
    return { ...card, isMine: ref.kind === 'project' || (linked !== null && card.project === linked) }
  }
  for (const column of columns) {
    for (const entry of await io.list(join(dir, column.id))) {
      if (entry.isDir || !entry.name.endsWith('.md')) continue
      const slug = entry.name.replace(/\.md$/, '')
      if (isClosed(column)) {
        cards[column.id].push(counted(slug))
        continue
      }
      const text = await io.read(join(dir, column.id, entry.name))
      if (text !== null) cards[column.id].push(read(text, slug))
    }
  }
  // Legacy files flat in tasks/ stay readable (commands/tasks.md → Legacy files): a .md with frontmatter.
  for (const entry of await io.list(dir)) {
    if (entry.isDir || !entry.name.endsWith('.md')) continue
    const text = await io.read(join(dir, entry.name))
    const block = text === null ? null : splitFrontmatter(text).block
    if (text === null || block === null) continue
    const column = legacyColumn(asString(parseYamlSubset(block).status), columns)
    const slug = entry.name.replace(/\.md$/, '')
    if (column === null) cards.done = [...(cards.done ?? []), counted(slug)]
    else cards[column.id].push(isClosed(column) ? counted(slug) : read(text, slug))
  }
  const open = columns.filter(column => !isClosed(column)).flatMap(column => cards[column.id])
  return {
    id: ref.id,
    kind: ref.kind,
    name: ref.name,
    project: ref.kind === 'project' ? null : linked,
    open: open.length,
    mine: open.filter(card => card.isMine).length,
    board: buildBoard(columns, cards),
    top: [...open].sort(byPriority).slice(0, 5),
  }
}

// ── this project ──────────────────────────────────────────────────────────────────────────────

/**
 * The spelling two names of one repository share: a URL without its scheme or user (`git@host:org/repo` as
 * `host/org/repo`), lower case; a path with `~` expanded and forward slashes, lower case on Windows; no
 * trailing `.git` or slash. Equal keys, same repository — nothing fuzzier.
 */
export const locationKey = (value: string, home: string | null): string => {
  let text = value.trim()
  const scheme = /^[a-z][a-z0-9+.-]*:\/\//i.exec(text)
  if (scheme !== null) text = text.slice(scheme[0].length).replace(/^[^@/]*@/, '')
  else if (/^[\w.-]+@[\w.-]+:(?![\\/])/.test(text)) text = text.replace(/^[\w.-]+@/, '').replace(':', '/')
  else {
    if (home && /^~(?=[\\/]|$)/.test(text)) text = `${toSlash(home)}${text.slice(1)}`
    const path = toSlash(text).replace(/\/+$/, '').replace(/\.git$/i, '').replace(/\/+$/, '')
    return isWindowsPath(text) ? path.toLowerCase() : path
  }
  return toSlash(text).replace(/\/+$/, '').replace(/\.git$/i, '').replace(/\/+$/, '').toLowerCase()
}

/** The `url` of `[remote "origin"]` in a git config file, or null. */
export const originUrl = (gitConfig: string): string | null => {
  let inOrigin = false
  for (const raw of gitConfig.split(/\r?\n/)) {
    const line = raw.trim()
    if (line.startsWith('[')) {
      inOrigin = /^\[remote\s+"origin"\]$/i.test(line)
      continue
    }
    const url = inOrigin ? /^url\s*=\s*(.+)$/i.exec(line) : null
    if (url !== null) return url[1].trim()
  }
  return null
}

/** The git config of the repository holding `root` (a worktree's `.git` file followed to its common folder), or null. */
const gitConfigOf = async (io: NfIo, root: string): Promise<string | null> => {
  let dir = toSlash(root)
  for (let depth = 0; depth < 32; depth += 1) {
    const dotGit = (await io.read(join(dir, '.git')))?.trim() ?? ''
    if (/^gitdir:/i.test(dotGit)) {
      const gitdir = resolveFrom(dir, dotGit.replace(/^gitdir:\s*/i, ''))
      const common = (await io.read(join(gitdir, 'commondir')))?.trim()
      return (common ? await io.read(join(resolveFrom(gitdir, common), 'config')) : null) ?? (await io.read(join(gitdir, 'config')))
    }
    const config = await io.read(join(dir, '.git/config'))
    if (config !== null) return config
    const parent = dirname(dir)
    if (parent === dir || parent === '.') return null
    dir = parent
  }
  return null
}

const parsed = (text: string | null): unknown => {
  try {
    return text === null ? null : JSON.parse(text)
  } catch {
    return null
  }
}

/** `{ projects: [...] }` or a bare list, as both registries are written. */
const entriesOf = (value: unknown): Record<string, unknown>[] => {
  const list = Array.isArray(value) ? value : value !== null && typeof value === 'object' ? (value as { projects?: unknown }).projects : null
  return Array.isArray(list) ? list.filter((item): item is Record<string, unknown> => item !== null && typeof item === 'object') : []
}

/** This folder as the registries can list it: its path and its origin remote URL, as location keys. */
export const projectKeys = async (io: NfIo, root: string, home: string): Promise<Set<string>> => {
  const config = await gitConfigOf(io, root)
  const remote = config === null ? null : originUrl(config)
  return new Set([locationKey(root, home), ...(remote === null ? [] : [locationKey(remote, home)])])
}

/** The id (else the name) of the projects/projects.json entry whose `repos` (strings or `{ url }`) hold one of `keys`. */
export const registryProject = (registryJson: string | null, keys: ReadonlySet<string>, home: string): string | null => {
  for (const project of entriesOf(parsed(registryJson))) {
    const name = typeof project.id === 'string' && project.id.trim() !== '' ? project.id.trim() : typeof project.name === 'string' ? project.name.trim() : ''
    if (name === '') continue
    for (const repo of Array.isArray(project.repos) ? project.repos : []) {
      const value = typeof repo === 'string' ? repo : repo !== null && typeof repo === 'object' && typeof (repo as { url?: unknown }).url === 'string' ? (repo as { url: string }).url : ''
      if (value.trim() !== '' && keys.has(locationKey(value, home))) return name
    }
  }
  return null
}

/**
 * This project at flowie level (commands/tasks.md → Levels): the flowie project this folder is linked to — the
 * `name` of its entry in ~/.neuroflow/local-projects.json, else the flowie's projects/projects.json entry that lists
 * this folder or its origin remote URL. Null when neither matches — no name guessing.
 */
export const linkedProject = async (io: NfIo, root: string, home: string, keys?: ReadonlySet<string>): Promise<string | null> => {
  const here = locationKey(root, home)
  for (const entry of entriesOf(parsed(await io.read(join(toSlash(home), '.neuroflow/local-projects.json'))))) {
    if (typeof entry.path === 'string' && typeof entry.name === 'string' && entry.name.trim() !== '' && locationKey(entry.path, home) === here) return entry.name.trim()
  }
  const registry = await io.read(join(toSlash(home), '.neuroflow/flowie/projects/projects.json'))
  return registry === null ? null : registryProject(registry, keys ?? (await projectKeys(io, root, home)), home)
}

/**
 * This project at a hive's level: the lab project of that hive's own projects/projects.json that lists this folder
 * or its origin remote URL — a hive task's `project:` names the lab project (phase-hive → --tasks). Null without one.
 */
export const hiveProject = async (io: NfIo, hiveDir: string, keys: ReadonlySet<string>, home: string): Promise<string | null> =>
  registryProject(await io.read(join(hiveDir, 'projects/projects.json')), keys, home)

/** Every level's board for the views, read from the local files (never pulled), each with this project's name there. */
export const loadTaskView = async (io: NfIo, root: string, home: string | null, today: string): Promise<NfTaskView> => {
  const refs = await taskLevels(io, root, home)
  const keys = home === null || refs.every(ref => ref.kind === 'project') ? null : await projectKeys(io, root, home)
  const levels: NfTaskLevel[] = []
  for (const ref of refs) {
    const linked =
      home === null || keys === null || ref.kind === 'project'
        ? null
        : ref.kind === 'flowie'
          ? await linkedProject(io, root, home, keys)
          : await hiveProject(io, ref.dir, keys, home)
    levels.push(await loadLevel(io, ref, today, linked))
  }
  return { levels }
}

// ── what the views say ────────────────────────────────────────────────────────────────────────

/** `project 0 · flowie 28 (5 Oddball) · example-lab-hive 8`: open tasks per level, this project's share in brackets. */
export const levelSummary = (view: NfTaskView): string =>
  view.levels
    .map(level => `${level.name} ${level.open}${level.kind !== 'project' && level.project !== null && level.mine > 0 ? ` (${level.mine} ${level.project})` : ''}`)
    .join(' · ')

/** The first open cards across levels: this project's first, overdue first, then by due date; level order breaks ties. */
export const topCards = (view: NfTaskView, max = 5): { level: NfTaskLevel; card: NfCard }[] =>
  view.levels
    .flatMap(level => level.top.map(card => ({ level, card })))
    .sort((a, b) => byPriority(a.card, b.card))
    .slice(0, max)

/**
 * The level the board pane opens on: the project's when it has open tasks, else the first level with open tasks
 * of this project, else the first with any open tasks, else the project's.
 */
export const openingLevel = (view: NfTaskView): string =>
  (view.levels.find(level => level.kind === 'project' && level.open > 0) ??
    view.levels.find(level => level.kind !== 'project' && level.mine > 0) ??
    view.levels.find(level => level.open > 0) ??
    view.levels[0])?.id ?? 'project'

/** The /tasks options that select a level, as commands/tasks.md spells them (nothing for the project level). */
export const levelArgs = (level: Pick<NfTaskLevel, 'kind' | 'name'>): string =>
  level.kind === 'project' ? '' : level.kind === 'flowie' ? ' --level flowie' : ` --level hive --hive ${level.name}`

/** The command a move on the board puts in the prompt: /tasks moves the file and records it. */
export const moveCommand = (level: Pick<NfTaskLevel, 'kind' | 'name'>, slug: string, column: string): string =>
  `/neuroflow:tasks${levelArgs(level)} --move ${slug} ${column}`
