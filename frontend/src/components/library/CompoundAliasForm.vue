<template>
  <HorizontalStepperForm
    ref="stepper"
    :title="title"
    :steps="steps"
    :form-observer-getter="getObserver"
    :editable="compoundAlias !== undefined && compoundAlias !== null"
    :help-items="helpItems"
    :edit-data="form"
    @close="close"
    @save="submit"
  >
    <template #[`step.compound`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-row>
          <v-col cols="12">
            <v-autocomplete
              v-model="form.compoundSimple"
              v-model:search="compoundSearch"
              :label="$t('CompoundAliasTable.compound_name')"
              :items="compounds"
              item-title="name"
              item-value="uid"
              return-object
              clearable
              hide-no-data
              :loading="loadingCompounds"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #[`step.alias`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.name"
              :label="$t('CompoundAliasForm.name')"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.name_sentence_case"
              :label="$t('CompoundAliasForm.sentence_case_name')"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <YesNoField
              v-model="form.is_preferred_synonym"
              :label="$t('CompoundAliasForm.is_preferred_synonym')"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-textarea
              v-model="form.definition"
              :label="$t('_global.definition')"
              clearable
              auto-grow
              rows="1"
            />
          </v-col>
        </v-row>
        <v-row v-if="compoundAliasUid">
          <v-col cols="12">
            <v-textarea
              v-model="form.change_description"
              :label="$t('HistoryTable.change_description')"
              clearable
              auto-grow
              rows="1"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </HorizontalStepperForm>
</template>

<script>
import compoundAliases from '@/api/concepts/compoundAliases'
import compounds from '@/api/concepts/compounds'
import compoundsSimple from '@/api/concepts/compoundsSimple'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import libConstants from '@/constants/libraries'
import YesNoField from '@/components/tools/YesNoField.vue'
import { useFormStore } from '@/stores/form'

export default {
  components: {
    HorizontalStepperForm,
    YesNoField,
  },
  inject: ['notificationHub', 'formRules'],
  props: {
    compoundAliasUid: {
      type: String,
      default: null,
    },
    formShown: Boolean,
  },
  emits: ['close', 'created', 'updated'],
  setup() {
    const formStore = useFormStore()
    return {
      formStore,
    }
  },
  data() {
    return {
      compounds: [],
      compoundAlias: null,
      compoundSearch: null,
      form: this.getInitialForm(),
      helpItems: [
        'CompoundAliasForm.step1_title',
        'CompoundAliasForm.name',
        'CompoundAliasForm.sentence_case_name',
        'CompoundAliasForm.is_preferred_synonym',
      ],
      loadingCompounds: false,
      steps: [
        { name: 'compound', title: this.$t('CompoundAliasForm.step1_title') },
        { name: 'alias', title: this.$t('CompoundAliasForm.step2_title') },
      ],
    }
  },
  computed: {
    title() {
      return this.compoundAlias
        ? this.$t('CompoundAliasForm.edit_title')
        : this.$t('CompoundAliasForm.add_title')
    },
    brandNames() {
      if (
        this.form.compound &&
        this.form.compound.brands &&
        this.form.compound.brands.length
      ) {
        return this.form.compound.brands.map((item) => item.name).join(', ')
      }
      return ''
    },
    substances() {
      if (
        this.form.compound &&
        this.form.compound.substances &&
        this.form.compound.substances.length
      ) {
        return this.form.compound.substances
          .map((item) => `${item.substance_name} (${item.substance_unii})`)
          .join(', ')
      }
      return ''
    },
    pharmacologicalClass() {
      if (
        this.form.compound &&
        this.form.compound.substances &&
        this.form.compound.substances.length
      ) {
        return this.form.compound.substances
          .map((item) => item.pclass_name)
          .filter((pclass) => pclass !== undefined && pclass !== null)
          .join(', ')
      }
      return ''
    },
  },
  watch: {
    formShown(value) {
      if (value) {
        this.loadFormData()
      } else {
        this.compoundAlias = null
        this.compound = null
      }
    },
    compoundAlias: {
      handler: function (value) {
        if (value) {
          this.form = { ...value }
        }
      },
      immediate: true,
    },
    'form.compoundSimple'(value) {
      if (value && value.uid) {
        compounds.getObject(value.uid).then((resp) => {
          this.form.compound = resp.data
        })
      }
    },
    'form.name'(value) {
      if (value) {
        this.form.name_sentence_case = value.toLowerCase()
      }
    },
    compoundSearch(value) {
      value && value !== this.form.compoundSimple && this.fetchCompounds(value)
    },
  },
  mounted() {
    this.loadFormData()
  },
  methods: {
    close() {
      this.$emit('close')
      this.notificationHub.clearErrors()
      this.compounds = []
      this.form = this.getInitialForm()
      this.$refs.stepper.reset()
    },
    getInitialForm() {
      return {
        compoundSimple: null,
        compound: {},
        isPreferredSynonym: false,
      }
    },
    loadFormData() {
      this.fetchCompounds('')
      if (this.compoundAliasUid !== null) {
        compoundAliases.getObject(this.compoundAliasUid).then((resp) => {
          this.compoundAlias = resp.data
          compounds
            .getObject(this.compoundAlias.compound.uid)
            .then((aliasResp) => {
              this.form.compoundSimple = aliasResp.data
            })
        })
      }
    },
    getObserver(step) {
      return this.$refs[`observer_${step}`]
    },
    async add(data) {
      data.library_name = libConstants.LIBRARY_SPONSOR
      await compoundAliases.create(data)
      this.$emit('created')
      this.notificationHub.add({
        msg: this.$t('CompoundAliasForm.add_success'),
        type: 'success',
      })
    },
    async update(data) {
      await compoundAliases.update(this.compoundAlias.uid, data)
      this.$emit('updated')
      this.notificationHub.add({
        msg: this.$t('CompoundAliasForm.update_success'),
        type: 'success',
      })
    },
    async submit() {
      this.notificationHub.clearErrors()

      if (this.formStore.isEmpty || this.formStore.isEqual(this.form)) {
        this.close()
        this.notificationHub.add({
          type: 'info',
          msg: this.$t('_global.no_changes'),
        })
        return
      }
      const data = { ...this.form }
      data.compound_uid = data.compound.uid
      delete data.compound
      try {
        if (!this.compoundAliasUid) {
          await this.add(data)
        } else {
          await this.update(data)
        }
        this.close()
      } catch (_error) {
        this.$refs.stepper.loading = false
      }
    },
    fetchCompounds(search) {
      const params = {
        filters: {
          name: { v: [search], op: 'co' },
        },
        sort_by: {
          name: true,
        },
      }
      this.loadingCompounds = true
      compoundsSimple.getFiltered(params).then((resp) => {
        this.compounds = resp.data.items
        this.loadingCompounds = false
      })
    },
  },
}
</script>
