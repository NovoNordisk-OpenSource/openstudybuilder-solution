<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('HelloExtension.title') }}
    </div>

    <v-alert
      color="nnLightBlue200"
      icon="mdi-information-outline"
      class="text-nnTrueBlue mx-0 my-0 mb-6"
    >
      {{ $t('HelloExtension.description') }}
    </v-alert>

    <v-card>
      <v-card-text>
        <!-- Your extension content here -->
        <p>Welcome to my extension!</p>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

onMounted(() => {
  // Initialize your extension
  console.log(t('HelloExtension.menu_label'), 'mounted')
})
</script>

<style scoped>
/* Component-specific styles */
</style>
