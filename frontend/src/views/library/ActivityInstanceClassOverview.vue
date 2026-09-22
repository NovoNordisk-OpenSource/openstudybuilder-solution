<template>
  <div v-if="activityInstanceClassOverview" class="px-4">
    <div class="d-flex page-title">
      {{ activityInstanceClassOverview.activity_instance_class.name }}
    </div>
    <ActivityInstanceClassOverview
      v-if="activityInstanceClassOverview"
      ref="overviewComponent"
    />
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import ActivityInstanceClassOverview from '@/components/library/ActivityInstanceClassOverview.vue'
import activityInstanceClasses from '@/api/activityInstanceClasses'
import { useAppStore } from '@/stores/app'

const route = useRoute()
// const router = useRouter()
const appStore = useAppStore()

const activityInstanceClassOverview = ref(null)
const overviewComponent = ref(null)

const fetchOverview = async () => {
  try {
    const response = await activityInstanceClasses.getOverview(
      route.params.id,
      route.params.version
    )
    activityInstanceClassOverview.value = response.data

    // Pass data to component after it's mounted
    await nextTick()
    if (overviewComponent.value) {
      overviewComponent.value.itemOverview = response.data
    }

    appStore.addBreadcrumbsLevel(
      activityInstanceClassOverview.value.activity_instance_class.name,
      { name: 'ActivityInstanceClassOverview', params: route.params },
      4,
      true
    )
  } catch (error) {
    console.error('Error fetching activity instance class overview:', error)
  }
}

// const closePage = () => {
//   router.push({
//     name: 'Activities',
//     params: { tab: 'activity-instance-classes' },
//   })
// }

// Set up breadcrumbs
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
