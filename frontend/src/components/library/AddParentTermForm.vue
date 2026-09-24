<template>
  <StepperForm
    ref="stepper"
    data-cy="form-body"
    :title="
      props.relationship === 'parent'
        ? $t('AddParentTermForm.title')
        : $t('AddChildTermForm.title')
    "
    :steps="steps"
    :form-observer-getter="getObserver"
    :help-items="
      props.relationship === 'parent' ? parentHelpItems : childHelpItems
    "
    :edit-data="form"
    @close="close"
    @save="submit"
  >
    <template #[`step.relationship_type`]>
      <v-row>
        <v-col>
          <v-radio-group v-model="relationshipType">
            <v-radio
              data-cy="parent-type"
              :label="$t('AddChildTermForm.type')"
              value="type"
            />
            <v-radio
              data-cy="parent-subtype"
              :label="$t('AddChildTermForm.subtype')"
              value="subtype"
            />
            <v-radio
              data-cy="specialization"
              :label="$t('AddChildTermForm.specialization')"
              value="specialization"
            />
            <v-radio
              data-cy="predecessor"
              :label="$t('AddChildTermForm.predecessor')"
              value="predecessor"
            />
          </v-radio-group>
        </v-col>
      </v-row>
    </template>
    <template #[`step.select`]>
      <v-row>
        <v-col>
          <NNTable
            table-id="add-parent-term-terms"
            :headers="termHeaders"
            :items="terms"
            :items-length="total"
            item-value="term_uid"
            class="mt-4"
            hide-export-button
            column-data-resource="ct/terms"
            :loading="loading"
            @filter="scheduleFilterTerms"
          >
            <template #[`item.selection`]="{ item }">
              <v-radio-group v-model="selectedTerm" hide-details>
                <v-radio :value="item.term_uid"></v-radio>
              </v-radio-group>
            </template>
          </NNTable>
        </v-col>
      </v-row>
    </template>
  </StepperForm>
</template>

<script setup>
import { inject, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import controlledTerminology from '@/api/controlledTerminology'
import termsApi from '@/api/controlledTerminology/terms'
import StepperForm from '@/components/tools/StepperForm.vue'
import NNTable from '@/components/tools/NNTable.vue'
import filteringParameters from '@/utils/filteringParameters'
import _debounce from 'lodash/debounce'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const props = defineProps({
  relationship: {
    type: String,
    default: 'parent',
  },
  termUid: {
    type: String,
    default: null,
  },
})
const emit = defineEmits(['close', 'created'])

const relationshipType = ref('type')
const form = ref({})
const childHelpItems = [
  'AddChildTermForm.type',
  'AddChildTermForm.subtype',
  'AddChildTermForm.specialization',
  'AddChildTermForm.predecessor',
]
const parentHelpItems = [
  'AddParentTermForm.type',
  'AddParentTermForm.subtype',
  'AddParentTermForm.specialization',
  'AddParentTermForm.predecessor',
]
const selectedTerm = ref(null)
const steps = ref(getInitialSteps())
const termHeaders = [
  { title: '', key: 'selection', sortable: false, noFilter: true, width: '8%' },
  {
    title: t('CodelistTermCreationForm.concept_id'),
    key: 'term_uid',
  },
  {
    title: t('CodelistTermCreationForm.sponsor_name'),
    key: 'name.sponsor_preferred_name',
  },
  {
    title: t('CodelistTermCreationForm.nci_pref_name'),
    key: 'attributes.nci_preferred_name',
  },
  { title: t('_global.definition'), key: 'attributes.definition' },
]
const terms = ref([])
const total = ref(0)
const loading = ref(false)
const stepper = ref()

onMounted(() => {
  termsApi.getAll({ page_size: 10, total_count: true }).then((resp) => {
    terms.value = resp.data.items
    total.value = resp.data.total
    selectedTerm.value = terms.value[0].term_uid
  })
})

function close() {
  emit('close')
  notificationHub.clearErrors()
  relationshipType.value = 'type'
  selectedTerm.value = null
  form.value = {}
  stepper.value.reset()
}
function getInitialSteps() {
  return [
    {
      name: 'relationship_type',
      title: t('AddChildTermForm.select_relationship'),
    },
    {
      name: 'select',
      title:
        props.relationship === 'parent'
          ? t('AddParentTermForm.select_term')
          : t('AddChildTermForm.select_term'),
    },
  ]
}
function getObserver() {
  return undefined
}

async function submit() {
  notificationHub.clearErrors()

  let firstUid, secondUid
  if (props.relationship === 'parent') {
    firstUid = props.termUid
    secondUid = selectedTerm.value
  } else {
    firstUid = selectedTerm.value
    secondUid = props.termUid
  }
  try {
    const resp = await controlledTerminology.addTermParent(
      firstUid,
      secondUid,
      relationshipType.value
    )
    notificationHub.add({
      msg: t('CodelistTermCreationForm.add_success'),
    })
    emit('created', resp.data)
    close()
  } finally {
    stepper.value.loading = false
  }
}

const scheduleFilterTerms = _debounce(function (
  filters,
  options,
  filtersUpdated
) {
  loading.value = true
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  termsApi.getAll(params).then((resp) => {
    terms.value = resp.data.items
    total.value = resp.data.total
    loading.value = false
  })
}, 300)
</script>
