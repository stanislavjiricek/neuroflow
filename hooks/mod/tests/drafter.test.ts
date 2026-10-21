import { describe, expect, mock, test } from 'claude-code/testing'

import { parseDraft } from '../features/bookkeeping'
import { answerAsks } from './ask'
import { buttons, hotkeys, keyProblems, lines } from './drawn'
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
    const toasts: string[] = []
    on('ui.toast', ($, e) => {
      toasts.push(JSON.stringify(e))
      return { value: undefined }
    })
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
    const tree = await band.drawn()
    const drawn = JSON.stringify(tree)
    expect(drawn).toContain('decision drafted for ')
    expect(drawn).toContain('Use FDR (BH) across electrodes')
    // The band's keys work once it holds the keyboard: the toast says how, and names the keys that work there.
    expect(toasts.join(' ')).toContain('keep or drop it on the band: ^X Tab, then y or n')
    // y keeps, n drops, d opens the dashboard; the ring starts on d, never on keep.
    expect(hotkeys(tree)).toEqual(['y', 'n', 'd'])
    expect(keyProblems(tree, 'band')).toEqual([])
    expect(buttons(tree).filter(button => button.autoFocus).map(button => button.key)).toEqual(['nf-band-dashboard'])
    await band.press({ key: 'nf-draft-keep' })
    const line = JSON.parse(fs.files[`${root}/.neuroflow/reasoning/data-analyze.jsonl`].trim())
    expect(line.statement).toBe('Use FDR (BH) across electrodes')
    expect(line.drafted_by).toBe('mod')
    expect(line.approved_by).toBe('person')
  })

  test('the dashboard\'s now tab lists the drafted decision; Enter on drop discards it after a yes, and a bare letter never does', { options: { runtime: 'on' } }, async ($, on) => {
    const root = '/work/proj'
    const fs = fakeFs(on, {
      [`${root}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nactive_phase: data-analyze\n---\n',
      [`${root}/.neuroflow/sessions/2026-10-07.md`]: '## 10:00 — [data-analyze] plan written\n',
      '*/commands/data-analyze.md': '---\nname: data-analyze\nphase: data-analyze\nlifecycle: full\n---\n',
    }, root)
    mock.env(on, { HOME: '/home/me' })
    const clock = mock.clock(on, { now: new Date(2026, 9, 7, 10, 30).getTime() })
    mock.store(on)
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('session.model', () => ({ value: 'claude-test' }))
    on('command.run', () => ({ text: '', ref: 1 }))
    on('turn.complete', () => ({ text: 'done' }))
    on('ui.status', () => ({ value: undefined }))
    on('ui.toast', () => ({ value: undefined }))
    on('ui.log', () => ({ value: undefined }))
    on('ui.open', () => ({ value: { isPlaced: true } }))
    const dialog = answerAsks(on)
    on('model.complete', () => ({
      value: {
        isAnswered: true,
        text: '{"statement": "Use FDR (BH) across electrodes", "reasoning": "Bonferroni was too conservative."}',
        usage: { input_tokens: 10, output_tokens: 10, cache_creation_input_tokens: 0, cache_read_input_tokens: 0 },
      },
    }))
    await $.session.start({ cwd: root, surface: 'terminal', isInteractive: true })
    await $.command.run({ command: 'neuroflow:data-analyze', args: '' })
    await $.turn.complete({ reason: 'answer', answer: 'We compared Bonferroni and FDR. '.repeat(10), durationMs: 1, isAborted: false, turnId: 't1' } as never)
    await $.command.run({ command: 'neuroflow:dashboard', args: '' })
    const pane = await $.ui.mount({
      plugin: 'neuroflow', surface: 'terminal', component: 'Pane', requestId: 'nf-dashboard',
      props: { title: 'neuroflow', isFocused: true, bodyColumns: 116, placement: 'inline', scroll: { offset: 0, bodyRows: 18 }, view: {} },
    } as never)
    const tree = await pane.drawn()
    expect(lines(tree)).toContain('✎ decision drafted for data-analyze: Use FDR (BH) across electrodes')
    expect(buttons(tree).filter(button => button.key.startsWith('nf-now-draft-')).map(button => [button.key, button.hotkey])).toEqual([
      ['nf-now-draft-keep', undefined],
      ['nf-now-draft-drop', undefined],
    ])
    // Enter on keep asks first, the safe answer on top: a stray Enter in the dialog keeps nothing.
    await clock.advance(500)
    await pane.press({ key: 'nf-now-draft-keep' })
    expect(dialog.asked.map(asked => [asked.question, asked.options, asked.header])).toEqual([
      ['Keep "Use FDR (BH) across electrodes" in the reasoning log, as a decision you approved?', ['Not now', 'Keep it'], 'Decision'],
    ])
    expect(fs.files[`${root}/.neuroflow/reasoning/data-analyze.jsonl`]).toBe(undefined)
    expect(JSON.stringify(await pane.drawn())).toContain('decision drafted')
    // Drop, after the person's yes, discards it.
    dialog.answer(asked => (asked.options.includes('Drop it') ? 'Drop it' : asked.options[0] ?? ''))
    await clock.advance(500)
    await pane.press({ key: 'nf-now-draft-drop' })
    expect(dialog.asked[1]).toEqual({ question: 'Drop the drafted decision "Use FDR (BH) across electrodes"? It is not written anywhere.', options: ['Keep it waiting', 'Drop it'], header: 'Decision' })
    expect(fs.files[`${root}/.neuroflow/reasoning/data-analyze.jsonl`]).toBe(undefined)
    expect(JSON.stringify(await pane.drawn())).not.toContain('decision drafted')
    await pane.unmount()
  })

  test('keep on the now tab writes the decision only after the person\'s yes, and as approved by them', { options: { runtime: 'on' } }, async ($, on) => {
    const root = '/work/proj'
    const fs = fakeFs(on, {
      [`${root}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nactive_phase: data-analyze\n---\n',
      [`${root}/.neuroflow/sessions/2026-10-07.md`]: '## 10:00 — [data-analyze] plan written\n',
      '*/commands/data-analyze.md': '---\nname: data-analyze\nphase: data-analyze\nlifecycle: full\n---\n',
    }, root)
    mock.env(on, { HOME: '/home/me' })
    const clock = mock.clock(on, { now: new Date(2026, 9, 7, 10, 30).getTime() })
    mock.store(on)
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('session.model', () => ({ value: 'claude-test' }))
    on('command.run', () => ({ text: '', ref: 1 }))
    on('turn.complete', () => ({ text: 'done' }))
    on('ui.status', () => ({ value: undefined }))
    on('ui.toast', () => ({ value: undefined }))
    on('ui.log', () => ({ value: undefined }))
    on('ui.open', () => ({ value: { isPlaced: true } }))
    const dialog = answerAsks(on, () => 'Keep it')
    on('model.complete', () => ({
      value: {
        isAnswered: true,
        text: '{"statement": "Use FDR (BH) across electrodes", "reasoning": "Bonferroni was too conservative."}',
        usage: { input_tokens: 10, output_tokens: 10, cache_creation_input_tokens: 0, cache_read_input_tokens: 0 },
      },
    }))
    await $.session.start({ cwd: root, surface: 'terminal', isInteractive: true })
    await $.command.run({ command: 'neuroflow:data-analyze', args: '' })
    await $.turn.complete({ reason: 'answer', answer: 'We compared Bonferroni and FDR. '.repeat(10), durationMs: 1, isAborted: false, turnId: 't1' } as never)
    await $.command.run({ command: 'neuroflow:dashboard', args: '' })
    const pane = await $.ui.mount({
      plugin: 'neuroflow', surface: 'terminal', component: 'Pane', requestId: 'nf-dashboard',
      props: { title: 'neuroflow', isFocused: true, bodyColumns: 116, placement: 'inline', scroll: { offset: 0, bodyRows: 18 }, view: {} },
    } as never)
    await clock.advance(500)
    await pane.press({ key: 'nf-now-draft-keep' })
    expect(dialog.asked).toHaveLength(1)
    const line = JSON.parse(fs.files[`${root}/.neuroflow/reasoning/data-analyze.jsonl`].trim())
    expect([line.statement, line.drafted_by, line.approved_by]).toEqual(['Use FDR (BH) across electrodes', 'mod', 'person'])
    await pane.unmount()
  })
})
