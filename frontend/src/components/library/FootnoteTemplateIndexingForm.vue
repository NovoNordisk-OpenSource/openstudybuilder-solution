<template>
  <TemplateIndexingForm
    ref="baseForm"
    :form="form"
    :template="template"
    @emit-form="updateForm"
  >
    <template #templateIndexFields>
      <NotApplicableField
        :checked="
          template &&
          (!template.activity_groups || !template.activity_groups.length)
        "
        :clean-function="() => (localForm.activity_group = null)"
      >
        <template #mainField="{ notApplicable }">
          <v-row>
            <v-col cols="11">
              <v-autocomplete
                v-model="localForm.activity_group"
                :label="$t('FootnoteTemplateForm.group')"
                data-cy="template-activity-group"
                :items="groups"
                item-title="name"
                item-value="uid"
                clearable
                :disabled="notApplicable"
                :rules="[
                  (value) => formRules.requiredIfNotNA(value, notApplicable),
                ]"
                @update:model-value="setSubGroups"
              />
            </v-col>
          </v-row>
        </template>
      </NotApplicableField>
      <NotApplicableField
        :checked="
          template &&
          (!template.activity_subgroups || !template.activity_subgroups.length)
        "
        :clean-function="() => (localForm.activity_subgroups = null)"
      >
        <template #mainField="{ notApplicable }">
          <v-row>
            <v-col cols="11">
              <v-autocomplete
                v-model="localForm.activity_subgroups"
                :label="$t('FootnoteTemplateForm.sub_group')"
                data-cy="template-activity-sub-group"
                :items="subGroups"
                item-title="name"
                item-value="uid"
                clearable
                multiple
                :disabled="notApplicable"
                :rules="[
                  (value) => formRules.requiredIfNotNA(value, notApplicable),
                ]"
                @update:model-value="setActivities"
              />
            </v-col>
          </v-row>
        </template>
      </NotApplicableField>
      <NotApplicableField
        :checked="
          template && (!template.activities || !template.activities.length)
        "
        :clean-function="() => (localForm.activities = null)"
      >
        <template #mainField="{ notApplicable }">
          <v-row>
            <v-col cols="11">
              <v-autocomplete
                v-model="localForm.activities"
                :label="$t('FootnoteTemplateForm.activity')"
                data-cy="template-activity-activity"
                :items="activities"
                item-title="name"
                return-object
                clearable
                multiple
                :disabled="notApplicable"
                :rules="[
                  (value) => formRules.requiredIfNotNA(value, notApplicable),
                ]"
              />
            </v-col>
          </v-row>
        </template>
      </NotApplicableField>
    </template>
  </TemplateIndexingForm>
</template>

<script setup>
import activitiesApi from '@/api/activities'
import NotApplicableField from '@/components/tools/NotApplicableField.vue'
import TemplateIndexingForm from './TemplateIndexingForm.vue'
import { ref, watch, inject } from 'vue'

const formRules = inject('formRules')
const baseForm = ref()

const props = defineProps({
  form: {
    type: Object,
    default: null,
  },
  template: {
    type: Object,
    default: null,
  },
})

const activities = ref([])
const groups = ref([])
const subGroups = ref([])
const localForm = ref({ ...props.form })

watch(
  () => props.template,
  async (value) => {
    if (value && value.activity_groups && value.activity_groups.length) {
      if (!groups.value.length) {
        const resp = await activitiesApi.getGroups()
        groups.value = resp.data.items
      }
      const activityGroupUid =
        typeof props.template.activity_groups[0] !== 'string'
          ? props.template.activity_groups[0].uid
          : props.template.activity_groups[0]
      localForm.value.activity_group = activityGroupUid
      await setSubGroups(localForm.value.activity_group, true)
      if (!localForm.value.activity_subgroups) {
        localForm.value.activity_subgroups = value.activity_subgroups
      }
      const subgroupUids = localForm.value.activity_subgroups.map((g) => g.uid)
      setActivities(subgroupUids, true)
      if (!localForm.value.activities) {
        localForm.value.activities = value.activities
      }
    }
  }
)

if (!groups.value.length) {
  activitiesApi.getGroups({ page_size: 0 }).then((resp) => {
    groups.value = resp.data.items
  })
}

function updateForm(indications) {
  localForm.value = { ...localForm.value, ...indications }
}

function preparePayload() {
  const result = {}
  Object.assign(result, baseForm.value.preparePayload())
  if (localForm.value.activity_group) {
    result.activity_group_uids = [localForm.value.activity_group]
  } else {
    result.activity_group_uids = []
  }
  if (
    localForm.value.activity_subgroups &&
    localForm.value.activity_subgroups.length
  ) {
    result.activity_subgroup_uids = []
    for (const item of localForm.value.activity_subgroups) {
      const itemUid = typeof item !== 'string' ? item.uid : item
      result.activity_subgroup_uids.push(itemUid)
    }
  } else {
    result.activity_subgroup_uids = []
  }
  if (localForm.value.activities) {
    result.activity_uids = localForm.value.activities.map((item) => item.uid)
  } else {
    result.activity_uids = []
  }
  return result
}

async function setSubGroups(group, noSubgroupReset) {
  if (group) {
    const resp = await activitiesApi.getSubGroups(group)
    subGroups.value = resp.data.items
  }
  if (!noSubgroupReset) {
    localForm.value.activity_subgroups = []
    localForm.value.activities = []
  }
}

function setActivities(subgroupUids) {
  activities.value = []
  for (const sg of subgroupUids) {
    activitiesApi.getSubGroupActivities(sg).then((resp) => {
      activities.value = activities.value.concat(resp.data.items)
    })
  }
}

defineExpose({
  preparePayload,
})
</script>
