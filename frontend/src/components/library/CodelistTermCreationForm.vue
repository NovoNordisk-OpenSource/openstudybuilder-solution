<template>
  <StepperForm
    ref="stepper"
    data-cy="form-body"
    :title="
      $t('CodelistTermCreationForm.title', {
        codelist: escapeHTMLHandler(props.codelistName),
      })
    "
    :steps="steps"
    :form-observer-getter="getObserver"
    :help-items="helpItems"
    :edit-data="form"
    @close="close"
    @save="submit"
  >
    <template #[`step.creation_mode`]>
      <v-row>
        <v-col>
          <v-radio-group v-model="createNewTerm">
            <v-radio
              data-cy="select-exitsing-term"
              :label="$t('CodelistTermCreationForm.select_mode')"
              :value="false"
            />
            <v-radio
              data-cy="create-new-term"
              :label="$t('CodelistTermCreationForm.create_mode')"
              :value="true"
            />
          </v-radio-group>
        </v-col>
      </v-row>
    </template>
    <template #[`step.select`]>
      <v-row>
        <v-col>
          <NNTable
            v-model="selection"
            table-id="codelist-term-creation-terms"
            :headers="termHeaders"
            :items="terms"
            :items-length="total"
            :items-per-page-options="itemsPerPage"
            item-value="term_uid"
            class="mt-4"
            hide-export-button
            column-data-resource="ct/terms"
            :loading="loading"
            show-select
            :codelist-uid="null"
            @filter="scheduleFilterTerms"
            @update:model-value="selectTerms"
          >
            <template #[`item.codelists.submission_value`]="{ item }">
              <div v-html="submissionValuesDisplay(item)" />
            </template>
          </NNTable>
        </v-col>
      </v-row>
    </template>
    <template #[`step.names`]>
      <v-form ref="namesForm">
        <v-row v-if="showLibraryDropdown">
          <v-col>
            <VSelect
              v-model="selectedLibraryName"
              data-cy="library-dropdown"
              :label="$t('CodelistTermCreationForm.library')"
              :items="editableLibraries"
              item-title="name"
              item-value="name"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.sponsor_preferred_name"
              data-cy="term-sponsor-preferred-name"
              :label="$t('CodelistTermCreationForm.sponsor_pref_name')"
              :rules="[formRules.required]"
              clearable
              @update:model-value="setSentenceCase"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.sponsor_preferred_name_sentence_case"
              data-cy="term-sentence-case-name"
              :label="$t('CodelistTermCreationForm.sponsor_sentence_case_name')"
              :rules="[
                formRules.required,
                (value) => formRules.sameAs(value, form.sponsor_preferred_name),
              ]"
              clearable
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #[`step.attributes`]>
      <v-form ref="attributesForm">
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.concept_id"
              data-cy="term-concept-id"
              :label="$t('CodelistTermCreationForm.concept_id')"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.nci_preferred_name"
              data-cy="term-nci-preffered-name"
              :label="$t('CodelistTermCreationForm.nci_pref_name')"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-textarea
              v-model="form.definition"
              data-cy="term-definition"
              :label="$t('CodelistTermCreationForm.definition')"
              :rules="[formRules.required]"
              clearable
              auto-grow
              rows="1"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #[`step.order_and_submval_new`]>
      <v-form ref="orderAndSubmvalFormNew">
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.submission_value"
              data-cy="term-name"
              :label="$t('CodelistTermCreationForm.submission_value')"
              :rules="[formRules.required]"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.order"
              data-cy="term-order"
              :label="$t('CodelistTermCreationForm.order')"
              :rules="[formRules.required]"
              clearable
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #[`step.order_and_submval`]>
      <v-form ref="orderAndSubmvalForm">
        <v-row v-for="(term, index) in selection" :key="`item-${index}`">
          <v-col>
            {{ term.name.sponsor_preferred_name }}
          </v-col>
          <v-col>
            {{ term.attributes.concept_id }}
          </v-col>
          <v-col>
            <component
              :is="getSubmissionValueComponent(term)"
              v-model="form[index].submission_value"
              :items="
                Array.from(
                  new Set(
                    term.codelists.map((codelist) => codelist.submission_value)
                  )
                )
              "
              data-cy="term-sponsor-preferred-name"
              :label="$t('_global.submission_value')"
              :rules="[formRules.required]"
              density="compact"
              clearable
              variant="outlined"
              rounded="lg"
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
import { inject, onMounted, ref, watch } from 'vue'
import { VCombobox, VSelect } from 'vuetify/components'
import { useI18n } from 'vue-i18n'
import constants from '@/constants/libraries.js'
import controlledTerminology from '@/api/controlledTerminology'
import termsApi from '@/api/controlledTerminology/terms'
import { useEditableLibraries } from '@/composables/editableLibraries'
import StepperForm from '@/components/tools/StepperForm.vue'
import NNTable from '@/components/tools/NNTable.vue'
import filteringParameters from '@/utils/filteringParameters'
import { escapeHTML } from '@/utils/sanitize'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const formRules = inject('formRules')
const props = defineProps({
  catalogueNames: {
    type: Array[String],
    default: [],
  },
  codelistUid: {
    type: String,
    default: null,
  },
  codelistName: {
    type: String,
    default: null,
  },
  // The parent codelist's library, used to pre-select the Library dropdown
  // in the "names" step instead of always defaulting to Sponsor.
  defaultLibraryName: {
    type: String,
    default: null,
  },
})
const emit = defineEmits(['close', 'created'])

const itemsPerPage = [
  {
    value: 5,
    title: '5',
  },
  {
    value: 10,
    title: '10',
  },
  {
    value: 15,
    title: '15',
  },
  {
    value: 25,
    title: '25',
  },
  {
    value: 50,
    title: '50',
  },
  {
    value: 100,
    title: '100',
  },
]
const createNewTerm = ref(false)
const form = ref([])
function resolveDefaultLibraryName() {
  return props.defaultLibraryName || constants.LIBRARY_SPONSOR
}
const selectedLibraryName = ref(resolveDefaultLibraryName())
const { libraries: editableLibraries, showDropdown: showLibraryDropdown } =
  useEditableLibraries()
const alternateSteps = [
  {
    name: 'creation_mode',
    title: t('CodelistTermCreationForm.creation_mode_label'),
  },
  {
    name: 'names',
    title: t('CodelistTermCreationForm.create_sponsor_name'),
  },
  {
    name: 'attributes',
    title: t('CodelistTermCreationForm.create_term_attributes'),
  },
  {
    name: 'order_and_submval_new',
    title: t('CodelistTermCreationForm.order_and_submval_label'),
  },
]
const helpItems = [
  'CodelistTermCreationForm.sponsor_pref_name',
  'CodelistTermCreationForm.sponsor_sentence_case_name',
  'CodelistTermCreationForm.concept_id',
  'CodelistTermCreationForm.nci_pref_name',
  'CodelistTermCreationForm.definition',
  'CodelistTermCreationForm.submission_value',
  'CodelistTermCreationForm.order',
]
const selection = ref([])
const steps = ref(getInitialSteps())
const termHeaders = [
  {
    title: t('CodelistTermCreationForm.concept_id'),
    key: 'attributes.concept_id',
  },
  {
    title: t('CodelistTermCreationForm.submission_value'),
    key: 'codelists.submission_value',
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
let timer = null
const total = ref(0)
const loading = ref(false)
const stepper = ref()
const namesForm = ref()
const attributesForm = ref()
const orderAndSubmvalForm = ref()
const pairedCodelist = ref(null)

watch(createNewTerm, (value) => {
  steps.value = value ? alternateSteps : getInitialSteps()
})

onMounted(() => {
  controlledTerminology.getPairedCodelists(props.codelistUid).then((resp) => {
    pairedCodelist.value = resp.data
  })
})

function close() {
  emit('close')
  notificationHub.clearErrors()
  createNewTerm.value = true
  form.value = {}
  selectedLibraryName.value = resolveDefaultLibraryName()
  stepper.value.reset()
}
function getInitialSteps() {
  return [
    {
      name: 'creation_mode',
      title: t('CodelistTermCreationForm.creation_mode_label'),
    },
    {
      name: 'select',
      title: t('CodelistTermCreationForm.select_term_label'),
    },
    {
      name: 'order_and_submval',
      title: t('CodelistTermCreationForm.order_and_submval_label'),
    },
  ]
}

function getSubmissionValueComponent(term) {
  if (term.library_name === constants.LIBRARY_SPONSOR && pairedCodelist.value) {
    return VCombobox
  }
  return VSelect
}

function getObserver(step) {
  if (step === 2) {
    return namesForm.value
  }
  if (step === 3) {
    return attributesForm.value
  }
  if (step === 4) {
    return orderAndSubmvalForm.value
  }
  return undefined
}
async function submit() {
  notificationHub.clearErrors()

  if (createNewTerm.value) {
    const data = {
      catalogue_names: props.catalogueNames,
      library_name: selectedLibraryName.value,
      nci_preferred_name: form.value.nci_preferred_name,
      definition: form.value.definition,
      sponsor_preferred_name: form.value.sponsor_preferred_name,
      sponsor_preferred_name_sentence_case:
        form.value.sponsor_preferred_name_sentence_case,
      concept_id: form.value.concept_id,
      codelists: [
        {
          codelist_uid: props.codelistUid,
          submission_value: form.value.submission_value,
          order: form.value.order,
        },
      ],
    }
    try {
      const resp = await controlledTerminology.createCodelistTerm(data)
      notificationHub.add({
        msg: t('CodelistTermCreationForm.add_success'),
      })
      emit('created', resp.data)
      close()
    } finally {
      stepper.value.loading = false
    }
  } else {
    if (!form.value.length) {
      notificationHub.add({
        msg: t('CodelistTermCreationForm.no_selection'),
        type: 'error',
      })
      return
    }
    const codelistUid = props.codelistUid
    // TODO this should be a single api call
    for (const term of form.value) {
      await controlledTerminology.addTermToCodelist(codelistUid, term)
    }
    notificationHub.add({
      msg: t('CodelistTermCreationForm.add_success'),
    })
    close()
  }
}
function setSentenceCase(value) {
  if (value) {
    form.value.sponsor_preferred_name_sentence_case = value.toLowerCase()
  }
}
function filterTerms(filters, options, filtersUpdated) {
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
}
/*
 ** Avoid sending too many request to the API
 */
function scheduleFilterTerms(filters, options, filtersUpdated) {
  loading.value = true
  if (timer) {
    clearTimeout(timer)
    timer = null
  }
  timer = setTimeout(filterTerms(filters, options, filtersUpdated), 300)
}
function selectTerms() {
  form.value = selection.value.map((term) => ({
    term_uid: term.term_uid,
    submission_value:
      term.codelists.length > 0 ? term.codelists[0].submission_value : null,
    order: null,
  }))
}
function escapeHTMLHandler(html) {
  return escapeHTML(html)
}
function submissionValuesDisplay(item) {
  let display = ''
  let values = new Set(
    item.codelists.map((codelist) => codelist.submission_value)
  )
  values.forEach((element) => {
    display += '&#9679; ' + element + '</br>'
  })
  return display
}
</script>
