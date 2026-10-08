// Path helpers that behave the same on Windows and POSIX. Comparisons fold case and separators
// on Windows-style paths (drive letter or backslashes), because NTFS is case-insensitive.

/** Forward slashes, no trailing slash (except a bare root like "C:/" or "/"). */
export const toSlash = (path: string): string => {
  const slashed = path.replace(/\\/g, '/').replace(/\/{2,}/g, (m, offset) => (offset === 0 ? m : '/'))
  if (slashed === '/' || /^[A-Za-z]:\/$/.test(slashed)) return slashed
  return slashed.replace(/\/+$/, '')
}

export const isWindowsPath = (path: string): boolean => /^[A-Za-z]:[\\/]/.test(path) || path.includes('\\')

/** The key two spellings of one path share: slashes, and lower case for Windows paths. */
export const fold = (path: string): string => {
  const slashed = toSlash(path)
  return isWindowsPath(path) ? slashed.toLowerCase() : slashed
}

export const join = (...parts: string[]): string =>
  toSlash(parts.filter(part => part !== '').join('/'))

export const dirname = (path: string): string => {
  const slashed = toSlash(path)
  const cut = slashed.lastIndexOf('/')
  if (cut < 0) return '.'
  if (cut === 0) return '/'
  const head = slashed.slice(0, cut)
  return /^[A-Za-z]:$/.test(head) ? `${head}/` : head
}

export const isAbsolute = (path: string): boolean => /^[A-Za-z]:[\\/]/.test(path) || path.startsWith('/') || path.startsWith('\\\\')

/** Resolve `path` against `base` when it is relative. Does not touch the file system. */
export const resolveFrom = (base: string, path: string): string => {
  if (isAbsolute(path)) return toSlash(path)
  const out: string[] = []
  for (const part of `${toSlash(base)}/${toSlash(path)}`.split('/')) {
    if (part === '.' || (part === '' && out.length > 0)) continue
    if (part === '..') {
      if (out.length > 1) out.pop()
      continue
    }
    out.push(part)
  }
  return toSlash(out.join('/') || '/')
}

/** True when `path` is `root` or lies under it (by folded spelling, no file system call). */
export const isInside = (path: string, root: string): boolean => {
  const p = fold(path)
  const r = fold(root)
  return p === r || p.startsWith(r.endsWith('/') ? r : `${r}/`)
}

/** `path` relative to `root`, or null when it is outside. */
export const relativeTo = (path: string, root: string): string | null => {
  if (!isInside(path, root)) return null
  const rest = toSlash(path).slice(toSlash(root).length).replace(/^\//, '')
  return rest
}

/** A network or device spelling (\\server\share, //server/share) the mod never touches. */
export const isNetworkPath = (path: string): boolean => /^[\\/]{2}/.test(path)
