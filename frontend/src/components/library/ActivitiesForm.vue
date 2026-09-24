<template>
  <SimpleFormDialog
    ref="formRef"
    :title="title"
    :help-items="helpItems"
    :open="open"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.library_name"
              :label="$t('_global.library')"
              disabled
            />
          </v-col>
        </v-row>
        <v-card position="relative" class="sub-v-card">
          <v-card-title style="position: relative">
            {{ $t('ActivityForms.activity_groupings') }}
          </v-card-title>
          <v-btn
            variant="outlined"
            color="nnBaseBlue"
            position="absolute"
            location="top right"
            icon="mdi-plus"
            size="x-small"
            @click="addGrouping"
          />
          <v-card-text>
            <v-card
              v-for="(grouping, index) in form.activity_groupings"
              :key="index"
              class="sub-v-card"
            >
              <v-card-text style="position: relative">
                <div data-cy="activityform-activity-group-class">
                  <v-autocomplete
                    v-model="form.activity_groupings[index].activity_group_uid"
                    :label="$t('ActivityForms.activity_group')"
                    data-cy="activityform-activity-group-dropdown"
                    :items="activitiesStore.activityGroups"
                    item-title="name"
                    item-value="uid"
                    :rules="[formRules.required]"
                    clearable
                  />
                </div>
                <div data-cy="activityform-activity-subgroup-class">
                  <v-autocomplete
                    v-model="
                      form.activity_groupings[index].activity_subgroup_uid
                    "
                    :label="$t('ActivityForms.activity_subgroup')"
                    data-cy="activityform-activity-subgroup-dropdown"
                    :items="activitiesStore.activitySubGroups"
                    item-title="name"
                    item-value="uid"
                    clearable
                    :rules="[formRules.required]"
                  />
                </div>
              </v-card-text>
              <v-btn
                v-if="index > 0"
                color="error"
                position="absolute"
                location="top right"
                icon="mdi-delete-outline"
                size="x-small"
                @click="removeGrouping(index)"
              />
            </v-card>
          </v-card-text>
        </v-card>
        <v-row data-cy="activityform-activity-name-class">
          <v-col>
            <v-text-field
              v-model="form.name"
              :label="$t('ActivityForms.activity_name')"
              data-cy="activityform-activity-name-field"
              :rules="[formRules.required]"
              :spellcheck="false"
              clearable
            />
          </v-col>
        </v-row>
        <SentenceCaseNameField
          v-model="form.name_sentence_case"
          :name="form.name"
        />
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.nci_concept_id"
              :label="$t('ActivityForms.nci_concept_id')"
              data-cy="activityform-nci-concept-id-field"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.nci_concept_name"
              :label="$t('ActivityForms.nci_concept_name')"
              data-cy="activityform-nci-concept-name-field"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-combobox
              v-model="form.synonyms"
              :items="form.synonyms"
              :label="$t('ActivityForms.synonyms')"
              data-cy="activityform-synonyms-field"
              clearable
              multiple
              chips
            >
              <template #selection="{ attrs, selected }">
                <v-chip v-bind="attrs" :model-value="selected" />
              </template>
            </v-combobox>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="3">
            <v-checkbox
              v-model="form.is_data_collected"
              :label="$t('ActivityForms.is_data_collected')"
              data-cy="activityform-datacollection-checkbox"
            />
          </v-col>
          <v-col>
            <v-checkbox
              v-model="form.is_multiple_selection_allowed"
              :label="$t('ActivityForms.multiple_instances')"
              data-cy="activityform-multipleselection-checkbox"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.abbreviation"
              :label="$t('ActivityForms.abbreviation')"
              data-cy="activityform-abbreviation-field"
              :error-messages="errors"
              clearable
            />
          </v-col>
        </v-row>
        <v-row data-cy="activityform-definition-class">
          <v-col>
            <v-textarea
              v-model="form.definition"
              :label="$t('ActivityForms.definition')"
              data-cy="activityform-definition-field"
              clearable
              auto-grow
              rows="1"
            />
          </v-col>
        </v-row>
        <v-row v-if="editing">
          <v-col>
            <label class="v-label">{{
              $t('ActivityForms.reason_for_change')
            }}</label>
            <v-textarea
              v-model="form.change_description"
              :rules="[formRules.required]"
              clearable
              auto-grow
              rows="1"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import _isEmpty from 'lodash/isEmpty'
import activities from '@/api/activities'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import SentenceCaseNameField from '@/components/tools/SentenceCaseNameField.vue'
import constants from '@/constants/libraries.js'
import statuses from '@/constants/statuses.js'
import { useFormStore } from '@/stores/form'
import { useLibraryActivitiesStore } from '@/stores/library-activities'
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const formStore = useFormStore()
const activitiesStore = useLibraryActivitiesStore()
const notificationHub = inject('notificationHub')
const formRules = inject('formRules')
const emit = defineEmits(['close'])
const formRef = ref()
const observer = ref()

const props = defineProps({
  editedActivity: {
    type: Object,
    default: null,
  },
  open: Boolean,
})

const form = ref({
  library_name: constants.LIBRARY_SPONSOR,
  activity_groupings: [{}],
  is_data_collected: true,
  is_multiple_selection_allowed: true,
})
const errors = ref([])
const helpItems = [
  'ActivityForms.activity_group',
  'ActivityForms.activity_subgroup',
  'ActivityForms.name',
  'ActivityForms.nci_concept_id',
  'ActivityForms.is_data_collected',
  'ActivityForms.abbreviation',
  'ActivityForms.definition',
  'ActivityForms.activity_name',
]
const editing = ref(false)

onMounted(() => {
  // When editing, filter sub-groups to only show Final status
  if (!_isEmpty(props.editedActivity)) {
    // add the existing group and subgroup UIDs to the filter so they show up in the dropdowns
    const usedGroupingUIDs = []
    for (const grouping of props.editedActivity.activity_groupings) {
      usedGroupingUIDs.push(grouping.activity_group_uid)
      usedGroupingUIDs.push(grouping.activity_subgroup_uid)
    }
    const statusFilter = {
      status: { v: [statuses.FINAL], op: 'eq' },
      uid: { v: usedGroupingUIDs, op: 'eq' },
    }
    activitiesStore.getGroupsAndSubgroups(statusFilter, 'or').then(() => {
      // Fetch full activity object and initialize form after data is loaded
      activities
        .getObject('activities', props.editedActivity.uid)
        .then((resp) => {
          initForm(resp.data)
        })
    })
  } else {
    const statusFilter = {
      status: { v: [statuses.FINAL], op: 'eq' },
    }
    activitiesStore.getGroupsAndSubgroups(statusFilter)
  }
})

const title = computed(() => {
  return !_isEmpty(props.editedActivity)
    ? t('ActivityForms.edit_activity')
    : t('ActivityForms.add_activity')
})

watch(
  () => props.editedActivity,
  (value) => {
    if (!_isEmpty(value)) {
      // Fetch sub-groups with Final status filter when editing
      const usedGroupingUIDs = []
      for (const grouping of value.activity_groupings) {
        usedGroupingUIDs.push(grouping.activity_group_uid)
        usedGroupingUIDs.push(grouping.activity_subgroup_uid)
      }
      const statusFilter = {
        status: { v: [statuses.FINAL], op: 'eq' },
        uid: { v: usedGroupingUIDs, op: 'eq' },
      }
      activitiesStore.getGroupsAndSubgroups(statusFilter, 'or').then(() => {
        activities.getObject('activities', value.uid).then((resp) => {
          initForm(resp.data)
        })
      })
    } else {
      const statusFilter = {
        status: { v: [statuses.FINAL], op: 'eq' },
      }
      activitiesStore.getGroupsAndSubgroups(statusFilter)
    }
  }
)

watch(
  () => props.open,
  () => {
    if (props.open && _isEmpty(props.editedActivity)) {
      formStore.save(form.value)
    }
  }
)

function initForm(value) {
  editing.value = true
  form.value = {
    name: value.name,
    name_sentence_case: value.name_sentence_case,
    nci_concept_id: value.nci_concept_id,
    nci_concept_name: value.nci_concept_name,
    synonyms: value.synonyms,
    is_data_collected: value.is_data_collected,
    is_multiple_selection_allowed: value.is_multiple_selection_allowed,
    definition: value.definition,
    abbreviation: value.abbreviation,
    change_description: t('_global.work_in_progress'),
    library_name: value.library_name,
    activity_groupings: [{}],
  }
  if (!_isEmpty(value)) {
    form.value.activity_groupings = value.activity_groupings
  }
  formStore.save(form.value)
}

async function cancel() {
  if (!formStore.isEqual(form.value)) {
    const options = {
      type: 'warning',
      cancelLabel: t('_global.cancel'),
      agreeLabel: t('_global.continue'),
    }
    if (!(await formRef.value.confirm(t('_global.cancel_changes'), options))) {
      return
    }
  }
  close()
}

async function close() {
  observer.value.reset()
  notificationHub.clearErrors()
  form.value = {
    library_name: constants.LIBRARY_SPONSOR,
    activity_groupings: [{}],
    is_data_collected: true,
    is_multiple_selection_allowed: true,
  }
  editing.value = false
  formStore.reset()
  emit('close')
}

async function submit() {
  notificationHub.clearErrors()

  if (!props.editedActivity) {
    activities.create(form.value, 'activities').then(
      () => {
        notificationHub.add({
          msg: t('ActivityForms.activity_created'),
        })
        close()
      },
      () => {
        formRef.value.working = false
      }
    )
  } else {
    activities
      .update(props.editedActivity.uid, form.value, {}, 'activities')
      .then(
        () => {
          notificationHub.add({
            msg: t('ActivityForms.activity_updated'),
          })
          close()
        },
        () => {
          formRef.value.working = false
        }
      )
  }
}

function addGrouping() {
  form.value.activity_groupings.push({})
}

function removeGrouping(index) {
  form.value.activity_groupings.splice(index, 1)
}
</script>
<style>
.sub-v-card {
  margin-bottom: 25px;
}
</style>
