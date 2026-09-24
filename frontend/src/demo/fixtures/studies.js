/**
 * Hand-tuned demo fixtures for the studies slice.
 *
 * Each handler entry: { method, regex, respond(ctx) }
 * Handlers take precedence over generated fixtures and can read/write
 * `ctx.state` (persisted in localStorage by the mock backend).
 *
 * Add more handlers here as demo coverage gaps are found.
 */

const DEMO_STUDIES = [
  {
    uid: 'Study_000001',
    study_parent_part: null,
    study_subpart_uids: [],
    possible_actions: ['lock', 'release', 'delete'],
    current_metadata: {
      identification_metadata: {
        study_number: '001',
        subpart_id: null,
        study_acronym: 'DEMO-001',
        study_subpart_acronym: null,
        project_number: 'P-001',
        project_name: 'Demo Project',
        clinical_programme_name: 'Demo Programme',
        study_id: 'P-001-001',
        registry_identifiers: {},
      },
      version_metadata: {
        study_status: 'DRAFT',
        version_number: null,
        version_timestamp: '2026-01-15T10:00:00Z',
        version_author: 'demo-user',
        version_description: null,
        locked_version_number: null,
      },
      study_description: {
        study_title: 'Demo Study 001 — A Phase II Trial',
        study_short_title: 'DEMO-001',
      },
      study_population: {},
      high_level_study_design: {},
      study_intervention: {},
    },
    study_number: '001',
    study_id: 'P-001-001',
    study_acronym: 'DEMO-001',
    project_number: 'P-001',
    project_name: 'Demo Project',
    status: 'DRAFT',
    latest_locked_version: null,
    latest_released_version: null,
  },
  {
    uid: 'Study_000002',
    study_parent_part: null,
    study_subpart_uids: [],
    possible_actions: ['lock', 'release', 'delete'],
    current_metadata: {
      identification_metadata: {
        study_number: '002',
        subpart_id: null,
        study_acronym: 'DEMO-002',
        study_subpart_acronym: null,
        project_number: 'P-001',
        project_name: 'Demo Project',
        clinical_programme_name: 'Demo Programme',
        study_id: 'P-001-002',
        registry_identifiers: {},
      },
      version_metadata: {
        study_status: 'RELEASED',
        version_number: '1.0',
        version_timestamp: '2026-02-20T12:00:00Z',
        version_author: 'demo-user',
        version_description: 'Initial release',
        locked_version_number: null,
      },
      study_description: {
        study_title: 'Demo Study 002 — A Phase III Confirmatory Study',
        study_short_title: 'DEMO-002',
      },
      study_population: {},
      high_level_study_design: {},
      study_intervention: {},
    },
    study_number: '002',
    study_id: 'P-001-002',
    study_acronym: 'DEMO-002',
    project_number: 'P-001',
    project_name: 'Demo Project',
    status: 'RELEASED',
    latest_locked_version: null,
    latest_released_version: {
      version_number: '1.0',
      change_description: 'Initial release',
    },
  },
]

function findStudy(uid) {
  return DEMO_STUDIES.find((s) => s.uid === uid)
}

const DEMO_VISITS = [
  {
    uid: 'StudyVisit_001',
    short: 'V1',
    epoch: 'Screening',
    day: -7,
    window: '-1/+1',
  },
  {
    uid: 'StudyVisit_002',
    short: 'V2',
    epoch: 'Treatment',
    day: 1,
    window: '0/+0',
  },
  {
    uid: 'StudyVisit_003',
    short: 'V3',
    epoch: 'Treatment',
    day: 28,
    window: '-2/+2',
  },
  {
    uid: 'StudyVisit_004',
    short: 'V4',
    epoch: 'Follow-up',
    day: 56,
    window: '-3/+3',
  },
]

const cell = (text, extra = {}) => ({ text, span: 1, ...extra })
const ref = (uid, type) => ({ uid, type })

function buildDemoFlowchart() {
  const visits = DEMO_VISITS

  const epochRow = {
    cells: [
      cell(''),
      ...visits.map((v, i) => {
        const sameAsPrev = i > 0 && visits[i - 1].epoch === v.epoch
        return sameAsPrev
          ? cell('')
          : cell(v.epoch, {
              refs: [ref(`StudyEpoch_${v.epoch}`, 'StudyEpoch')],
            })
      }),
    ],
    hide: false,
  }
  const visitRow = {
    cells: [
      cell(''),
      ...visits.map((v) => cell(v.short, { refs: [ref(v.uid, 'StudyVisit')] })),
    ],
    hide: false,
  }
  const dayRow = {
    cells: [cell('Study day'), ...visits.map((v) => cell(String(v.day)))],
    hide: false,
  }
  const windowRow = {
    cells: [cell('Visit window (days)'), ...visits.map((v) => cell(v.window))],
    hide: false,
  }

  // Activity X visit schedule. true = scheduled.
  const activities = [
    {
      uid: 'StudyActivity_001',
      name: 'Informed Consent',
      schedule: [true, false, false, false],
    },
    {
      uid: 'StudyActivity_002',
      name: 'Demographics',
      schedule: [true, true, false, false],
    },
    {
      uid: 'StudyActivity_003',
      name: 'Vital Signs',
      schedule: [true, true, true, true],
    },
  ]

  const bodyRows = [
    {
      cells: [
        cell('GENERAL', {
          style: 'soaGroup',
          refs: [ref('StudySoAGroup_001', 'StudySoAGroup')],
        }),
        ...visits.map(() => cell('')),
      ],
      hide: false,
      order: 1,
    },
    {
      cells: [
        cell('Eligibility', {
          style: 'group',
          refs: [ref('StudyActivityGroup_001', 'StudyActivityGroup')],
        }),
        ...visits.map(() => cell('')),
      ],
      hide: false,
      order: 1,
    },
    {
      cells: [
        cell('Inclusion / Exclusion', {
          style: 'subGroup',
          refs: [ref('StudyActivitySubGroup_001', 'StudyActivitySubGroup')],
        }),
        ...visits.map(() => cell('')),
      ],
      hide: false,
      order: 1,
    },
    ...activities.map((a, ai) => ({
      cells: [
        cell(a.name, {
          style: 'activity',
          refs: [ref(a.uid, 'StudyActivity')],
        }),
        ...a.schedule.map((scheduled, vi) =>
          scheduled
            ? cell('X', {
                refs: [
                  ref(
                    `StudyActivitySchedule_${ai + 1}_${vi + 1}`,
                    'StudyActivitySchedule'
                  ),
                ],
              })
            : cell('')
        ),
      ],
      hide: false,
      order: ai + 1,
    })),
  ]

  return {
    rows: [epochRow, visitRow, dayRow, windowRow, ...bodyRows],
    footnotes: null,
    num_header_rows: 4,
    num_header_cols: 1,
    title: null,
    id: null,
  }
}

function applyOverrides(study, overrides) {
  if (!overrides) return study
  return { ...study, ...overrides }
}

function findStudyMerged(uid, state, clone) {
  const base = findStudy(uid)
  if (!base) return null
  return applyOverrides(clone(base), state.studyOverrides?.[uid])
}

export const studyHandlers = [
  {
    method: 'GET',
    regex: /^\/studies\/list$/,
    respond: ({ state, clone }) => ({
      data: DEMO_STUDIES.map((s) =>
        applyOverrides(clone(s), state.studyOverrides?.[s.uid])
      ),
    }),
  },
  {
    method: 'GET',
    regex: /^\/studies$/,
    respond: ({ state, clone }) => {
      const items = DEMO_STUDIES.map((s) =>
        applyOverrides(clone(s), state.studyOverrides?.[s.uid])
      )
      return {
        data: { items, total: items.length, page: 1, size: 10 },
      }
    },
  },
  {
    method: 'GET',
    regex: /^\/studies\/template$/,
    respond: () => ({ data: null }),
  },
  {
    method: 'GET',
    regex: /^\/studies\/(?<uid>[^/]+)$/,
    respond: ({ routeParams, state, clone }) => {
      const study = findStudyMerged(routeParams.uid, state, clone)
      if (!study) return { status: 404, data: { message: 'Study not found' } }
      return { data: study }
    },
  },
  {
    method: 'PATCH',
    regex: /^\/studies\/(?<uid>[^/]+)$/,
    respond: ({ routeParams, data, state, persist, clone }) => {
      const base = findStudy(routeParams.uid)
      if (!base) return { status: 404, data: { message: 'Study not found' } }
      state.studyOverrides ??= {}
      state.studyOverrides[routeParams.uid] = {
        ...(state.studyOverrides[routeParams.uid] ?? {}),
        ...data,
      }
      persist()
      return {
        data: applyOverrides(
          clone(base),
          state.studyOverrides[routeParams.uid]
        ),
      }
    },
  },
  {
    // SoA flowchart. The UI reads rows[num_header_rows - 3..-1].cells, so we
    // need at least 4 header rows (epoch / visit / day / window) to keep the
    // soaVisitRow/soaDayRow/soaWindowRow computeds well-defined. Body rows
    // walk SoA group → group → subgroup → activities; activity rows must
    // carry visit-aligned schedule cells so currentSelectionMatrix populates.
    method: 'GET',
    regex: /^\/studies\/(?<uid>[^/]+)\/flowchart$/,
    respond: () => ({ data: buildDemoFlowchart() }),
  },
  {
    // Hand-crafted visit list. StudyVisitForm.callbacks() looks up a unit by
    // `studyVisits[i].visit_window_unit_name` (StudyVisitForm.vue:1156); if
    // the name doesn't match anything in the Study Time subset the form
    // throws on `lockedUnit.uid`. Anchoring the seed visit's window unit to
    // the mocked 'days' entry keeps the form safe while letting the visits
    // table render real-looking rows.
    method: 'GET',
    regex: /^\/studies\/(?<uid>[^/]+)\/study-visits$/,
    respond: ({ routeParams }) => {
      const visit = {
        uid: 'StudyVisit_000001',
        study_uid: routeParams.uid,
        study_epoch_uid: 'StudyEpoch_000001',
        study_epoch: {
          term_uid: 'StudyEpoch_000001',
          sponsor_preferred_name: 'Screening',
        },
        study_epoch_name: 'Screening',
        visit_class: 'SINGLE_VISIT',
        visit_subclass: 'SINGLE_VISIT',
        visit_type_name: 'Screening',
        visit_type: { term_uid: 'C_VISIT_TYPE_SCREEN', name: 'Screening' },
        visit_contact_mode: { term_uid: 'C_CONTACT_ON_SITE', name: 'On Site' },
        visit_contact_mode_name: 'On Site',
        time_reference: {
          term_uid: 'C_TIMEREF_GLOBAL_ANCHOR',
          name: 'Global anchor visit',
        },
        time_reference_name: 'Global anchor visit',
        time_value: 0,
        time_unit_uid: 'UNIT_DAYS',
        time_unit_name: 'days',
        visit_name: 'Visit 1',
        visit_short_name: 'V1',
        visit_number: 1,
        unique_visit_number: 100,
        visit_sublabel: null,
        visit_sublabel_reference: null,
        visit_window_min: -1,
        visit_window_max: 1,
        visit_window_unit_uid: 'UNIT_DAYS',
        visit_window_unit_name: 'days',
        description: 'Demo screening visit',
        start_rule: null,
        end_rule: null,
        epoch_allocation: {
          term_uid: 'C_EPOCH_ALLOC_CURRENT',
          name: 'Current visit',
        },
        epoch_allocation_name: 'Current visit',
        is_global_anchor_visit: true,
        is_soa_milestone: false,
        show_visit: true,
        study_day_label: 'Day 1',
        study_day_number: 1,
        study_week_label: 'Week 1',
        study_week_number: 1,
        study_duration_days_label: '1 day',
        study_duration_weeks_label: '1 week',
        possible_actions: ['edit', 'delete'],
        author_username: 'demo-user',
        start_date: '2026-01-15T10:00:00Z',
        status: 'Draft',
        version: '0.1',
      }
      return {
        data: { items: [visit], total: 1, page: 1, size: 1 },
      }
    },
  },
  {
    // StudyVisitForm.callbacks() calls units.getBySubset('Study Time'). Without
    // a 'days' entry the form throws "Cannot read properties of undefined
    // (reading 'uid')" when it runs `defaultUnit.uid` on the schema-walked
    // (and therefore non-matching) result. Provide canonical Study Time units.
    method: 'GET',
    regex: /^\/concepts\/unit-definitions$/,
    respond: () => {
      const baseUnit = (uid, name, factor) => ({
        uid,
        name,
        library_name: 'Sponsor',
        status: 'Final',
        version: '1.0',
        start_date: '2026-01-15T10:00:00Z',
        change_description: 'Initial demo seed',
        convertible_unit: true,
        display_unit: true,
        master_unit: false,
        si_unit: false,
        us_conventional_unit: false,
        use_complex_unit_conversion: false,
        template_parameter: false,
        conversion_factor_to_master: factor,
        ct_units: [],
        unit_subsets: [{ term_uid: 'STUDY_TIME', term_name: 'Study Time' }],
        unit_dimension: { term_uid: 'TIME', term_name: 'Time' },
      })
      const TIME_UNITS = [
        baseUnit('UNIT_DAYS', 'days', 86400),
        baseUnit('UNIT_WEEKS', 'weeks', 604800),
      ]
      return {
        data: {
          items: TIME_UNITS,
          total: TIME_UNITS.length,
          page: 1,
          size: TIME_UNITS.length,
        },
      }
    },
  },
  {
    method: 'GET',
    regex: /^\/projects$/,
    respond: () => ({
      data: {
        items: [
          {
            uid: 'Project_000001',
            project_number: 'P-001',
            name: 'Demo Project',
            description: 'Demo project for offline mode',
            clinical_programme: { uid: 'CP_000001', name: 'Demo Programme' },
          },
        ],
        total: 1,
        page: 1,
        size: 10,
      },
    }),
  },
]
