// Finding the neuroflow project and loading its typed snapshot (a mirror of the .neuroflow/ files,
// never a source of truth). Every read is tolerant: a missing or odd file becomes a `problems`
// entry, never an exception, so a broken file can only make the mod show less.
import type { NfDeadline, NfEthics, NfLoop, NfMeeting, NfPrereg, NfScope, NfSnapshot } from '../../../types'
import { manifestVersion } from './config'
import { asList, asMap, asNumber, asString, parseLegacyConfig, parseYamlSubset, splitFrontmatter } from './frontmatter'
import type { Frontmatter } from './frontmatter'
import type { NfIo } from './io'
import { dirname, fold, isNetworkPath, join, toSlash } from './paths'

/** The newest project_config schema this mod understands (neuroflow-core → C1). */
export const KNOWN_SCHEMA = 1

const CONFIG = '.neuroflow/project_config.md'

const homeDir = async (io: NfIo): Promise<string | null> => {
  const home = await io.home()
  return home ? toSlash(home) : null
}

/** Walks up from `cwd` to the nearest folder holding .neuroflow/project_config.md (neuroflow-core → walk-up rule). */
export const findProjectRoot = async (io: NfIo, cwd: string): Promise<string | null> => {
  let dir = toSlash(cwd)
  for (let depth = 0; depth < 64; depth += 1) {
    if (await io.exists(join(dir, CONFIG))) return dir
    const parent = dirname(dir)
    if (parent === dir || parent === '.') return null
    dir = parent
  }
  return null
}

/** Decides whether the mod acts here: a project, not the home folder, not the plugin's own repo. */
export const computeScope = async (io: NfIo, cwd: string, isInteractive: boolean): Promise<NfScope> => {
  const isHeadless = !isInteractive
  if (isNetworkPath(cwd)) return { isActive: false, reason: 'network path', root: null, isHeadless }
  const root = await findProjectRoot(io, cwd)
  if (root === null) return { isActive: false, reason: 'no neuroflow project here', root: null, isHeadless }
  const home = await homeDir(io)
  if (home !== null && fold(root) === fold(home)) {
    return { isActive: false, reason: 'the home folder is not a project', root: null, isHeadless }
  }
  const manifest = await io.read(join(root, '.claude-plugin/plugin.json'))
  if (manifest !== null && /"name"\s*:\s*"neuroflow"/.test(manifest)) {
    return { isActive: false, reason: "the plugin's own repository", root, isHeadless }
  }
  return { isActive: true, reason: 'active', root, isHeadless }
}

const readStatusFile = async (io: NfIo, path: string, problems: string[]): Promise<Frontmatter | null> => {
  const text = await io.read(path)
  if (text === null) return null
  const { block } = splitFrontmatter(text)
  if (block === null) {
    problems.push(`${path.replace(/^.*\.neuroflow\//, '.neuroflow/')} has no frontmatter`)
    return null
  }
  return parseYamlSubset(block)
}

const daysBetween = (fromMs: number, isoDate: string): number => {
  const [y, m, d] = isoDate.split('-').map(Number)
  const target = new Date(y, m - 1, d).getTime()
  const from = new Date(fromMs)
  const today = new Date(from.getFullYear(), from.getMonth(), from.getDate()).getTime()
  return Math.round((target - today) / 86_400_000)
}

/** Rows of timeline.md: `| YYYY-MM-DD | what | phase it gates |`. Past entries are dropped. */
export const parseTimeline = (text: string, nowMs: number): NfDeadline[] => {
  const out: NfDeadline[] = []
  for (const line of text.split('\n')) {
    const cells = line.split('|').map(cell => cell.trim())
    if (cells.length < 3) continue
    const date = cells[1]
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) continue
    const daysLeft = daysBetween(nowMs, date)
    if (daysLeft < 0) continue
    out.push({ date, what: cells[2] || '(no description)', gates: cells[3] ? cells[3] : null, daysLeft })
  }
  return out.sort((a, b) => a.daysLeft - b.daysLeft)
}

/** Rows of an autoresearch pointer registry: `| Name | Location | Iterations | Best | Status |`. */
export const parseLoopRegistry = (text: string, phase: string): NfLoop[] => {
  const out: NfLoop[] = []
  for (const line of text.split(/\r?\n/)) {
    const cells = line.split('|').map(cell => cell.trim())
    if (cells.length < 7 || cells[1] === '' || /^name$/i.test(cells[1]) || /^-+$/.test(cells[1])) continue
    out.push({ phase, name: cells[1], location: cells[2], iterations: cells[3], best: cells[4], status: cells[5] })
  }
  return out
}

const TASK_COLUMNS = ['inbox', 'ready', 'active', 'review', 'meeting', 'done', 'archive']

/** A meeting file's facts (phase-meeting → file format), or null when it is not a dated meeting. */
export const parseMeeting = (text: string, slug: string, level: NfMeeting['level'], nowMs: number): NfMeeting | null => {
  const { block, body } = splitFrontmatter(text)
  if (block === null) return null
  const fm = parseYamlSubset(block)
  const date = asString(fm.date)
  const match = date === null ? null : /^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}))?/.exec(date)
  if (date === null || match === null) return null
  const [, y, mo, d, h, mi] = match
  const startMs = new Date(Number(y), Number(mo) - 1, Number(d), Number(h ?? 9), Number(mi ?? 0)).getTime()
  const closed = (asString(fm.closed) ?? '').trim() !== ''
  return {
    level,
    slug,
    title: asString(fm.title) ?? slug,
    date,
    startsIn: Math.round((startMs - nowMs) / 60_000),
    closed,
    openActions: body.split(/\r?\n/).filter(line => /^\s*-\s\[\s\]\s/.test(line)).length,
  }
}

export const loadSnapshot = async (io: NfIo, root: string): Promise<NfSnapshot> => {
  const problems: string[] = []
  const nowMs = await io.now()
  const configText = (await io.read(join(root, CONFIG))) ?? ''
  const { block, body } = splitFrontmatter(configText)
  const dialect = block === null ? 'legacy' : 'frontmatter'
  const config: Frontmatter = block === null ? parseLegacyConfig(body) : parseYamlSubset(block)
  if (block === null) problems.push('project_config.md uses a legacy format — /neuroflow:migrate converts it')

  const nfSchema = asNumber(config.nf_schema)
  if (nfSchema !== null && nfSchema > KNOWN_SCHEMA) {
    problems.push(`project_config.md has nf_schema ${nfSchema}; this plugin knows ${KNOWN_SCHEMA} — update neuroflow`)
  }

  const ethicsFm = await readStatusFile(io, join(root, '.neuroflow/ethics/status.md'), problems)
  const ethics: NfEthics | null = ethicsFm === null ? null : {
    status: asString(ethicsFm.status) ?? 'none',
    setBy: asString(ethicsFm.set_by),
    setAt: asString(ethicsFm.set_at),
    approvalId: asString(ethicsFm.approval_id),
    expires: asString(ethicsFm.expires),
    aiProcessing: asString(ethicsFm.ai_processing),
  }

  const preregFm = await readStatusFile(io, join(root, '.neuroflow/preregistration/status.md'), problems)
  const prereg: NfPrereg | null = preregFm === null ? null : {
    status: asString(preregFm.status) ?? 'draft',
    setBy: asString(preregFm.set_by),
    setAt: asString(preregFm.set_at),
    frozenAt: asString(preregFm.frozen_at),
    files: asMap(preregFm.files),
    plannedN: asNumber(preregFm.planned_n),
  }

  const timeline = await io.read(join(root, '.neuroflow/timeline.md'))
  const deadlines = timeline === null ? [] : parseTimeline(timeline, nowMs)
  if (ethics?.expires && /^\d{4}-\d{2}-\d{2}$/.test(ethics.expires)) {
    const daysLeft = daysBetween(nowMs, ethics.expires)
    if (daysLeft >= 0 && !deadlines.some(item => item.date === ethics.expires && /ethic/i.test(item.what))) {
      deadlines.push({ date: ethics.expires, what: 'ethics approval expires', gates: null, daysLeft })
      deadlines.sort((a, b) => a.daysLeft - b.daysLeft)
    }
  }

  const nfDir = join(root, '.neuroflow')
  const entries = await io.list(nfDir)
  const phasesVisited = entries.filter(entry => entry.isDir).map(entry => entry.name)
  let taskCounts: Record<string, number> | null = null
  if (phasesVisited.includes('tasks')) {
    taskCounts = {}
    for (const column of TASK_COLUMNS) {
      const files = await io.list(join(nfDir, 'tasks', column))
      taskCounts[column] = files.filter(file => !file.isDir && file.name.endsWith('.md')).length
    }
  }
  const loops: NfLoop[] = []
  for (const phase of phasesVisited) {
    const registry = await io.read(join(nfDir, phase, 'autoresearch-loops.md'))
    if (registry !== null) loops.push(...parseLoopRegistry(registry, phase))
  }
  const meetings: NfMeeting[] = []
  const home = await io.home()
  const meetingDirs: [string, NfMeeting['level']][] = [[join(nfDir, 'meetings'), 'project']]
  if (home) meetingDirs.push([join(toSlash(home), '.neuroflow/flowie/meetings'), 'flowie'])
  for (const [dir, level] of meetingDirs) {
    for (const entry of await io.list(dir)) {
      if (entry.isDir || !entry.name.endsWith('.md')) continue
      const text = await io.read(join(dir, entry.name))
      const meeting = text === null ? null : parseMeeting(text, entry.name.replace(/\.md$/, ''), level, nowMs)
      if (meeting !== null && meeting.startsIn > -2 * 24 * 60 && meeting.startsIn < 2 * 24 * 60) meetings.push(meeting)
    }
  }
  meetings.sort((a, b) => a.startsIn - b.startsIn)
  let wikiPending = 0
  for (const entry of await io.list(join(nfDir, 'wiki/.pending'))) {
    if (entry.isDir || !entry.name.endsWith('.md')) continue
    const card = await io.read(join(nfDir, 'wiki/.pending', entry.name))
    if (card !== null && !/^status:\s*(accepted|skipped)\b/m.test(card)) wikiPending += 1
  }
  let wellbeingDue = false
  if (home) {
    const wellbeing = join(toSlash(home), '.neuroflow/flowie/wellbeing')
    const config = await io.read(join(wellbeing, 'config.json'))
    if (config !== null && /"collect"\s*:\s*true/.test(config)) {
      const d = new Date(nowMs)
      const today = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
      wellbeingDue = !(await io.exists(join(wellbeing, `${today}.json`)))
    }
  }

  return {
    root,
    nfSchema,
    dialect,
    pluginVersion: asString(config.plugin_version),
    runningVersion: manifestVersion(await io.read(join(io.pluginRoot, '.claude-plugin/plugin.json'))),
    projectName: asString(config.project_name) ?? asString(config.project),
    phase: asString(config.active_phase) ?? asString(config.phase),
    mode: asString(config.default_mode),
    recommendedPhases: asList(config.recommended_phases),
    rawRoots: asList(config.raw_roots),
    paperAuto: config.paper_auto === true || config.paper_auto === 'on',
    ethics,
    prereg,
    deadlines,
    phasesVisited,
    taskCounts,
    loops,
    meetings,
    wellbeingDue,
    ethicsNotApplicable: asString(config.ethics) === 'not-applicable',
    flowieProfiles: asList(config.flowie_profiles),
    wikiCapture: asString(config.wiki_capture),
    wikiPending,
    problems,
    loadedAt: nowMs,
  }
}

/** A frozen/approved marker counts only when a person set it (neuroflow-core → C2). */
export const isPersonSet = (file: { setBy: string | null } | null): boolean => file?.setBy === 'person'

/** Dotted versions compared number by number ("0.2.10" is newer than "0.2.9"): below, at or above zero. */
export const compareVersions = (a: string, b: string): number => {
  const x = a.split(/[.+-]/).map(part => Number.parseInt(part, 10) || 0)
  const y = b.split(/[.+-]/).map(part => Number.parseInt(part, 10) || 0)
  for (let i = 0; i < Math.max(x.length, y.length); i += 1) {
    const diff = (x[i] ?? 0) - (y[i] ?? 0)
    if (diff !== 0) return diff
  }
  return 0
}

/**
 * The version notice (neuroflow-core → Command lifecycle), in the prose's own words: the running neuroflow is newer
 * than the version the project was last brought up to date to (`plugin_version`, which only the scaffold and
 * /neuroflow:migrate write), or the file names none. Null when there is nothing to say (or the running version is unknown).
 */
export const versionNotice = (snap: Pick<NfSnapshot, 'pluginVersion' | 'runningVersion'>): string | null => {
  const running = snap.runningVersion
  if (typeof running !== 'string' || running === '') return null
  const recorded = typeof snap.pluginVersion === 'string' && snap.pluginVersion !== '' ? snap.pluginVersion : null
  if (recorded !== null && compareVersions(recorded, running) >= 0) return null
  return `neuroflow ${running} is installed; this project is on ${recorded ?? 'an older version'} — run /neuroflow:migrate to bring the project, your flowie and the team hive up to date`
}
