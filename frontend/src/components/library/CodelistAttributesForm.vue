<template>
  <v-card color="dfltBackground">
    <v-card-title class="d-flex align-center">
      <span class="dialog-title">{{ $t('CodelistAttributesForm.title') }}</span>
      <HelpButtonWithPanels :title="$t('_global.help')" :items="helpItems" />
    </v-card-title>
    <v-card-text>
      <div class="white px-2">
        <v-form ref="observer">
          <v-row class="mt-4">
            <v-col>
              <v-text-field
                v-model="form.name"
                :label="$t('CodelistAttributesForm.name')"
                clearable
                :rules="[formRules.required]"
              />
            </v-col>
          </v-row>
          <v-row class="mt-4">
            <v-col>
              <v-text-field
                v-model="form.submission_value"
                :label="$t('CodelistAttributesForm.subm_value')"
                clearable
                :rules="[formRules.required]"
              />
            </v-col>
          </v-row>
          <v-row class="mt-4">
            <v-col>
              <v-text-field
                v-model="form.nci_preferred_name"
                :label="$t('CodelistAttributesForm.nci_pref_name')"
                clearable
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col>
              <v-switch
                v-model="form.extensible"
                :label="$t('CodelistAttributesForm.extensible')"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col>
              <v-textarea
                v-model="form.definition"
                :label="$t('CodelistAttributesForm.definition')"
                rows="1"
                clearable
                auto-grow
                :rules="[formRules.required]"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col>
              <v-textarea
                v-model="form.change_description"
                :label="$t('HistoryTable.change_description')"
                :rows="1"
                clearable
                auto-grow
                :rules="[formRules.required]"
              />
            </v-col>
          </v-row>
        </v-form>
      </div>
    </v-card-text>
    <v-card-actions class="pb-6 px-6">
      <v-spacer />
      <v-btn class="secondary-btn" color="white" @click="cancel">
        {{ $t('_global.cancel') }}
      </v-btn>
      <v-btn color="secondary" :loading="working" @click="submit">
        {{ $t('_global.save') }}
      </v-btn>
    </v-card-actions>
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  </v-card>
</template>

<script>
import controlledTerminology from '@/api/controlledTerminology'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import { useFormStore } from '@/stores/form'

export default {
  components: {
    ConfirmDialog,
    HelpButtonWithPanels,
  },
  inject: ['notificationHub', 'formRules'],
  props: {
    modelValue: {
      type: Object,
      default: null,
    },
  },
  emits: ['close', 'update:modelValue'],
  setup() {
    const formStore = useFormStore()
    return {
      formStore,
    }
  },
  data() {
    return {
      form: {},
      helpItems: [
        'CodelistAttributesForm.name',
        'CodelistAttributesForm.subm_value',
        'CodelistAttributesForm.nci_pref_name',
        'CodelistAttributesForm.extensible',
        'CodelistAttributesForm.definition',
      ],
      working: false,
    }
  },
  watch: {
    modelValue: {
      handler(val) {
        if (val) {
          this.form = {
            name: val.name,
            submission_value: val.submission_value,
            nci_preferred_name: val.nci_preferred_name,
            extensible: val.extensible,
            definition: val.definition,
          }
          this.formStore.save(this.form)
        }
      },
      immediate: true,
    },
  },
  methods: {
    async cancel() {
      if (this.formStore.isEmpty || this.formStore.isEqual(this.form)) {
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
      this.formStore.reset()
      this.$emit('close')
      this.notificationHub.clearErrors()
      this.form = {}
    },
    async submit() {
      const { valid } = await this.$refs.observer.validate()
      if (!valid) return

      this.notificationHub.clearErrors()

      this.working = true
      try {
        const resp = await controlledTerminology.updateCodelistAttributes(
          this.modelValue.codelist_uid,
          this.form
        )
        this.$emit('update:modelValue', resp.data)
        this.notificationHub.add({
          msg: this.$t('CodelistAttributesForm.update_success'),
        })
        this.close()
      } finally {
        this.working = false
      }
    },
  },
}
</script>
