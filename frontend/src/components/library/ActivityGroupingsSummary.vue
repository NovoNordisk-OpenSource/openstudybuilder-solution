<template>
  <div class="activity-summary-container">
    <table class="activity-summary-table">
      <tbody>
        <tr>
          <td>
            <div class="summary-label">{{ label }}</div>
            <div class="summary-value">
              <v-select
                v-if="allGroupingsVersions && allGroupingsVersions.length"
                :items="allGroupingsVersions"
                :model-value="modelValue"
                hide-details
                class="version-select"
                @update:model-value="$emit('update:modelValue', $event)"
              ></v-select>
              <span v-else>{{ modelValue }}</span>
            </div>
          </td>
          <td>
            <div class="summary-label">{{ $t('_global.start_date') }}</div>
            <div class="summary-value">{{ formattedStartDate }}</div>
          </td>
          <td>
            <div class="summary-label">{{ $t('_global.end_date') }}</div>
            <div class="summary-value">{{ formattedEndDate }}</div>
          </td>
          <td>
            <div class="summary-label">{{ $t('_global.status') }}</div>
            <div class="summary-value">
              <StatusChip
                v-if="summaryData.status"
                :status="summaryData.status"
              />
              <span v-else>-</span>
            </div>
          </td>
          <td>
            <div class="summary-label">{{ $t('_global.author') }}</div>
            <div class="summary-value">
              {{ summaryData.author_username || '-' }}
            </div>
          </td>
        </tr>
        <tr>
          <td>
            <div class="summary-label">Change description</div>
            <div class="summary-value">
              {{ summaryData.change_description || '-' }}
            </div>
          </td>
          <td class="empty-cell"></td>
          <td class="empty-cell"></td>
          <td class="empty-cell"></td>
          <td class="empty-cell"></td>
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
import { computed, getCurrentInstance } from 'vue'
import { useI18n } from 'vue-i18n'
import StatusChip from '@/components/tools/StatusChip.vue'

const { t: $t } = useI18n()
const instance = getCurrentInstance()
const $filters = instance.appContext.config.globalProperties.$filters

defineEmits(['update:modelValue'])

const props = defineProps({
  label: {
    type: String,
    default: '',
  },
  allGroupingsVersions: {
    type: Array,
    default: () => [],
  },
  modelValue: {
    type: String,
    default: '-',
  },
  summaryData: {
    type: Object,
    default: () => ({}),
  },
})

const formattedStartDate = computed(() => {
  return props.summaryData?.start_date
    ? $filters.date(props.summaryData.start_date)
    : 'None'
})

const formattedEndDate = computed(() => {
  return props.summaryData?.end_date
    ? $filters.date(props.summaryData.end_date)
    : 'None'
})
</script>

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
