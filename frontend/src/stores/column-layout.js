// Saved column layouts remember which keys were visible, not which keys
// existed. A column added after that save is absent from the list, and the
// table treats "absent" as switched off. `known` is the set of keys the user
// has already been shown, so a key that is not in it is new and follows the
// default (on, unless the table's default headers leave it off).

export function normalizeLayoutEntry(value) {
  if (Array.isArray(value)) {
    return {
      visible: value
        .map((entry) =>
          entry && typeof entry === 'object' ? entry.key : entry
        )
        .filter((key) => typeof key === 'string'),
      known: null,
    }
  }
  if (value && typeof value === 'object' && Array.isArray(value.visible)) {
    return {
      visible: value.visible.filter((key) => typeof key === 'string'),
      known: Array.isArray(value.known)
        ? value.known.filter((key) => typeof key === 'string')
        : null,
    }
  }
  return { visible: [], known: null }
}

// `defaultKeys` empty means every header is on by default. If none of the
// defaults exist in `headerKeys`, every header is on, so the table is never
// left showing only its untitled (action/select) columns.
// A saved layout with nothing visible (the user hid every column, or the saved
// keys no longer exist) is treated as "no layout" and falls back to the defaults.
// A legacy entry (`known: null`) has no record of columns the user switched
// off, so those come back on once, together with columns that are genuinely new.
// The next save records `known`, and switches made after that stay put.
export function resolveVisibleKeys(layout, headerKeys, defaultKeys) {
  const defaults = defaultKeys?.length ? defaultKeys : headerKeys
  const matchingDefaults = defaults.filter((key) => headerKeys.includes(key))
  const defaultsInHeaders = matchingDefaults.length
    ? matchingDefaults
    : headerKeys
  if (!layout?.visible?.length) {
    return defaultsInHeaders
  }
  const savedVisible = layout.visible.filter((key) => headerKeys.includes(key))
  const seen = new Set(layout.known == null ? savedVisible : layout.known)
  const defaultOn = new Set(defaultsInHeaders)
  const show = new Set(savedVisible)
  for (const key of headerKeys) {
    if (!seen.has(key) && defaultOn.has(key)) {
      show.add(key)
    }
  }
  if (![...show].some((key) => headerKeys.includes(key))) {
    return defaultsInHeaders
  }
  return headerKeys.filter((key) => show.has(key))
}

// Builds the entry to store. The header set a table is given can change under
// one storage key (e.g. an edit mode with fewer columns), so the previous entry
// is merged in rather than replaced: `known` only grows, and visible keys that
// the current headers do not mention are carried over untouched.
export function mergeLayoutForSave(previous, visibleKeys, headerKeys) {
  const prev = previous ? normalizeLayoutEntry(previous) : null
  const known = new Set([
    ...(prev?.known ?? prev?.visible ?? []),
    ...headerKeys,
  ])
  const carriedOver = (prev?.visible ?? []).filter(
    (key) => !headerKeys.includes(key)
  )
  return {
    visible: [...new Set([...visibleKeys, ...carriedOver])],
    known: [...known],
  }
}
