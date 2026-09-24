<template>
  <v-card class="pl-6 pr-6 pb-4" color="dfltBackground">
    <v-card-title>
      <v-row>
        <span class="dialog-title mt-1">{{ title }}</span>
        <HelpButtonWithPanels :title="$t('_global.help')" :items="helpItems" />
      </v-row>
    </v-card-title>
    <v-card-text class="mt-4 white">
      <v-stepper v-model="currentStep">
        <template v-for="(step, index) in steps" :key="`stepper-${index}`">
          <v-stepper-header>
            <v-stepper-item
              :complete="currentStep > index + 1 || editable"
              :title="step.title"
              :value="index + 1"
              color="secondary"
              :editable="editable"
              :edit-icon="editable ? '$complete' : '$edit'"
            />
          </v-stepper-header>
          <v-stepper-window
            v-show="currentStep === index + 1"
            direction="vertical"
          >
            <v-stepper-window-item :value="index + 1">
              <v-sheet v-if="!step.noStyle" class="ma-2 pa-4" :rounded="false">
                <slot :name="`step.${step.name}`" :step="index + 1" />
              </v-sheet>
              <template v-else>
                <slot :name="`step.${step.name}`" :step="index + 1" />
              </template>
              <div class="mt-6 mb-1 mr-5">
                <v-row class="pl-3 pb-3">
                  <v-spacer />
                  <v-btn
                    class="secondary-btn"
                    variant="outlined"
                    elevation="1"
                    width="120px"
                    data-cy="cancel-button"
                    @click="cancel"
                  >
                    {{ $t('_global.cancel') }}
                  </v-btn>
                  <v-btn
                    v-if="currentStep > 1"
                    class="secondary-btn ml-2"
                    variant="outlined"
                    elevation="1"
                    width="120px"
                    @click="currentStep = index"
                  >
                    {{ $t('_global.previous') }}
                  </v-btn>
                  <slot name="extraActions" />
                  <v-btn
                    v-if="currentStep < steps.length"
                    :data-cy="`step.${step.name}` + '-continue-button'"
                    color="secondary"
                    class="ml-2 mr-2"
                    elevation="1"
                    width="120px"
                    @click="goToStep(index + 1, index + 2)"
                  >
                    {{ $t('_global.continue') }}
                  </v-btn>
                  <v-btn
                    v-if="currentStep >= steps.length || editable"
                    :data-cy="`step.${step.name}` + '-continue-button'"
                    color="secondary"
                    class="ml-2"
                    :loading="loading"
                    elevation="1"
                    width="120px"
                    @click="submit"
                  >
                    {{ $t('_global.save') }}
                  </v-btn>
                </v-row>
              </div>
            </v-stepper-window-item>
          </v-stepper-window>
        </template>
      </v-stepper>
    </v-card-text>
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  </v-card>
</template>

<script>
import HelpButtonWithPanels from './HelpButtonWithPanels.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import _isEqual from 'lodash/isEqual'
import { useFormStore } from '@/stores/form'

export default {
  components: {
    HelpButtonWithPanels,
    ConfirmDialog,
  },
  props: {
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
    helpItems: {
      type: Array,
      default: () => [],
    },
    editData: {
      type: Object,
      default: undefined,
    },
  },
  emits: ['change', 'close', 'save'],
  setup() {
    const formStore = useFormStore()
    return {
      formStore,
    }
  },
  data() {
    return {
      currentStep: 1,
      loading: false,
    }
  },
  watch: {
    currentStep(value) {
      this.$emit('change', value)
    },
  },
  mounted() {
    this.formStore.save(this.editData)
    document.addEventListener('keydown', (evt) => {
      if (evt.code === 'Escape') {
        this.cancel()
      }
    })
  },
  methods: {
    async cancel() {
      if (
        this.storedForm === '' ||
        _isEqual(this.storedForm, JSON.stringify(this.editData))
      ) {
        this.close()
      } else {
        const options = {
          type: 'warning',
          cancelLabel: this.$t('_global.cancel'),
          agreeLabel: this.$t('_global.continue'),
        }
        if (
          await this.$refs.confirm.open(
            this.$t('_global.cancel_changes'),
            options
          )
        ) {
          this.close()
        }
      }
    },
    close() {
      this.$emit('close')
      this.formStore.reset()
      this.reset()
    },
    reset() {
      this.currentStep = 1
      this.steps.forEach((item, index) => {
        const observer = this.formObserverGetter(index + 1)
        if (observer !== undefined) {
          observer.reset()
        }
      })
      this.loading = false
    },
    async validateStepObserver(step) {
      const observer = this.formObserverGetter(step)
      if (observer !== undefined && observer !== null) {
        const { valid } = await observer.validate()
        return valid
      }
      return true
    },
    async goToStep(currentStep, nextStep) {
      if (!(await this.validateStepObserver(currentStep))) {
        return
      }
      if (this.extraStepValidation) {
        if (!(await this.extraStepValidation(currentStep))) {
          return
        }
      }
      this.currentStep = nextStep
    },
    setCurrentStep(value) {
      this.currentStep = value
    },
    async submit() {
      if (!(await this.validateStepObserver(this.currentStep))) {
        return
      }
      this.loading = true
      this.$emit('save')
    },
  },
}
</script>

<style scoped lang="scss">
.v-stepper {
  box-shadow: none !important;
  background-color: white;
}

.v-stepper-header {
  box-shadow: none !important;
}

.v-stepper-item {
  color: #0066f8 !important;
  font-size: 18px;
  font-weight: 600;
}
</style>
