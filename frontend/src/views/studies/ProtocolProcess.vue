<template>
  <div class="px-4">
    <div class="page-title">
      {{ $t('ProtocolProcessView.title') }}
    </div>
    <v-card flat>
      <v-card-title class="text-headline-small">
        {{ $t('ProtocolProcessView.sub_title') }}
      </v-card-title>
      <v-card-text>
        <p>{{ $t('ProtocolProcessView.description') }}</p>
        <div class="d-flex flex-wrap align-center">
          <div
            v-for="(step, index) in protocol"
            :key="index"
            class="d-flex mt-4 text-center align-center"
          >
            <v-menu v-if="step.items" offset-y>
              <template #activator="{ props }">
                <v-btn
                  color="primary"
                  :class="step.padding ? step.padding : 'pa-6'"
                  style="max-width: 150px"
                  :data-cy="step.title"
                  v-bind="props"
                >
                  {{ step.title }}
                </v-btn>
              </template>
              <v-list>
                <v-list-item
                  v-for="(item, itemIndex) in step.items"
                  :key="itemIndex"
                  @click="navigate(item.to)"
                >
                  <v-list-item-title>{{ item.title }}</v-list-item-title>
                </v-list-item>
              </v-list>
            </v-menu>
            <v-btn
              v-else-if="step.click"
              color="primary"
              :class="step.padding ? step.padding : 'pa-6'"
              style="max-width: 150px"
              :data-cy="step.title"
              @click="step.click"
            >
              {{ step.title }}
            </v-btn>
            <v-btn
              v-else
              color="primary"
              :class="step.padding ? step.padding : 'pa-6'"
              style="max-width: 150px"
              :data-cy="step.title"
              @click="navigate(step.to)"
            >
              {{ step.title }}
            </v-btn>
            <v-icon
              v-if="index !== protocol.length - 1 && !step.separatorText"
              size="large"
              class="mx-4"
              color="secondary"
              icon="mdi-arrow-right-bold-outline"
            />
            <span
              v-if="index !== protocol.length - 1 && step.separatorText"
              class="mx-6 text-secondary"
              ><strong>{{ step.separatorText }}</strong></span
            >
          </div>
        </div>
      </v-card-text>
    </v-card>
    <ConfirmDialog ref="confirmRef" :text-cols="5" :action-cols="6">
      <template #actions>
        <v-btn
          color="nnBaseBlue"
          rounded="xl"
          class="mr-2"
          elevation="1"
          @click="openSelectStudyDialog"
        >
          {{ $t('_global.select_study') }}
        </v-btn>
        <v-btn
          color="nnBaseBlue"
          rounded="xl"
          elevation="1"
          @click="redirectToStudyTable"
        >
          {{ $t('_global.add_study') }}
        </v-btn>
      </template>
    </ConfirmDialog>
    <v-dialog
      v-model="showSelectForm"
      persistent
      max-width="600px"
      @keydown.esc="showSelectForm = false"
    >
      <StudyQuickSelectForm
        @close="showSelectForm = false"
        @selected="goToNextUrl"
      />
    </v-dialog>
  </div>
</template>

<script setup>
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import StudyQuickSelectForm from '@/components/studies/StudyQuickSelectForm.vue'
import generalUtils from '@/utils/generalUtils'
import { useAppStore } from '@/stores/app'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

const { t } = useI18n()
const studiesGeneralStore = useStudiesGeneralStore()
const appStore = useAppStore()
const router = useRouter()
const route = useRoute()

const confirmRef = ref()
const studyUid = generalUtils.extractStudyUidFromLocalStorage()
const protocol = ref([
  {
    title: t('ProtocolProcessView.select_study'),
    click: showForm,
    separatorText: 'OR',
  },
  {
    title: t('ProtocolProcessView.add_new_study'),
    to: { name: 'SelectOrAddStudy' },
  },
  {
    title: t('ProtocolProcessView.study_structure'),
    items: [
      {
        title: t('ProtocolProcessView.study_arms'),
        to: {
          name: 'StudyStructure',
          params: { tab: 'arms', study_id: studyUid },
        },
      },
      {
        title: t('ProtocolProcessView.study_epochs'),
        to: {
          name: 'StudyStructure',
          params: { tab: 'epochs', study_id: studyUid },
        },
      },
      {
        title: t('ProtocolProcessView.study_elements'),
        to: {
          name: 'StudyStructure',
          params: { tab: 'elements', study_id: studyUid },
        },
      },
      {
        title: t('ProtocolProcessView.study_visits'),
        to: {
          name: 'StudyStructure',
          params: { tab: 'visits', study_id: studyUid },
        },
      },
      {
        title: t('ProtocolProcessView.design_matrix'),
        to: {
          name: 'StudyStructure',
          params: { tab: 'design_matrix', study_id: studyUid },
        },
      },
    ],
  },
  {
    title: t('ProtocolProcessView.study_purpose'),
    items: [
      {
        title: t('ProtocolProcessView.study_title'),
        to: { name: 'StudyTitle', params: { study_id: studyUid } },
      },
      {
        title: t('ProtocolProcessView.objectives'),
        to: {
          name: 'StudyPurpose',
          params: { tab: 'objectives', study_id: studyUid },
        },
      },
      {
        title: t('ProtocolProcessView.endpoints'),
        to: {
          name: 'StudyPurpose',
          params: { tab: 'endpoints', study_id: studyUid },
        },
      },
    ],
  },
  {
    title: t('ProtocolProcessView.study_population'),
    items: [
      {
        title: t('ProtocolProcessView.study_population'),
        to: { name: 'StudyPopulation', params: { study_id: studyUid } },
      },
      {
        title: t('ProtocolProcessView.inclusion_criteria'),
        to: {
          name: 'StudySelectionCriteria',
          params: { tab: 'Inclusion Criteria', study_id: studyUid },
        },
      },
      {
        title: t('ProtocolProcessView.exclusion_criteria'),
        to: {
          name: 'StudySelectionCriteria',
          params: { tab: 'Exclusion Criteria', study_id: studyUid },
        },
      },
      {
        title: t('ProtocolProcessView.runin_criteria'),
        to: {
          name: 'StudySelectionCriteria',
          params: { tab: 'Run-in Criteria', study_id: studyUid },
        },
      },
      {
        title: t('ProtocolProcessView.randomisation_criteria'),
        to: {
          name: 'StudySelectionCriteria',
          params: { tab: 'Randomisation Criteria', study_id: studyUid },
        },
      },
      {
        title: t('ProtocolProcessView.dosing_criteria'),
        to: {
          name: 'StudySelectionCriteria',
          params: { tab: 'Dosing Criteria', study_id: studyUid },
        },
      },
      {
        title: t('ProtocolProcessView.withdrawal_criteria'),
        to: {
          name: 'StudySelectionCriteria',
          params: { tab: 'Withdrawal Criteria', study_id: studyUid },
        },
      },
    ],
  },
  {
    title: t('ProtocolProcessView.schedules'),
    items: [
      {
        title: t('ProtocolProcessView.activity_list'),
        to: {
          name: 'StudyActivities',
          params: { tab: 'list', study_id: studyUid },
        },
      },
      {
        title: t('ProtocolProcessView.detailed_flowchart'),
        to: {
          name: 'StudyActivities',
          params: { tab: 'soa', study_id: studyUid },
        },
      },
    ],
  },
])
const showSelectForm = ref(false)
let nextUrl = {}

async function navigate(to) {
  nextUrl = to
  if (to.name !== 'SelectOrAddStudy' && !studiesGeneralStore.selectedStudy) {
    const options = {
      type: 'warning',
    }
    await confirmRef.value.open(t('_global.no_study_selected'), options)
    return
  }
  goToNextUrl()
}

function showForm() {
  showSelectForm.value = true
}

function goToNextUrl() {
  if (!nextUrl) {
    nextUrl = { name: route.name }
  }
  if (!nextUrl.params) {
    nextUrl.params = {
      study_id: generalUtils.extractStudyUidFromLocalStorage(),
    }
  } else {
    nextUrl.params.study_id = generalUtils.extractStudyUidFromLocalStorage()
  }
  const resolved = router.resolve(nextUrl)
  const [menuItem, menuSubItem] = appStore.findMenuItemPath(
    'Studies',
    nextUrl.name
  )
  appStore.section = 'Studies'
  nextUrl = null
  if (menuItem) {
    appStore.addBreadcrumbsLevel(menuItem.title, menuItem.url, 1)
    if (menuSubItem) {
      appStore.addBreadcrumbsLevel(menuSubItem.title, menuSubItem.url)
    }
  }
  router.push(resolved.href)
}

function openSelectStudyDialog() {
  confirmRef.value.cancel()
  showSelectForm.value = true
}

function redirectToStudyTable() {
  confirmRef.value.cancel()
  router.push({ name: 'SelectOrAddStudy' })
}
</script>

<style lang="scss">
.v-btn {
  &__content {
    width: 100% !important;
    white-space: normal !important;
  }
}
</style>
