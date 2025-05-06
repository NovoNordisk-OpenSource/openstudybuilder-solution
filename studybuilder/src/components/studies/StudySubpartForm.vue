<template>
  <HorizontalStepperForm
    ref="stepper"
    :title="$t('StudySubparts.add_subpart')"
    :steps="steps"
    :form-observer-getter="getObserver"
    :extra-step-validation="extraValidation"
    @close="cancel"
    @save="submit"
  >
    <template #[`step.method`]>
      <v-radio-group v-model="method" color="primary">
        <v-radio :label="$t('StudySubparts.create_new')" value="create" />
        <v-radio :label="$t('StudySubparts.add_existing')" value="select" />
      </v-radio-group>
    </template>
    <template #[`step.select`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-card class="px-4 mb-2">
          <v-card-title class="dialog-title">
            {{ $t('StudySubparts.selected_substudy') }}
          </v-card-title>
          <v-card-text>
            <v-data-table
              key="uid"
              :headers="selectedHeaders"
              :items="[selectedSubstudy]"
              hide-default-footer
            />
          </v-card-text>
        </v-card>
        <v-card class="px-4 mb-2">
          <v-card-title class="dialog-title">
            {{ $t('StudySubparts.available_studies') }}
          </v-card-title>
          <v-card-text>
            <NNTable
              item-value="uid"
              :modifiable-table="false"
              :headers="headers"
              :items="studies"
              :items-length="total"
              hide-default-switches
              column-data-resource="studies"
              @filter="fetchAvailableStudies"
            >
              <template #[`item.select`]="{ item }">
                <v-btn
                  icon="mdi-content-copy"
                  :title="$t('StudySelectionTable.copy_item')"
                  variant="text"
                  @click="selectStudy(item)"
                />
              </template>
            </NNTable>
          </v-card-text>
        </v-card>
      </v-form>
    </template>
    <template #[`step.create`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-row>
          <v-col cols="8">
            <v-text-field
              :label="$t('StudyForm.project_id')"
              :model-value="
                selectedStudy.current_metadata.identification_metadata
                  .project_number
              "
              disabled
              variant="filled"
              hide-details
              data-cy="project-name"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="8">
            <v-text-field
              :label="$t('StudyForm.project_name')"
              :model-value="
                selectedStudy.current_metadata.identification_metadata
                  .project_name
              "
              disabled
              variant="filled"
              hide-details
            />
          </v-col>
        </v-row>
        <!-- Brand name is not yet implemented in api -->
        <v-row>
          <v-col cols="8">
            <v-text-field
              :label="$t('StudyForm.brand_name')"
              disabled
              variant="filled"
              hide-details
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="8">
            <v-text-field
              v-model="form.study_subpart_acronym"
              :label="$t('StudyForm.subpart_acronym')"
              density="compact"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="8">
            <v-text-field
              v-model="form.study_acronym"
              :label="$t('StudyForm.acronym')"
              density="compact"
              disabled
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="8">
            <v-textarea
              v-model="form.description"
              :label="$t('_global.description')"
              density="compact"
              clearable
              auto-grow
              rows="3"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #[`step.define`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-card v-if="method === 'select'" class="px-4 mb-2">
          <v-card-title class="dialog-title">
            {{ $t('StudySubparts.selected_substudy') }}
          </v-card-title>
          <v-card-text>
            <v-data-table
              key="uid"
              :headers="selectedHeaders"
              :items="[selectedSubstudy]"
            >
              <template #bottom />
            </v-data-table>
          </v-card-text>
        </v-card>
        <v-card class="px-4" flat>
          <v-card-title class="dialog-title">
            {{ $t('StudySubparts.subpart_attrs') }}
          </v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="3" class="text-h6 dialog-title">
                {{ $t('StudySubparts.derived_subpart_id') }}
              </v-col>
              <v-col cols="4">
                <v-text-field
                  :model-value="form.study_number"
                  density="compact"
                  disabled
                  variant="filled"
                  hide-details
                />
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="3" class="dialog-title text-h6">
                {{ $t('StudySubparts.study_subpart_acronym') }}
              </v-col>
              <v-col cols="4">
                <v-text-field
                  v-model="form.study_subpart_acronym"
                  density="compact"
                  :rules="[formRules.required]"
                />
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="8">
                <span class="dialog-title text-h6">
                  {{ $t('_global.description') }}
                </span>
                <v-textarea
                  v-model="form.description"
                  density="compact"
                  clearable
                  auto-grow
                  rows="3"
                />
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-form>
    </template>
  </HorizontalStepperForm>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
</template>

<script>
import { computed } from 'vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import studies from '@/api/study'
import _isEmpty from 'lodash/isEmpty'
import filteringParameters from '@/utils/filteringParameters'
import NNTable from '@/components/tools/NNTable.vue'
import { useFormStore } from '@/stores/form'
import { useStudiesManageStore } from '@/stores/studies-manage'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    ConfirmDialog,
    HorizontalStepperForm,
    NNTable,
  },
  inject: ['eventBusEmit', 'formRules'],
  emits: ['close'],
  setup() {
    const formStore = useFormStore()
    const studiesGeneralStore = useStudiesGeneralStore()
    const studiesManageStore = useStudiesManageStore()
    return {
      formStore,
      addStudy: studiesManageStore.addStudy,
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
    }
  },
  data() {
    return {
      form: {},
      steps: this.getInitialSteps(),
      selectSteps: [
        { name: 'method', title: this.$t('StudySubparts.select_method') },
        {
          name: 'select',
          title: this.$t('StudySubparts.select_study_subpart'),
        },
        { name: 'define', title: this.$t('StudySubparts.define_subpart') },
      ],
      createSteps: [
        { name: 'method', title: this.$t('StudySubparts.select_method') },
        { name: 'create', title: this.$t('StudySubparts.create_subpart') },
      ],
      method: 'create',
      headers: [
        { title: '', key: 'select', width: '5%' },
        {
          title: this.$t('StudySubparts.study_id'),
          key: 'current_metadata.identification_metadata.study_id',
        },
        {
          title: this.$t('StudyTable.acronym'),
          key: 'current_metadata.identification_metadata.study_acronym',
        },
        {
          title: this.$t('StudyTable.title'),
          key: 'current_metadata.study_description.study_title',
        },
        {
          title: this.$t('_global.description'),
          key: 'current_metadata.identification_metadata.description',
        },
      ],
      selectedHeaders: [
        {
          title: this.$t('StudyTable.acronym'),
          key: 'current_metadata.identification_metadata.study_acronym',
        },
        {
          title: this.$t('StudyTable.title'),
          key: 'current_metadata.study_description.study_title',
        },
        {
          title: this.$t('_global.description'),
          key: 'current_metadata.identification_metadata.description',
        },
      ],
      studies: [],
      selectedSubstudy: {},
      options: {},
      total: 0,
    }
  },
  watch: {
    method(value) {
      this.steps = value === 'select' ? this.selectSteps : this.createSteps
      if (value === 'select') {
        this.eventBusEmit('notification', {
          msg: this.$t('StudySubparts.select_warning'),
          type: 'warning',
          timeout: 15000,
        })
      }
      this.form = {}
    },
  },
  mounted() {
    this.initForm()
  },
  methods: {
    initForm() {
      this.form = {
        study_acronym:
          this.selectedStudy.current_metadata.identification_metadata
            .study_acronym,
      }
      this.formStore.save(this.form)
    },
    selectStudy(study) {
      this.selectedSubstudy = study
      this.form.description =
        study.current_metadata.identification_metadata.description
      this.form.study_acronym =
        study.current_metadata.identification_metadata.study_acronym
    },
    fetchAvailableStudies(filters, options, filtersUpdated) {
      if (filters) {
        const filtersObj = JSON.parse(filters)
        filtersObj.study_subpart_uids = { v: [] }
        filtersObj.study_parent_part = { v: [] }
        filtersObj.uid = { v: [this.selectedStudy.uid], op: 'ne' }
        filtersObj['current_metadata.identification_metadata.study_acronym'] = {
          v: [null],
          op: 'ne',
        }
        filtersObj['current_metadata.identification_metadata.project_number'] =
          {
            v: [
              this.selectedStudy.current_metadata.identification_metadata
                .project_number,
            ],
          }
        filters = filtersObj
      } else {
        filters = {
          uid: { v: [this.selectedStudy.uid], op: 'ne' },
          study_subpart_uids: { v: [] },
          study_parent_part: { v: [] },
          'current_metadata.identification_metadata.study_number': { v: [] },
        }
      }
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      studies.get(params).then((resp) => {
        this.studies = resp.data.items
        this.total = resp.data.total
      })
    },
    async extraValidation(step) {
      if (step !== 2) {
        return true
      }
      if (this.method === 'select' && _isEmpty(this.selectedSubstudy)) {
        this.eventBusEmit('notification', {
          msg: this.$t('StudySubparts.select_study_warning'),
          type: 'info',
        })
        return false
      }
      return true
    },
    async cancel() {
      this.close()
    },
    close() {
      this.$emit('close')
      this.method = 'create'
      this.steps = this.selectSteps
      this.form = {}
      this.selectedSubstudy = {}
      this.formStore.reset()
      this.$refs.stepper.reset()
      this.$refs.stepper.loading = false
    },
    submit() {
      if (this.method === 'select') {
        this.selectedSubstudy.study_parent_part_uid = this.selectedStudy.uid
        this.selectedSubstudy.current_metadata.identification_metadata.description =
          this.form.description
        this.selectedSubstudy.current_metadata.identification_metadata.study_subpart_acronym =
          this.form.study_subpart_acronym
        studies
          .updateStudy(this.selectedSubstudy.uid, this.selectedSubstudy)
          .then(() => {
            this.eventBusEmit('notification', {
              msg: this.$t('StudySubparts.subpart_created'),
            })
            this.$refs.stepper.loading = false
            this.close()
          })
      } else {
        this.form.project_number =
          this.selectedStudy.current_metadata.identification_metadata.project_number
        this.form.study_parent_part_uid = this.selectedStudy.uid
        this.addStudy(this.form).then(() => {
          this.eventBusEmit('notification', {
            msg: this.$t('StudySubparts.subpart_created'),
          })
          this.close()
        })
      }
    },
    getObserver(step) {
      return this.$refs[`observer_${step}`]
    },
    getInitialSteps() {
      return [
        { name: 'method', title: this.$t('StudySubparts.select_method') },
        { name: 'create', title: this.$t('StudySubparts.create_subpart') },
      ]
    },
  },
}
</script>
