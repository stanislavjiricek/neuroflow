// A small reader for the YAML subset neuroflow's contract files use (neuroflow-core → C1/C2):
// `key: value`, inline lists `[a, b]`, block lists (`  - item`), and one level of nested map
// (`files:` followed by indented `path: hash` lines). Anything fancier is kept as raw text.
// It never throws: unreadable input yields an empty result.

export type FmValue = string | number | boolean | null | string[] | Record<string, string>
export type Frontmatter = Record<string, FmValue>

const unquote = (raw: string): string => {
  const text = raw.trim()
  if (text.length >= 2 && ((text.startsWith('"') && text.endsWith('"')) || (text.startsWith("'") && text.endsWith("'")))) {
    return text.slice(1, -1)
  }
  return text
}

/** Drops a trailing ` # comment` (only when the hash follows whitespace, so URLs survive). */
const stripComment = (raw: string): string => {
  const match = /\s+#.*$/.exec(raw)
  return match ? raw.slice(0, match.index) : raw
}

const scalar = (raw: string): FmValue => {
  const text = unquote(stripComment(raw))
  if (text === '' || text === '~' || text === 'null') return null
  if (/^\[.*\]$/.test(text)) {
    return text.slice(1, -1).split(',').map(part => unquote(part)).filter(part => part !== '')
  }
  if (text === 'true' || text === 'yes' || text === 'on') return true
  if (text === 'false' || text === 'no' || text === 'off') return false
  if (/^-?\d+(\.\d+)?$/.test(text)) return Number(text)
  return text
}

/** Splits a document into its leading `---` frontmatter block (or null) and the body. */
export const splitFrontmatter = (text: string): { block: string | null; body: string } => {
  const normalized = text.replace(/^﻿/, '').replace(/\r\n/g, '\n')
  const match = /^---[ \t]*\n([\s\S]*?)\n---[ \t]*(\n|$)/.exec(normalized)
  if (!match) return { block: null, body: normalized }
  return { block: match[1], body: normalized.slice(match[0].length) }
}

export const parseYamlSubset = (block: string): Frontmatter => {
  const out: Frontmatter = {}
  const lines = block.split('\n')
  let i = 0
  while (i < lines.length) {
    const line = lines[i]
    const top = /^([A-Za-z_][\w-]*):[ \t]*(.*)$/.exec(line)
    if (!top) {
      i += 1
      continue
    }
    const [, key, rest] = top
    if (stripComment(rest).trim() !== '') {
      out[key] = scalar(rest)
      i += 1
      continue
    }
    // An empty value: a block list or a one-level map may follow, indented.
    const items: string[] = []
    const map: Record<string, string> = {}
    i += 1
    while (i < lines.length && (/^\s+\S/.test(lines[i]) || lines[i].trim() === '')) {
      const inner = lines[i].trim()
      i += 1
      if (inner === '' || inner.startsWith('#')) continue
      const item = /^-\s*(.*)$/.exec(inner)
      if (item) {
        items.push(unquote(stripComment(item[1])))
        continue
      }
      const pair = /^("[^"]+"|'[^']+'|[^:]+):\s*(.*)$/.exec(inner)
      if (pair) map[unquote(pair[1])] = unquote(stripComment(pair[2]))
    }
    out[key] = items.length > 0 ? items : Object.keys(map).length > 0 ? map : null
  }
  return out
}

/** The legacy config dialects: `key: value` lines and `**Label:** value` lines in the body. */
export const parseLegacyConfig = (body: string): Frontmatter => {
  const out: Frontmatter = {}
  for (const line of body.split('\n')) {
    const bold = /^\s*[-*]?\s*\*\*([^*]+?):?\*\*:?\s*(.+)$/.exec(line)
    if (bold) {
      const key = bold[1].trim().toLowerCase().replace(/\s+/g, '_')
      if (!(key in out)) out[key] = scalar(bold[2])
      continue
    }
    const plain = /^([a-z_][\w-]*):\s+(.+)$/.exec(line)
    if (plain && !(plain[1] in out)) out[plain[1]] = scalar(plain[2])
  }
  return out
}

export const asString = (value: FmValue | undefined): string | null =>
  typeof value === 'string' ? value : typeof value === 'number' || typeof value === 'boolean' ? String(value) : null

export const asList = (value: FmValue | undefined): string[] =>
  Array.isArray(value) ? value : typeof value === 'string' && value !== '' ? value.split(',').map(part => part.trim()).filter(Boolean) : []

export const asNumber = (value: FmValue | undefined): number | null =>
  typeof value === 'number' ? value : typeof value === 'string' && /^\d+$/.test(value) ? Number(value) : null

export const asMap = (value: FmValue | undefined): Record<string, string> =>
  value !== null && typeof value === 'object' && !Array.isArray(value) ? value : {}
