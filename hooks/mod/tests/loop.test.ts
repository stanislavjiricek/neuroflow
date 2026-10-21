import { describe, expect, mock, test } from 'claude-code/testing'

import { costCapUsd, driveToast, iterationPrompt, stopReason } from '../features/loop'
import { buttons, hotkeys, keyProblems } from './drawn'
import { fakeFs } from './fakefs'

describe('driver rules', () => {
  test('cost caps are read only when they are money', () => {
    expect(costCapUsd('20 USD')).toBe(20)
    expect(costCapUsd('$7.5')).toBe(7.5)
    expect(costCapUsd('n/a')).toBe(null)
    expect(costCapUsd('200k tokens')).toBe(null)
    expect(costCapUsd(undefined)).toBe(null)
  })

  test('the next iteration starts only on a clean status', () => {
    expect(stopReason(0, { findings: [] }, 1, 20)).toBe(null)
    expect(stopReason(1, { findings: [{ kind: 'cap', detail: 'max_iterations reached (30 of 30 this run) - stop the loop' }] }, null, null))
      .toBe('cap: max_iterations reached (30 of 30 this run) - stop the loop')
    expect(stopReason(2, null, null, null)).toBe('the loop bookkeeping (ar.py status) could not run')
    expect(stopReason(0, { findings: [] }, 21, 20)).toBe('max_cost reached (21.00 of 20 USD this run)')
  })

  test('each driven turn asks for exactly one iteration', () => {
    const text = iterationPrompt({ name: 'connectivity', location: 'scripts/analysis/connectivity_autoresearch/' }, 3)
    expect(text).toContain('driven turn 3')
    expect(text).toContain('exactly ONE iteration')
  })
})

describe('driving in a session', () => {
  const root = '/work/proj'
  const files = {
    [`${root}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nactive_phase: data-analyze\n---\n',
    [`${root}/.neuroflow/data-analyze/autoresearch-loops.md`]: '| Name | Location | Iterations | Best | Status |\n|---|---|---|---|---|\n| connectivity | scripts/analysis/connectivity_autoresearch/ | 4 | v003 | running |\n',
  }

  test('drive → one prompt per answered turn → stops at a cap', { options: { runtime: 'on' } }, async ($, on) => {
    fakeFs(on, files, root)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: new Date(2026, 9, 7, 11, 0).getTime() })
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('session.usage', () => ({ value: { startedAt: 0, context: {}, rateLimits: [] } }))
    on('ui.toast', () => ({ value: undefined }))
    on('ui.status', () => ({ value: undefined }))
    on('ui.log', () => ({ value: undefined }))
    on('turn.complete', () => ({ text: 'done' }))
    const submitted: string[] = []
    on('prompt.submit', ($, e) => {
      submitted.push(e.text)
      return { text: e.text }
    })
    const statuses = [
      { exitCode: 0, stdout: JSON.stringify({ caps: { max_consecutive_errors: '3', max_cost: 'n/a' }, findings: [] }), stderr: '' },
      { exitCode: 0, stdout: JSON.stringify({ findings: [] }), stderr: '' },
      { exitCode: 1, stdout: JSON.stringify({ findings: [{ kind: 'cap', detail: 'max_iterations reached' }] }), stderr: '' },
    ]
    // Only ar.py answers from the queue; other scripts (the guards' start checks) find no Python.
    on('process.run', ($, e) => ({ value: (/ar\.py/.test(JSON.stringify(e)) ? statuses.shift() : undefined) ?? { exitCode: 2, stdout: '', stderr: 'x' } }))
    let ranProse = ''
    on('command.run', ($, e) => {
      ranProse = (e as { args: string }).args
      return { text: '', ref: 7 }
    })
    await $.session.start({ cwd: root, surface: 'terminal', isInteractive: true })

    await $.command.run({ command: 'neuroflow:autoresearch', args: 'drive connectivity' })
    expect(ranProse).toBe('drive connectivity')
    expect(submitted.length).toBe(0)

    await $.turn.complete({ reason: 'answer', answer: 'iteration 5 done', durationMs: 1, isAborted: false, turnId: 't1' } as never)
    expect(submitted.length).toBe(1)
    expect(submitted[0]).toContain('driven turn 2')

    await $.turn.complete({ reason: 'answer', answer: 'iteration 6 done', durationMs: 1, isAborted: false, turnId: 't2' } as never)
    expect(submitted.length).toBe(1)
    expect((await $.command.run({ command: 'neuroflow:autoresearch', args: 'stop' })).text).toBe('No loop is being driven.')
  })

  test('the band shows the drive with x to stop it, and the start says which keys stop it', { options: { runtime: 'on' } }, async ($, on) => {
    const fs = fakeFs(on, files, root)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: new Date(2026, 9, 7, 11, 0).getTime() })
    mock.store(on)
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('session.usage', () => ({ value: { startedAt: 0, context: {}, rateLimits: [] } }))
    const toasts: string[] = []
    on('ui.toast', ($, e) => {
      toasts.push(JSON.stringify(e))
      return { value: undefined }
    })
    on('ui.status', () => ({ value: undefined }))
    on('ui.log', () => ({ value: undefined }))
    on('process.run', ($, e) => ({
      value: /ar\.py/.test(JSON.stringify(e))
        ? { exitCode: 0, stdout: JSON.stringify({ caps: { max_consecutive_errors: '3', max_cost: 'n/a' }, findings: [] }), stderr: '' }
        : { exitCode: 2, stdout: '', stderr: 'x' },
    }))
    on('command.run', () => ({ text: '', ref: 7 }))
    await $.session.start({ cwd: root, surface: 'terminal', isInteractive: true })
    await $.command.run({ command: 'neuroflow:autoresearch', args: 'drive connectivity' })
    expect(toasts.join(' ')).toContain('or your stop (Esc, /neuroflow:autoresearch stop, or ^X Tab then x on the band)')
    const band = await $.ui.mount({
      plugin: 'neuroflow', surface: 'terminal', component: 'AbovePrompt',
      props: { hasSurvey: false, isWorking: true, maxRows: 4, bodyColumns: 116, scroll: { offset: 0, bodyRows: 4 }, view: {} },
    } as never)
    const tree = await band.drawn()
    expect(JSON.stringify(tree)).toContain('↻ driving autoresearch \\"connectivity\\" · turn 1')
    expect(buttons(tree).map(button => `${button.hotkey}: ${button.label}`)).toEqual(['x: stop', 'd: dashboard'])
    expect(keyProblems(tree, 'band')).toEqual([])
    await band.press({ key: 'nf-drive-stop' })
    expect(Object.values(fs.files).join('\n')).toContain('driver stopped after 1 turn(s): stopped by the person')
    expect((await $.command.run({ command: 'neuroflow:autoresearch', args: 'stop' })).text).toBe('No loop is being driven.')
    await band.unmount()
  })

  test('with band: off the start names only the stops that exist: Esc and /neuroflow:autoresearch stop', { options: { runtime: 'on', band: 'off' } }, async ($, on) => {
    fakeFs(on, files, root)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: new Date(2026, 9, 7, 11, 0).getTime() })
    mock.store(on)
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('session.usage', () => ({ value: { startedAt: 0, context: {}, rateLimits: [] } }) as never)
    const toasts: string[] = []
    on('ui.toast', ($, e) => {
      toasts.push(String((e as unknown as { text: string }).text))
      return { value: undefined }
    })
    // Where the mod draws no band, the engine draws its own.
    on('ui.render', () => ({ type: 'Text', children: ['(the engine draws its own band)'] }) as never)
    on('ui.status', () => ({ value: undefined }))
    on('ui.log', () => ({ value: undefined }))
    on('process.run', ($, e) => ({
      value: /ar\.py/.test(JSON.stringify(e))
        ? { exitCode: 0, stdout: JSON.stringify({ caps: { max_consecutive_errors: '3', max_cost: 'n/a' }, findings: [] }), stderr: '' }
        : { exitCode: 2, stdout: '', stderr: 'x' },
    }) as never)
    on('command.run', () => ({ text: '', ref: 7 }))
    await $.session.start({ cwd: root, surface: 'terminal', isInteractive: true })
    await $.command.run({ command: 'neuroflow:autoresearch', args: 'drive connectivity' } as never)
    expect(toasts).toContain('neuroflow: driving "connectivity" — one iteration per turn until a cap, 3 errored turns in a row, or your stop (Esc or /neuroflow:autoresearch stop)')
    expect(driveToast('connectivity', 3, 'quiet')).toContain('or your stop (Esc, /neuroflow:autoresearch stop, or ^X Tab then x on the band)')
    // No band is drawn: there is no x to press.
    const band = await $.ui.mount({
      plugin: 'neuroflow', surface: 'terminal', component: 'AbovePrompt',
      props: { hasSurvey: false, isWorking: true, maxRows: 4, bodyColumns: 116, scroll: { offset: 0, bodyRows: 4 }, view: {} },
    } as never)
    expect(hotkeys(await band.drawn())).toEqual([])
    await band.unmount()
    expect((await $.command.run({ command: 'neuroflow:autoresearch', args: 'stop' } as never)).text).toBe('Stopped driving "connectivity". The current iteration, if any, finishes; no new one starts.')
  })

  test('an interrupted turn ends the drive, and observe mode never drives', { options: { runtime: 'observe' } }, async ($, on) => {
    fakeFs(on, files, root)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: 0 })
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    await $.session.start({ cwd: root, surface: 'terminal', isInteractive: true })
    const answer = await $.command.run({ command: 'neuroflow:autoresearch', args: 'drive connectivity' })
    expect(answer.text).toContain('needs the neuroflow mod runtime set to on')
  })
})
