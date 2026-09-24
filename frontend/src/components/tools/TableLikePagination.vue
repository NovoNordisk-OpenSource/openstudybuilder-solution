<template>
  <div v-if="total" class="d-flex align-center mt-4">
    <v-spacer />
    <span>{{ $t('Pagination.rows_per_page') }}</span>
    <v-select
      v-model="itemsPerPage"
      :items="tablesConstants.ITEMS_PER_PAGE_OPTIONS"
      hide-details
      class="flex-grow-0 ml-2"
    />
    <span class="mx-10">
      {{ firstItemOffset }}-{{ lastItemOffset }} {{ $t('Pagination.of') }}
      {{ props.total }}
    </span>
    <v-pagination
      v-model="pageNumber"
      density="comfortable"
      :length="pageCount"
      :next-aria-label="$t('Pagination.next_aria_label')"
      :previous-aria-label="$t('Pagination.previous_aria_label')"
      rounded
      show-first-last-page
      :total-visible="0"
      variant="plain"
    >
    </v-pagination>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import tablesConstants from '@/constants/tables'

const props = defineProps({
  total: {
    type: Number,
    default: 0,
  },
  currentPage: {
    type: Array,
    default: null,
  },
})

const pageNumber = defineModel('pageNumber', {
  type: Number,
})
const itemsPerPage = defineModel('itemsPerPage', {
  type: Number,
})

const firstItemOffset = computed(() => {
  return 1 + (pageNumber.value - 1) * itemsPerPage.value
})

const lastItemOffset = computed(() => {
  return firstItemOffset.value + props.currentPage.length - 1
})

const pageCount = computed(() => {
  return Math.ceil(props.total / itemsPerPage.value)
})
</script>
