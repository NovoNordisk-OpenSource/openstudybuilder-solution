import { ref } from 'vue'

/**
 * Generic composable for infinite scroll functionality
 *
 * @param {Function} fetchFunction - Async function that fetches data, receives (page, searchQuery) as params
 * @param {Object} options - Configuration options
 * @param {number} options.pageSize - Number of items per page (default: 50)
 * @param {number} options.initialPage - Starting page number (default: 1)
 *
 * @returns {Object} - Infinite scroll state and methods
 */
export function useInfiniteScroll(fetchFunction, options = {}) {
  const { pageSize = 50, initialPage = 1 } = options

  // State
  const items = ref([])
  const loading = ref(false)
  const currentPage = ref(initialPage)
  const hasMore = ref(true)
  const searchQuery = ref('')

  /**
   * Load the next page of items
   */
  async function loadMore() {
    if (loading.value || !hasMore.value) {
      return
    }

    loading.value = true

    try {
      const result = await fetchFunction(
        currentPage.value,
        searchQuery.value,
        pageSize
      )

      // Append new items to existing items
      if (result.items && result.items.length > 0) {
        items.value = [...items.value, ...result.items]
        currentPage.value += 1

        // Check if there are more items to load
        if (result.items.length < pageSize) {
          hasMore.value = false
        } else if (result.total !== undefined) {
          // If total count is provided, use it to determine if there are more items
          hasMore.value = items.value.length < result.total
        }
      } else {
        hasMore.value = false
      }
    } catch (error) {
      console.error('Error loading more items:', error)
      hasMore.value = false
    } finally {
      loading.value = false
    }
  }

  /**
   * Reset to initial state and load first page
   * @param {string} newSearchQuery - Optional new search query
   */
  async function reset(newSearchQuery = '') {
    searchQuery.value = newSearchQuery
    items.value = []
    currentPage.value = initialPage
    hasMore.value = true
    await loadMore()
  }

  /**
   * Update search query and reset
   * @param {string} newSearchQuery - New search query
   */
  async function search(newSearchQuery) {
    await reset(newSearchQuery)
  }

  return {
    // State
    items,
    loading,
    currentPage,
    hasMore,
    searchQuery,

    // Methods
    loadMore,
    reset,
    search,
  }
}
