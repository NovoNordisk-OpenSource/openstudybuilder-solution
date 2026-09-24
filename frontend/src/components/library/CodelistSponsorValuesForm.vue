<template>
  <v-card data-cy="form-body" color="dfltBackground">
    <v-card-title class="d-flex align-center">
      <span class="dialog-title">{{
        $t('CodelistSponsorValuesForm.title')
      }}</span>
      <HelpButtonWithPanels :title="$t('_global.help')" :items="helpItems" />
    </v-card-title>
    <v-card-text>
      <div class="bg-white px-2">
        <v-form ref="observer">
          <v-row class="mt-4">
            <v-col>
              <v-text-field
                v-model="form.name"
                data-cy="sponsor-preffered-name"
                :label="$t('CodelistSponsorValuesForm.pref_name')"
                :rules="[formRules.required]"
                clearable
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="6">
              <v-switch
                v-model="form.template_parameter"
                :label="$t('CodelistSponsorValuesForm.tpl_parameter')"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col>
              <v-select
                v-model="form.codelist_type"
                data-cy="codelist-type"
                :label="$t('CodelistAttributesForm.codelist_type')"
                :items="codelistTypes"
                clearable
                :rules="[formRules.required]"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col>
              <v-switch
                v-model="form.is_ordinal"
                :label="$t('CodelistAttributesForm.is_ordinal')"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col>
              <v-textarea
                v-model="form.change_description"
                data-cy="change-description"
                :label="$t('HistoryTable.change_description')"
                :rules="[formRules.required]"
                rows="1"
                auto-grow
                clearable
                class="white pa-2"
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
      <v-btn
        data-cy="save-button"
        color="secondary"
        :loading="working"
        @click="submit"
      >
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
    HelpButtonWithPanels,
    ConfirmDialog,
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
        'CodelistSponsorValuesForm.pref_name',
        'CodelistSponsorValuesForm.tpl_parameter',
        'CodelistAttributesForm.codelist_type',
        'CodelistAttributesForm.is_ordinal',
      ],
      codelistTypes: ['Response', 'Standard'],
      working: false,
    }
  },
  watch: {
    modelValue: {
      handler(val) {
        if (val) {
          controlledTerminology
            .getCodelistNames(val.codelist_uid)
            .then((resp) => {
              this.form = {
                name: resp.data.name,
                template_parameter: resp.data.template_parameter,
                codelist_type: resp.data.codelist_type,
                is_ordinal: resp.data.is_ordinal,
              }
              this.formStore.save(this.form)
            })
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
      this.$emit('close')
      this.notificationHub.clearErrors()
      this.formStore.reset()
    },
    async submit() {
      const { valid } = await this.$refs.observer.validate()
      if (!valid) return

      this.notificationHub.clearErrors()

      this.working = true
      try {
        const resp = await controlledTerminology.updateCodelistNames(
          this.modelValue.codelist_uid,
          this.form
        )
        this.$emit('update:modelValue', resp.data)
        this.notificationHub.add({
          msg: this.$t('CodelistSponsorValuesForm.update_success'),
        })
        delete this.form.change_description
        this.close()
      } finally {
        this.working = false
      }
    },
  },
}
</script>
