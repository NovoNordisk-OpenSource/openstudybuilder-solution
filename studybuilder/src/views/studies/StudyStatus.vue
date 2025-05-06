<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('StudyStatusView.title') }} ({{ studiesGeneralStore.studyId }})
      <HelpButton width="800px">
        <div class="text-h6">
          {{ $t('_help.StudyStatus.core_attributes') }}
        </div>
        <div
          class="my-2"
          v-html="$t('_help.StudyStatus.core_attributes_body')"
        />
        <div class="text-h6">
          {{ $t('_help.StudyStatus.study_status') }}
        </div>
        <div class="my-2">
          {{ $t('_help.StudyStatus.content_line_1') }}
          <ul>
            <li v-html="$t('_help.StudyStatus.content_line_2')" />
            <li v-html="$t('_help.StudyStatus.content_line_3')" />
            <li v-html="$t('_help.StudyStatus.content_line_4')" />
          </ul>
          <p class="mt-2">
            {{ $t('_help.StudyStatus.content_line_5') }}
          </p>
          <p>{{ $t('_help.StudyStatus.content_line_6') }}</p>
        </div>
        <ul>
          <li>
            <span v-html="$t('_help.StudyStatus.content_line_7')" />
            <ul>
              <li v-html="$t('_help.StudyStatus.content_line_8')" />
            </ul>
          </li>
          <li>
            <span v-html="$t('_help.StudyStatus.content_line_9')" />
            <ul>
              <li v-html="$t('_help.StudyStatus.content_line_10')" />
            </ul>
          </li>
          <li>
            <span v-html="$t('_help.StudyStatus.content_line_11')" />
            <ul>
              <li v-html="$t('_help.StudyStatus.content_line_12')" />
            </ul>
          </li>
        </ul>

        <div class="text-h6 mt-2">
          {{ $t('_help.StudyStatus.study_sub_parts') }}
        </div>
        <div class="my-2">
          {{ $t('_help.StudyStatus.study_sub_parts_body') }}
        </div>
        <div class="text-h6">
          {{ $t('_help.StudyStatus.protocol_version') }}
        </div>
        <div class="my-2">
          {{ $t('_help.StudyStatus.protocol_version_body') }}
        </div>
      </HelpButton>
    </div>
    <NavigationTabs :tabs="tabs">
      <template #default="{ tabKeys }">
        <v-window-item value="core_attributes">
          <StudyIdentificationSummary
            :key="`core_attributes-${tabKeys.core_attributes}`"
          />
        </v-window-item>
        <v-window-item value="study_status">
          <StudyStatusTable :key="`study_status-${tabKeys.study_status}`" />
        </v-window-item>
        <v-window-item value="subparts">
          <StudySubpartsTable :key="`subparts-${tabKeys.subparts}`" />
        </v-window-item>
        <v-window-item value="protocolversions">
          <UnderConstruction
            :key="`protocolversions-${tabKeys.protocolversions}`"
          />
        </v-window-item>
      </template>
    </NavigationTabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import HelpButton from '@/components/tools/HelpButton.vue'
import NavigationTabs from '@/components/tools/NavigationTabs.vue'
import StudyIdentificationSummary from '@/components/studies/StudyIdentificationSummary.vue'
import StudyStatusTable from '@/components/studies/StudyStatusTable.vue'
import StudySubpartsTable from '@/components/studies/StudySubpartsTable.vue'
import UnderConstruction from '@/components/layout/UnderConstruction.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

const studiesGeneralStore = useStudiesGeneralStore()
const { t } = useI18n()

const tabs = ref([
  { tab: 'core_attributes', name: t('StudyStatusView.tab1_title') },
  { tab: 'study_status', name: t('StudyStatusView.tab2_title') },
  { tab: 'subparts', name: t('StudyStatusView.tab3_title') },
  { tab: 'protocolversions', name: t('StudyStatusView.tab4_title') },
])
</script>
