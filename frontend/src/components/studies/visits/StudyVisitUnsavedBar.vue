<template>
  <Teleport to="body">
    <v-slide-y-reverse-transition>
      <div v-if="show" class="unsaved-bar">
        <v-btn
          variant="outlined"
          color="nnBaseBlue"
          rounded
          :disabled="saving"
          data-cy="discard-visit-changes"
          @click="emit('discard')"
        >
          {{ $t('_global.discard_changes') }}
        </v-btn>
        <span v-if="hint" class="text-caption">{{ hint }}</span>
        <v-spacer />
        <v-btn
          color="nnBaseBlue"
          variant="flat"
          rounded
          :loading="saving"
          data-cy="save-visit-changes"
          @click="emit('save')"
        >
          {{ $t('_global.save_changes') }}
        </v-btn>
      </div>
    </v-slide-y-reverse-transition>
  </Teleport>
</template>

<script setup>
defineProps({
  show: Boolean,
  saving: Boolean,
  hint: { type: String, default: '' },
})
const emit = defineEmits(['discard', 'save'])
</script>

<style scoped>
.unsaved-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 2000;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 32px;
  background-color: rgb(var(--v-theme-nnWhite, 255, 255, 255));
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.12);
}
</style>
