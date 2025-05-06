<template>
  <StudySelectionEditForm
    v-if="studyObjective"
    ref="form"
    :title="$t('StudyObjectiveEditForm.title')"
    :study-selection="editedObject"
    :template="template"
    :library-name="library.name"
    object-type="objective"
    :open="open"
    :get-object-from-selection="(selection) => selection.objective"
    @init-form="initForm"
    @submit="submit"
    @close="$emit('close')"
  >
    <template #formFields="{ editTemplate, form }">
      <p class="mt-6 text-secondary text-h6">
        {{ $t('StudyObjectiveEditForm.select_level') }}
      </p>
      <v-row>
        <v-col cols="11">
          <v-select
            v-model="form.objective_level"
            :label="$t('StudyObjectiveForm.objective_level')"
            :items="objectiveLevels"
            item-title="sponsor_preferred_name"
            return-object
            dense
            clearable
            style="max-width: 400px"
            :disabled="editTemplate"
          />
        </v-col>
      </v-row>
    </template>
  </StudySelectionEditForm>
</template>

<script>
import _isEmpty from 'lodash/isEmpty'
import formUtils from '@/utils/forms'
import instances from '@/utils/instances'
import study from '@/api/study'
import StudySelectionEditForm from './StudySelectionEditForm.vue'
import constants from '@/constants/libraries'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useStudiesObjectivesStore } from '@/stores/studies-objectives'
import { computed } from 'vue'

export default {
  components: {
    StudySelectionEditForm,
  },
  inject: ['eventBusEmit'],
  props: {
    studyObjective: {
      type: Object,
      default: undefined,
    },
    open: Boolean,
  },
  emits: ['close', 'updated'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    const studiesObjectivesStore = useStudiesObjectivesStore()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
      objectiveLevels: computed(() => studiesGeneralStore.objectiveLevels),
      updateStudyObjective: studiesObjectivesStore.updateStudyObjective,
    }
  },
  data() {
    return {
      editedObject: {},
    }
  },
  computed: {
    template() {
      return this.editedObject.objective
        ? this.editedObject.objective.template
        : this.editedObject.template
    },
    library() {
      return {
        name: constants.LIBRARY_USER_DEFINED,
      }
    },
  },
  watch: {
    studyObjective: {
      handler: function (value) {
        if (value) {
          study
            .getStudyObjective(
              this.selectedStudy.uid,
              value.study_objective_uid
            )
            .then((resp) => {
              this.editedObject = resp.data
            })
        }
      },
      immediate: true,
    },
  },
  methods: {
    initForm(form) {
      form.objective_level = this.editedObject.objective_level
      this.originalForm = JSON.parse(JSON.stringify(form))
    },
    async getStudyObjectiveNamePreview(parameters) {
      const objectiveData = {
        objective_template_uid: this.editedObject.objective.template.uid,
        parameter_terms: await instances.formatParameterValues(parameters),
        library_name: this.editedObject.objective.library.name,
      }
      const resp = await study.getStudyObjectivePreview(
        this.selectedStudy.uid,
        { objective_data: objectiveData }
      )
      return resp.data.objective.name
    },
    async submit(newTemplate, form, parameters) {
      const data = formUtils.getDifferences(this.originalForm, form)

      if (newTemplate) {
        data.parameters = parameters
      } else if (!this.editedObject.objective) {
        data.parameters = parameters
      } else {
        const namePreview = await this.getStudyObjectiveNamePreview(parameters)
        if (namePreview !== this.editedObject.objective.name) {
          data.parameters = parameters
        }
      }
      if (_isEmpty(data)) {
        this.eventBusEmit('notification', {
          msg: this.$t('_global.no_changes'),
          type: 'info',
        })
        this.$refs.form.close()
        return
      }
      const args = {
        studyUid: this.selectedStudy.uid,
        studyObjectiveUid: this.editedObject.study_objective_uid,
        form: data,
        library: this.library,
      }
      if (newTemplate) {
        args.template = newTemplate
      } else {
        args.template = this.template
      }
      this.updateStudyObjective(args)
        .then(() => {
          this.eventBusEmit('notification', {
            msg: this.$t('StudyObjectiveEditForm.objective_updated'),
          })
          this.$emit('updated')
          this.$refs.form.close()
        })
        .catch((err) => {
          console.log(err)
        })
    },
  },
}
</script>
