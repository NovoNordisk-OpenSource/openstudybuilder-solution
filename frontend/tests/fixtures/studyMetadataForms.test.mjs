import { test } from 'node:test'
import assert from 'node:assert/strict'

import studyMetadataForms from '../../src/utils/studyMetadataForms.js'

const { getTermDefinition } = studyMetadataForms

const terms = [
  { term_uid: 'T1', definition: 'First rule' },
  { term_uid: 'T2', definition: 'Second rule' },
]

test('returns the definition of the codelist term with the same uid', () => {
  assert.equal(getTermDefinition({ term_uid: 'T2' }, terms), 'Second rule')
})

test('returns undefined when no term is selected', () => {
  assert.equal(getTermDefinition(null, terms), undefined)
  assert.equal(getTermDefinition(undefined, terms), undefined)
})

// A retired stored rule is not in the Final-only codelist terms
test('returns undefined when the term is not in the codelist terms', () => {
  assert.equal(getTermDefinition({ term_uid: 'T9' }, terms), undefined)
})
