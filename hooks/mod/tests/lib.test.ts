import { describe, expect, test } from 'claude-code/testing'

import { parseLegacyConfig, parseYamlSubset, splitFrontmatter } from '../lib/frontmatter'
import { readOptions } from '../lib/options'
import { fold, isInside, relativeTo, resolveFrom, toSlash } from '../lib/paths'
import { parseTimeline } from '../lib/project'

describe('frontmatter', () => {
  test('reads the C1 config contract', () => {
    const { block, body } = splitFrontmatter([
      '---',
      'nf_schema: 1',
      'project_name: "Oddball EEG study"',
      'active_phase: data-analyze   # canonical id',
      'recommended_phases: [ideation, data, paper]',
      'raw_roots:',
      '  - sourcedata/',
      'paper_auto: off',
      '---',
      '# Notes',
    ].join('\r\n'))
    expect(block).not.toBe(null)
    const fm = parseYamlSubset(block ?? '')
    expect(fm.nf_schema).toBe(1)
    expect(fm.project_name).toBe('Oddball EEG study')
    expect(fm.active_phase).toBe('data-analyze')
    expect(fm.recommended_phases).toEqual(['ideation', 'data', 'paper'])
    expect(fm.raw_roots).toEqual(['sourcedata/'])
    expect(fm.paper_auto).toBe(false)
    expect(body.startsWith('# Notes')).toBe(true)
  })

  test('reads a one-level map (prereg file hashes)', () => {
    const fm = parseYamlSubset(['status: frozen', 'files:', '  .neuroflow/preregistration/p.md: abc123', 'set_by: person'].join('\n'))
    expect(fm.files).toEqual({ '.neuroflow/preregistration/p.md': 'abc123' })
    expect(fm.set_by).toBe('person')
  })

  test('reads both legacy dialects', () => {
    const lines = parseLegacyConfig('# Project config\n\nproject_name: Pilot\nactive_phase: ideation\n')
    expect(lines.active_phase).toBe('ideation')
    const bold = parseLegacyConfig('**Project:** Pilot study\n**Phase:** data\n')
    expect(bold.phase).toBe('data')
    expect(bold.project).toBe('Pilot study')
  })
})

describe('paths', () => {
  test('fold makes Windows spellings of one path equal', () => {
    expect(fold('C:\\Users\\A\\Proj\\.NEUROFLOW')).toBe(fold('c:/users/a/proj/.neuroflow'))
    expect(isInside('C:\\Users\\A\\proj\\sourcedata\\sub-01', 'c:/users/a/proj/sourcedata')).toBe(true)
    expect(isInside('/work/proj-other/x', '/work/proj')).toBe(false)
  })

  test('resolve and relative', () => {
    expect(resolveFrom('/work/proj', 'a/../b/c.md')).toBe('/work/proj/b/c.md')
    expect(resolveFrom('C:/work/proj', 'x.md')).toBe('C:/work/proj/x.md')
    expect(relativeTo('/work/proj/.neuroflow/flow.md', '/work/proj')).toBe('.neuroflow/flow.md')
    expect(toSlash('C:\\a\\b\\')).toBe('C:/a/b')
  })
})

describe('options', () => {
  test('unknown values fall back to the quiet defaults', () => {
    expect(readOptions({})).toEqual({ runtime: 'observe', guards: 'warn', band: 'quiet', citations: false })
    expect(readOptions({ runtime: 'loud', guards: 'enforce', band: 'normal', citations: true }))
      .toEqual({ runtime: 'observe', guards: 'enforce', band: 'normal', citations: true })
  })
})

describe('timeline', () => {
  test('keeps future rows, sorted, with days left', () => {
    const now = new Date(2026, 9, 7, 12, 0).getTime()
    const rows = parseTimeline([
      '| Date | What | Gates |',
      '|---|---|---|',
      '| 2026-10-10 | Abstract deadline | paper |',
      '| 2026-01-01 | Old | x |',
      '| 2026-10-08 | Lab meeting | |',
    ].join('\n'), now)
    expect(rows.map(row => row.date)).toEqual(['2026-10-08', '2026-10-10'])
    expect(rows[0].daysLeft).toBe(1)
    expect(rows[1].what).toBe('Abstract deadline')
    expect(rows[1].gates).toBe('paper')
  })
})
