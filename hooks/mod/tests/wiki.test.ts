import { describe, expect, mock, test } from 'claude-code/testing'

import { captureAllowed, cardText, parseCard, parseJudge, setCardStatus, slugify, takenTitles } from '../lib/wikiqueue'
import { answerAsks } from './ask'
import { buttons, lines } from './drawn'
import { fakeFs } from './fakefs'

/** A card file from an earlier day, already settled by the person. */
const settledCard = (title: string, status: 'accepted' | 'skipped'): string =>
  setCardStatus(cardText({ title, type: 'decision', evidence: 'reasoning/data-analyze.jsonl (2026-10-01 entry)', captured: '2026-10-01T09:00', by: 'mod', status: 'pending', body: 'An earlier card.' }), status)

describe('wiki review queue', () => {
  test('a card round-trips through its file format; a missing status is pending', () => {
    const text = cardText({ title: 'Use FDR: across electrodes', type: 'decision', evidence: 'reasoning/data-analyze.jsonl (14:03 entry)', captured: '2026-10-07T14:05', by: 'mod', status: 'pending', body: 'Bonferroni was too conservative for 64 channels.' })
    const card = parseCard(text)
    expect(card).toMatchObject({ title: 'Use FDR: across electrodes', type: 'decision', by: 'mod', status: 'pending' })
    expect(card?.body).toBe('Bonferroni was too conservative for 64 channels.')
    expect(parseCard('---\ntitle: X\n---\nbody')?.status).toBe('pending')
    expect(parseCard(setCardStatus(text, 'skipped'))?.status).toBe('skipped')
    expect(parseCard('no frontmatter')).toBe(null)
  })

  test('slugs are short ASCII', () => {
    expect(slugify('Use FDR (BH) across 64 électrodes!')).toBe('use-fdr-bh-across-64-electrodes')
    expect(slugify('***')).toBe('card')
  })

  test('the judge answer keeps at most two cards with evidence, never results', () => {
    const answer = 'Here: {"cards": [' +
      '{"title": "FDR across electrodes", "type": "decision", "summary": "Chosen over Bonferroni.", "evidence": "entry 14:03"},' +
      '{"title": "No evidence", "type": "method", "summary": "x", "evidence": ""},' +
      '{"title": "Cluster threshold", "type": "results", "summary": "y", "evidence": "entry 14:05"},' +
      '{"title": "Baseline window", "type": "method", "summary": "-200 to 0 ms.", "evidence": "entry 14:06"},' +
      '{"title": "Third", "type": "concept", "summary": "z", "evidence": "entry 14:07"}]}'
    const cards = parseJudge(answer)
    expect(cards.map(card => card.title)).toEqual(['FDR across electrodes', 'Baseline window'])
    expect(parseJudge('{"cards": []}')).toEqual([])
    expect(parseJudge('not json')).toEqual([])
  })

  test('every queued card blocks its title, whatever its status', () => {
    const queued = [parseCard(settledCard('FDR across electrodes', 'skipped')), parseCard(settledCard('Baseline window', 'accepted')), parseCard('no frontmatter')]
    const taken = takenTitles(['  ICA before epoching '], queued)
    expect([...taken].sort()).toEqual(['baseline window', 'fdr across electrodes', 'ica before epoching'])
  })

  test('capture needs the person\'s opt-in and a project that does not forbid it', () => {
    expect(captureAllowed('name: x\nwiki_auto: ask\n', null)).toBe(true)
    expect(captureAllowed('wiki_auto: off\n', null)).toBe(false)
    expect(captureAllowed(null, 'allow')).toBe(false)
    expect(captureAllowed('wiki_auto: ask\n', 'forbid')).toBe(false)
  })
})

describe('auto wiki in a session', () => {
  const root = '/work/proj'
  const files = {
    [`${root}/.neuroflow/project_config.md`]: '---\nnf_schema: 1\nactive_phase: data-analyze\n---\n',
    [`${root}/.neuroflow/reasoning/data-analyze.jsonl`]: '{"statement": "older decision"}\n',
    [`${root}/.neuroflow/sessions/2026-10-07.md`]: '## 14:00 — [data-analyze] started\n',
    '/home/me/.neuroflow/user.yaml': 'wiki_auto: ask\n',
    '*/commands/data-analyze.md': '---\nname: data-analyze\nphase: data-analyze\nlifecycle: full\n---\n',
  }

  test('a logged decision becomes a card; review opens it holding the keys; skip, on Enter and a yes, drops it for good', { options: { runtime: 'on' } }, async ($, on) => {
    const fs = fakeFs(on, files, root)
    mock.env(on, { HOME: '/home/me' })
    const clock = mock.clock(on, { now: new Date(2026, 9, 7, 14, 10).getTime() })
    mock.store(on)
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('session.model', () => ({ value: 'claude-test' }))
    on('ui.status', () => ({ value: undefined }))
    const toasts: string[] = []
    on('ui.toast', ($, e) => {
      toasts.push(JSON.stringify(e))
      return { value: undefined }
    })
    on('ui.log', () => ({ value: undefined }))
    const opens: { id: string; focus?: boolean; rows?: number }[] = []
    on('ui.open', ($, e) => {
      opens.push(e as never)
      return { value: undefined }
    })
    const closed: string[] = []
    on('ui.close', ($, e) => {
      closed.push(e.id)
      return { value: undefined }
    })
    on('turn.complete', () => ({ text: 'done' }))
    const ran: string[] = []
    on('command.run', ($, e) => {
      ran.push(`${e.command} ${e.args}`)
      return { text: '', ref: 1 }
    })
    // Every question answered as a stray Enter would answer it, unless the test answers otherwise.
    const dialog = answerAsks(on)
    const asked: string[] = []
    on('model.complete', ($, e) => {
      asked.push(String((e as unknown as { prompt: string }).prompt))
      return {
        value: {
          isAnswered: true,
          text: '{"cards": [{"title": "FDR across electrodes", "type": "decision", "summary": "Chosen over Bonferroni for 64 channels.", "evidence": "reasoning/data-analyze.jsonl, 14:05 entry"}]}',
          usage: { input_tokens: 1, output_tokens: 1, cache_creation_input_tokens: 0, cache_read_input_tokens: 0 },
        },
      }
    })
    await $.session.start({ cwd: root, surface: 'terminal', isInteractive: true })
    await $.command.run({ command: 'neuroflow:data-analyze', args: '' })
    fs.files[`${root}/.neuroflow/reasoning/data-analyze.jsonl`] += '{"statement": "Use FDR across electrodes", "reasoning": "Bonferroni too conservative"}\n'
    await $.turn.complete({ reason: 'answer', answer: 'done', durationMs: 1, isAborted: false, turnId: 't1' } as never)
    expect(asked.join(' ')).toContain('Use FDR across electrodes')
    expect(asked.join(' ')).not.toContain('older decision')
    const card = `${root}/.neuroflow/wiki/.pending/2026-10-07-fdr-across-electrodes.md`
    expect(parseCard(fs.files[card] ?? '')?.title).toBe('FDR across electrodes')
    expect(fs.files[`${root}/.neuroflow/wiki/.pending/.gitignore`]).toBe('*\n')
    // The toast names a path that works from the prompt; the band's key needs ^X Tab first.
    expect(toasts.join(' ')).toContain('1 wiki card to review — /neuroflow:wiki --review, or ^X Tab then w on the band')

    const review = await $.command.run({ command: 'neuroflow:wiki', args: '--review' })
    expect(review.text).toContain('1 wiki card waiting — Tab to accept (runs /neuroflow:wiki --add for the card) or skip (for good), Enter, then your yes')
    expect(opens.map(open => [open.id, open.focus, open.rows])).toEqual([['nf-wiki', true, 12]])
    ran.length = 0
    const pane = await $.ui.mount({
      plugin: 'neuroflow', surface: 'terminal', component: 'Pane', requestId: 'nf-wiki',
      props: { title: 'wiki cards', isFocused: true, bodyColumns: 100, placement: 'inline', scroll: { offset: 0, bodyRows: 12 }, view: {} },
    } as never)
    const drawn = await pane.drawn()
    expect(JSON.stringify(drawn)).toContain('FDR across electrodes')
    expect(lines(drawn)).toEqual(expect.arrayContaining(['◌ wiki cards', '1 of 1', 'DECISION', 'FDR across electrodes', 'EVIDENCE']))
    // Accept is a model turn and skip is for good: Enter on them and a yes, never a letter typed for the prompt.
    expect(Object.fromEntries(buttons(drawn).map(button => [button.key, button.hotkey]))).toEqual({ 'nf-wiki-accept': undefined, 'nf-wiki-skip': undefined, 'nf-wiki-close': 'q' })
    expect(lines(drawn)).toContain('tab, enter: act · esc: prompt')
    await clock.advance(500)
    // A stray Enter in either question writes nothing and starts nothing.
    await pane.press({ key: 'nf-wiki-accept' })
    await clock.advance(500)
    await pane.press({ key: 'nf-wiki-skip' })
    expect(dialog.asked).toEqual([
      { question: 'Accept "FDR across electrodes"? /neuroflow:wiki --add writes the page from the card, as a model turn.', options: ['Not now', 'Accept'], header: 'Wiki' },
      { question: 'Skip "FDR across electrodes" for good? A skipped card is never raised again.', options: ['Keep it waiting', 'Skip it'], header: 'Wiki' },
    ])
    expect(parseCard(fs.files[card])?.status).toBe('pending')
    expect([ran, closed]).toEqual([[], []])
    // The person's yes skips it.
    dialog.answer(() => 'Skip it')
    await clock.advance(500)
    await pane.press({ key: 'nf-wiki-skip' })
    expect(parseCard(fs.files[card])?.status).toBe('skipped')
  })

  test('a skipped or accepted card is never raised again', { options: { runtime: 'on' } }, async ($, on) => {
    const pending = `${root}/.neuroflow/wiki/.pending`
    const fs = fakeFs(on, {
      ...files,
      [`${pending}/.gitignore`]: '*\n',
      [`${pending}/2026-10-01-fdr-across-electrodes.md`]: settledCard('FDR across electrodes', 'skipped'),
      [`${pending}/2026-10-02-baseline-window.md`]: settledCard('Baseline window', 'accepted'),
    }, root)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: new Date(2026, 9, 7, 14, 10).getTime() })
    mock.store(on)
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('session.model', () => ({ value: 'claude-test' }))
    on('ui.status', () => ({ value: undefined }))
    on('ui.toast', () => ({ value: undefined }))
    on('ui.log', () => ({ value: undefined }))
    on('turn.complete', () => ({ text: 'done' }))
    on('command.run', () => ({ text: '', ref: 1 }))
    const asked: string[] = []
    on('model.complete', ($, e) => {
      asked.push(String((e as unknown as { prompt: string }).prompt))
      return {
        value: {
          isAnswered: true,
          text: '{"cards": [' +
            '{"title": "FDR across electrodes", "type": "decision", "summary": "Chosen over Bonferroni again.", "evidence": "reasoning/data-analyze.jsonl, 14:05 entry"},' +
            '{"title": "baseline window", "type": "method", "summary": "-200 to 0 ms.", "evidence": "reasoning/data-analyze.jsonl, 14:06 entry"}]}',
          usage: { input_tokens: 1, output_tokens: 1, cache_creation_input_tokens: 0, cache_read_input_tokens: 0 },
        },
      }
    })
    await $.session.start({ cwd: root, surface: 'terminal', isInteractive: true })
    await $.command.run({ command: 'neuroflow:data-analyze', args: '' })
    fs.files[`${root}/.neuroflow/reasoning/data-analyze.jsonl`] += '{"statement": "Use FDR across electrodes", "reasoning": "Bonferroni too conservative"}\n'
    await $.turn.complete({ reason: 'answer', answer: 'done', durationMs: 1, isAborted: false, turnId: 't1' } as never)
    expect(asked.length).toBe(1)
    expect(asked[0]).toContain('Cards already in the queue (pending, accepted or skipped): Baseline window; FDR across electrodes')
    expect(Object.keys(fs.files).filter(path => path.startsWith(`${pending}/2026-10-07`))).toEqual([])
    expect(parseCard(fs.files[`${pending}/2026-10-01-fdr-across-electrodes.md`])?.status).toBe('skipped')
  })

  test('accept, on Enter and a yes, closes the pane and runs /neuroflow:wiki --add for the card; a stray Enter does neither', { options: { runtime: 'observe' } }, async ($, on) => {
    const pending = `${root}/.neuroflow/wiki/.pending`
    const card = cardText({ title: 'FDR across electrodes', type: 'decision', evidence: 'reasoning/data-analyze.jsonl (14:05 entry)', captured: '2026-10-07T14:05', by: 'mod', status: 'pending', body: 'Chosen over Bonferroni.' })
    fakeFs(on, { ...files, [`${pending}/2026-10-07-fdr-across-electrodes.md`]: card }, root)
    mock.env(on, { HOME: '/home/me' })
    const clock = mock.clock(on, { now: new Date(2026, 9, 7, 14, 10).getTime() })
    mock.store(on)
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('ui.status', () => ({ value: undefined }))
    on('ui.toast', () => ({ value: undefined }))
    on('ui.open', () => ({ value: undefined }))
    const closed: string[] = []
    on('ui.close', ($, e) => {
      closed.push(e.id)
      return { value: undefined }
    })
    const ran: string[] = []
    on('command.run', ($, e) => {
      ran.push(`${e.command} ${e.args}`)
      return { text: '', ref: 1 }
    })
    const dialog = answerAsks(on)
    await $.session.start({ cwd: root, surface: 'terminal', isInteractive: true })
    await $.command.run({ command: 'neuroflow:wiki', args: '--review' })
    const pane = await $.ui.mount({
      plugin: 'neuroflow', surface: 'terminal', component: 'Pane', requestId: 'nf-wiki',
      props: { title: 'wiki cards', isFocused: true, bodyColumns: 100, placement: 'inline', scroll: { offset: 0, bodyRows: 12 }, view: {} },
    } as never)
    await clock.advance(500)
    await pane.press({ key: 'nf-wiki-accept' })
    expect(dialog.asked.map(asked => asked.options)).toEqual([['Not now', 'Accept']])
    expect([ran, closed]).toEqual([[], []])
    dialog.answer(() => 'Accept')
    await clock.advance(500)
    await pane.press({ key: 'nf-wiki-accept' })
    expect(closed).toEqual(['nf-wiki'])
    expect(ran).toEqual(['neuroflow:wiki --add --from-pending .neuroflow/wiki/.pending/2026-10-07-fdr-across-electrodes.md'])
    await pane.unmount()
  })

  test('without the opt-in no model call is made', { options: { runtime: 'on' } }, async ($, on) => {
    const fs = fakeFs(on, { ...files, '/home/me/.neuroflow/user.yaml': 'wiki_auto: off\n' }, root)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: new Date(2026, 9, 7, 14, 10).getTime() })
    mock.store(on)
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('session.model', () => ({ value: 'claude-test' }))
    on('ui.status', () => ({ value: undefined }))
    on('ui.toast', () => ({ value: undefined }))
    on('ui.log', () => ({ value: undefined }))
    on('turn.complete', () => ({ text: 'done' }))
    on('command.run', () => ({ text: '', ref: 1 }))
    let calls = 0
    on('model.complete', () => {
      calls += 1
      return { value: { isAnswered: false, reason: 'empty-reply', usage: { input_tokens: 0, output_tokens: 0, cache_creation_input_tokens: 0, cache_read_input_tokens: 0 } } }
    })
    await $.session.start({ cwd: root, surface: 'terminal', isInteractive: true })
    await $.command.run({ command: 'neuroflow:data-analyze', args: '' })
    fs.files[`${root}/.neuroflow/reasoning/data-analyze.jsonl`] += '{"statement": "Use FDR"}\n'
    await $.turn.complete({ reason: 'answer', answer: 'done', durationMs: 1, isAborted: false, turnId: 't1' } as never)
    expect(calls).toBe(0)
  })
})
