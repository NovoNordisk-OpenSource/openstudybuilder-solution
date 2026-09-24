<template>
  <div>
    <div class="d-flex page-title">
      {{ $t('StudyArmsForm.study_arm') + ': ' + arm.name }}
      <v-chip
        :color="arm.arm_colour"
        size="small"
        class="mt-2 ml-2"
        variant="flat"
      >
        <span>&nbsp;</span>
        <span>&nbsp;</span>
      </v-chip>
      <v-spacer />
      <v-btn
        size="small"
        :title="$t('_global.close')"
        class="ml-2"
        variant="text"
        @click="close"
      >
        <v-icon>{{ 'mdi-close' }}</v-icon>
      </v-btn>
    </div>
    <v-card elevation="0" class="rounded-0">
      <v-card-text>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyArmsForm.arm_short_name') }}
          </v-col>
          <v-col cols="2">
            {{ arm.short_name }}
          </v-col>
        </v-row>
        <v-row v-if="arm.arm_type">
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyArmsForm.arm_type') }}
          </v-col>
          <v-col cols="2">
            <CTCodelistTermDisplay :term="arm.arm_type" />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyArmsForm.randomisation_group') }}
          </v-col>
          <v-col cols="2">
            {{ arm.randomization_group }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyArmsForm.arm_code') }}
          </v-col>
          <v-col cols="2">
            {{ arm.code }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyArmsForm.planned_number') }}
          </v-col>
          <v-col cols="2">
            {{ arm.number_of_subjects }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyArmsForm.description') }}
          </v-col>
          <v-col cols="2">
            {{ arm.description }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyArmsForm.connected_branches') }}
          </v-col>
          <v-col cols="10">
            <v-data-table
              class="elevation-0"
              :headers="branchesHeaders"
              :items="
                arm.arm_connected_branch_arms
                  ? arm.arm_connected_branch_arms
                  : []
              "
              item-value="branch_arm_uid"
            >
              <template #bottom />
              <template #[`item.name`]="{ item }">
                <router-link
                  :to="{
                    name: 'StudyBranchArmOverview',
                    params: {
                      study_id: selectedStudy.uid,
                      id: item.branch_arm_uid,
                      root_tab: $route.params.root_tab,
                    },
                  }"
                >
                  {{ item.name }}
                </router-link>
              </template>
            </v-data-table>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import arms from '@/api/arms'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import CTCodelistTermDisplay from '@/components/tools/CTCodelistTermDisplay.vue'

const router = useRouter()
const route = useRoute()
const { t } = useI18n()

const studiesGeneralStore = useStudiesGeneralStore()

const selectedStudy = computed(() => studiesGeneralStore.selectedStudy)

const arm = ref({})
const branchesHeaders = [
  { title: '#', key: 'order', width: '5%' },
  { title: t('StudyBranchArms.name'), key: 'name' },
  { title: t('StudyBranchArms.short_name'), key: 'short_name' },
  {
    title: t('StudyBranchArms.randomisation_group'),
    key: 'randomization_group',
  },
  { title: t('StudyBranchArms.code'), key: 'code' },
  { title: t('StudyBranchArms.description'), key: 'description' },
]

onMounted(() => {
  arms.getStudyArm(route.params.study_id, route.params.id).then((resp) => {
    arm.value = resp.data
  })
})

function close() {
  router.push({ name: 'StudyStructure', params: { tab: 'arms' } })
}
</script>
