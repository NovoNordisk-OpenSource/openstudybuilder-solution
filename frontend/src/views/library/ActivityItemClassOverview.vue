<template>
  <div v-if="itemOverview" class="px-4">
    <div class="d-flex page-title">
      {{ itemOverview.activity_item_class.name }}
      <HelpButtonWithPanels
        :help-text="$t('_help.ActivityItemClassOverview.general')"
        :items="helpItems"
      />
    </div>
    <ActivityItemClassOverview ref="overviewComponent" />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import ActivityItemClassOverview from '@/components/library/ActivityItemClassOverview.vue'
import activityItemClasses from '@/api/activityItemClasses'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import { useAppStore } from '@/stores/app'

const route = useRoute()
const appStore = useAppStore()

const itemOverview = ref(null)
const overviewComponent = ref(null)

const helpItems = [
  'ActivityItemClassOverview.nci_code',
  'ActivityItemClassOverview.adam_param_specific',
  'ActivityItemClassOverview.mandatory',
]

const fetchOverview = async () => {
  try {
    // Fetch main overview data
    const resp = await activityItemClasses.getOverview(
      route.params.id,
      route.params.version
    )

    itemOverview.value = resp.data

    // Pass the data to the child component
    if (overviewComponent.value) {
      overviewComponent.value.itemOverview = resp.data
    }

    // Update breadcrumb with the item name
    appStore.addBreadcrumbsLevel(
      itemOverview.value.activity_item_class.name,
      { name: 'ActivityItemClassOverview', params: route.params },
      4,
      true
    )
  } catch (error) {
    console.error('Error fetching activity item class overview:', error)
  }
}

// Set up breadcrumbs
onMounted(() => {
  appStore.addBreadcrumbsLevel('Concepts', { name: 'Library' }, 1, true)

  appStore.addBreadcrumbsLevel('Activities', { name: 'Activities' }, 2, true)

  appStore.addBreadcrumbsLevel(
    'Activity Item Classes',
    { name: 'Activities', params: { tab: 'activity-item-classes' } },
    3,
    true
  )
})

watch(
  () => route.params,
  () => {
    fetchOverview()
  },
  { immediate: true, deep: true }
)

// Watch for overviewComponent to be available and pass data
watch(overviewComponent, (newVal) => {
  if (newVal && itemOverview.value) {
    newVal.itemOverview = itemOverview.value
  }
})
</script>
