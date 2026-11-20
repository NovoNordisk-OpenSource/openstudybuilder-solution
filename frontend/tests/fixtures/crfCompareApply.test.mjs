import { test } from 'node:test'
import assert from 'node:assert/strict'

import { compareForms, normalizeFormTree } from '../../src/utils/crfCompare.js'
import {
  changedParts,
  describeApply,
  isApplicable,
  itemPatch,
  itemsWithAdded,
  itemsWithRefValues,
  itemsWithRemoved,
} from '../../src/utils/crfCompareApply.js'

const term = (uid, name, order) => ({
  term_uid: uid,
  name,
  display_text: name,
  order,
  mandatory: true,
})

function itemOf(uid, extra = {}) {
  return {
    uid,
    name: uid,
    version: '1.0',
    oid: `I.${uid}`,
    prompt: 'p',
    datatype: { uid: 'dt-text', submission_value: 'text' },
    length: 10,
    terms: [],
    unit_definitions: [],
    activity_instances: [],
    translated_texts: [],
    aliases: [],
    vendor_elements: [],
    vendor_attributes: [],
    vendor_element_attributes: [],
    ...extra,
  }
}

function formOf(items) {
  return normalizeFormTree({
    form: { uid: 'f', name: 'F', library_name: 'L', version: '1.0' },
    groups: [
      {
        ref: {},
        group: { uid: 'g', name: 'G', version: '1.0' },
        items: items.map((item, index) => ({
          ref: { uid: item.uid, order_number: index + 1, mandatory: 'No' },
          item,
        })),
      },
    ],
  })
}

const itemRow = (result) => result.rows.find((row) => row.kind === 'item')

test('changedParts splits item fields from group-reference fields', () => {
  const left = formOf([itemOf('a', { prompt: 'x', sds_var_name: 'A' })])
  const right = formOf([itemOf('a', { prompt: 'y', sds_var_name: 'B' })])
  const row = itemRow(
    compareForms(left, right, { enabledFields: new Set(['sdtm']) })
  )
  const { itemFields, refFields } = changedParts(row)
  assert.deepEqual([...itemFields].sort(), ['prompt', 'sdtm'])
  assert.equal(refFields.size, 0)

  const mandatoryRow = itemRow(
    compareForms(
      formOf([itemOf('a')]),
      normalizeFormTree({
        form: { uid: 'f', name: 'F', library_name: 'L', version: '1.0' },
        groups: [
          {
            ref: {},
            group: { uid: 'g', name: 'G', version: '1.0' },
            items: [{ ref: { uid: 'a', mandatory: 'Yes' }, item: itemOf('a') }],
          },
        ],
      })
    )
  )
  assert.deepEqual([...changedParts(mandatoryRow).refFields], ['mandatory'])
})

test('changedParts reports a changed term list and skips source values', () => {
  const left = formOf([
    itemOf('a', { terms: [term('t1', 'Sit', 1), term('t2', 'Lie', 2)] }),
  ])
  const right = formOf([itemOf('a', { terms: [term('t1', 'Sit', 1)] })])
  const row = itemRow(compareForms(left, right))
  assert.deepEqual([...changedParts(row).itemFields], ['terms'])
})

test('itemPatch overlays only the chosen fields onto the target', () => {
  const target = itemOf('a', {
    prompt: 'old',
    length: 5,
    terms: [term('t1', 'Sit', 1)],
    translated_texts: [
      { text_type: 'Question', language: 'en', text: 'Old?' },
      { text_type: 'Question', language: 'da', text: 'Gammel?' },
    ],
  })
  const source = itemOf('a', {
    prompt: 'new',
    length: 9,
    terms: [term('t1', 'Sit', 1), term('t2', 'Lie', 2)],
    translated_texts: [{ text_type: 'Question', language: 'en', text: 'New?' }],
  })
  const payload = itemPatch(
    target,
    source,
    new Set(['prompt', 'terms', 'question']),
    {
      language: 'en',
      changeDescription: 'why',
    }
  )
  assert.equal(payload.prompt, 'new')
  assert.equal(payload.length, 5)
  assert.equal(payload.change_description, 'why')
  assert.deepEqual(
    payload.terms.map((entry) => entry.uid),
    ['t1', 't2']
  )
  assert.deepEqual(
    payload.translated_texts.map((entry) => `${entry.language}:${entry.text}`),
    ['da:Gammel?', 'en:New?']
  )
})

test('itemPatch with no fields re-saves the target unchanged', () => {
  const target = itemOf('a', { prompt: 'keep' })
  const payload = itemPatch(
    target,
    itemOf('a', { prompt: 'other' }),
    new Set(),
    {
      language: 'en',
      changeDescription: 'x',
    }
  )
  assert.equal(payload.prompt, 'keep')
  assert.equal(payload.datatype_uid, 'dt-text')
})

const refs = [
  { uid: 'b', order_number: 2, mandatory: 'No' },
  { uid: 'a', order_number: 1, mandatory: 'Yes', key_sequence: '1' },
]

test('group item lists are rebuilt in order and renumbered', () => {
  assert.deepEqual(
    itemsWithAdded(refs, { uid: 'c', mandatory: true }).map(
      (input) => `${input.uid}:${input.order_number}:${input.mandatory}`
    ),
    ['a:1:Yes', 'b:2:No', 'c:3:Yes']
  )
  assert.deepEqual(
    itemsWithRemoved(refs, 'a').map((input) => [input.uid, input.order_number]),
    [['b', 1]]
  )
  const changed = itemsWithRefValues(
    refs,
    'b',
    { mandatory: 'Yes', key_sequence: '2' },
    new Set(['mandatory'])
  )
  assert.equal(changed[1].mandatory, 'Yes')
  assert.equal(changed[1].key_sequence, null)
})

test('describeApply reads the direction off which side has the item', () => {
  const row = itemRow(compareForms(formOf([itemOf('a')]), formOf([])))
  assert.equal(describeApply(row, 'toRight').kind, 'add')
  assert.equal(describeApply(row, 'toLeft').kind, 'remove')
})

test('item attributes are copied onto the target patch', () => {
  const target = itemOf('t', { oid: 'I.old', comment: 'old' })
  const source = itemOf('s', {
    oid: 'I.new',
    comment: 'new',
    significant_digits: 2,
    aliases: [{ name: 'n', context: 'c' }],
    codelist: { uid: 'cl', allows_multi_choice: true },
    translated_texts: [
      { text_type: 'Description', language: 'en', text: 'desc' },
      { text_type: 'Description', language: 'da', text: 'beskrivelse' },
    ],
    vendor_attributes: [{ uid: 'va', name: 'n', value: 'v' }],
  })
  const fields = new Set([
    'oid',
    'comment',
    'significantDigits',
    'aliases',
    'codelist',
    'descriptions',
    'vendor',
  ])
  const patch = itemPatch(target, source, fields, {
    language: 'en',
    changeDescription: 'x',
  })
  assert.equal(patch.oid, 'I.new')
  assert.equal(patch.comment, 'new')
  assert.equal(patch.significant_digits, 2)
  assert.deepEqual(patch.aliases, [{ name: 'n', context: 'c' }])
  assert.deepEqual(patch.codelist, { uid: 'cl', allows_multi_choice: true })
  assert.deepEqual(patch.translated_texts, [
    { text_type: 'Description', language: 'en', text: 'desc' },
  ])
  assert.deepEqual(patch.vendor_attributes, [
    { uid: 'va', name: 'n', value: 'v' },
  ])
})

test('a position difference alone has nothing to apply', () => {
  const left = formOf([itemOf('a'), itemOf('b')])
  const right = formOf([itemOf('b'), itemOf('a')])
  const moved = compareForms(left, right).rows.filter(
    (row) => row.kind === 'item' && row.status === 'changed'
  )
  assert.equal(moved.length, 1)
  assert.equal(isApplicable(moved[0], 'toRight'), false)
})
