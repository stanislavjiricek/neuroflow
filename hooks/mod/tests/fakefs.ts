// A file system in memory for tests: answers the fs.* op events beneath the plugin, the way the
// engine would (claude plugin test has no fs). Op hooks answer `{ value }` (or throw, which the
// caller sees as a rejection).
//
// On Windows the engine hands ops absolute, drive-lettered paths ("C:\work\proj\…") even for
// "/work/proj/…", so keys drop the drive and use forward slashes: fixtures use POSIX paths on every OS.
import type { On } from 'claude-code'

export type FakeFs = { files: Record<string, string>; writes: string[] }

export const fsKey = (path: string): string =>
  path.replace(/\\/g, '/').replace(/\/+$/, '').replace(/^[A-Za-z]:(?=\/)/, '')

export const fakeFs = (on: On, initial: Record<string, string>, cwd = '/work/proj', surfaces: readonly string[] = ['terminal']): FakeFs => {
  const fs: FakeFs = { files: Object.fromEntries(Object.entries(initial).map(([path, text]) => [fsKey(path), text])), writes: [] }
  const abs = (path: string): string => (fsKey(path).startsWith('/') ? fsKey(path) : fsKey(`${cwd}/${path}`))
  const isDir = (path: string): boolean => Object.keys(fs.files).some(file => file.startsWith(`${abs(path)}/`))

  on('fs.read', ($, e) => {
    const text = fs.files[abs(e.path)]
    if (text === undefined) throw new Error(`ENOENT: ${e.path}`)
    return { value: text }
  })
  on('fs.exists', ($, e) => ({ value: abs(e.path) in fs.files || isDir(e.path) }))
  on('fs.write', ($, e) => {
    fs.files[abs(e.path)] = e.text
    fs.writes.push(abs(e.path))
    return { value: undefined }
  })
  on('fs.stat', ($, e) => {
    const path = abs(e.path)
    if (path in fs.files) return { value: { kind: 'file', size: fs.files[path].length, mtimeMs: 0, isLink: false, ...(e.resolve ? { realPath: path } : {}) } }
    if (isDir(path)) return { value: { kind: 'directory', size: 0, mtimeMs: 0, isLink: false, ...(e.resolve ? { realPath: path } : {}) } }
    throw new Error(`ENOENT: ${e.path}`)
  })
  on('fs.list', ($, e) => {
    const dir = abs(e.path || '.')
    const names = new Map<string, 'file' | 'directory'>()
    for (const file of Object.keys(fs.files)) {
      if (!file.startsWith(`${dir}/`)) continue
      const [head, ...rest] = file.slice(dir.length + 1).split('/')
      names.set(head, rest.length > 0 ? 'directory' : 'file')
    }
    return { value: [...names].map(([name, kind]) => ({ name, kind, size: 0, mtimeMs: 0, isLink: false })) }
  })
  on('session.cwd', () => ({ value: cwd }))
  on('session.root', () => ({ value: cwd }))
  on('session.surfaces', () => ({ value: surfaces }))
  return fs
}
