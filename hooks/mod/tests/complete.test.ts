import { describe, expect, test } from 'claude-code/testing'

import type { NfCard, NfTaskLevel, NfTaskView } from '../../../types'
import { MAX_SUGGESTIONS, completions } from '../lib/complete'
import type { CompleteContext } from '../lib/complete'

/** The prompt box with the cursor at the end, and the token there as the event hands it. */
const typed = (text: string) => {
  const token = /\S*$/.exec(text)?.[0] ?? ''
  return { text, cursor: text.length, token, start: text.length - token.length }
}

const card = (slug: string, title: string): NfCard => ({ slug, title, owner: null, due: null, overdue: false, project: null, isMine: true })
const level = (id: string, kind: NfTaskLevel['kind'], name: string, columns: Record<string, NfCard[]>): NfTaskLevel => ({
  id,
  kind,
  name,
  project: null,
  open: Object.values(columns).flat().length,
  mine: 0,
  board: {
    columns: Object.entries(columns).map(([column, cards]) => ({ id: column, label: column, cards, total: cards.length })),
    openColumns: ['inbox', 'ready', 'active', 'review', 'meeting'],
    done: 0,
    archived: 0,
  },
  top: [],
})

const TASKS: NfTaskView = {
  levels: [
    level('project', 'project', 'project', { inbox: [card('fix-markers', 'Fix marker channels')], active: [card('rerun-ica', 'Rerun ICA')] }),
    level('flowie', 'flowie', 'flowie', { review: [card('check-stats', 'Check stats')] }),
    level('hive:lab-team', 'hive', 'lab-team', { meeting: [card('agenda-item', 'Agenda item')], inbox: [card('poster', 'Review poster')] }),
    level('hive:alpha-team', 'hive', 'alpha-team', { inbox: [] }),
  ],
}

const CONTEXT: CompleteContext = { phase: 'data', visited: ['ideation', 'data'], recommended: ['ideation', 'data', 'data-analyze', 'paper'], tasks: TASKS }
const rows = (text: string, context: CompleteContext = CONTEXT) => completions(typed(text), context).map(row => `${row.text} | ${row.description ?? ''}`)

describe('typeahead for the typed paths', () => {
  test('phases after /neuroflow:phase, in picker order, each with its mark and state', () => {
    expect(typed('/neuroflow:phase da')).toEqual({ text: '/neuroflow:phase da', cursor: 19, token: 'da', start: 17 })
    expect(rows('/neuroflow:phase da')).toEqual([
      'data | ◉ current · acquisition & BIDS',
      'data-analyze | → next · analysis',
      'data-preprocess | ○ not started · preprocessing',
    ])
    // paper is recommended, but data-analyze comes next: the picker's word, `recommended`.
    expect(rows('/phase pa')).toEqual(['paper | → recommended · manuscript'])
    expect(rows('/neuroflow:phase I')).toEqual(['ideation | ● visited · question & literature'])
    // A next phase already visited keeps the visited glyph's word, and says next beside it.
    expect(rows('/neuroflow:phase data-a', { ...CONTEXT, visited: ['ideation', 'data', 'data-analyze'] })).toEqual(['data-analyze | ● visited · next · analysis'])
    // The id is the whole argument: nothing after it, and nothing for another command.
    expect(rows('/neuroflow:phase data-analyze x')).toEqual([])
    expect(rows('/neuroflow:paper da')).toEqual([])
  })

  test('the dashboard\'s tabs after /neuroflow:dashboard', () => {
    expect(rows('/neuroflow:dashboard d')).toEqual(['deadlines | tab 3'])
    expect(rows('/neuroflow:dashboard l')).toEqual(['loop | tab 6'])
    expect(rows('/neuroflow:dashboard --web l')).toEqual([])
  })

  test('levels after --level and the hive folders after --hive, in the commands that take them', () => {
    expect(rows('/neuroflow:tasks --level h')).toEqual(['hive | a team\'s board, with --hive'])
    expect(rows('/neuroflow:meeting --level f')).toEqual(['flowie | your own board'])
    expect(rows('/neuroflow:tasks --level hive --hive a')).toEqual(['alpha-team | hive · 0 open'])
    expect(rows('/neuroflow:tasks --level hive --hive L')).toEqual(['lab-team | hive · 2 open'])
    // Hives come from the boards the mod has read; before that, none.
    expect(rows('/neuroflow:tasks --level hive --hive l', { ...CONTEXT, tasks: null })).toEqual([])
    expect(rows('/neuroflow:git --level p')).toEqual([])
    expect(rows('please --level p')).toEqual([])
    // /migrate takes no --hive of its own: the flag belongs to the scripts its prose runs.
    expect(rows('/neuroflow:migrate --hive l')).toEqual([])
    expect(rows('/migrate --hive a')).toEqual([])
  })

  test('at hive level a single joined hive needs no --hive; among several the line must name one', () => {
    const one: CompleteContext = { ...CONTEXT, tasks: { levels: TASKS.levels.filter(item => item.id !== 'hive:alpha-team') } }
    expect(rows('/neuroflow:tasks --level hive --move a', one)).toEqual(['agenda-item | Agenda item · meeting'])
    expect(rows('/neuroflow:tasks --level hive --move agenda-item i', one)).toEqual(['inbox | move agenda-item here'])
    // Two hives and no --hive: /tasks would ask which, so nothing is offered.
    expect(rows('/neuroflow:tasks --level hive --move a')).toEqual([])
    expect(rows('/neuroflow:tasks --level hive --hive alpha-team --move a')).toEqual([])
  })

  test('after --move, the open cards of the level the line names; after the card, the columns it can move to', () => {
    expect(rows('/neuroflow:tasks --move re')).toEqual(['rerun-ica | Rerun ICA · active'])
    expect(rows('/neuroflow:tasks --level flowie --move c')).toEqual(['check-stats | Check stats · review'])
    expect(rows('/neuroflow:tasks --level hive --hive lab-team --move a')).toEqual(['agenda-item | Agenda item · meeting'])
    expect(rows('/neuroflow:tasks --move rerun-ica r')).toEqual(['ready | move rerun-ica here', 'review | move rerun-ica here'])
    expect(rows('/neuroflow:tasks --move rerun-ica d')).toEqual(['done | move rerun-ica here'])
    // Its own column is no target; an unknown card has none.
    expect(rows('/neuroflow:tasks --move rerun-ica a')).toEqual([])
    expect(rows('/neuroflow:tasks --move nothing-here r')).toEqual([])
    expect(rows('/neuroflow:tasks --move re', { ...CONTEXT, tasks: null })).toEqual([])
  })

  test('at most eight rows, beneath the engine\'s own', () => {
    const many = level('project', 'project', 'project', { ready: Array.from({ length: 12 }, (_, at) => card(`step-${at + 1}`, `Step ${at + 1}`)) })
    expect(completions(typed('/neuroflow:tasks --move step'), { ...CONTEXT, tasks: { levels: [many] } })).toHaveLength(MAX_SUGGESTIONS)
  })
})
