import { describe, expect, mock, test } from 'claude-code/testing'

import { commandKeys, parseScholarReport, scholarProblems, staleWatchQueries } from '../features/capture'
import { fakeFs } from './fakefs'

describe('command keys', () => {
  test('reads requires and next', () => {
    const keys = commandKeys('---\nname: data-analyze\nrequires:\n  - .neuroflow/data-preprocess/preprocess-report.md\nnext:\n  - paper\n  - /neuroflow:write-report\n---\nbody')
    expect(keys).toEqual({ requires: ['.neuroflow/data-preprocess/preprocess-report.md'], next: ['paper', 'write-report'] })
    expect(commandKeys(null)).toEqual({ requires: [], next: [] })
  })
})

describe('scholar report', () => {
  test('parses the last REPORT line', () => {
    const text = 'Found 12 papers.\n[REPORT downloaded=2 files=.neuroflow/ideation/papers/smith2024/smith2024.pdf, .neuroflow/ideation/papers/lee2023/lee2023.txt stubs=10]'
    expect(parseScholarReport(text)).toEqual({
      downloaded: 2,
      files: ['.neuroflow/ideation/papers/smith2024/smith2024.pdf', '.neuroflow/ideation/papers/lee2023/lee2023.txt'],
      stubs: 10,
    })
    expect(parseScholarReport('[REPORT downloaded=0 files=none stubs=3]')).toEqual({ downloaded: 0, files: [], stubs: 3 })
    expect(parseScholarReport('no report')).toBe(null)
  })

  test('names every claim the disk does not back', () => {
    const report = { downloaded: 3, files: ['.neuroflow/ideation/papers/a/a.pdf', '.neuroflow/ideation/papers/b/b.pdf'], stubs: 0 }
    const problems = scholarProblems(report, {
      '.neuroflow/ideation/papers/a/a.pdf': { exists: true, head: '<!DOCTYPE html>' },
      '.neuroflow/ideation/papers/b/b.pdf': { exists: false, head: null },
    })
    expect(problems).toEqual([
      'the report says 3 download(s) but lists 2 file(s)',
      '.neuroflow/ideation/papers/a/a.pdf is not a PDF (it does not start with %PDF-)',
      '.neuroflow/ideation/papers/b/b.pdf does not exist',
    ])
    expect(scholarProblems({ downloaded: 1, files: ['.neuroflow/ideation/papers/a/a.pdf'], stubs: 0 }, { '.neuroflow/ideation/papers/a/a.pdf': { exists: true, head: '%PDF-1.7' } })).toEqual([])
  })
})

describe('literature watch', () => {
  test('counts queries not checked for a week', () => {
    const watch = '| Query | Tools | Pinned | Last checked | Free alert |\n|---|---|---|---|---|\n| P300 | search_pubmed | 2026-09-01 | 2026-09-20 | PubMed |\n| N400 | search_pubmed | 2026-10-01 | 2026-10-05 | none |\n'
    expect(staleWatchQueries(watch, new Date(2026, 9, 7, 12).getTime())).toEqual({ count: 1, oldest: 17 })
  })
})

describe('requires in a session', () => {
  test('a missing required input becomes a note for the model, never a block', { options: { runtime: 'observe' } }, async ($, on) => {
    const root = '/work/proj'
    fakeFs(on, {
      [`${root}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nactive_phase: data-analyze\n---\n',
      '*/commands/data-analyze.md': '---\nname: data-analyze\nphase: data-analyze\nlifecycle: full\nrequires:\n  - .neuroflow/data-preprocess/preprocess-report.md\nnext:\n  - paper\n---\n',
    }, root)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: 0 })
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('command.run', () => ({ text: '', ref: 1 }))
    on('prompt.submit', ($, e) => ({ text: e.text, context: e.context }))
    on('ui.toast', () => ({ value: undefined }))
    on('ui.status', () => ({ value: undefined }))
    await $.session.start({ cwd: root, surface: 'terminal', isInteractive: true })
    const result = await $.command.run({ command: 'neuroflow:data-analyze', args: '' })
    expect(result.ref).toBe(1)
    // The engine runs the command, then submits its prompt: the note rides on the prompt.
    const prompt = await $.prompt.submit({ text: '/neuroflow:data-analyze', origin: { kind: 'composer' }, wait: false } as never)
    expect((prompt.context ?? []).join(' ')).toContain('expects .neuroflow/data-preprocess/preprocess-report.md')
    // Typed without the plugin prefix, the same command gets the same note.
    await $.command.run({ command: 'neuroflow:data-analyze', args: '' })
    const bare = await $.prompt.submit({ text: '/data-analyze', origin: { kind: 'composer' }, wait: false } as never)
    expect((bare.context ?? []).join(' ')).toContain('expects .neuroflow/data-preprocess/preprocess-report.md')
  })
})
