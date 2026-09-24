<template>
  <v-dialog :model-value="true" max-width="500" persistent>
    <v-card elevation="0" rounded="xl">
      <v-card-title class="d-flex align-center">
        <v-icon icon="mdi-lock-outline" size="24" color="grey" class="mr-2" />
        <span class="dialog-title">
          {{ $t('FeatureDisabledDialog.title') }}
        </span>
        <v-spacer />
        <v-btn icon="mdi-close" variant="text" @click="$emit('close')" />
      </v-card-title>
      <v-divider />
      <v-card-text class="text-body-1 text-center pa-8">
        {{ message || $t('FeatureDisabledDialog.message') }}
      </v-card-text>
      <v-divider />
      <v-card-actions class="justify-end pr-6 my-2">
        <v-btn color="secondary" variant="flat" rounded @click="$emit('close')">
          {{ $t('_global.close') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
defineProps({
  message: {
    type: String,
    default: null,
  },
})
defineEmits(['close'])
</script>
