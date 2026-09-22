<template>
  <div class="section-header mb-1">
    <h3 class="text-headline-small font-weight-bold text-primary">
      {{ $t('ActivityInstanceOverview.summary_title') }}
    </h3>
  </div>
  <v-row class="mb-4">
    <v-col cols="12" md="6">
      <v-card color="white" class="summary-card" elevation="1">
        <v-card-title class="text-title-large font-weight-bold text-primary">
          {{ $t('ActivityInstanceOverview.attributes') }}
        </v-card-title>
        <v-list density="compact" bg-color="white">
          <v-list-item class="summary-label">
            <v-list-item-title class="text-label-large">{{
              $t('_global.version')
            }}</v-list-item-title>
            <template #append>
              <span class="summary-value text-body-large font-weight-bold">{{
                activityInstance?.version || '-'
              }}</span>
            </template>
          </v-list-item>
          <v-list-item class="summary-label">
            <v-list-item-title class="text-label-large">{{
              $t('_global.status')
            }}</v-list-item-title>
            <template #append>
              <StatusChip
                v-if="activityInstance?.status"
                :status="activityInstance.status"
              />
              <span v-else>-</span>
            </template>
          </v-list-item>
          <v-list-item class="summary-label">
            <v-list-item-title class="text-label-large">{{
              $t('_global.start_date')
            }}</v-list-item-title>
            <template #append>
              <span class="summary-value text-body-large font-weight-bold">
                {{
                  activityInstance?.start_date
                    ? $filters.date(activityInstance.start_date)
                    : '-'
                }}
              </span>
            </template>
          </v-list-item>
          <v-list-item class="summary-label">
            <v-list-item-title class="text-label-large">{{
              $t('_global.end_date')
            }}</v-list-item-title>
            <template #append>
              <span class="summary-value text-body-large font-weight-bold">
                {{
                  activityInstance?.end_date
                    ? $filters.date(activityInstance.end_date)
                    : '-'
                }}
              </span>
            </template>
          </v-list-item>
        </v-list>
      </v-card>
    </v-col>
    <v-col cols="12" md="6">
      <v-card color="white" class="summary-card" elevation="1">
        <v-card-title class="text-title-large font-weight-bold text-primary">
          {{ $t('ActivityInstanceOverview.groupings') }}
        </v-card-title>
        <v-list density="compact" bg-color="white">
          <v-list-item class="summary-label">
            <v-list-item-title class="text-label-large">{{
              $t('_global.version')
            }}</v-list-item-title>
            <template #append>
              <span class="summary-value text-body-large font-weight-bold">{{
                groupingsVersion || '-'
              }}</span>
            </template>
          </v-list-item>
          <v-list-item class="summary-label">
            <v-list-item-title class="text-label-large">{{
              $t('_global.status')
            }}</v-list-item-title>
            <template #append>
              <StatusChip
                v-if="groupingsData?.status"
                :status="groupingsData.status"
              />
              <span v-else>-</span>
            </template>
          </v-list-item>
          <v-list-item class="summary-label">
            <v-list-item-title class="text-label-large">{{
              $t('_global.start_date')
            }}</v-list-item-title>
            <template #append>
              <span class="summary-value text-body-large font-weight-bold">
                {{
                  groupingsData?.start_date
                    ? $filters.date(groupingsData.start_date)
                    : '-'
                }}
              </span>
            </template>
          </v-list-item>
          <v-list-item class="summary-label">
            <v-list-item-title class="text-label-large">{{
              $t('_global.end_date')
            }}</v-list-item-title>
            <template #append>
              <span class="summary-value text-body-large font-weight-bold">
                {{
                  groupingsData?.end_date
                    ? $filters.date(groupingsData.end_date)
                    : '-'
                }}
              </span>
            </template>
          </v-list-item>
        </v-list>
      </v-card>
    </v-col>
  </v-row>
</template>

<script setup>
import { getCurrentInstance } from 'vue'
import StatusChip from '@/components/tools/StatusChip.vue'

defineProps({
  activityInstance: {
    type: Object,
    default: () => ({}),
  },
  groupingsVersion: {
    type: [String, Number],
    default: null,
  },
  groupingsData: {
    type: Object,
    default: () => ({}),
  },
})

const $filters =
  getCurrentInstance().appContext.config.globalProperties.$filters
</script>

<style scoped>
.summary-card.v-card.v-card {
  background-color: white !important;
  box-shadow:
    0 2px 1px -1px rgba(0, 0, 0, 0.2),
    0 1px 1px 0 rgba(0, 0, 0, 0.14),
    0 1px 3px 0 rgba(0, 0, 0, 0.12) !important;
}

.summary-label {
  color: var(--semantic-system-brand, #001965);
  margin-bottom: 4px;
  text-transform: none;
}

.summary-value {
  color: var(--semantic-system-brand, #001965);
}
</style>
