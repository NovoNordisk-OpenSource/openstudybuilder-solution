<template>
  <div>
    <div class="d-flex page-title">
      {{ $t('StudyElements.study_element') + ': ' + element.name }}
      <v-chip
        :color="element.element_colour"
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
        icon="mdi-close"
        variant="text"
        @click="close"
      />
    </div>
    <v-card elevation="0" class="rounded-0">
      <v-card-text>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyElements.el_short_name') }}
          </v-col>
          <v-col cols="2">
            {{ element.short_name }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyElements.el_type') }}
          </v-col>
          <v-col cols="2">
            <CTTermDisplay :term="element.element_type" />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyElements.el_sub_type') }}
          </v-col>
          <v-col cols="2">
            <CTTermDisplay :term="element.element_subtype" />
          </v-col>
        </v-row>
        <v-row v-if="element.planned_duration">
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyElements.planned_duration') }}
          </v-col>
          <v-col cols="2">
            {{
              element.planned_duration.duration_value +
              ' ' +
              element.planned_duration.duration_unit_code.name
            }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyElements.el_start_rule') }}
          </v-col>
          <v-col cols="2">
            {{ element.start_rule }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyElements.el_end_rule') }}
          </v-col>
          <v-col cols="2">
            {{ element.end_rule }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('StudyElements.description') }}
          </v-col>
          <v-col cols="2">
            {{ element.description }}
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import arms from '@/api/arms'
import CTTermDisplay from '@/components/tools/CTTermDisplay.vue'

const router = useRouter()
const route = useRoute()

const element = ref({})

onMounted(() => {
  arms.getStudyElement(route.params.study_id, route.params.id).then((resp) => {
    element.value = resp.data
  })
})

function close() {
  router.push({ name: 'StudyStructure', params: { tab: 'elements' } })
}
</script>
