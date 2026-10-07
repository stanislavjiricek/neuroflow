// User ideas — the living paper and the paper X-ray, drawn and decided by code.
//  - U1 living paper: `/neuroflow:paper --auto status` is answered in code (the status line commands/paper.md
//    specifies) and opens a pane with the reporting gaps, the Results slots still without a final result,
//    and how many allow-listed sources changed since the last sync; `y` runs `/neuroflow:paper --auto sync`.
//    The mod never writes the skeleton: sync stays a model turn, on the person's key press.
//  - U3 X-ray: `/neuroflow:paper --xray view` opens the newest X-ray as a pane; a finding is accepted (its box
//    ticked) or rejected with a reason on a key press, in both X-ray files. `--xray check <file>` runs the two
//    deterministic checks (statcheck.py, cite_check.py) and reports them with no model turn.
//  - U2 auto wiki: after a command turn that logged a new decision, one model call judges whether it is
//    reusable knowledge (the wiki skill's rubric: nothing is the normal answer, evidence mandatory, never
//    results); at most two cards go to .neuroflow/wiki/.pending/. Only with `wiki_auto: ask` in the person's
//    user.yaml, a project that does not forbid it, and runtime on. `/neuroflow:wiki --review` opens the cards
//    as a pane: accept runs the normal `/neuroflow:wiki --add --from-pending`; skip marks the card skipped.
// The figure check (U4) is prose only: a viewer cannot show figures or take pointer input on most terminals.
import { atom, read, update } from 'claude-code'
import type { EngineInterface, On } from 'claude-code'

import type { NfPaperView, NfWikiCard, NfXrayView } from '../../../types'
import type { NfIo } from '../lib/io'
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
import { PENDING_DIR, WIKI_JUDGE_SYSTEM, captureAllowed, cardText, parseCard, parseJudge, setCardStatus, slugify } from '../lib/wikiqueue'
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

const PAPER_PANE = 'nf-paper'
const XRAY_PANE = 'nf-xray'
const WIKI_PANE = 'nf-wiki'
const PAPER_DIR = '.neuroflow/paper'

/** The allow-listed source folders a sync reads (phase-paper → Living paper skeleton), for the staleness count. */
export const SKELETON_SOURCES = [
  'ideation', 'preregistration', 'ethics', 'experiment', 'tool-build', 'tool-validate', 'data', 'data-preprocess',
  'data-analyze', 'brain-build', 'brain-optimize', 'brain-run', 'reasoning',
]

const SEVERITY_GLYPH: Record<string, string> = { red: '●', orange: '◐' }

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

const isPersonThere = async ($: EngineInterface): Promise<boolean> => (await $.session.surfaces()).length > 0

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
  await loadXray($, scope.root)
  const next = (await read($, xrayViewAtom))?.findings.find(item => item.status === 'open')
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

/** U2 — the pending cards, newest first, into state. */
const loadCards = async ($: EngineInterface, root: string): Promise<NfWikiCard[]> => {
  const io = ioOf($)
  const dir = join(root, PENDING_DIR)
  const cards: NfWikiCard[] = []
  const names = (await io.list(dir)).filter(entry => !entry.isDir && entry.name.endsWith('.md')).map(entry => entry.name).sort().reverse()
  for (const name of names) {
    const card = parseCard((await io.read(join(dir, name))) ?? '')
    if (card !== null && card.status === 'pending') cards.push({ file: name, title: card.title, type: card.type, evidence: card.evidence, body: card.body, by: card.by })
  }
  await update($, wikiCardsAtom, () => cards)
  const pick = await read($, wikiPickAtom)
  if (pick === null || !cards.some(card => card.file === pick)) await update($, wikiPickAtom, () => cards[0]?.file ?? null)
  return cards
}

/** Skip marks the card skipped (it is never raised again); accept closes the pane and runs the normal --add flow. */
const settleCard = async ($: EngineInterface, file: string, accept: boolean): Promise<void> => {
  const scope = await read($, scopeAtom)
  if (scope === null || scope.root === null) return
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

/** U2 — after a command logged decisions: one judge call, at most two cards. */
const judgeNewDecisions = async ($: EngineInterface, root: string, command: string, logPath: string, before: number, projectPolicy: string | null): Promise<number> => {
  const io = ioOf($)
  const home = await io.home()
  const userYaml = home ? await io.read(join(toSlash(home), '.neuroflow/user.yaml')) : null
  if (!captureAllowed(userYaml, projectPolicy)) return 0
  const fresh = ((await io.read(logPath)) ?? '').split(/\r?\n/).filter(line => line.trim() !== '').slice(before)
  if (fresh.length === 0) return 0
  const known = (await read($, wikiIndexAtom)).filter(page => page.level === 'project').map(page => page.title)
  const waiting = (await loadCards($, root)).map(card => card.title)
  const prompt = [
    `Command: /neuroflow:${command}`,
    `New entries in ${relativeTo(logPath, root) ?? logPath}:`,
    ...fresh.slice(-10),
    '',
    `Pages already in the wiki: ${known.slice(0, 200).join('; ') || 'none'}`,
    `Cards already waiting: ${waiting.join('; ') || 'none'}`,
  ].join('\n')
  const reply = await $.model.complete({ model: await $.session.model(), system: WIKI_JUDGE_SYSTEM, prompt, maxTokens: 600, timeoutMs: 30_000 })
  if (!reply.isAnswered) return 0
  const taken = new Set([...known, ...waiting].map(title => title.toLowerCase()))
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
    if (written > 0 && !scope.isHeadless) $.ui.toast(`neuroflow: ${written} wiki card${written === 1 ? '' : 's'} to review — w on the band, or /neuroflow:wiki --review`)
    return result
  }).catch(($, e, next) => next(e))

  // U2: /neuroflow:wiki --review opens the queue as a pane when a person is there; otherwise the prose walks it.
  on('command.run', { command: 'neuroflow:wiki' }, async ($, e, next) => {
    const scope = await read($, scopeAtom)
    if (!scope?.isActive || scope.root === null || e.args.trim() !== '--review' || !(await isPersonThere($))) return next(e)
    const cards = await loadCards($, scope.root)
    if (cards.length === 0) return { text: 'No wiki cards are waiting for review.' }
    await $.ui.open({ id: WIKI_PANE, title: 'wiki cards', focus: true })
    return { text: `${cards.length} wiki card${cards.length === 1 ? '' : 's'} waiting — accept runs /neuroflow:wiki --add for the card; skip drops it for good.` }
  }).catch(($, e, next) => next(e))

  on('ui.render', { component: 'Pane', requestId: WIKI_PANE }, async ($, e) => {
    const { Box, Button, Text } = $.ui.resolve(e)
    const cards = await read($, wikiCardsAtom)
    const pick = await read($, wikiPickAtom)
    const card = cards.find(item => item.file === pick) ?? cards[0] ?? null
    if (card === null) return <Text dimColor>No wiki cards are waiting.</Text>
    const index = cards.indexOf(card)
    return (
      <Box flexDirection="column" gap={1}>
        <Text bold wrap="truncate-end">{`${index + 1}/${cards.length} · ${card.type}: ${card.title}`}</Text>
        <Text wrap="wrap">{card.body}</Text>
        <Text dimColor wrap="truncate-end">{`evidence: ${card.evidence} · captured by ${card.by === 'mod' ? 'the mod' : 'the model'}`}</Text>
        <Box flexDirection="row" columnGap={1}>
          <Button key="nf-wiki-accept" label="accept → /wiki --add" hotkey="a" onPress={() => settleCard($, card.file, true)} />
          <Button key="nf-wiki-skip" label="skip" hotkey="s" onPress={() => settleCard($, card.file, false)} />
          {cards.length > 1 ? (
            <Button key="nf-wiki-next" label="next" hotkey="n" onPress={() => update($, wikiPickAtom, () => cards[(index + 1) % cards.length].file)} />
          ) : null}
          <Button key="nf-wiki-close" label="close" hotkey="c" role="dismiss" onPress={() => $.ui.close({ id: WIKI_PANE })} />
        </Box>
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
      if (await isPersonThere($)) await $.ui.open({ id: PAPER_PANE, title: 'living paper' })
      return { text: view.status + (view.stale.length > 0 ? ` | ${view.stale.length} source file(s) changed since the last sync` : '') }
    }
    if (/^--xray\s+view\s*$/.test(args)) {
      const view = await loadXray($, root)
      if (view === null) return { text: 'No X-ray yet. Run /neuroflow:paper --xray <manuscript file> first.' }
      await update($, xrayPickAtom, () => view.findings.find(item => item.status === 'open')?.id ?? null)
      if (await isPersonThere($)) await $.ui.open({ id: XRAY_PANE, title: `X-ray ${view.title}`, focus: true })
      const counts = xrayCounts(view.findings)
      return { text: `X-ray ${view.title}: ${counts.red} red, ${counts.orange} orange open; ${counts.decided} decided.` }
    }
    const check = /^--xray\s+check\s+(.+)$/.exec(args)
    if (check !== null) return { text: await quickCheck($, root, check[1].trim().replace(/^["']|["']$/g, '')) }
    return next(e)
  }).catch(($, e, next) => next(e))

  on('ui.render', { component: 'Pane', requestId: PAPER_PANE }, async ($, e) => {
    const { Box, Button, Text } = $.ui.resolve(e)
    const view = await read($, paperViewAtom)
    const scope = await read($, scopeAtom)
    if (view === null || scope === null || scope.root === null) return <Text dimColor>neuroflow: no living paper loaded — /neuroflow:paper --auto status</Text>
    const root = scope.root
    return (
      <Box flexDirection="column" gap={1}>
        <Text bold wrap="truncate-end">{view.status}</Text>
        {view.frozen ? <Text color="warning">The paper is frozen (a submission or revision exists): sync reports changes and rewrites nothing.</Text> : null}
        {view.stale.length > 0 ? (
          <Text color="warning" wrap="truncate-end">{`${view.stale.length} source file(s) changed since the last sync: ${view.stale.slice(0, 4).join(', ')}${view.stale.length > 4 ? ' …' : ''}`}</Text>
        ) : null}
        {view.slots.length > 0 ? <Text>{`Results slots without a final result: ${view.slots.join(', ')}`}</Text> : null}
        <Box flexDirection="column">
          {view.gaps.length === 0 ? <Text dimColor>No reporting gaps listed.</Text> : <Text>Reporting gaps:</Text>}
          {view.gaps.slice(0, 8).map(gap => (
            <Text wrap="truncate-end">{`· ${gap.gap} — ${gap.item} → ${gap.fill}`}</Text>
          ))}
          {view.gaps.length > 8 ? <Text dimColor>{`… ${view.gaps.length - 8} more in .neuroflow/paper/gaps.md`}</Text> : null}
        </Box>
        <Box flexDirection="row" columnGap={1}>
          <Button
            key="nf-paper-sync"
            label="sync now"
            hotkey="y"
            onPress={async () => {
              await $.ui.close({ id: PAPER_PANE })
              await $.command.run({ command: 'neuroflow:paper', args: '--auto sync' })
            }}
          />
          <Button
            key="nf-paper-refresh"
            label="refresh"
            hotkey="r"
            onPress={async () => {
              const snap = await read($, snapshotAtom)
              const fresh = await loadPaperView($, root, snap?.paperAuto === true)
              await update($, paperViewAtom, () => fresh)
            }}
          />
          <Button key="nf-paper-close" label="close" hotkey="c" role="dismiss" onPress={() => $.ui.close({ id: PAPER_PANE })} />
        </Box>
      </Box>
    )
  }).catch(($, e, next) => next(e))

  on('ui.render', { component: 'Pane', requestId: XRAY_PANE }, async ($, e) => {
    const view = await read($, xrayViewAtom)
    const pick = await read($, xrayPickAtom)
    const { Box, Button, Text } = $.ui.resolve(e)
    if (view === null) return <Text dimColor>neuroflow: no X-ray loaded — /neuroflow:paper --xray view</Text>
    const counts = xrayCounts(view.findings)
    const open = view.findings.filter(item => item.status === 'open')
    const picked = view.findings.find(item => item.id === pick) ?? open[0] ?? null
    const header = `${view.title} · ${counts.red} red · ${counts.orange} orange open · ${counts.decided} decided`
    const Select = e.surface === 'mobile' ? null : $.ui.resolve(e).Select
    const list =
      Select === null ? (
        <Box flexDirection="column">
          {open.slice(0, 8).map(item => (
            <Button key={`nf-xray-${item.id}`} label={findingLabel(item)} onPress={() => update($, xrayPickAtom, () => item.id)} />
          ))}
        </Box>
      ) : (
        <Select
          key="nf-xray-select"
          label="Finding "
          options={open.map(item => ({ value: item.id, label: findingLabel(item) }))}
          value={picked?.id}
          autoFocus
          onSelect={value => {
            void update($, xrayPickAtom, () => value)
          }}
        />
      )
    return (
      <Box flexDirection="column" gap={1}>
        <Text bold wrap="truncate-end">{header}</Text>
        {open.length === 0 ? <Text color="success">Every finding is decided.</Text> : list}
        {picked !== null ? (
          <Box flexDirection="column">
            <Text wrap="wrap">{`${picked.id} (${picked.scope}${picked.line ? `, line ${picked.line}` : ''}, ${picked.basis ?? 'model'}): ${picked.finding}`}</Text>
            {picked.fix ? <Text dimColor wrap="wrap">{`Fix: ${picked.fix}`}</Text> : null}
          </Box>
        ) : null}
        <Box flexDirection="row" columnGap={1}>
          {picked !== null && picked.status === 'open' ? <Button key="nf-xray-accept" label="accept" hotkey="a" onPress={() => decide($, picked.id, 'accepted')} /> : null}
          {picked !== null && picked.status === 'open' ? <Button key="nf-xray-reject" label="reject…" hotkey="x" onPress={() => decide($, picked.id, 'rejected')} /> : null}
          <Button key="nf-xray-close" label="close" hotkey="c" role="dismiss" onPress={() => $.ui.close({ id: XRAY_PANE })} />
        </Box>
        <Text dimColor>Accepted findings are applied only when you ask Claude to apply them: to a -r1 copy, under the --revise rule.</Text>
      </Box>
    )
  }).catch(($, e, next) => next(e))
}
