// Pure payload builders for applying a difference found in the CRF Compare tab
// from one form to the other. No Vue, no API imports, so it can be tested with
// `node --test` (see tests/fixtures/crfCompareApply.test.mjs).

import { TEXT_TYPES } from './crfCompare.js'

const REF_FIELDS = ['mandatory', 'keys']
const TEXT_FIELDS = [
  'question',
  'designNotes',
  'completionInstructions',
  'descriptions',
]
const NOT_EDITABLE_HERE = ['sourceValue', 'order']
// Item attributes copied as they are, from the compare name to the API field.
const PLAIN_ATTRIBUTES = {
  oid: 'oid',
  significantDigits: 'significant_digits',
  sasFieldName: 'sas_field_name',
  origin: 'origin',
  comment: 'comment',
}

// Which parts of a differing item row would be copied. `itemFields` are written
// to the item itself; `refFields` live on the group's reference to the item.
export function changedParts(row) {
  const itemFields = new Set()
  const refFields = new Set()
  for (const field of row.detail.scalars) {
    if (NOT_EDITABLE_HERE.includes(field)) continue
    if (REF_FIELDS.includes(field)) refFields.add(field)
    else itemFields.add(field)
  }
  for (const [list, lines] of Object.entries(row.detail.lists)) {
    if (lines.some((line) => line.state !== 'same')) itemFields.add(list)
  }
  return { itemFields, refFields }
}

const datatypeUid = (item) =>
  item.datatype?.uid || item.datatype?.term_uid || null

const termInput = (term, index) => ({
  uid: term.term_uid,
  mandatory: term.mandatory ?? true,
  display_text: term.display_text ?? null,
  order: term.order ?? index + 1,
})

const unitInput = (unit, index) => ({
  uid: unit.uid,
  mandatory: unit.mandatory ?? true,
  order: unit.order ?? index + 1,
})

const activityInstanceInput = (instance, index) => ({
  activity_instance_uid: instance.activity_instance_uid,
  activity_item_class_uid: instance.activity_item_class_uid,
  order: instance.order ?? index + 1,
  primary: instance.primary ?? false,
  preset_response_value: instance.preset_response_value ?? undefined,
  value_condition: instance.value_condition ?? undefined,
  value_dependent_map: instance.value_dependent_map ?? undefined,
})

const codelistInput = (codelist) =>
  codelist?.uid
    ? {
        uid: codelist.uid,
        allows_multi_choice: codelist.allows_multi_choice ?? false,
      }
    : null

const externalQuestionInput = (question) =>
  question?.uid
    ? { term_uid: question.uid, codelist_uid: question.codelist_uid }
    : null

const textEntry = ({ text_type, language, text }) => ({
  text_type,
  language,
  text,
})

// The PATCH body that re-saves `target` unchanged. The endpoint wants the whole
// item back, not just the fields that change.
export function itemPatchFromItem(target, changeDescription) {
  return {
    change_description: changeDescription,
    name: target.name,
    oid: target.oid ?? null,
    datatype_uid: datatypeUid(target),
    prompt: target.prompt ?? null,
    length: target.length ?? null,
    significant_digits: target.significant_digits ?? null,
    sas_field_name: target.sas_field_name ?? null,
    sds_var_name: target.sds_var_name ?? null,
    origin: target.origin ?? null,
    comment: target.comment ?? null,
    translated_texts: (target.translated_texts || []).map(textEntry),
    aliases: target.aliases || [],
    unit_definitions: (target.unit_definitions || []).map(unitInput),
    external_question: externalQuestionInput(target.external_question),
    codelist: codelistInput(target.codelist),
    terms: (target.terms || []).map(termInput),
    activity_instances: (target.activity_instances || []).map(
      activityInstanceInput
    ),
    vendor_elements: target.vendor_elements || [],
    vendor_element_attributes: target.vendor_element_attributes || [],
    vendor_attributes: target.vendor_attributes || [],
  }
}

// The PATCH body for `target` with the listed fields taken from `source`.
// `fields` holds the names used by the comparison: name, prompt, datatype,
// length, sdtm, question, designNotes, completionInstructions, terms, units,
// activityInstances and the item attributes (oid, significantDigits,
// sasFieldName, origin, comment, aliases, codelist, externalQuestion,
// descriptions, vendor).
export function itemPatch(target, source, fields, options) {
  const payload = itemPatchFromItem(target, options.changeDescription)

  if (fields.has('name')) payload.name = source.name
  if (fields.has('prompt')) payload.prompt = source.prompt ?? null
  if (fields.has('length')) payload.length = source.length ?? null
  if (fields.has('sdtm')) payload.sds_var_name = source.sds_var_name ?? null
  if (fields.has('datatype')) payload.datatype_uid = datatypeUid(source)
  if (fields.has('terms')) {
    // Terms are a subset of the item's codelist, so the two travel together.
    payload.terms = (source.terms || []).map(termInput)
    payload.codelist = codelistInput(source.codelist)
  }
  if (fields.has('units')) {
    payload.unit_definitions = (source.unit_definitions || []).map(unitInput)
  }
  if (fields.has('activityInstances')) {
    payload.activity_instances = (source.activity_instances || []).map(
      activityInstanceInput
    )
  }

  for (const [field, apiField] of Object.entries(PLAIN_ATTRIBUTES)) {
    if (fields.has(field)) payload[apiField] = source[apiField] ?? null
  }
  if (fields.has('aliases')) payload.aliases = source.aliases || []
  if (fields.has('codelist')) payload.codelist = codelistInput(source.codelist)
  if (fields.has('externalQuestion')) {
    payload.external_question = externalQuestionInput(source.external_question)
  }
  if (fields.has('vendor')) {
    payload.vendor_elements = source.vendor_elements || []
    payload.vendor_attributes = source.vendor_attributes || []
    payload.vendor_element_attributes = source.vendor_element_attributes || []
  }

  for (const field of TEXT_FIELDS) {
    if (!fields.has(field)) continue
    const type = TEXT_TYPES[field === 'descriptions' ? 'description' : field]
    const language = options.language
    payload.translated_texts = [
      ...payload.translated_texts.filter(
        (entry) => !(entry.text_type === type && entry.language === language)
      ),
      ...(source.translated_texts || [])
        .filter(
          (entry) => entry.text_type === type && entry.language === language
        )
        .map(textEntry),
    ]
  }
  return payload
}

const isMandatory = (ref) => ref?.mandatory === 'Yes' || ref?.mandatory === true

// A group's reference to an item, in the shape POST .../items expects.
export function groupItemInput(ref, orderNumber) {
  return {
    uid: ref.uid,
    order_number: orderNumber,
    mandatory: isMandatory(ref) ? 'Yes' : 'No',
    key_sequence: ref.key_sequence ?? null,
    method_oid: ref.method_oid ?? null,
    imputation_method_oid: ref.imputation_method_oid ?? null,
    role: ref.role ?? null,
    role_codelist_oid: ref.role_codelist_oid ?? null,
    collection_exception_condition_oid:
      ref.collection_exception_condition_oid ?? null,
    vendor: {
      attributes: (ref.vendor?.attributes || []).map((attribute) => ({
        uid: attribute.uid,
        value: attribute.value,
      })),
    },
  }
}

const inOrder = (refs) =>
  [...refs].sort(
    (a, b) =>
      (a.order_number ?? Number.MAX_SAFE_INTEGER) -
      (b.order_number ?? Number.MAX_SAFE_INTEGER)
  )

const toInputs = (refs) =>
  refs.map((ref, index) => groupItemInput(ref, index + 1))

// The full item list of a group after the change; POST .../items replaces the
// group's items with whatever it is given when override is on.
export function itemsWithAdded(existingRefs, newRef) {
  return toInputs([...inOrder(existingRefs), newRef])
}

export function itemsWithRemoved(existingRefs, itemUid) {
  return toInputs(inOrder(existingRefs).filter((ref) => ref.uid !== itemUid))
}

export function itemsWithRefValues(
  existingRefs,
  itemUid,
  sourceRef,
  refFields
) {
  return toInputs(
    inOrder(existingRefs).map((ref) => {
      if (ref.uid !== itemUid) return ref
      const changed = { ...ref }
      if (refFields.has('mandatory')) changed.mandatory = sourceRef.mandatory
      if (refFields.has('keys')) changed.key_sequence = sourceRef.key_sequence
      return changed
    })
  )
}

// What applying a row does to the target side, for the confirmation dialog.
// `direction` is 'toRight' (copy left onto right) or 'toLeft'.
export function describeApply(row, direction) {
  const [from, to] =
    direction === 'toRight' ? ['left', 'right'] : ['right', 'left']
  if (row[from] && !row[to]) return { kind: 'add' }
  if (!row[from] && row[to]) return { kind: 'remove' }
  return { kind: 'update', ...changedParts(row) }
}

// Whether applying the row changes anything: adding and removing always do, an
// update only when something other than a position difference is copied.
export function isApplicable(row, direction) {
  const desc = describeApply(row, direction)
  if (desc.kind !== 'update') return true
  return desc.itemFields.size > 0 || desc.refFields.size > 0
}
