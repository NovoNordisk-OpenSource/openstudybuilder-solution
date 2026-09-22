/**
 * Hand-tuned demo fixtures for the library slice.
 *
 * Add entries here when the schema-walked placeholders break a view — e.g. when
 * the UI expects a coherent enumeration of real-world values rather than
 * synthetic "X A / X B / X C" labels.
 *
 * Same handler shape as studies.js: { method, regex, respond(ctx) }.
 */

// Mutable demo state: enabled is independent of status (Final/Retired).
const DEMO_FEATURE_FLAGS = [
  'activity_instance_wizard_stepper_interventions',
  'new_activity_instance_wizard_stepper',
  'complexity_score_calculation',
  'complexity_score_details',
  'compounds_library',
  'compounds_studies',
  'loinc_dictionary',
  'meddra_dictionary',
  'soa_protocol_lab_table',
  'streamline_placeholder_activities',
  'studies_view_listings_analysis_study_metadata_new',
  'study_data_suppliers',
  'nsvs_library',
].map((name, idx) => ({
  uid: `FeatureFlag_${String(idx + 1).padStart(6, '0')}`,
  section: 'studies',
  feature: name,
  name,
  enabled: true,
  status: 'Final',
  version: '1.0',
}))

function findDemoFeatureFlag(uid) {
  return DEMO_FEATURE_FLAGS.find((flag) => flag.uid === uid)
}

function bumpMinorVersion(version) {
  const [majorRaw, minorRaw] = String(version || '1.0').split('.')
  const major = Number.parseInt(majorRaw, 10)
  const minor = Number.parseInt(minorRaw, 10)
  const nextMajor = Number.isNaN(major) ? 1 : major
  const nextMinor = Number.isNaN(minor) ? 1 : minor + 1
  return `${nextMajor}.${nextMinor}`
}

const CT_CATALOGUES = [
  { name: 'SDTM CT', library_name: 'CDISC' },
  { name: 'SEND CT', library_name: 'CDISC' },
  { name: 'ADAM CT', library_name: 'CDISC' },
  { name: 'CDASH CT', library_name: 'CDISC' },
  { name: 'COA CT', library_name: 'CDISC' },
  { name: 'Protocol CT', library_name: 'CDISC' },
  { name: 'QRS CT', library_name: 'CDISC' },
  { name: 'QS CT', library_name: 'CDISC' },
]

// Minimal Activity object — schema walker leaves `used_by_studies` null on
// some cycles, but BaseActivityOverview unconditionally reads
// `item.used_by_studies` and `item.possible_actions`.
function buildActivity(uid) {
  return {
    uid,
    name: 'Demo Activity',
    name_sentence_case: 'Demo activity',
    definition: 'Synthetic demo activity for offline mode.',
    abbreviation: null,
    library_name: 'Sponsor',
    nci_concept_id: null,
    nci_concept_name: null,
    synonyms: [],
    activity_groupings: [],
    request_rationale: null,
    is_request_final: false,
    is_request_rejected: false,
    contact_person: null,
    reason_for_rejecting: null,
    requester_study_id: null,
    replaced_by_activity: null,
    is_data_collected: true,
    is_multiple_selection_allowed: true,
    is_finalized: false,
    is_used_by_legacy_instances: false,
    status: 'Draft',
    version: '0.1',
    change_description: 'Initial draft',
    author_username: 'demo-user',
    start_date: '2026-01-15T10:00:00Z',
    end_date: null,
    possible_actions: ['edit', 'approve', 'delete'],
    used_by_studies: [],
  }
}

function buildActivityOverview(uid) {
  return {
    activity: buildActivity(uid),
    activity_groupings: [],
    activity_instances: [],
    all_versions: ['0.1'],
  }
}

function buildActivityItemClassOverview(uid) {
  return {
    activity_item_class: {
      uid,
      name: 'Demo Activity Item Class',
      definition: 'Synthetic demo item class for offline mode.',
      nci_code: null,
      order: 1,
      mandatory: false,
      data_type: { uid: 'CT_DATA_TYPE_TEXT', name: 'Text' },
      role: { uid: 'CT_ROLE_TOPIC', name: 'Topic' },
      library_name: 'Sponsor',
      status: 'Draft',
      version: '0.1',
      start_date: '2026-01-15T10:00:00Z',
      end_date: null,
      author_username: 'demo-user',
      modified_date: '2026-01-15T10:00:00Z',
      possible_actions: ['edit', 'approve', 'delete'],
    },
    activity_instance_classes: [],
    all_versions: ['0.1'],
  }
}

function buildGroup(uid) {
  return {
    uid,
    name: 'Demo Activity Group',
    name_sentence_case: 'Demo activity group',
    definition: 'Synthetic demo group for offline mode.',
    abbreviation: null,
    library_name: 'Sponsor',
    status: 'Draft',
    version: '0.1',
    start_date: '2026-01-15T10:00:00Z',
    end_date: null,
    author_username: 'demo-user',
    change_description: 'Initial draft',
    possible_actions: ['edit', 'approve', 'delete'],
  }
}

function buildGroupOverview(uid) {
  // The view sets `subgroups: null` on the happy path which trips a
  // temporal-dead-zone bug in GroupOverview.vue's immediate-watcher. Routing
  // through the fallback (`/overview`) lets us provide a non-null
  // `subgroups` array so the watcher avoids the broken branch.
  return {
    group: buildGroup(uid),
    subgroups: [],
    all_versions: ['0.1'],
  }
}

// ActivityInstanceForm fetches this list filtered by `name` to build the
// step-2 "activity instance class" dropdown. The generic schema walker
// ignores query filters and fabricates unrelated placeholder names, so the
// wizard would never offer "Interventions" — hand-mock the small set of
// real class names the form actually looks for.
const ACTIVITY_INSTANCE_CLASSES = [
  {
    uid: 'ActivityInstanceClass_000000',
    name: 'ActivityInstanceClass',
    order: 0,
    level: 0,
    is_domain_specific: false,
    parent_class: null,
    definition: 'Synthetic demo root activity instance class for offline mode.',
    library_name: 'Sponsor',
    status: 'Final',
    version: '1.0',
    change_description: 'Approved',
    author_username: 'demo-user',
    start_date: '2026-01-15T10:00:00Z',
    end_date: null,
    possible_actions: ['new_version'],
  },
  {
    uid: 'ActivityInstanceClass_000001',
    name: 'NumericFindings',
    order: 1,
    level: 3,
    is_domain_specific: true,
    parent_class: null,
    definition: 'Synthetic demo activity instance class for offline mode.',
    library_name: 'Sponsor',
    status: 'Final',
    version: '1.0',
    change_description: 'Approved',
    author_username: 'demo-user',
    start_date: '2026-01-15T10:00:00Z',
    end_date: null,
    possible_actions: ['new_version'],
  },
  {
    uid: 'ActivityInstanceClass_000002',
    name: 'Interventions',
    order: 2,
    level: 3,
    is_domain_specific: true,
    parent_class: null,
    definition: 'Synthetic demo activity instance class for offline mode.',
    library_name: 'Sponsor',
    status: 'Final',
    version: '1.0',
    change_description: 'Approved',
    author_username: 'demo-user',
    start_date: '2026-01-15T10:00:00Z',
    end_date: null,
    possible_actions: ['new_version'],
  },
]

function parseFilters(params) {
  if (!params?.filters) {
    return {}
  }
  try {
    return JSON.parse(params.filters)
  } catch {
    return {}
  }
}

export const libraryHandlers = [
  {
    method: 'GET',
    regex: /^\/activity-instance-classes$/,
    respond: ({ clone, params }) => {
      const filters = parseFilters(params)
      let items = ACTIVITY_INSTANCE_CLASSES
      const nameFilter = filters.name?.v
      if (Array.isArray(nameFilter) && nameFilter.length) {
        items = items.filter((item) => nameFilter.includes(item.name))
      }
      const uidFilter = filters.uid?.v
      if (Array.isArray(uidFilter) && uidFilter.length) {
        items = items.filter((item) => uidFilter.includes(item.uid))
      }
      return {
        data: clone({
          items,
          total: items.length,
          page: 1,
          size: items.length,
        }),
      }
    },
  },
  {
    method: 'GET',
    regex: /^\/ct\/catalogues$/,
    respond: ({ clone }) => ({ data: clone(CT_CATALOGUES) }),
  },
  {
    method: 'GET',
    regex: /^\/feature-flags$/,
    respond: ({ clone, params }) => {
      const includeRetired =
        params?.include_retired === true ||
        params?.include_retired === 'true' ||
        params?.include_deprecated === true ||
        params?.include_deprecated === 'true'
      const flags = includeRetired
        ? DEMO_FEATURE_FLAGS
        : DEMO_FEATURE_FLAGS.filter((flag) => flag.status === 'Final')
      return { data: clone(flags) }
    },
  },
  {
    method: 'PATCH',
    regex: /^\/feature-flags\/(?<uid>[^/]+)$/,
    respond: ({ routeParams, data, clone }) => {
      const flag = findDemoFeatureFlag(routeParams.uid)
      if (!flag) {
        return { status: 404, data: { message: 'Feature flag not found' } }
      }
      if (flag.status !== 'Final') {
        return {
          status: 400,
          data: { message: 'Only Final feature flags can be updated.' },
        }
      }
      let changed = false
      if (
        data &&
        typeof data.enabled === 'boolean' &&
        data.enabled !== flag.enabled
      ) {
        flag.enabled = data.enabled
        changed = true
      }
      if (data?.section && data.section !== flag.section) {
        flag.section = data.section
        changed = true
      }
      if (data?.feature && data.feature !== flag.feature) {
        flag.feature = data.feature
        changed = true
      }
      if (data && Object.prototype.hasOwnProperty.call(data, 'description')) {
        const nextDescription = data.description ?? null
        const currentDescription = flag.description ?? null
        if (nextDescription !== currentDescription) {
          flag.description = nextDescription
          changed = true
        }
      }
      if (changed) {
        flag.version = bumpMinorVersion(flag.version)
      }
      return { data: clone(flag) }
    },
  },
  {
    method: 'DELETE',
    regex: /^\/feature-flags\/(?<uid>[^/]+)\/activations$/,
    respond: ({ routeParams, clone }) => {
      const flag = findDemoFeatureFlag(routeParams.uid)
      if (!flag) {
        return { status: 404, data: { message: 'Feature flag not found' } }
      }
      if (flag.status !== 'Final') {
        return {
          status: 400,
          data: { message: 'Only Final feature flags can be inactivated.' },
        }
      }
      // Lifecycle only — do not change enabled
      flag.status = 'Retired'
      return { status: 200, data: clone(flag) }
    },
  },
  {
    method: 'POST',
    regex: /^\/feature-flags\/(?<uid>[^/]+)\/activations$/,
    respond: ({ routeParams, clone }) => {
      const flag = findDemoFeatureFlag(routeParams.uid)
      if (!flag) {
        return { status: 404, data: { message: 'Feature flag not found' } }
      }
      if (flag.status !== 'Retired') {
        return {
          status: 400,
          data: { message: 'Only Retired feature flags can be reactivated.' },
        }
      }
      // Lifecycle only — do not change enabled
      flag.status = 'Final'
      return { status: 200, data: clone(flag) }
    },
  },
  {
    method: 'GET',
    regex: /^\/system\/information$/,
    respond: ({ specInfo }) => ({
      data: {
        api_version: specInfo?.version
          ? `mock backend based on OpenAPI specification ${specInfo.version}`
          : 'mock backend',
        db_version: 'mocked — no database',
        db_name: 'mocked',
        build_id: 'demo',
      },
    }),
  },
  {
    method: 'GET',
    regex: /^\/concepts\/activities\/activities\/(?<uid>[^/]+)$/,
    respond: ({ routeParams }) => ({ data: buildActivity(routeParams.uid) }),
  },
  {
    method: 'GET',
    regex: /^\/concepts\/activities\/activities\/(?<uid>[^/]+)\/overview$/,
    respond: ({ routeParams }) => ({
      data: buildActivityOverview(routeParams.uid),
    }),
  },
  {
    method: 'GET',
    regex:
      /^\/concepts\/activities\/activities\/(?<uid>[^/]+)\/overview\.cosmos$/,
    respond: () => ({ data: '# demo cosmos\n' }),
  },
  {
    method: 'GET',
    regex: /^\/concepts\/activity-item-classes\/(?<uid>[^/]+)\/overview$/,
    respond: ({ routeParams }) => ({
      data: buildActivityItemClassOverview(routeParams.uid),
    }),
  },
  {
    // GroupOverview.vue calls `/details` first; the spec response is
    // ActivityGroupDetail, but the happy-path code sets `subgroups: null` on
    // the resulting overview which trips a TDZ bug in
    // GroupOverview.vue's immediate-watcher. Returning 404 routes the view
    // through its fallback to `/overview`, which surfaces a non-null
    // `subgroups` array (see buildGroupOverview).
    method: 'GET',
    regex: /^\/concepts\/activities\/activity-groups\/(?<uid>[^/]+)\/details$/,
    respond: () => ({ status: 404, data: { message: 'Use /overview' } }),
  },
  {
    method: 'GET',
    regex: /^\/concepts\/activities\/activity-groups\/(?<uid>[^/]+)\/overview$/,
    respond: ({ routeParams }) => ({
      data: buildGroupOverview(routeParams.uid),
    }),
  },
  {
    method: 'GET',
    regex:
      /^\/concepts\/activities\/activity-groups\/(?<uid>[^/]+)\/overview\.cosmos$/,
    respond: () => ({ data: '# demo cosmos\n' }),
  },
  {
    // CodelistTermDetail renders a router-link per parent/child term using
    // `attributes.term_uid`. The schema walker emits placeholder values that
    // can be missing/empty, which trips Vue Router's required-param check
    // and floods console.error. The page handles an empty list cleanly, so
    // hand-mock it that way.
    method: 'GET',
    regex: /^\/ct\/terms\/(?<uid>[^/]+)\/parents$/,
    respond: ({ routeParams }) => ({
      data: { term_uid: routeParams.uid, parents: [], children: [] },
    }),
  },
  {
    // app store boot calls preferencesApi.getUserPreferences() and reads
    // resp.data.preferences. Empty maps are fine — applyPreferences() falls
    // back to hardcoded defaults for missing keys.
    method: 'GET',
    regex: /^\/user-preferences$/,
    respond: () => ({
      data: { preferences: {}, overrides: {}, metadata: {} },
    }),
  },
  {
    method: 'PATCH',
    regex: /^\/user-preferences$/,
    respond: ({ data }) => ({
      data: { preferences: data ?? {}, overrides: {}, metadata: {} },
    }),
  },
  {
    // NSV form needs a SEMTCDT option named "CT Term". Other term queries
    // (criteria/footnote breadcrumbs, sponsor tables) stay on the walker.
    method: 'GET',
    regex: /^\/ct\/codelists\/terms$/,
    respond: ({ params }) => {
      if (params?.codelist_submission_value !== 'SEMTCDT') return undefined
      const items = [
        {
          term_uid: 'CTTerm_DT_CTTERM',
          sponsor_preferred_name: 'CT Term',
          name: 'CT Term',
          submission_value: 'ctTerm',
        },
        {
          term_uid: 'CTTerm_DT_TEXT',
          sponsor_preferred_name: 'Text',
          name: 'Text',
          submission_value: 'text',
        },
      ]
      return { data: { items, total: items.length } }
    },
  },
]
