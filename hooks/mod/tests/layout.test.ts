import { describe, expect, test } from 'claude-code/testing'

import {
  align,
  bandItemWidths,
  bandPlan,
  boardLayout,
  cells,
  fit,
  flowLine,
  isCompact,
  moreLabel,
  pad,
  pageNote,
  pageOf,
  paneColumns,
  rule,
  ruler,
  tabStrip,
  widthClass,
} from '../lib/layout'
import { PHASE_GLYPH, phaseLegend, phaseMap, phaseNodes, phaseSummary, shortName, travelledTo } from '../lib/phases'

/** The dashboard's tabs as the engine draws them: hotkey, colon, label. */
const TABS = ['1: now', '2: phase', '3: deadlines', '4: integrity', '5: tasks', '6: loop']
const RECOMMENDED = ['ideation', 'preregistration', 'data', 'data-analyze', 'paper']
const VISITED = ['ideation', 'preregistration', 'data', 'data-analyze']

describe('widths and heights', () => {
  test('narrow under 56 body cells, medium 56–89, wide from 90; compact under 30 rows', () => {
    expect([44, 55, 56, 75, 89, 90, 115].map(widthClass)).toEqual(['narrow', 'narrow', 'medium', 'medium', 'medium', 'wide', 'wide'])
    expect([isCompact(24), isCompact(29), isCompact(30), isCompact(null), isCompact(undefined)]).toEqual([true, true, false, false, false])
  })

  test('a view asks for its columns when it opens docked', () => {
    expect([paneColumns('dashboard'), paneColumns('board'), paneColumns('picker')]).toEqual([64, 84, 56])
  })

  test('text is cut to its width with an ellipsis, never mid-character; padded and aligned to a width', () => {
    expect(fit('Rerun ICA on sub-07', 10)).toBe('Rerun ICA…')
    expect(fit('short', 10)).toBe('short')
    expect(fit('a b c d', 4)).toBe('a b…')
    expect(fit('abc', 1)).toBe('…')
    expect(fit('abc', 0)).toBe('')
    expect(cells('◆ ⚠ Check stats')).toBe(15)
    expect(pad('abc', 5)).toBe('abc  ')
    expect(pad('abcdef', 4)).toBe('abc…')
    expect(align('left', 'right', 12)).toBe('left   right')
    expect(align('a long left part', 'right', 12)).toBe('a lo…  right')
    expect(align('x', 'too long right', 10)).toBe('too long…')
    expect(align('only left', '', 6)).toBe('only…')
  })
})

describe('the dashboard\'s tab strip', () => {
  test('one row with the widest gap that fits, a heavy rule under the shown tab, at 76 and 116 cells', () => {
    expect(rule(10, 2, 3)).toBe('──━━━─────')
    expect(tabStrip(TABS, 0, 76)).toEqual({ gap: 3, fits: true, rule: `${'━'.repeat(6)}${'─'.repeat(70)}` })
    // 3: deadlines starts after `1: now` and `2: phase` and their gaps of three.
    expect(tabStrip(TABS, 2, 116)).toEqual({ gap: 3, fits: true, rule: `${'─'.repeat(20)}${'━'.repeat(12)}${'─'.repeat(84)}` })
    // A 64-cell dock: gaps of two still keep one row.
    expect(tabStrip(TABS, 5, 64)).toEqual({ gap: 2, fits: true, rule: `${'─'.repeat(56)}${'━'.repeat(7)}─` })
    expect(tabStrip(TABS, 0, 60).gap).toBe(1)
  })

  test('narrow: the row wraps and the rule is plain', () => {
    expect(tabStrip(TABS, 1, 44)).toEqual({ gap: 1, fits: false, rule: '─'.repeat(44) })
  })
})

describe('the phase flow line', () => {
  const nodes = phaseNodes('data-analyze', VISITED, RECOMMENDED)

  test('the one glyph legend: ◉ current, ● visited, → recommended next, ○ not started', () => {
    expect(PHASE_GLYPH).toEqual({ current: '◉', visited: '●', recommended: '→', other: '○' })
    expect(nodes.map(node => `${node.glyph} ${node.id}`)).toEqual(['● ideation', '● preregistration', '● data', '◉ data-analyze', '→ paper'])
    expect(phaseMap('data-analyze', VISITED, RECOMMENDED)).toBe('● ideation  ● preregistration  ● data  ◉ data-analyze  → paper')
    expect(phaseSummary('data-analyze', VISITED, RECOMMENDED)).toBe('● ideation ─ ● prereg ─ ● data ─ ◉ analyze ─ → paper')
    expect(phaseLegend(nodes)).toBe('◉ current  ● visited  → recommended next')
    expect(phaseLegend(phaseNodes('notes', [], ['ideation']))).toBe('◉ current  → recommended next')
    expect([shortName('data-preprocess'), shortName('write-report'), shortName('paper')]).toEqual(['preprocess', 'report', 'paper'])
  })

  test('without recommended phases, the visited ones in canonical order; the current one is always drawn', () => {
    expect(phaseMap('data', ['data', 'ideation'], [])).toBe('● ideation  ◉ data')
    expect(phaseMap('notes', [], ['ideation', 'paper'])).toBe('→ ideation  → paper  ◉ notes')
    expect(phaseMap(null, [], [])).toBe('')
    expect(travelledTo(nodes)).toBe(3)
    expect(travelledTo(phaseNodes(null, ['ideation'], ['ideation', 'paper']))).toBe(0)
    expect(travelledTo(phaseNodes(null, [], ['ideation']))).toBe(-1)
  })

  test('at 76 cells: heavy up to the current phase, light after it, a short name under each glyph', () => {
    const line = flowLine(nodes, travelledTo(nodes), 76)
    expect(line).toEqual({
      head: `●${'━'.repeat(14)}●${'━'.repeat(14)}●${'━'.repeat(14)}◉`,
      tail: `${'─'.repeat(14)}→`,
      labels: `${pad('ideation', 15)}${pad('prereg', 15)}${pad('data', 15)}${pad('analyze', 15)}paper`,
    })
    expect(cells(`${line?.head}${line?.tail}`)).toBe(61)
  })

  test('at 116 cells the cells widen; under nine cells a phase it gives way to the word list', () => {
    const wide = flowLine(nodes, 3, 116)
    expect(wide?.head).toBe(`${`●${'━'.repeat(22)}`.repeat(3)}◉`)
    expect(wide?.tail).toBe(`${'─'.repeat(22)}→`)
    expect(flowLine(nodes, 3, 44)).toBe(null)
    expect(flowLine(nodes, 3, 45)?.labels.startsWith('ideation prereg')).toBe(true)
    // Nothing travelled yet: all of it is still to come.
    expect(flowLine(nodes, -1, 76)?.head).toBe('')
    expect(flowLine([], 0, 76)).toBe(null)
  })
})

describe('the dates ruler', () => {
  const marks = [
    { days: 55, glyph: '·', rank: 2 },
    { days: 1, glyph: '·', rank: 2 },
    { days: 1, glyph: '⚠', rank: 0 },
    { days: 12, glyph: '▸', rank: 1 },
    { days: 80, glyph: '·', rank: 2 },
  ]

  test('one cell a day, a tick each week, as many weeks as fit: 56 days at 76 cells, 98 at 116', () => {
    const medium = ruler(76, marks)
    expect(medium?.axis).toBe(`today ┼${'──────┬'.repeat(8)} +56 d`)
    expect(cells(medium?.axis ?? '')).toBe(69)
    // The most urgent date wins a shared day; one past the end is left to the list.
    expect(medium?.marks).toBe(`${' '.repeat(6)} ⚠${' '.repeat(10)}▸${' '.repeat(42)}·`)
    expect(ruler(116, [])).toEqual({ axis: `today ┼${'──────┬'.repeat(14)} +98 d`, marks: '', days: 98 })
  })

  test('narrow: four weeks in a 44-cell dock; no ruler where under two weeks fit', () => {
    expect(ruler(44, [])?.axis).toBe(`today ┼${'──────┬'.repeat(4)} +28 d`)
    expect(ruler(26, marks)).toBe(null)
  })
})

describe('the board', () => {
  test('a grid where each column keeps 18 cells, at most 36; a list under that', () => {
    expect(boardLayout(76, 3)).toEqual({ kind: 'grid', columnWidth: 24 })
    expect(boardLayout(116, 5)).toEqual({ kind: 'grid', columnWidth: 22 })
    expect(boardLayout(116, 3)).toEqual({ kind: 'grid', columnWidth: 36 })
    expect(boardLayout(76, 4)).toEqual({ kind: 'grid', columnWidth: 18 })
    expect(boardLayout(76, 5)).toEqual({ kind: 'list' })
    expect(boardLayout(44, 3)).toEqual({ kind: 'list' })
  })

  test('a column pages five cards at a time: the page holding the ring\'s card, what comes before and after it', () => {
    const twelve = Array.from({ length: 12 }, (_, at) => at)
    const second = pageOf(twelve, 7)
    expect(second).toEqual({ shown: [5, 6, 7, 8, 9], from: 6, to: 10, total: 12, before: 5, after: 2 })
    expect(pageNote(second)).toBe('6–10 of 12')
    expect(pageNote(pageOf(twelve, -1))).toBe('+7 more')
    expect(pageNote(pageOf(twelve, 11))).toBe('11–12 of 12')
    expect(pageNote(pageOf([1, 2, 3], 0))).toBe(null)
    expect(pageOf([], 0)).toEqual({ shown: [], from: 0, to: 0, total: 0, before: 0, after: 0 })
  })
})

describe('the band', () => {
  const hint = '^X Tab: keys'
  const meeting = ['p: prepare', 'o: notes', 'd: dashboard', 'x: hide today']
  const meetingShort = ['p: prepare', 'o: notes', 'd: dashboard', 'x: hide']

  test('one row at 75 cells: the mark, the most urgent item and its keys stay; the hint goes first, then the long labels', () => {
    expect(bandPlan({ columns: 75, items: 1, total: 1, buttons: ['d: dashboard', 'x: hide today'], hint, lead: 2 })).toEqual({ items: 1, more: 0, hint: true, short: false, room: 30 })
    // A meeting brings two keys of its own: the hint gives way, then `x: hide` and `+2` keep the item its room.
    expect(bandPlan({ columns: 75, items: 1, total: 3, buttons: meeting, short: meetingShort, hint, lead: 2 })).toEqual({ items: 1, more: 2, hint: false, short: true, room: 24 })
    // Without short labels the item truncates.
    expect(bandPlan({ columns: 75, items: 1, total: 3, buttons: meeting, hint })).toEqual({ items: 1, more: 2, hint: false, short: false, room: 15 })
    expect([moreLabel(2, false), moreLabel(2, true), moreLabel(0, true)]).toEqual(['+2 more', '+2', ''])
  })

  test('at 115 cells a normal band shows two items, the rest counted, and the hint; below 110 it shows one', () => {
    expect(bandPlan({ columns: 115, items: 2, total: 5, buttons: ['d: dashboard', 'x: hide today'], hint, lead: 2 })).toEqual({ items: 2, more: 3, hint: true, short: false, room: 59 })
    expect(bandPlan({ columns: 100, items: 2, total: 5, buttons: ['d: dashboard', 'x: hide today'], hint })).toEqual({ items: 1, more: 4, hint: true, short: false, room: 48 })
    // Learned: no hint at any width.
    expect(bandPlan({ columns: 160, items: 1, total: 1, buttons: ['d: dashboard'], hint: null }).hint).toBe(false)
  })

  test('two items share the room: the first keeps its whole text while the second keeps 24 cells', () => {
    const deadline = '⚠ Abstract deadline — tomorrow'
    const ethics = '▸ ethics approval expires — in 12 days'
    expect(bandItemWidths(59, [deadline, ethics])).toEqual([30, 29])
    expect(bandItemWidths(40, [deadline, ethics])).toEqual([16, 24])
    expect(bandItemWidths(80, [deadline, 'short'])).toEqual([30, 5])
    expect(bandItemWidths(13, [deadline])).toEqual([13])
    expect(bandItemWidths(-4, [deadline])).toEqual([0])
  })
})
