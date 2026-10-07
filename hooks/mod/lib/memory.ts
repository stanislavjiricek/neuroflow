// Writing into project memory, the only way the mod does it (neuroflow-core → C8): marked with
// "(auto)", idempotent (a line already present is not written twice), append-only (never
// rewrites what a person or the model wrote), and checked after writing (compare-and-retry),
// because the file system API has no append or lock and another writer may race us.
import type { NfIo } from './io'
import { join } from './paths'

export const AUTO = '(auto)'

const two = (n: number): string => String(n).padStart(2, '0')

export const isoDate = (ms: number): string => {
  const d = new Date(ms)
  return `${d.getFullYear()}-${two(d.getMonth() + 1)}-${two(d.getDate())}`
}

export const clockTime = (ms: number): string => {
  const d = new Date(ms)
  return `${two(d.getHours())}:${two(d.getMinutes())}`
}

/** The canonical session-log line (neuroflow-core), marked as written by the mod. */
export const sessionLine = (ms: number, tag: string, text: string): string =>
  `## ${clockTime(ms)} — [${tag}] ${text} ${AUTO}`

export const sessionLogPath = (root: string, ms: number): string =>
  join(root, '.neuroflow/sessions', `${isoDate(ms)}.md`)

/**
 * Appends `line` to the file at `path` unless an identical line is already there.
 * Returns 'written', 'present', or 'failed' (after one retry when a racing write lost our line).
 */
export const appendLine = async (io: NfIo, path: string, line: string): Promise<'written' | 'present' | 'failed'> => {
  for (let attempt = 0; attempt < 2; attempt += 1) {
    const current = (await io.read(path)) ?? ''
    if (current.split(/\r?\n/).includes(line)) return 'present'
    const separator = current === '' || current.endsWith('\n') ? '' : '\n'
    try {
      await io.write(path, `${current}${separator}${line}\n`)
      const after = await io.read(path)
      if (after !== null && after.split(/\r?\n/).includes(line)) return 'written'
    } catch {
      // fall through to the retry
    }
  }
  return 'failed'
}
