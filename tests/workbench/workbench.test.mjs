// node --test tests/workbench/workbench.test.mjs — the workbench page's logic against the golden snapshot that
// workbench.py writes (tests/fixtures/workbench), so the exporter and the page cannot drift apart on the format,
// on the overlay of waiting clicks, or on the intent documents the validator reads.
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { Script, createContext } from 'node:vm'

import {
  activeIntents, assembleLevel, boardModel, daysUntil, defaultPrefs, freshnessLabel, intentDocument, intentsPath, isCollectionPath,
  isDelimiterRow, isDocumentPath, isOverdue, lanes, levelOrder, makeAdd, makeCancel, makeMove, metaPath, neighbourColumn, newIntentId,
  normalizePrefs, oldestWaiting, outcomeText, parseInline, parseMarkdown, partsPath, phaseMap, prefsPath, recentOutcomes, releasePatch,
  safeHref, segments, tabSummary, upcomingDates, userRoot, validLevelKey, validSegment, waitingCount, waitingIntents, wikiIndex,
} from '../../skills/neuroflow-core/assets/workbench/workbench.mjs'

const here = dirname(fileURLToPath(import.meta.url))
const root = join(here, '..', '..')
const read = name => JSON.parse(readFileSync(join(root, 'tests', 'fixtures', 'workbench', name), 'utf8'))
const snapshot = read('snapshot.json')
const golden = read('intents.json')
const expected = read('expected.json')
const goldenList = () => Object.entries(structuredClone(golden)).map(([id, body]) => ({ id, ...body }))
const level = key => {
  const result = assembleLevel(snapshot.metas[key], Object.values(snapshot.parts[key]))
  assert.equal(result.status, 'ready', result.reason)
  return result.level
}
const HIVE = 'hive+example-lab+hive'
const NOW = Date.parse('2026-10-21T10:30:00Z')

test('every database path the page builds has the right parity', () => {
  const uid = 'u_0123456789abcdefghijkl'
  assert.equal(segments(userRoot(uid)), 3)
  assert.ok(isCollectionPath(userRoot(uid)))
  for (const key of Object.keys(snapshot.metas)) {
    assert.ok(validLevelKey(key), key)
    assert.ok(isDocumentPath(metaPath(uid, key)), key) // 4
    assert.ok(isCollectionPath(partsPath(uid, key)), key) // 5
    assert.ok(isDocumentPath(`${partsPath(uid, key)}/core`), key) // 6
  }
  assert.ok(isCollectionPath(intentsPath(uid))) // 5
  assert.ok(isDocumentPath(`${intentsPath(uid)}/${newIntentId(NOW, 'abc123xyz')}`)) // 6
  assert.ok(isDocumentPath(prefsPath(uid))) // 4
  assert.ok(!isDocumentPath(`${userRoot(uid)}/hive:example-lab:hive/parts`))
  assert.ok(!validLevelKey('prefs') && !validLevelKey('inbox') && !validLevelKey('hive:example-lab:hive'))
})

test('intent ids are valid document ids that sort by creation', () => {
  const a = newIntentId(Date.parse('2026-10-21T10:00:00Z'), 'k3j2h1g0')
  const b = newIntentId(Date.parse('2026-10-21T10:00:01Z'), 'a0a0a0a0')
  assert.match(a, /^i-[0-9a-z]+-[0-9a-z]{6,12}$/)
  assert.ok(validSegment(a) && a < b)
})

test('a level is drawn only from a complete, current snapshot', () => {
  const key = 'flowie'
  const parts = Object.values(snapshot.parts[key])
  assert.equal(assembleLevel(snapshot.metas[key], parts).level.cards.length, snapshot.metas[key].counts.cards)
  const torn = parts.map(part => (part.part === 'core' ? { ...part, sha256: 'x' } : part))
  assert.equal(assembleLevel(snapshot.metas[key], torn).status, 'updating')
  assert.equal(assembleLevel({ ...snapshot.metas[key], snap_schema: 2 }, parts).status, 'newer')
  assert.equal(assembleLevel(null, parts).status, 'invalid')
})

test('the freshness label is word for word what workbench.py writes', () => {
  for (const [key, text] of Object.entries(expected.freshness)) assert.equal(freshnessLabel(snapshot.metas[key]), text)
  const meta = { machine: 'laptop', working_tree: true, source: { git: true, branch: 'main', head: 'abcdef1234', uncommitted_tasks: 2, fetched_at: 'T' } }
  assert.equal(freshnessLabel(meta), 'working tree on main @ abcdef1 + 2 uncommitted task changes · upstream fetched T · from laptop')
})

test('the waiting clicks put each card where the validator will (golden intents)', () => {
  const intents = goldenList()
  for (const [key, finals] of Object.entries(expected.final)) {
    const board = boardModel(level(key), intents, { today: '2026-10-21', nowMs: NOW })
    const where = new Map(board.columns.flatMap(column => column.cards.map(card => [card.slug || card.addId, column.id])))
    for (const [slug, column] of Object.entries(finals)) {
      const add = Object.entries(expected.adds).find(([, planned]) => planned === slug)
      assert.equal(where.get(add ? add[0] : slug), column, `${key} ${slug}`)
    }
  }
  const hive = boardModel(level(HIVE), intents, { today: '2026-10-21', nowMs: NOW })
  const moved = hive.columns.find(column => column.id === 'review').cards.find(card => card.slug === 'fix-channel-map')
  assert.deepEqual(moved.pending.ids, ['i-mh2a0001-aaaa', 'i-mh2a0002-bbbb'])
  assert.equal(moved.pending.from, 'inbox')
  assert.equal(hive.pending, 2)
})

test('the gestures write exactly the golden intent documents', () => {
  const at = id => Date.parse(golden[id].created_at)
  const doc = intent => JSON.parse(JSON.stringify(intentDocument(intent)))
  const hive = level(HIVE)
  const cardIn = (board, slug) => board.columns.flatMap(column => column.cards).find(card => card.slug === slug)
  // a move of an exported card carries its content hash
  let board = boardModel(hive, [], { nowMs: NOW })
  const first = makeMove({ level: HIVE, card: cardIn(board, 'fix-channel-map'), to: 'active', nowMs: at('i-mh2a0001-aaaa'), id: 'i-mh2a0001-aaaa' })
  assert.deepEqual(doc(first), golden['i-mh2a0001-aaaa'])
  // a second move of the same card is chained to the first and still carries the hash
  board = boardModel(hive, [first], { nowMs: NOW })
  const second = makeMove({ level: HIVE, card: cardIn(board, 'fix-channel-map'), to: 'review', nowMs: at('i-mh2a0002-bbbb'), id: 'i-mh2a0002-bbbb' })
  assert.deepEqual(doc(second), golden['i-mh2a0002-bbbb'])
  // a card added on the board has no slug: its move names the add, with no hash
  const add = makeAdd({ level: 'flowie', fields: { title: ' Draft the methods ', project: 'solo-review', owner: '' }, to: 'inbox', nowMs: at('i-mh2a0003-cccc'), id: 'i-mh2a0003-cccc' })
  assert.deepEqual(doc(add), golden['i-mh2a0003-cccc'])
  board = boardModel(level('flowie'), [add], { nowMs: NOW })
  const added = board.columns.find(column => column.id === 'inbox').cards.find(card => card.isNew)
  const move = makeMove({ level: 'flowie', card: added, to: 'active', nowMs: at('i-mh2a0004-dddd'), id: 'i-mh2a0004-dddd' })
  assert.deepEqual(doc(move), golden['i-mh2a0004-dddd'])
  const undo = makeCancel({ level: 'flowie', target: 'i-mh2a0004-dddd', nowMs: at('i-mh2a0005-eeee'), id: 'i-mh2a0005-eeee' })
  assert.deepEqual(doc(undo), golden['i-mh2a0005-eeee'])
  assert.equal(makeMove({ level: HIVE, card: cardIn(boardModel(hive, [], {}), 'rerun-ica'), to: 'active', nowMs: NOW, id: 'x' }), null)
  assert.equal(makeAdd({ level: 'flowie', fields: { title: '   ' }, nowMs: NOW, id: 'x' }), null)
})

test('a legacy or unreadable card cannot be moved', () => {
  const lvl = { key: 'flowie', meta: { applied: {} }, columns: [{ id: 'inbox' }, { id: 'active' }], cards: [
    { slug: 'old', column: 'inbox', title: 'Old', legacy: true, readable: true, sha256: 'a' },
    { slug: 'broken', column: 'inbox', title: 'Broken', legacy: false, readable: false, sha256: 'b' },
  ] }
  for (const card of boardModel(lvl, [], {}).columns[0].cards) assert.equal(makeMove({ level: 'flowie', card, to: 'active', nowMs: NOW, id: 'x' }), null)
})

test('what the snapshot contains, what a cancel undid and what depended on it are not drawn over it', () => {
  const intents = goldenList()
  const meta = { ...snapshot.metas[HIVE], applied: { 'i-mh2a0001-aaaa': { state: 'committed' } } }
  assert.deepEqual(activeIntents(intents, HIVE, meta).map(item => item.id), ['i-mh2a0002-bbbb'])
  assert.deepEqual(activeIntents(intents, 'flowie', snapshot.metas.flowie).map(item => item.id), ['i-mh2a0003-cccc'])
  const withCancel = [...intents, { id: 'i-zz-cancel', op: 'cancel', level: HIVE, target: { intent: 'i-mh2a0001-aaaa' }, status: 'pending', created_at: '2026-10-21T10:10:00Z' }]
  assert.deepEqual(activeIntents(withCancel, HIVE, snapshot.metas[HIVE]), [])
  const released = intents.map(item => (item.id === 'i-mh2a0001-aaaa' ? { ...item, ...releasePatch(NOW) } : item))
  assert.deepEqual(activeIntents(released, HIVE, snapshot.metas[HIVE]), [])
  assert.equal(waitingIntents(intents, 'flowie').length, 3)
  assert.equal(tabSummary(snapshot.metas, intents).flowie.waiting, 1) // the undone move no longer waits
  assert.equal(waitingCount(snapshot.metas, intents), 3)
  // since when changes wait: the undone move (10:08) is not the oldest of its level, the add (10:07) is
  assert.equal(tabSummary(snapshot.metas, intents).flowie.oldest, '2026-10-21T10:07:00.000Z')
  assert.equal(oldestWaiting(snapshot.metas, intents), '2026-10-21T10:05:00.000Z')
  assert.equal(oldestWaiting(snapshot.metas, []), null)
})

test('a claim shows who holds it, and an old one shows as stuck', () => {
  const claimed = goldenList().map(item => (item.id === 'i-mh2a0001-aaaa'
    ? { ...item, status: 'claimed', claim: { machine: 'laptop', claimed_at: '2026-10-21T10:20:00Z' } } : item))
  let card = boardModel(level(HIVE), claimed, { nowMs: NOW }).columns.flatMap(c => c.cards).find(c => c.slug === 'fix-channel-map')
  assert.equal(card.pending.state, 'pending') // the last waiting click decides: 0002 is still pending
  const only = claimed.filter(item => item.id === 'i-mh2a0001-aaaa')
  card = boardModel(level(HIVE), only, { nowMs: NOW }).columns.flatMap(c => c.cards).find(c => c.slug === 'fix-channel-map')
  assert.deepEqual([card.pending.state, card.pending.by], ['claimed', 'laptop'])
  card = boardModel(level(HIVE), only, { nowMs: NOW + 31 * 60000 }).columns.flatMap(c => c.cards).find(c => c.slug === 'fix-channel-map')
  assert.equal(card.pending.state, 'stale')
})

test('outcomes say what happened, conflicts first', () => {
  const done = [
    { id: 'i-1-aaaa', level: 'flowie', status: 'done', target: { slug: 'write-intro' }, created_at: '2026-10-21T09:00:00Z', outcome: { result: 'applied', state: 'pushed', at: '2026-10-21T09:05:00Z' } },
    { id: 'i-2-bbbb', level: 'flowie', status: 'done', target: { slug: 'write-intro' }, created_at: '2026-10-21T09:01:00Z', outcome: { result: 'conflict', reason: 'the task is now in done', at: '2026-10-21T09:05:00Z' } },
  ]
  assert.deepEqual(recentOutcomes(done, 'flowie', NOW).map(item => item.id), ['i-2-bbbb', 'i-1-aaaa'])
  assert.equal(outcomeText(done[0].outcome), 'applied — pushed')
  assert.equal(outcomeText(done[1].outcome), 'not applied: the task is now in done')
  const card = boardModel(level('flowie'), done, { nowMs: NOW }).columns.flatMap(c => c.cards).find(c => c.slug === 'write-intro')
  assert.equal(card.outcome.result, 'conflict')
  assert.equal(recentOutcomes(done, 'flowie', NOW + 2 * 86400000).length, 0)
})

test('overdue and "this project" come from the viewer and the open tab', () => {
  const lvl = level('flowie')
  const board = boardModel(lvl, [], { today: '2026-10-21', focusProject: 'oddball-eeg', nowMs: NOW })
  const card = board.columns.find(column => column.id === 'inbox').cards[0]
  assert.equal(card.slug, 'read-n2pc-review')
  assert.ok(card.overdue && card.mine)
  assert.ok(!boardModel(lvl, [], { today: '2026-10-19' }).columns.find(column => column.id === 'inbox').cards[0].overdue)
  assert.ok(!isOverdue('2026-10-01', '2026-10-21', true))
  assert.equal(daysUntil('2026-10-24', '2026-10-21'), 3)
  const filtered = boardModel(lvl, [], { filter: { overdue: true }, today: '2026-10-21' })
  assert.equal(filtered.total, 1)
  assert.equal(boardModel(lvl, [], { hiddenColumns: ['ready', 'meeting'] }).columns.some(column => column.id === 'ready'), false)
  const wip = boardModel(lvl, [], { wip: { active: 0, inbox: 1 }, today: '2026-10-21' }).columns.find(column => column.id === 'inbox')
  assert.equal(wip.wip, 1)
  assert.deepEqual(lanes([{ project: 'b' }, { project: null }, { project: 'a' }], 'project').map(lane => lane.name), ['a', 'b', null])
})

test('the keyboard moves a card one column at a time', () => {
  const columns = level(HIVE).columns
  assert.equal(neighbourColumn(columns, 'inbox', 1), 'active')
  assert.equal(neighbourColumn(columns, 'inbox', -1), null)
  assert.equal(neighbourColumn(columns, 'done', 1), null) // the archive is no keyboard target
})

test('markdown renders as tokens only: HTML stays text and only http links leave', () => {
  const page = level('flowie').pages.find(item => item.id === 'concepts/alpha-oscillations')
  const blocks = parseMarkdown(page.body)
  assert.equal(blocks[0].type, 'paragraph')
  assert.deepEqual(blocks[0].inline[0], { type: 'text', text: '<script>alert(1)</script> ' })
  assert.deepEqual(blocks[0].inline[1], { type: 'strong', children: [{ type: 'text', text: 'Alpha' }] })
  assert.equal(safeHref('javascript:alert(1)'), null)
  assert.deepEqual(parseInline('[x](javascript:alert(1))').map(token => token.type), ['text'])
  assert.deepEqual(parseInline('[doi](https://doi.org/10.1/x)')[0], { type: 'link', href: 'https://doi.org/10.1/x', children: [{ type: 'text', text: 'doi' }] })
  const n2pc = parseMarkdown(level('flowie').pages.find(item => item.id === 'concepts/n2pc').body)
  const tokens = n2pc.flatMap(block => block.inline || [])
  assert.ok(tokens.some(token => token.type === 'wikilink' && token.target === 'concepts/alpha-oscillations'))
  assert.ok(tokens.some(token => token.type === 'wikilink' && token.target === '' && token.label === 'a gap'))
  assert.ok(tokens.some(token => token.type === 'local' && token.name === 'figure-1.png'))
  const mixed = parseMarkdown('# Title\n\n- one\n  - two\n- [x] done\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n```\n<b>code</b>\n```\n\n> quoted\n\n---\n1. first')
  assert.deepEqual(mixed.map(block => block.type), ['heading', 'list', 'table', 'code', 'quote', 'hr', 'list'])
  assert.equal(mixed[1].items[0].children[0].inline[0].text, 'two')
  assert.equal(mixed[1].items[1].task, true)
  assert.equal(mixed[3].text, '<b>code</b>')
  assert.ok(mixed[6].ordered)
})

test('markdown always ends: a pipe that starts no table, a one-dash delimiter row, a quoted pipe', () => {
  // run under a time limit: a parser that stops advancing would otherwise hang the test (and the page's tab)
  const context = createContext({ parse: parseMarkdown, text: '' })
  const script = new Script('parse(text)')
  const within = text => {
    context.text = text
    return script.runInContext(context, { timeout: 1000 })
  }
  const types = blocks => blocks.map(block => block.type)
  assert.deepEqual(types(within('text\n| just a pipe')), ['paragraph'])
  assert.equal(within('text\n| just a pipe')[0].inline[0].text, 'text | just a pipe')
  const table = within('| Left | Center |\n|:-|:-:|\n| a | b |')
  assert.deepEqual(types(table), ['table'])
  assert.deepEqual([table[0].header.length, table[0].rows.length], [2, 1])
  assert.deepEqual(types(within('| A | B |')), ['paragraph'])
  assert.deepEqual(types(within('intro\n| A | B |')), ['paragraph'])
  assert.deepEqual(types(within('> | quoted')), ['quote'])
  assert.deepEqual(types(within('> | quoted')[0].blocks), ['paragraph'])
  assert.equal(within('# a b').length, 1)
  assert.deepEqual(types(within('text\n| a | b |\n|---|---|\n| 1 | 2 |')), ['paragraph', 'table'])
  // every mix of three block starters ends
  const starts = ['|', '| a |', '|:-|', '---', '> ', '> |', '# ', '# x', '- ', '1. ', '```', 'text', '', '  x', '|-']
  for (const a of starts) for (const b of starts) for (const c of starts) assert.ok(Array.isArray(within([a, b, c].join('\n'))))
  assert.ok(isDelimiterRow('|:-|:-:|') && isDelimiterRow('---|---') && isDelimiterRow('| --- | :--: |'))
  assert.ok(!isDelimiterRow('| a |') && !isDelimiterRow('|') && !isDelimiterRow(''))
})

test('the wiki index groups pages by type and searches titles, tags and summaries', () => {
  const groups = wikiIndex(level('flowie').pages, '')
  assert.deepEqual(groups.map(group => group.type), ['concept', 'method'])
  assert.deepEqual(wikiIndex(level('flowie').pages, 'lateral')[0].pages.map(page => page.id), ['concepts/n2pc'])
})

test('the project panel: phases with a word for each mark, dates ahead from the viewer\'s date', () => {
  const panel = level('project+oddball-eeg').panel
  assert.deepEqual(phaseMap(panel).map(item => `${item.glyph} ${item.phase} ${item.state}`), [
    '● ideation visited', '● preregistration visited', '○ data not started', '◉ data-analyze current', '○ paper not started'])
  assert.deepEqual(upcomingDates(panel, '2026-10-21').map(row => `${row.date} ${row.days}`), ['2026-12-01 41', '2027-06-30 252'])
  assert.equal(panel.prereg.by_person, false)
})

test('preferences: what is stored is checked, and the tabs follow them', () => {
  assert.deepEqual(normalizePrefs({ theme: 'neon', order: ['x y', 'flowie'], wip: { flowie: { inbox: 3, active: -1 } } }),
    { ...defaultPrefs(), order: ['flowie'], wip: { flowie: { inbox: 3 } } })
  assert.deepEqual(levelOrder(snapshot.metas, defaultPrefs()), ['flowie', HIVE, 'project+oddball-eeg'])
  assert.deepEqual(levelOrder(snapshot.metas, { order: ['project+oddball-eeg'], hidden: ['flowie'] }), ['project+oddball-eeg', HIVE])
})

test('the page template keeps the safety rules (the same rules workbench.py check enforces)', () => {
  const html = readFileSync(join(root, 'skills', 'neuroflow-core', 'assets', 'workbench', 'workbench.html'), 'utf8')
  const logic = readFileSync(join(root, 'skills', 'neuroflow-core', 'assets', 'workbench', 'workbench.mjs'), 'utf8')
  for (const text of [html, logic]) {
    assert.doesNotMatch(text, /\binnerHTML\b|\bouterHTML\b|\binsertAdjacentHTML\b|\bdocument\.write\b|\beval\s*\(|\bnew\s+Function\b/)
    assert.doesNotMatch(text, /\bfetch\s*\(|\bXMLHttpRequest\b|\bWebSocket\b/)
  }
  assert.doesNotMatch(html, /<script\b[^>]*\bsrc\s*=/i)
  for (const link of html.match(/<link\b[^>]*>/gi) || []) assert.match(link, /href="https:\/\/fonts\.(googleapis|gstatic)\.com/)
  assert.match(html, /<meta name="neuroflow:workbench-template" content="\d+">/)
  assert.match(html, /\/\* @@WORKBENCH_LOGIC@@ \*\//)
  assert.doesNotMatch(logic, /^\s*(import|export\s+(default|\{|\*))/m)
})
