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
          v-model="codelistSearch"
          clearable
          clear-icon="mdi-close"
          prepend-inner-icon="mdi-magnify"
          :label="$t('TermsSelectionForm.search_for_codelists')"
          color="nnBaseBlue"
          hide-details
          data-cy="nsv-codelist-search-field"
          @update:model-value="fetchCodelists"
        />
        <v-radio-group v-model="searchMode" inline class="mt-2">
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
          <v-switch
            v-model="searchParams.only_ordinal_codelists"
            :label="$t('TermsSelectionForm.ordinal_codelists')"
            :disabled="!hasSearchQuery"
            class="mr-4"
            hide-details
            @update:model-value="_fetchCodelists"
          />
          <v-switch
            v-model="searchParams.only_response_codelists"
            :label="$t('TermsSelectionForm.response_codelists')"
            :disabled="!hasSearchQuery"
            class="mr-4"
            hide-details
            @update:model-value="_fetchCodelists"
          />
          <v-switch
            v-model="searchParams.match_whole_words"
            :label="$t('TermsSelectionForm.whole_word_match')"
            :disabled="!hasSearchQuery"
            hide-details
            @update:model-value="_fetchCodelists"
          />
        </div>
      </div>
      <div>
        <NNTable
          key="codelistsTable"
          ref="codelistsTable"
          table-id="nsv-codelist-selection"
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
          data-cy="nsv-codelist-table"
          @filter="handleCodelistsFilter"
        >
          <template #[`item.select`]="{ item }">
            <div
              class="d-flex justify-center"
              :data-cy="`nsv-codelist-row-${item.uid}`"
              @click.stop="selectCodelist(item)"
            >
              <v-radio
                :model-value="selectedCodelistUid"
                :value="item.uid"
                hide-details
                @update:model-value="selectCodelist(item)"
              />
            </div>
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
import NNTable from '@/components/tools/NNTable.vue'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'

const props = defineProps({
  open: Boolean,
  title: {
    type: String,
    default: null,
  },
})
const emit = defineEmits(['close', 'selected'])

const codelist = defineModel('codelist', { type: Object, default: null })

const { t } = useI18n()

const codelistHeaders = computed(() => [
  {
    title: '',
    key: 'select',
    sortable: false,
    width: '50px',
  },
  { title: t('TermsSelectionForm.library'), key: 'library_name' },
  {
    title: t('TermsSelectionForm.sponsor_name'),
    key: 'sponsor_preferred_name',
  },
  {
    title: t('TermsSelectionForm.submission_value'),
    key: 'submission_value',
  },
  { title: 'UID', key: 'uid' },
])

const codelists = ref([])
const codelistsTable = ref()
const dialog = ref()
const codelistPage = ref(1)
const codelistSearch = ref('')
const loadingCodelists = ref(false)
const searchMode = ref('name')
const searchParams = ref({
  only_ordinal_codelists: false,
  only_response_codelists: false,
})
const selectedCodelistUid = ref(null)
const selectedCodelist = ref(null)
const totalCodelists = ref(0)
const hasSearchQuery = computed(() => !!(codelistSearch.value || '').trim())

function toPickerCodelist(item) {
  if (!item) return null
  const uid = item.uid || item.codelist_uid || null
  return {
    ...item,
    uid,
    library_name: item.library_name,
    sponsor_preferred_name:
      item.sponsor_preferred_name ||
      item.name?.sponsor_preferred_name ||
      item.name?.name ||
      '',
    submission_value:
      item.submission_value || item.attributes?.submission_value || '',
  }
}

async function _fetchCodelists() {
  loadingCodelists.value = true
  try {
    const params = {
      ...searchParams.value,
      page_number: codelistPage.value,
    }
    const query = (codelistSearch.value || '').trim()
    let resp
    if (query) {
      params.search_string = query
      if (searchMode.value === 'name') {
        resp = await codelistApi.search(params)
      } else {
        resp = await codelistApi.searchByTerm(params)
      }
    } else {
      params.total_count = true
      resp = await codelistApi.getAll(params)
    }
    codelists.value = (resp.data.items || [])
      .map(toPickerCodelist)
      .filter((item) => item?.uid)
    totalCodelists.value = resp.data.total ?? codelists.value.length
  } finally {
    loadingCodelists.value = false
  }
}
const fetchCodelists = _debounce(_fetchCodelists, 300)

function handleCodelistsFilter(_filters, options) {
  codelistPage.value = options.page
  _fetchCodelists()
}

function selectCodelist(item) {
  selectedCodelistUid.value = item.uid
  selectedCodelist.value = item
}

function reset() {
  codelists.value = []
  totalCodelists.value = 0
  codelistPage.value = 1
  selectedCodelistUid.value = null
  selectedCodelist.value = null
  codelistSearch.value = ''
  if (codelistsTable.value) codelistsTable.value.selected = []
}

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      selectedCodelistUid.value =
        codelist.value?.uid || codelist.value?.codelist_uid || null
      selectedCodelist.value = codelist.value
      _fetchCodelists()
    } else {
      reset()
    }
  }
)

function close() {
  reset()
  emit('close')
}

function submit() {
  codelist.value = selectedCodelist.value
  emit('selected')
  close()
}
</script>
