<template>
  <div class="w-50">
    <div class="dialog-title mb-4">
      {{ $t('StudyStructureCopyForm.title1') }}
    </div>
    <v-form ref="formRef">
      <StudySelectorField
        v-model="form.study"
        @update:model-value="loadStudyData"
      />
      <template v-if="form.study">
        <v-skeleton-loader v-if="loading" type="card" />
        <template v-else>
          <div class="dialog-sub-title">
            {{ $t('StudyStructureCopyForm.preview_of_study') }}
          </div>
          <div class="my-4" v-html="studyDesignSvg" />
          <div class="dialog-title mb-4">
            {{ $t('StudyStructureCopyForm.title2') }}
          </div>
          <div class="w-50">
            <CheckboxField
              v-model="form.copy_study_arm"
              :label="
                $t('StudyStructureCopyForm.arms', {
                  count: studyStats.arm_count,
                })
              "
              :help="$t('StudyStructureCopyForm.arms_help')"
              @update:model-value="(value) => checkDependencies('arm', value)"
            />
            <CheckboxField
              v-if="form.copy_study_arm"
              v-model="form.copy_study_branch_arm"
              :label="
                $t('StudyStructureCopyForm.branches', {
                  count: studyStats.branch_count,
                })
              "
              :help="$t('StudyStructureCopyForm.branches_help')"
              class="mt-4"
              @update:model-value="
                (value) => checkDependencies('branch_arm', value)
              "
            />
            <CheckboxField
              v-if="form.copy_study_arm && form.copy_study_branch_arm"
              v-model="form.copy_study_cohort"
              :label="
                $t('StudyStructureCopyForm.cohorts', {
                  count: studyStats.cohort_count,
                })
              "
              :help="$t('StudyStructureCopyForm.cohorts_help')"
              class="mt-4"
            />
            <CheckboxField
              v-model="form.copy_study_element"
              :label="
                $t('StudyStructureCopyForm.elements', {
                  count: studyStats.element_count,
                })
              "
              :help="$t('StudyStructureCopyForm.elements_help')"
              class="mt-4"
              @update:model-value="
                (value) => checkDependencies('element', value)
              "
            />
            <CheckboxWithChildField
              v-model="form.copy_study_epochs_study_footnote"
              :label="
                $t('StudyStructureCopyForm.footnotes', {
                  count: studyStats.epoch_footnote_count,
                })
              "
              class="mt-4"
            >
              <template #default="{ updateChildDisplay }">
                <CheckboxField
                  v-model="form.copy_study_epoch"
                  :label="
                    $t('StudyStructureCopyForm.epochs', {
                      count: studyStats.epoch_count,
                    })
                  "
                  :help="$t('StudyStructureCopyForm.epochs_help')"
                  @update:model-value="
                    (value) => {
                      updateChildDisplay(value)
                      checkDependencies('epoch', value)
                    }
                  "
                />
              </template>
            </CheckboxWithChildField>
            <CheckboxWithChildField
              v-if="form.copy_study_epoch"
              v-model="form.copy_study_visits_study_footnote"
              :label="
                $t('StudyStructureCopyForm.footnotes', {
                  count: studyStats.visit_footnote_count,
                })
              "
              class="mt-4"
            >
              <template #default="{ updateChildDisplay }">
                <CheckboxField
                  v-model="form.copy_study_visit"
                  :label="
                    $t('StudyStructureCopyForm.visits', {
                      count: studyStats.visit_count,
                    })
                  "
                  :help="$t('StudyStructureCopyForm.visits_help')"
                  @update:model-value="
                    (value) => {
                      updateChildDisplay(value)
                      checkDependencies('visit', value)
                    }
                  "
                />
              </template>
            </CheckboxWithChildField>
            <CheckboxField
              v-if="designMatrixEnabled"
              v-model="form.copy_study_design_matrix"
              :label="$t('StudyStructureCopyForm.design_matrix')"
              :help="$t('StudyStructureCopyForm.design_matrix_help')"
              class="mt-4"
            />
          </div>
        </template>
      </template>
    </v-form>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import studyApi from '@/api/study'
import StudySelectorField from './StudySelectorField.vue'
import CheckboxField from '@/components/ui/CheckboxField.vue'
import CheckboxWithChildField from '@/components/ui/CheckboxWithChildField.vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: null,
  },
})
const emit = defineEmits(['update:modelValue'])

const formRef = ref()
const loading = ref(false)
const studyDesignSvg = ref()
const studyStats = ref({})

const form = computed({
  get() {
    return props.modelValue
  },
  set(value) {
    emit('update:modelValue', value)
  },
})

const designMatrixEnabled = computed(() => {
  return (
    form.value.copy_study_arm &&
    form.value.copy_study_branch_arm &&
    form.value.copy_study_element &&
    form.value.copy_study_epoch
  )
})

const selectionMade = computed(() => {
  return Object.values(form.value).some((checkbox) => checkbox === true)
})

async function loadStudyData(study) {
  loading.value = true
  let resp = await studyApi.getStudyDesignFigureSvg(study.uid)
  studyDesignSvg.value = resp.data
  resp = await studyApi.getStructureStatistics(study.uid)
  studyStats.value = resp.data
  loading.value = false
}

const checkDependencies = (element, value) => {
  switch (element) {
    case 'arm':
      if (!value) {
        form.value.copy_study_branch_arm = false
        form.value.copy_study_cohort = false
        form.value.copy_study_design_matrix = false
      }
      break
    case 'branch_arm':
      if (!value) {
        form.value.copy_study_cohort = false
        form.value.copy_study_design_matrix = false
      }
      break
    case 'element':
      if (!value) {
        form.value.copy_study_design_matrix = false
      }
      break
    case 'epoch':
      if (!value) {
        form.value.copy_study_epochs_study_footnote = false
        form.value.copy_study_visit = false
        form.value.copy_study_visits_study_footnote = false
        form.value.copy_study_design_matrix = false
      }
      break
    case 'visit':
      if (!value) {
        form.value.copy_study_visits_study_footnote = false
        form.value.copy_study_design_matrix = false
      }
      break
  }
}

defineExpose({
  formRef,
  selectionMade,
})
</script>
