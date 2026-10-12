<template>
  <div :id="cardId" class="rule-card pa-5">
    <div class="field-label mb-0">
      {{ t('DataSupplierView.RulesManager.rule_name') }}
    </div>
    <div class="d-flex align-center flex-wrap" style="gap: 16px">
      <v-text-field
        v-model="ruleName"
        density="comfortable"
        variant="outlined"
        :hide-details="!(showValidationError && !ruleName)"
        :error="showValidationError && !ruleName"
        :error-messages="
          showValidationError && !ruleName
            ? [t('DataSupplierView.RulesManager.rule_name_required')]
            : []
        "
        class="rule-name-select"
        :disabled="readOnly"
        data-cy="rule-name"
      />

      <v-btn
        variant="elevated"
        color="error"
        class="remove-btn ml-auto"
        :disabled="readOnly"
        data-cy="remove-rule"
        @click="onRemove"
      >
        {{ t('_global.remove') }}
      </v-btn>
    </div>

    <v-divider class="my-4" />

    <div class="text-body-medium font-weight-medium text-medium-emphasis mb-2">
      {{ t('DataSupplierView.RulesManager.activity_mapping_section') }}
    </div>

    <div
      v-if="showValidationError && !hasGroupings"
      class="text-error text-caption mb-2"
      data-cy="activity-groupings-error"
    >
      {{ t('DataSupplierView.RulesManager.activity_groupings_required') }}
    </div>

    <v-row v-if="groupings.length" no-gutters class="mb-1">
      <v-col cols="12" md="4" class="pr-2">
        <div class="field-label">
          {{ t('DataSupplierView.RulesManager.activity_groups') }}
        </div>
      </v-col>
      <v-col cols="12" md="4" class="px-2">
        <div class="field-label">
          {{ t('DataSupplierView.RulesManager.activity_subgroups') }}
        </div>
      </v-col>
      <v-col cols="12" md="3" class="px-2">
        <div class="field-label">
          {{ t('DataSupplierView.RulesManager.activities') }}
        </div>
      </v-col>
      <v-col cols="12" md="1" />
    </v-row>

    <v-row
      v-for="grouping in groupings"
      :key="grouping.id"
      no-gutters
      align="center"
      class="grouping-row pa-2 mb-3"
    >
      <v-col cols="12" md="4" class="pr-2">
        <v-select
          v-model="grouping.activity_group_uid"
          :items="activityGroups"
          item-title="name"
          item-value="uid"
          density="comfortable"
          variant="outlined"
          hide-details
          :disabled="readOnly"
          @update:model-value="onGroupChange(grouping)"
        />
      </v-col>
      <v-col cols="12" md="4" class="px-2">
        <v-select
          v-model="grouping.activity_subgroup_uid"
          :items="grouping.subGroups"
          item-title="name"
          item-value="uid"
          density="comfortable"
          variant="outlined"
          hide-details
          :disabled="readOnly || !grouping.activity_group_uid"
          @update:model-value="onSubgroupChange(grouping)"
        />
      </v-col>
      <v-col cols="12" md="3" class="px-2">
        <v-select
          v-model="grouping.activity_uids"
          :items="grouping.activities"
          item-title="name"
          item-value="uid"
          density="comfortable"
          variant="outlined"
          hide-details
          multiple
          :disabled="readOnly || !grouping.activity_subgroup_uid"
        >
          <template #prepend-item>
            <v-list-item
              data-cy="select-all-activities"
              :title="t('_global.select_all')"
              @click="toggleSelectAllActivities(grouping)"
            >
              <template #prepend>
                <v-checkbox-btn
                  :model-value="isAllActivitiesSelected(grouping)"
                  :indeterminate="isSomeActivitiesSelected(grouping)"
                />
              </template>
            </v-list-item>
            <v-divider class="mt-2" />
          </template>
          <template #selection="{ index }">
            <span v-if="index === 0" class="text-truncate">
              {{ activitySummary(grouping) }}
            </span>
          </template>
        </v-select>
      </v-col>
      <v-col cols="12" md="1" class="d-flex justify-center">
        <v-btn
          icon
          variant="text"
          size="small"
          :disabled="readOnly"
          data-cy="remove-grouping"
          @click="removeGrouping(grouping)"
        >
          <v-icon>mdi-minus-circle-outline</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ t('_global.remove') }}
          </v-tooltip>
        </v-btn>
      </v-col>
    </v-row>

    <v-btn
      variant="outlined"
      color="nnBaseBlue"
      prepend-icon="mdi-plus"
      class="mt-2"
      :disabled="readOnly"
      data-cy="add-grouping"
      @click="addGrouping"
    >
      {{ t('DataSupplierView.RulesManager.add_grouping') }}
    </v-btn>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import activitiesApi from '@/api/activities'
import dataSupplierRulesApi from '@/api/dataSupplierRules'

const { t } = useI18n()

const props = defineProps({
  rule: {
    type: Object,
    default: null,
  },
  typeUid: {
    type: String,
    required: true,
  },
  activityGroups: {
    type: Array,
    default: () => [],
  },
  readOnly: {
    type: Boolean,
    default: false,
  },
  cardId: {
    type: String,
    default: null,
  },
})

const emit = defineEmits(['removed', 'saved'])

const uid = ref(props.rule?.uid || null)
const ruleName = ref(props.rule?.name || '')
const groupings = ref([])
let groupingSeq = 0

function newGrouping(seed = {}) {
  return {
    id: `g-${groupingSeq++}`,
    activity_group_uid: seed.activity_group_uid || null,
    activity_subgroup_uid: seed.activity_subgroup_uid || null,
    activity_uids: seed.activity_uids || [],
    subGroups: [],
    activities: [],
  }
}

function isAllActivitiesSelected(grouping) {
  return (
    grouping.activities.length > 0 &&
    grouping.activity_uids.length === grouping.activities.length
  )
}

function isSomeActivitiesSelected(grouping) {
  return (
    grouping.activity_uids.length > 0 &&
    grouping.activity_uids.length < grouping.activities.length
  )
}

function toggleSelectAllActivities(grouping) {
  grouping.activity_uids = isAllActivitiesSelected(grouping)
    ? []
    : grouping.activities.map((a) => a.uid)
}

function activitySummary(grouping) {
  const names = grouping.activity_uids
    .map((u) => grouping.activities.find((a) => a.uid === u)?.name)
    .filter(Boolean)
  if (!names.length) {
    return `${grouping.activity_uids.length}`
  }
  return names.join(', ')
}

async function loadSubGroups(grouping) {
  if (!grouping.activity_group_uid) {
    grouping.subGroups = []
    return
  }
  const resp = await activitiesApi.getSubGroups(grouping.activity_group_uid)
  grouping.subGroups = resp.data.items
}

async function loadActivities(grouping) {
  if (!grouping.activity_group_uid || !grouping.activity_subgroup_uid) {
    grouping.activities = []
    return
  }
  const resp = await activitiesApi.getSubGroupActivities(
    grouping.activity_subgroup_uid,
    grouping.activity_group_uid
  )
  grouping.activities = resp.data.items
}

function groupingsFromRule(rule) {
  if (!rule?.activity_groupings?.length) {
    return []
  }
  const byPair = new Map()
  for (const g of rule.activity_groupings) {
    const key = `${g.activity_group_uid}::${g.activity_subgroup_uid}`
    if (!byPair.has(key)) {
      byPair.set(
        key,
        newGrouping({
          activity_group_uid: g.activity_group_uid,
          activity_subgroup_uid: g.activity_subgroup_uid,
          activity_uids: [],
        })
      )
    }
    if (g.activity_uid) {
      byPair.get(key).activity_uids.push(g.activity_uid)
    }
  }
  return Array.from(byPair.values())
}

function buildActivityGroupings() {
  const result = []
  for (const g of groupings.value) {
    if (!g.activity_group_uid || !g.activity_subgroup_uid) {
      continue
    }
    for (const activityUid of g.activity_uids) {
      result.push({
        activity_uid: activityUid,
        activity_group_uid: g.activity_group_uid,
        activity_subgroup_uid: g.activity_subgroup_uid,
      })
    }
  }
  return result
}

const showValidationError = ref(false)
const hasGroupings = computed(() => buildActivityGroupings().length > 0)

function currentTypeUid() {
  return props.typeUid
}

const canPersist = computed(() => Boolean(ruleName.value) && hasGroupings.value)

function validate() {
  const valid = Boolean(ruleName.value) && hasGroupings.value
  showValidationError.value = !valid
  return valid
}

async function save(overrideTypeUid) {
  if (!validate() || !canPersist.value) {
    return false
  }
  const finalTypeUid =
    overrideTypeUid !== undefined ? overrideTypeUid : currentTypeUid()
  if (!uid.value) {
    const payload = {
      name: ruleName.value,
      activity_groupings: buildActivityGroupings(),
      data_supplier_type_uid: finalTypeUid,
    }
    const resp = await dataSupplierRulesApi.create(payload)
    uid.value = resp.data.uid
  } else {
    const payload = {
      name: ruleName.value,
      activity_groupings: buildActivityGroupings(),
      data_supplier_type_uid: finalTypeUid === null ? '' : finalTypeUid,
      change_description: t('DataSupplierView.RulesManager.change_description'),
    }
    await dataSupplierRulesApi.update(uid.value, payload)
  }
  emit('saved')
  return true
}

async function onGroupChange(grouping) {
  grouping.activity_subgroup_uid = null
  grouping.activity_uids = []
  grouping.activities = []
  await loadSubGroups(grouping)
}

async function onSubgroupChange(grouping) {
  grouping.activity_uids = []
  await loadActivities(grouping)
}

function addGrouping() {
  groupings.value.push(newGrouping())
}

function removeGrouping(grouping) {
  groupings.value = groupings.value.filter((g) => g.id !== grouping.id)
}

function onRemove() {
  emit('removed', uid.value)
}

defineExpose({ save, validate, uid })

onMounted(async () => {
  groupings.value = groupingsFromRule(props.rule)
  if (!groupings.value.length) {
    groupings.value.push(newGrouping())
  }
  await Promise.all(
    groupings.value.map(async (g) => {
      await loadSubGroups(g)
      await loadActivities(g)
    })
  )
})
</script>

<style scoped>
.rule-card {
  position: relative;
  background-color: #fafafa;
  border: 1px solid #e0e0e0;
  border-radius: 10px;
}
.remove-btn {
  flex-shrink: 0;
}
.rule-name-select {
  max-width: 480px;
  background-color: white;
}
.grouping-row {
  background-color: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
}
.field-label {
  font-size: 0.8rem;
  color: rgba(0, 0, 0, 0.6);
  margin-bottom: 4px;
}
</style>
