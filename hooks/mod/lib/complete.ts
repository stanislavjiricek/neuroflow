// Typeahead for the typed paths into the views (the prompt.autocomplete event): phase ids after `/neuroflow:phase `,
// the dashboard's tabs after `/neuroflow:dashboard `, levels after `--level `, hive folders after `--hive `, and after
// `/neuroflow:tasks … --move ` the open cards of the level the line names, then the columns that card can move to.
// Pure (no `$`, no file read — charter rule 20): the hook hands it the state the mod already holds, so the cards and
// hives come once the boards have been read this session (the boards, or the dashboard's now or tasks tab).
import type { NfTaskLevel, NfTaskView } from '../../../types'
import { DASHBOARD_TABS } from './keys'
import { phaseStateMark, pickerOrder } from './phases'
import { moveTargets } from './tasks'

/** One typeahead row: what taking it writes over the token, and the dim line beside it. */
export type Suggestion = { text: string; description?: string }

/** The prompt box as the event hands it: the draft, the cursor, the token at the cursor and where it starts. */
export type CompleteInput = { text: string; cursor: number; token: string; start: number }

/** What the mod's state holds for the typeahead: the phases and, once read, every level's board. */
export type CompleteContext = { phase: string | null; visited: readonly string[]; recommended: readonly string[]; tasks: NfTaskView | null }

/** Rows at most, beneath the engine's own. */
export const MAX_SUGGESTIONS = 8

/** The levels `/tasks`, `/meeting` and `/flowie` take (`--level project|flowie|hive`). */
const LEVELS: readonly { id: string; what: string }[] = [
  { id: 'project', what: 'this repository\'s board' },
  { id: 'flowie', what: 'your own board' },
  { id: 'hive', what: 'a team\'s board, with --hive' },
]

/**
 * The commands that take `--level` (commands/tasks.md, meeting.md, flowie.md) and `--hive` (tasks.md only: the
 * `--hive` in migrate.md is a flag of its scripts, which the prose builds itself).
 */
const TAKES_LEVEL: ReadonlySet<string> = new Set(['tasks', 'meeting', 'flowie'])
const TAKES_HIVE: ReadonlySet<string> = new Set(['tasks'])

/** The words of the line before the token, the command first: `/neuroflow:tasks`, `--level`, `hive`, … */
const wordsBefore = (input: CompleteInput): string[] => input.text.slice(0, input.start).trim().split(/\s+/).filter(word => word !== '')

/** The neuroflow command a line starts with (`/neuroflow:tasks` or `/tasks`), or null. */
const commandOf = (words: readonly string[]): string | null => /^\/(?:neuroflow:)?([a-z][a-z-]*)$/.exec(words[0] ?? '')?.[1] ?? null

/** The value an option has earlier in the line (`--level hive`), or null. */
const optionValue = (words: readonly string[], option: string): string | null => {
  const at = words.lastIndexOf(option)
  return at >= 0 ? (words[at + 1] ?? null) : null
}

/**
 * The board a `/tasks` line names with `--level` and `--hive`: the project's when it names none. At hive level without
 * `--hive`, the one hive board there is (commands/tasks.md: a single joined hive needs no flag); none among several.
 */
const namedLevel = (tasks: NfTaskView, words: readonly string[]): NfTaskLevel | undefined => {
  const level = optionValue(words, '--level')
  if (level === 'flowie') return tasks.levels.find(item => item.kind === 'flowie')
  if (level === 'hive') {
    const hive = optionValue(words, '--hive')
    const hives = tasks.levels.filter(item => item.kind === 'hive')
    return hive === null ? (hives.length === 1 ? hives[0] : undefined) : hives.find(item => item.name === hive)
  }
  return tasks.levels.find(item => item.kind === 'project')
}

const starts = (value: string, token: string): boolean => value.toLowerCase().startsWith(token.toLowerCase())

/** The rows for the token at the cursor, or none when the line is not one of the paths above. */
export const completions = (input: CompleteInput, context: CompleteContext): Suggestion[] => {
  const token = input.token
  if (token === '' || token.startsWith('/')) return []
  const words = wordsBefore(input)
  const command = commandOf(words)
  if (command === null) return []
  const last = words[words.length - 1] ?? ''
  const rows = ((): Suggestion[] => {
    // /neuroflow:phase <phase>: switches at once (the mod answers it), so the id is the whole argument. Each phase
    // carries the mark the picker gives it (phaseStateMark).
    if (command === 'phase' && words.length === 1) {
      return pickerOrder(context.phase, context.recommended)
        .filter(phase => starts(phase.id, token))
        .map(phase => ({ text: phase.id, description: `${phaseStateMark(phase.id, context.phase, context.visited, context.recommended)} · ${phase.label}` }))
    }
    // /neuroflow:dashboard <tab>: opens the pane on that tab.
    if (command === 'dashboard' && words.length === 1) {
      return DASHBOARD_TABS.filter(tab => starts(tab.id, token)).map(tab => ({ text: tab.id, description: `tab ${tab.digit}` }))
    }
    if (last === '--level' && TAKES_LEVEL.has(command)) return LEVELS.filter(level => starts(level.id, token)).map(level => ({ text: level.id, description: level.what }))
    if (last === '--hive' && TAKES_HIVE.has(command)) {
      return (context.tasks?.levels ?? [])
        .filter(level => level.kind === 'hive' && starts(level.name, token))
        .map(level => ({ text: level.name, description: `hive · ${level.open} open` }))
    }
    if (command !== 'tasks' || context.tasks === null) return []
    const level = namedLevel(context.tasks, words)
    if (level === undefined || level.kind === 'remote') return []
    const cards = level.board.columns.flatMap(column => column.cards.map(card => ({ card, column: column.id })))
    // --move <slug>: the level's open cards.
    if (last === '--move') return cards.filter(({ card }) => starts(card.slug, token)).map(({ card, column }) => ({ text: card.slug, description: `${card.title} · ${column}` }))
    // --move <slug> <column>: where that card can go.
    if (words[words.length - 2] === '--move') {
      const from = cards.find(({ card }) => card.slug === last)?.column ?? null
      if (from === null) return []
      return moveTargets(level.board, from)
        .filter(column => starts(column, token))
        .map(column => ({ text: column, description: `move ${last} here` }))
    }
    return []
  })()
  return rows.slice(0, MAX_SUGGESTIONS)
}
