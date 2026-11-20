// Pure comparison logic for the CRF Compare tab. No Vue, no API imports, so it
// can be unit-tested with `node --test` (see tests/fixtures/crfCompare.test.mjs).
//
// The LEFT form is annotated against the RIGHT form, which is the baseline:
//   added   - the left has something the right does not
//   missing - the right has something the left does not
//   changed - both have it, but a compared value differs

export const TEXT_TYPES = {
  description: 'Description',
  question: 'Question',
  designNotes: 'osb:DesignNotes',
  completionInstructions: 'osb:CompletionInstructions',
}

// Attributes that are only compared when the user switches them on.
export const OPTIONAL_FIELDS = [
  'sourceValue',
  'activityInstance',
  'designNotes',
  'completionInstructions',
  'sdtm',
  'keys',
]

const text = (value) => (value == null ? '' : String(value))

const aliasEntries = (raw) =>
  (raw.aliases || []).map((alias) => ({
    key: `${alias.context}|${alias.name}`,
    label: `${alias.name} (${alias.context})`,
  }))

const vendorEntry = (kind, vendor) => {
  const name = vendor.name || vendor.uid
  const value = text(vendor.value)
  return {
    key: `${kind}:${name}:${value}`,
    group: `${kind}:${name}`,
    label: value ? `${name} = ${value}` : name,
  }
}

const vendorEntries = (raw) => [
  ...(raw.vendor_elements || []).map((entry) => vendorEntry('element', entry)),
  ...(raw.vendor_attributes || []).map((entry) =>
    vendorEntry('attribute', entry)
  ),
  ...(raw.vendor_element_attributes || []).map((entry) =>
    vendorEntry('elementAttribute', entry)
  ),
]

const scalar = (name, field = name) => ({
  name,
  kind: 'scalar',
  read: (raw) => text(raw[field]),
})
const list = (name, read) => ({ name, kind: 'list', read })
const descriptions = {
  name: 'descriptions',
  kind: 'text',
  read: (raw) => textsOfType(raw.translated_texts, TEXT_TYPES.description),
}

// Attributes that can be added to the comparison on top of the built-in ones.
// `scalar` values are compared as text, `list` ones as keyed lists and `text`
// ones per language. A user switches one on with the key `${level}.${name}`.
export const ATTRIBUTES = {
  form: [
    scalar('oid'),
    scalar('repeating'),
    scalar('sdtmVersion', 'sdtm_version'),
    list('aliases', aliasEntries),
    descriptions,
    list('vendor', vendorEntries),
  ],
  group: [
    scalar('oid'),
    scalar('repeating'),
    scalar('isReferenceData', 'is_reference_data'),
    scalar('sasDatasetName', 'sas_dataset_name'),
    scalar('origin'),
    scalar('purpose'),
    scalar('comment'),
    list('sdtmDomains', (raw) =>
      (raw.sdtm_domains || []).map((domain) => ({
        key: domain.submission_value || domain.name || domain.term_uid,
        label: domain.name || domain.submission_value || domain.term_uid,
      }))
    ),
    list('aliases', aliasEntries),
    descriptions,
    list('vendor', vendorEntries),
  ],
  item: [
    scalar('oid'),
    scalar('significantDigits', 'significant_digits'),
    scalar('sasFieldName', 'sas_field_name'),
    scalar('origin'),
    scalar('comment'),
    list('aliases', aliasEntries),
    {
      name: 'codelist',
      kind: 'scalar',
      read: (raw) =>
        raw.codelist
          ? text(raw.codelist.name || raw.codelist.submission_value) ||
            raw.codelist.uid
          : '',
    },
    {
      name: 'externalQuestion',
      kind: 'scalar',
      read: (raw) =>
        raw.external_question
          ? text(
              raw.external_question.name ||
                raw.external_question.submission_value
            ) || text(raw.external_question.uid)
          : '',
    },
    descriptions,
    list('vendor', vendorEntries),
  ],
}

export const attributeKey = (level, name) => `${level}.${name}`

function readAttributes(level, raw) {
  const attrs = {}
  for (const def of ATTRIBUTES[level]) attrs[def.name] = def.read(raw)
  return attrs
}

const EMPTY_ITEM = {
  uid: null,
  name: '',
  prompt: '',
  datatype: '',
  length: null,
  mandatory: false,
  keys: '',
  sdtm: '',
  question: {},
  designNotes: {},
  completionInstructions: {},
  terms: [],
  units: [],
  activityInstances: [],
}

const normalizeName = (name) => (name || '').trim().toLowerCase()

function sortByOrder(list) {
  return [...list].sort(
    (a, b) =>
      (a.order ?? Number.MAX_SAFE_INTEGER) -
      (b.order ?? Number.MAX_SAFE_INTEGER)
  )
}

function textsOfType(translatedTexts, type) {
  const byLanguage = {}
  for (const entry of translatedTexts || []) {
    if (entry.text_type === type) {
      byLanguage[entry.language] = entry.text
    }
  }
  return byLanguage
}

// A file has no version, so when either side comes from one the Version part is
// left out of the comparison.
const FILE_VERSION_KEY = 'Version=file'
const withoutVersion = (keys) => keys.replace(/Version=[^,\]]*,? ?/, '')

export function keysDiffer(left, right) {
  if (left === right) return false
  if (left.includes(FILE_VERSION_KEY) || right.includes(FILE_VERSION_KEY)) {
    return withoutVersion(left) !== withoutVersion(right)
  }
  return true
}

// Mirrors the "Keys" display of the CRF HTML template (api/templates/odm/crf.html).
export function formatKeys(raw, extra = []) {
  const parts = [
    `OID=${raw.oid ?? ''}`,
    `Version=${raw.version ?? ''}`,
    ...extra,
  ]
  return `[${parts.join(', ')}]`
}

export function normalizeItem(ref, item) {
  const datatype = item.datatype?.submission_value || item.datatype?.name || ''
  return {
    uid: item.uid,
    name: item.name,
    version: item.version,
    prompt: item.prompt || '',
    datatype,
    length: item.length ?? null,
    mandatory: ref?.mandatory === 'Yes' || ref?.mandatory === true,
    keys: formatKeys(item, [
      `DataType=${datatype}`,
      ...(item.length != null ? [`Length=${item.length}`] : []),
    ]),
    sdtm: item.sds_var_name || '',
    question: textsOfType(item.translated_texts, TEXT_TYPES.question),
    designNotes: textsOfType(item.translated_texts, TEXT_TYPES.designNotes),
    completionInstructions: textsOfType(
      item.translated_texts,
      TEXT_TYPES.completionInstructions
    ),
    terms: sortByOrder(item.terms || []).map((term) => ({
      key: term.term_uid || term.name,
      label: term.display_text || term.name || term.submission_value || '',
      sourceValue: term.submission_value || '',
    })),
    units: sortByOrder(item.unit_definitions || []).map((unit) => ({
      key: unit.name || unit.uid,
      label: unit.name || '',
    })),
    activityInstances: (item.activity_instances || []).map((instance) => ({
      key: instance.activity_instance_uid || instance.activity_instance_name,
      label: instance.activity_instance_name || instance.activity_instance_uid,
    })),
    attrs: readAttributes('item', item),
    raw: item,
    ref: ref || null,
  }
}

export function normalizeFormTree(tree) {
  return {
    uid: tree.form.uid,
    name: tree.form.name,
    libraryName: tree.form.library_name,
    version: tree.form.version,
    status: tree.form.status,
    attrs: readAttributes('form', tree.form),
    groups: tree.groups.map(({ ref, group, items }) => ({
      uid: group.uid,
      name: group.name,
      version: group.version,
      mandatory: ref?.mandatory === 'Yes' || ref?.mandatory === true,
      keys: formatKeys(group),
      attrs: readAttributes('group', group),
      raw: group,
      items: items.map((entry) => normalizeItem(entry.ref, entry.item)),
    })),
  }
}

export function normalizeCollectionTree(tree) {
  return {
    uid: tree.collection.uid,
    name: tree.collection.name,
    libraryName: tree.collection.library_name,
    version: tree.collection.version,
    status: tree.collection.status,
    forms: tree.forms.map(normalizeFormTree),
  }
}

export function collectLanguages(normalizedForm) {
  if (normalizedForm?.forms) {
    const languages = new Set()
    normalizedForm.forms.forEach((form) =>
      collectLanguages(form).forEach((language) => languages.add(language))
    )
    return languages
  }
  const languages = new Set()
  const addDescriptions = (element) =>
    Object.keys(element?.attrs?.descriptions || {}).forEach((language) =>
      languages.add(language)
    )
  addDescriptions(normalizedForm)
  for (const group of normalizedForm?.groups || []) {
    addDescriptions(group)
    for (const item of group.items) {
      addDescriptions(item)
      for (const field of [
        'question',
        'designNotes',
        'completionInstructions',
      ]) {
        Object.keys(item[field]).forEach((language) => languages.add(language))
      }
    }
  }
  return languages
}

// Match elements of two lists by uid first, then by name. Returns the pairs in
// a stable order: the right list's order, with left-only elements slotted in
// after the element that preceded them on the left.
export function pairElements(leftList, rightList) {
  const rightByLeft = new Map()
  const taken = new Set()

  leftList.forEach((left, leftIndex) => {
    const rightIndex = rightList.findIndex(
      (right, index) => !taken.has(index) && left.uid && left.uid === right.uid
    )
    if (rightIndex !== -1) {
      rightByLeft.set(leftIndex, rightIndex)
      taken.add(rightIndex)
    }
  })
  leftList.forEach((left, leftIndex) => {
    if (rightByLeft.has(leftIndex)) return
    const rightIndex = rightList.findIndex(
      (right, index) =>
        !taken.has(index) &&
        normalizeName(left.name) === normalizeName(right.name)
    )
    if (rightIndex !== -1) {
      rightByLeft.set(leftIndex, rightIndex)
      taken.add(rightIndex)
    }
  })

  const leftByRight = new Map(
    [...rightByLeft.entries()].map(([leftIndex, rightIndex]) => [
      rightIndex,
      leftIndex,
    ])
  )

  const pairs = []
  let nextLeft = 0
  rightList.forEach((right, rightIndex) => {
    if (leftByRight.has(rightIndex)) {
      const leftIndex = leftByRight.get(rightIndex)
      for (; nextLeft < leftIndex; nextLeft++) {
        if (!rightByLeft.has(nextLeft)) {
          pairs.push({ left: leftList[nextLeft], right: null })
        }
      }
      nextLeft = Math.max(nextLeft, leftIndex + 1)
      pairs.push({ left: leftList[leftIndex], right })
    } else {
      pairs.push({ left: null, right })
    }
  })
  for (; nextLeft < leftList.length; nextLeft++) {
    if (!rightByLeft.has(nextLeft)) {
      pairs.push({ left: leftList[nextLeft], right: null })
    }
  }
  return pairs
}

// Align two keyed lists (terms, units, ...) so both cells can render the same
// number of lines. state is relative to the left cell.
export function alignLists(leftList, rightList) {
  const rightKeys = new Set(rightList.map((entry) => entry.key))
  const leftKeys = new Set(leftList.map((entry) => entry.key))
  // An unmatched entry whose group (e.g. a vendor extension name) also has an
  // unmatched entry on the other side is one changed entry, not two.
  const changedPartner = new Map()
  const freeRight = rightList.filter((entry) => !leftKeys.has(entry.key))
  for (const left of leftList) {
    if (rightKeys.has(left.key) || !left.group) continue
    const index = freeRight.findIndex((entry) => entry.group === left.group)
    if (index >= 0) {
      changedPartner.set(left.key, freeRight[index])
      freeRight.splice(index, 1)
    }
  }
  const pairedRight = new Set(
    [...changedPartner.values()].map((entry) => entry.key)
  )
  const lines = []
  const pushLeftOnly = (left) => {
    if (rightKeys.has(left.key)) return
    const partner = changedPartner.get(left.key)
    lines.push(
      partner
        ? { left, right: partner, state: 'changed' }
        : { left, right: null, state: 'added' }
    )
  }
  let nextLeft = 0
  for (const right of rightList) {
    if (leftKeys.has(right.key)) {
      const leftIndex = leftList.findIndex((entry) => entry.key === right.key)
      for (; nextLeft < leftIndex; nextLeft++) pushLeftOnly(leftList[nextLeft])
      nextLeft = Math.max(nextLeft, leftIndex + 1)
      lines.push({ left: leftList[leftIndex], right, state: 'same' })
    } else if (!pairedRight.has(right.key)) {
      lines.push({ left: null, right, state: 'missing' })
    }
  }
  for (; nextLeft < leftList.length; nextLeft++)
    pushLeftOnly(leftList[nextLeft])
  return lines
}

// Compare the switched-on extra attributes of two elements of one level
// (either may be missing). Returns the names of the differing scalar/text
// attributes and an aligned line list for every switched-on list attribute.
export function diffAttributes(level, left, right, enabled, language) {
  const scalars = new Set()
  const lists = {}
  for (const def of ATTRIBUTES[level]) {
    if (!enabled.has(attributeKey(level, def.name))) continue
    const leftValue = left?.attrs?.[def.name]
    const rightValue = right?.attrs?.[def.name]
    if (def.kind === 'list') {
      lists[def.name] = alignLists(leftValue || [], rightValue || [])
    } else if (def.kind === 'text') {
      if (!sameTexts(leftValue || {}, rightValue || {}, language)) {
        scalars.add(def.name)
      }
    } else if ((leftValue || '') !== (rightValue || '')) {
      scalars.add(def.name)
    }
  }
  return { scalars, lists }
}

const hasChangedLine = (lists) =>
  Object.values(lists).some((lines) =>
    lines.some((line) => line.state !== 'same')
  )

// Of the pairs that exist on both sides, the ones whose position relative to
// the others differs between the two lists. The longest run that keeps its
// order is treated as unmoved, so moving one element flags just that element.
// Returns the indexes into `pairs`.
export function findMoved(pairs, leftList) {
  const both = pairs
    .map((pair, index) => ({ index, position: leftList.indexOf(pair.left) }))
    .filter((_, index) => pairs[index].left && pairs[index].right)
  const length = new Array(both.length).fill(1)
  const previous = new Array(both.length).fill(-1)
  let best = -1
  both.forEach((entry, i) => {
    for (let j = 0; j < i; j++) {
      if (both[j].position < entry.position && length[j] + 1 > length[i]) {
        length[i] = length[j] + 1
        previous[i] = j
      }
    }
    if (best === -1 || length[i] > length[best]) best = i
  })
  const kept = new Set()
  for (let i = best; i !== -1; i = previous[i]) {
    kept.add(both[i].index)
  }
  return new Set(both.map((entry) => entry.index).filter((i) => !kept.has(i)))
}

function sameTexts(left, right, language) {
  return (left[language] || '') === (right[language] || '')
}

// Compare a paired left/right item. `enabled` is the Set of optional fields
// the user has switched on; `language` selects which translation is compared.
export function diffItems(left, right, enabled, language) {
  const scalars = []
  if (left.name !== right.name) scalars.push('name')
  if (left.prompt !== right.prompt) scalars.push('prompt')
  if (left.datatype !== right.datatype) scalars.push('datatype')
  if (left.length !== right.length) scalars.push('length')
  if (left.mandatory !== right.mandatory) scalars.push('mandatory')
  if (!sameTexts(left.question, right.question, language)) {
    scalars.push('question')
  }
  if (enabled.has('sdtm') && left.sdtm !== right.sdtm) scalars.push('sdtm')
  if (enabled.has('keys') && keysDiffer(left.keys, right.keys)) {
    scalars.push('keys')
  }
  if (
    enabled.has('designNotes') &&
    !sameTexts(left.designNotes, right.designNotes, language)
  ) {
    scalars.push('designNotes')
  }
  if (
    enabled.has('completionInstructions') &&
    !sameTexts(
      left.completionInstructions,
      right.completionInstructions,
      language
    )
  ) {
    scalars.push('completionInstructions')
  }

  const extra = diffAttributes('item', left, right, enabled, language)
  extra.scalars.forEach((name) => scalars.push(name))
  const lists = {
    terms: alignLists(left.terms, right.terms),
    units: alignLists(left.units, right.units),
    activityInstances: enabled.has('activityInstance')
      ? alignLists(left.activityInstances, right.activityInstances)
      : [],
    ...extra.lists,
  }
  // Source values travel with the terms; a changed one is a scalar-style change.
  if (enabled.has('sourceValue')) {
    const rightTerms = new Map(right.terms.map((term) => [term.key, term]))
    const changed = left.terms.some(
      (term) =>
        rightTerms.has(term.key) &&
        rightTerms.get(term.key).sourceValue !== term.sourceValue
    )
    if (changed) scalars.push('sourceValue')
  }

  const listStates = Object.values(lists)
    .flat()
    .map((line) => line.state)
    .filter((state) => state !== 'same')
  const hasAdded = listStates.includes('added')
  const hasMissing = listStates.includes('missing')

  let status = 'same'
  if (
    scalars.length > 0 ||
    listStates.includes('changed') ||
    (hasAdded && hasMissing)
  )
    status = 'changed'
  else if (hasAdded) status = 'added'
  else if (hasMissing) status = 'missing'

  return { status, scalars: new Set(scalars), lists }
}

// Build the aligned row list that the view renders. Each row is one line of the
// two-column layout.
export function compareForms(leftForm, rightForm, options = {}) {
  const enabled = options.enabledFields || new Set()
  const language = options.language || 'en'
  const rows = []
  let counter = 0
  const nextId = (prefix) => `${prefix}-${counter++}`

  const formDetail = diffAttributes(
    'form',
    leftForm,
    rightForm,
    enabled,
    language
  )
  if (leftForm.name !== rightForm.name) formDetail.scalars.add('name')
  const formDiffers =
    formDetail.scalars.size > 0 || hasChangedLine(formDetail.lists)
  if (formDiffers || [...enabled].some((key) => key.startsWith('form.'))) {
    const detail = formDetail
    rows.push({
      id: nextId('form'),
      kind: 'form',
      status: formDiffers ? 'changed' : 'same',
      left: leftForm,
      right: rightForm,
      detail,
    })
  }

  const groupPairs = pairElements(leftForm.groups, rightForm.groups)
  const movedGroups = findMoved(groupPairs, leftForm.groups)
  groupPairs.forEach((groupPair, groupIndex) => {
    const { left: leftGroup, right: rightGroup } = groupPair
    const groupDetail = diffAttributes(
      'group',
      leftGroup,
      rightGroup,
      enabled,
      language
    )
    let groupStatus = 'same'
    if (leftGroup && !rightGroup) groupStatus = 'added'
    else if (!leftGroup && rightGroup) groupStatus = 'missing'
    else {
      if (leftGroup.name !== rightGroup.name) groupDetail.scalars.add('name')
      if (leftGroup.mandatory !== rightGroup.mandatory) {
        groupDetail.scalars.add('mandatory')
      }
      if (enabled.has('keys') && keysDiffer(leftGroup.keys, rightGroup.keys)) {
        groupDetail.scalars.add('keys')
      }
      if (movedGroups.has(groupIndex)) groupDetail.scalars.add('order')
      if (groupDetail.scalars.size > 0 || hasChangedLine(groupDetail.lists)) {
        groupStatus = 'changed'
      }
    }
    if (!leftGroup || !rightGroup) groupDetail.scalars = new Set()

    const groupId = nextId('group')
    rows.push({
      id: groupId,
      kind: 'group',
      status: groupStatus,
      left: leftGroup,
      right: rightGroup,
      detail: groupDetail,
    })

    const leftItems = leftGroup?.items || []
    const itemPairs = pairElements(leftItems, rightGroup?.items || [])
    const movedItems = findMoved(itemPairs, leftItems)
    itemPairs.forEach((itemPair, itemIndex) => {
      const { left, right } = itemPair
      let status
      let detail = null
      if (left && !right) {
        status = 'added'
        detail = diffItems(left, EMPTY_ITEM, enabled, language)
      } else if (!left && right) {
        status = 'missing'
        detail = diffItems(EMPTY_ITEM, right, enabled, language)
      } else {
        detail = diffItems(left, right, enabled, language)
        status = detail.status
        if (movedItems.has(itemIndex)) {
          detail.scalars.add('order')
          if (status === 'same') status = 'changed'
        }
      }
      if (!left || !right) detail.scalars = new Set()
      rows.push({
        id: nextId('item'),
        kind: 'item',
        groupId,
        status,
        left,
        right,
        detail,
      })
    })
  })

  // Every row that is a place to jump to with the previous/next buttons.
  const stops = rows.filter(
    (row) =>
      row.status !== 'same' &&
      (row.kind === 'item' || (row.kind !== 'item' && row.status === 'changed'))
  )

  const differences = rows
    .filter((row) => row.status !== 'same')
    .map((row) => ({
      id: row.id,
      kind: row.kind,
      status: row.status,
      name: (row.left || row.right).name,
    }))

  return { rows, stops: stops.map((row) => row.id), differences }
}

// Compare two collections: their forms are paired like groups and items are,
// and every pair is compared as two forms. Each form's rows follow a
// 'collectionForm' header row; every row carries the forms it belongs to.
export function compareCollections(leftCollection, rightCollection, options) {
  const emptyForm = normalizeFormTree({ form: {}, groups: [] })
  const formPairs = pairElements(leftCollection.forms, rightCollection.forms)
  const moved = findMoved(formPairs, leftCollection.forms)
  const rows = []
  const stops = []
  const differences = []

  formPairs.forEach(({ left, right }, index) => {
    const bothSides = !!(left && right)
    const prefix = `f${index}-`
    const forms = { left, right }
    const inner = compareForms(left || emptyForm, right || emptyForm, options)

    let status = 'same'
    if (left && !right) status = 'added'
    else if (!left && right) status = 'missing'
    else if (moved.has(index)) status = 'changed'
    const headerId = `${prefix}header`
    rows.push({
      id: headerId,
      kind: 'collectionForm',
      status,
      left,
      right,
      forms,
      detail: {
        scalars: new Set(bothSides && moved.has(index) ? ['order'] : []),
        lists: { terms: [], units: [], activityInstances: [] },
      },
    })
    if (status === 'changed') stops.push(headerId)
    if (status !== 'same') {
      differences.push({
        id: headerId,
        kind: 'form',
        status,
        name: (left || right).name,
      })
    }

    const innerRows = inner.rows
      .filter((row) => bothSides || row.kind !== 'form')
      .map((row) => ({
        ...row,
        id: prefix + row.id,
        groupId: row.groupId ? prefix + row.groupId : undefined,
        forms,
      }))
    const kept = new Set(innerRows.map((row) => row.id))
    rows.push(...innerRows)
    stops.push(
      ...inner.stops.map((id) => prefix + id).filter((id) => kept.has(id))
    )
    differences.push(
      ...inner.differences
        .map((difference) => ({ ...difference, id: prefix + difference.id }))
        .filter((difference) => kept.has(difference.id))
    )
  })

  return { rows, stops, differences }
}

// Rows to render when "show only differences" is on: every changed row, plus
// the header of any form or group that still has a changed row beneath it.
export function filterRows(rows, onlyDifferences) {
  if (!onlyDifferences) return rows
  const kept = []
  let pendingForm = null
  let pendingGroup = null
  const flush = () => {
    if (pendingForm) kept.push(pendingForm)
    if (pendingGroup) kept.push(pendingGroup)
    pendingForm = null
    pendingGroup = null
  }
  for (const row of rows) {
    if (row.kind === 'collectionForm') {
      pendingForm = row
      pendingGroup = null
      if (row.status !== 'same') flush()
    } else if (row.kind === 'group') {
      pendingGroup = row
      if (row.status !== 'same') {
        if (pendingForm) kept.push(pendingForm)
        pendingForm = null
        kept.push(row)
        pendingGroup = null
      }
    } else if (row.status !== 'same') {
      flush()
      kept.push(row)
    }
  }
  return kept
}

export default {
  OPTIONAL_FIELDS,
  normalizeItem,
  formatKeys,
  normalizeFormTree,
  normalizeCollectionTree,
  collectLanguages,
  pairElements,
  alignLists,
  diffItems,
  diffAttributes,
  findMoved,
  compareForms,
  compareCollections,
  filterRows,
}
