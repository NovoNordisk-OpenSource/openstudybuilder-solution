<template>
  <v-dialog
    :model-value="dialog"
    :max-width="options.width"
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
            <div class="text-body-1 mt-1" v-html="savedMessage" />
          </v-col>
        </v-row>
        <v-divider class="pa-2" />
        <v-row>
          <v-col class="text-center">
            <v-btn
              v-if="!options.noCancel"
              variant="outlined"
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
                :color="btnClasses"
                rounded="xl"
                data-cy="continue-popup"
                @click="agree"
              >
                {{ options.agreeLabel }}
              </v-btn>
              <v-btn
                v-else
                data-cy="continue-popup"
                variant="outlined"
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

const { t } = useI18n()
const router = useRouter()

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
  if (options.value.type === 'warning') {
    return 'warning'
  } else if (options.value.type === 'info') {
    return 'info'
  } else {
    return 'success'
  }
})

const open = (message, extraOptions) => {
  dialog.value = true
  savedMessage.value = message
  options.value = Object.assign(options.value, extraOptions)
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
  cancel,
})
</script>
<style>
.dialogText {
  color: rgb(var(--v-theme-nnTrueBlue));
}
</style>
