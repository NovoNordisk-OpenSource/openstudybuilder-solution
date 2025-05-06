<template>
  <SimpleFormDialog
    ref="form"
    :title="title"
    :help-items="helpItems"
    :help-text="$t('_help.StudyDefineForm.general')"
    :open="open"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-alert
        v-if="studyEpoch && studyEpoch.study_visit_count > 0"
        type="warning"
      >
        {{
          $t('StudyEpochForm.epoch_linked_to_visits_warning', {
            epoch: studyEpoch.epoch_name,
          })
        }}
      </v-alert>
      <v-form ref="observer">
        <v-row>
          <v-col cols="6">
            <v-autocomplete
              v-model="form.epoch_type"
              :label="$t('StudyEpochForm.epoch_type')"
              :items="uniqueTypeGroups"
              item-title="type_name"
              item-value="type"
              density="compact"
              :rules="[formRules.required]"
              clearable
              data-cy="epoch-type"
              :disabled="studyEpoch ? true : false"
              class="required"
              @update:model-value="setEpochGroups()"
              @click:clear="setEpochGroups()"
            />
          </v-col>
          <v-col cols="6">
            <v-autocomplete
              v-model="form.epoch_subtype"
              :label="$t('StudyEpochForm.epoch_subtype')"
              :items="subtypeGroups"
              item-title="subtype_name"
              item-value="subtype"
              density="compact"
              :rules="[formRules.required]"
              clearable
              data-cy="epoch-subtype"
              :disabled="studyEpoch ? true : false"
              class="required"
              @update:model-value="setEpochGroups()"
              @click:clear="setEpochGroups()"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              :key="typeTrigger"
              v-model="epochDisplay"
              data-cy="select-epoch"
              :label="$t('StudyEpochForm.name')"
              density="compact"
              disabled
              variant="filled"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-textarea
              id="startRule"
              v-model="form.start_rule"
              data-cy="epoch-start-rule"
              :label="$t('StudyEpochForm.start_rule')"
              rows="1"
              auto-grow
              density="compact"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-textarea
              id="endRule"
              v-model="form.end_rule"
              data-cy="epoch-end-rule"
              :label="$t('StudyEpochForm.stop_rule')"
              rows="1"
              auto-grow
              density="compact"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-textarea
              id="description"
              v-model="form.description"
              data-cy="description"
              :label="$t('StudyEpochForm.description')"
              rows="1"
              auto-grow
              density="compact"
            />
          </v-col>
        </v-row>
        <div v-if="studyEpoch">
          <label class="v-label required">{{
            $t('_global.change_description')
          }}</label>
          <v-textarea
            v-model="form.change_description"
            :rules="[formRules.required]"
            density="compact"
            clearable
            rows="1"
            auto-grow
          />
        </div>
        <div class="mt-4">
          <label class="v-label">{{ $t('StudyEpochForm.color') }}</label>
          <v-color-picker
            v-model="colorHash"
            data-cy="epoch-color-picker"
            clearable
            show-swatches
            hide-canvas
            hide-sliders
            swatches-max-height="300px"
          />
        </div>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script>
import _isEmpty from 'lodash/isEmpty'
import _isEqual from 'lodash/isEqual'
import units from '@/api/units'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import studyEpochs from '../../api/studyEpochs'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useEpochsStore } from '@/stores/studies-epochs'
import { computed } from 'vue'

export default {
  components: {
    SimpleFormDialog,
  },
  inject: ['eventBusEmit', 'formRules'],
  props: {
    studyEpoch: {
      type: Object,
      default: undefined,
    },
    open: Boolean,
  },
  emits: ['close'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    const epochsStore = useEpochsStore()
    return {
      selectedStudy: studiesGeneralStore.selectedStudy,
      studyEpochs: computed(() => epochsStore.studyEpochs),
      groups: computed(() => epochsStore.allowedConfigs),
      updateStudyEpoch: epochsStore.updateStudyEpoch,
      fetchAllowedConfigs: epochsStore.fetchAllowedConfigs,
      addStudyEpoch: epochsStore.addStudyEpoch,
      fetchStudyEpochs: epochsStore.fetchStudyEpochs,
    }
  },
  data() {
    return {
      colorHash: null,
      epochs: [],
      form: {},
      helpItems: [
        'StudyEpochForm.name',
        'StudyEpochForm.epoch_type',
        'StudyEpochForm.epoch_subtype',
        'StudyEpochForm.description',
        'StudyEpochForm.start_rule',
        'StudyEpochForm.stop_rule',
        'StudyEpochForm.epoch_time_unit',
        'StudyEpochForm.expected_epoch_duration',
        'StudyEpochForm.color',
      ],
      timeUnits: [],
      typeTrigger: 0,
      typeGroups: [],
      subtypeGroups: [],
      epochDisplay: '',
    }
  },
  computed: {
    uniqueTypeGroups() {
      const result = []
      for (let group of this.typeGroups) {
        if (!result.find((item) => item.type === group.type)) {
          result.push(group)
        }
      }
      return result
    },
    title() {
      return this.studyEpoch
        ? this.$t('StudyEpochForm.edit_title')
        : this.$t('StudyEpochForm.add_title')
    },
  },
  watch: {
    studyEpoch(value) {
      if (value) {
        studyEpochs
          .getStudyEpoch(this.selectedStudy.uid, value.uid)
          .then((resp) => {
            this.loadFromStudyEpoch(resp.data)
          })
      }
    },
    groups() {
      this.typeGroups = this.groups
      this.subtypeGroups = this.groups
    },
  },
  mounted() {
    this.fetchAllowedConfigs()
    units.getByDimension('TIME').then((resp) => {
      this.timeUnits = resp.data.items
    })
    if (this.studyEpoch) {
      this.loadFromStudyEpoch(this.studyEpoch)
      this.setEpochGroups()
    }
  },
  methods: {
    createMapping(codelist) {
      const returnValue = {}
      codelist.forEach((item) => {
        returnValue[item.term_uid] = item.sponsor_preferred_name
      })
      return returnValue
    },
    close() {
      this.$emit('close')
      this.form = {}
      this.colorHash = null
      this.$refs.observer.reset()
      this.typeGroups = this.groups
      this.subtypeGroups = this.groups
    },
    async cancel() {
      if (
        (!this.studyEpoch && !_isEmpty(this.form)) ||
        (this.studyEpoch && !_isEqual(this.form, this.studyEpoch))
      ) {
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
      } else {
        this.close()
      }
    },
    setEpochGroups() {
      let type = ''
      let subtype = ''
      if (!this.form.epoch_subtype && !this.form.epoch_type) {
        this.form.epoch = ''
        this.subtypeGroups = this.groups
        this.typeGroups = this.groups
        this.epochDisplay = ''
      } else if (!this.form.epoch_subtype) {
        this.form.epoch = ''
        type = this.form.epoch_type
        this.subtypeGroups = this.groups
        this.typeGroups = this.groups
        this.subtypeGroups = this.groups.filter(function (value) {
          return value.type === type
        })
        this.epochDisplay = ''
      } else if (!this.form.epoch_type) {
        this.form.epoch = ''
        subtype = this.form.epoch_subtype
        this.typeGroups = this.groups
        this.subtypeGroups = this.groups
        this.typeGroups = this.groups.filter(function (value) {
          return value.subtype === subtype
        })
        this.epochDisplay = ''
      } else {
        subtype = this.form.epoch_subtype
        type = this.form.epoch_type
        this.typeGroups = this.groups.filter(function (value) {
          return value.subtype === subtype
        })
        this.subtypeGroups = this.groups.filter(function (value) {
          return value.type === type
        })

        const data = {
          study_uid: this.selectedStudy.uid,
          epoch_subtype: subtype,
        }
        studyEpochs
          .getPreviewEpoch(this.selectedStudy.uid, data)
          .then((resp) => {
            this.form.epoch = resp.data.epoch
            this.epochDisplay = resp.data.epoch_name
          })
      }
    },
    async submit() {
      try {
        if (!this.studyEpoch) {
          await this.addObject()
        } else {
          await this.updateObject()
        }
        this.close()
      } finally {
        this.$refs.form.working = false
      }
    },
    addObject() {
      const data = JSON.parse(JSON.stringify(this.form))
      if (this.colorHash) {
        data.color_hash = this.colorHash
      } else {
        data.color_hash = '#BDBDBD'
      }
      data.study_uid = this.selectedStudy.uid
      return this.addStudyEpoch({
        studyUid: this.selectedStudy.uid,
        input: data,
      }).then(() => {
        this.fetchStudyEpochs({ studyUid: this.selectedStudy.uid })
        this.eventBusEmit('notification', {
          msg: this.$t('StudyEpochForm.add_success'),
        })
      })
    },
    updateObject() {
      const data = JSON.parse(JSON.stringify(this.form))
      if (this.colorHash) {
        data.color_hash =
          this.colorHash.hexa !== undefined
            ? this.colorHash.hexa
            : this.colorHash
      } else {
        data.color_hash = '#BDBDBD'
      }
      return this.updateStudyEpoch({
        studyUid: this.selectedStudy.uid,
        studyEpochUid: this.studyEpoch.uid,
        input: data,
      }).then(() => {
        this.fetchStudyEpochs({ studyUid: this.selectedStudy.uid })
        this.eventBusEmit('notification', {
          msg: this.$t('StudyEpochForm.update_success'),
        })
      })
    },
    loadFromStudyEpoch(studyEpoch) {
      this.form = { ...studyEpoch }
      this.form.epoch_type = this.uniqueTypeGroups.find(
        (group) => group.type_name === this.form.epoch_type_name
      )
      this.form.epoch_subtype = this.subtypeGroups.find(
        (group) => group.subtype_name === this.form.epoch_subtype_name
      ).subtype
      this.epochDisplay = studyEpoch.epoch_name
      if (studyEpoch.color_hash) {
        this.colorHash = studyEpoch.color_hash
      }
    },
  },
}
</script>
<style>
.v-color-picker__controls {
  display: none;
}
</style>
