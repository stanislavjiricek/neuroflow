// Reading a drawn tree in tests: what `ui.drawn()` returns is plain data (RenderElement), so the Buttons, Inputs and
// texts a view drew can be listed without the kit's own queries.
import { VIEW_KEYS } from '../lib/keys'
import type { View } from '../lib/keys'

export type DrawnElement = { type: string; key: string; props: Record<string, unknown> }
export type DrawnButton = { key: string; label: string; hotkey?: string; plain?: boolean; dimColor?: boolean; autoFocus?: boolean }

/** Every element of the given type in a drawn tree, in document order. */
export const elements = (tree: unknown, type: string): DrawnElement[] => {
  const out: DrawnElement[] = []
  const walk = (node: unknown): void => {
    if (node === null || typeof node !== 'object') return
    if (Array.isArray(node)) {
      for (const child of node) walk(child)
      return
    }
    const element = node as { type?: unknown; props?: Record<string, unknown>; children?: unknown }
    if (element.type === type) out.push({ type, key: String(element.props?.key ?? ''), props: element.props ?? {} })
    walk(element.children)
  }
  walk(tree)
  return out
}

/**
 * What each outermost Text of a drawn tree reads, its nested Texts (a glyph in its colour, a dim part) joined in, in
 * document order: the rows a person sees, whatever colours split them.
 */
export const lines = (tree: unknown): string[] => {
  const out: string[] = []
  const textOf = (node: unknown): string => {
    if (typeof node === 'string') return node
    if (node === null || typeof node !== 'object') return ''
    if (Array.isArray(node)) return node.map(textOf).join('')
    return textOf((node as { children?: unknown }).children)
  }
  const walk = (node: unknown): void => {
    if (node === null || typeof node !== 'object') return
    if (Array.isArray(node)) {
      for (const child of node) walk(child)
      return
    }
    const element = node as { type?: unknown; children?: unknown }
    if (element.type === 'Text') out.push(textOf(element.children))
    else walk(element.children)
  }
  walk(tree)
  return out
}

/** Every Button in a drawn tree, with what decides how it reads and how it is pressed. */
export const buttons = (tree: unknown): DrawnButton[] =>
  elements(tree, 'Button').map(({ key, props }) => ({
    key,
    label: String(props.label ?? ''),
    ...(typeof props.hotkey === 'string' ? { hotkey: props.hotkey } : {}),
    ...(props.plain === true ? { plain: true } : {}),
    ...(props.dimColor === true ? { dimColor: true } : {}),
    ...(props.autoFocus === true ? { autoFocus: true } : {}),
  }))

/** The hotkeys a drawing offers, in document order. */
export const hotkeys = (tree: unknown): string[] => buttons(tree).flatMap(button => (button.hotkey === undefined ? [] : [button.hotkey]))

/**
 * What is wrong with a drawing's keys against the key registry (lib/keys.ts), as lines (none: all is well): a
 * hotkey the view does not list, one drawn twice, one on a Button that is not plain (its key would not show).
 */
export const keyProblems = (tree: unknown, view: View): string[] => {
  const allowed = VIEW_KEYS[view]
  const problems: string[] = []
  const seen = new Map<string, string>()
  for (const button of buttons(tree)) {
    if (button.hotkey === undefined) continue
    if (!(button.hotkey in allowed)) problems.push(`${button.key}: ${button.hotkey} is not a ${view} key`)
    const twin = seen.get(button.hotkey)
    if (twin !== undefined) problems.push(`${button.key}: ${button.hotkey} is already ${twin}'s`)
    seen.set(button.hotkey, button.key)
    if (button.plain !== true) problems.push(`${button.key}: a hotkey on a Button that is not plain does not show`)
  }
  return problems
}
