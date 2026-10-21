import { describe, expect, mock, test } from 'claude-code/testing'

import { BAND, DASHBOARD_TABS, DIGITS, NAV, VIEW_KEYS, gridNeighbour, isPastTypeThrough, lineNeighbour, paneRows, tabNeighbour } from '../lib/keys'
import type { View } from '../lib/keys'
import { bandPlan, cells, fit } from '../lib/layout'
import { buttons, hotkeys, keyProblems } from './drawn'
import { fakeFs } from './fakefs'

describe('the key registry', () => {
  test('a key is one digit or one lowercase letter; the band has letters only; a key means one thing in every view', () => {
    const meaning = new Map<string, string>()
    for (const [view, keys] of Object.entries(VIEW_KEYS)) {
      for (const [key, what] of Object.entries(keys)) {
        expect(/^([0-9]|[a-z])$/.test(key), `${view}: ${key}`).toBe(true)
        // Charter rule 7: a digit typed into an empty prompt would press a band Button.
        if (view === 'band') expect(/^[0-9]$/.test(key), `band: ${key}`).toBe(false)
        const before = meaning.get(key)
        if (before !== undefined) expect(what, `${key} in the ${view} view`).toBe(before)
        meaning.set(key, what)
      }
    }
  })

  test('the NAV letters mean what NAV says wherever a view offers them, and nothing else takes them', () => {
    const nav: Record<string, string> = { [NAV.left]: 'left', [NAV.down]: 'down', [NAV.up]: 'up', [NAV.right]: 'right', [NAV.reread]: 'reread', [NAV.close]: 'close', [NAV.yes]: 'yes', [NAV.no]: 'no', [NAV.cancel]: 'cancel' }
    expect(new Set(Object.values(NAV)).size).toBe(Object.values(NAV).length)
    for (const [view, keys] of Object.entries(VIEW_KEYS)) {
      for (const [key, what] of Object.entries(keys)) if (key in nav) expect(what, `${view}: ${key}`).toBe(nav[key])
    }
    // The band shares y, n and x with the panes, and means the same by them.
    expect([BAND.keep, BAND.drop, BAND.dismiss]).toEqual([NAV.yes, NAV.no, NAV.cancel])
    const bandLetters = Object.values(BAND)
    expect(new Set(bandLetters).size).toBe(bandLetters.length)
    expect(bandLetters.filter(letter => Object.values(NAV).includes(letter as never)).sort()).toEqual(['n', 'x', 'y'])
  })

  test('the dashboard tabs are the digits 1–6, now first, under the ids /neuroflow:dashboard <tab> takes', () => {
    expect(DASHBOARD_TABS.map(tab => `${tab.digit} ${tab.id}`)).toEqual(['1 now', '2 phase', '3 deadlines', '4 integrity', '5 tasks', '6 loop'])
    expect(DASHBOARD_TABS.every((tab, at) => tab.digit === DIGITS[at])).toBe(true)
    expect(tabNeighbour('now', -1)).toBe('loop')
    expect(tabNeighbour('loop', 1)).toBe('now')
    expect(tabNeighbour('phase', 1)).toBe('deadlines')
  })

  test('the ring steps: a list and a grid of element keys', () => {
    expect(lineNeighbour(['a', 'b', 'c'], null, 1)).toBe('a')
    expect(lineNeighbour(['a', 'b', 'c'], 'a', 1)).toBe('b')
    expect(lineNeighbour(['a', 'b', 'c'], 'c', 1)).toBe('c')
    expect(lineNeighbour(['a', 'b', 'c'], 'a', -1)).toBe('a')
    expect(lineNeighbour(['a', 'b'], 'elsewhere', -1)).toBe('a')
    expect(lineNeighbour([], null, 1)).toBe(null)
    const grid = [['a1', 'a2', 'a3'], [], ['c1']]
    expect(gridNeighbour(grid, null, 'down')).toBe('a1')
    expect(gridNeighbour(grid, 'a1', 'down')).toBe('a2')
    expect(gridNeighbour(grid, 'a3', 'down')).toBe('a3')
    // An empty column is stepped over; a shorter column takes its last card.
    expect(gridNeighbour(grid, 'a3', 'right')).toBe('c1')
    expect(gridNeighbour(grid, 'c1', 'left')).toBe('a1')
    expect(gridNeighbour(grid, 'c1', 'right')).toBe('c1')
    expect(gridNeighbour([[], []], null, 'down')).toBe(null)
  })

  test('keys typed through a focused open are dropped for TYPE_THROUGH_MS', () => {
    expect(isPastTypeThrough(1_000, undefined)).toBe(true)
    expect(isPastTypeThrough(1_399, 1_000)).toBe(false)
    expect(isPastTypeThrough(1_400, 1_000)).toBe(true)
  })

  test('a view asks for fewer rows on a short terminal (24 rows over SSH)', () => {
    expect([paneRows('dashboard', null), paneRows('dashboard', 40), paneRows('dashboard', 24)]).toEqual([18, 18, 10])
    expect([paneRows('board', null), paneRows('board', 29), paneRows('board', 30)]).toEqual([16, 10, 16])
    expect([paneRows('wiki', 24), paneRows('xray', 24), paneRows('paper', 24), paneRows('picker', 24)]).toEqual([9, 10, 9, 9])
  })
})

describe('layout', () => {
  test('a text is cut to its width with an ellipsis, never mid-character', () => {
    expect(fit('Rerun ICA on sub-07', 10)).toBe('Rerun ICA…')
    expect(fit('short', 10)).toBe('short')
    expect(fit('a b c d', 4)).toBe('a b…')
    expect(fit('abc', 1)).toBe('…')
    expect(fit('abc', 0)).toBe('')
    expect(cells('◆ ⚠ Check stats')).toBe(15)
  })

  test('the band\'s one row at 75 and 115 cells: the most urgent item and its keys stay, the chord hint goes first', () => {
    const hint = '^X Tab: keys'
    // 80 columns: a deadline, its band keys and the hint fit.
    expect(bandPlan({ columns: 75, items: 1, total: 1, buttons: ['d: dashboard', 'x: hide today'], hint })).toEqual({ items: 1, more: 0, hint: true })
    // A meeting brings two keys of its own: the hint gives way, the item keeps its room.
    expect(bandPlan({ columns: 75, items: 1, total: 3, buttons: ['p: prepare', 'o: notes', 'd: dashboard', 'x: hide today'], hint })).toEqual({ items: 1, more: 2, hint: false })
    // 120 columns, a normal band: two items, the rest counted, the hint too.
    expect(bandPlan({ columns: 115, items: 2, total: 5, buttons: ['d: dashboard', 'x: hide today'], hint })).toEqual({ items: 2, more: 3, hint: true })
    // Below BAND_SECOND_ITEM a normal band shows one item.
    expect(bandPlan({ columns: 100, items: 2, total: 5, buttons: ['d: dashboard', 'x: hide today'], hint })).toEqual({ items: 1, more: 4, hint: true })
    // Learned: no hint at any width.
    expect(bandPlan({ columns: 160, items: 1, total: 1, buttons: ['d: dashboard'], hint: null }).hint).toBe(false)
  })
})

// ── every view, as drawn ──────────────────────────────────────────────────────────────────────

const ROOT = '/work/proj'
/** A project with something on every band and dashboard row: a deadline, two meetings, wiki cards, an update. */
const FULL: Record<string, string> = {
  [`${ROOT}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nproject_name: Oddball\nactive_phase: data\nplugin_version: 0.2.21\nrecommended_phases: [data, data-analyze, paper]\n---\n',
  // Not named "neuroflow": the pattern also matches the project, which would then read as the plugin's own repo.
  '*/.claude-plugin/plugin.json': '{"name": "neuroflow-fixture", "version": "0.2.22"}',
  [`${ROOT}/.neuroflow/timeline.md`]: '| Date | What | Gates |\n|---|---|---|\n| 2026-10-08 | Abstract deadline | paper |\n',
  [`${ROOT}/.neuroflow/meetings/lab-2026-10-07.md`]: '---\ntitle: Lab meeting\ndate: 2026-10-07T14:00\n---\n',
  [`${ROOT}/.neuroflow/meetings/pi-2026-10-06.md`]: '---\ntitle: PI check-in\ndate: 2026-10-06T10:00\n---\n## Actions\n- [ ] send data\n- [ ] book the room\n',
  [`${ROOT}/.neuroflow/wiki/.pending/2026-10-07-fdr.md`]: '---\ntitle: FDR\nstatus: pending\n---\nbody\n',
  [`${ROOT}/.neuroflow/wiki/.pending/2026-10-07-window.md`]: '---\ntitle: Window\nstatus: pending\n---\nbody\n',
  [`${ROOT}/.neuroflow/tasks/active/rerun-ica.md`]: '---\ntitle: Rerun ICA\nstatus: active\n---\n',
  [`${ROOT}/.neuroflow/data/flow.md`]: '# data\n',
}
const SURFACES = ['terminal', 'desktop', 'vscode', 'mobile'] as const
const bandProps = (bodyColumns: number) => ({ hasSurvey: false, isWorking: false, maxRows: 4, bodyColumns, scroll: { offset: 0, bodyRows: 4 }, view: {} })
const paneProps = (isFocused = true) => ({ title: 'neuroflow', isFocused, bodyColumns: 116, placement: 'inline', scroll: { offset: 0, bodyRows: 18 }, view: {} })

describe('every drawn hotkey comes from the registry', () => {
  test('the band, the dashboard on every tab, the boards and the picker, on every surface', { options: { runtime: 'observe', band: 'normal' } }, async ($, on) => {
    fakeFs(on, FULL, ROOT)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: new Date(2026, 9, 7, 13, 0).getTime() })
    mock.store(on)
    on('session.start', ($$, e) => ({ cwd: e.cwd }))
    on('ui.open', () => ({ value: { isPlaced: true } }))
    on('ui.close', () => ({ value: undefined }))
    on('ui.status', () => ({ value: undefined }))
    on('command.run', () => ({ text: '', ref: 1 }))
    await $.session.start({ cwd: ROOT, surface: 'terminal', isInteractive: true })
    const check = async (component: 'AbovePrompt' | 'Pane', view: View, requestId: string | undefined, surfaces: readonly (typeof SURFACES)[number][], props: unknown) => {
      const drawn: unknown[] = []
      for (const surface of surfaces) {
        const ui = await $.ui.mount({ plugin: 'neuroflow', surface, component, ...(requestId === undefined ? {} : { requestId }), props } as never)
        const tree = await ui.drawn()
        expect(keyProblems(tree, view), `${view} on ${surface}`).toEqual([])
        drawn.push(tree)
        await ui.unmount()
      }
      return drawn
    }
    // The band is raised on the terminal and desktop only.
    for (const columns of [75, 116, 160]) {
      const [terminal] = await check('AbovePrompt', 'band', undefined, ['terminal', 'desktop'], bandProps(columns))
      expect(hotkeys(terminal).some(key => /^[0-9]$/.test(key))).toBe(false)
      // The ring starts on the dashboard key when the band takes the keys: never on one that writes or consents.
      expect(buttons(terminal).filter(button => button.autoFocus).map(button => button.key)).toEqual(['nf-band-dashboard'])
    }
    for (const tab of DASHBOARD_TABS) {
      await $.command.run({ command: 'neuroflow:dashboard', args: tab.id } as never)
      for (const tree of await check('Pane', 'dashboard', 'nf-dashboard', SURFACES, paneProps())) {
        // The shown tab is text, every other one its digit.
        const digits = hotkeys(tree).filter(key => /^[0-9]$/.test(key))
        expect(digits, tab.id).toEqual(DASHBOARD_TABS.filter(item => item.id !== tab.id).map(item => item.digit))
        expect(JSON.stringify(tree)).toContain(`${tab.digit}: ${tab.label}`)
      }
    }
    await $.command.run({ command: 'neuroflow:tasks', args: '' } as never)
    await check('Pane', 'board', 'nf-board', SURFACES, paneProps())
    await $.command.run({ command: 'neuroflow:phase', args: '' } as never)
    await check('Pane', 'picker', 'nf-phase', SURFACES, paneProps())
  })
})
