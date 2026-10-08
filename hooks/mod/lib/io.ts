// The engine calls shared helpers need, as plain closures. The validator follows `$` only into
// functions declared in the same file, so `$` never crosses a file boundary: each feature file
// builds an NfIo from its own `$` (see ioOf in features/scope.ts) and passes that instead.
// Tests pass an in-memory NfIo (tests/memio.ts).

export type NfRun = { exitCode: number; stdout: string; stderr: string }

export type NfIo = {
  /** File text, or null when it is missing or unreadable. */
  read: (path: string) => Promise<string | null>
  exists: (path: string) => Promise<boolean>
  /** Entries of a directory (empty when it is missing). */
  list: (path: string) => Promise<{ name: string; isDir: boolean }[]>
  write: (path: string, text: string) => Promise<void>
  /** The user's home folder (HOME, or USERPROFILE on Windows), if set. */
  home: () => Promise<string | undefined>
  now: () => Promise<number>
  /** Runs a host command by argv; rejects when the program cannot start (callers also guard a synchronous throw). */
  run: (argv: readonly string[], init: { cwd?: string; timeoutMs?: number; env?: Record<string, string> }) => Promise<NfRun>
  /** The plugin's own folder (holding .claude-plugin/plugin.json), absolute. */
  pluginRoot: string
}
