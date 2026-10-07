// The plugin's userConfig, read once per load. Unknown or missing values fall back to the
// safe default, so a bad setting can only make the mod quieter, never stricter.
import type { PluginOptions } from 'claude-code'

import type { NfRuntime } from '../../../types'

export type NfOptions = {
  /** off: the mod does nothing. observe: views and warnings only. on: also fills gaps and enforces. */
  runtime: NfRuntime
  /** warn: guards say what they would block. enforce: guards deny (only with runtime on). */
  guards: 'warn' | 'enforce'
  /** off | quiet (only what needs attention) | normal */
  band: 'off' | 'quiet' | 'normal'
  /** check DOIs of citations after manuscript writes */
  citations: boolean
}

const pick = <T extends string>(value: unknown, allowed: readonly T[], fallback: T): T =>
  typeof value === 'string' && (allowed as readonly string[]).includes(value) ? (value as T) : fallback

export const readOptions = (options: PluginOptions): NfOptions => ({
  runtime: pick(options.runtime, ['off', 'observe', 'on'] as const, 'observe'),
  guards: pick(options.guards, ['warn', 'enforce'] as const, 'warn'),
  band: pick(options.band, ['off', 'quiet', 'normal'] as const, 'quiet'),
  citations: options.citations === true,
})

/** True when a guard may actually deny (never in observe mode). */
export const mayEnforce = (opts: NfOptions): boolean => opts.runtime === 'on' && opts.guards === 'enforce'

/** True when the mod may write into project memory (never in observe mode). */
export const mayWrite = (opts: NfOptions): boolean => opts.runtime === 'on'
