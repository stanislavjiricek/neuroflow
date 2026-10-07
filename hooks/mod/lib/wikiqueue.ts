// The auto-wiki review queue (wiki-protocol skill → Auto capture): cards in .neuroflow/wiki/.pending/, written when a
// command logs a decision worth keeping, accepted or skipped by the person, turned into pages only by the
// normal /wiki --add flow. Pure functions over text; the mod and the prose share the format and the rubric.
import { asString, parseYamlSubset, splitFrontmatter } from './frontmatter'

export const PENDING_DIR = '.neuroflow/wiki/.pending'

export type WikiCard = {
  title: string
  type: string
  evidence: string
  captured: string
  by: 'mod' | 'model'
  status: 'pending' | 'accepted' | 'skipped'
  body: string
}

const CARD_TYPES = ['decision', 'method', 'concept', 'question']

/** A card file, or null when it is not one. A missing status counts as pending. */
export const parseCard = (text: string): WikiCard | null => {
  const { block, body } = splitFrontmatter(text)
  if (block === null) return null
  const fm = parseYamlSubset(block)
  const title = asString(fm.title)
  if (title === null || title.trim() === '') return null
  const status = asString(fm.status) ?? 'pending'
  return {
    title: title.trim(),
    type: asString(fm.type) ?? 'decision',
    evidence: asString(fm.evidence) ?? '',
    captured: asString(fm.captured) ?? '',
    by: asString(fm.by) === 'model' ? 'model' : 'mod',
    status: status === 'accepted' || status === 'skipped' ? status : 'pending',
    body: body.trim(),
  }
}

const yamlValue = (text: string): string => (/[:#'"\n]|^\s|\s$/.test(text) ? JSON.stringify(text) : text)

/** The card file text (wiki-protocol skill → card format). */
export const cardText = (card: WikiCard): string =>
  [
    '---',
    `title: ${yamlValue(card.title)}`,
    `type: ${card.type}`,
    `evidence: ${yamlValue(card.evidence)}`,
    `captured: ${card.captured}`,
    `by: ${card.by}`,
    `status: ${card.status}`,
    '---',
    card.body,
    '',
  ].join('\n')

/** `status: pending` → `status: skipped` (or accepted), leaving the rest of the card as it is. */
export const setCardStatus = (text: string, status: 'accepted' | 'skipped'): string =>
  /^status:\s*\S+/m.test(text) ? text.replace(/^status:\s*\S+/m, `status: ${status}`) : text.replace(/^---\n/, `---\nstatus: ${status}\n`)

/** A file-name slug from a title: lowercase ASCII words joined by hyphens, at most 60 characters. */
export const slugify = (title: string): string =>
  title
    .normalize('NFKD')
    .replace(/[^\x00-\x7f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 60)
    .replace(/-+$/, '') || 'card'

/** The judge's instructions: the rubric of the wiki-protocol skill's Auto capture section. */
export const WIKI_JUDGE_SYSTEM = [
  'You decide whether research decisions just logged by a research assistant deserve a page in the project wiki.',
  'Rules: nothing is the normal answer. A card needs evidence: name the log entry it comes from. Never a result, never a number from an analysis, never participant data.',
  'A decision deserves a card only when it is reusable knowledge — why a method, parameter or design was chosen over its alternatives — not a routine step.',
  'Skip anything whose title is already in the wiki or in the queue (pending, accepted or skipped). At most two cards.',
  'Answer with JSON only: {"cards": [{"title": "...", "type": "decision|method|concept|question", "summary": "one to three sentences quoting the evidence", "evidence": "which entry"}]} — or {"cards": []}.',
].join('\n')

/** The judge's answer as cards (at most two, results and empty titles dropped). */
export const parseJudge = (text: string): { title: string; type: string; summary: string; evidence: string }[] => {
  const start = text.indexOf('{')
  const end = text.lastIndexOf('}')
  if (start < 0 || end <= start) return []
  try {
    const data = JSON.parse(text.slice(start, end + 1)) as { cards?: unknown }
    if (!Array.isArray(data.cards)) return []
    return data.cards
      .filter((card): card is { title: string; type?: string; summary?: string; evidence?: string } => typeof (card as { title?: unknown })?.title === 'string')
      .filter(card => !/result/i.test(String(card.type ?? '')))
      .map(card => ({
        title: card.title.trim(),
        type: CARD_TYPES.includes(String(card.type)) ? String(card.type) : 'decision',
        summary: String(card.summary ?? '').trim(),
        evidence: String(card.evidence ?? '').trim(),
      }))
      .filter(card => card.title !== '' && card.summary !== '' && card.evidence !== '')
      .slice(0, 2)
  } catch {
    return []
  }
}

/** The titles a new card may not take (lowercase): the wiki's pages and every card in the queue, whatever its
 *  status — a skipped card is never raised again, an accepted one is already a page or on its way. */
export const takenTitles = (pages: readonly string[], queued: readonly (WikiCard | null)[]): Set<string> =>
  new Set([...pages, ...queued.flatMap(card => (card === null ? [] : [card.title]))].map(title => title.trim().toLowerCase()))

/** Whether capture may run: the person opted in (`wiki_auto: ask` in user.yaml) and the project allows it. */
export const captureAllowed = (userYaml: string | null, projectPolicy: string | null): boolean => {
  if (projectPolicy === 'forbid') return false
  if (userYaml === null) return false
  return /^wiki_auto:\s*["']?ask["']?\s*(#.*)?$/m.test(userYaml)
}
