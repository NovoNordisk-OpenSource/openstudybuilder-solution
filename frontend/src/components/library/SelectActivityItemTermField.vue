<template>
  <div class="d-flex">
    <template
      v-if="
        props.activityItemClass.name !== 'unit_dimension' &&
        codelists.length > 1
      "
    >
      <v-select
        v-model="codelist"
        :label="$t('ActivityInstanceForm.codelist')"
        :items="codelists"
        item-value="codelist_uid"
        item-title="name.name"
        bg-color="white"
        class="mr-4"
        :disabled="props.disabled"
        :loading="loadingCodelists"
        @update:model-value="changeCodelist"
      />
    </template>
    <v-select
      :model-value="model"
      :label="props.label"
      :items="allItems"
      item-value="term_uid"
      :item-title="props.itemTitle"
      bg-color="white"
      :disabled="props.disabled"
      :rules="validationRules"
      :multiple="props.multiple"
      :loading="loading"
      @update:model-value="onTermsChanged"
    >
      <template #menu-header>
        <SelectMenuSearch
          v-model="search"
          :placeholder="$t('_global.search')"
          @clear="reset"
        />
      </template>
      <template v-if="hasInvalidTerms" #append-inner>
        <v-tooltip location="top">
          <template #activator="{ props: tooltipProps }">
            <v-icon
              v-bind="tooltipProps"
              color="warning"
              icon="mdi-alert"
              size="small"
            />
          </template>
          {{ $t('ActivityInstanceForm.termNotInCodelist') }}
        </v-tooltip>
      </template>
      <template #item="{ item, props: itemProps }">
        <v-list-item v-bind="itemProps">
          <template v-if="props.multiple" #prepend="{ isActive }">
            <v-checkbox-btn :model-value="isActive" />
          </template>
          <template v-if="invalidTermUids.has(item.value)" #append>
            <v-icon color="warning" icon="mdi-alert" size="small" />
          </template>
        </v-list-item>
      </template>
    </v-select>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { i18n } from '@/plugins/i18n'
import activityItemClassesApi from '@/api/activityItemClasses'
import codelistsApi from '@/api/controlledTerminology/codelists'
import termsApi from '@/api/controlledTerminology/terms'
import SelectMenuSearch from '@/components/tools/SelectMenuSearch.vue'
import _debounce from 'lodash/debounce'

const emit = defineEmits(['updatecodelist'])

const props = defineProps({
  activityItemClass: {
    type: Object,
    default: null,
  },
  dataDomain: {
    type: String,
    default: null,
  },
  label: {
    type: String,
    default: () => i18n.t('ActivityInstanceForm.value'),
  },
  itemTitle: {
    type: String,
    default: 'title',
  },
  multiple: {
    type: Boolean,
    default: false,
  },
  rules: {
    type: Array,
    default: () => [],
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})
const codelist = defineModel('codelist', { type: String })
const model = defineModel({ type: [String, Array] })
const search = defineModel('search', { type: String })

const ALL_TERMS_UID = '__ALL_TERMS__'

const codelists = ref([])
const allowedValues = ref([])
const invalidTermUids = ref(new Set())
const loading = ref(false)
const loadingCodelists = ref(false)

const allItems = computed(() => {
  if (props.multiple) {
    const allTermsItem = {
      term_uid: ALL_TERMS_UID,
      sponsor_preferred_name: i18n.t(
        'ActivityInstanceForm.all_terms_in_codelist'
      ),
    }
    return [allTermsItem, ...allowedValues.value]
  }
  return allowedValues.value
})

const hasInvalidTerms = computed(() => {
  if (!model.value || invalidTermUids.value.size === 0) return false
  if (typeof model.value === 'string') {
    return invalidTermUids.value.has(model.value)
  }
  return model.value.some((uid) => invalidTermUids.value.has(uid))
})

const validationRules = computed(() => [
  ...props.rules,
  () =>
    !hasInvalidTerms.value || i18n.t('ActivityInstanceForm.termNotInCodelist'),
])

function onTermsChanged(newVal) {
  if (Array.isArray(newVal) && newVal.includes(ALL_TERMS_UID)) {
    const prevHadAll =
      Array.isArray(model.value) && model.value.includes(ALL_TERMS_UID)
    if (!prevHadAll) {
      // Just selected "All terms" — clear specific terms
      model.value = [ALL_TERMS_UID]
    } else if (newVal.length > 1) {
      // Had "All terms" and now a specific term was added — deselect "All terms"
      model.value = newVal.filter((uid) => uid !== ALL_TERMS_UID)
    } else {
      model.value = newVal
    }
  } else {
    model.value = newVal
  }
}

const changeCodelist = (codelist) => {
  // find the selected codelist object in the codelists array
  const selectedCodelist = codelists.value.find(
    (item) => item.codelist_uid === codelist
  )
  emit('updatecodelist', selectedCodelist)
  fetchTerms(codelist)
}

/**
 * Collect term UIDs that are selected but missing from the fetched items.
 */
function collectMissingUids(fetchedItems) {
  if (!model.value) return []
  if (typeof model.value === 'string') {
    if (model.value === ALL_TERMS_UID) return []
    const found = fetchedItems.some((item) => item.term_uid === model.value)
    return found ? [] : [model.value]
  }
  return model.value.filter(
    (uid) =>
      uid !== ALL_TERMS_UID &&
      !fetchedItems.some((item) => item.term_uid === uid)
  )
}

/**
 * Try to resolve full term data from the codelist endpoint first (handles
 * terms beyond page 50), then fall back to the /names endpoint.
 * The /names endpoint does not return submission_value (it is codelist-scoped),
 * so we use sponsor_preferred_name as a fallback for all display fields.
 *
 * Returns { item, inCodelist } where inCodelist indicates whether the term
 * was found in the codelist (just not on the current page).
 */
async function resolveTermDisplay(uid, codelistUid) {
  // 1. Try fetching the specific term from the codelist (handles pagination)
  try {
    const codelistResp = await codelistsApi.getCodelistTerms(codelistUid, {
      page_size: 1,
      filters: { term_uid: { v: [uid] } },
    })
    if (codelistResp.data.items.length > 0) {
      return { item: codelistResp.data.items[0], inCodelist: true }
    }
  } catch {
    // codelist lookup failed, continue to fallback
  }

  // 2. Fall back to the term names endpoint (term is not in this codelist)
  try {
    const termResp = await termsApi.getTermByUid(uid)
    const data = termResp.data
    const name = data.sponsor_preferred_name || uid
    return {
      item: {
        term_uid: uid,
        sponsor_preferred_name: name,
        submission_value: name,
        title: name,
      },
      inCodelist: false,
    }
  } catch {
    return {
      item: {
        term_uid: uid,
        sponsor_preferred_name: uid,
        submission_value: uid,
        title: uid,
      },
      inCodelist: false,
    }
  }
}

const fetchTerms = _debounce(function (codelistUid) {
  loading.value = true
  const params = {
    page_size: 50,
    sort_by: JSON.stringify({ sponsor_preferred_name: true }),
  }
  if (search.value) {
    params.filters = { '*': { v: [search.value] } }
  }
  codelistsApi.getCodelistTerms(codelistUid, params).then(async (resp) => {
    const fetchedItems = resp.data.items
    const missingUids = collectMissingUids(fetchedItems)
    const newInvalidUids = new Set()

    // Resolve display info for missing terms and prepend them to the list.
    // Only mark as invalid if the term is truly not in the codelist.
    for (const uid of missingUids) {
      const { item, inCodelist } = await resolveTermDisplay(uid, codelistUid)
      fetchedItems.unshift(item)
      if (!inCodelist) {
        newInvalidUids.add(uid)
      }
    }

    invalidTermUids.value = newInvalidUids
    allowedValues.value = fetchedItems
    loading.value = false
  })
}, 800)

const fetchTermsIfNeeded = async (value) => {
  if (!allowedValues.value || !value) return
  const uids = typeof value === 'string' ? [value] : value
  const missing = uids.filter(
    (uid) =>
      uid !== ALL_TERMS_UID &&
      !allowedValues.value.some((item) => item.term_uid === uid)
  )
  for (const uid of missing) {
    const { item } = await resolveTermDisplay(uid, codelist.value)
    allowedValues.value.unshift(item)
  }
}

const fetchCodelists = async () => {
  if (!props.dataDomain) {
    codelists.value = []
    return
  }
  loadingCodelists.value = true
  try {
    const params = {
      page_size: 0,
      ct_catalogue_name: 'SDTM CT',
    }
    if (props.activityItemClass.name === 'categoric_finding_original_result') {
      params.valid_codelists_for_item = true
    }
    const resp = await activityItemClassesApi.getDatasetCodelists(
      props.activityItemClass.uid,
      props.dataDomain,
      params
    )
    codelists.value = resp.data.items
    if (codelists.value.length === 1) {
      codelist.value = codelists.value[0].codelist_uid
      nextTick(() => {
        fetchTerms(codelist.value)
      })
    } else if (codelist.value) {
      // Codelist was pre-set (e.g., during edit mode) — fetch its terms
      nextTick(() => {
        fetchTerms(codelist.value)
      })
    }
  } finally {
    loadingCodelists.value = false
  }
}

const reset = () => {
  if (search.value && search.value !== '') {
    model.value = null
    allowedValues.value = []
    search.value = ''
  }
}

watch(model, () => {
  fetchTermsIfNeeded(model.value)
})
watch(search, () => {
  if (codelist.value) {
    fetchTerms(codelist.value)
  }
})
watch(codelist, () => {
  fetchTerms(codelist.value)
})
watch(
  () => props.activityItemClass,
  async (value) => {
    if (!value) {
      return
    }
    if (value.name !== 'unit_dimension') {
      await fetchCodelists()
    } else {
      const resp = await codelistsApi.getAll({
        filters: {
          'name.name': { v: ['Unit Dimension'] },
        },
      })
      fetchTerms(resp.data.items[0].codelist_uid)
      codelist.value = resp.data.items[0].codelist_uid
    }
  },
  { immediate: true }
)

watch(
  () => props.dataDomain,
  (newVal, oldVal) => {
    // Only reset codelist when actively changing between domains,
    // not when setting domain for the first time (from null)
    if (oldVal) {
      codelist.value = null
    }
    fetchCodelists()
  }
)

defineExpose({
  allowedValues,
  invalidTermUids,
  hasInvalidTerms,
  ALL_TERMS_UID,
})
</script>
