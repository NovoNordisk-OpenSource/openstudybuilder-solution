<template>
  <div>
    <NNTable
      ref="table"
      :headers="headers"
      :items="items"
      item-value="uid"
      :items-length="total"
      :export-data-url="exportDataUrl"
      export-object-label="StudyDesignPopulations"
      :column-data-resource="exportDataUrl"
      :hide-default-body="sortMode && items.length > 0"
      :history-config="{
        dataFetcher: fetchAllHistory,
        externalHeaders: historyHeaders,
        identityKey: 'uid',
        title: $t('StudyDesignPopulationTable.global_history_title'),
      }"
      @filter="fetchItems"
    >
      <template #afterSwitches>
        <div :title="$t('NNTableTooltips.reorder_content')">
          <v-switch
            v-model="sortMode"
            :label="$t('NNTable.reorder_content')"
            hide-details
            class="mr-6"
            :disabled="!accessGuard.checkPermission($roles.STUDY_WRITE)"
          />
        </div>
      </template>
      <template #actions>
        <v-btn
          data-cy="add-study-design-population"
          class="ml-2"
          icon
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          :disabled="
            !accessGuard.checkPermission($roles.STUDY_WRITE) ||
            studiesGeneralStore.selectedStudyVersion !== null
          "
          @click="openCreate"
        >
          <v-icon>mdi-plus</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ $t('StudyDesignPopulationForm.add_title') }}
          </v-tooltip>
        </v-btn>
      </template>
      <template #tbody>
        <tbody v-show="sortMode" ref="parent">
          <tr v-for="item in items" :key="item.uid">
            <td>
              <v-icon size="small"> mdi-sort </v-icon>
            </td>
            <td>{{ item.group_id }}</td>
            <td>{{ item.name }}</td>
            <td>{{ item.definition }}</td>
            <td>{{ item.notes }}</td>
            <td>
              <ul
                v-if="criteriaByPopulation[item.uid]?.inclusion?.length"
                class="criteria-list"
              >
                <li
                  v-for="c in criteriaByPopulation[item.uid].inclusion"
                  :key="c.uid"
                >
                  {{ c.shortLabel }}
                  <v-tooltip
                    v-if="c.truncated"
                    activator="parent"
                    location="top"
                    max-width="400"
                  >
                    {{ c.label }}
                  </v-tooltip>
                </li>
              </ul>
              <span v-else class="text-disabled text-caption">—</span>
            </td>
            <td>
              <ul
                v-if="criteriaByPopulation[item.uid]?.exclusion?.length"
                class="criteria-list"
              >
                <li
                  v-for="c in criteriaByPopulation[item.uid].exclusion"
                  :key="c.uid"
                >
                  {{ c.shortLabel }}
                  <v-tooltip
                    v-if="c.truncated"
                    activator="parent"
                    location="top"
                    max-width="400"
                  >
                    {{ c.label }}
                  </v-tooltip>
                </li>
              </ul>
              <span v-else class="text-disabled text-caption">—</span>
            </td>
            <td>{{ $filters.date(item.start_date) }}</td>
            <td>{{ item.author_username }}</td>
          </tr>
        </tbody>
      </template>
      <template #[`item.actions`]="{ item }">
        <ActionsMenu :actions="actions" :item="item" />
      </template>
      <template #[`item.inclusion_criteria`]="{ item }">
        <ul
          v-if="criteriaByPopulation[item.uid]?.inclusion?.length"
          class="criteria-list"
        >
          <li
            v-for="c in criteriaByPopulation[item.uid].inclusion"
            :key="c.uid"
          >
            {{ c.shortLabel }}
            <v-tooltip
              v-if="c.truncated"
              activator="parent"
              location="top"
              max-width="400"
            >
              {{ c.label }}
            </v-tooltip>
          </li>
        </ul>
        <span v-else class="text-disabled text-caption">—</span>
      </template>
      <template #[`item.exclusion_criteria`]="{ item }">
        <ul
          v-if="criteriaByPopulation[item.uid]?.exclusion?.length"
          class="criteria-list"
        >
          <li
            v-for="c in criteriaByPopulation[item.uid].exclusion"
            :key="c.uid"
          >
            {{ c.shortLabel }}
            <v-tooltip
              v-if="c.truncated"
              activator="parent"
              location="top"
              max-width="400"
            >
              {{ c.label }}
            </v-tooltip>
          </li>
        </ul>
        <span v-else class="text-disabled text-caption">—</span>
      </template>
      <template #[`item.start_date`]="{ item }">
        <v-tooltip location="top">
          <template #activator="{ props }">
            <span v-bind="props">{{
              $filters.dateRelative(item.start_date)
            }}</span>
          </template>
          {{ $filters.date(item.start_date) }}
        </v-tooltip>
      </template>
    </NNTable>

    <StudyDesignPopulationForm
      :open="showForm"
      :sdp="selectedItem"
      @close="closeForm"
      @saved="onPopulationSaved"
    />

    <StudyDesignPopulationCriteriaForm
      :open="showCriteriaForm"
      :population="savedPopulation"
      @close="closeCriteriaForm"
      @saved="table.filterTable()"
    />

    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />

    <v-dialog
      v-model="showHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="showHistory = false"
    >
      <HistoryTable
        :title="historyTitle"
        :headers="historyHeaders"
        :items="historyItems"
        :items-total="historyItems.length"
        identity-key="uid"
        @close="showHistory = false"
      />
    </v-dialog>
  </div>
</template>

<script setup>
import { computed, inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDragAndDrop } from '@formkit/drag-and-drop/vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StudyDesignPopulationCriteriaForm from './StudyDesignPopulationCriteriaForm.vue'
import StudyDesignPopulationForm from './StudyDesignPopulationForm.vue'
import filteringParameters from '@/utils/filteringParameters'
import study from '@/api/study'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'

const [parent, items] = useDragAndDrop([], {
  onDragend: (event) => {
    const newOrder =
      event.draggedNode.data.value.order -
      (event.state.initialIndex - event.state.targetIndex)
    changeOrder(event.draggedNode.data.value.uid, newOrder)
  },
})

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const roles = inject('roles')
const studiesGeneralStore = useStudiesGeneralStore()
const accessGuard = useAccessGuard()

const table = ref()
const confirm = ref()
const total = ref(0)
const selectedItem = ref(null)
const showForm = ref(false)
const showCriteriaForm = ref(false)
const savedPopulation = ref(null)
const showHistory = ref(false)
const historyItems = ref([])
const allCriteria = ref([])
const sortMode = ref(false)

const headers = [
  { title: '', key: 'actions', width: '1%' },
  { title: t('StudyDesignPopulationTable.group_id'), key: 'group_id' },
  { title: t('StudyDesignPopulationTable.name'), key: 'name' },
  { title: t('StudyDesignPopulationTable.definition'), key: 'definition' },
  { title: t('StudyDesignPopulationTable.notes'), key: 'notes' },
  {
    title: t('StudyDesignPopulationTable.inclusion_criteria'),
    key: 'inclusion_criteria',
    sortable: false,
  },
  {
    title: t('StudyDesignPopulationTable.exclusion_criteria'),
    key: 'exclusion_criteria',
    sortable: false,
  },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.modified_by'), key: 'author_username' },
]

// The criteria columns are derived from the criteria selections, which have
// their own audit trail, so they cannot be shown on a design population
// history record.
const historyHeaders = [
  { title: t('_global.uid'), key: 'uid' },
  { title: t('StudyDesignPopulationTable.group_id'), key: 'group_id' },
  { title: t('StudyDesignPopulationTable.name'), key: 'name' },
  { title: t('StudyDesignPopulationTable.definition'), key: 'definition' },
  { title: t('StudyDesignPopulationTable.notes'), key: 'notes' },
]

const actions = [
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    click: editItem,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('StudyDesignPopulationTable.link_criteria'),
    icon: 'mdi-link-variant',
    iconColor: 'primary',
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    click: linkCriteria,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    click: deleteItem,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openHistory,
  },
]

const exportDataUrl = computed(
  () =>
    `studies/${studiesGeneralStore.selectedStudy.uid}/study-design-populations`
)
const historyTitle = computed(() =>
  selectedItem.value
    ? t('StudyDesignPopulationTable.item_history_title', {
        uid: selectedItem.value.uid,
      })
    : ''
)

// Long criteria texts are shortened in the cell and shown in full on hover.
const CRITERIA_LABEL_MAX_LENGTH = 50

const criteriaByPopulation = computed(() => {
  const map = {}
  for (const c of allCriteria.value) {
    const popUids = [...new Set(c.study_design_population_uids ?? [])]
    if (!popUids.length) continue
    const typeName = c.criteria_type?.term_name?.toLowerCase() ?? ''
    const label = `${c.order}. ${c.criteria ? c.criteria.name_plain : (c.template?.name_plain ?? '')}`
    const truncated = label.length > CRITERIA_LABEL_MAX_LENGTH
    const entry = {
      uid: c.study_criteria_uid,
      label,
      truncated,
      shortLabel: truncated
        ? `${label.slice(0, CRITERIA_LABEL_MAX_LENGTH).trimEnd()}…`
        : label,
    }
    for (const popUid of popUids) {
      if (!map[popUid]) map[popUid] = { inclusion: [], exclusion: [] }
      if (typeName.includes('inclusion')) {
        map[popUid].inclusion.push(entry)
      } else if (typeName.includes('exclusion')) {
        map[popUid].exclusion.push(entry)
      }
    }
  }
  return map
})

function fetchItems(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  study
    .getStudyDesignPopulations(studiesGeneralStore.selectedStudy.uid, params)
    .then((resp) => {
      items.value = resp.data.items
      total.value = resp.data.total
    })
  study.getStudyCriteria(studiesGeneralStore.selectedStudy.uid).then((resp) => {
    const seen = new Set()
    allCriteria.value = (resp.data.items ?? []).filter((c) => {
      if (seen.has(c.study_criteria_uid)) return false
      seen.add(c.study_criteria_uid)
      return true
    })
  })
}

async function fetchAllHistory() {
  const resp = await study.getStudyDesignPopulationsAuditTrail(
    studiesGeneralStore.selectedStudy.uid
  )
  return resp.data
}

function openCreate() {
  selectedItem.value = null
  showForm.value = true
}

function editItem(item) {
  selectedItem.value = item
  showForm.value = true
}

function closeForm() {
  showForm.value = false
}

// The population and its criteria assignments are saved via two
// independent API calls: once the population form closes on a successful
// save, automatically open the criteria dialog for the saved population.
function onPopulationSaved(population) {
  table.value.filterTable()
  savedPopulation.value = population
  showCriteriaForm.value = true
}

function linkCriteria(item) {
  savedPopulation.value = item
  showCriteriaForm.value = true
}

function closeCriteriaForm() {
  showCriteriaForm.value = false
  savedPopulation.value = null
}

async function deleteItem(item) {
  const options = { type: 'warning' }
  const msg = t('StudyDesignPopulationTable.confirm_delete', {
    name: item.name || item.uid,
  })
  if (!(await confirm.value.open(msg, options))) return
  study
    .deleteStudyDesignPopulation(
      studiesGeneralStore.selectedStudy.uid,
      item.uid
    )
    .then(() => {
      notificationHub.add({
        msg: t('StudyDesignPopulationTable.delete_success'),
      })
      table.value.filterTable()
    })
}

async function openHistory(item) {
  selectedItem.value = item
  const resp = await study.getStudyDesignPopulationAuditTrail(
    studiesGeneralStore.selectedStudy.uid,
    item.uid
  )
  historyItems.value = resp.data
  showHistory.value = true
}

function changeOrder(populationUid, newOrder) {
  study
    .updateStudyDesignPopulationOrder(
      studiesGeneralStore.selectedStudy.uid,
      populationUid,
      newOrder
    )
    .then(() => {
      table.value.filterTable()
    })
    .catch(() => {
      table.value.filterTable()
    })
}
</script>

<style scoped>
.criteria-list {
  margin: 4px 0;
  padding-left: 18px;
  list-style-type: disc;
}

.criteria-list li {
  padding: 1px 0;
}
</style>
