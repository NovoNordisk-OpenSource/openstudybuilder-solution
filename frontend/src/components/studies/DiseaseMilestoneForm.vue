<template>
  <SimpleFormDialog
    ref="form"
    :title="title"
    :help-items="helpItems"
    :help-text="$t('_help.StudyDefineForm.general')"
    :open="open"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="form.disease_milestone_type"
              :label="$t('DiseaseMilestone.disease_milestone_type')"
              data-cy="disease-milestone-type"
              :items="diseaseMilestoneTypes"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              :rules="[formRules.required]"
              clearable
              class="required"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-checkbox
              v-model="form.repetition_indicator"
              :label="$t('DiseaseMilestone.repetition_indicator')"
              data-cy="repetition-indicator"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script>
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import study from '@/api/study'
import terms from '@/api/controlledTerminology/terms'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    SimpleFormDialog,
  },
  inject: ['notificationHub', 'formRules'],
  props: {
    diseaseMilestone: {
      type: Object,
      default: undefined,
    },
    open: Boolean,
  },
  emits: ['close'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      selectedStudy: studiesGeneralStore.selectedStudy,
    }
  },
  data() {
    return {
      diseaseMilestoneTypes: [],
      form: {},
      helpItems: [
        'DiseaseMilestone.disease_milestone_type',
        'DiseaseMilestone.repetition_indicator',
      ],
    }
  },
  computed: {
    title() {
      return this.diseaseMilestone
        ? this.$t('DiseaseMilestoneForm.edit_title')
        : this.$t('DiseaseMilestoneForm.add_title')
    },
  },
  watch: {
    diseaseMilestone: {
      handler: function (newValue) {
        if (newValue) {
          study
            .getStudyDiseaseMilestone(this.selectedStudy.uid, newValue.uid)
            .then((resp) => {
              this.form = { ...resp.data }
            })
        } else {
          this.form = {}
        }
      },
      immediate: true,
    },
  },
  mounted() {
    terms.getTermsByCodelist('diseaseMilestoneTypes').then((resp) => {
      this.diseaseMilestoneTypes = resp.data.items
    })
  },
  methods: {
    close() {
      this.$emit('close')
      this.notificationHub.clearErrors()
      this.form = {}
      this.$refs.observer.reset()
    },
    async submit() {
      this.notificationHub.clearErrors()

      const data = { ...this.form }
      data.study_uid = this.selectedStudy.uid
      if (data.repetition_indicator === undefined) {
        data.repetition_indicator = false
      }
      if (!this.diseaseMilestone) {
        study.createStudyDiseaseMilestone(this.selectedStudy.uid, data).then(
          () => {
            this.$refs.form.working = false
            this.notificationHub.add({
              msg: this.$t('DiseaseMilestoneForm.add_success'),
            })
            this.close()
          },
          () => {
            this.$refs.form.working = false
          }
        )
      } else {
        study
          .updateStudyDiseaseMilestone(
            this.selectedStudy.uid,
            this.diseaseMilestone.uid,
            data
          )
          .then(
            () => {
              this.$refs.form.working = false
              this.notificationHub.add({
                msg: this.$t('DiseaseMilestoneForm.update_success'),
              })
              this.close()
            },
            () => {
              this.$refs.form.working = false
            }
          )
      }
    },
  },
}
</script>
