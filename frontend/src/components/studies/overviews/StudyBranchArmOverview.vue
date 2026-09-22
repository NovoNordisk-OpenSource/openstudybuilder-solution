<template>
  <div>
    <div class="d-flex page-title">
      {{ $t('StudyBranchArms.study_branch_arm') + ': ' + branchArm.name }}
      <v-chip
        :color="branchArm.colour_code"
        size="small"
        class="mt-2 ml-2"
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
            {{ $t('StudyBranchArms.short_name') }}
          </v-col>
          <v-col cols="2">
            {{ branchArm.short_name }}
          </v-col>
        </v-row>
        <v-row v-if="branchArm.arm_root">
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyBranchArms.arm_name') }}
          </v-col>
          <v-col cols="2">
            <router-link
              :to="{
                name: 'StudyArmOverview',
                params: {
                  study_id: $route.params.study_id,
                  id: branchArm.arm_root.arm_uid,
                },
              }"
            >
              {{ branchArm.arm_root.name }}
            </router-link>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyBranchArms.randomisation_group') }}
          </v-col>
          <v-col cols="2">
            {{ branchArm.randomization_group }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyBranchArms.code') }}
          </v-col>
          <v-col cols="2">
            {{ branchArm.code }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyBranchArms.number_of_subjects') }}
          </v-col>
          <v-col cols="2">
            {{ branchArm.number_of_subjects }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyBranchArms.description') }}
          </v-col>
          <v-col cols="2">
            {{ branchArm.description }}
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
import arms from '@/api/arms'

export default {
  data() {
    return {
      branchArm: {},
    }
  },
  mounted() {
    arms
      .getStudyBranchArm(this.$route.params.study_id, this.$route.params.id)
      .then((resp) => {
        this.branchArm = resp.data
      })
  },
  methods: {
    close() {
      this.$router.push({
        name: 'StudyStructure',
        params: { tab: this.$route.params.root_tab },
      })
    },
  },
}
</script>
