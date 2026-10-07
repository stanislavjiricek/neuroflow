import { describe, expect, mock, test } from 'claude-code/testing'

import { captureAllowed, cardText, parseCard, parseJudge, setCardStatus, slugify, takenTitles } from '../lib/wikiqueue'
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

  test('a logged decision becomes a card; review opens it; skip drops it for good', { options: { runtime: 'on' } }, async ($, on) => {
    const fs = fakeFs(on, files, root)
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: new Date(2026, 9, 7, 14, 10).getTime() })
    mock.store(on)
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('session.model', () => ({ value: 'claude-test' }))
    on('ui.status', () => ({ value: undefined }))
    on('ui.toast', () => ({ value: undefined }))
    on('ui.log', () => ({ value: undefined }))
    on('ui.open', () => ({ value: undefined }))
    on('ui.close', () => ({ value: undefined }))
    on('turn.complete', () => ({ text: 'done' }))
    on('command.run', () => ({ text: '', ref: 1 }))
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

    const review = await $.command.run({ command: 'neuroflow:wiki', args: '--review' })
    expect(review.text).toContain('1 wiki card waiting')
    const pane = await $.ui.mount({
      plugin: 'neuroflow', surface: 'terminal', component: 'Pane', requestId: 'nf-wiki',
      props: { title: 'wiki cards', isFocused: true, bodyColumns: 100, placement: 'inline', scroll: { offset: 0, bodyRows: 12 }, view: {} },
    } as never)
    expect(JSON.stringify(await pane.drawn())).toContain('FDR across electrodes')
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
