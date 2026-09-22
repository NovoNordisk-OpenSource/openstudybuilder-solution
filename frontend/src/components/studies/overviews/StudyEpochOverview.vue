<template>
  <div>
    <div class="d-flex page-title">
      {{ $t('StudyEpochForm.epoch') + ': ' + epoch.epoch_name }}
      <v-chip
        :color="epoch.color_hash"
        size="small"
        class="mt-3 ml-2"
        variant="flat"
      />
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
            {{ $t('StudyEpochForm.epoch_type') }}
          </v-col>
          <v-col cols="2">
            {{ epoch.epoch_type_name }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyEpochForm.epoch_subtype') }}
          </v-col>
          <v-col cols="2">
            {{ epoch.epoch_subtype_name }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyEpochForm.start_rule') }}
          </v-col>
          <v-col cols="2">
            {{ epoch.start_rule }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyEpochForm.stop_rule') }}
          </v-col>
          <v-col cols="2">
            {{ epoch.end_rule }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyEpochForm.visit_count') }}
          </v-col>
          <v-col cols="2">
            {{ epoch.study_visit_count }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyEpochForm.description') }}
          </v-col>
          <v-col cols="2">
            {{ epoch.description }}
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
import epochs from '@/api/studyEpochs'

export default {
  data() {
    return {
      epoch: {},
    }
  },
  mounted() {
    epochs
      .getStudyEpoch(this.$route.params.study_id, this.$route.params.id)
      .then((resp) => {
        this.epoch = resp.data
      })
  },
  methods: {
    close() {
      this.$router.push({ name: 'StudyStructure', params: { tab: 'epochs' } })
    },
  },
}
</script>
