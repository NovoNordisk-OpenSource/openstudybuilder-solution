/**
 * Hand-tuned demo fixtures for the CRF Compare tab.
 *
 * One form, "Vital Signs", in two versions that differ the way the design
 * mockup does: a changed prompt, a term dropped, and an item added. Every
 * handler returns undefined for uids it does not own, so the schema-walked
 * placeholders keep serving the rest of the CRF Builder.
 */

const LIBRARY = 'Library A'
const FORM_VS = 'CrfForm_000001'
const FORM_DM = 'CrfForm_000002'

const term = (uid, name, order) => ({
  term_uid: uid,
  name,
  display_text: name,
  submission_value: name.toUpperCase(),
  order,
})

const question = (text) => [{ text_type: 'osb:Question', language: 'en', text }]

function item(uid, version, name, extra = {}) {
  return {
    uid,
    version,
    name,
    library_name: LIBRARY,
    status: 'Final',
    prompt: '',
    datatype: { submission_value: 'text', name: 'text' },
    length: null,
    sds_var_name: '',
    terms: [],
    unit_definitions: [],
    activity_instances: [],
    translated_texts: [],
    ...extra,
  }
}

const ITEMS = {
  'CrfItem_000001@1.0': item('CrfItem_000001', '1.0', 'Study ID', {
    length: 20,
  }),
  'CrfItem_000002@1.0': item('CrfItem_000002', '1.0', 'Date of examination', {
    prompt: 'DD-MM-YYYY',
    datatype: { submission_value: 'date', name: 'date' },
    translated_texts: question('Date of examination'),
  }),
  'CrfItem_000002@2.0': item('CrfItem_000002', '2.0', 'Date of examination', {
    prompt: 'MM-DD-YYYY',
    datatype: { submission_value: 'date', name: 'date' },
    translated_texts: question('Date of examination'),
  }),
  'CrfItem_000003@1.0': item('CrfItem_000003', '1.0', 'Position', {
    translated_texts: question('Position of the subject'),
    terms: [
      term('CTTerm_SIT', 'Sitting', 1),
      term('CTTerm_SUP', 'Supine Position', 2),
      term('CTTerm_STA', 'Standing', 3),
    ],
  }),
  'CrfItem_000003@2.0': item('CrfItem_000003', '2.0', 'Position', {
    translated_texts: question('Position of the subject'),
    terms: [
      term('CTTerm_SIT', 'Sitting', 1),
      term('CTTerm_STA', 'Standing', 2),
    ],
  }),
  'CrfItem_000004@1.0': item('CrfItem_000004', '1.0', 'Anatomical Location'),
  'CrfItem_000005@1.0': item('CrfItem_000005', '1.0', 'Pulse', {
    oid: 'I.PULSE',
    datatype: { submission_value: 'integer', name: 'integer' },
    length: 3,
    unit_definitions: [{ uid: 'Unit_BPM', name: 'beats/min', order: 1 }],
  }),
  'CrfItem_000006@1.0': item('CrfItem_000006', '1.0', 'Birth date', {
    datatype: { submission_value: 'date', name: 'date' },
  }),
}

const itemRef = (uid, version, extra = {}) => ({
  uid,
  version,
  mandatory: 'No',
  order: 1,
  ...extra,
})

const GROUPS = {
  'CrfGroup_000001@1.0': {
    uid: 'CrfGroup_000001',
    version: '1.0',
    name: 'Vital Signs',
    library_name: LIBRARY,
    items: [
      itemRef('CrfItem_000001', '1.0', { mandatory: 'Yes', order: 1 }),
      itemRef('CrfItem_000002', '1.0', { order: 2 }),
    ],
  },
  'CrfGroup_000001@2.0': {
    uid: 'CrfGroup_000001',
    version: '2.0',
    name: 'Vital Signs',
    library_name: LIBRARY,
    items: [
      itemRef('CrfItem_000001', '1.0', { mandatory: 'Yes', order: 1 }),
      itemRef('CrfItem_000002', '2.0', { order: 2 }),
    ],
  },
  'CrfGroup_000002@1.0': {
    uid: 'CrfGroup_000002',
    version: '1.0',
    name: 'Blood pressure and pulse',
    library_name: LIBRARY,
    items: [
      itemRef('CrfItem_000003', '1.0', { order: 1 }),
      itemRef('CrfItem_000005', '1.0', { order: 2 }),
    ],
  },
  'CrfGroup_000002@2.0': {
    uid: 'CrfGroup_000002',
    version: '2.0',
    name: 'Blood pressure and pulse',
    library_name: LIBRARY,
    items: [
      itemRef('CrfItem_000003', '2.0', { order: 1 }),
      itemRef('CrfItem_000004', '1.0', { order: 2 }),
      itemRef('CrfItem_000005', '1.0', { order: 3 }),
    ],
  },
  'CrfGroup_000003@1.0': {
    uid: 'CrfGroup_000003',
    version: '1.0',
    name: 'Demographics',
    library_name: LIBRARY,
    items: [itemRef('CrfItem_000006', '1.0')],
  },
}

const groupRef = (uid, version, order) => ({
  uid,
  version,
  order,
  mandatory: 'Yes',
})

const FORMS = {
  [`${FORM_VS}@1.0`]: {
    uid: FORM_VS,
    name: 'Vital Signs',
    version: '1.0',
    status: 'Final',
    oid: 'F.VS',
    item_groups: [
      groupRef('CrfGroup_000001', '1.0', 1),
      groupRef('CrfGroup_000002', '1.0', 2),
    ],
  },
  [`${FORM_VS}@2.0`]: {
    uid: FORM_VS,
    name: 'Vital Signs',
    version: '2.0',
    status: 'Draft',
    oid: 'F.VS.2',
    item_groups: [
      groupRef('CrfGroup_000001', '2.0', 1),
      groupRef('CrfGroup_000002', '2.0', 2),
    ],
  },
  [`${FORM_DM}@1.0`]: {
    uid: FORM_DM,
    name: 'Demographics',
    version: '1.0',
    status: 'Final',
    item_groups: [groupRef('CrfGroup_000003', '1.0', 1)],
  },
}

const FORM_VERSIONS = {
  [FORM_VS]: [
    { version: '2.0', status: 'Draft' },
    { version: '1.0', status: 'Final' },
  ],
  [FORM_DM]: [{ version: '1.0', status: 'Final' }],
}

const versionNumber = (version) => Number(version)

// An element looked up without a version is its newest one, as on the API.
function latestVersion(store, uid) {
  const versions = Object.keys(store)
    .filter((key) => key.startsWith(`${uid}@`))
    .map((key) => key.split('@')[1])
  return versions.sort((a, b) => versionNumber(b) - versionNumber(a))[0]
}

// POST .../versions answers with a Draft copy of the newest version. Nothing is
// stored; the write is only recorded in globalThis.__demoLastWrite.
const newDraft = (regex, store) => ({
  method: 'POST',
  regex,
  respond: ({ routeParams, clone }) => {
    const latest =
      store[`${routeParams.uid}@${latestVersion(store, routeParams.uid)}`]
    if (!latest) return undefined
    const next = (versionNumber(latest.version) + 0.1).toFixed(1)
    return { data: clone({ ...latest, version: next, status: 'Draft' }) }
  },
})

export const crfHandlers = [
  {
    method: 'GET',
    regex: /^\/libraries$/,
    respond: () => ({ data: [{ name: LIBRARY, is_editable: true }] }),
  },
  {
    method: 'GET',
    regex: /^\/odms\/forms$/,
    respond: ({ params }) => {
      if (params?.library_name !== LIBRARY || params?.fields !== 'uid,name') {
        return undefined
      }
      const items = [
        { uid: FORM_VS, name: 'Vital Signs' },
        { uid: FORM_DM, name: 'Demographics' },
      ]
      return { data: { items, total: items.length, page: 1, size: 0 } }
    },
  },
  {
    method: 'GET',
    regex: /^\/odms\/forms\/(?<uid>[^/]+)\/versions$/,
    respond: ({ routeParams, clone }) => {
      const versions = FORM_VERSIONS[routeParams.uid]
      return versions ? { data: clone(versions) } : undefined
    },
  },
  {
    method: 'GET',
    regex: /^\/odms\/forms\/(?<uid>[^/]+)$/,
    respond: ({ routeParams, params, clone }) => {
      const version =
        params?.version ?? FORM_VERSIONS[routeParams.uid]?.[0]?.version
      const form = FORMS[`${routeParams.uid}@${version}`]
      return form
        ? { data: clone({ library_name: LIBRARY, ...form }) }
        : undefined
    },
  },
  {
    method: 'GET',
    regex: /^\/odms\/item-groups\/(?<uid>CrfGroup_\d+)$/,
    respond: ({ routeParams, params, clone }) => {
      const version = params?.version ?? latestVersion(GROUPS, routeParams.uid)
      const group = GROUPS[`${routeParams.uid}@${version}`]
      return group ? { data: clone(group) } : undefined
    },
  },
  newDraft(/^\/odms\/item-groups\/(?<uid>CrfGroup_\d+)\/versions$/, GROUPS),
  {
    method: 'GET',
    regex: /^\/odms\/items\/(?<uid>CrfItem_\d+)$/,
    respond: ({ routeParams, params, clone }) => {
      const version = params?.version ?? latestVersion(ITEMS, routeParams.uid)
      const found = ITEMS[`${routeParams.uid}@${version}`]
      return found ? { data: clone(found) } : undefined
    },
  },
  newDraft(/^\/odms\/items\/(?<uid>CrfItem_\d+)\/versions$/, ITEMS),
  // ODM XML parse (nothing stored): one "Vital Signs" form whose elements carry
  // synthetic OID uids and version 'file', as the real endpoint returns them.
  {
    method: 'POST',
    regex: /^\/odms\/metadata\/xmls\/parse$/,
    respond: ({ clone }) => {
      const fileItem = (oid, name, extra = {}) => ({
        ref: { mandatory: 'No', order_number: 1 },
        item: item(oid, 'file', name, { oid, ...extra }),
      })
      const forms = [
        {
          form: {
            uid: 'F.VS',
            version: 'file',
            name: 'Vital Signs',
            oid: 'F.VS',
          },
          groups: [
            {
              ref: { mandatory: 'Yes', order_number: 1 },
              group: {
                uid: 'IG.VS',
                version: 'file',
                name: 'Vital Signs',
                oid: 'IG.VS',
              },
              items: [
                fileItem('I.STUDYID', 'Study ID', { length: 20 }),
                fileItem('I.VSDAT', 'Date of examination', {
                  prompt: 'YYYY-MM-DD',
                  datatype: { submission_value: 'date', name: 'date' },
                }),
              ],
            },
          ],
        },
      ]
      return { data: clone({ forms }) }
    },
  },
]
