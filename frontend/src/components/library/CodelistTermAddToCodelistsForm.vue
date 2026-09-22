<template>
  <StepperForm
    ref="stepper"
    data-cy="form-body"
    :title="
      $t('CodelistTermAddToCodelistsForm.title', {
        term: escapeHTMLHandler(props.termName),
      })
    "
    :steps="steps"
    :form-observer-getter="getObserver"
    :help-items="helpItems"
    :edit-data="form"
    @close="close"
    @save="submit"
  >
    <template #[`step.select`]>
      <v-row>
        <v-col>
          <NNTable
            v-model="selection"
            table-id="codelist-term-add-to-codelists"
            :headers="codelistHeaders"
            :items="codelists"
            :items-length="total"
            item-value="codelist_uid"
            class="mt-4"
            hide-export-button
            column-data-resource="ct/codelists"
            :loading="loading"
            show-select
            @filter="scheduleFilterCodelists"
            @update:model-value="selectCodelists"
          />
        </v-col>
      </v-row>
    </template>
    <template #[`step.order_and_submval`]>
      <v-form ref="orderAndSubmvalForm">
        <v-row v-for="(cl, index) in selection" :key="`item-${index}`">
          <v-col>
            {{ cl.attributes.submission_value }}
          </v-col>
          <v-col>
            {{ cl.name.name }}
          </v-col>
          <v-col>
            <v-combobox
              v-model="form[index].submission_value"
              :items="props.submissionValues"
              data-cy="term-sponsor-preferred-name"
              :label="$t('_global.submission_value')"
              :rules="[formRules.required]"
              clearable
            />
          </v-col>
          <v-col>
            <v-text-field
              v-model="form[index].order"
              data-cy="term-order"
              :label="$t('_global.order')"
              :rules="[formRules.required]"
              clearable
            />
          </v-col>
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
import { escapeHTML } from '@/utils/sanitize'
import _debounce from 'lodash/debounce'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const formRules = inject('formRules')
const props = defineProps({
  termUid: {
    type: String,
    default: null,
  },
  termName: {
    type: String,
    default: null,
  },
  submissionValues: {
    type: Array,
    default: () => [],
  },
})
const emit = defineEmits(['close', 'created'])

const form = ref([])
const helpItems = [
  'CodelistTermCreationForm.submission_value',
  'CodelistTermCreationForm.order',
]
const selection = ref([])
const steps = ref(getInitialSteps())
const codelistHeaders = [
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
const orderAndSubmvalForm = ref()

onMounted(() => {
  codelistsApi.getAll({ page_size: 10, total_count: true }).then((resp) => {
    codelists.value = resp.data.items
    total.value = resp.data.total
  })
})

function close() {
  emit('close')
  notificationHub.clearErrors()
  form.value = {}
  stepper.value.reset()
}
function getInitialSteps() {
  return [
    {
      name: 'select',
      title: t('CodelistTermAddToCodelistsForm.select_codelists_label'),
    },
    {
      name: 'order_and_submval',
      title: t('CodelistTermAddToCodelistsForm.order_and_submval_label'),
    },
  ]
}
function getObserver(step) {
  if (step === 2) {
    return orderAndSubmvalForm.value
  }
  return undefined
}
async function submit() {
  notificationHub.clearErrors()

  // TODO this should be a single api call
  for (const item of form.value) {
    const data = {
      term_uid: props.termUid,
      order: item.order,
      submission_value: item.submission_value,
    }
    await controlledTerminology.addTermToCodelist(item.codelist_uid, data)
  }
  notificationHub.add({
    msg: t('CodelistTermAddToCodelistsForm.add_success'),
  })
  close()
}

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

function selectCodelists() {
  form.value = selection.value.map((cl) => ({
    codelist_uid: cl.codelist_uid,
    submission_value: props.submissionValues[0],
    order: null,
  }))
}

function escapeHTMLHandler(html) {
  return escapeHTML(html)
}
</script>
