import assert from 'node:assert/strict'
import { test } from 'node:test'

import {
  applySavedExpandState,
  assignRowDisplayUids,
  buildRowsDisplayState,
} from '../../src/utils/soaDisplayState.js'

const isActivityRow = (row) => row.cells[0].style === 'activity'

function row(style, uid) {
  return { cells: [{ style, refs: uid ? [{ uid }] : [] }] }
}

// What the API returns for an ungrouped activity: a ref-less group and subgroup above it
function ungroupedActivity(uid) {
  return [row('group'), row('subGroup'), row('activity', uid)]
}

function displayUids(rows) {
  return rows.map((r) => r.displayUid)
}

test('rows with a uid keep it as their display uid', () => {
  const rows = [
    row('soaGroup', 'sg1'),
    row('group', 'g1'),
    row('subGroup', 's1'),
    row('activity', 'a1'),
  ]
  assignRowDisplayUids(rows)
  assert.deepEqual(displayUids(rows), ['sg1', 'g1', 's1', 'a1'])
})

test('ref-less group and subgroup rows get distinct keys per activity', () => {
  const rows = [...ungroupedActivity('a1'), ...ungroupedActivity('a2')]
  assignRowDisplayUids(rows)
  assert.deepEqual(displayUids(rows), [
    'group-before-a1',
    'subGroup-before-a1',
    'a1',
    'group-before-a2',
    'subGroup-before-a2',
    'a2',
  ])
})

test('keys of the remaining rows survive deleting or moving another activity', () => {
  const before = [
    ...ungroupedActivity('a1'),
    ...ungroupedActivity('a2'),
    ...ungroupedActivity('a3'),
  ]
  assignRowDisplayUids(before)
  const keysOfA3 = displayUids(before.slice(6))

  const afterDelete = [...ungroupedActivity('a2'), ...ungroupedActivity('a3')]
  assignRowDisplayUids(afterDelete)
  assert.deepEqual(displayUids(afterDelete.slice(3)), keysOfA3)

  const afterMove = [...ungroupedActivity('a3'), ...ungroupedActivity('a1')]
  assignRowDisplayUids(afterMove)
  assert.deepEqual(displayUids(afterMove.slice(0, 3)), keysOfA3)
})

test('trailing ref-less rows with nothing below them still get unique keys', () => {
  const rows = [row('group'), row('subGroup'), row('group'), row('subGroup')]
  assignRowDisplayUids(rows)
  assert.equal(new Set(displayUids(rows)).size, rows.length)
})

test('a group with a ref but a ref-less subgroup uses the activity below it', () => {
  const rows = [row('group', 'g1'), row('subGroup'), row('activity', 'a1')]
  assignRowDisplayUids(rows)
  assert.deepEqual(displayUids(rows), ['g1', 'subGroup-before-a1', 'a1'])
})

test('parent links follow the group, subgroup and activity hierarchy', () => {
  const rows = [
    row('soaGroup', 'sg1'),
    row('group', 'g1'),
    row('subGroup', 's1'),
    row('activity', 'a1'),
    ...ungroupedActivity('a2'),
  ]
  assignRowDisplayUids(rows)
  assert.deepEqual(buildRowsDisplayState(rows, isActivityRow), {
    'row-sg1': { value: false },
    'row-g1': { value: false, parent: 'sg1' },
    'row-s1': { value: false, parent: 'g1' },
    'row-a1': { value: false, parent: 's1' },
    'row-group-before-a2': { value: false, parent: 'sg1' },
    'row-subGroup-before-a2': { value: false, parent: 'group-before-a2' },
    'row-a2': { value: false, parent: 'subGroup-before-a2' },
  })
})

test('saved expansion is kept for surviving rows, including collapsed ones', () => {
  const state = {
    'row-g1': { value: false },
    'row-g2': { value: false },
  }
  applySavedExpandState(state, { 'row-g1': true, 'row-g2': false })
  assert.equal(state['row-g1'].value, true)
  assert.equal(state['row-g2'].value, false)
})

test('rows without a saved value are expanded so the change stays visible', () => {
  const state = {
    'row-g1': { value: false },
    'row-group-before-a9': { value: false },
  }
  applySavedExpandState(state, { 'row-g1': false })
  assert.equal(state['row-g1'].value, false)
  assert.equal(state['row-group-before-a9'].value, true)
})
