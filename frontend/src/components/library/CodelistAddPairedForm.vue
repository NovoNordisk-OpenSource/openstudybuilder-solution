<template>
  <StepperForm
    ref="stepper"
    data-cy="form-body"
    :title="$t('CodelistAddPairedForm.title')"
    :steps="steps"
    :form-observer-getter="getObserver"
    :help-items="helpItems"
    @close="close"
    @save="submit"
  >
    <template #[`step.select_codelist`]>
      <v-row>
        <v-col>
          <NNTable
            table-id="codelist-add-paired-codelists"
            :headers="codelistHeaders"
            :items="codelists"
            :items-length="total"
            item-value="codelist_uid"
            class="mt-4"
            hide-export-button
            column-data-resource="ct/codelists"
            :loading="loading"
            hide-default-switches
            @filter="scheduleFilterCodelists"
          >
            <template #[`item.selection`]="{ item }">
              <v-radio-group v-model="selectedCodelist" hide-details>
                <v-radio :value="item.codelist_uid"></v-radio>
              </v-radio-group>
            </template>
          </NNTable>
        </v-col>
      </v-row>
    </template>
    <template #[`step.select_pair_type`]>
      <v-form ref="pairTypeForm">
        <v-row class="mb-4">
          <v-radio-group v-model="pairType">
            <v-radio
              data-cy="select-paired-names"
              :label="$t('CodelistAddPairedForm.pair_type_names')"
              :value="'names'"
            />
            <v-radio
              data-cy="select-paired-codes"
              :label="$t('CodelistAddPairedForm.pair_type_codes')"
              :value="'codes'"
            />
          </v-radio-group>
        </v-row>
      </v-form>
    </template>
  </StepperForm>
</template>

<script setup>
import { inject, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import controlledTerminology from '@/api/controlledTerminology'
import codelistsApi from '@/api/controlledTerminology/codelists'
import StepperForm from '@/components/tools/StepperForm.vue'
import NNTable from '@/components/tools/NNTable.vue'
import filteringParameters from '@/utils/filteringParameters'
import _debounce from 'lodash/debounce'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const props = defineProps({
  codelistUid: {
    type: String,
    default: null,
  },
})
const emit = defineEmits(['close', 'created'])

const pairType = ref('names')
const selectedCodelist = ref(null)
const helpItems = [
  'CodelistAddPairedForm.pair_type_names',
  'CodelistAddPairedForm.pair_type_codes',
]
const steps = ref(getInitialSteps())
const codelistHeaders = [
  { title: '', key: 'selection', sortable: false, noFilter: true },
  {
    title: t('CodelistTermAddToCodelistsForm.concept_id'),
    key: 'codelist_uid',
  },
  {
    title: t('CodelistTermAddToCodelistsForm.sponsor_name'),
    key: 'name.name',
  },
  {
    title: t('_global.submission_value'),
    key: 'attributes.submission_value',
  },
  { title: t('_global.definition'), key: 'attributes.definition' },
]
const codelists = ref([])
const total = ref(0)
const loading = ref(false)
const stepper = ref()

onMounted(() => {
  codelistsApi.getAll({ page_size: 10, total_count: true }).then((resp) => {
    codelists.value = resp.data.items
    total.value = resp.data.total
  })
})

function close() {
  emit('close')
  notificationHub.clearErrors()
  stepper.value.reset()
}
function getInitialSteps() {
  return [
    {
      name: 'select_codelist',
      title: t('CodelistAddPairedForm.select_codelist'),
    },
    {
      name: 'select_pair_type',
      title: t('CodelistAddPairedForm.select_pair_type'),
    },
  ]
}
function getObserver() {
  return undefined
}
async function submit() {
  notificationHub.clearErrors()

  const data = {}
  data[`paired_${pairType.value}_codelist_uid`] = selectedCodelist.value
  await controlledTerminology.updatePairedCodelists(props.codelistUid, data)
  notificationHub.add({
    msg: t('CodelistAddPairedForm.add_success'),
  })
  close()
}

/*
 ** Avoid sending too many request to the API
 */
const scheduleFilterCodelists = _debounce(function (
  filters,
  options,
  filtersUpdated
) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  codelistsApi.getAll(params).then((resp) => {
    codelists.value = resp.data.items
    total.value = resp.data.total
    loading.value = false
  })
}, 300)
</script>
