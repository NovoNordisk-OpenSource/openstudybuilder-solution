<template>
  <v-dialog
    :model-value="open"
    :scrollable="scrollable"
    persistent
    :max-width="maxWidth"
    v-bind="$attrs"
    @keydown.esc="cancel"
  >
    <v-card data-cy="form-body" elevation="0" rounded="xl">
      <v-card-title class="d-flex align-center">
        <span class="dialog-title">{{ title }}</span>
        <HelpButtonWithPanels
          v-if="helpItems"
          :title="$t('_global.help')"
          :help-text="helpText"
          :items="helpItems"
        />
        <v-btn
          v-if="formUrl"
          color="secondary"
          class="ml-2 text-label-large"
          size="small"
          @click="copyUrl"
        >
          {{ $t('_global.copy_link') }}
        </v-btn>
        <v-spacer />
        <v-btn
          v-if="topRightCancel"
          icon="mdi-close"
          variant="text"
          @click="cancel"
        />
      </v-card-title>
      <v-divider />
      <v-card-text>
        <slot name="body" />
      </v-card-text>
      <v-divider />
      <v-card-actions class="pr-6 my-2">
        <v-spacer />
        <div>
          <slot name="actions" />
        </div>
        <div v-if="!noDefaultActions">
          <v-btn
            data-cy="cancel-button"
            :disabled="actionDisabled"
            variant="outlined"
            rounded
            class="mr-2"
            elevation="0"
            width="120px"
            @click="cancel"
          >
            {{ cancelLabel ?? $t('_global.cancel') }}
          </v-btn>
          <v-btn
            v-if="!noSaving"
            data-cy="save-button"
            color="secondary"
            variant="flat"
            min-width="120px"
            :loading="working"
            :disabled="actionDisabled"
            rounded
            @click="submit"
          >
            {{ actionButtonLabel }}
          </v-btn>
        </div>
      </v-card-actions>
    </v-card>
  </v-dialog>
  <ConfirmDialog ref="confirmRef" :text-cols="6" :action-cols="5" />
</template>

<script setup>
import { computed, getCurrentInstance, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'

const { t } = useI18n()

const props = defineProps({
  actionLabel: {
    type: String,
    default: null,
  },
  title: {
    type: String,
    default: '',
  },
  helpItems: {
    type: Array,
    default: null,
  },
  helpText: {
    type: String,
    required: false,
    default: '',
  },
  open: Boolean,
  maxWidth: {
    type: String,
    default: '800px',
  },
  noSaving: {
    type: Boolean,
    default: false,
  },
  formUrl: {
    type: String,
    default: '',
  },
  scrollable: {
    type: Boolean,
    default: true,
  },
  noDefaultActions: {
    type: Boolean,
    default: false,
  },
  topRightCancel: {
    type: Boolean,
    default: false,
  },
  cancelLabel: {
    type: String,
    default: null,
  },
})

const emit = defineEmits(['close', 'submit'])

const confirmRef = ref(null)
const actionDisabled = ref(false)
const working = ref(false)
const instance = getCurrentInstance()

const actionButtonLabel = computed(() => {
  return props.actionLabel ? props.actionLabel : t('_global.save')
})

watch(
  () => props.open,
  () => {
    working.value = false
  }
)

function copyUrl() {
  navigator.clipboard.writeText(props.formUrl)
}

function cancel() {
  working.value = false
  emit('close')
}

async function confirm(message, options) {
  return await confirmRef.value.open(message, options)
}

async function submit() {
  const observer = instance?.proxy?.$parent?.$refs?.observer
  if (observer) {
    const { valid } = await observer.validate()
    if (!valid) {
      return
    }
  }
  working.value = true
  emit('submit')
}

defineExpose({
  actionDisabled,
  working,
  copyUrl,
  cancel,
  confirm,
  submit,
})
</script>
