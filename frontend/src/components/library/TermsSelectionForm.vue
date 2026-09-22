<template>
  <SimpleFormDialog
    ref="dialog"
    content-class="h-100"
    :title="props.title"
    :open="props.open"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <div class="mb-6">
        <v-text-field
          v-if="!props.pairedCodelistMode"
          v-model="codelistSearch"
          clearable
          clear-icon="mdi-close"
          prepend-inner-icon="mdi-magnify"
          :label="$t('TermsSelectionForm.search_for_codelists')"
          color="nnBaseBlue"
          hide-details
          @update:model-value="fetchCodelists"
        />
        <v-text-field
          v-else
          v-model="termSearch"
          clearable
          clear-icon="mdi-close"
          prepend-inner-icon="mdi-magnify"
          :label="$t('TermsSelectionForm.search_for_term')"
          color="nnBaseBlue"
          hide-details
          @update:model-value="fetchTerms"
        />
        <v-radio-group
          v-if="!props.pairedCodelistMode"
          v-model="searchMode"
          inline
          class="mt-2"
        >
          <v-radio
            value="name"
            :label="$t('TermsSelectionForm.search_by_codelist')"
          />
          <v-radio
            value="term"
            :label="$t('TermsSelectionForm.search_by_term')"
          />
        </v-radio-group>
        <div class="d-flex px-2">
          <template v-if="!props.pairedCodelistMode">
            <v-switch
              v-model="searchParams.only_ordinal_codelists"
              :label="$t('TermsSelectionForm.ordinal_codelists')"
              class="mr-4"
              hide-details
              @update:model-value="_fetchCodelists"
            />
            <v-switch
              v-model="searchParams.only_response_codelists"
              :label="$t('TermsSelectionForm.response_codelists')"
              class="mr-4"
              hide-details
              @update:model-value="_fetchCodelists"
            />
          </template>
          <v-switch
            v-if="!props.pairedCodelistMode"
            v-model="searchParams.match_whole_words"
            :label="$t('TermsSelectionForm.whole_word_match')"
            hide-details
          />
          <!-- <v-switch
               v-if="props.pairedCodelistMode"
               v-model="useFullTextSearch"
               :label="$t('TermsSelectionForm.semantic_search')"
               class="ml-4"
               hide-details
               /> -->
        </div>
      </div>
      <div>
        <NNTable
          v-if="!props.pairedCodelistMode"
          key="codelistsTable"
          ref="codelistsTable"
          table-id="terms-selection-codelists"
          :headers="codelistHeaders"
          :items="codelists"
          :items-length="totalCodelists"
          item-value="uid"
          :hide-default-switches="true"
          :hide-search-field="true"
          :hide-export-button="true"
          :disable-filtering="true"
          :modifiable-table="false"
          elevation="0"
          :loading="loadingCodelists"
          @filter="handleCodelistsFilter"
        >
          <template #beforeSearch>
            <div class="dialog-title">
              {{ $t('TermsSelectionForm.select_codelist') }}
            </div>
          </template>
          <template #[`item.select`]="{ item }">
            <v-radio-group v-model="selectedCodelistUid" hide-details>
              <v-radio :value="item.uid" />
            </v-radio-group>
          </template>
        </NNTable>
        <NNTable
          v-if="selectedCodelistUid || props.pairedCodelistMode"
          key="termsTable"
          ref="termsTable"
          class="mt-4"
          table-id="terms-selection-terms"
          :headers="termHeaders"
          :items="terms"
          :items-length="totalTerms"
          item-value="term_uid"
          :show-select="props.multiple"
          :hide-default-switches="true"
          :hide-search-field="true"
          :hide-export-button="true"
          :disable-filtering="true"
          :modifiable-table="false"
          elevation="0"
          :loading="loadingTerms"
          @filter="handleTermsFilter"
        >
          <template #beforeSearch>
            <div class="dialog-title">
              {{ $t('TermsSelectionForm.select_terms') }}
            </div>
          </template>
          <template v-if="!props.multiple" #[`item.select`]="{ item }">
            <v-radio-group v-model="selectedTerm" hide-details>
              <v-radio :value="item.term_uid" />
            </v-radio-group>
          </template>
        </NNTable>
      </div>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import _debounce from 'lodash/debounce'
import codelistApi from '@/api/controlledTerminology/codelists'
import pairedCodelistApi from '@/api/controlledTerminology/pairedCodelists'
import NNTable from '@/components/tools/NNTable.vue'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'

const props = defineProps({
  open: Boolean,
  title: {
    type: String,
    default: null,
  },
  pairedCodelistMode: {
    type: Boolean,
    default: false,
  },
  multiple: {
    type: Boolean,
    default: false,
  },
})
const emit = defineEmits(['close', 'selected'])

const codelist = defineModel('codelist', { type: String })
const termSelection = defineModel('termSelection', { type: [String, Array] })

const { t } = useI18n()

const codelistHeaders = [
  { title: '', key: 'select', sortable: false, width: '50px' },
  { title: t('TermsSelectionForm.library'), key: 'library_name' },
  {
    title: t('TermsSelectionForm.sponsor_name'),
    key: 'sponsor_preferred_name',
  },
  { title: t('TermsSelectionForm.submission_value'), key: 'submission_value' },
  { title: 'UID', key: 'uid' },
]
const termHeaders = computed(() => {
  const headers = props.pairedCodelistMode
    ? [
        { title: t('TermsSelectionForm.library'), key: 'library_name' },
        {
          title: t('TermsSelectionForm.name_submission_value'),
          key: 'name_submission_value',
        },
        {
          title: t('TermsSelectionForm.code_submission_value'),
          key: 'code_submission_value',
        },
        { title: t('TermsSelectionForm.concept_id'), key: 'concept_id' },
      ]
    : [
        { title: t('TermsSelectionForm.library'), key: 'library_name' },
        {
          title: t('TermsSelectionForm.sponsor_name'),
          key: 'sponsor_preferred_name',
        },
        {
          title: t('TermsSelectionForm.submission_value'),
          key: 'submission_value',
        },
        { title: t('TermsSelectionForm.concept_id'), key: 'concept_id' },
      ]
  if (!props.multiple) {
    headers.unshift({
      title: '',
      key: 'select',
      sortable: false,
      width: '50px',
    })
  }
  return headers
})

const codelists = ref([])
const codelistsTable = ref()
const dialog = ref()
const codelistPage = ref(1)
const codelistSearch = ref('')
const loadingCodelists = ref(false)
const loadingTerms = ref(false)
const searchMode = ref('name')
const searchParams = ref({
  only_response_codelists: true,
})
const selectedCodelistUid = ref(null)
const selectedTerm = ref(null)
const termPage = ref(1)
const termSearch = ref([])
const terms = ref([])
const termsTable = ref()
const totalCodelists = ref(0)
const totalTerms = ref(0)
// const useFullTextSearch = ref(true)

async function _fetchCodelists() {
  if (!codelistSearch.value || codelistSearch.value === '') {
    reset()
    return
  }
  loadingCodelists.value = true
  selectedCodelistUid.value = null
  selectedTerm.value = null
  if (termsTable.value) termsTable.value.selected = []
  try {
    const params = {
      ...searchParams.value,
      page_number: codelistPage.value,
      search_string: codelistSearch.value,
    }
    let resp
    if (searchMode.value === 'name') {
      resp = await codelistApi.search(params)
    } else {
      resp = await codelistApi.searchByTerm(params)
    }
    codelists.value = resp.data.items
    totalCodelists.value = resp.data.total
  } finally {
    loadingCodelists.value = false
  }
}
const fetchCodelists = _debounce(_fetchCodelists, 300)

async function _fetchTerms() {
  loadingTerms.value = true
  try {
    const params = {
      page_number: termPage.value,
      total_count: true,
    }
    if (termSearch.value && termSearch.value.length) {
      params.filters = { '*': { v: [termSearch.value] } }
    }
    let resp
    if (props.pairedCodelistMode) {
      resp = await pairedCodelistApi.getCodelistTerms(codelist.value, params)
    } else {
      resp = await codelistApi.getCodelistTerms(
        selectedCodelistUid.value,
        params
      )
    }
    terms.value = resp.data.items
    totalTerms.value = resp.data.total
  } finally {
    loadingTerms.value = false
  }
}

const fetchTerms = _debounce(_fetchTerms, 300)

function handleCodelistsFilter(filters, options) {
  codelistPage.value = options.page
  _fetchCodelists()
}

function handleTermsFilter(filters, options) {
  termPage.value = options.page
  _fetchTerms()
}

function reset() {
  codelists.value = []
  totalCodelists.value = 0
  codelistPage.value = 1
  terms.value = []
  totalTerms.value = 0
  termPage.value = 1
  if (termsTable.value) termsTable.value.selected = []
  selectedTerm.value = null
  selectedCodelistUid.value = null
  codelistSearch.value = ''
  termSearch.value = []
}

function close() {
  reset()
  emit('close')
}

function submit() {
  if (!props.pairedCodelistMode) {
    codelist.value = selectedCodelistUid.value
  }
  if (props.multiple) {
    const selected = termsTable.value?.selected || []
    termSelection.value = selected.map((item) => item.term_uid)
  } else {
    termSelection.value = selectedTerm.value
  }
  emit('selected')
  close()
}

watch(selectedCodelistUid, () => {
  if (selectedCodelistUid.value) {
    _fetchTerms()
  }
})
</script>

<style lang="scss" scoped>
.codelist {
  cursor: pointer;
}
</style>
