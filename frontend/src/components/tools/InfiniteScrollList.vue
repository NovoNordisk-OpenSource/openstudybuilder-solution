<template>
  <div ref="containerRef" class="infinite-scroll-container">
    <!-- Slot for list items -->
    <slot
      :items="infiniteScroll.items.value"
      :loading="infiniteScroll.loading.value"
    />

    <!-- Loading indicator -->
    <div v-if="infiniteScroll.loading.value" class="pa-2 text-center">
      <slot name="loading">
        <v-progress-circular indeterminate :size="loadingSize" />
      </slot>
    </div>

    <!-- Scroll for more message -->
    <div
      v-else-if="infiniteScroll.hasMore.value && showScrollMessage"
      class="pa-2 text-center text-caption text-grey"
    >
      <slot name="scroll-message">
        {{ scrollMessage || $t('_global.scroll_for_more') }}
      </slot>
    </div>

    <!-- End of list message -->
    <div
      v-else-if="!infiniteScroll.hasMore.value && showEndMessage"
      class="pa-2 text-center text-caption text-grey"
    >
      <slot name="end-message">
        {{ endMessage || $t('_global.end_of_list') }}
      </slot>
    </div>

    <!-- Sentinel element for scroll detection -->
    <div ref="sentinelRef" style="height: 1px" />
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useInfiniteScroll } from '@/composables/useInfiniteScroll'

const props = defineProps({
  /**
   * Fetch function that returns { items, total }
   */
  fetchFunction: {
    type: Function,
    required: true,
  },
  /**
   * Number of items per page
   */
  pageSize: {
    type: Number,
    default: 50,
  },
  /**
   * Search query (v-model:search)
   */
  search: {
    type: String,
    default: '',
  },
  /**
   * Scroll threshold in pixels from bottom
   */
  scrollThreshold: {
    type: Number,
    default: 50,
  },
  /**
   * Show "scroll for more" message
   */
  showScrollMessage: {
    type: Boolean,
    default: true,
  },
  /**
   * Custom scroll message
   */
  scrollMessage: {
    type: String,
    default: '',
  },
  /**
   * Show "end of list" message
   */
  showEndMessage: {
    type: Boolean,
    default: false,
  },
  /**
   * Custom end message
   */
  endMessage: {
    type: String,
    default: '',
  },
  /**
   * Loading spinner size
   */
  loadingSize: {
    type: Number,
    default: 24,
  },
  /**
   * Auto-detect scrollable parent (for dropdowns, modals, etc.)
   */
  autoDetectScrollable: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:search', 'items-loaded', 'error'])

const containerRef = ref(null)
const sentinelRef = ref(null)
let scrollableElement = null
let observer = null

// Initialize infinite scroll
const infiniteScroll = useInfiniteScroll(props.fetchFunction, {
  pageSize: props.pageSize,
})

// Watch for search changes
watch(
  () => props.search,
  (newSearch) => {
    if (newSearch !== infiniteScroll.searchQuery.value) {
      infiniteScroll.search(newSearch)
    }
  }
)

// Emit items when loaded
watch(
  () => infiniteScroll.items.value,
  (items) => {
    emit('items-loaded', items)
  }
)

// Handle scroll event
function handleScroll(event) {
  const element = event.target
  const scrollTop = element.scrollTop
  const scrollHeight = element.scrollHeight
  const clientHeight = element.clientHeight

  const isNearBottom =
    scrollTop + clientHeight >= scrollHeight - props.scrollThreshold

  if (
    isNearBottom &&
    infiniteScroll.hasMore.value &&
    !infiniteScroll.loading.value
  ) {
    infiniteScroll.loadMore()
  }
}

// Find scrollable parent element
function findScrollableParent(element) {
  if (!element) return null

  let parent = element.parentElement
  while (parent) {
    const overflow = window.getComputedStyle(parent).overflow
    const overflowY = window.getComputedStyle(parent).overflowY

    if (
      overflow === 'auto' ||
      overflow === 'scroll' ||
      overflowY === 'auto' ||
      overflowY === 'scroll'
    ) {
      return parent
    }

    parent = parent.parentElement
  }

  return null
}

// Set up scroll listener
function setupScrollListener() {
  if (props.autoDetectScrollable) {
    // Find scrollable parent automatically
    scrollableElement = findScrollableParent(containerRef.value)
  } else {
    // Use the container itself
    scrollableElement = containerRef.value
  }

  if (scrollableElement) {
    scrollableElement.addEventListener('scroll', handleScroll, {
      passive: true,
    })
  }
}

// Set up IntersectionObserver for sentinel-based detection
function setupIntersectionObserver() {
  if (!sentinelRef.value) return

  observer = new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting && infiniteScroll.hasMore.value) {
        infiniteScroll.loadMore()
      }
    },
    {
      root: scrollableElement,
      threshold: 0.1,
    }
  )

  observer.observe(sentinelRef.value)
}

onMounted(async () => {
  // Load initial data
  await infiniteScroll.reset(props.search)

  // Wait for DOM to render
  await nextTick()

  // Set up scroll detection
  setupScrollListener()

  // Optionally set up intersection observer as fallback
  if (!props.autoDetectScrollable) {
    setupIntersectionObserver()
  }
})

onBeforeUnmount(() => {
  if (scrollableElement) {
    scrollableElement.removeEventListener('scroll', handleScroll)
  }
  if (observer) {
    observer.disconnect()
  }
})

// Expose methods for parent components
defineExpose({
  reset: infiniteScroll.reset,
  loadMore: infiniteScroll.loadMore,
  search: infiniteScroll.search,
  items: infiniteScroll.items,
  loading: infiniteScroll.loading,
  hasMore: infiniteScroll.hasMore,
})
</script>

<style scoped>
.infinite-scroll-container {
  width: 100%;
  height: 100%;
}
</style>
