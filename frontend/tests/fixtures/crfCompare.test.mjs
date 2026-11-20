import { test } from 'node:test'
import assert from 'node:assert/strict'

import {
  alignLists,
  compareCollections,
  compareForms,
  filterRows,
  formatKeys,
  keysDiffer,
  normalizeFormTree,
  pairElements,
} from '../../src/utils/crfCompare.js'

// tests/fixtures/*.test.mjs is the only glob `npm run test:fixtures` runs.

function rawItem(uid, name, extra = {}) {
  return {
    ref: { mandatory: 'No' },
    item: {
      uid,
      name,
      version: '1.0',
      terms: [],
      unit_definitions: [],
      activity_instances: [],
      translated_texts: [],
      ...extra,
    },
  }
}

function rawForm(libraryName, version, groups) {
  return normalizeFormTree({
    form: {
      uid: `form-${libraryName}`,
      name: 'Vital Signs',
      library_name: libraryName,
      version,
      status: 'Final',
    },
    groups: groups.map(([name, items]) => ({
      ref: {},
      group: { uid: `g-${libraryName}-${name}`, name, version: '1.0' },
      items,
    })),
  })
}

const term = (uid, name, order) => ({ term_uid: uid, name, order })

const sponsor = rawForm('Sponsor', '1.0', [
  [
    'Vital Signs',
    [
      rawItem('s1', 'Study ID'),
      rawItem('s2', 'Date of examination', { prompt: 'MM-DD-YYYY' }),
    ],
  ],
  [
    'Blood pressure and pulse',
    [
      rawItem('s3', 'Position', {
        terms: [
          term('t1', 'Sitting', 1),
          term('t2', 'Supine Position', 2),
          term('t3', 'Standing', 3),
        ],
      }),
      rawItem('s4', 'Pulse'),
    ],
  ],
])

const veeva = rawForm('Veeva', '2.0', [
  [
    'Vital Signs',
    [
      rawItem('v1', 'Study ID'),
      rawItem('v2', 'Date of examination', { prompt: 'DD-MM-YYYY' }),
    ],
  ],
  [
    'Blood pressure and pulse',
    [
      rawItem('v3', 'Position', {
        terms: [term('t1', 'Sitting', 1), term('t3', 'Standing', 2)],
      }),
      rawItem('v5', 'Anatomical Location'),
      rawItem('v4', 'Pulse'),
    ],
  ],
])

const itemRow = (result, name) =>
  result.rows.find(
    (row) => row.kind === 'item' && (row.left || row.right).name === name
  )

test('pairs across libraries by name and reports each kind of difference', () => {
  const result = compareForms(sponsor, veeva)

  assert.equal(itemRow(result, 'Study ID').status, 'same')

  const date = itemRow(result, 'Date of examination')
  assert.equal(date.status, 'changed')
  assert.deepEqual([...date.detail.scalars], ['prompt'])

  assert.equal(itemRow(result, 'Position').status, 'added')
  assert.equal(itemRow(result, 'Anatomical Location').status, 'missing')
  assert.equal(itemRow(result, 'Pulse').status, 'same')

  assert.deepEqual(
    result.differences.map((d) => d.name),
    ['Date of examination', 'Position', 'Anatomical Location']
  )
  assert.equal(result.stops.length, 3)
})

test('a right-only item sits where it belongs in the right form order', () => {
  const result = compareForms(sponsor, veeva)
  const names = result.rows
    .filter((row) => row.kind === 'item')
    .map((row) => (row.left || row.right).name)
  assert.deepEqual(names, [
    'Study ID',
    'Date of examination',
    'Position',
    'Anatomical Location',
    'Pulse',
  ])
})

test('identical forms produce no differences', () => {
  const result = compareForms(sponsor, sponsor)
  assert.equal(result.differences.length, 0)
  assert.equal(result.stops.length, 0)
})

test('optional fields are ignored until enabled', () => {
  const a = rawForm('A', '1.0', [
    ['G', [rawItem('1', 'Weight', { sds_var_name: 'WEIGHT' })]],
  ])
  const b = rawForm('A', '2.0', [
    ['G', [rawItem('1', 'Weight', { sds_var_name: 'WGT' })]],
  ])
  assert.equal(compareForms(a, b).differences.length, 0)
  const withSdtm = compareForms(a, b, { enabledFields: new Set(['sdtm']) })
  assert.equal(withSdtm.differences.length, 1)
  assert.deepEqual([...withSdtm.rows[1].detail.scalars], ['sdtm'])
})

test('translated text is compared in the selected language only', () => {
  const text = (language, value) => [
    { text_type: 'osb:DesignNotes', language, text: value },
  ]
  const a = rawForm('A', '1.0', [
    ['G', [rawItem('1', 'Weight', { translated_texts: text('en', 'x') })]],
  ])
  const b = rawForm('A', '2.0', [
    ['G', [rawItem('1', 'Weight', { translated_texts: text('en', 'y') })]],
  ])
  const enabledFields = new Set(['designNotes'])
  assert.equal(
    compareForms(a, b, { enabledFields, language: 'en' }).differences.length,
    1
  )
  assert.equal(
    compareForms(a, b, { enabledFields, language: 'da' }).differences.length,
    0
  )
})

test('a term gained on one side and lost on the other is a plain change', () => {
  const a = rawForm('A', '1.0', [
    [
      'G',
      [
        rawItem('1', 'Pos', {
          terms: [term('t1', 'Sit', 1), term('t2', 'Lie', 2)],
        }),
      ],
    ],
  ])
  const b = rawForm('A', '2.0', [
    [
      'G',
      [
        rawItem('1', 'Pos', {
          terms: [term('t1', 'Sit', 1), term('t3', 'Stand', 2)],
        }),
      ],
    ],
  ])
  assert.equal(compareForms(a, b).rows[1].status, 'changed')
})

test('a group present on one side only marks the group and its items', () => {
  const a = rawForm('A', '1.0', [['Extra', [rawItem('1', 'Only here')]]])
  const b = rawForm('A', '2.0', [])
  const { rows } = compareForms(a, b)
  assert.deepEqual(
    rows.map((row) => row.status),
    ['added', 'added']
  )
})

test('filterRows keeps only differing rows and their group headers', () => {
  const { rows } = compareForms(sponsor, veeva)
  const filtered = filterRows(rows, true)
  assert.deepEqual(
    filtered.map((row) => (row.left || row.right).name),
    [
      'Vital Signs',
      'Date of examination',
      'Blood pressure and pulse',
      'Position',
      'Anatomical Location',
    ]
  )
  assert.equal(filterRows(rows, false), rows)
})

test('pairElements prefers uid over name', () => {
  const left = [
    { uid: 'a', name: 'X' },
    { uid: 'b', name: 'Y' },
  ]
  const right = [
    { uid: 'b', name: 'X' },
    { uid: 'a', name: 'Y' },
  ]
  const pairs = pairElements(left, right)
  assert.deepEqual(
    pairs.map((p) => [p.left.uid, p.right.uid]),
    [
      ['b', 'b'],
      ['a', 'a'],
    ]
  )
})

test('alignLists puts left-only keys as added and right-only as missing', () => {
  const lines = alignLists(
    [{ key: 'a' }, { key: 'b' }],
    [{ key: 'a' }, { key: 'c' }]
  )
  assert.deepEqual(
    lines.map((line) => line.state),
    ['same', 'missing', 'added']
  )
})

// --- extra attributes and reordering ---------------------------------------

function treeOf(formExtra, groups) {
  return normalizeFormTree({
    form: {
      uid: 'f',
      name: 'F',
      library_name: 'L',
      version: '1.0',
      ...formExtra,
    },
    groups: groups.map(([uid, groupExtra, items]) => ({
      ref: {},
      group: { uid, name: uid, version: '1.0', ...groupExtra },
      items: items.map(([itemUid, itemExtra = {}]) =>
        rawItem(itemUid, itemUid, itemExtra)
      ),
    })),
  })
}

test('extra attributes are ignored until switched on', () => {
  const left = treeOf({ oid: 'F.1' }, [['g', { oid: 'G.1' }, [['i']]]])
  const right = treeOf({ oid: 'F.2' }, [['g', { oid: 'G.2' }, [['i']]]])
  const result = compareForms(left, right)
  assert.equal(result.differences.length, 0)
  assert.equal(
    result.rows.some((row) => row.kind === 'form'),
    false
  )
})

test('form, group and item scalar attributes are compared per level', () => {
  const left = treeOf({ oid: 'F.1', repeating: 'Yes' }, [
    ['g', { oid: 'G.1' }, [['i', { oid: 'I.1', origin: 'CRF' }]]],
  ])
  const right = treeOf({ oid: 'F.1', repeating: 'No' }, [
    ['g', { oid: 'G.2' }, [['i', { oid: 'I.1', origin: 'eDT' }]]],
  ])
  const enabled = new Set([
    'form.oid',
    'form.repeating',
    'group.oid',
    'item.oid',
    'item.origin',
  ])
  const { rows } = compareForms(left, right, { enabledFields: enabled })
  const [form, group, item] = rows
  assert.equal(form.kind, 'form')
  assert.deepEqual([...form.detail.scalars], ['repeating'])
  assert.equal(group.status, 'changed')
  assert.deepEqual([...group.detail.scalars], ['oid'])
  assert.equal(item.status, 'changed')
  assert.deepEqual([...item.detail.scalars], ['origin'])
})

test('list attributes report added and missing entries', () => {
  const alias = (name) => ({ name, context: 'ctx' })
  const left = treeOf({ aliases: [alias('a'), alias('b')] }, [])
  const right = treeOf({ aliases: [alias('a'), alias('c')] }, [])
  const { rows } = compareForms(left, right, {
    enabledFields: new Set(['form.aliases']),
  })
  assert.equal(rows[0].status, 'changed')
  assert.deepEqual(
    rows[0].detail.lists.aliases.map((line) => line.state),
    ['same', 'missing', 'added']
  )
})

test('descriptions are compared in the selected language only', () => {
  const description = (language, text) => [
    { text_type: 'Description', language, text },
  ]
  const left = treeOf({ translated_texts: description('en', 'one') }, [])
  const right = treeOf({ translated_texts: description('en', 'two') }, [])
  const enabled = new Set(['form.descriptions'])
  assert.equal(
    compareForms(left, right, { enabledFields: enabled }).rows[0].status,
    'changed'
  )
  assert.equal(
    compareForms(left, right, { enabledFields: enabled, language: 'da' })
      .rows[0].status,
    'same'
  )
})

test('vendor extensions of an item are compared by value', () => {
  const vendor = (value) => ({
    vendor_attributes: [{ uid: 'va', name: 'attr', value }],
  })
  const left = treeOf({}, [['g', {}, [['i', vendor('x')]]]])
  const right = treeOf({}, [['g', {}, [['i', vendor('y')]]]])
  const item = compareForms(left, right, {
    enabledFields: new Set(['item.vendor']),
  }).rows.find((row) => row.kind === 'item')
  assert.equal(item.status, 'changed')
})

test('a moved item is flagged but its neighbours are not', () => {
  const left = treeOf({}, [['g', {}, [['a'], ['b'], ['c'], ['d']]]])
  const right = treeOf({}, [['g', {}, [['b'], ['c'], ['d'], ['a']]]])
  const items = compareForms(left, right).rows.filter(
    (row) => row.kind === 'item'
  )
  assert.deepEqual(
    items.map((row) => [row.left.uid, row.status]),
    [
      ['b', 'same'],
      ['c', 'same'],
      ['d', 'same'],
      ['a', 'changed'],
    ]
  )
  assert.equal(items[3].detail.scalars.has('order'), true)
})

test('a moved group is flagged as changed', () => {
  const left = treeOf({}, [
    ['g1', {}, []],
    ['g2', {}, []],
    ['g3', {}, []],
  ])
  const right = treeOf({}, [
    ['g2', {}, []],
    ['g3', {}, []],
    ['g1', {}, []],
  ])
  const groups = compareForms(left, right).rows.filter(
    (row) => row.kind === 'group'
  )
  assert.deepEqual(
    groups.map((row) => row.status),
    ['same', 'same', 'changed']
  )
  assert.equal(groups[2].detail.scalars.has('order'), true)
})

test('additions and removals do not count as moves', () => {
  const left = treeOf({}, [['g', {}, [['a'], ['x'], ['b']]]])
  const right = treeOf({}, [['g', {}, [['a'], ['b'], ['y']]]])
  const statuses = compareForms(left, right)
    .rows.filter((row) => row.kind === 'item')
    .map((row) => row.status)
  assert.deepEqual(statuses, ['same', 'added', 'same', 'missing'])
})

// --- ODM file sources ---------------------------------------------------------

// What the parse endpoint returns per FormDef; the composable's loadFile runs it
// through normalizeFormTree. Synthetic uids (the OID), version 'file'.
function fileTree(groups) {
  return {
    form: { uid: 'F.VS', name: 'Vital Signs', version: 'file' },
    groups: groups.map(([oid, name, items]) => ({
      ref: { mandatory: 'Yes' },
      group: { uid: oid, name, version: 'file' },
      items: items.map(([itemOid, itemName, extra]) => ({
        ref: { mandatory: 'No' },
        item: {
          uid: itemOid,
          name: itemName,
          version: 'file',
          terms: [],
          unit_definitions: [],
          activity_instances: [],
          translated_texts: [],
          ...extra,
        },
      })),
    })),
  }
}

test('a file-shaped tree pairs by name with a DB-shaped tree', () => {
  const file = {
    ...normalizeFormTree(
      fileTree([
        [
          'IG.VS',
          'Vital Signs',
          [
            ['I.STUDYID', 'Study ID', {}],
            ['I.VSDAT', 'Date of examination', { prompt: 'DD-MM-YYYY' }],
          ],
        ],
        ['IG.EXTRA', 'Only in file', [['I.X', 'X', {}]]],
      ])
    ),
    libraryName: 'vs.xml',
    version: 'file',
  }
  assert.equal(file.version, 'file')
  assert.equal(file.groups[0].uid, 'IG.VS')

  // DB side: different uids, same names.
  const db = rawForm('Sponsor', '1.0', [
    [
      'Vital Signs',
      [
        rawItem('CrfItem_1', 'Study ID'),
        rawItem('CrfItem_2', 'Date of examination', { prompt: 'MM-DD-YYYY' }),
      ],
    ],
  ])

  for (const [left, right] of [
    [file, db],
    [db, file],
  ]) {
    const result = compareForms(left, right)
    assert.equal(itemRow(result, 'Study ID').status, 'same')
    const date = itemRow(result, 'Date of examination')
    assert.equal(date.status, 'changed')
    assert.deepEqual([...date.detail.scalars], ['prompt'])
    // The group present only in the file is flagged on the file's side.
    const extra = result.rows.find(
      (row) =>
        row.kind === 'group' && (row.left || row.right).name === 'Only in file'
    )
    assert.equal(extra.status, left === file ? 'added' : 'missing')
  }
})

test('two file-shaped trees pair by their OID uids', () => {
  const a = normalizeFormTree(
    fileTree([['IG.1', 'Renamed', [['I.1', 'Weight', {}]]]])
  )
  const b = normalizeFormTree(
    fileTree([['IG.1', 'Vitals', [['I.1', 'Body weight', {}]]]])
  )
  const result = compareForms(a, b)
  const group = result.rows.find((row) => row.kind === 'group')
  assert.equal(group.left.uid, 'IG.1')
  assert.equal(group.right.uid, 'IG.1')
  const item = result.rows.find((row) => row.kind === 'item')
  assert.equal(item.left.uid, 'I.1')
  assert.equal(item.right.uid, 'I.1')
})

test('the keys comparison ignores the version when a side is a file', () => {
  const fileItem = { oid: 'I.1', version: 'file' }
  const dbItem = { oid: 'I.1', version: '3.0' }
  assert.equal(keysDiffer(formatKeys(fileItem), formatKeys(dbItem)), false)
  assert.equal(keysDiffer(formatKeys(dbItem), formatKeys(fileItem)), false)
  assert.equal(
    keysDiffer(formatKeys({ oid: 'I.2', version: 'file' }), formatKeys(dbItem)),
    true
  )
  assert.equal(
    keysDiffer(formatKeys(dbItem), formatKeys({ oid: 'I.1', version: '4.0' })),
    true
  )
})

function collectionOf(...forms) {
  return {
    uid: 'c',
    name: 'C',
    libraryName: 'L',
    version: '1.0',
    forms: forms.map(([uid, groups]) => ({
      ...treeOf({ uid, name: uid }, groups),
    })),
  }
}

test('collections pair forms and compare each pair', () => {
  const left = collectionOf(
    ['f1', [['g', {}, [['a'], ['b']]]]],
    ['f2', [['g', {}, [['a']]]]]
  )
  const right = collectionOf(
    ['f1', [['g', {}, [['a']]]]],
    ['f3', [['g', {}, [['a']]]]]
  )
  const result = compareCollections(left, right, { enabledFields: new Set() })
  const headers = result.rows.filter((row) => row.kind === 'collectionForm')
  assert.deepEqual(
    headers.map((row) => row.status),
    ['same', 'missing', 'added']
  )
  assert.equal(
    new Set(result.rows.map((row) => row.id)).size,
    result.rows.length
  )
  const itemB = result.rows.find((row) => row.left?.name === 'b')
  assert.equal(itemB.status, 'added')
  assert.equal(itemB.forms.left.uid, 'f1')
  assert.ok(
    result.rows.find((row) => row.id === itemB.groupId),
    'item group row is in the list'
  )
  assert.equal(result.differences.length, 7)
})

test('only-differences keeps just the forms and groups that differ', () => {
  const left = collectionOf(
    ['f1', [['g', {}, [['a']]]]],
    ['f2', [['g', {}, [['a'], ['b']]]]]
  )
  const right = collectionOf(
    ['f1', [['g', {}, [['a']]]]],
    ['f2', [['g', {}, [['a']]]]]
  )
  const { rows } = compareCollections(left, right, { enabledFields: new Set() })
  assert.deepEqual(
    filterRows(rows, true).map((row) => row.kind),
    ['collectionForm', 'group', 'item']
  )
})

test('a changed form name or group mandatory flag is a difference', () => {
  const tree = (formName, mandatory) =>
    normalizeFormTree({
      form: { uid: 'f', name: formName, version: '1.0' },
      groups: [
        {
          ref: { mandatory },
          group: { uid: 'g', name: 'Group', version: '1.0' },
          items: [],
        },
      ],
    })
  const same = compareForms(tree('A', 'Yes'), tree('A', 'Yes'))
  assert.equal(
    same.rows.some((row) => row.kind === 'form'),
    false
  )
  assert.deepEqual(same.differences, [])

  const result = compareForms(tree('A', 'Yes'), tree('B', 'No'))
  const [form, group] = result.rows
  assert.equal(form.kind, 'form')
  assert.equal(form.status, 'changed')
  assert.ok(form.detail.scalars.has('name'))
  assert.equal(group.status, 'changed')
  assert.ok(group.detail.scalars.has('mandatory'))
})
