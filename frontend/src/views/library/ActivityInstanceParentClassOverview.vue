<template>
  <div v-if="activityInstanceParentClassOverview" class="px-4">
    <div class="d-flex page-title">
      {{
        activityInstanceParentClassOverview.parent_activity_instance_class.name
      }}
    </div>
    <ActivityInstanceParentClassOverview
      v-if="activityInstanceParentClassOverview"
      ref="overviewComponent"
    />
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import ActivityInstanceParentClassOverview from '@/components/library/ActivityInstanceParentClassOverview.vue'
import activityInstanceClasses from '@/api/activityInstanceClasses'
import { useAppStore } from '@/stores/app'

const route = useRoute()
const appStore = useAppStore()

const activityInstanceParentClassOverview = ref(null)
const overviewComponent = ref(null)

const fetchOverview = async () => {
  try {
    const response = await activityInstanceClasses.getParentClassOverview(
      route.params.id,
      route.params.version
    )
    activityInstanceParentClassOverview.value = response.data

    // Pass data to component after it's mounted
    await nextTick()
    if (overviewComponent.value) {
      overviewComponent.value.itemOverview = response.data
    }

    appStore.addBreadcrumbsLevel(
      activityInstanceParentClassOverview.value.parent_activity_instance_class
        .name,
      { name: 'ActivityInstanceParentClassOverview', params: route.params },
      4,
      true
    )
  } catch (error) {
    console.error(
      'Error fetching activity instance parent class overview:',
      error
    )
  }
}

// Set up breadcrumbs. The router guard already plants "Library" at index 0
// via setSection(), so this view fills indices 1..4. Matches the pattern in
// ActivityInstanceClassOverview, ActivityItemClassOverview, Subgroup /
// GroupOverview etc. — see tests/smoke/specs/breadcrumbs.smoke.spec.js.
onMounted(() => {
  appStore.addBreadcrumbsLevel('Concepts', { name: 'Library' }, 1, true)

  appStore.addBreadcrumbsLevel('Activities', { name: 'Activities' }, 2, true)

  appStore.addBreadcrumbsLevel(
    'Activity Instance Classes',
    { name: 'Activities', params: { tab: 'activity-instance-classes' } },
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
</script>
