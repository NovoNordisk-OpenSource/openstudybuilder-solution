<template>
  <SimpleFormDialog
    ref="formRef"
    :title="$t('StudyAgeRulesForm.title')"
    :help-items="helpItems"
    :help-text="$t('_help.StudyAgeRulesForm.general')"
    :open="open"
    :save-disabled="loading"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-progress-linear v-if="loading" indeterminate color="primary" />
      <v-form ref="observer">
        <v-row v-for="field in fields" :key="field.name" class="pr-4">
          <v-col cols="11">
            <v-select
              v-model="form[field.name]"
              :data-cy="field.dataCy"
              :label="$t(field.label)"
              :items="field.items"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              return-object
              bg-color="white"
              color="nnBaseBlue"
              base-color="nnBaseBlue"
              clearable
            >
              <template #item="{ props: itemProps, item }">
                <v-list-item v-bind="itemProps">
                  <v-tooltip
                    v-if="item.definition"
                    activator="parent"
                    location="end"
                    max-width="400"
                  >
                    {{ item.definition }}
                  </v-tooltip>
                </v-list-item>
              </template>
              <template v-if="field.definition" #append>
                <v-btn
                  icon
                  size="small"
                  variant="text"
                  color="nnBaseBlue"
                  :aria-label="$t('_global.definition')"
                >
                  <v-icon>mdi-information-outline</v-icon>
                  <v-tooltip activator="parent" location="top" max-width="400">
                    {{ field.definition }}
                  </v-tooltip>
                </v-btn>
              </template>
            </v-select>
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useStudiesManageStore } from '@/stores/studies-manage'
import studyMetadataForms from '@/utils/studyMetadataForms'
import study from '@/api/study'

const { t } = useI18n()
const notificationHub = inject('notificationHub')

defineProps({
  open: Boolean,
})

const emit = defineEmits(['close', 'updated'])

const studiesGeneralStore = useStudiesGeneralStore()
const studiesManageStore = useStudiesManageStore()

const form = ref({})
const helpItems = [
  'StudyAgeRulesForm.age_at_baseline_rule',
  'StudyAgeRulesForm.age_group_rule',
]
const loading = ref(false)
const formRef = ref()
const observer = ref()
const fields = computed(() => [
  {
    name: 'age_at_baseline_rule_code',
    dataCy: 'age_at_baseline_rule',
    label: 'StudyAgeRulesForm.age_at_baseline_rule',
    items: studiesGeneralStore.ageAtBaselineRuleCodes,
    definition: studyMetadataForms.getTermDefinition(
      form.value.age_at_baseline_rule_code,
      studiesGeneralStore.ageAtBaselineRuleCodes
    ),
  },
  {
    name: 'age_group_rule_code',
    dataCy: 'age_group_rule',
    label: 'StudyAgeRulesForm.age_group_rule',
    items: studiesGeneralStore.ageGroupRuleCodes,
    definition: studyMetadataForms.getTermDefinition(
      form.value.age_group_rule_code,
      studiesGeneralStore.ageGroupRuleCodes
    ),
  },
])

onMounted(() => {
  loading.value = true
  study
    .getHighLevelStudyDesignMetadata(studiesGeneralStore.selectedStudy.uid)
    .then((resp) => {
      form.value = { ...resp.data.current_metadata.high_level_study_design }
    })
    .finally(() => {
      loading.value = false
    })
})

function prepareRequestPayload() {
  const data = { ...form.value }
  data.age_at_baseline_rule_code = studyMetadataForms.getTermPayload(
    data,
    'age_at_baseline_rule_code'
  )
  data.age_group_rule_code = studyMetadataForms.getTermPayload(
    data,
    'age_group_rule_code'
  )
  return data
}

function close() {
  emit('close')
  notificationHub.clearErrors()
  observer.value.resetValidation()
}

async function cancel() {
  const options = {
    type: 'warning',
    cancelLabel: t('_global.cancel'),
    agreeLabel: t('_global.continue'),
  }
  if (await formRef.value.confirm(t('_global.cancel_changes'), options)) {
    close()
  }
}

async function submit() {
  notificationHub.clearErrors()

  const data = prepareRequestPayload()
  try {
    const parentUid = studiesGeneralStore.selectedStudy.study_parent_part
      ? studiesGeneralStore.selectedStudy.study_parent_part.uid
      : null
    await studiesManageStore.editStudyType(
      studiesGeneralStore.selectedStudy.uid,
      data,
      parentUid
    )
    emit('updated', data)
    notificationHub.add({
      msg: t('StudyAgeRulesForm.update_success'),
    })
    close()
  } finally {
    formRef.value.working = false
  }
}
</script>
