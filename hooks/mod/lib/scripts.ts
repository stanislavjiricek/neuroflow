// Running the plugin's own portable Python checks (skills/<skill>/scripts/*.py) — the same files the
// prose tells the model to run, so every check has one executable home (charter: no third copy).
import type { NfIo } from './io'
import { join } from './paths'

export type ScriptRun = { ok: boolean; exitCode: number; stdout: string; stderr: string; python: string | null }

const CANDIDATES: readonly (readonly string[])[] = [['python'], ['python3'], ['py', '-3']]

/**
 * Runs `skills/...py` from the plugin with the first Python that answers. Exit codes follow the
 * scripts' contract: 0 clean, 1 findings, 2 usage or runtime error. Never throws.
 */
export const runScript = async (
  io: NfIo,
  script: string,
  args: readonly string[],
  init: { cwd?: string; timeoutMs?: number } = {},
): Promise<ScriptRun> => {
  const path = join(io.pluginRoot, script)
  for (const python of CANDIDATES) {
    try {
      const result = await io.run([...python, path, ...args], { cwd: init.cwd, timeoutMs: init.timeoutMs ?? 30_000 })
      // 9009 and these messages mean "no such interpreter" (Windows shims, the Store stub), not a script error
      const isMissing = result.exitCode === 9009 || /Python was not found|is not recognized as an internal or external command/i.test(result.stderr)
      if (isMissing) continue
      return { ok: result.exitCode === 0, exitCode: result.exitCode, stdout: result.stdout, stderr: result.stderr, python: python.join(' ') }
    } catch {
      // this interpreter is not installed; try the next one
    }
  }
  return { ok: false, exitCode: 2, stdout: '', stderr: 'no Python interpreter found', python: null }
}

/** Parses a script's `--json` output; null when it is not JSON. */
export const parseJson = <T>(stdout: string): T | null => {
  try {
    return JSON.parse(stdout) as T
  } catch {
    return null
  }
}
