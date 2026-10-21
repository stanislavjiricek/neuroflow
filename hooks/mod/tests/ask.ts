// The engine's question dialog in tests. `$.ui.ask` is a tool.call of AskUserQuestion beneath the plugin, so a test
// answers it with a tool.call hook: each question is recorded with its options in the order the dialog draws them,
// and answered as a person would — by default with the first option, which is what a stray Enter picks.
import type { On } from 'claude-code'

export type Asked = { question: string; options: string[]; header: string }
export type Dialog = {
  /** Every question asked so far, oldest first. */
  asked: Asked[]
  /** What the next questions are answered with (the label of an option, or free text as typed under "Other"). */
  answer: (pick: (asked: Asked) => string) => void
}

/** The first option: what a stray Enter answers. */
export const STRAY_ENTER = (asked: Asked): string => asked.options[0] ?? ''

export const answerAsks = (on: On, pick: (asked: Asked) => string = STRAY_ENTER): Dialog => {
  let answer = pick
  const dialog: Dialog = { asked: [], answer: next => (answer = next) }
  on('tool.call', ($, e, next) => {
    const input = e as unknown as { tool: string; questions?: { question: string; header?: string; options?: ({ label: string } | string)[] }[] }
    if (input.tool !== 'AskUserQuestion') return next(e)
    const first = input.questions?.[0]
    const asked: Asked = {
      question: first?.question ?? '',
      options: (first?.options ?? []).map(option => (typeof option === 'string' ? option : option.label)),
      header: first?.header ?? '',
    }
    dialog.asked.push(asked)
    const text = answer(asked)
    return { result: { questions: input.questions ?? [], answers: { [asked.question]: text } }, text } as never
  })
  return dialog
}
