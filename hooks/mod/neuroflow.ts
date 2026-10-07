// neuroflow mod — the hooks module (Claude Code function hooks, early access).
//
// The mod is an optional layer over the plugin's skills and commands: it shows project state at
// zero tokens, fills bookkeeping gaps, answers some commands instantly and enforces a few rules.
// The prose stays the source of truth: everything here also works, slower, without the module
// (rollout flag off, hooks disabled, older builds), and every guard enforces a rule the prose
// states under an <!-- nf-rule: ID --> marker. Charter: docs/concepts/mods.md.
//
// Features register in a fixed order; earlier registrations sit outermost, so scope tracking
// wraps everything and the guards judge before any other feature sees a call.
import type { Register } from 'claude-code'

import { readOptions } from './lib/options'
import { registerBookkeeping } from './features/bookkeeping'
import { registerCapture } from './features/capture'
import { registerChecks } from './features/checks'
import { registerContext } from './features/context'
import { registerGuards } from './features/guards'
import { registerLoop } from './features/loop'
import { registerScope } from './features/scope'
import { registerStatus } from './features/status'
import { registerUser } from './features/user'
import { registerViews } from './features/views'

export const register: Register = (on, options) => {
  const opts = readOptions(options)
  if (opts.runtime === 'off') return

  registerScope(on, opts)
  registerGuards(on, opts)
  registerContext(on, opts)
  registerBookkeeping(on, opts)
  registerStatus(on, opts)
  registerViews(on, opts)
  registerLoop(on, opts)
  registerCapture(on, opts)
  registerChecks(on, opts)
  registerUser(on, opts)
}
