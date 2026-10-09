<template>
  <div class="">
    <v-select
      v-if="editMode"
      v-model="element"
      :items="studyElements"
      :label="$t('ElementDropdownList.element')"
      item-title="name"
      item-value="element_uid"
      clearable
      class="mt-6 cellWidth"
      @update:model-value="updateElement"
      @click:clear="deleteElement"
    >
      <template v-if="props.transitionRulesMode && element" #append-inner>
        <v-menu
          v-model="showTransitionRuleMenu"
          open-on-hover
          :close-on-content-click="false"
          location="bottom end"
        >
          <template #activator="{ props: menuProps }">
            <v-badge
              :model-value="hasTransitionRule"
              dot
              color="primary"
              location="top end"
            >
              <v-btn
                v-bind="menuProps"
                :icon="
                  hasTransitionRule ? 'mdi-note-text' : 'mdi-note-text-outline'
                "
                :color="hasTransitionRule ? 'primary' : undefined"
                variant="text"
                size="x-small"
                :aria-label="
                  hasTransitionRule
                    ? $t('ElementDropdownList.edit_transition_rule')
                    : $t('ElementDropdownList.add_transition_rule')
                "
                @mousedown.stop
                @click.stop
              />
            </v-badge>
          </template>
          <v-card max-width="260">
            <v-card-text class="pb-2">
              <div class="text-caption text-medium-emphasis mb-1">
                {{ $t('ElementDropdownList.transition_rule_form_title') }}
              </div>
              <p
                v-if="hasTransitionRule"
                class="text-body-2 mb-0 transitionRuleText"
              >
                {{ transitionRule }}
              </p>
              <p v-else class="text-body-2 text-medium-emphasis mb-0">
                {{ $t('ElementDropdownList.no_transition_rule') }}
              </p>
            </v-card-text>
            <v-card-actions class="pt-0 justify-end">
              <v-btn
                size="small"
                variant="text"
                color="primary"
                @click="openTransitionRuleFromMenu"
              >
                {{ hasTransitionRule ? $t('_global.edit') : $t('_global.add') }}
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-menu>
      </template>
    </v-select>
    <div v-else class="d-flex justify-space-between align-center">
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
          <v-icon
            v-bind="tooltipProps"
            icon="mdi-note-text"
            color="primary"
            size="small"
            class="ml-1"
          />
        </template>
        <span class="transitionRuleText">{{ cell?.transition_rule }}</span>
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
const hasTransitionRule = computed(() =>
  Boolean(transitionRule.value && transitionRule.value.trim().length > 0)
)

const element = ref(null)
const cell = ref({})
const data = ref({})
const showTransitionRuleForm = ref(false)
const showTransitionRuleMenu = ref(false)
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

function openTransitionRuleFromMenu() {
  showTransitionRuleMenu.value = false
  openTransitionRuleForm()
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

.transitionRuleText {
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
