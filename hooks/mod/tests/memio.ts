// An in-memory NfIo for testing the shared helpers in ../lib without an engine.
import type { NfIo, NfRun } from '../lib/io'

export type MemIo = NfIo & { files: Record<string, string>; ran: string[][] }

const norm = (path: string): string => path.replace(/\\/g, '/').replace(/\/+$/, '')

export const memIo = (
  files: Record<string, string>,
  options: { home?: string; now?: number; cwd?: string; run?: (argv: readonly string[]) => NfRun } = {},
): MemIo => {
  const cwd = options.cwd ?? '/work/proj'
  const abs = (path: string): string => norm(/^([A-Za-z]:)?\//.test(norm(path)) ? path : `${cwd}/${path}`)
  const io: MemIo = {
    files: Object.fromEntries(Object.entries(files).map(([path, text]) => [norm(path), text])),
    ran: [],
    read: async path => io.files[abs(path)] ?? null,
    exists: async path => abs(path) in io.files || Object.keys(io.files).some(file => file.startsWith(`${abs(path)}/`)),
    list: async path => {
      const dir = abs(path)
      const seen = new Map<string, boolean>()
      for (const file of Object.keys(io.files)) {
        if (!file.startsWith(`${dir}/`)) continue
        const [head, ...rest] = file.slice(dir.length + 1).split('/')
        seen.set(head, (seen.get(head) ?? false) || rest.length > 0)
      }
      return [...seen].map(([name, isDir]) => ({ name, isDir }))
    },
    write: async (path, text) => {
      io.files[abs(path)] = text
    },
    home: async () => options.home,
    now: async () => options.now ?? 0,
    run: async argv => {
      io.ran.push([...argv])
      if (options.run) return options.run(argv)
      throw new Error('no process in tests')
    },
    pluginRoot: '/plugin',
  }
  return io
}
