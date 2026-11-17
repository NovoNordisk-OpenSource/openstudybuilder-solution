import terms from '@/api/controlledTerminology/terms'
import footnoteConstants from '@/constants/footnotes'
import dataFormating from '@/utils/dataFormating'

let soaFootnoteType = null

// Resolves the "SoA" footnote type term, or null when the codelist lacks it.
// Only a found term is cached, so a missing one is looked up again next call.
export async function getSoaFootnoteType() {
  if (!soaFootnoteType) {
    const resp = await terms.getTermsByCodelist('footnoteTypes')
    soaFootnoteType =
      resp.data.items.find(
        (item) =>
          item.sponsor_preferred_name === footnoteConstants.FOOTNOTE_TYPE_SOA
      ) ?? null
  }
  return soaFootnoteType
}

// Mirrors the backend SoAItemType; cells also carry refs to library objects
// ('Activity', 'CTTerm', ...) that a footnote cannot reference.
const REFERENCEABLE_ITEM_TYPES = new Set([
  'StudyActivitySchedule',
  'StudyActivity',
  'StudyActivityInstance',
  'StudyActivitySubGroup',
  'StudyActivityGroup',
  'StudySoAGroup',
  'StudyEpoch',
  'StudyVisit',
  'StudySoAFootnote',
])

export function isReferenceableRef(cellRef) {
  return REFERENCEABLE_ITEM_TYPES.has(cellRef.type)
}

export function toReferencedItem(cellRef) {
  return {
    item_uid: cellRef.uid,
    item_type: cellRef.type,
    // Placeholder: the backend ignores item_name on write and resolves it on read.
    item_name: cellRef.type,
    via_propagated_cell: Boolean(cellRef.viaPropagatedCell),
  }
}

export function normalizeFootnoteText(text) {
  return text.replace(/\s+/g, ' ').trim()
}

export function getFootnoteNamePlain(footnote) {
  return footnote.template?.name_plain ?? footnote.footnote?.name_plain ?? ''
}

// The protocol prints a letter only for the footnotes it shows, so `protocolLetters`
// (footnote uid -> letter) covers some of the study's footnotes. The others (unlinked,
// or linked only to hidden rows) get the next free letters in the order the footnotes
// endpoint returns them, which keeps every letter unique.
export function assignFootnoteLetters(footnotes, protocolLetters) {
  const letters = new Map()
  const withoutLetter = []
  footnotes.forEach((footnote) => {
    const letter = protocolLetters[footnote.uid]
    if (letter) {
      letters.set(footnote.uid, letter)
    } else {
      withoutLetter.push(footnote)
    }
  })
  const taken = new Set(letters.values())
  let position = 0
  withoutLetter.forEach((footnote) => {
    let letter
    do {
      position += 1
      letter = dataFormating.footnoteSymbol(position)
    } while (taken.has(letter))
    letters.set(footnote.uid, letter)
  })
  return letters
}

// A `via_propagated_cell` item matches the propagated checkmark and the item's own cell;
// any other item matches only its own cell, never a propagated checkmark.
export function referencedItemMatchesRef(referencedItem, cellRef) {
  if (referencedItem.item_uid !== cellRef.uid) {
    return false
  }
  if (referencedItem.via_propagated_cell) {
    return true
  }
  return !cellRef.viaPropagatedCell
}

// Keeps one item per uid like the backend, preferring the one via a propagated cell,
// as that one is also shown on the item's own cell.
export function addReferencedItems(referencedItems, newItems) {
  const merged = new Map(referencedItems.map((item) => [item.item_uid, item]))
  for (const item of newItems) {
    if (!merged.has(item.item_uid) || item.via_propagated_cell) {
      merged.set(item.item_uid, item)
    }
  }
  return [...merged.values()]
}

// Linking and unlinking send a footnote's whole list of referenced items, rebuilt from the store,
// so the requests must run one at a time and read the store only once they start.
// Module-level on purpose: the queue has to outlive the components and cell selections that fill it.
let footnoteTaskQueue = Promise.resolve()

export function enqueueFootnoteTask(task) {
  const result = footnoteTaskQueue.then(task)
  footnoteTaskQueue = result.catch(() => {})
  return result
}

export function isSameReferencedItem(item, otherItem) {
  return (
    item.item_uid === otherItem.item_uid &&
    Boolean(item.via_propagated_cell) === Boolean(otherItem.via_propagated_cell)
  )
}
