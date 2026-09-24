<template>
  <div class="activity-summary-container">
    <table class="activity-summary-table">
      <tbody>
        <!-- Dynamically create rows based on organized fields -->
        <tr v-for="(row, rowIndex) in organizedRows" :key="rowIndex">
          <td v-for="(field, cellIndex) in row" :key="cellIndex">
            <div class="summary-label">{{ field.label }}</div>
            <div class="summary-value">
              <!-- Special handling for specific field types -->
              <template v-if="field.key === 'status'">
                <StatusChip
                  v-if="field.value && field.value !== '-'"
                  :status="field.value"
                />
                <span v-else>-</span>
              </template>
              <template v-else-if="field.key === 'version'">
                <v-select
                  v-if="allVersions && allVersions.length"
                  :items="allVersions"
                  :model-value="field.value"
                  hide-details
                  class="version-select"
                  @update:model-value="$emit('version-change', $event)"
                ></v-select>
                <span v-else>{{ field.value }}</span>
              </template>
              <template v-else-if="field.key === 'nci_concept_id'">
                <NCIConceptLink
                  v-if="field.value && field.value !== '-'"
                  :concept-id="field.value"
                />
                <span v-else>-</span>
              </template>
              <template
                v-else-if="field.key === 'activity_name' && activityInfo"
              >
                <router-link
                  :to="{
                    name: 'ActivityOverview',
                    params: {
                      id: activityInfo.uid,
                      version: activityInfo.version,
                    },
                  }"
                  class="activity-link"
                >
                  <v-tooltip
                    v-if="showTooltip(field.value)"
                    location="top"
                    max-width="300"
                    :text="field.value"
                    interactive
                  >
                    <template #activator="{ props }">
                      <span v-bind="props">{{
                        field.value.substring(0, 50) + '...'
                      }}</span>
                    </template>
                  </v-tooltip>
                  <span v-else>{{ field.value }}</span>
                </router-link>
              </template>
              <template v-else>
                <v-tooltip
                  v-if="showTooltip(field.value)"
                  location="top"
                  max-width="300"
                  :text="field.value"
                  interactive
                >
                  <template #activator="{ props }">
                    <span v-bind="props">{{
                      field.value.substring(0, 50) + '...'
                    }}</span>
                  </template>
                </v-tooltip>
                <span v-else>{{ field.value }}</span>
              </template>
            </div>
          </td>
          <!-- Add empty cells if row has less than 5 items -->
          <td
            v-for="n in 5 - row.length"
            :key="`empty-${n}`"
            class="empty-cell"
          ></td>
        </tr>
      </tbody>
    </table>
    <div v-if="$slots.content || $slots.default" class="summary-content">
      <slot name="content">
        <slot></slot>
      </slot>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { computed, getCurrentInstance } from 'vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import NCIConceptLink from '@/components/tools/NCIConceptLink.vue'

const { t } = useI18n()
const instance = getCurrentInstance()
const $filters = instance.appContext.config.globalProperties.$filters

defineEmits(['version-change'])

const props = defineProps({
  activity: {
    type: Object,
    default: () => ({}),
  },
  allVersions: {
    type: Array,
    default: () => [],
  },
  showLibrary: {
    type: Boolean,
    default: true,
  },
  showNciConceptId: {
    type: Boolean,
    default: true,
  },
  showDataCollection: {
    type: Boolean,
    default: true,
  },
  showAbbreviation: {
    type: Boolean,
    default: true,
  },
  showAuthor: {
    type: Boolean,
    default: false,
  },
  showSynonyms: {
    type: Boolean,
    default: true,
  },
  activityGroupings: {
    type: Array,
    default: () => [],
  },
  usedStudies: {
    type: Array,
    default: () => [],
  },
})

function showTooltip(value) {
  return value && value.length > 50 && !value.includes(' ')
}

// Extract activity information from activity groupings
const activityInfo = computed(() => {
  if (!props.activityGroupings || props.activityGroupings.length === 0) {
    return null
  }

  const firstGrouping = props.activityGroupings[0]
  if (!firstGrouping.activity) {
    return null
  }

  return {
    uid: firstGrouping.activity.uid,
    name: firstGrouping.activity.name,
    version: firstGrouping.activity.version,
  }
})

// Organize fields into rows dynamically
const organizedRows = computed(() => {
  const fields = []

  // Always include these core fields
  fields.push({
    key: 'name',
    label: t('_global.sentence_case_name'),
    value: props.activity.name_sentence_case || props.activity.name || '-',
  })

  if (props.activity.display_name !== undefined) {
    fields.push({
      key: 'display_name',
      label: t('ActivityItemClassTable.display_name'),
      value: props.activity.display_name || '-',
    })
  }

  fields.push({
    key: 'start_date',
    label: t('_global.start_date'),
    value: props.activity.start_date
      ? $filters.date(props.activity.start_date)
      : 'None',
  })

  fields.push({
    key: 'end_date',
    label: t('_global.end_date'),
    value: props.activity.end_date
      ? $filters.date(props.activity.end_date)
      : 'None',
  })

  fields.push({
    key: 'status',
    label: t('_global.status'),
    value: props.activity.status || '-',
  })

  fields.push({
    key: 'version',
    label: t('_global.version'),
    value: props.activity.version || '-',
  })
  // Definition is always shown
  fields.push({
    key: 'definition',
    label: t('_global.definition'),
    value: props.activity.definition || '-',
  })

  // Synonyms
  if (props.showSynonyms) {
    fields.push({
      key: 'synonyms',
      label: t('ActivityTable.synonyms'),
      value:
        props.activity.synonyms && props.activity.synonyms.length > 0
          ? props.activity.synonyms.join(', ')
          : '-',
    })
  }

  // Conditionally add other fields
  if (props.showAbbreviation) {
    fields.push({
      key: 'abbreviation',
      label: t('_global.abbreviation'),
      value: props.activity.abbreviation || '-',
    })
  }

  if (props.showLibrary) {
    fields.push({
      key: 'library',
      label: t('_global.library'),
      value: props.activity.library_name || '-',
    })
  }

  if (props.showNciConceptId) {
    fields.push({
      key: 'nci_concept_id',
      label: t('ActivityForms.nci_concept_id'),
      value: props.activity.nci_concept_id || '-',
    })
  }

  if (props.showNciConceptId) {
    fields.push({
      key: 'nci_concept_name',
      label: t('ActivityForms.nci_concept_name'),
      value: props.activity.nci_concept_name || '-',
    })
  }

  if (props.showDataCollection) {
    fields.push({
      key: 'data_collection',
      label: t('ActivitySummary.data_collection'),
      value: $filters.yesno(props.activity.is_data_collected),
    })
  }

  fields.push({
    key: 'is_multiple_selection_allowed',
    label: t('ActivitySummary.multiple_instances_allowed'),
    value: $filters.yesno(props.activity.is_multiple_selection_allowed),
  })

  // Activity instance specific fields
  if (props.activity.is_legacy_usage !== undefined) {
    fields.push({
      key: 'legacy_usage',
      label: t('ActivityInstanceOverview.is_legacy_usage'),
      value: $filters.yesno(props.activity.is_legacy_usage),
    })
  }

  if (props.activity.adam_param_code !== undefined) {
    fields.push({
      key: 'adam_param_code',
      label: t('ActivityInstanceOverview.adam_code'),
      value: props.activity.adam_param_code || '-',
    })
  }

  if (props.activity.activity_instance_class !== undefined) {
    fields.push({
      key: 'activity_instance_class',
      label: t('ActivityInstanceOverview.activity_instance_class'),
      value: props.activity.activity_instance_class || '-',
    })
  }

  if (props.activity.is_required_for_activity !== undefined) {
    fields.push({
      key: 'required_for_activity',
      label: t('ActivityInstanceOverview.is_required_for_activity'),
      value: $filters.yesno(props.activity.is_required_for_activity),
    })
  }

  if (props.activity.is_default_selected_for_activity !== undefined) {
    fields.push({
      key: 'default_selected_for_activity',
      label: t('ActivityInstanceOverview.is_default_selected_for_activity'),
      value: $filters.yesno(props.activity.is_default_selected_for_activity),
    })
  }

  if (props.activity.topic_code !== undefined) {
    fields.push({
      key: 'topic_code',
      label: t('ActivityInstanceOverview.topic_code'),
      value: props.activity.topic_code || '-',
    })
  }

  if (props.activity.is_data_sharing !== undefined) {
    fields.push({
      key: 'data_sharing',
      label: t('ActivityInstanceOverview.is_data_sharing'),
      value: $filters.yesno(props.activity.is_data_sharing),
    })
  }

  if (
    props.activity.molecular_weight !== undefined &&
    props.activity.molecular_weight !== null
  ) {
    fields.push({
      key: 'molecular_weight',
      label: t('ActivityInstanceOverview.molecular_weight'),
      value: `${props.activity.molecular_weight} g/mol`,
    })
  }

  if (props.activity.activity_name !== undefined) {
    fields.push({
      key: 'activity_name',
      label: t('ActivityInstanceOverview.activity_name'),
      value: props.activity.activity_name || '-',
    })
  }

  if (props.showAuthor) {
    fields.push({
      key: 'author',
      label: t('_global.author'),
      value: props.activity.author_username || '-',
    })
  }

  // Domain specific field
  if (props.activity.domain_specific !== undefined) {
    fields.push({
      key: 'domain_specific',
      label: t('ActivityInstanceClassOverview.domain_specific'),
      value: props.activity.domain_specific || '-',
    })
  }

  // Hierarchy field
  if (props.activity.hierarchy_label !== undefined) {
    fields.push({
      key: 'hierarchy',
      label: t('ActivityInstanceClassOverview.hierarchy'),
      value: props.activity.hierarchy_label || '-',
    })
  }

  // Modified by field
  if (props.activity.modified_by !== undefined) {
    fields.push({
      key: 'modified_by',
      label: t('_global.modified_by'),
      value: props.activity.modified_by || '-',
    })
  }

  if (props.usedStudies) {
    fields.push({
      key: 'used_studies',
      label: t('StudyTable.id'),
      value: props.usedStudies.join(', ') || '-',
    })
  }

  // Organize fields into rows of 5
  const rows = []
  for (let i = 0; i < fields.length; i += 5) {
    rows.push(fields.slice(i, i + 5))
  }

  return rows
})
</script>

<!-- This needs to be set into a global place, color, fontsize etc -->
<style scoped>
.activity-summary-container {
  margin-bottom: 24px;
  border-radius: 4px;
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

.activity-summary-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.activity-summary-table td {
  padding: 12px 16px;
  vertical-align: top;
  width: 20%;
  position: relative;
}

.activity-summary-table td.empty-cell {
  padding: 0;
  background: transparent;
}

.summary-content {
  border-top: 1px solid #e0e0e0;
  padding: 0 16px 16px;
}

.summary-label {
  font-size: 14px;
  color: var(--semantic-system-brand, #001965);
  margin-bottom: 4px;
  font-weight: 400;
  text-transform: none;
}

.summary-value {
  font-weight: 700;
  font-size: 18px;
  line-height: 24px;
  letter-spacing: -0.02em;
  color: var(--semantic-system-brand, #001965);
  min-height: 24px;
}

.version-select {
  width: 120px;
}

.version-select :deep(.v-field__input),
.version-select :deep(.v-select__selection) {
  font-weight: 700;
  font-size: 18px;
  line-height: 24px;
  letter-spacing: -0.02em;
  color: var(--semantic-system-brand, #001965);
}

.activity-link {
  color: var(--semantic-system-brand, #001965);
  text-decoration: underline;
  cursor: pointer;
  font-weight: 700;
  font-size: 18px;
  line-height: 24px;
  letter-spacing: -0.02em;
}

.activity-link:hover {
  text-decoration: none;
  opacity: 0.8;
}

@media (max-width: 1200px) {
  .activity-summary-table,
  .activity-summary-table tbody,
  .activity-summary-table tr {
    display: block;
    width: 100%;
  }

  .activity-summary-table td {
    display: inline-block;
    width: 33.33%;
    box-sizing: border-box;
  }
}

@media (max-width: 768px) {
  .activity-summary-table td {
    width: 50%;
  }
}
</style>
