<template>
  <v-card elevation="0" rounded="xl">
    <v-card-title>
      <span class="dialog-title">{{ $t('StudyCopyForm.title') }}</span>
    </v-card-title>
    <v-divider />
    <v-card-text>
      <v-form ref="observer">
        <v-row class="mt-4">
          <v-col cols="6">
            <v-autocomplete
              v-model="study"
              :label="$t('StudyQuickSelectForm.study_id')"
              :items="studiesWithId"
              data-cy="study-id"
              item-title="current_metadata.identification_metadata.study_id"
              item-value="uid"
              return-object
              :rules="[(value) => formRules.atleastone(value, study)]"
              clearable
              color="nnBaseBlue"
            />
          </v-col>
          <v-col cols="6">
            <v-autocomplete
              v-model="study"
              :label="$t('StudyQuickSelectForm.study_acronym')"
              :items="studiesWithAcronym"
              item-title="current_metadata.identification_metadata.study_acronym"
              item-value="uid"
              return-object
              :rules="[(value) => formRules.atleastone(value, study)]"
              clearable
              color="nnBaseBlue"
            />
          </v-col>
        </v-row>
        <v-spacer v-if="expand || expand2" />
        <v-row>
          <v-col cols="6">
            <v-text-field
              v-if="study"
              v-model="study.current_metadata.version_metadata.study_status"
              readonly
              color="nnBaseBlue"
            />
          </v-col>
        </v-row>
        <v-radio-group
          v-model="overwrite"
          hide-details
          :label="$t('StudyCopyForm.overwrite_content')"
          color="primary"
        >
          <v-radio
            :label="$t('_global.yes')"
            data-cy="overwrite-yes"
            :value="true"
          />
          <v-radio
            :label="$t('_global.no')"
            data-cy="overwrite-no"
            :value="false"
          />
        </v-radio-group>
      </v-form>
    </v-card-text>
    <v-divider />
    <v-card-actions>
      <v-spacer />
      <v-btn
        variant="outlined"
        rounded
        elevation="0"
        width="120px"
        @click="close"
      >
        {{ $t('_global.cancel') }}
      </v-btn>
      <v-btn
        data-cy="ok-form"
        rounded
        color="secondary"
        variant="flat"
        elevation="0"
        width="120px"
        @click="select"
      >
        {{ $t('_global.apply') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import { computed } from 'vue'
import study from '@/api/study'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  inject: ['formRules'],
  props: {
    component: {
      type: String,
      default: '',
    },
  },
  emits: ['apply', 'close'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
    }
  },
  data() {
    return {
      study: null,
      studies: [],
      expand: false,
      expand2: false,
      overwrite: false,
    }
  },
  computed: {
    studiesWithId() {
      return this.studies.filter(
        (study) => study.current_metadata.identification_metadata.study_id
      )
    },
    studiesWithAcronym() {
      return this.studies.filter(
        (study) => study.current_metadata.identification_metadata.study_acronym
      )
    },
  },
  mounted() {
    study.getAll().then((resp) => {
      this.studies = resp.data.items
    })
  },
  methods: {
    close() {
      this.$emit('close')
    },
    select() {
      const form = {
        reference_study_uid: this.study.uid,
        component_to_copy: this.component,
        overwrite: this.overwrite,
      }
      study.copyFromStudy(this.selectedStudy.uid, form).then((resp) => {
        switch (this.component) {
          case 'high_level_study_design':
            this.$emit(
              'apply',
              resp.data.current_metadata.high_level_study_design
            )
            break
          case 'study_intervention':
            this.$emit('apply', resp.data.current_metadata.study_intervention)
            break
          case 'study_population':
            this.$emit('apply', resp.data.current_metadata.study_population)
            break
        }
        this.close()
      })
    },
  },
}
</script>
