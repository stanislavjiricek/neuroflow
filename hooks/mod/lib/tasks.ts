// The project task board, read exactly as commands/tasks.md defines it: one file per task at
// tasks/{column}/{slug}.md, the folder is the column, columns from tasks/config.json or the defaults.
import type { NfBoard, NfCard } from '../../../types'
import { asList, asString, parseYamlSubset, splitFrontmatter } from './frontmatter'

export type Column = { id: string; label: string; archive: boolean }

export const DEFAULT_COLUMNS: readonly Column[] = ['inbox', 'ready', 'active', 'review', 'meeting', 'done', 'archive'].map(id => ({
  id,
  label: id,
  archive: id === 'archive',
}))

/** Columns from tasks/config.json (`columns[].id`, `label`, `archive`), else the defaults. */
export const columnsFromConfig = (configJson: string | null): readonly Column[] => {
  if (configJson === null) return DEFAULT_COLUMNS
  try {
    const parsed = JSON.parse(configJson) as { columns?: { id?: unknown; label?: unknown; archive?: unknown }[] }
    const columns = (parsed.columns ?? [])
      .filter(column => typeof column.id === 'string' && column.id !== '')
      .map(column => ({ id: String(column.id), label: typeof column.label === 'string' ? column.label : String(column.id), archive: column.archive === true }))
    return columns.length > 0 ? columns : DEFAULT_COLUMNS
  } catch {
    return DEFAULT_COLUMNS
  }
}

/** One task file as a card; `today` is YYYY-MM-DD. Legacy keys (assignee, responsible) read as owner. */
export const parseTask = (text: string, slug: string, today: string, isDone: boolean): NfCard => {
  const { block } = splitFrontmatter(text)
  const fm = block === null ? {} : parseYamlSubset(block)
  const due = asString(fm.due)
  const owner = asString(fm.owner) ?? asString(fm.assignee) ?? asString(fm.responsible) ?? asList(fm.owner)[0] ?? null
  return {
    slug,
    title: asString(fm.title) ?? slug,
    owner,
    due: due !== null && /^\d{4}-\d{2}-\d{2}$/.test(due) ? due : null,
    overdue: !isDone && due !== null && /^\d{4}-\d{2}-\d{2}$/.test(due) && due < today,
  }
}

/** The board as the Rendering rules say: board order, overdue first, done/archive counted not drawn. */
export const buildBoard = (columns: readonly Column[], cards: Readonly<Record<string, NfCard[]>>): NfBoard => {
  const drawn = columns.filter(column => column.id !== 'done' && !column.archive)
  const done = (cards.done ?? []).length
  const archived = columns.filter(column => column.archive).reduce((sum, column) => sum + (cards[column.id] ?? []).length, 0)
  return {
    columns: drawn
      .map(column => {
        const list = [...(cards[column.id] ?? [])].sort((a, b) => Number(b.overdue) - Number(a.overdue) || (a.due ?? '9999').localeCompare(b.due ?? '9999'))
        return { id: column.id, label: column.label, cards: list.slice(0, 5), total: list.length }
      })
      .filter(column => column.total > 0 || column.id === 'inbox' || column.id === 'active'),
    done,
    archived,
  }
}

/** A card as one text line: `⚠ rerun-ica @li due 08-20`. */
export const cardLine = (card: NfCard): string =>
  `${card.overdue ? '⚠ ' : ''}${card.title}${card.owner ? ` @${card.owner}` : ''}${card.due ? ` due ${card.due.slice(5)}` : ''}`
