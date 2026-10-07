// Pure edits of project_config.md that keep everything else byte-for-byte (neuroflow-core → C1).
import { splitFrontmatter } from './frontmatter'

/**
 * Returns the config text with `active_phase` set to `phase`, or null when the file's dialect
 * cannot be edited safely (no frontmatter and no `active_phase:` line — /neuroflow:migrate first).
 */
export const setActivePhase = (configText: string, phase: string): string | null => {
  const eol = configText.includes('\r\n') ? '\r\n' : '\n'
  const { block } = splitFrontmatter(configText)
  const lines = configText.split(/\r?\n/)
  if (block !== null) {
    // Frontmatter: lines[0] is '---'; find its closing fence.
    const end = lines.findIndex((line, index) => index > 0 && /^---[ \t]*$/.test(line))
    if (end < 0) return null
    const at = lines.findIndex((line, index) => index > 0 && index < end && /^active_phase:/.test(line))
    if (at >= 0) {
      const comment = /(\s+#.*)$/.exec(lines[at])
      lines[at] = `active_phase: ${phase}${comment ? comment[1] : ''}`
    } else {
      lines.splice(end, 0, `active_phase: ${phase}`)
    }
    return lines.join(eol)
  }
  const legacy = lines.findIndex(line => /^active_phase:\s/.test(line))
  if (legacy < 0) return null
  lines[legacy] = `active_phase: ${phase}`
  return lines.join(eol)
}
