<template>
  <SimpleFormDialog
    ref="form"
    :title="title"
    :help-items="helpItems"
    :open="open"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col cols="12">
            <v-autocomplete
              v-model="form.arm_uids"
              :label="$t('StudyCohorts.study_arm')"
              data-cy="study-arm"
              :items="arms"
              item-title="name"
              item-value="arm_uid"
              clearable
              multiple
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-autocomplete
              v-model="form.branch_arm_uids"
              :label="$t('StudyCohorts.study_branch_arm')"
              data-cy="branch-arm"
              :items="branches"
              item-title="name"
              item-value="branch_arm_uid"
              clearable
              multiple
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.name"
              :label="$t('StudyCohorts.cohort_name')"
              data-cy="study-cohort-name"
              :rules="[formRules.required, formRules.max(form.name, 200)]"
              clearable
              class="required"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.short_name"
              :label="$t('StudyCohorts.cohort_short_name')"
              data-cy="study-cohort-short-name"
              :rules="[formRules.required, formRules.max(form.short_name, 20)]"
              clearable
              class="required"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.code"
              :label="$t('StudyCohorts.cohort_code')"
              :rules="[formRules.required, formRules.max(form.code, 20)]"
              data-cy="study-cohort-code"
              clearable
              class="required"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              :disabled="!form.arm_uids"
              :model-value="form.number_of_subjects"
              :label="$t('StudyCohorts.number_of_subjects')"
              :rules="[
                formRules.min_value(form.number_of_subjects, 1),
                numberOfSubjectsMaxValueRule(
                  form.number_of_subjects,
                  findMaxNuberOfSubjects()
                ),
              ]"
              data-cy="study-cohort-planned-number-of-subjects"
              type="number"
              clearable
              @update:model-value="
                form.number_of_subjects = $event !== '' ? $event : null
              "
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.description"
              :label="$t('_global.description')"
              data-cy="study-cohort-description"
              clearable
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script>
import arms from '@/api/arms'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useFormStore } from '@/stores/form'

export default {
  components: {
    SimpleFormDialog,
  },
  inject: ['notificationHub', 'formRules'],
  props: {
    editedCohort: {
      type: Object,
      default: undefined,
    },
    arms: {
      type: Array,
      default: () => [],
    },
    branches: {
      type: Array,
      default: () => [],
    },
    open: Boolean,
  },
  emits: ['close'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    const formStore = useFormStore()
    return {
      selectedStudy: studiesGeneralStore.selectedStudy,
      formStore,
    }
  },
  data() {
    return {
      form: {},
      helpItems: [],
    }
  },
  computed: {
    title() {
      return Object.keys(this.editedCohort).length !== 0
        ? this.$t('StudyCohorts.edit_cohort')
        : this.$t('StudyCohorts.add_cohort')
    },
  },
  watch: {
    editedCohort(value) {
      if (Object.keys(value).length !== 0) {
        arms
          .getStudyCohort(this.selectedStudy.uid, value.cohort_uid)
          .then((resp) => {
            this.form = JSON.parse(JSON.stringify(resp.data))
            this.form.arm_uids = resp.data.arm_roots
              ? resp.data.arm_roots.map((el) => el.arm_uid)
              : null
            this.form.branch_arm_uids = resp.data.branch_arm_roots
              ? resp.data.branch_arm_roots.map((el) => el.branch_arm_uid)
              : null
            this.formStore.save(this.form)
          })
      }
    },
  },
  mounted() {
    if (Object.keys(this.editedCohort).length !== 0) {
      this.form = JSON.parse(JSON.stringify(this.editedCohort))
      this.form.arm_uids = this.editedCohort.arm_roots
        ? this.editedCohort.arm_roots.map((el) => el.arm_uid)
        : null
      this.form.branch_arm_uids = this.editedCohort.branch_arm_roots
        ? this.editedCohort.branch_arm_roots.map((el) => el.branch_arm_uid)
        : null
      this.formStore.save(this.form)
    }
  },
  methods: {
    // This rule is same as max_value generic rule but with custom message
    numberOfSubjectsMaxValueRule(value, max) {
      let result = true
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          result =
            value.length > 0 &&
            value.every((val) => this.formRules.max_value(val, max))
        } else {
          result = Number(value) <= Number(max)
        }
      }
      return result || this.$t('StudyCohorts.number_of_subjects_exceeds')
    },
    async submit() {
      this.notificationHub.clearErrors()

      if (Object.keys(this.editedCohort).length !== 0) {
        this.edit()
      } else {
        this.create()
      }
    },
    async create() {
      arms.createCohort(this.selectedStudy.uid, this.form).then(
        () => {
          this.notificationHub.add({
            msg: this.$t('StudyCohorts.cohort_created'),
          })
          this.close()
        },
        () => {
          this.$refs.form.working = false
        }
      )
    },
    edit() {
      arms
        .editCohort(
          this.selectedStudy.uid,
          this.editedCohort.cohort_uid,
          this.form
        )
        .then(
          () => {
            this.notificationHub.add({
              msg: this.$t('StudyCohorts.cohort_updated'),
            })
            this.close()
          },
          () => {
            this.$refs.form.working = false
          }
        )
    },
    close() {
      this.notificationHub.clearErrors()
      this.form = {}
      this.formStore.reset()
      this.$refs.observer.reset()
      this.$emit('close')
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
    findMaxNuberOfSubjects() {
      let subjectsSum = 0
      if (this.form.arm_uids) {
        this.form.arm_uids.forEach((el) => {
          subjectsSum += this.arms.find(
            (e) => e.arm_uid === el
          ).number_of_subjects
        })
      }
      return subjectsSum
    },
  },
}
</script>
