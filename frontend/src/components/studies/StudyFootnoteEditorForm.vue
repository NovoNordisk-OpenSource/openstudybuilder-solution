<template>
  <div>
    <div class="d-flex align-center pa-2">
      <v-btn
        icon="mdi-arrow-left"
        color="secondary"
        data-cy="footnote-editor-back"
        size="small"
        variant="text"
        :disabled="submitting"
        @click="handleBack"
      />
      <span class="font-weight-medium ml-1">
        {{
          $t(
            isEdit
              ? 'ProtocolFlowchart.edit_footnote'
              : 'ProtocolFlowchart.create_from_scratch'
          )
        }}
      </span>
    </div>
    <v-divider />
    <v-progress-linear v-if="loading" indeterminate />
    <div v-else class="pa-4">
      <NNTemplateInputField
        v-model="templateHtml"
        data-cy="footnote-text"
        :label="$t('ProtocolFlowchart.footnote_text_placeholder')"
        :items="parameterTypes"
        hide-details
      />
      <v-expand-transition>
        <ParameterValueSelector
          v-if="parameters.length"
          :model-value="parameters"
          :template="templateHtml"
          data-cy="footnote-parameter-selector"
          preview-text=" "
          stacked
          :with-unformatted-version="false"
        />
      </v-expand-transition>
    </div>
    <v-divider />
    <div class="d-flex justify-end ga-2 pa-3">
      <v-btn
        variant="outlined"
        :disabled="submitting"
        data-cy="cancel-footnote"
        @click="handleBack"
      >
        {{ $t('_global.cancel') }}
      </v-btn>
      <v-btn
        color="secondary"
        variant="flat"
        data-cy="submit-footnote"
        :disabled="!canSubmit"
        :loading="submitting"
        @click="submit"
      >
        {{ $t(isEdit ? '_global.save' : '_global.add') }}
      </v-btn>
    </div>
    <ConfirmDialog ref="confirm" />
  </div>
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useFootnotesStore } from '@/stores/studies-footnotes'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import footnotes from '@/api/footnotes'
import footnoteTemplates from '@/api/footnoteTemplates'
import study from '@/api/study'
import templateParameterTypes from '@/api/templateParameterTypes'
import footnoteConstants from '@/constants/footnotes'
import libraryConstants from '@/constants/libraries'
import statuses from '@/constants/statuses'
import instances from '@/utils/instances'
import { getSoaFootnoteType } from '@/utils/soaFootnotes'
import templateParameters from '@/utils/templateParameters'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import NNTemplateInputField from '@/components/tools/NNTemplateInputField.vue'
import ParameterValueSelector from '@/components/tools/ParameterValueSelector.vue'

const props = defineProps({
  studyFootnote: {
    type: Object,
    default: null,
  },
  // Items a newly created footnote is assigned to, in the layout given by `layout`.
  referencedItems: {
    type: Array,
    default: () => [],
  },
  layout: {
    type: String,
    default: null,
  },
})
const emit = defineEmits(['cancel', 'created', 'updated'])

const footnotesStore = useFootnotesStore()
const studiesGeneralStore = useStudiesGeneralStore()
const { t } = useI18n()
const notificationHub = inject('notificationHub')

const isEdit = computed(() => Boolean(props.studyFootnote))
const confirm = ref()
const loading = ref(isEdit.value)
const templateHtml = ref('')
const parameters = ref([])
const parameterTypes = ref([])
const submitting = ref(false)
const original = ref(null)
let createdTemplate = null

const parameterTypesLoaded = templateParameterTypes.getTypes().then((resp) => {
  parameterTypes.value = resp.data
})

const parameterTypeNames = computed(() =>
  parameterTypes.value.map((type) => type.name)
)
const parameterNames = computed(() =>
  templateParameters.getTemplateParametersFromTemplate(
    templateHtml.value,
    parameterTypeNames.value
  )
)
const isTextEmpty = computed(() => {
  const container = document.createElement('div')
  container.innerHTML = templateHtml.value || ''
  const plainText = (container.textContent || '').replace(/\u00A0|\s/g, '')
  return !plainText
})
const hasChanges = computed(
  () =>
    !isEdit.value ||
    (original.value !== null &&
      (cleanName(templateHtml.value) !== cleanName(original.value.text) ||
        snapshotValues(parameters.value) !== original.value.values))
)
const canSubmit = computed(
  () =>
    !loading.value &&
    hasChanges.value &&
    !isTextEmpty.value &&
    parameters.value.length === parameterNames.value.length &&
    parameters.value.every(
      (parameter, index) =>
        parameter.name === parameterNames.value[index] && isFilled(parameter)
    )
)

// Quill wraps the text in a paragraph the stored template name does not have.
function cleanName(value) {
  return value.replace(/^<p>/, '').replace(/<\/p>$/, '')
}

function snapshotValues(list) {
  return JSON.stringify(
    list.map(({ name, skip, selectedSeparator, selectedValues }) => ({
      name,
      skip: Boolean(skip),
      selectedSeparator: selectedSeparator ?? '',
      selectedValues: Array.isArray(selectedValues)
        ? selectedValues.map((value) => value.uid)
        : (selectedValues ?? ''),
    }))
  )
}

function isFilled({ skip, selectedValues: values, selectedSeparator }) {
  if (skip) {
    return true
  }
  if (Array.isArray(values)) {
    return values.length === 1 || (values.length > 1 && !!selectedSeparator)
  }
  return String(values ?? '').trim() !== ''
}

async function fetchParameterTerms(name) {
  const resp = await templateParameterTypes.getTerms(name)
  return resp.data.filter((term) => term.name?.trim())
}

async function loadFootnote() {
  try {
    const resp = await study.getStudyFootnote(
      studiesGeneralStore.selectedStudy.uid,
      props.studyFootnote.uid
    )
    const { footnote, template: studyTemplate } = resp.data
    const template = footnote
      ? { uid: footnote.template_uid, name: footnote.template_name }
      : { uid: studyTemplate.uid, name: studyTemplate.name }
    await parameterTypesLoaded
    const loaded = await Promise.all(
      templateParameters
        .getTemplateParametersFromTemplate(
          template.name,
          parameterTypeNames.value
        )
        .map(async (name) => ({ name, terms: await fetchParameterTerms(name) }))
    )
    if (footnote) {
      const { data } = await footnotes.getObject(footnote.uid)
      if (data.parameter_terms?.length === loaded.length) {
        instances.loadParameterValues(data.parameter_terms, loaded)
      }
    }
    parameters.value = loaded
    templateHtml.value = template.name
    original.value = {
      template,
      text: template.name,
      values: snapshotValues(loaded),
    }
    loading.value = false
  } catch {
    emit('cancel')
  }
}

onMounted(() => {
  if (isEdit.value) {
    loadFootnote()
  }
})

// The selector does not emit when a term is picked, so this component owns the
// item list and hands it down one-way; the selector mutates the items in place.
watch(
  () => JSON.stringify(parameterNames.value),
  async (_, __, onCleanup) => {
    let stale = false
    onCleanup(() => {
      stale = true
    })
    const loaded = await Promise.all(
      parameterNames.value.map(async (name, index) =>
        parameters.value[index]?.name === name
          ? parameters.value[index]
          : { name, terms: await fetchParameterTerms(name) }
      )
    )
    if (!stale) {
      parameters.value = loaded
    }
  }
)

async function handleBack() {
  if (
    (isEdit.value ? !hasChanges.value : isTextEmpty.value) ||
    (await confirm.value.open(t('_global.cancel_changes'), { type: 'warning' }))
  ) {
    emit('cancel')
  }
}

async function getApprovedTemplate(name) {
  if (createdTemplate?.name !== name) {
    const typeTerm = await getSoaFootnoteType()
    if (!typeTerm) {
      notificationHub.add({
        msg: t('ProtocolFlowchart.footnote_type_missing', {
          type: footnoteConstants.FOOTNOTE_TYPE_SOA,
        }),
        type: 'error',
      })
      return null
    }
    const resp = await footnoteTemplates.create({
      name,
      library_name: libraryConstants.LIBRARY_USER_DEFINED,
      type_uid: typeTerm.term_uid,
    })
    createdTemplate = { name, template: resp.data }
  }
  const { template } = createdTemplate
  if (template.status === statuses.DRAFT) {
    await footnoteTemplates.approve(template.uid)
    template.status = statuses.FINAL
  }
  return template
}

async function submit() {
  if (submitting.value) {
    return
  }
  const name = templateHtml.value
  const filledParameters = parameters.value
  notificationHub.clearErrors()
  submitting.value = true
  try {
    if (isEdit.value) {
      const textChanged = cleanName(name) !== cleanName(original.value.text)
      const template = textChanged
        ? await getApprovedTemplate(name)
        : original.value.template
      if (!template) {
        return
      }
      await footnotesStore.updateStudyFootnote({
        studyUid: studiesGeneralStore.selectedStudy.uid,
        studyFootnoteUid: props.studyFootnote.uid,
        form: { parameters: filledParameters },
        template,
        library: { name: libraryConstants.LIBRARY_USER_DEFINED },
      })
      emit('updated')
      return
    }
    const template = await getApprovedTemplate(name)
    if (!template) {
      return
    }
    await footnotesStore.addStudyFootnoteFromTemplate({
      studyUid: studiesGeneralStore.selectedStudy.uid,
      form: { footnote_template: template },
      parameters: filledParameters,
      referencedItems: props.referencedItems,
      layout: props.layout,
    })
    emit('created')
  } finally {
    submitting.value = false
  }
}
</script>
