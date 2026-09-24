<template>
  <v-dialog
    :model-value="dialog"
    :max-width="options.width"
    persistent
    :style="{ zIndex: options.zIndex }"
    @keydown.esc="cancel"
  >
    <v-card :border="cardClasses" class="pa-1" style="border-radius: 20px">
      <v-card-title v-if="options.title" class="dialogText">
        {{ options.title }}
      </v-card-title>
      <v-card-text v-if="savedMessage" class="pt-2 dialogText">
        <v-row no-gutters class="align-center pa-2">
          <v-col cols="12">
            <slot name="body">
              <div
                class="text-body-large mt-1"
                v-html="sanitizeHTML(savedMessage)"
              />
            </slot>
          </v-col>
        </v-row>
        <v-divider class="pa-2" />
        <v-row>
          <v-col class="text-center">
            <v-btn
              v-if="!options.noCancel"
              :color="options.cancelIsPrimaryAction ? btnClasses : ''"
              :variant="options.cancelIsPrimaryAction ? 'elevated' : 'outlined'"
              :disabled="props.cancelDisabled"
              data-cy="cancel-popup"
              class="mr-4"
              rounded="xl"
              @click="cancel"
            >
              {{ options.cancelLabel }}
            </v-btn>
            <slot name="actions">
              <v-btn
                v-if="options.redirect === null"
                :color="options.cancelIsPrimaryAction ? '' : btnClasses"
                :variant="
                  options.cancelIsPrimaryAction ? 'outlined' : 'elevated'
                "
                :disabled="props.agreeDisabled"
                rounded="xl"
                data-cy="continue-popup"
                @click="agree"
              >
                {{ options.agreeLabel }}
              </v-btn>
              <v-btn
                v-else
                data-cy="continue-popup"
                :color="options.cancelIsPrimaryAction ? '' : btnClasses"
                :variant="
                  options.cancelIsPrimaryAction ? 'outlined' : 'elevated'
                "
                :disabled="props.agreeAndRedirectDisabled"
                rounded="xl"
                @click="agreeAndRedirect"
              >
                {{ options.agreeLabel }}
              </v-btn>
            </slot>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { escapeHTML, sanitizeHTML } from '@/utils/sanitize'

const { t } = useI18n()
const router = useRouter()

const props = defineProps({
  cancelDisabled: { type: Boolean, default: false },
  agreeDisabled: { type: Boolean, default: false },
  agreeAndRedirectDisabled: { type: Boolean, default: false },
})

const dialog = ref(false)
let savedResolve = null
const savedMessage = ref(null)
const options = ref({
  title: null,
  type: 'success',
  width: 450,
  zIndex: 3000,
  noCancel: false,
  agreeLabel: t('_global.continue'),
  cancelLabel: t('_global.cancel'),
  cancelIsPrimaryAction: false,
  redirect: null,
})

const cardClasses = computed(() => {
  return btnClasses.value + ' lg opacity-100'
})
const btnClasses = computed(() => {
  if (options.value.type === 'error') {
    return 'error'
  } else if (options.value.type === 'warning') {
    return 'warning'
  } else if (options.value.type === 'info') {
    return 'info'
  } else {
    return 'success'
  }
})

const open = (messagePlain, extraOptions, callback) => {
  dialog.value = true
  savedMessage.value = escapeHTML(messagePlain).replace(/\n+/g, '<br />')
  options.value = Object.assign(options.value, extraOptions)

  callback?.()

  return new Promise((resolve) => {
    savedResolve = resolve
  })
}
const openHtml = (messageHtml, extraOptions, callback) => {
  dialog.value = true
  savedMessage.value = messageHtml
  options.value = Object.assign(options.value, extraOptions)

  callback?.()

  return new Promise((resolve) => {
    savedResolve = resolve
  })
}
const agree = () => {
  savedResolve(true)
  dialog.value = false
}
const agreeAndRedirect = () => {
  dialog.value = false
  router.push(options.value.redirect)
}
const cancel = () => {
  savedResolve(false)
  dialog.value = false
}

defineExpose({
  open,
  openHtml,
  cancel,
})
</script>
<style>
.dialogText {
  color: rgb(var(--v-theme-nnTrueBlue));
}
</style>
