import { describe, expect, mock, test } from 'claude-code/testing'

import { parseDraft } from '../features/bookkeeping'
import { fakeFs } from './fakefs'

describe('decision drafter', () => {
  test('parses one decision or none', () => {
    expect(parseDraft('{"statement": "Use FDR (BH) across electrodes", "reasoning": "Bonferroni was too conservative for 64 channels."}'))
      .toEqual({ statement: 'Use FDR (BH) across electrodes', reasoning: 'Bonferroni was too conservative for 64 channels.' })
    expect(parseDraft('Here you go: {"statement": null}')).toBe(null)
    expect(parseDraft('no json at all')).toBe(null)
    expect(parseDraft('{"statement": "  "}')).toBe(null)
  })

  test('drafts after a command turn that logged no decision, and a keep press writes it', { options: { runtime: 'on' } }, async ($, on) => {
    const root = '/work/proj'
    const fs = fakeFs(on, {
      [`${root}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nactive_phase: data-analyze\n---\n',
      [`${root}/.neuroflow/sessions/2026-10-07.md`]: '## 10:00 — [data-analyze] plan written\n',
      '*/commands/data-analyze.md': '---\nname: data-analyze\nphase: data-analyze\nlifecycle: full\nnext:\n  - paper\n---\n',
    }, root)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: new Date(2026, 9, 7, 10, 30).getTime() })
    mock.store(on)
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('session.model', () => ({ value: 'claude-test' }))
    on('command.run', () => ({ text: '', ref: 1 }))
    on('turn.complete', () => ({ text: 'done' }))
    on('ui.status', () => ({ value: undefined }))
    on('ui.toast', () => ({ value: undefined }))
    on('ui.log', () => ({ value: undefined }))
    on('model.complete', () => ({
      value: {
        isAnswered: true,
        text: '{"statement": "Use FDR (BH) across electrodes", "reasoning": "Bonferroni was too conservative for 64 channels."}',
        usage: { input_tokens: 10, output_tokens: 10, cache_creation_input_tokens: 0, cache_read_input_tokens: 0 },
      },
    }))
    await $.session.start({ cwd: root, surface: 'terminal', isInteractive: true })
    await $.command.run({ command: 'neuroflow:data-analyze', args: '' })
    await $.turn.complete({ reason: 'answer', answer: 'We compared Bonferroni and FDR. '.repeat(10), durationMs: 1, isAborted: false, turnId: 't1' } as never)

    const band = await $.ui.mount({
      plugin: 'neuroflow',
      surface: 'terminal',
      component: 'AbovePrompt',
      props: { hasSurvey: false, isWorking: false, maxRows: 4, bodyColumns: 100, scroll: { offset: 0, bodyRows: 4 }, view: {} },
    } as never)
    const drawn = JSON.stringify(await band.drawn())
    expect(drawn).toContain('decision drafted for ')
    expect(drawn).toContain('Use FDR (BH) across electrodes')
    await band.press({ key: 'nf-draft-keep' })
    const line = JSON.parse(fs.files[`${root}/.neuroflow/reasoning/data-analyze.jsonl`].trim())
    expect(line.statement).toBe('Use FDR (BH) across electrodes')
    expect(line.drafted_by).toBe('mod')
    expect(line.approved_by).toBe('person')
  })
})
