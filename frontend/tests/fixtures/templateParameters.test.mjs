import { test } from 'node:test'
import assert from 'node:assert/strict'

import templateParameters from '../../src/utils/templateParameters.js'

// Unit tests for the syntax template tokenizer. They live here because
// tests/fixtures/*.test.mjs is the only glob `npm run test:fixtures` runs.

const { splitTemplate, getTemplateParametersFromTemplate, escapeBrackets } =
  templateParameters

test('splits placeholders from literal text', () => {
  assert.deepEqual(
    splitTemplate('To assess [Intervention] in [Activity]', [
      'Intervention',
      'Activity',
    ]),
    [
      { isParameter: false, value: 'To assess ' },
      { isParameter: true, value: 'Intervention' },
      { isParameter: false, value: ' in ' },
      { isParameter: true, value: 'Activity' },
    ]
  )
})

test('keeps bracket text that is not a parameter name as literal', () => {
  assert.deepEqual(
    splitTemplate('Dose [see note] of [Activity]', ['Activity']),
    [
      { isParameter: false, value: 'Dose [see note] of ' },
      { isParameter: true, value: 'Activity' },
    ]
  )
})

test('keeps unbalanced brackets as literal', () => {
  assert.deepEqual(splitTemplate('a [ b ] c [Activity', ['Activity']), [
    { isParameter: false, value: 'a [ b ] c [Activity' },
  ])
})

test('matches a placeholder nested in literal brackets', () => {
  assert.deepEqual(splitTemplate('[a [Activity] b]', ['Activity']), [
    { isParameter: false, value: '[a ' },
    { isParameter: true, value: 'Activity' },
    { isParameter: false, value: ' b]' },
  ])
})

test('treats every occurrence of a duplicated name as a placeholder', () => {
  assert.deepEqual(
    getTemplateParametersFromTemplate('[Activity] and [Activity]', [
      'Activity',
      'Activity',
    ]),
    ['Activity', 'Activity']
  )
})

test('matches parameter names exactly', () => {
  assert.deepEqual(
    getTemplateParametersFromTemplate('[activity] [ Activity] [Activity]', [
      'Activity',
    ]),
    ['Activity']
  )
})

test('has no placeholders without parameter names', () => {
  assert.deepEqual(getTemplateParametersFromTemplate('[Activity]', []), [])
  assert.deepEqual(getTemplateParametersFromTemplate('[Activity]'), [])
  assert.deepEqual(getTemplateParametersFromTemplate(null, ['Activity']), [])
})

test('ignores empty brackets', () => {
  assert.deepEqual(splitTemplate('a [] b', ['']), [
    { isParameter: false, value: 'a [] b' },
  ])
})

test('keeps HTML around placeholders in literal parts', () => {
  assert.deepEqual(splitTemplate('<p>[Activity]</p>', ['Activity']), [
    { isParameter: false, value: '<p>' },
    { isParameter: true, value: 'Activity' },
    { isParameter: false, value: '</p>' },
  ])
})

test('encodes literal brackets as HTML entities', () => {
  assert.equal(escapeBrackets('[see note]'), '&#91;see note&#93;')
  assert.equal(escapeBrackets('no brackets'), 'no brackets')
})
