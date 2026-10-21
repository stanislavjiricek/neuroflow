// User ideas — the living paper and the paper X-ray, drawn and decided by code.
//  - U1 living paper: `/neuroflow:paper --auto status` is answered in code (the status line commands/paper.md
//    specifies) and opens a pane with the reporting gaps, the Results slots still without a final result,
//    and how many allow-listed sources changed since the last sync; Enter on sync now, after a yes, runs
//    `/neuroflow:paper --auto sync`. The mod never writes the skeleton: sync stays a model turn, the person's.
//  - U3 X-ray: `/neuroflow:paper --xray view` opens the newest X-ray as a pane; a finding is accepted (its box
//    ticked) or rejected with a reason, each with Enter and the person's answer, in both X-ray files; `j` and `k`
//    step through the open findings, red first. `--xray check <file>` runs the two deterministic checks
//    (statcheck.py, cite_check.py) and reports them with no model turn.
//  - U2 auto wiki: after a command turn that logged a new decision, one model call judges whether it is
//    reusable knowledge (the wiki-protocol skill's rubric: nothing is the normal answer, evidence mandatory, never
//    results); at most two cards go to .neuroflow/wiki/.pending/, never one whose title is already in the wiki or
//    anywhere in the queue (a skipped card is never raised again). Only with `wiki_auto: ask` in the person's
//    user.yaml, a project that does not forbid it, and runtime on. `/neuroflow:wiki --review` opens the cards
//    as a pane: accept runs the normal `/neuroflow:wiki --add --from-pending`; skip marks the card skipped for good.
// Each pane opens holding the keys, on the one key map of lib/keys.ts; keys typed through that open are dropped.
// Since a pane holds the keys while the person may be typing for the prompt, no letter there writes or starts a model
// turn: accept, skip, reject and sync are Enter on their buttons (Tab reaches them), never right after another key
// (actOn), and each asks first, the safe answer on top (confirm). They
// share the views' look (skills/neuroflow-develop → Visual style): the ring mark and the pane's name, rules on the
// terminal, UPPERCASE dim labels, a quiet legend; an X-ray's red finding reads ✖, an orange one !.
// The figure check (U4) is prose only: a viewer cannot show figures or take pointer input on most terminals.
import { atom, read, update } from 'claude-code'
import type { EngineInterface, On } from 'claude-code'

import type { NfPaperView, NfWikiCard, NfXrayView } from '../../../types'
import type { NfIo } from '../lib/io'
import { NAV, isPastTypeThrough, paneRows, unfocusedHint } from '../lib/keys'
import { MARK, fit, isCompact, measuredRows, paneColumns, rememberViewport, rule, widthClass } from '../lib/layout'
import { isoDate } from '../lib/memory'
import { mayWrite } from '../lib/options'
import type { NfOptions } from '../lib/options'
import { join, relativeTo, resolveFrom, toSlash } from '../lib/paths'
import {
  autoStatusLine,
  decideInJsonl,
  decideInMarkdown,
  newestXray,
  openSlots,
  parseGaps,
  parseLedger,
  parseXray,
  skeletonDate,
} from '../lib/paper'
import type { XrayFinding } from '../lib/paper'
import { parseJson, runScript } from '../lib/scripts'
import { PENDING_DIR, WIKI_JUDGE_SYSTEM, captureAllowed, cardText, parseCard, parseJudge, setCardStatus, slugify, takenTitles } from '../lib/wikiqueue'
import type { WikiCard } from '../lib/wikiqueue'
import { paperOutputPath } from './checks'

const scopeAtom = atom({ plugin: 'neuroflow', key: 'scope' } as const, null)
const snapshotAtom = atom({ plugin: 'neuroflow', key: 'snapshot' } as const, null)
const paperViewAtom = atom({ plugin: 'neuroflow', key: 'paperView' } as const, null)
const xrayViewAtom = atom({ plugin: 'neuroflow', key: 'xrayView' } as const, null)
const xrayPickAtom = atom({ plugin: 'neuroflow', key: 'xrayPick' } as const, null)
const wikiCardsAtom = atom({ plugin: 'neuroflow', key: 'wikiCards' } as const, [])
const wikiPickAtom = atom({ plugin: 'neuroflow', key: 'wikiPick' } as const, null)
const wikiIndexAtom = atom({ plugin: 'neuroflow', key: 'wikiIndex' } as const, [])
const activeCommandAtom = atom({ plugin: 'neuroflow', key: 'activeCommand' } as const, null)
const baselineAtom = atom({ plugin: 'neuroflow', key: 'reasoningBaseline' } as const, null)
const openedAtAtom = atom({ plugin: 'neuroflow', key: 'openedAt' } as const, {})
const keyAtAtom = atom({ plugin: 'neuroflow', key: 'keyAt' } as const, {})

const PAPER_PANE = 'nf-paper'
const XRAY_PANE = 'nf-xray'
const WIKI_PANE = 'nf-wiki'
const PAPER_DIR = '.neuroflow/paper'
/** The column the panes' UPPERCASE labels (EVIDENCE, CHANGED, FIX) stand in. */
const LABEL = 10

/** The allow-listed source folders a sync reads (phase-paper → Living paper skeleton), for the staleness count. */
export const SKELETON_SOURCES = [
  'ideation', 'preregistration', 'ethics', 'experiment', 'tool-build', 'tool-validate', 'data', 'data-preprocess',
  'data-analyze', 'brain-build', 'brain-optimize', 'brain-run', 'reasoning',
]

/** The question before the living paper syncs: a model turn that rewrites the skeleton files, unless it is frozen. */
export const syncQuestion = (frozen: boolean): string =>
  frozen
    ? 'Sync the living paper now? It is frozen (a submission or revision exists): a model turn reports what changed and rewrites nothing.'
    : 'Sync the living paper now? A model turn rewrites skeleton.md, paper-ledger.md and gaps.md from their sources.'

/**
 * The toast when the judge queued wiki cards: the ways in that work whatever the `band` setting — the command, and the
 * dashboard's now tab, which lists every band item. Not the band's `w`: a quiet band (the default) never shows the cards,
 * and a normal one offers `w` only while they are its first item.
 */
export const wikiCardsToast = (count: number): string =>
  `neuroflow: ${count} wiki card${count === 1 ? '' : 's'} to review — /neuroflow:wiki --review, or the dashboard's now tab`

/** A red finding is a countable defect (✖, as a failed check reads), an orange one a judgement to look at (!). */
const SEVERITY_GLYPH: Record<string, string> = { red: '✖', orange: '!' }

/** One line per finding, as the pane and its text form show it. */
export const findingLabel = (item: XrayFinding): string =>
  `${SEVERITY_GLYPH[item.severity] ?? '·'} ${item.id} ${item.severity}${item.area ? ` · Area ${item.area}` : ''} · ${item.finding}`

/** Counts for the X-ray header: red and orange still open, and decided ones. */
export const xrayCounts = (findings: readonly XrayFinding[]): { red: number; orange: number; open: number; decided: number } => ({
  red: findings.filter(item => item.severity === 'red' && item.status === 'open').length,
  orange: findings.filter(item => item.severity === 'orange' && item.status === 'open').length,
  open: findings.filter(item => item.status === 'open').length,
  decided: findings.filter(item => item.status !== 'open').length,
})

/** Open findings the X-ray pane lists at a time, as rows the ring and j/k walk (no Select: no option limit, #255). */
export const XRAY_PAGE = 8

/** The open findings in the pane's order: red before orange, file order within each. */
const xrayOrder = (open: readonly XrayFinding[]): XrayFinding[] => {
  const rank = (item: XrayFinding) => (item.severity === 'red' ? 0 : 1)
  return open.map((item, at) => ({ item, at })).sort((a, b) => rank(a.item) - rank(b.item) || a.at - b.at).map(entry => entry.item)
}

/**
 * The page of open findings the pane lists: red before orange (file order within each), `size` at a time, the page
 * that holds the picked finding (else the first). `previous`/`next` are the findings that open the neighbouring
 * pages; `from`/`to` are 1-based for the header.
 */
export const xrayPage = (open: readonly XrayFinding[], pickId: string | null, size: number) => {
  const ordered = xrayOrder(open)
  const at = Math.max(0, ordered.findIndex(item => item.id === pickId))
  const start = Math.floor(at / size) * size
  const shown = ordered.slice(start, start + size)
  return {
    first: ordered[0] ?? null,
    shown,
    from: shown.length === 0 ? 0 : start + 1,
    to: start + shown.length,
    total: ordered.length,
    previous: start > 0 ? (ordered[start - size] ?? null) : null,
    next: start + size < ordered.length ? (ordered[start + size] ?? null) : null,
  }
}

/** j (`1`) and k (`-1`) in the X-ray: the open finding after or before the picked one, across pages; stays at the ends. */
export const xrayStep = (open: readonly XrayFinding[], pickId: string | null, step: 1 | -1): XrayFinding | null => {
  const ordered = xrayOrder(open)
  const at = ordered.findIndex(item => item.id === pickId)
  if (at < 0) return ordered[0] ?? null
  return ordered[Math.min(ordered.length - 1, Math.max(0, at + step))] ?? null
}

// ── engine side ────────────────────────────────────────────────────────────────────────────────

const ioOf = ($: EngineInterface): NfIo => ({
  read: path => $.fs.read(path).then(text => (typeof text === 'string' ? text : null), () => null),
  exists: path => $.fs.exists(path).catch(() => false),
  list: path => $.fs.list(path).then(entries => entries.map(entry => ({ name: entry.name, isDir: entry.kind === 'dir' || String(entry.kind) === 'directory' })), () => []),
  write: (path, text) => $.fs.write(path, text),
  home: async () => (await $.env.get('HOME')) ?? (await $.env.get('USERPROFILE')),
  now: () => $.clock.now(),
  run: (argv, init) => $.process.run(argv, init),
  pluginRoot: $.plugin.root,
})

const isPersonThere = async ($: EngineInterface): Promise<boolean> => (await $.session.surfaces()).length > 0

/** A pane opens asking for the keys: keys typed within TYPE_THROUGH_MS of it are taken as typed through. */
const markOpened = async ($: EngineInterface, id: string): Promise<void> => {
  const now = await $.clock.now()
  await update($, openedAtAtom, opened => ({ ...opened, [id]: now }))
}

/** Notes a key of a pane: an Enter on an action right after it is dropped (actOn). */
const noteKey = async ($: EngineInterface, id: string): Promise<void> => {
  const now = await $.clock.now()
  await update($, keyAtAtom, keys => ({ ...keys, [id]: now }))
}

/** A press handler for one of a pane's keys (j, k, r, q), dropped while typed through a focused open (lib/keys.ts). */
const act =
  ($: EngineInterface, id: string, run: () => unknown) =>
  async (): Promise<void> => {
    const now = await $.clock.now()
    const opened = (await read($, openedAtAtom))[id]
    await noteKey($, id)
    if (!isPastTypeThrough(now, opened)) return
    await run()
  }

/**
 * A press handler for an action — accept, skip, reject, sync now, a finding's row — which has no letter: Enter on it
 * with the ring there, or a click. Dropped while typed through the open and within TYPE_THROUGH_MS of the pane's
 * last key, so an Enter that ends a sentence typed for the prompt never presses it; what writes or starts a model
 * turn asks first besides (confirm).
 */
const actOn =
  ($: EngineInterface, id: string, run: () => unknown) =>
  async (): Promise<void> => {
    const now = await $.clock.now()
    const opened = (await read($, openedAtAtom))[id]
    const last = (await read($, keyAtAtom))[id]
    await noteKey($, id)
    if (!isPastTypeThrough(now, opened, last)) return
    await run()
  }

/**
 * Asks before a pane's action writes or starts a model turn: the engine's question dialog with the safe answer
 * first, so a stray Enter there answers no. Only the exact yes acts — a dismissed dialog, an answer typed under
 * "Other" and a run with nobody to ask all mean no.
 */
const confirm = async ($: EngineInterface, question: string, no: string, yes: string, header: string): Promise<boolean> =>
  (await $.ui.ask(question, { options: [no, yes], header }).catch(() => no)) === yes

/** U1 — reads the three skeleton files and counts sources newer than the skeleton. */
const loadPaperView = async ($: EngineInterface, root: string, on: boolean): Promise<NfPaperView> => {
  const io = ioOf($)
  const dir = join(root, PAPER_DIR)
  const ledgerText = await io.read(join(dir, 'paper-ledger.md'))
  const skeletonText = await io.read(join(dir, 'skeleton.md'))
  const gapsText = await io.read(join(dir, 'gaps.md'))
  const ledger = ledgerText === null ? null : parseLedger(ledgerText)
  const gaps = gapsText === null ? [] : parseGaps(gapsText)
  const slots = skeletonText === null ? [] : openSlots(skeletonText)
  const synced = skeletonText === null ? null : skeletonDate(skeletonText)
  const skeletonMtime = skeletonText === null ? 0 : ((await $.fs.stat(join(dir, 'skeleton.md')).catch(() => null))?.mtimeMs ?? 0)
  const stale: string[] = []
  if (skeletonText !== null) {
    for (const folder of SKELETON_SOURCES) {
      for (const entry of await $.fs.list(join(root, '.neuroflow', folder)).catch(() => [])) {
        if (entry.kind === 'file' && /\.(md|jsonl)$/.test(entry.name) && (entry.mtimeMs ?? 0) > skeletonMtime) stale.push(`${folder}/${entry.name}`)
      }
    }
  }
  const out = paperOutputPath(await io.read(join(dir, 'flow.md')))
  const frozen = (await io.exists(join(root, out, 'submission'))) || (await io.exists(join(root, out, 'revision')))
  return { status: autoStatusLine(on, ledger, synced, gapsText === null ? null : gaps.length, slots), gaps, slots, stale, frozen }
}

/** U3 — loads the newest X-ray (or the one named) into state. */
const loadXray = async ($: EngineInterface, root: string): Promise<NfXrayView | null> => {
  const dir = join(root, PAPER_DIR)
  const names = (await ioOf($).list(dir)).filter(entry => !entry.isDir).map(entry => entry.name)
  const name = newestXray(names)
  if (name === null) return null
  const text = (await ioOf($).read(join(dir, name))) ?? ''
  const md = name.replace(/\.jsonl$/, '.md')
  const view: NfXrayView = {
    jsonl: `${PAPER_DIR}/${name}`,
    md: names.includes(md) ? `${PAPER_DIR}/${md}` : null,
    title: name.replace(/^xray-/, '').replace(/\.jsonl$/, ''),
    findings: parseXray(text),
  }
  await update($, xrayViewAtom, () => view)
  return view
}

/** Records the person's decision on one finding in the .jsonl and the annotated .md, then reloads. */
const decide = async ($: EngineInterface, id: string, status: 'accepted' | 'rejected'): Promise<void> => {
  const scope = await read($, scopeAtom)
  const view = await read($, xrayViewAtom)
  if (scope === null || scope.root === null || view === null) return
  let reason: string | undefined
  if (status === 'accepted' && !(await confirm($, `Accept ${id}? Its box is ticked in both X-ray files; the fix is applied only when you ask Claude to.`, 'Keep it open', 'Accept', 'X-ray'))) {
    return
  }
  if (status === 'rejected') {
    const keep = 'Keep it open'
    const answer = await $.ui
      .ask(`Reject ${id}? The finding stays in the file with your reason, and a later X-ray raises it again only if the sentence changes.`, {
        options: [keep, 'Not a problem in this context', 'Out of scope for this paper'],
        header: 'X-ray',
      })
      .catch(() => keep)
    if (answer.trim() === '' || answer === keep) return
    reason = answer.trim()
  }
  const io = ioOf($)
  const jsonlPath = join(scope.root, view.jsonl)
  const jsonl = await io.read(jsonlPath)
  if (jsonl === null) return
  await io.write(jsonlPath, decideInJsonl(jsonl, id, status, reason))
  if (view.md !== null) {
    const mdPath = join(scope.root, view.md)
    const md = await io.read(mdPath)
    if (md !== null) await io.write(mdPath, decideInMarkdown(md, id, status, reason))
  }
  // The next pick is the open finding after this one in the pane's order (red first), so the page stays put.
  const before = xrayPage(view.findings.filter(item => item.status === 'open'), null, Number.MAX_SAFE_INTEGER).shown.map(item => item.id)
  await loadXray($, scope.root)
  const open = (await read($, xrayViewAtom))?.findings.filter(item => item.status === 'open') ?? []
  const after = before.slice(before.indexOf(id) + 1)
  const next = after.map(nextId => open.find(item => item.id === nextId)).find(item => item !== undefined) ?? xrayPage(open, null, 1).first
  await update($, xrayPickAtom, () => next?.id ?? null)
}

/** `--xray check <file>`: the two deterministic checks of an X-ray, reported without a model turn. */
const quickCheck = async ($: EngineInterface, root: string, file: string): Promise<string> => {
  const io = ioOf($)
  if (!(await io.exists(resolveFrom(root, file)))) return `No such file: ${file}`
  const lines = [`X-ray check of ${file} (scripts only; the sentence-by-sentence reading is /neuroflow:paper --xray ${file}):`]
  const stat = await runScript(io, 'skills/phase-paper/scripts/statcheck.py', [file, '--json'], { cwd: root, timeoutMs: 120_000 })
  const statReport = parseJson<{ summary?: Record<string, number>; results?: { line: number; text: string; status: string; label: string }[] }>(stat.stdout)
  if (statReport === null) lines.push(`- statcheck.py did not run: ${stat.stderr.trim().split('\n').pop() || 'no output'}`)
  else {
    const s = statReport.summary ?? {}
    lines.push(`- statcheck.py: ${s.consistent ?? 0} consistent, ${s.inconsistent ?? 0} inconsistent, ${s['decision-error'] ?? 0} decision errors, ${s.skipped ?? 0} skipped`)
    for (const item of (statReport.results ?? []).filter(r => r.status === 'inconsistent' || r.status === 'decision-error').slice(0, 6)) {
      lines.push(`  - line ${item.line}: ${item.text} — ${item.label}`)
    }
  }
  const cite = await runScript(io, 'skills/phase-paper/scripts/cite_check.py', [file, '--cache', '.neuroflow/paper/doi-cache.json', '--offline', '--json'], { cwd: root, timeoutMs: 60_000 })
  const citeReport = parseJson<{ summary?: Record<string, number>; dois?: { doi: string; status: string; label: string }[] }>(cite.stdout)
  if (citeReport === null) lines.push(`- cite_check.py (from the DOI cache) did not run: ${cite.stderr.trim().split('\n').pop() || 'no output'}`)
  else {
    const s = citeReport.summary ?? {}
    lines.push(`- cite_check.py, from the DOI cache: ${s.dois ?? 0} DOIs, ${s.do_not_resolve ?? 0} do not resolve, ${s.unchecked ?? 0} not in the cache yet, ${s.serious_notices ?? 0} with a retraction or concern notice`)
    for (const item of (citeReport.dois ?? []).filter(d => d.status === 'flag').slice(0, 6)) lines.push(`  - ${item.doi}: ${item.label}`)
  }
  lines.push('A clean result is not a review: unmarked numbers and citations are not "verified".')
  return lines.join('\n')
}

/** U2 — every card in the queue with its file name, newest first, whatever its status (pending, accepted or skipped). */
const queuedCards = async (io: NfIo, root: string): Promise<{ file: string; card: WikiCard }[]> => {
  const dir = join(root, PENDING_DIR)
  const names = (await io.list(dir)).filter(entry => !entry.isDir && entry.name.endsWith('.md')).map(entry => entry.name).sort().reverse()
  const out: { file: string; card: WikiCard }[] = []
  for (const name of names) {
    const card = parseCard((await io.read(join(dir, name))) ?? '')
    if (card !== null) out.push({ file: name, card })
  }
  return out
}

/** U2 — the pending cards, newest first, into state. */
const loadCards = async ($: EngineInterface, root: string): Promise<NfWikiCard[]> => {
  const cards: NfWikiCard[] = (await queuedCards(ioOf($), root))
    .filter(({ card }) => card.status === 'pending')
    .map(({ file, card }) => ({ file, title: card.title, type: card.type, evidence: card.evidence, body: card.body, by: card.by }))
  await update($, wikiCardsAtom, () => cards)
  const pick = await read($, wikiPickAtom)
  if (pick === null || !cards.some(card => card.file === pick)) await update($, wikiPickAtom, () => cards[0]?.file ?? null)
  return cards
}

/**
 * Skip marks the card skipped (it is never raised again); accept closes the pane and runs the normal --add flow, a
 * model turn. Each only after the person's yes: the pane holds the keys while the person may be typing.
 */
const settleCard = async ($: EngineInterface, file: string, title: string, accept: boolean): Promise<void> => {
  const scope = await read($, scopeAtom)
  if (scope === null || scope.root === null) return
  const yes = accept
    ? await confirm($, `Accept "${title}"? /neuroflow:wiki --add writes the page from the card, as a model turn.`, 'Not now', 'Accept', 'Wiki')
    : await confirm($, `Skip "${title}" for good? A skipped card is never raised again.`, 'Keep it waiting', 'Skip it', 'Wiki')
  if (!yes) return
  const path = join(scope.root, PENDING_DIR, file)
  if (!accept) {
    const text = await ioOf($).read(path)
    if (text !== null) await ioOf($).write(path, setCardStatus(text, 'skipped'))
    const left = await loadCards($, scope.root)
    if (left.length === 0) await $.ui.close({ id: WIKI_PANE })
    return
  }
  await $.ui.close({ id: WIKI_PANE })
  await $.command.run({ command: 'neuroflow:wiki', args: `--add --from-pending ${PENDING_DIR}/${file}` })
}

/** U2 — after a command logged decisions: one judge call, at most two cards. A title already in the wiki or anywhere
 *  in the queue — skipped cards included, which are never raised again — is not queued a second time. */
const judgeNewDecisions = async ($: EngineInterface, root: string, command: string, logPath: string, before: number, projectPolicy: string | null): Promise<number> => {
  const io = ioOf($)
  const home = await io.home()
  const userYaml = home ? await io.read(join(toSlash(home), '.neuroflow/user.yaml')) : null
  if (!captureAllowed(userYaml, projectPolicy)) return 0
  const fresh = ((await io.read(logPath)) ?? '').split(/\r?\n/).filter(line => line.trim() !== '').slice(before)
  if (fresh.length === 0) return 0
  const known = (await read($, wikiIndexAtom)).filter(page => page.level === 'project').map(page => page.title)
  const queued = (await queuedCards(io, root)).map(entry => entry.card)
  const prompt = [
    `Command: /neuroflow:${command}`,
    `New entries in ${relativeTo(logPath, root) ?? logPath}:`,
    ...fresh.slice(-10),
    '',
    `Pages already in the wiki: ${known.slice(0, 200).join('; ') || 'none'}`,
    `Cards already in the queue (pending, accepted or skipped): ${queued.slice(0, 200).map(card => card.title).join('; ') || 'none'}`,
  ].join('\n')
  const reply = await $.model.complete({ model: await $.session.model(), system: WIKI_JUDGE_SYSTEM, prompt, maxTokens: 600, timeoutMs: 30_000 })
  if (!reply.isAnswered) return 0
  const taken = takenTitles(known, queued)
  const cards = parseJudge(reply.text).filter(card => !taken.has(card.title.toLowerCase()))
  if (cards.length === 0) return 0
  const dir = join(root, PENDING_DIR)
  if (!(await io.exists(join(dir, '.gitignore')))) await io.write(join(dir, '.gitignore'), '*\n')
  const now = await io.now()
  const at = new Date(now)
  const captured = `${isoDate(now)}T${String(at.getHours()).padStart(2, '0')}:${String(at.getMinutes()).padStart(2, '0')}`
  let written = 0
  for (const card of cards) {
    const file = join(dir, `${isoDate(now)}-${slugify(card.title)}.md`)
    if (await io.exists(file)) continue
    await io.write(file, cardText({ title: card.title, type: card.type, evidence: card.evidence, captured, by: 'mod', status: 'pending', body: card.summary }))
    written += 1
  }
  return written
}

export const registerUser = (on: On, opts: NfOptions): void => {
  // U2: the judge runs after a main-loop command turn that logged new decisions (runtime on, opted in).
  on('turn.complete', { reason: 'answer' }, async ($, e, next) => {
    const result = await next(e)
    if (!mayWrite(opts) || e.agentId !== undefined) return result
    const scope = await read($, scopeAtom)
    const command = await read($, activeCommandAtom)
    const baseline = await read($, baselineAtom)
    if (!scope?.isActive || scope.root === null || command === null || command.lifecycle === 'quiet' || baseline === null) return result
    const snap = await read($, snapshotAtom)
    const written = await judgeNewDecisions($, scope.root, command.name, baseline.path, baseline.lines, snap?.wikiCapture ?? null).catch(() => 0)
    if (written > 0 && !scope.isHeadless) $.ui.toast(wikiCardsToast(written))
    return result
  }).catch(($, e, next) => next(e))

  // U2: /neuroflow:wiki --review opens the queue as a pane when a person is there; otherwise the prose walks it.
  on('command.run', { command: 'neuroflow:wiki' }, async ($, e, next) => {
    const scope = await read($, scopeAtom)
    if (!scope?.isActive || scope.root === null || e.args.trim() !== '--review' || !(await isPersonThere($))) return next(e)
    const cards = await loadCards($, scope.root)
    if (cards.length === 0) return { text: 'No wiki cards are waiting for review.' }
    await markOpened($, WIKI_PANE)
    await $.ui.open({ id: WIKI_PANE, title: 'wiki cards', focus: true, rows: paneRows('wiki', measuredRows()), columns: paneColumns('wiki') })
    return {
      text: `${cards.length} wiki card${cards.length === 1 ? '' : 's'} waiting — Tab to accept (runs /neuroflow:wiki --add for the card) or skip (for good), Enter, then your yes; j/k move between cards, q closes.`,
    }
  }).catch(($, e, next) => next(e))

  on('ui.render', { component: 'Pane', requestId: WIKI_PANE }, async ($, e) => {
    rememberViewport(e.viewport)
    const { Box, Button, Text } = $.ui.resolve(e)
    const cards = await read($, wikiCardsAtom)
    const pick = await read($, wikiPickAtom)
    const card = cards.find(item => item.file === pick) ?? cards[0] ?? null
    if (card === null) return <Text dimColor>No wiki cards are waiting.</Text>
    const index = cards.indexOf(card)
    const run = (fn: () => unknown) => act($, WIKI_PANE, fn)
    const runOn = (fn: () => unknown) => actOn($, WIKI_PANE, fn)
    const keysHere = e.surface !== 'terminal' || e.props.isFocused
    const step = (by: 1 | -1): string => cards[(index + by + cards.length) % cards.length]?.file ?? card.file
    const width = e.props.bodyColumns
    const term = e.surface === 'terminal'
    const compact = isCompact(e.viewport?.rows ?? measuredRows())
    /** Rows under UPPERCASE dim labels (the card's type, EVIDENCE), the labels in a column of their own. */
    const labelled = (items: readonly { label: string; value: string; dim?: boolean }[]): JSX.Element => (
      <Box flexDirection="column">
        {items.map(item => (
          <Box flexDirection="row">
            <Box width={LABEL} flexShrink={0}>
              <Text dimColor wrap="truncate-end">
                {item.label}
              </Text>
            </Box>
            <Box flexShrink={1}>
              <Text dimColor={item.dim === true} wrap="wrap">
                {item.value}
              </Text>
            </Box>
          </Box>
        ))}
      </Box>
    )
    return (
      <Box flexDirection="column">
        <Box flexDirection="row" justifyContent="space-between" columnGap={2}>
          <Box flexShrink={0}>
            <Text>{`${MARK} wiki cards`}</Text>
          </Box>
          <Box flexShrink={1}>
            <Text dimColor wrap="truncate-end">{`${index + 1} of ${cards.length}`}</Text>
          </Box>
        </Box>
        {term ? (
          <Text dimColor wrap="truncate-end">
            {rule(width)}
          </Text>
        ) : null}
        <Box flexDirection="column" marginY={compact || !term ? 0 : 1}>
          {labelled([
            { label: (card.type || 'card').toUpperCase(), value: card.title },
            { label: '', value: card.body },
            { label: 'EVIDENCE', value: [card.evidence, `captured by ${card.by === 'mod' ? 'the mod' : 'the model'}`].filter(part => part !== '').join(' · '), dim: true },
          ])}
        </Box>
        {term && !compact ? (
          <Text dimColor wrap="truncate-end">
            {rule(width)}
          </Text>
        ) : null}
        {keysHere ? (
          <Box flexDirection={widthClass(width) === 'narrow' ? 'column' : 'row'} justifyContent="space-between" columnGap={2}>
            <Box flexDirection="row" flexWrap="wrap" columnGap={2} flexShrink={1}>
              <Button key="nf-wiki-accept" label={widthClass(width) === 'wide' ? 'accept → /wiki --add' : 'accept'} plain onPress={runOn(() => settleCard($, card.file, card.title, true))} />
              <Button key="nf-wiki-skip" label="skip" plain onPress={runOn(() => settleCard($, card.file, card.title, false))} />
              {cards.length > 1
                ? [
                    <Button key="nf-wiki-next" label="next" hotkey={NAV.down} plain dimColor onPress={run(() => update($, wikiPickAtom, () => step(1)))} />,
                    <Button key="nf-wiki-prev" label="previous" hotkey={NAV.up} plain dimColor onPress={run(() => update($, wikiPickAtom, () => step(-1)))} />,
                  ]
                : null}
              <Button key="nf-wiki-close" label="close" hotkey={NAV.close} plain dimColor role="dismiss" onPress={run(() => $.ui.close({ id: WIKI_PANE }))} />
            </Box>
            {term ? (
              <Box flexShrink={0}>
                <Text dimColor>tab, enter: act · esc: prompt</Text>
              </Box>
            ) : null}
          </Box>
        ) : (
          <Text dimColor wrap="truncate-end">
            {unfocusedHint('/neuroflow:wiki --review')}
          </Text>
        )}
      </Box>
    )
  }).catch(($, e, next) => next(e))

  on('command.run', { command: 'neuroflow:paper' }, async ($, e, next) => {
    const scope = await read($, scopeAtom)
    if (!scope?.isActive || scope.root === null) return next(e)
    const args = e.args.trim()
    const root = scope.root
    if (/^--auto\s+status\s*$/.test(args)) {
      const snap = await read($, snapshotAtom)
      const view = await loadPaperView($, root, snap?.paperAuto === true)
      await update($, paperViewAtom, () => view)
      if (await isPersonThere($)) {
        await markOpened($, PAPER_PANE)
        await $.ui.open({ id: PAPER_PANE, title: 'living paper', focus: true, rows: paneRows('paper', measuredRows()), columns: paneColumns('paper') })
      }
      return { text: view.status + (view.stale.length > 0 ? ` | ${view.stale.length} source file(s) changed since the last sync` : '') }
    }
    if (/^--xray\s+view\s*$/.test(args)) {
      const view = await loadXray($, root)
      if (view === null) return { text: 'No X-ray yet. Run /neuroflow:paper --xray <manuscript file> first.' }
      await update($, xrayPickAtom, () => xrayPage(view.findings.filter(item => item.status === 'open'), null, 1).first?.id ?? null)
      if (await isPersonThere($)) {
        await markOpened($, XRAY_PANE)
        await $.ui.open({ id: XRAY_PANE, title: `X-ray ${view.title}`, focus: true, rows: paneRows('xray', measuredRows()), columns: paneColumns('xray') })
      }
      const counts = xrayCounts(view.findings)
      return { text: `X-ray ${view.title}: ${counts.red} red, ${counts.orange} orange open; ${counts.decided} decided.` }
    }
    const check = /^--xray\s+check\s+(.+)$/.exec(args)
    if (check !== null) return { text: await quickCheck($, root, check[1].trim().replace(/^["']|["']$/g, '')) }
    return next(e)
  }).catch(($, e, next) => next(e))

  on('ui.render', { component: 'Pane', requestId: PAPER_PANE }, async ($, e) => {
    rememberViewport(e.viewport)
    const { Box, Button, Text } = $.ui.resolve(e)
    const view = await read($, paperViewAtom)
    const scope = await read($, scopeAtom)
    if (view === null || scope === null || scope.root === null) return <Text dimColor>neuroflow: no living paper loaded — /neuroflow:paper --auto status</Text>
    const root = scope.root
    const run = (fn: () => unknown) => act($, PAPER_PANE, fn)
    const runOn = (fn: () => unknown) => actOn($, PAPER_PANE, fn)
    const keysHere = e.surface !== 'terminal' || e.props.isFocused
    const width = e.props.bodyColumns
    const term = e.surface === 'terminal'
    const compact = isCompact(e.viewport?.rows ?? measuredRows())
    /** A row under an UPPERCASE dim label: CHANGED, RESULTS, GAPS. */
    const labelled = (label: string, children: JSX.Element): JSX.Element => (
      <Box flexDirection="row">
        <Box width={LABEL} flexShrink={0}>
          <Text dimColor>{label}</Text>
        </Box>
        <Box flexDirection="column" flexShrink={1}>
          {children}
        </Box>
      </Box>
    )
    return (
      <Box flexDirection="column">
        <Text>{`${MARK} living paper`}</Text>
        {term ? (
          <Text dimColor wrap="truncate-end">
            {rule(width)}
          </Text>
        ) : null}
        <Box flexDirection="column" marginY={compact || !term ? 0 : 1}>
          <Text wrap="wrap">{view.status}</Text>
          {view.frozen ? <Text color="warning" wrap="wrap">The paper is frozen (a submission or revision exists): sync reports changes and rewrites nothing.</Text> : null}
          <Box flexDirection="column" marginTop={compact ? 0 : 1}>
            {view.stale.length > 0
              ? labelled(
                  'CHANGED',
                  <Text color="warning" wrap="truncate-end">{`${view.stale.length} source file(s) since the last sync: ${view.stale.slice(0, 4).join(', ')}${view.stale.length > 4 ? ' …' : ''}`}</Text>,
                )
              : null}
            {view.slots.length > 0 ? labelled('RESULTS', <Text wrap="wrap">{`without a final result: ${view.slots.join(', ')}`}</Text>) : null}
            {labelled(
              'GAPS',
              view.gaps.length === 0 ? (
                <Text dimColor>No reporting gaps listed.</Text>
              ) : (
                <Box flexDirection="column">
                  {view.gaps.slice(0, 8).map(gap => (
                    <Text wrap="truncate-end">{`· ${gap.gap} — ${gap.item} → ${gap.fill}`}</Text>
                  ))}
                  {view.gaps.length > 8 ? <Text dimColor>{`… ${view.gaps.length - 8} more in .neuroflow/paper/gaps.md`}</Text> : null}
                </Box>
              ),
            )}
          </Box>
        </Box>
        {term && !compact ? (
          <Text dimColor wrap="truncate-end">
            {rule(width)}
          </Text>
        ) : null}
        {keysHere ? (
          <Box flexDirection={widthClass(width) === 'narrow' ? 'column' : 'row'} justifyContent="space-between" columnGap={2}>
            <Box flexDirection="row" flexWrap="wrap" columnGap={2} flexShrink={1}>
              <Button
                key="nf-paper-sync"
                label="sync now"
                plain
                onPress={runOn(async () => {
                  if (!(await confirm($, syncQuestion(view.frozen), 'Not now', 'Sync now', 'Paper'))) return
                  await $.ui.close({ id: PAPER_PANE })
                  await $.command.run({ command: 'neuroflow:paper', args: '--auto sync' })
                })}
              />
              <Button
                key="nf-paper-refresh"
                label="reread"
                hotkey={NAV.reread}
                plain
                dimColor
                onPress={run(async () => {
                  const snap = await read($, snapshotAtom)
                  const fresh = await loadPaperView($, root, snap?.paperAuto === true)
                  await update($, paperViewAtom, () => fresh)
                })}
              />
              <Button key="nf-paper-close" label="close" hotkey={NAV.close} plain dimColor role="dismiss" onPress={run(() => $.ui.close({ id: PAPER_PANE }))} />
            </Box>
            {term ? (
              <Box flexShrink={0}>
                <Text dimColor>tab, enter: act · esc: prompt</Text>
              </Box>
            ) : null}
          </Box>
        ) : (
          <Text dimColor wrap="truncate-end">
            {unfocusedHint('/neuroflow:paper --auto status')}
          </Text>
        )}
      </Box>
    )
  }).catch(($, e, next) => next(e))

  on('ui.render', { component: 'Pane', requestId: XRAY_PANE }, async ($, e) => {
    rememberViewport(e.viewport)
    const view = await read($, xrayViewAtom)
    const pick = await read($, xrayPickAtom)
    const { Box, Button, Text } = $.ui.resolve(e)
    if (view === null) return <Text dimColor>neuroflow: no X-ray loaded — /neuroflow:paper --xray view</Text>
    const counts = xrayCounts(view.findings)
    const open = view.findings.filter(item => item.status === 'open')
    // XRAY_PAGE rows at a time, the page that holds the picked finding: j and k turn the pages as they go (#255).
    const page = xrayPage(open, pick, XRAY_PAGE)
    const picked = view.findings.find(item => item.id === pick) ?? page.first
    const run = (fn: () => unknown) => act($, XRAY_PANE, fn)
    const runOn = (fn: () => unknown) => actOn($, XRAY_PANE, fn)
    const keysHere = e.surface !== 'terminal' || e.props.isFocused
    const width = e.props.bodyColumns
    const term = e.surface === 'terminal'
    const compact = isCompact(e.viewport?.rows ?? measuredRows())
    const stepTo = (step: 1 | -1) => run(() => update($, xrayPickAtom, () => xrayStep(open, picked?.id ?? null, step)?.id ?? null))
    /** A row under an UPPERCASE dim label (or the finding's id), the labels in a column of their own. */
    const labelled = (label: string, value: string, dim = false): JSX.Element => (
      <Box flexDirection="row">
        <Box width={LABEL} flexShrink={0}>
          <Text dimColor wrap="truncate-end">
            {label}
          </Text>
        </Box>
        <Box flexShrink={1}>
          <Text dimColor={dim} wrap="wrap">
            {value}
          </Text>
        </Box>
      </Box>
    )
    return (
      <Box flexDirection="column">
        <Box flexDirection="row" justifyContent="space-between" columnGap={2}>
          <Box flexShrink={1}>
            <Text wrap="truncate-end">
              {`${MARK} X-ray`}
              <Text dimColor>{` · ${view.title}`}</Text>
            </Text>
          </Box>
          <Box flexShrink={0}>
            <Text dimColor>{`${counts.red} red · ${counts.orange} orange open · ${counts.decided} decided`}</Text>
          </Box>
        </Box>
        {term ? (
          <Text dimColor wrap="truncate-end">
            {rule(width)}
          </Text>
        ) : null}
        <Box flexDirection="column" marginY={compact || !term ? 0 : 1}>
          {open.length === 0 ? (
            <Text color="success">✔ Every finding is decided.</Text>
          ) : (
            <Box flexDirection="column">
              {page.shown.map(item => (
                <Button
                  key={`nf-xray-${item.id}`}
                  label={fit(`${item.id === picked?.id ? '▸' : ' '} ${findingLabel(item)}`, Math.max(20, width))}
                  plain
                  onPress={runOn(() => update($, xrayPickAtom, () => item.id))}
                />
              ))}
              {page.total > page.shown.length ? <Text dimColor>{`  showing ${page.from}–${page.to} of ${page.total} open, red first`}</Text> : null}
            </Box>
          )}
          {picked !== null ? (
            <Box flexDirection="column" marginTop={compact ? 0 : 1}>
              {labelled(picked.id, `${picked.scope}${picked.line ? `, line ${picked.line}` : ''} · ${picked.basis ?? 'model'}`, true)}
              {labelled('', picked.finding)}
              {picked.fix ? labelled('FIX', picked.fix) : null}
            </Box>
          ) : null}
        </Box>
        {term && !compact ? (
          <Text dimColor wrap="truncate-end">
            {rule(width)}
          </Text>
        ) : null}
        {keysHere ? (
          <Box flexDirection={widthClass(width) === 'narrow' ? 'column' : 'row'} justifyContent="space-between" columnGap={2}>
            <Box flexDirection="row" flexWrap="wrap" columnGap={2} flexShrink={1}>
              {picked !== null && picked.status === 'open'
                ? [
                    <Button key="nf-xray-accept" label="accept" plain onPress={runOn(() => decide($, picked.id, 'accepted'))} />,
                    <Button key="nf-xray-reject" label="reject…" plain onPress={runOn(() => decide($, picked.id, 'rejected'))} />,
                  ]
                : null}
              {open.length > 1
                ? [
                    <Button key="nf-xray-next" label="next" hotkey={NAV.down} plain dimColor onPress={stepTo(1)} />,
                    <Button key="nf-xray-prev" label="previous" hotkey={NAV.up} plain dimColor onPress={stepTo(-1)} />,
                  ]
                : null}
              <Button key="nf-xray-close" label="close" hotkey={NAV.close} plain dimColor role="dismiss" onPress={run(() => $.ui.close({ id: XRAY_PANE }))} />
            </Box>
            {term ? (
              <Box flexShrink={0}>
                <Text dimColor>tab, enter: act · esc: prompt</Text>
              </Box>
            ) : null}
          </Box>
        ) : (
          <Text dimColor wrap="truncate-end">
            {unfocusedHint('/neuroflow:paper --xray view')}
          </Text>
        )}
        <Text dimColor wrap="wrap">
          Accepted findings are applied only when you ask Claude to apply them: to a -r1 copy, under the --revise rule.
        </Text>
      </Box>
    )
  }).catch(($, e, next) => next(e))
}
