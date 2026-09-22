<template>
  <SimpleFormDialog
    ref="form"
    :title="$t('DictionaryTermForm.title', { dictionaryName })"
    :help-items="helpItems"
    :open="open"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.dictionary_id"
              :label="`${dictionaryName} ID`"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.name"
              :label="$t('_global.name')"
              clearable
              :rules="[formRules.required]"
              @blur="setLowerCase"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.name_sentence_case"
              :label="$t('DictionaryTermForm.lower_case_name')"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.abbreviation"
              :label="$t('DictionaryTermForm.abbreviation')"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-textarea
              v-model="form.definition"
              :label="$t('DictionaryTermForm.definition')"
              clearable
              rows="1"
              auto-grow
            />
          </v-col>
        </v-row>
        <v-row v-if="editedTerm">
          <v-col cols="12">
            <v-textarea
              v-model="form.change_description"
              :label="$t('_global.change_description')"
              clearable
              rows="1"
              auto-grow
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script>
import dictionaries from '@/api/dictionaries'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import { useFormStore } from '@/stores/form'
import _isEmpty from 'lodash/isEmpty'

export default {
  components: {
    SimpleFormDialog,
  },
  inject: ['notificationHub', 'formRules'],
  props: {
    editedTerm: {
      type: Object,
      default: null,
    },
    editedTermCategory: {
      type: String,
      default: null,
    },
    dictionaryName: {
      type: String,
      default: null,
    },
    open: Boolean,
  },
  emits: ['close', 'save'],
  setup() {
    const formStore = useFormStore()

    return {
      formStore,
    }
  },
  data() {
    return {
      helpItems: [
        'DictionaryTermForm.dictionary_id',
        'DictionaryTermForm.name',
        'DictionaryTermForm.lower_case_name',
        'DictionaryTermForm.abbreviation',
        'DictionaryTermForm.definition',
      ],
      form: {},
    }
  },
  watch: {
    editedTerm: {
      handler(value) {
        if (!_isEmpty(value)) {
          dictionaries.retrieve(value.term_uid).then((resp) => {
            this.initForm(resp.data)
            this.form.codelist_uid = this.editedTermCategory
            this.formStore.save(this.form)
          })
        }
      },
      immediate: true,
    },
  },
  mounted() {
    if (this.editedTerm) {
      this.initForm(this.editedTerm)
      this.form.change_description = this.$t(
        'DictionaryTermForm.default_change_descr'
      )
    }
    this.form.codelist_uid = this.editedTermCategory
    this.formStore.save(this.form)
  },
  methods: {
    isUpdate() {
      return Boolean(this.editedTerm)
    },
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
          await this.$refs.form.confirm(
            this.$t('_global.cancel_changes'),
            options
          )
        ) {
          this.close()
        }
      }
    },
    close() {
      this.notificationHub.clearErrors()
      this.form = {}
      this.$refs.form.working = false
      this.formStore.reset()
      this.$emit('close')
    },
    submit() {
      if (this.editedTerm) {
        this.edit()
      } else {
        this.create()
      }
    },
    edit() {
      this.notificationHub.clearErrors()

      const data = JSON.parse(JSON.stringify(this.form))
      dictionaries.edit(this.editedTerm.term_uid, data).then(
        () => {
          this.notificationHub.add({
            msg: this.$t('DictionaryTermForm.update_success'),
          })
          this.$emit('save')
          this.close()
        },
        () => {
          this.$refs.form.working = false
        }
      )
    },
    async create() {
      this.notificationHub.clearErrors()

      this.form.library_name = this.dictionaryName
      this.form.codelist_uid = this.editedTermCategory
      const data = JSON.parse(JSON.stringify(this.form))
      dictionaries.create(data).then(
        () => {
          this.notificationHub.add({
            msg: this.$t('DictionaryTermForm.create_success'),
          })
          this.$emit('save')
          this.close()
        },
        () => {
          this.$refs.form.working = false
        }
      )
    },
    initForm(form) {
      this.form = form
    },
    setLowerCase() {
      if (this.form.name) {
        this.form.name_sentence_case = this.form.name.toLowerCase()
      }
    },
  },
}
</script>
