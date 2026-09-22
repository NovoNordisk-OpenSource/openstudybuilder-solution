<template>
  <SimpleFormDialog
    ref="formRef"
    :title="$t('ActivityInstanceLinking.title')"
    :open="open"
    max-width="900px"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-alert type="info" variant="tonal" class="mb-4">
          {{ $t('ActivityInstanceLinking.description') }}
        </v-alert>

        <v-card
          v-if="loading"
          class="d-flex justify-center align-center pa-8"
          flat
        >
          <v-progress-circular indeterminate color="primary" />
        </v-card>

        <template v-else>
          <v-card v-if="previousInstances.length > 0" class="sub-v-card">
            <v-card-title>
              {{ $t('ActivityInstanceLinking.current_linking_title') }}
              <span class="text-caption text-medium-emphasis ml-2">
                ({{ $t('ActivityInstanceLinking.latest_activity_version') }}:
                {{ activity?.version }})
              </span>
            </v-card-title>
            <v-card-text>
              <div class="d-flex ga-4 mb-2">
                <v-chip
                  size="small"
                  color="success"
                  variant="flat"
                  class="text-white"
                >
                  {{ $t('ActivityInstanceLinking.legend_current') }}
                  <v-tooltip activator="parent" location="top">
                    {{ $t('ActivityInstanceLinking.legend_current_tooltip') }}
                  </v-tooltip>
                </v-chip>
                <v-chip
                  size="small"
                  color="warning"
                  variant="flat"
                  class="text-white"
                >
                  {{ $t('ActivityInstanceLinking.legend_previous') }}
                  <v-tooltip activator="parent" location="top">
                    {{ $t('ActivityInstanceLinking.legend_previous_tooltip') }}
                  </v-tooltip>
                </v-chip>
                <v-chip
                  size="small"
                  color="error"
                  variant="flat"
                  class="text-white"
                >
                  {{ $t('ActivityInstanceLinking.legend_older') }}
                  <v-tooltip activator="parent" location="top">
                    {{ $t('ActivityInstanceLinking.legend_older_tooltip') }}
                  </v-tooltip>
                </v-chip>
                <v-chip
                  size="small"
                  color="info"
                  variant="flat"
                  class="text-white"
                >
                  {{ $t('ActivityInstanceLinking.legend_other_activity') }}
                  <v-tooltip activator="parent" location="top">
                    {{
                      $t(
                        'ActivityInstanceLinking.legend_other_activity_tooltip'
                      )
                    }}
                  </v-tooltip>
                </v-chip>
              </div>
              <v-data-table
                :headers="summaryHeaders"
                :items="instanceVersionSummary"
                item-value="uid"
                density="compact"
                show-expand
                :items-per-page="-1"
                hide-default-footer
              >
                <template #[`item.name`]="{ item }">
                  <span :class="`text-${item.color} font-weight-medium`">{{
                    item.name
                  }}</span>
                </template>
                <template #[`item.linkedVersion`]="{ item }">
                  <v-chip
                    size="small"
                    :color="item.color"
                    variant="flat"
                    class="text-white"
                  >
                    {{ item.linkedVersion || '—' }}
                  </v-chip>
                </template>
                <template #[`item.actions`]="{ item }">
                  <v-btn
                    v-if="item.fromOtherActivity"
                    icon="mdi-delete"
                    size="x-small"
                    variant="text"
                    color="error"
                    @click="removeMovedInstance(item.uid)"
                  >
                    <v-icon size="small">mdi-delete</v-icon>
                    <v-tooltip activator="parent" location="top">
                      {{ $t('ActivityInstanceLinking.remove_moved_instance') }}
                    </v-tooltip>
                  </v-btn>
                </template>
                <template #expanded-row="{ columns, item }">
                  <tr>
                    <td :colspan="columns.length" class="pa-2">
                      <div class="ml-8">
                        <div
                          v-if="item.fromOtherActivity"
                          class="d-flex align-center py-1"
                        >
                          <span class="text-body-2">
                            {{
                              $t('ActivityInstanceLinking.currently_linked_to')
                            }}
                            <strong>{{ item.sourceActivityName }}</strong>
                          </span>
                        </div>
                        <div
                          v-if="
                            item.groupings.length === 0 &&
                            !item.fromOtherActivity
                          "
                          class="text-medium-emphasis text-body-2 py-1"
                        >
                          {{ $t('ActivityInstanceLinking.no_groupings') }}
                        </div>
                        <div
                          v-for="(grouping, gIdx) in item.groupings"
                          :key="gIdx"
                          class="d-flex align-center py-1"
                        >
                          <v-icon
                            v-if="grouping.removed"
                            icon="mdi-alert"
                            color="error"
                            size="small"
                            class="mr-2"
                          />
                          <span :class="{ 'text-error': grouping.removed }">
                            {{ grouping.activity_group_name }}
                            &mdash;
                            {{ grouping.activity_subgroup_name }}
                          </span>
                          <v-chip
                            v-if="grouping.removed"
                            size="x-small"
                            color="error"
                            variant="tonal"
                            class="ml-2"
                          >
                            {{ $t('ActivityInstanceLinking.grouping_removed') }}
                          </v-chip>
                        </div>
                      </div>
                    </td>
                  </tr>
                </template>
              </v-data-table>
            </v-card-text>
          </v-card>

          <v-alert
            v-if="unassignedInstances.length > 0"
            type="warning"
            class="text-white mb-4"
          >
            {{ $t('ActivityInstanceLinking.unassigned_warning') }}
            <ul class="mt-1">
              <li v-for="inst in unassignedInstances" :key="inst.uid">
                {{ inst.name }}
              </li>
            </ul>
          </v-alert>

          <v-card
            v-if="form.groupings.length === 0"
            flat
            class="text-center pa-4"
          >
            <v-card-text class="text-grey">
              {{ $t('ActivityInstanceLinking.no_groupings') }}
            </v-card-text>
          </v-card>

          <div class="d-flex justify-end mb-2">
            <v-btn
              color="primary"
              variant="outlined"
              prepend-icon="mdi-plus"
              @click="showInstancePicker = true"
            >
              {{ $t('ActivityInstanceLinking.move_from_other_activities') }}
            </v-btn>
          </div>

          <ActivityInstancePickerDialog
            :open="showInstancePicker"
            :exclude-uids="previousInstances.map((i) => i.uid)"
            @close="showInstancePicker = false"
            @select="onInstancesPicked"
          />

          <v-card class="sub-v-card">
            <v-card-title>
              {{ $t('ActivityForms.activity_groupings') }}
            </v-card-title>
            <v-card-text>
              <v-card
                v-for="(grouping, index) in form.groupings"
                :key="index"
                class="sub-v-card"
              >
                <v-card-text style="position: relative">
                  <div class="mb-2">
                    <span class="text-caption text-medium-emphasis">
                      {{ $t('ActivityForms.activity_group') }}
                    </span>
                    <div class="text-body-1">
                      {{ grouping.activity_group_name }}
                    </div>
                  </div>
                  <div class="mb-2">
                    <span class="text-caption text-medium-emphasis">
                      {{ $t('ActivityForms.activity_subgroup') }}
                    </span>
                    <div class="text-body-1">
                      {{ grouping.activity_subgroup_name }}
                    </div>
                  </div>
                  <div>
                    <v-autocomplete
                      v-model="form.groupings[index].activity_instance_uids"
                      :label="$t('ActivityInstanceLinking.activity_instance')"
                      :items="previousInstances"
                      item-title="name"
                      item-value="uid"
                      multiple
                      chips
                      closable-chips
                      clearable
                    />
                  </div>
                </v-card-text>
              </v-card>
            </v-card-text>
          </v-card>
        </template>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import activitiesApi from '@/api/activities'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import ActivityInstancePickerDialog from '@/components/library/ActivityInstancePickerDialog.vue'
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const emit = defineEmits(['close'])
const formRef = ref()
const observer = ref()

const summaryHeaders = computed(() => [
  {
    title: t('ActivityInstanceLinking.activity_instance'),
    key: 'name',
    sortable: false,
  },
  {
    title: t('ActivityInstanceLinking.linked_activity_version'),
    key: 'linkedVersion',
    sortable: false,
  },
  { title: '', key: 'actions', sortable: false, width: '60px' },
  { title: '', key: 'data-table-expand' },
])

const props = defineProps({
  activity: {
    type: Object,
    default: null,
  },
  open: Boolean,
})

const loading = ref(false)
const showInstancePicker = ref(false)
const movedInstances = ref(new Map())
const previousInstances = ref([])
const previousGroupingInstanceMap = ref(new Map())
const allVersionsData = ref([])
const form = ref({
  groupings: [],
})

const instanceVersionSummary = computed(() => {
  if (!previousInstances.value.length) return []
  const currentVersion = props.activity?.version
  // The second entry (if any) is the previous final version
  const previousFinalVersion =
    allVersionsData.value.length > 1 ? allVersionsData.value[1].version : null

  // Build a set of current activity grouping keys
  const currentGroupingKeys = new Set(
    (props.activity?.activity_groupings || []).map(
      (g) => `${g.activity_group_uid}|${g.activity_subgroup_uid}`
    )
  )

  return previousInstances.value.map((inst) => {
    // Check if this instance was picked from another activity
    const moved = movedInstances.value.get(inst.uid)
    if (moved) {
      return {
        uid: inst.uid,
        name: inst.name,
        linkedVersion: null,
        color: 'info',
        isLinkedToCurrentVersion: false,
        fromOtherActivity: true,
        sourceActivityName: moved.activity_name,
        groupings: (moved.activity_groupings || []).map((g) => ({
          activity_group_uid: g.activity_group?.uid,
          activity_group_name: g.activity_group?.name,
          activity_subgroup_uid: g.activity_subgroup?.uid,
          activity_subgroup_name: g.activity_subgroup?.name,
          removed: false,
        })),
      }
    }

    let linkedVersion = null
    let instanceGroupings = []
    for (const versionEntry of allVersionsData.value) {
      const found = versionEntry.instances.find((i) => i.uid === inst.uid)
      if (found) {
        linkedVersion = versionEntry.version
        instanceGroupings = (found.groupings || []).map((g) => ({
          activity_group_uid: g.activity_group_uid,
          activity_group_name: g.activity_group_name,
          activity_subgroup_uid: g.activity_subgroup_uid,
          activity_subgroup_name: g.activity_subgroup_name,
          removed: !currentGroupingKeys.has(
            `${g.activity_group_uid}|${g.activity_subgroup_uid}`
          ),
        }))
        break
      }
    }

    let color = 'error' // older versions
    if (linkedVersion === currentVersion) {
      color = 'success'
    } else if (linkedVersion === previousFinalVersion) {
      color = 'warning'
    }

    return {
      uid: inst.uid,
      name: inst.name,
      linkedVersion,
      color,
      isLinkedToCurrentVersion: linkedVersion === currentVersion,
      fromOtherActivity: false,
      sourceActivityName: null,
      groupings: instanceGroupings,
    }
  })
})

const unassignedInstances = computed(() => {
  if (!previousInstances.value.length) return []
  const assignedUids = new Set()
  for (const row of form.value.groupings) {
    for (const uid of row.activity_instance_uids || []) {
      assignedUids.add(uid)
    }
  }
  return previousInstances.value.filter((inst) => !assignedUids.has(inst.uid))
})

onMounted(() => {
  if (props.activity && props.open) {
    initialize()
  }
})

watch(
  () => props.open,
  (newVal) => {
    if (newVal && props.activity) {
      initialize()
    }
  }
)

async function initialize() {
  loading.value = true
  try {
    // Fetch the previous final version's groupings to get available instances
    await fetchPreviousVersionInstances()

    // Initialize groupings from current activity
    initializeGroupings()
  } finally {
    loading.value = false
  }
}

async function fetchPreviousVersionInstances() {
  previousInstances.value = []
  previousGroupingInstanceMap.value = new Map()
  if (!props.activity?.uid) return

  const resp = await activitiesApi.getAllVersionsInstances(props.activity.uid)
  const allVersions = resp.data || []
  allVersionsData.value = allVersions

  // Try the current version first, then fall back to the most recent other version with instances
  const currentVersion = props.activity.version
  const currentVersionData = allVersions.find(
    (v) => v.version === currentVersion
  )
  const fallbackVersionData = allVersions.find(
    (v) => v.version !== currentVersion && v.instances.length > 0
  )

  const versionData =
    currentVersionData?.instances?.length > 0
      ? currentVersionData
      : fallbackVersionData

  if (!versionData || versionData.instances.length === 0) {
    return
  }

  const instanceMap = new Map()
  const groupingMap = new Map()

  for (const instance of versionData.instances) {
    instanceMap.set(instance.uid, {
      uid: instance.uid,
      name: instance.name,
      topic_code: instance.topic_code,
    })
    for (const grouping of instance.groupings || []) {
      const key = `${grouping.activity_group_uid}|${grouping.activity_subgroup_uid}`
      if (!groupingMap.has(key)) {
        groupingMap.set(key, [])
      }
      groupingMap.get(key).push(instance.uid)
    }
  }

  previousInstances.value = Array.from(instanceMap.values())
  previousGroupingInstanceMap.value = groupingMap
}

function initializeGroupings() {
  if (
    props.activity?.activity_groupings &&
    props.activity.activity_groupings.length > 0
  ) {
    form.value.groupings = props.activity.activity_groupings.map((g) => {
      const key = `${g.activity_group_uid}|${g.activity_subgroup_uid}`
      const preSelected = previousGroupingInstanceMap.value.get(key) || []
      return {
        activity_group_uid: g.activity_group_uid,
        activity_group_name: g.activity_group_name,
        activity_subgroup_uid: g.activity_subgroup_uid,
        activity_subgroup_name: g.activity_subgroup_name,
        activity_instance_uids: preSelected,
      }
    })
  } else {
    form.value.groupings = [{}]
  }
}

function onInstancesPicked(instances) {
  for (const inst of instances) {
    const alreadyExists = previousInstances.value.some(
      (p) => p.uid === inst.uid
    )
    if (!alreadyExists) {
      previousInstances.value.push({
        uid: inst.uid,
        name: inst.name,
        topic_code: inst.topic_code,
      })
      movedInstances.value.set(inst.uid, {
        activity_name: inst.activity_name,
        activity_groupings: inst.activity_groupings || [],
      })
    }
  }
}

function removeMovedInstance(uid) {
  movedInstances.value.delete(uid)
  previousInstances.value = previousInstances.value.filter(
    (inst) => inst.uid !== uid
  )
  for (const row of form.value.groupings) {
    if (row.activity_instance_uids) {
      row.activity_instance_uids = row.activity_instance_uids.filter(
        (id) => id !== uid
      )
    }
  }
}

async function cancel() {
  close()
}

function close() {
  if (observer.value) {
    observer.value.reset()
  }
  form.value = { groupings: [] }
  previousInstances.value = []
  previousGroupingInstanceMap.value = new Map()
  allVersionsData.value = []
  movedInstances.value = new Map()
  emit('close')
}

/**
 * Groups the form rows by instance and builds one groupings-update payload
 * per instance. Each instance payload contains all the group/subgroup
 * combinations the user assigned to it, all referencing the current activity.
 */
function buildInstancePayloads() {
  const activityUid = props.activity.uid
  const byInstance = new Map()

  for (const row of form.value.groupings) {
    if (!row.activity_instance_uids?.length) continue

    const grouping = {
      activity_group_uid: row.activity_group_uid,
      activity_subgroup_uid: row.activity_subgroup_uid,
      activity_uid: activityUid,
    }

    for (const instanceUid of row.activity_instance_uids) {
      if (!byInstance.has(instanceUid)) {
        byInstance.set(instanceUid, [])
      }
      byInstance.get(instanceUid).push(grouping)
    }
  }

  // Omit instances that are already linked to the current version
  // and whose grouping assignments have not changed
  const summaryMap = new Map(
    instanceVersionSummary.value.map((row) => [row.uid, row])
  )
  for (const instanceUid of byInstance.keys()) {
    const summary = summaryMap.get(instanceUid)
    if (summary?.isLinkedToCurrentVersion && !instanceHasChanges(instanceUid)) {
      byInstance.delete(instanceUid)
    }
  }

  return byInstance
}

/**
 * Checks whether a specific instance's grouping assignments changed
 * compared to the pre-selected state loaded from the API.
 */
function instanceHasChanges(instanceUid) {
  const originalKeys = new Set()
  for (const [key, uids] of previousGroupingInstanceMap.value) {
    if (uids.includes(instanceUid)) {
      originalKeys.add(key)
    }
  }

  const currentKeys = new Set()
  for (const row of form.value.groupings) {
    if ((row.activity_instance_uids || []).includes(instanceUid)) {
      const key = `${row.activity_group_uid}|${row.activity_subgroup_uid}`
      currentKeys.add(key)
    }
  }

  if (originalKeys.size !== currentKeys.size) return true
  for (const key of originalKeys) {
    if (!currentKeys.has(key)) return true
  }
  return false
}

async function submit() {
  notificationHub.clearErrors()

  const instancePayloads = buildInstancePayloads()

  if (instancePayloads.size === 0) {
    notificationHub.add({
      msg: t('ActivityInstanceLinking.update_success'),
    })
    close()
    return
  }

  try {
    const changeDescription = t(
      'ActivityInstanceLinking.change_description_default'
    )

    const items = []
    for (const [instanceUid, groupings] of instancePayloads) {
      items.push({
        activity_instance_uid: instanceUid,
        activity_groupings: groupings,
      })
    }

    await activitiesApi.batchUpdateInstanceGroupings({
      change_description: changeDescription,
      items,
    })

    notificationHub.add({
      msg: t('ActivityInstanceLinking.update_success'),
    })
    close()
  } catch {
    if (formRef.value) {
      formRef.value.working = false
    }
  }
}
</script>

<style>
.sub-v-card {
  margin-bottom: 25px;
}
</style>
