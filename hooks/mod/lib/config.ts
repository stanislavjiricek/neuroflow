// Pure edits of project_config.md that keep everything else byte-for-byte (neuroflow-core → C1).
import { splitFrontmatter } from './frontmatter'

/**
 * Returns the config text with frontmatter `key` set to `value`, or null when the file's dialect cannot
 * be edited safely (no frontmatter and no `key:` line of the legacy dialect — /neuroflow:migrate first).
 */
export const setConfigKey = (configText: string, key: string, value: string): string | null => {
  const eol = configText.includes('\r\n') ? '\r\n' : '\n'
  const { block } = splitFrontmatter(configText)
  const lines = configText.split(/\r?\n/)
  const keyLine = new RegExp(`^${key}:`)
  if (block !== null) {
    // Frontmatter: lines[0] is '---'; find its closing fence.
    const end = lines.findIndex((line, index) => index > 0 && /^---[ \t]*$/.test(line))
    if (end < 0) return null
    const at = lines.findIndex((line, index) => index > 0 && index < end && keyLine.test(line))
    if (at >= 0) {
      const comment = /(\s+#.*)$/.exec(lines[at])
      lines[at] = `${key}: ${value}${comment ? comment[1] : ''}`
    } else {
      lines.splice(end, 0, `${key}: ${value}`)
    }
    return lines.join(eol)
  }
  const legacy = lines.findIndex(line => new RegExp(`^${key}:\\s`).test(line))
  if (legacy < 0) return null
  lines[legacy] = `${key}: ${value}`
  return lines.join(eol)
}

/** `active_phase` set to `phase` (see setConfigKey). */
export const setActivePhase = (configText: string, phase: string): string | null => setConfigKey(configText, 'active_phase', phase)

/** The `version` of a plugin.json text, or null. */
export const manifestVersion = (manifest: string | null): string | null => {
  if (manifest === null) return null
  try {
    const version = (JSON.parse(manifest) as { version?: unknown }).version
    return typeof version === 'string' ? version : null
  } catch {
    return null
  }
}
