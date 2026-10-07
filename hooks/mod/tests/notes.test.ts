import { describe, expect, mock, test } from 'claude-code/testing'

import { appendToSection, captureCount, captureTarget, ideaLine, isCaptureExit } from '../features/capture'
import { fakeFs } from './fakefs'

describe('capture helpers', () => {
  test('idea lines, flags and exits', () => {
    expect(ideaLine(new Date(2026, 9, 7, 9, 5).getTime(), 'data', '  try CSD instead  ')).toBe('- 2026-10-07 09:05 [data] try CSD instead')
    expect(captureTarget('')).toBe(null)
    expect(captureTarget('.neuroflow/meetings/lab-2026-10-07.md#Notes\n')).toEqual({ path: '.neuroflow/meetings/lab-2026-10-07.md', section: '## Notes' })
    expect(captureTarget('.neuroflow/notes/notes-x-draft.md')).toEqual({ path: '.neuroflow/notes/notes-x-draft.md', section: null })
    expect(isCaptureExit('done')).toBe(true)
    expect(isCaptureExit('/neuroflow:phase')).toBe(true)
    expect(isCaptureExit('done with the pilot, start the main study')).toBe(false)
  })

  test('appends inside the right section', () => {
    const doc = '# Lab meeting\n\n## Agenda\n- x\n\n## Notes\n\n[09:00] start\n\n## Actions\n- [ ] y\n'
    const next = appendToSection(doc, '## Notes', '[09:05] second')
    expect(next).toBe('# Lab meeting\n\n## Agenda\n- x\n\n## Notes\n\n[09:00] start\n[09:05] second\n\n## Actions\n- [ ] y\n')
    expect(captureCount(next, '## Notes')).toBe(2)
    expect(appendToSection('# Draft\n', null, '[09:00] a')).toBe('# Draft\n[09:00] a\n')
  })
})

describe('zero-turn capture in a session', () => {
  const root = '/work/proj'
  const setup = (files: Record<string, string>) => files

  test('`idea:` goes to the project inbox and never reaches the model', { options: { runtime: 'observe' } }, async ($, on) => {
    const fs = fakeFs(on, setup({ [`${root}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nactive_phase: data\n---\n' }), root)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: new Date(2026, 9, 7, 9, 5).getTime() })
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    let reachedModel = false
    on('prompt.submit', ($, e) => {
      reachedModel = true
      return { text: e.text }
    })
    await $.session.start({ cwd: root, surface: 'terminal', isInteractive: true })
    const result = await $.prompt.submit({ text: 'idea: test the effect in older adults', origin: { kind: 'composer' } } as never)
    expect(reachedModel).toBe(false)
    expect(JSON.stringify(result)).toContain('Idea saved — inbox: 1')
    expect(fs.files[`${root}/.neuroflow/notes/ideas-inbox.md`]).toBe('# Ideas inbox\n\n- 2026-10-07 09:05 [data] test the effect in older adults\n')
  })

  test('live capture writes each message into the meeting notes; done goes through', { options: { runtime: 'observe' } }, async ($, on) => {
    const meeting = `${root}/.neuroflow/meetings/lab.md`
    const fs = fakeFs(on, setup({
      [`${root}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nactive_phase: data\n---\n',
      [`${root}/.neuroflow/notes/.capturing`]: '.neuroflow/meetings/lab.md#Notes\n',
      [meeting]: '# Lab\n\n## Notes\n\n## Actions\n',
    }), root)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: new Date(2026, 9, 7, 14, 30).getTime() })
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    const reached: string[] = []
    on('prompt.submit', ($, e) => {
      reached.push(e.text)
      return { text: e.text }
    })
    await $.session.start({ cwd: root, surface: 'terminal', isInteractive: true })
    const first = await $.prompt.submit({ text: 'delete the old epochs before Friday', origin: { kind: 'composer' } } as never)
    expect(JSON.stringify(first)).toContain('✓ 1')
    expect(fs.files[meeting]).toBe('# Lab\n\n## Notes\n[14:30] delete the old epochs before Friday\n\n## Actions\n')
    await $.prompt.submit({ text: 'done', origin: { kind: 'composer' } } as never)
    expect(reached).toEqual(['done'])
  })
})
