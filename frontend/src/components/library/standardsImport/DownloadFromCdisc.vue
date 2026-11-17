<template>
  <div>
    <v-btn
      variant="text"
      density="comfortable"
      rounded="xl"
      size="small"
      color="primary"
      class="px-2"
      prepend-icon="mdi-tray-arrow-down"
      append-icon="mdi-open-in-new"
      :href="href"
      target="_blank"
      rel="noopener"
    >
      {{ label }}
    </v-btn>
    <div v-if="note" class="text-caption text-medium-emphasis ml-2 mt-n1">
      <v-icon icon="mdi-account-key-outline" size="x-small" class="mr-1" />
      {{ note }}
    </div>
  </div>
</template>

<script setup>
/**
 * A link out to a file CDISC publishes for this release.
 *
 * The URL is built from the effective date by the caller rather than being a
 * link the user follows through the CDISC site, because the filenames encode
 * the date and the two sources spell it differently — the whole point is to
 * save someone assembling it by hand and getting a 404 for their trouble.
 */
defineProps({
  href: {
    type: String,
    required: true,
  },
  label: {
    type: String,
    required: true,
  },
  // Shown beside the link, for anything a person needs to know *before*
  // clicking it — a sign-in requirement being the obvious one, since without
  // it the site answers with its login page rather than the file.
  note: {
    type: String,
    default: '',
  },
})
</script>
