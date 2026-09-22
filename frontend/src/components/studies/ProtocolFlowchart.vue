<template>
  <div class="pa-4 bg-white">
    <v-row class="mb-2">
      <v-col cols="4"> </v-col>
      <v-col cols="8" class="d-flex align-center">
        <v-spacer />
        <v-switch
          v-show="switchIsEnabled(['protocol'])"
          v-model="showSplitMenu"
          :label="$t('ProtocolFlowchart.show_split_menu')"
          hide-details
          class="mr-4"
          :readonly="loading || toggle.length !== 0"
          :disabled="toggle.length !== 0"
          :loading="loading ? 'warning' : null"
        />
        <v-switch
          v-show="switchIsEnabled(['protocol'])"
          v-model="studiesGeneralStore.soaPreferences.show_epochs"
          :label="$t('ProtocolFlowchart.show_epochs')"
          hide-details
          class="mr-4"
          :readonly="loading"
          :loading="loading ? 'warning' : null"
          @update:model-value="updateSoaPreferences('show_epochs')"
        />
        <v-switch
          v-show="switchIsEnabled(['protocol'])"
          v-model="studiesGeneralStore.soaPreferences.show_milestones"
          :label="$t('ProtocolFlowchart.show_milestones')"
          hide-details
          class="mr-4"
          :readonly="loading"
          :loading="loading ? 'warning' : null"
          @update:model-value="updateSoaPreferences('show_milestones')"
        />
        <v-switch
          v-show="switchIsEnabled(['protocol_lab_table'])"
          v-model="studiesGeneralStore.soaPreferences.show_all_visits_lab_table"
          :label="$t('ProtocolFlowchart.show_all_visits_lab_table')"
          hide-details
          class="mr-4"
          :readonly="loading"
          :loading="loading ? 'warning' : null"
          @update:model-value="
            updateSoaPreferences('show_all_visits_lab_table')
          "
        />
        <v-menu rounded location="bottom">
          <template #activator="{ props }">
            <v-btn
              class="ml-2"
              icon
              size="small"
              variant="outlined"
              color="nnBaseBlue"
              v-bind="props"
              :loading="loading"
            >
              <v-icon>mdi-download-outline</v-icon>
              <v-tooltip activator="parent" location="top">
                {{ $t('DataTableExportButton.export') }}
              </v-tooltip>
            </v-btn>
          </template>
          <v-list>
            <v-list-item link @click="downloadCSV">
              <v-list-item-title>CSV</v-list-item-title>
            </v-list-item>
            <v-list-item link @click="downloadEXCEL">
              <v-list-item-title>EXCEL</v-list-item-title>
            </v-list-item>
            <v-list-item link @click="downloadDocx">
              <v-list-item-title>DOCX</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
      </v-col>
    </v-row>
    <div v-if="layout === 'protocol' && showSplitMenu">
      <div class="text-center">
        {{ $t('ProtocolFlowchart.split_info_1') }}
      </div>
      <div class="text-center">
        {{ $t('ProtocolFlowchart.split_info_2') }}
      </div>
      <div class="d-flex flex-column align-center pa-2">
        <v-btn-toggle
          v-model="toggle"
          class="btn-toggle"
          variant="outlined"
          divided
          multiple
        >
          <v-slide-group show-arrows>
            <div
              v-for="visit in groupedVisits"
              :key="visit.uid"
              class="slide-div"
            >
              <v-btn
                selected-class="split-class"
                variant="outlined"
                rounded="0"
                class="mt-2"
                height="40px"
                elevation="0"
                :value="visit.uid"
                :disabled="!switchIsEnabled(['protocol'])"
                @click="splitSoA(visit.uid)"
              >
                <template #prepend>
                  <v-icon
                    v-if="toggle.includes(visit.uid)"
                    icon="mdi-content-cut"
                    class="horizontal-flip"
                  />
                </template>
                {{ visit.group || visit.name }}
              </v-btn>

              <Transition name="slide-fade">
                <div
                  v-if="toggle.includes(visit.uid)"
                  style="text-align: center"
                >
                  <v-btn
                    variant="outlined"
                    class="mt-n2 go-to-btn"
                    elevation="0"
                    :loading="splitLoading"
                    @click="scrollToSplit(visit)"
                  >
                    {{ $t('_global.go_to') }}
                    <template #loader>
                      <v-progress-linear
                        style="width: 75%"
                        rounded
                        indeterminate
                      />
                    </template>
                  </v-btn>
                </div>
              </Transition>
            </div>
          </v-slide-group>
        </v-btn-toggle>
      </div>
    </div>
    <div
      id="protocolFlowchart"
      v-html="sanitizeHTMLHandler(protocolFlowchart)"
    />
  </div>
</template>

<script setup>
import { inject, onMounted, ref, watch } from 'vue'
import study from '@/api/study'
import soaDownloads from '@/utils/soaDownloads'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import unitConstants from '@/constants/units'
import units from '@/api/units'
import { useAccessGuard } from '@/composables/accessGuard'
import { sanitizeHTML } from '@/utils/sanitize'

const props = defineProps({
  update: {
    type: Number,
    default: 0,
  },
  layout: {
    type: String,
    default: 'protocol',
  },
  studyVisits: {
    type: Array,
    default: null,
  },
})

const studiesGeneralStore = useStudiesGeneralStore()
const accessGuard = useAccessGuard()
const roles = inject('roles')

const protocolFlowchart = ref('')
const loading = ref(true)
const preferredTimeUnits = ref([])
const toggle = ref([])
const groupedVisits = ref([])
const showSplitMenu = ref(false)
const splitLoading = ref(false)

watch(
  () => props.layout,
  (newVal, oldVal) => {
    if (newVal !== oldVal) updateFlowchart()
  }
)
watch(
  () => props.update,
  (newVal, oldVal) => {
    if (newVal !== oldVal) updateFlowchart()
  }
)

onMounted(() => {
  updateFlowchart()
  units
    .getBySubset(unitConstants.TIME_UNIT_SUBSET_STUDY_PREFERRED_TIME_UNIT)
    .then((resp) => {
      preferredTimeUnits.value = resp.data.items
    })
  loadVisits()
  getSoASplits()
})

function scrollToSplit(visit) {
  toggle.value = toggle.value.filter(
    (item) => !(typeof item === 'number' && Number.isInteger(item))
  )
  const uidSet = new Set(toggle.value)
  const index = groupedVisits.value
    .filter((item) => uidSet.has(item.uid))
    .map((item) => item.uid)
    .indexOf(visit.uid)
  const els = document.querySelectorAll('table')
  els[index + 1].scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function loadVisits() {
  try {
    // These visit names are placeholders and should be excluded from split-menu grouping.
    const excludedVisitNames = new Set(['29500', '29999'])

    const visits = props.studyVisits.map((v) => ({
      name: v.visit_short_name,
      uid: v.uid,
      show_visit: v.show_visit,
      group: v.consecutive_visit_group ?? null,
    }))

    const result = []
    let lastGroup = null
    let lastVisitInGroup = null

    for (const visit of visits.slice(1)) {
      if (!visit.show_visit) {
        continue
      }

      if (excludedVisitNames.has(`${visit.name}`.trim())) {
        continue
      }

      if (!visit.group) {
        if (lastVisitInGroup) {
          result.push(lastVisitInGroup)
          lastVisitInGroup = null
        }
        result.push(visit)
        lastGroup = null
      } else {
        if (!lastGroup) {
          lastVisitInGroup = visit
        } else if (visit.group === lastGroup) {
          lastVisitInGroup = visit
        } else {
          result.push(lastVisitInGroup)
        }
        lastGroup = visit.group
      }
    }
    groupedVisits.value = result
  } catch (error) {
    console.error('Failed to load visits', error)
  }
}
async function splitSoA(visitUid) {
  splitLoading.value = true
  loading.value = true
  if (toggle.value.includes(visitUid)) {
    const payload = { uid: visitUid }
    await study.splitSoA(studiesGeneralStore.selectedStudy.uid, payload)
    updateFlowchart()
  } else {
    await study.removeSoASplit(studiesGeneralStore.selectedStudy.uid, visitUid)
    updateFlowchart()
  }
}
async function getSoASplits() {
  const resp = await study.getSoASplits(studiesGeneralStore.selectedStudy.uid)
  toggle.value = resp.data.map((item) => item.uid)
  if (toggle.value.length) {
    showSplitMenu.value = true
  }
}
function sanitizeHTMLHandler(html) {
  return sanitizeHTML(html)
}
function switchIsEnabled(layouts = []) {
  return (
    !studiesGeneralStore.selectedStudyVersion &&
    accessGuard.checkPermission(roles.STUDY_WRITE) &&
    (!layouts || layouts.includes(props.layout))
  )
}
function updateSoaPreferences(key) {
  loading.value = true
  studiesGeneralStore
    .setSoaPreferences({ [key]: studiesGeneralStore.soaPreferences[key] })
    .then(() => {
      updateFlowchart()
    })
}
function updateFlowchart() {
  loading.value = true
  study
    .getStudyProtocolFlowchartHtml(studiesGeneralStore.selectedStudy.uid, {
      layout: props.layout,
    })
    .then((resp) => {
      protocolFlowchart.value = resp.data
      splitLoading.value = false
    })
    .finally(() => {
      stopLoading()
    })
}
async function downloadDocx() {
  loading.value = true
  try {
    await soaDownloads.docxDownload(props.layout)
  } finally {
    stopLoading()
  }
}
async function downloadCSV() {
  loading.value = true
  try {
    await soaDownloads.csvDownload(props.layout)
  } finally {
    stopLoading()
  }
}
async function downloadEXCEL() {
  loading.value = true
  try {
    await soaDownloads.excelDownload(props.layout)
  } finally {
    stopLoading()
  }
}
function stopLoading() {
  loading.value = false
}
</script>

<style lang="scss">
.split-class {
  color: red;
  border-inline-start-style: solid !important;
  border-left-color: red !important;
  border-left-width: medium !important;
  width: -webkit-fill-available;
}
.layoutSelect {
  max-width: 200px;
}
.horizontal-flip {
  transform: rotate(180deg);
}
.btn-toggle {
  overflow-x: auto;
  height: 70px !important;
}
.slide-div {
  display: inline-block;
  vertical-align: top;
}
.go-to-btn {
  width: -webkit-fill-available;
  border-bottom-left-radius: 5px !important;
  border-bottom-right-radius: 5px !important;
}
#protocolFlowchart {
  padding-bottom: 1em;

  table {
    width: 100%;
    border-collapse: collapse;
    table-layout: auto;
    resize: both;
    margin-bottom: 1em;

    &:not(:first-child) {
      margin-top: 2em;
    }

    &,
    & th,
    & td {
      border: 1px solid black;
      padding: 1px 3px;
    }

    & thead {
      background-color: rgb(var(--v-theme-tableGray));

      & th {
        border-color: black;
      }

      & .header1:nth-child(n + 2) {
        vertical-align: top;
        text-orientation: mixed;
      }

      & th:first-child {
        text-align: left;
      }
    }

    & tbody {
      & th {
        text-align: left;
        font-weight: normal;
      }

      & tr td:nth-child(n + 2) {
        text-align: center;
        vertical-align: middle;
      }

      & .soaGroup {
        background-color: rgb(var(--v-theme-tableGray));
        font-weight: bold;
      }

      & .group {
        background-color: rgb(var(--v-theme-tableGray));
        font-weight: bold;
      }

      & .subGroup {
        background-color: rgb(var(--v-theme-tableGray));
      }

      & .activity:first-child,
      & .activityPlaceholder:first-child,
      & .activityPlaceholderSubmitted:first-child {
        padding-left: 1em;
      }

      & .activityInstance:first-child {
        padding-left: 2em;
        font-style: italic;
      }
    }
  }
}

.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}

.slide-fade-enter-from {
  transform: translateY(15px);
}

.slide-fade-leave-active {
  animation: slideOut 0.2s ease-out;
}

@keyframes slideOut {
  0% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(-30px);
  }
  100% {
    transform: translateX(150px);
  }
}

.slide-fade-leave-to {
  transform: translateX(150px);
}
</style>
