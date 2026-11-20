<template>
  <div class="">
    <template v-if="editMode">
      <v-select
        v-model="element"
        :items="studyElements"
        :label="$t('ElementDropdownList.element')"
        item-title="name"
        item-value="element_uid"
        clearable
        class="mt-6 cellWidth"
        @update:model-value="updateElement"
        @click:clear="deleteElement"
      />
      <v-textarea
        v-if="props.transitionRulesMode && element"
        v-model="transitionRule"
        :label="$t('ElementDropdownList.transition_rule')"
        maxlength="200"
        counter="200"
        rows="1"
        auto-grow
        hide-details="auto"
        class="mb-4 cellWidth"
        @update:model-value="updateElement"
      />
    </template>
    <div v-else class="d-flex flex-column align-start">
      <v-tooltip bottom>
        <template #activator="{ props }">
          <span v-bind="props">
            <router-link
              v-if="element"
              :to="{
                name: 'StudyElementOverview',
                params: { study_id: selectedStudy.uid, id: element },
              }"
            >
              {{ getElementShortName(element) }}
            </router-link>
          </span>
        </template>
        <span>{{ getElementName(element) }}</span>
      </v-tooltip>
      <v-tooltip
        v-if="props.transitionRulesMode && cell?.transition_rule"
        bottom
      >
        <template #activator="{ props: tooltipProps }">
          <span
            v-bind="tooltipProps"
            tabindex="0"
            class="text-body-small text-primary transitionRuleLabel"
          >
            {{ $t('ElementDropdownList.transition_rule') }}
          </span>
        </template>
        <span class="transitionRuleText">{{ cell?.transition_rule }}</span>
      </v-tooltip>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

const props = defineProps({
  epoch: {
    type: String,
    default: '',
  },
  arm: {
    type: String,
    default: '',
  },
  armBranch: {
    type: String,
    default: '',
  },
  studyElements: {
    type: Array,
    default: () => [],
  },
  cells: {
    type: Object,
    default: undefined,
  },
  editMode: Boolean,
  transitionRulesMode: Boolean,
  saveObject: {
    type: Boolean,
    default: undefined,
  },
})
const emit = defineEmits(['addToObject'])

const studiesGeneralStore = useStudiesGeneralStore()

const selectedStudy = computed(() => studiesGeneralStore.selectedStudy)

const element = ref(null)
const cell = ref({})
const data = ref({})
const transitionRule = ref('')

watch(
  () => props.saveObject,
  (value) => {
    if (value) {
      emit('addToObject', data.value)
      data.value = {}
    }
  }
)
watch(
  () => props.cells,
  (value) => {
    cell.value = value.data.find(findCell)
    element.value = cell.value?.study_element_uid ?? null
  }
)

watch(
  () => props.editMode,
  (value) => {
    if (value) {
      transitionRule.value = cell.value?.transition_rule ?? ''
    }
  }
)

onMounted(() => {
  if (props.cells.data) {
    cell.value = props.cells.data.find(findCell)
  }
  if (cell.value) {
    element.value = cell.value.study_element_uid
    // The editMode watcher is not immediate, so a cell mounted while already
    // in edit mode must pick up its stored rule here.
    transitionRule.value = cell.value.transition_rule ?? ''
  }
})

function updateElement() {
  if (cell.value && element.value) {
    data.value = {
      method: 'PATCH',
      content: {
        study_element_uid: element.value,
        study_design_cell_uid: cell.value.design_cell_uid,
        transition_rule: transitionRule.value,
      },
    }
    props.armBranch
      ? (data.value.study_branch_arm_uid = props.armBranch)
      : (data.value.study_arm_uid = props.arm)
  } else if (element.value) {
    data.value = {
      method: 'POST',
      content: {
        study_arm_uid: props.arm,
        study_epoch_uid: props.epoch,
        study_element_uid: element.value,
        study_branch_arm_uid: props.armBranch,
        transition_rule: transitionRule.value,
      },
    }
  }
}

function deleteElement() {
  if (cell.value) {
    // cell stays set: picking another element must PATCH this cell, not POST
    // over (and thereby lose) the pending DELETE.
    data.value = {
      method: 'DELETE',
      content: {
        uid: cell.value.design_cell_uid,
      },
    }
  } else {
    // Nothing persisted to delete: drop any pending POST for the cleared element.
    data.value = {}
  }
  // Do not carry this rule over to a later POST for a different element.
  transitionRule.value = ''
}
function findCell(cell) {
  return (
    cell.study_epoch_uid === props.epoch &&
    (cell.study_arm_uid
      ? cell.study_arm_uid === props.arm
      : cell.study_branch_arm_uid === props.armBranch)
  )
}
function getElementShortName(elementUid) {
  const element = props.studyElements.find(
    (el) => el.element_uid === elementUid
  )
  return element ? element.short_name : ''
}
function getElementName(elementUid) {
  const element = props.studyElements.find(
    (el) => el.element_uid === elementUid
  )
  return element ? element.name : ''
}
</script>

<style scoped>
.cellWidth {
  max-width: 250px;
  min-width: 150px;
}

.transitionRuleText {
  white-space: pre-wrap;
  word-break: break-word;
}

.transitionRuleLabel {
  cursor: help;
  text-decoration: underline dotted;
  text-underline-offset: 2px;
}
</style>
