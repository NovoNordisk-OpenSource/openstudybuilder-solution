<template>
  <v-select
    v-model="model"
    :items="terms"
    item-value="term_uid"
    bg-color="white"
    hide-details
    :loading="loading"
  >
    <template #menu-header>
      <SelectMenuSearch
        v-model="search"
        :placeholder="$t('_global.search')"
        @update:model-value="fetchTerms()"
        @clear="reset"
      />
    </template>
  </v-select>
</template>

<script setup>
import { ref, watch } from 'vue'
import _debounce from 'lodash/debounce'
import termsApi from '@/api/controlledTerminology/terms'
import SelectMenuSearch from '@/components/tools/SelectMenuSearch.vue'

const props = defineProps({
  codelist: {
    type: String,
    default: null,
  },
})
const model = defineModel({ type: String })

const loading = ref(false)
const search = ref('')
const terms = ref([])

watch(
  () => props.codelist,
  () => {
    search.value = ''
    fetchTerms()
  }
)

const fetchTerms = _debounce(function () {
  if (!props.codelist) {
    terms.value = []
    loading.value = false
    return
  }
  loading.value = true
  const params = {
    page_size: 50,
    sort_by: JSON.stringify({ sponsor_preferred_name: true }),
  }
  if (search.value) {
    params.filters = { '*': { v: [search.value] } }
  }
  termsApi.getTermsByCodelist(props.codelist, params).then((resp) => {
    terms.value = []
    const present = resp.data.items.find(
      (item) => item.term_uid === model.value
    )
    if (model.value && !present) {
      model.value = null
    }
    terms.value = resp.data.items
    loading.value = false
  })
}, 800)

const reset = () => {
  if (search.value && search.value !== '') {
    model.value = null
    terms.value = []
    search.value = ''
  }
}

watch(
  () => props.codelist,
  (value) => {
    if (value) {
      fetchTerms()
    }
  }
)

if (props.codelist) {
  fetchTerms()
}
</script>
