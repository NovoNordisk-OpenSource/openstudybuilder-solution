<template>
  <div class="">
    <v-row v-if="editMode" class="d-flex align-center">
      <v-select
        v-model="element"
        :items="studyElements"
        label="Element"
        item-title="name"
        item-value="element_uid"
        clearable
        class="mt-6 cellWidth"
        @update:model-value="updateElement"
        @click:clear="deleteElement"
      />
      <v-btn
        v-if="props.transitionRulesMode && element"
        variant="outlined"
        class="ml-2 text-none"
        rounded="lg"
        hide-details
        @click="openTransitionRuleForm"
      >
        <span>{{ truncatedTransitionRule }}</span>
      </v-btn>
    </v-row>
    <div v-else class="d-flex justify-space-between">
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
      <v-tooltip v-if="props.transitionRulesMode" bottom>
        <template #activator="{ props }">
          <span v-bind="props">{{ truncatedTransitionRule }}</span>
        </template>
        <span>{{ cell?.transition_rule }}</span>
      </v-tooltip>
    </div>
    <SimpleFormDialog
      :title="$t('ElementDropdownList.transition_rule_form_title')"
      :open="showTransitionRuleForm"
      :action-label="$t('_global.accept')"
      @close="closeTransitionRuleForm"
      @submit="setTransitionRule"
    >
      <template #body>
        <v-form ref="observer">
          <v-textarea
            v-model="transitionRule"
            :rules="[(value) => formRules.max(value, 200)]"
            hide-details="auto"
          />
        </v-form>
      </template>
    </SimpleFormDialog>
  </div>
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'

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
const formRules = inject('formRules')

const studiesGeneralStore = useStudiesGeneralStore()

const selectedStudy = computed(() => studiesGeneralStore.selectedStudy)
const truncatedTransitionRule = computed(() => {
  let text
  if (props.editMode) {
    text = transitionRule.value
  } else {
    if (!cell.value) return ''
    text = cell.value.transition_rule
  }
  if (text < 5) {
    return text
  }
  return text.substring(0, 5) + '...'
})

const element = ref(null)
const cell = ref({})
const data = ref({})
const showTransitionRuleForm = ref(false)
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
    if (cell.value) {
      element.value = cell.value.study_element_uid
    }
  }
)

watch(
  () => props.editMode,
  (value) => {
    if (value) {
      if (cell.value) {
        transitionRule.value = cell.value.transition_rule
      }
    }
  }
)

onMounted(() => {
  if (props.cells.data) {
    cell.value = props.cells.data.find(findCell)
  }
  if (cell.value) {
    element.value = cell.value.study_element_uid
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
    data.value = {
      method: 'DELETE',
      content: {
        uid: cell.value.design_cell_uid,
      },
    }
    cell.value = undefined
  }
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

function openTransitionRuleForm() {
  showTransitionRuleForm.value = true
}

function closeTransitionRuleForm() {
  showTransitionRuleForm.value = false
}

function setTransitionRule() {
  if (cell.value) {
    cell.value.transition_rule = transitionRule.value
  }
  updateElement()
  closeTransitionRuleForm()
}
</script>

<style scoped>
.cellWidth {
  max-width: 250px;
  min-width: 150px;
}
</style>
