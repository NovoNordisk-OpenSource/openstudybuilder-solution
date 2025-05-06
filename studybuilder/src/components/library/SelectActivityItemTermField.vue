<template>
  <v-select
    v-model="model"
    :label="props.label"
    :items="allowedValues"
    item-value="term_uid"
    bg-color="white"
    variant="outlined"
    density="compact"
    hide-details
    :loading="loading"
  >
    <template #prepend-item>
      <v-row @keydown.stop>
        <v-text-field
          v-model="search"
          class="pl-6"
          :placeholder="$t('_global.search')"
        />
        <v-btn
          variant="text"
          size="small"
          icon="mdi-close"
          class="mr-3 mt-3"
          @click="reset"
        />
      </v-row>
    </template>
  </v-select>
</template>

<script setup>
import { ref, watch } from 'vue'
import { i18n } from '@/plugins/i18n'
import activityItemClassesApi from '@/api/activityItemClasses'
import constants from '@/constants/activityItemClasses'
import _debounce from 'lodash/debounce'

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
})
const model = defineModel()
const search = defineModel('search')

const allowedValues = ref([])
const loading = ref(false)

const fetchTerms = _debounce(function () {
  loading.value = true
  const filters = { '*': { v: [search.value] } }
  activityItemClassesApi
    .getTerms(props.activityItemClass.uid, {
      filters,
      page_size: 50,
    })
    .then((resp) => {
      allowedValues.value = []
      const codelists =
        constants.codelistsPerDomain[props.dataDomain][
          props.activityItemClass.name
        ]
      if (codelists) {
        allowedValues.value = resp.data.items.filter((item) =>
          codelists.includes(item.codelist_submission_value)
        )
      } else {
        const present = resp.data.items.find(
          (item) => item.term_uid === model.value
        )
        if (!present) {
          model.value = null
        }
        allowedValues.value = resp.data.items
      }
      loading.value = false
    })
}, 800)

const reset = () => {
  model.value = null
  allowedValues.value = []
  search.value = ''
}

watch(search, () => {
  fetchTerms()
})
watch(
  () => props.activityItemClass,
  (value) => {
    if (value) {
      fetchTerms()
    }
  },
  { immediate: true }
)

defineExpose({
  allowedValues,
})
</script>
