<template>
  <div>
    <div class="d-flex page-title">
      {{ $t('StudyVisitForm.study_visit') + ': ' + visit.visit_name }}
      <v-spacer />
      <v-btn
        size="small"
        :title="$t('_global.close')"
        class="ml-2"
        icon="mdi-close"
        variant="text"
        @click="close"
      />
    </div>
    <v-card elevation="0" class="rounded-0">
      <v-card-text>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyVisitForm.vtype_step_label') }}
          </v-col>
          <v-col cols="2">
            {{
              visit.visit_class
                ? visitClasses.find((cl) => cl.value === visit.visit_class)
                    .label
                : ''
            }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyVisitForm.period') }}
          </v-col>
          <v-col cols="2">
            {{
              visit.study_epoch_uid && epochs.length
                ? epochs.find((epoch) => epoch.uid === visit.study_epoch_uid)
                    .epoch_name
                : ''
            }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyVisitForm.visit_short_name') }}
          </v-col>
          <v-col cols="2">
            {{ visit.visit_short_name }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyVisitForm.visit_type') }}
          </v-col>
          <v-col cols="2">
            {{ visit.visit_type_name }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyVisitForm.contact_mode') }}
          </v-col>
          <v-col cols="2">
            {{ visit.visit_contact_mode_name }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyVisitForm.anchor_visit') }}
          </v-col>
          <v-col cols="2">
            {{ $filters.yesno(visit.is_global_anchor_visit) }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyVisitForm.time_reference') }}
          </v-col>
          <v-col cols="2">
            {{ visit.time_reference_name }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyVisitForm.time_reference') }}
          </v-col>
          <v-col cols="2">
            {{ visit.visit_sublabel_reference }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyVisitForm.time_dist') }}
          </v-col>
          <v-col cols="2">
            {{ visit.time_value + ' ' + visit.time_unit_name }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyVisitForm.study_day_label') }}
          </v-col>
          <v-col cols="2">
            {{ visit.study_day_label }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyVisitForm.study_week_label') }}
          </v-col>
          <v-col cols="2">
            {{ visit.study_week_label }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyVisitForm.visit_window') }}
          </v-col>
          <v-col cols="2">
            {{ visit.min_visit_window_value }} /
            {{ visit.max_visit_window_value }}
            {{ visit.visit_window_unit_name }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyVisitForm.visit_description') }}
          </v-col>
          <v-col cols="2">
            {{ visit.description }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyVisitForm.epoch_allocation') }}
          </v-col>
          <v-col cols="2">
            {{ visit.epoch_allocation_name }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyVisitForm.visit_start_rule') }}
          </v-col>
          <v-col cols="2">
            {{ visit.start_rule }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyVisitForm.visit_stop_rule') }}
          </v-col>
          <v-col cols="2">
            {{ visit.end_rule }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyVisitForm.visit_notes') }}
          </v-col>
          <v-col cols="2">
            {{ visit.note }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyVisitForm.show_visit') }}
          </v-col>
          <v-col cols="2">
            {{ $filters.yesno(visit.show_visit) }}
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
import studyEpochs from '@/api/studyEpochs'
import visitConstants from '@/constants/visits'
import { computed } from 'vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
    }
  },
  data() {
    return {
      visit: {},
      visitClasses: [
        {
          label: this.$t('StudyVisitForm.scheduled_visit'),
          value: visitConstants.CLASS_SINGLE_VISIT,
        },
        {
          label: this.$t('StudyVisitForm.unscheduled_visit'),
          value: visitConstants.CLASS_UNSCHEDULED_VISIT,
        },
        {
          label: this.$t('StudyVisitForm.non_visit'),
          value: visitConstants.CLASS_NON_VISIT,
        },
        {
          label: this.$t('StudyVisitForm.special_visit'),
          value: visitConstants.CLASS_SPECIAL_VISIT,
        },
        {
          label: this.$t('StudyVisitForm.insertion_visit'),
          value: visitConstants.CLASS_INSERTION_VISIT,
        },
      ],
      epochs: [],
    }
  },
  mounted() {
    studyEpochs
      .getStudyVisit(this.$route.params.study_id, this.$route.params.id)
      .then((resp) => {
        this.visit = resp.data
      })
    studyEpochs.getStudyEpochs(this.selectedStudy.uid).then((resp) => {
      this.epochs = resp.data.items
    })
  },
  methods: {
    close() {
      this.$router.push({ name: 'StudyStructure', params: { tab: 'visits' } })
    },
  },
}
</script>
