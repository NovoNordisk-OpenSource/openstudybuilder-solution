<template>
  <v-card
    data-cy="form-body"
    color="dfltBackground"
    class="bg-dfltBackground fullscreen-dialog"
  >
    <v-card-title class="d-flex align-center">
      <span class="dialog-title ml-6">{{ title }}</span>
      <HelpButton v-if="helpText" :help-text="helpText" />
      <HelpButtonWithPanels
        v-if="helpItems"
        :title="$t('_global.help')"
        :items="helpItems"
      />
      <v-btn
        v-if="formUrl"
        color="secondary"
        class="ml-2"
        size="small"
        @click="copyUrl"
      >
        {{ $t('_global.copy_link') }}
      </v-btn>
    </v-card-title>
    <v-card-text class="mt-4 mb-12 pb-12 bg-dfltBackground">
      <v-stepper
        v-model="currentStep"
        bg-color="white"
        :items="stepTitles"
        :non-linear="editable"
        :editable="editable"
        hide-actions
      >
        <template
          v-for="(step, index) in stepTitles"
          :key="`content-${index}`"
          #[`item.${index+1}`]
        >
          <v-sheet elevation="0" class="ma-2 pa-4">
            <v-row>
              <v-col :cols="12" class="pr-0">
                <slot :name="`step.${steps[index].name}`" :step="index + 1" />
              </v-col>
              <slot
                :name="`step.${steps[index].name}.after`"
                :step="index + 1"
              />
            </v-row>
          </v-sheet>
        </template>
      </v-stepper>
    </v-card-text>
    <v-card-actions class="bg-white fixed-actions border-t-thin">
      <v-col>
        <v-btn
          class="secondary-btn"
          variant="outlined"
          width="120px"
          rounded="xl"
          @click="cancel"
        >
          {{ $t('_global.cancel') }}
        </v-btn>
      </v-col>
      <v-spacer />
      <div v-if="currentStep === 1">
        <slot name="actions" />
      </div>
      <div class="mx-2">
        <v-row>
          <v-col v-if="currentStep > 1">
            <v-btn
              class="secondary-btn"
              variant="outlined"
              width="120px"
              rounded="xl"
              @click="currentStep -= 1"
            >
              {{ $t('_global.previous') }}
            </v-btn>
          </v-col>
          <v-col v-if="currentStep < steps.length">
            <v-btn
              data-cy="continue-button"
              color="secondary"
              :loading="loadingContinue"
              variant="flat"
              width="120px"
              rounded="xl"
              @click="goToNextStep()"
            >
              {{ $t('_global.continue') }}
            </v-btn>
          </v-col>
          <v-col v-if="currentStep >= steps.length || saveFromAnyStep">
            <v-btn
              data-cy="save-button"
              color="secondary"
              :loading="loading"
              variant="flat"
              width="120px"
              rounded="xl"
              @click.stop="submit"
            >
              {{ $t('_global.save') }}
            </v-btn>
          </v-col>
          <v-col>
            <slot
              :name="`step.${steps[currentStep - 1].name}.afterActions`"
              :step="currentStep + 1"
            />
          </v-col>
        </v-row>
      </div>
    </v-card-actions>
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
    <template v-if="debug">
      <div class="debug">
        {{ editData }}
      </div>
    </template>
  </v-card>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch, inject } from 'vue'
import { useI18n } from 'vue-i18n'
import HelpButton from '@/components/tools/HelpButton.vue'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import { useFormStore } from '@/stores/form'

const eventBusEmit = inject('eventBusEmit')
const { t } = useI18n()
const props = defineProps({
  title: {
    type: String,
    default: '',
  },
  steps: {
    type: Array,
    default: () => [],
  },
  formObserverGetter: {
    type: Function,
    default: undefined,
  },
  editable: {
    type: Boolean,
    default: false,
  },
  extraStepValidation: {
    type: Function,
    required: false,
    default: undefined,
  },
  helpText: {
    type: String,
    required: false,
    default: '',
  },
  helpItems: {
    type: Array,
    required: false,
    default: null,
  },
  editData: {
    type: Object,
    default: undefined,
  },
  debug: Boolean,
  formUrl: {
    type: String,
    default: '',
  },
  saveFromAnyStep: {
    type: Boolean,
    default: false,
  },
  loadingContinue: {
    type: Boolean,
    default: false,
  },
  resetLoading: {
    type: Number,
    default: 0,
  },
})
const emit = defineEmits(['close', 'change', 'save', 'stepLoaded'])
const formStore = useFormStore()

const currentStep = ref(1)
const loading = ref(false)
const confirm = ref()

const stepTitles = computed(() => {
  return props.steps.map((step) => step.title)
})

watch(currentStep, (value) => {
  emit('change', value)
})
watch(
  () => props.resetLoading,
  () => {
    loading.value = false
  }
)

onMounted(() => {
  formStore.save(props.editData)
  document.addEventListener('keydown', (evt) => {
    if (evt.code === 'Escape') {
      cancel()
    }
  })
})

function copyUrl() {
  navigator.clipboard.writeText(props.formUrl)
}

function closeWithNoChange() {
  close()
  eventBusEmit('notification', { type: 'info', msg: t('_global.no_changes') })
}

async function cancel() {
  if (formStore.isEmpty || formStore.isEqual(props.editData)) {
    closeWithNoChange()
  } else {
    const options = {
      type: 'warning',
      cancelLabel: t('_global.cancel'),
      agreeLabel: t('_global.continue'),
    }
    if (await confirm.value.open(t('_global.cancel_changes'), options)) {
      close()
    }
  }
}
function close() {
  emit('close')
  formStore.reset()
  reset()
}
function reset() {
  currentStep.value = 1
  props.steps.forEach((item, index) => {
    const observer = props.formObserverGetter(index + 1)
    if (observer !== undefined && observer !== null) {
      observer.reset()
    }
  })
  loading.value = false
}
async function validateStepObserver(step) {
  const observer = props.formObserverGetter(step)
  if (observer !== undefined && observer !== null) {
    const { valid } = await observer.validate()
    return valid
  }
  return true
}
async function goToNextStep() {
  if (!(await validateStepObserver(currentStep.value))) {
    return
  }
  if (props.extraStepValidation) {
    if (!(await props.extraStepValidation(currentStep.value))) {
      return
    }
  }
  currentStep.value += 1
  nextTick(() => {
    emit('stepLoaded', currentStep.value)
  })
}
async function submit() {
  if (!(await validateStepObserver(currentStep.value))) {
    return
  }
  loading.value = true
  emit('save')
}

defineExpose({
  reset,
  loading,
  close,
})
</script>

<style lang="scss">
.v-stepper-header {
  box-shadow: unset !important;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  padding: 10px;
  margin: 0 10px;
}
.v-stepper-item {
  font-size: large;
  color: rgba(0, 0, 0, 0.6);

  .v-avatar {
    background-color: rgba(0, 0, 0, 0.6) !important;
  }

  &--selected {
    color: rgb(var(--v-theme-secondary)) !important;

    .v-avatar {
      background-color: rgb(var(--v-theme-secondary)) !important;
    }
  }
}

.debug {
  padding: 1% 10%;
  background: lightgray;
  white-space: pre-wrap;
}
</style>
