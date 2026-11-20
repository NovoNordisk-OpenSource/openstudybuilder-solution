import assert from 'node:assert/strict'
import { test } from 'node:test'

import {
  mergeLayoutForSave,
  normalizeLayoutEntry,
  resolveVisibleKeys,
} from '../../src/stores/column-layout.js'

const headers = ['name', 'status', 'note']

test('a table with no saved layout shows its defaults', () => {
  assert.deepEqual(resolveVisibleKeys(undefined, headers, ['name', 'status']), [
    'name',
    'status',
  ])
})

test('a column added after the last save is switched on', () => {
  const layout = {
    visible: ['name', 'status', 'note'],
    known: ['name', 'status', 'note'],
  }
  assert.deepEqual(resolveVisibleKeys(layout, [...headers, 'owner'], []), [
    'name',
    'status',
    'note',
    'owner',
  ])
})

test('a column the user switched off stays off when another column is added', () => {
  const layout = {
    visible: ['name'],
    known: ['name', 'status', 'note'],
  }
  assert.deepEqual(
    resolveVisibleKeys(layout, [...headers, 'owner'], [...headers, 'owner']),
    ['name', 'owner']
  )
})

test('a new column that is off by default stays off', () => {
  const layout = {
    visible: ['name', 'status'],
    known: ['name', 'status'],
  }
  assert.deepEqual(
    resolveVisibleKeys(layout, [...headers, 'internal'], ['name', 'status']),
    ['name', 'status']
  )
})

test('a legacy list with no known-set turns on columns it does not mention', () => {
  const layout = normalizeLayoutEntry(['name', 'status'])
  assert.equal(layout.known, null)
  assert.deepEqual(resolveVisibleKeys(layout, headers, headers), headers)
})

test('normalize keeps an already recorded known-set', () => {
  const layout = normalizeLayoutEntry({
    visible: ['name'],
    known: ['name', 'status'],
  })
  assert.deepEqual(layout, {
    visible: ['name'],
    known: ['name', 'status'],
  })
})

test('renamed header keys collapse to the defaults instead of an empty table', () => {
  const layout = { visible: ['a', 'b'], known: ['a', 'b'] }
  assert.deepEqual(resolveVisibleKeys(layout, ['c', 'd'], []), ['c', 'd'])
})

test('defaults that share no key with the headers show every header', () => {
  const layout = { visible: ['a'], known: ['a'] }
  assert.deepEqual(resolveVisibleKeys(layout, ['c', 'd'], ['x']), ['c', 'd'])
  assert.deepEqual(resolveVisibleKeys(undefined, ['c', 'd'], ['x']), ['c', 'd'])
})

test('a layout with nothing visible falls back to the defaults', () => {
  const layout = { visible: [], known: headers }
  assert.deepEqual(resolveVisibleKeys(layout, headers, ['name']), ['name'])
})

test('an empty known-set treats every default-on column as unseen', () => {
  const layout = { visible: ['name'], known: [] }
  assert.deepEqual(resolveVisibleKeys(layout, headers, headers), headers)
})

test('visible columns follow header order, not saved order', () => {
  const layout = { visible: ['note', 'name'], known: headers }
  assert.deepEqual(resolveVisibleKeys(layout, headers, headers), [
    'name',
    'note',
  ])
})

test('normalize converts a legacy array of header objects to keys', () => {
  assert.deepEqual(normalizeLayoutEntry([{ key: 'name' }, { key: 'status' }]), {
    visible: ['name', 'status'],
    known: null,
  })
})

test('normalize drops non-string entries in both formats', () => {
  assert.deepEqual(
    normalizeLayoutEntry(['a', null, 3, { foo: 1 }, { key: 'b' }]).visible,
    ['a', 'b']
  )
  assert.deepEqual(
    normalizeLayoutEntry({ visible: ['a', null, 3], known: ['a', {}, 'b'] }),
    { visible: ['a'], known: ['a', 'b'] }
  )
})

test('normalize turns unusable values into an empty layout', () => {
  const empty = { visible: [], known: null }
  for (const value of [undefined, null, 'x', 5, {}, { visible: 'a' }]) {
    assert.deepEqual(normalizeLayoutEntry(value), empty)
  }
})

test('save with no previous entry records the current headers as known', () => {
  assert.deepEqual(mergeLayoutForSave(undefined, ['name'], headers), {
    visible: ['name'],
    known: headers,
  })
})

test('save keeps what the previous entry knew about when headers shrink', () => {
  const previous = { visible: ['name', 'status'], known: headers }
  assert.deepEqual(mergeLayoutForSave(previous, ['name'], ['name']), {
    visible: ['name', 'status'],
    known: headers,
  })
})

test('save does not carry over a column the user hid among current headers', () => {
  const previous = { visible: ['name', 'status'], known: headers }
  assert.deepEqual(mergeLayoutForSave(previous, ['name'], headers), {
    visible: ['name'],
    known: headers,
  })
})

test('a hidden column stays hidden after an edit-mode header swap and reload', () => {
  const normal = ['name', 'status', 'note']
  const edit = ['name', 'action']
  let stored = mergeLayoutForSave(undefined, ['name', 'note'], normal)
  stored = mergeLayoutForSave(stored, ['name', 'action'], edit)
  assert.deepEqual(resolveVisibleKeys(stored, normal, normal), ['name', 'note'])
})

test('save upgrades a legacy array entry', () => {
  assert.deepEqual(
    mergeLayoutForSave(['name', 'gone'], ['name', 'status'], headers),
    {
      visible: ['name', 'status', 'gone'],
      known: ['name', 'gone', 'status', 'note'],
    }
  )
})
