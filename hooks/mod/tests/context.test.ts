import { describe, expect, mock, test } from 'claude-code/testing'

import type { NfSnapshot } from '../../../types'
import { footerLabel, identitySection } from '../features/context'
import { fakeFs } from './fakefs'

const snap = { projectName: 'Oddball', phase: 'data-analyze', mode: 'critic' } as NfSnapshot

describe('context', () => {
  test('footer label and identity section are short and stable', () => {
    expect(footerLabel(snap)).toBe('neuroflow · data-analyze · critic')
    expect(footerLabel({ ...snap, mode: null })).toBe('neuroflow · data-analyze')
    expect(footerLabel(snap, true)).toBe('neuroflow · data-analyze · critic · login node')
    expect(identitySection(snap)).toBe(identitySection({ ...snap }))
    expect(identitySection(snap).split('\n')).toHaveLength(4)
    expect(identitySection(snap)).toContain('active phase: data-analyze · mode: critic.')
  })

  test('the section is added after the engine\'s own, only in a project', { options: { runtime: 'observe' } }, async ($, on) => {
    fakeFs(on, { '/work/proj/.neuroflow/project_config.md': '---\nnf_schema: 1\nproject_name: Oddball\nactive_phase: paper\n---\n' })
    mock.env(on, { HOME: '/home/me' })
    mock.clock(on, { now: 0 })
    on('session.start', ($, e) => ({ cwd: e.cwd }))
    on('prompt.compose', () => ({ sections: [{ id: 'intro', text: 'engine', scope: 'shared' }] }))
    await $.session.start({ cwd: '/work/proj', surface: 'terminal', isInteractive: true })
    const composed = await $.prompt.compose({ model: 'claude-test', promptModel: 'claude-test', surfaces: ['terminal'], tools: [], outputStyle: null, traits: [] })
    expect(composed.sections.map(section => section.id)).toEqual(['intro', 'neuroflow:project'])
    expect(composed.sections[1].scope).toBe('session')
  })
})
