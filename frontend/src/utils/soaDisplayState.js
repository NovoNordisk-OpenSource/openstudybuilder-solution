const LEVEL_STYLES = ['group', 'subGroup']

// Group and subgroup rows of activities that have none (e.g. placeholders) come without refs,
// so they would all share one key. Their key is derived from the first row below them that has
// a uid, which is normally their own activity. Adding, removing or moving other rows therefore
// leaves the key unchanged. For a shared ref-less group the first activity below it is used, so
// its key changes when that activity changes, and the group then counts as a new row.
export function assignRowDisplayUids(rows) {
  const syntheticUids = new Set()
  let nextUid
  for (let index = rows.length - 1; index >= 0; index--) {
    const row = rows[index]
    const firstCell = row.cells?.[0]
    const uid = firstCell?.refs?.[0]?.uid
    if (uid) {
      row.displayUid = uid
      nextUid = uid
    } else if (LEVEL_STYLES.includes(firstCell?.style)) {
      const baseUid = `${firstCell.style}-before-${nextUid}`
      let displayUid = baseUid
      for (let copy = 2; syntheticUids.has(displayUid); copy++) {
        displayUid = `${baseUid}-${copy}`
      }
      syntheticUids.add(displayUid)
      row.displayUid = displayUid
    } else {
      row.displayUid = undefined
    }
  }
}

export function buildRowsDisplayState(rows, isActivityRow) {
  const state = {}
  let currentSoaGroup
  let currentGroup
  let currentSubGroup
  let currentActivity
  for (const row of rows) {
    if (!row.cells?.length) {
      continue
    }
    const key = `row-${row.displayUid}`
    const style = row.cells[0].style
    if (style === 'soaGroup') {
      state[key] = { value: false }
      currentGroup = null
      currentSubGroup = null
      currentSoaGroup = row.displayUid
    } else if (style === 'group') {
      state[key] = { value: false, parent: currentSoaGroup }
      currentSubGroup = null
      currentGroup = row.displayUid
    } else if (style === 'subGroup') {
      state[key] = { value: false, parent: currentGroup }
      currentSubGroup = row.displayUid
    } else if (isActivityRow(row)) {
      state[key] = { value: false, parent: currentSubGroup }
      currentActivity = row.displayUid
    } else if (style === 'activityInstance') {
      // Only the operational layout has instance rows, nested under their activity
      state[key] = { value: false, parent: currentActivity }
    }
  }
  return state
}

// Rows without a saved value did not exist before (a new group, or an activity moved or added
// into one), so they open to keep the change visible. Saved values, including false, are kept.
export function applySavedExpandState(state, savedValues) {
  for (const key in state) {
    state[key].value = savedValues[key] ?? true
  }
}
