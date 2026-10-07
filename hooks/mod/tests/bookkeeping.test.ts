import { describe, expect, mock, test } from 'claude-code/testing'

import { hasSessionLineSince, missingFlowRows } from '../features/bookkeeping'
import { statusLine, atLeast, doctorText } from '../features/status'
import type { NfSnapshot } from '../../../types'
import { fakeFs } from './fakefs'

describe('bookkeeping helpers', () => {
  test('finds files missing from their flow.md', () => {
    const rows = missingFlowRows('/p', [
      '/p/.neuroflow/data-analyze/analysis-plan.md',
      '/p/.neuroflow/data-analyze/summary.md',
      '/p/.neuroflow/sessions/2026-10-07.md',
      '/p/.neuroflow/data-analyze/flow.md',
      '/p/scripts/analysis/x.py',
    ], { '/p/.neuroflow/data-analyze/flow.md': '| analysis-plan.md | Plan | 2026-10-01 |\n' }, 'data-analyze', '2026-10-07')
    expect(rows).toEqual({ '/p/.neuroflow/data-analyze/flow.md': ['| summary.md | Written by /neuroflow:data-analyze (auto) | 2026-10-07 |'] })
  })

  test('a session line after the command started counts', () => {
    const log = '## 09:00 — [paper] session started\n## 10:42 — [data-analyze] plan written\n'
    expect(hasSessionLineSince(log, ['data-analyze'], '10:40')).toBe(true)
    expect(hasSessionLineSince(log, ['data-analyze'], '10:43')).toBe(false)
    expect(hasSessionLineSince(log, ['paper'], '09:30')).toBe(false)
  })
})

describe('status', () => {
  test('silent when nothing needs attention, short when something does', () => {
    const base = { ethics: null, prereg: null, deadlines: [], problems: [] } as unknown as NfSnapshot
    expect(statusLine(base, [])).toBe(undefined)
    const busy = { ...base, deadlines: [{ date: '2026-10-08', what: 'Abstract', gates: null, daysLeft: 1 }, { date: '2026-10-09', what: 'Poster', gates: null, daysLeft: 2 }], problems: ['legacy'] } as NfSnapshot
    expect(statusLine(busy, ['guards'])).toBe('neuroflow: ⚠ Abstract tomorrow (+1) · ! config needs attention — /neuroflow:doctor · ! mod: 1 feature(s) degraded — /neuroflow:doctor')
  })

  test('version floor and doctor text', () => {
    expect(atLeast('2.1.300', '2.1.292')).toBe(true)
    expect(atLeast('2.1.30', '2.1.292')).toBe(false)
    expect(doctorText([{ id: 'mod', status: 'ok', message: 'live' }], { checks: [{ id: 'git', status: 'warn', message: 'no remote' }] }, null))
      .toBe('neuroflow doctor — some warnings\n✔ live\n⚠ no remote')
  })
})

describe('bookkeeping in a session', () => {
  test('fills the missing session line and flow row after a command turn', { options: { runtime: 'on' } }, async ($, on) => {
    const root = '/work/proj'
    const fs = fakeFs(on, {
      [`${root}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nactive_phase: data-analyze\n---\n',
      [`${root}/.neuroflow/data-analyze/flow.md`]: '| File / Folder | Description | Last changed |\n|---|---|---|\n',
    }, root)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: new Date(2026, 9, 7, 10, 15).getTime() })
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('command.run', () => ({ text: '', ref: 1 }))
    on('tool.call', () => ({ result: 'ok', text: 'ok' }))
    on('ui.status', () => ({ value: undefined }))
    on('ui.log', () => ({ value: undefined }))
    on('turn.complete', () => ({ text: 'done' }))
    await $.session.start({ cwd: root, surface: 'terminal', isInteractive: true })
    await $.command.run({ command: 'neuroflow:data-analyze', args: '' })
    await $.tool.call({ tool: 'Write', file_path: `${root}/.neuroflow/data-analyze/analysis-plan.md`, content: '# Plan' } as never)
    await $.turn.complete({ reason: 'answer', answer: 'done', durationMs: 1, isAborted: false, turnId: 't1' } as never)
    // the tag is the command's phase, read from commands/data-analyze.md in the plugin folder
    expect(fs.files[`${root}/.neuroflow/sessions/2026-10-07.md`]).toBe('## 10:15 — [data-analyze] /neuroflow:data-analyze wrote 1 file(s) (auto)\n')
    expect(fs.files[`${root}/.neuroflow/data-analyze/flow.md`]).toContain('| analysis-plan.md | Written by /neuroflow:data-analyze (auto) | 2026-10-07 |')
  })
})
