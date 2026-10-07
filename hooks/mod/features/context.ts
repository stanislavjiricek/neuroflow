// Context — what the person and the model see about the project without anyone reading files.
//  - M062: the footer label (`neuroflow · data-analyze · critic`) beside the engine's own mode labels
//  - M002 (lite): one small, stable system-prompt section naming the project, phase and mode, and
//    pointing at project_config.md as the source of truth. Stable facts only (charter: no volatile
//    or bloated injection) — deadlines and tasks belong on screen, not in the prompt.
// Command-start digests (M004), the profile digest (M143) and wiki lookups (M133) live here too.
import { atom, read } from 'claude-code'
import type { On } from 'claude-code'

import type { NfSnapshot } from '../../../types'
import type { NfOptions } from '../lib/options'

const scopeAtom = atom({ plugin: 'neuroflow', key: 'scope' } as const, null)
const snapshotAtom = atom({ plugin: 'neuroflow', key: 'snapshot' } as const, null)
const loginNodeAtom = atom({ plugin: 'neuroflow', key: 'loginNode' } as const, null)

/** The footer label: phase, the personality mode when set, and a reminder on an HPC login node. */
export const footerLabel = (snap: NfSnapshot, loginNode = false): string =>
  ['neuroflow', snap.phase ?? 'no phase', snap.mode, loginNode ? 'login node' : null].filter(Boolean).join(' · ')

/** The one system-prompt section. Byte-identical while the config does not change. */
export const identitySection = (snap: NfSnapshot): string =>
  [
    'neuroflow (a Claude Code plugin for neuroscience research) is active in this project.',
    `Project: ${snap.projectName ?? 'unnamed'} · active phase: ${snap.phase ?? 'none'}${snap.mode ? ` · mode: ${snap.mode}` : ''}.`,
    'Project memory lives in .neuroflow/; project_config.md is the source of truth for these facts.',
    'Read project_config.md and flow.md before neuroflow work, and follow the neuroflow-core lifecycle.',
  ].join('\n')

export const registerContext = (on: On, _opts: NfOptions): void => {
  on('ui.render', { component: 'SessionMode' }, async ($, e, next) => {
    const scope = await read($, scopeAtom)
    const snap = await read($, snapshotAtom)
    if (!scope?.isActive || snap === null) return next(e)
    return next({ ...e, props: { ...e.props, modes: [...e.props.modes, footerLabel(snap, (await read($, loginNodeAtom)) === true)] } })
  }).catch(($, e, next) => next(e))

  on('prompt.compose', async ($, e, next) => {
    const result = await next(e)
    const scope = await read($, scopeAtom)
    const snap = await read($, snapshotAtom)
    if (!scope?.isActive || snap === null) return result
    return { sections: [...result.sections, { id: 'neuroflow:project', text: identitySection(snap), scope: 'session' as const }] }
  }).catch(($, e, next) => next(e))
}
