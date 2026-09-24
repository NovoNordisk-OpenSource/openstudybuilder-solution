<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('StudyTitleView.title') }} ({{ studyId }})
      <HelpButtonWithPanels
        :help-text="$t('_help.StudyTitleView.general')"
        :items="helpItems"
      />
      <v-spacer />
      <v-btn
        class="ml-2"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        :data-cy="$t('StudyTitleView.edit_title')"
        :disabled="
          !checkPermission($roles.STUDY_WRITE) ||
          studiesGeneralStore.selectedStudyVersion !== null ||
          Boolean(studiesGeneralStore.selectedStudy.study_parent_part)
        "
        @click.stop="openForm"
      >
        <v-icon>mdi-pencil-outline</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ $t('StudyTitleView.edit_title') }}
        </v-tooltip>
      </v-btn>
    </div>
    <v-alert
      v-if="studiesGeneralStore.selectedStudy.study_parent_part"
      color="nnLightBlue200"
      icon="mdi-information-outline"
      class="text-nnTrueBlue my-2 sub-study-alert"
    >
      {{ $t('_global.sub_study_edit_warning') }}
    </v-alert>
    <v-sheet elevation="0" class="pa-6" rounded="lg">
      <v-divider class="mb-4" />
      <v-progress-linear
        v-if="loading"
        indeterminate
        color="nnBaseBlue"
        class="mb-4 description-loading"
      />
      <v-row>
        <v-col cols="12" md="6" class="title-col">
          <div class="h-100">
            <div class="label mb-2">
              {{ $t('StudyTitleView.title') }}
            </div>
            <div data-cy="study-title-field" class="text-body-large value">
              {{ description.study_title }}
            </div>
          </div>
        </v-col>
        <v-col cols="12" md="6" class="title-col">
          <div class="h-100">
            <div class="label mb-2">
              {{ $t('StudyTitleView.short_title') }}
            </div>
            <div data-cy="study-title-field" class="text-body-large value">
              {{ description.study_short_title }}
            </div>
          </div>
        </v-col>
      </v-row>
      <v-divider class="mt-4" />
      <div class="d-flex align-center mt-2 caption-row text-medium-emphasis">
        <v-icon size="18" class="mr-1">mdi-information-outline</v-icon>
        {{ $t('_help.StudyTitleView.general') }}
      </div>
    </v-sheet>
    <v-dialog
      v-model="showForm"
      persistent
      fullscreen
      hide-overlay
      @keydown.esc="showForm = false"
    >
      <StudyTitleForm
        :description="description"
        @updated="fetchStudyDescription"
        @close="showForm = false"
      />
    </v-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import study from '@/api/study'
import StudyTitleForm from '@/components/studies/StudyTitleForm.vue'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useAccessGuard } from '@/composables/accessGuard'

const studiesGeneralStore = useStudiesGeneralStore()

const studyId = studiesGeneralStore.studyId
const { checkPermission } = useAccessGuard()

const description = ref({})
const loading = ref(false)
const showForm = ref(false)
const helpItems = ['StudyTitleView.title']

function fetchStudyDescription() {
  loading.value = true
  const studyUid = studiesGeneralStore.selectedStudy.study_parent_part
    ? studiesGeneralStore.selectedStudy.study_parent_part.uid
    : studiesGeneralStore.selectedStudy.uid
  study
    .getStudyDescriptionMetadata(studyUid)
    .then((resp) => {
      description.value = resp.data.current_metadata.study_description
    })
    .finally(() => {
      loading.value = false
    })
}

function openForm() {
  showForm.value = true
}

onMounted(() => {
  fetchStudyDescription()
})
</script>

<style scoped>
.label {
  font-size: 20px;
  font-weight: 600;
  color: rgb(var(--v-theme-nnTrueBlue));
}

.value {
  line-height: 1.5;
  font-weight: 500;
  color: rgb(var(--v-theme-nnTrueBlue));
}

.caption-row {
  font-size: 13px;
}

.sub-study-alert {
  width: fit-content;
  max-width: 100%;
}

.description-loading {
  width: 80%;
  margin: 0 auto;
}

.title-col {
  position: relative;
  padding-left: 1rem;
}

.title-col::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  height: 80%;
  border-left: 1px solid rgb(var(--v-theme-greyBackground));
}
</style>
