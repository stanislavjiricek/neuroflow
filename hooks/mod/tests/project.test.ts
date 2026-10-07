import { describe, expect, test } from 'claude-code/testing'

import { appendLine } from '../lib/memory'
import { compareVersions, computeScope, loadSnapshot, versionNotice } from '../lib/project'
import { runScript } from '../lib/scripts'
import { memIo } from './memio'

const CONFIG = [
  '---',
  'nf_schema: 1',
  'project_name: Oddball',
  'active_phase: data-analyze',
  'default_mode: critic',
  'raw_roots: [sourcedata/]',
  '---',
  '',
].join('\n')

describe('scope', () => {
  test('finds the project by walking up from a subfolder', async () => {
    const io = memIo({ '/work/proj/.neuroflow/project_config.md': CONFIG }, { home: '/home/me' })
    const scope = await computeScope(io, '/work/proj/scripts/analysis', true)
    expect(scope).toEqual({ isActive: true, reason: 'active', root: '/work/proj', isHeadless: false })
  })

  test('stays off outside a project, in the home folder, and in the plugin repo', async () => {
    const io = memIo({
      '/home/me/.neuroflow/project_config.md': CONFIG,
      '/dev/neuroflow/.neuroflow/project_config.md': CONFIG,
      '/dev/neuroflow/.claude-plugin/plugin.json': '{ "name": "neuroflow", "version": "0.2.22" }',
    }, { home: '/home/me' })
    expect((await computeScope(io, '/tmp/elsewhere', true)).isActive).toBe(false)
    expect((await computeScope(io, '/home/me', true)).reason).toBe('the home folder is not a project')
    const repo = await computeScope(io, '/dev/neuroflow/skills', false)
    expect(repo.reason).toBe("the plugin's own repository")
    expect(repo.isHeadless).toBe(true)
  })

  test('Windows spellings of the home folder are the same folder', async () => {
    const io = memIo({ 'C:/Users/Me/.neuroflow/project_config.md': CONFIG }, { home: 'c:\\users\\me' })
    expect((await computeScope(io, 'C:/Users/Me', true)).isActive).toBe(false)
  })
})

describe('snapshot', () => {
  test('mirrors config, integrity markers and deadlines', async () => {
    const io = memIo({
      '/work/proj/.neuroflow/project_config.md': CONFIG,
      '/work/proj/.neuroflow/ethics/status.md': '---\nstatus: approved\nexpires: 2026-10-20\nai_processing: pseudonymised\nset_by: person\n---\n',
      '/work/proj/.neuroflow/preregistration/status.md': '---\nstatus: frozen\nfiles:\n  .neuroflow/preregistration/p.md: abc\nplanned_n: 48\nset_by: model\n---\n',
      '/work/proj/.neuroflow/timeline.md': '| Date | What | Gates |\n|---|---|---|\n| 2026-10-09 | Poster | poster |\n',
    }, { now: new Date(2026, 9, 7, 9, 0).getTime() })
    const snap = await loadSnapshot(io, '/work/proj')
    expect(snap.phase).toBe('data-analyze')
    expect(snap.mode).toBe('critic')
    expect(snap.rawRoots).toEqual(['sourcedata/'])
    expect(snap.ethics?.status).toBe('approved')
    expect(snap.ethics?.aiProcessing).toBe('pseudonymised')
    expect(snap.prereg?.files).toEqual({ '.neuroflow/preregistration/p.md': 'abc' })
    expect(snap.prereg?.plannedN).toBe(48)
    expect(snap.prereg?.setBy).toBe('model')
    expect(snap.deadlines.map(d => d.what)).toEqual(['Poster', 'ethics approval expires'])
    expect(snap.deadlines[0].gates).toBe('poster')
    expect(snap.problems).toEqual([])
  })

  test('a legacy config still loads, with a migrate hint', async () => {
    const io = memIo({ '/work/proj/.neuroflow/project_config.md': '# Project config\n\nproject_name: Pilot\nactive_phase: ideation\n' })
    const snap = await loadSnapshot(io, '/work/proj')
    expect(snap.dialect).toBe('legacy')
    expect(snap.phase).toBe('ideation')
    expect(snap.problems[0]).toContain('/neuroflow:migrate')
  })

  test('a newer schema is reported, not trusted', async () => {
    const io = memIo({ '/work/proj/.neuroflow/project_config.md': '---\nnf_schema: 9\nactive_phase: paper\n---\n' })
    const snap = await loadSnapshot(io, '/work/proj')
    expect(snap.problems.some(p => p.includes('nf_schema 9'))).toBe(true)
  })
})

describe('version notice', () => {
  test('the snapshot mirrors the version that last wrote the project and the running plugin\'s', async () => {
    const io = memIo({
      '/work/proj/.neuroflow/project_config.md': '---\nnf_schema: 1\nactive_phase: paper\nplugin_version: 0.2.21\n---\n',
      '/plugin/.claude-plugin/plugin.json': '{ "name": "neuroflow", "version": "0.2.22" }',
    })
    const snap = await loadSnapshot(io, '/work/proj')
    expect([snap.pluginVersion, snap.runningVersion]).toEqual(['0.2.21', '0.2.22'])
    expect(versionNotice(snap)).toBe('neuroflow 0.2.22 is installed — this project is on 0.2.21 · /neuroflow:migrate')
    const legacy = await loadSnapshot(memIo({ '/work/proj/.neuroflow/project_config.md': '**Plugin version:** 0.2.20\n**Phase:** data\n' }), '/work/proj')
    expect([legacy.pluginVersion, legacy.runningVersion]).toEqual(['0.2.20', null])
  })

  test('versions compare number by number; nothing to say when current, newer or unknown', () => {
    expect(compareVersions('0.2.10', '0.2.9') > 0).toBe(true)
    expect(compareVersions('0.2', '0.2.0')).toBe(0)
    expect(versionNotice({ pluginVersion: '0.2.9', runningVersion: '0.2.10' })).toBe('neuroflow 0.2.10 is installed — this project is on 0.2.9 · /neuroflow:migrate')
    expect(versionNotice({ pluginVersion: null, runningVersion: '0.2.22' })).toBe('neuroflow 0.2.22 is installed — this project is on an older version · /neuroflow:migrate')
    expect(versionNotice({ pluginVersion: '0.2.22', runningVersion: '0.2.22' })).toBe(null)
    expect(versionNotice({ pluginVersion: '0.2.23', runningVersion: '0.2.22' })).toBe(null)
    expect(versionNotice({ pluginVersion: '0.2.21', runningVersion: null })).toBe(null)
  })
})

describe('memory', () => {
  test('appendLine is idempotent and keeps what was there', async () => {
    const path = '/work/proj/.neuroflow/sessions/2026-10-07.md'
    const io = memIo({ [path]: '## 09:00 — [paper] started' })
    expect(await appendLine(io, path, '## 09:30 — [paper] draft saved (auto)')).toBe('written')
    expect(await appendLine(io, path, '## 09:30 — [paper] draft saved (auto)')).toBe('present')
    expect(io.files[path]).toBe('## 09:00 — [paper] started\n## 09:30 — [paper] draft saved (auto)\n')
  })
})

describe('scripts', () => {
  test('falls through interpreters that are not installed', async () => {
    const io = memIo({}, {
      run: argv => (argv[0] === 'python'
        ? { exitCode: 9009, stdout: '', stderr: 'Python was not found' }
        : { exitCode: 1, stdout: '{"findings": 2}', stderr: '' }),
    })
    const result = await runScript(io, 'skills/x/scripts/check.py', ['--json'])
    expect(result.python).toBe('python3')
    expect(result.exitCode).toBe(1)
    expect(io.ran[1]).toEqual(['python3', '/plugin/skills/x/scripts/check.py', '--json'])
  })
})
