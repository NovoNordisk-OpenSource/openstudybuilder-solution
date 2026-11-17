<template>
  <div>
    <div v-for="(entry, index) in entries" :key="index" class="py-1">
      <div class="text-body-2">
        {{ entry.change_summary }}
        <!-- A codelist also carries the entries of terms it no longer holds; the
             summary alone does not say which term those were about. -->
        <span
          v-if="codelistId && entry.nci_code && entry.nci_code !== codelistId"
          class="text-medium-emphasis"
        >
          &middot; {{ entry.nci_code }}
        </span>
      </div>
      <div
        v-if="entry.request_codes?.length"
        class="d-flex flex-wrap ga-1 mt-1"
      >
        <v-chip
          v-for="code in entry.request_codes"
          :key="code"
          size="x-small"
          variant="tonal"
        >
          {{ code }}
        </v-chip>
      </div>
      <div
        v-if="entry.implementation_instructions"
        class="text-caption text-medium-emphasis font-italic mt-1"
      >
        {{ entry.implementation_instructions }}
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  entries: {
    type: Array,
    required: true,
  },
  // Set where the entries are a codelist's: names the term an entry is about.
  codelistId: {
    type: String,
    default: null,
  },
})
</script>
