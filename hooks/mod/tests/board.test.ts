import { describe, expect, mock, test } from 'claude-code/testing'

import type { NfMeeting, NfSnapshot } from '../../../types'
import { parseMeeting } from '../lib/project'
import { buildBoard, cardLine, columnsFromConfig, parseTask } from '../lib/tasks'
import { bandItems, meetingWhen, parseWellbeing } from '../features/views'
import { fakeFs } from './fakefs'

describe('task board', () => {
  test('cards, overdue first, done counted not drawn', () => {
    const columns = columnsFromConfig(null)
    const today = '2026-10-07'
    const late = parseTask('---\ntitle: "Rerun ICA"\nowner: li\ndue: 2026-10-01\n---\n', 'rerun-ica', today, false)
    const fine = parseTask('---\ntitle: Spin tests\ndue: 2026-10-20\n---\n', 'spin-tests', today, false)
    const legacy = parseTask('---\ntitle: QC report\nassignee: jana\n---\n', 'qc-report', today, false)
    expect(late).toEqual({ slug: 'rerun-ica', title: 'Rerun ICA', owner: 'li', due: '2026-10-01', overdue: true })
    expect(legacy.owner).toBe('jana')
    const board = buildBoard(columns, { active: [fine, late], review: [legacy], done: [fine, fine] })
    expect(board.columns.map(column => column.id)).toEqual(['inbox', 'active', 'review'])
    expect(board.columns[1].cards[0].slug).toBe('rerun-ica')
    expect(board.done).toBe(2)
    expect(cardLine(late)).toBe('⚠ Rerun ICA @li due 10-01')
    expect(columnsFromConfig('{"columns":[{"id":"todo"},{"id":"doing","label":"Doing"}]}').map(c => c.label)).toEqual(['todo', 'Doing'])
  })
})

describe('meetings and wellbeing in the band', () => {
  test('meeting facts and band actions', () => {
    const now = new Date(2026, 9, 7, 13, 0).getTime()
    const meeting = parseMeeting('---\ntitle: Lab meeting\ndate: 2026-10-07T14:00:00\nclosed: ""\n---\n## Actions\n- [ ] send data\n', 'lab-2026-10-07', 'project', now) as NfMeeting
    expect(meeting.startsIn).toBe(60)
    expect(meeting.openActions).toBe(1)
    expect(meetingWhen(60, meeting.date, now)).toBe('in 60 min')
    expect(meetingWhen(20 * 60, '2026-10-08T09:00:00', now)).toBe('tomorrow 09:00')
    const snap = { ethics: null, prereg: null, deadlines: [], problems: [], loops: [], meetings: [meeting], phase: null, recommendedPhases: [], loadedAt: now } as unknown as NfSnapshot
    const items = bandItems(snap, true)
    expect(items[0].text).toBe('meeting "Lab meeting" in 60 min')
    expect(items[0].actions?.map(action => action.args)).toEqual(['--prepare lab-2026-10-07', '--notes lab-2026-10-07'])
  })

  test('wellbeing input: three scores 1–10, notes optional', () => {
    expect(parseWellbeing('3 6 7')).toEqual({ anxiety: 3, energy: 6, happiness: 7, notes: '' })
    expect(parseWellbeing('3,6,7 slept badly')).toEqual({ anxiety: 3, energy: 6, happiness: 7, notes: 'slept badly' })
    expect(parseWellbeing('3 6 11')).toBe(null)
    expect(parseWellbeing('fine')).toBe(null)
  })

  test('/neuroflow:tasks opens the board from the files', { options: { runtime: 'observe' } }, async ($, on) => {
    const root = '/work/proj'
    fakeFs(on, {
      [`${root}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nactive_phase: data\n---\n',
      [`${root}/.neuroflow/tasks/active/rerun-ica.md`]: '---\ntitle: Rerun ICA\nstatus: active\ndue: 2026-10-01\n---\n',
    }, root)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: new Date(2026, 9, 7, 9, 0).getTime() })
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('ui.open', () => ({ value: { isPlaced: true } }))
    await $.session.start({ cwd: root, surface: 'terminal', isInteractive: true })
    const answer = await $.command.run({ command: 'neuroflow:tasks', args: '' })
    expect(answer.text).toContain('Task board open')
    const pane = await $.ui.mount({
      plugin: 'neuroflow', surface: 'terminal', component: 'Pane', requestId: 'nf-board',
      props: { title: 'tasks', isFocused: true, bodyColumns: 90, placement: 'inline', scroll: { offset: 0, bodyRows: 20 }, view: {} },
    } as never)
    expect(JSON.stringify(await pane.drawn())).toContain('⚠ Rerun ICA due 10-01')
  })
})
