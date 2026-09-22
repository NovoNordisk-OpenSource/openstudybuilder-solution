<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('Sidebar.study.analysis_study_metadata_new') }}
      <HelpButton :help-text="$t('_help.SdtmSpecificationTable.general')" />
    </div>
    <NavigationTabs :tabs="tabs">
      <template #default="{ tabKeys }">
        <v-window-item :key="`mdvisit-${tabKeys.mdvisit}`" value="mdvisit">
          <AnalysisMetadataTable
            key="mdvisit"
            type="mdvisit"
            :headers="mdVisitHeaders"
          />
        </v-window-item>
        <v-window-item :key="`mdendpnt-${tabKeys.mdendpnt}`" value="mdendpnt">
          <AnalysisMetadataTable
            key="mdendpnt"
            type="mdendpnt"
            :headers="mdEndpntHeaders"
          >
            <template #[`item.OBJTV`]="{ item }">
              <div v-html="sanitizeHTML(item.OBJTV)" />
            </template>
            <template #[`item.RACT`]="{ item }">
              {{ $filters.itemList(item.RACT) }}
            </template>
            <template #[`item.ENDPNT`]="{ item }">
              <div v-html="sanitizeHTML(item.ENDPNT)" />
            </template>
            <template #[`item.RACTSGRP`]="{ item }">
              {{ $filters.itemList(item.RACTSGRP) }}
            </template>
            <template #[`item.RACTGRP`]="{ item }">
              {{ $filters.itemList(item.RACTGRP) }}
            </template>
            <template #[`item.RACTINST`]="{ item }">
              {{ $filters.itemList(item.RACTINST) }}
            </template>
            <template #[`item.TMFRM`]="{ item }">
              <div v-html="sanitizeHTML(item.TMFRM)" />
            </template>
          </AnalysisMetadataTable>
        </v-window-item>
        <v-window-item :key="`mdflow-${tabKeys.mdflow}`" value="mdflow">
          <AnalysisMetadataTable
            key="mdflow"
            type="mdflow"
            :headers="mdFlowHeaders"
          />
        </v-window-item>
      </template>
    </NavigationTabs>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import AnalysisMetadataTable from '@/components/studies/AnalysisMetadataTable.vue'
import HelpButton from '@/components/tools/HelpButton.vue'
import NavigationTabs from '@/components/tools/NavigationTabs.vue'
import { sanitizeHTML } from '@/utils/sanitize'

const { t } = useI18n()
const mdEndpntHeaders = [
  { title: t('AnalysisMetadataTable.study_id'), key: 'STUDYID_OBJ' },
  { title: t('AnalysisMetadataTable.objective_level'), key: 'OBJTVLVL' },
  { title: t('AnalysisMetadataTable.objective'), key: 'OBJTV' },
  { title: t('AnalysisMetadataTable.objective_plain_text'), key: 'OBJTVPT' },
  { title: t('AnalysisMetadataTable.endpoint_level'), key: 'ENDPNTLVL' },
  { title: t('AnalysisMetadataTable.endpoint_sub_level'), key: 'ENDPNTSL' },
  { title: t('AnalysisMetadataTable.endpoint_plain'), key: 'ENDPNT' },
  { title: t('AnalysisMetadataTable.endpoint_plain_text'), key: 'ENDPNTPT' },
  { title: t('AnalysisMetadataTable.unit_definition'), key: 'UNITDEF' },
  { title: t('AnalysisMetadataTable.unit'), key: 'UNIT' },
  { title: t('AnalysisMetadataTable.time_frame'), key: 'TMFRM' },
  { title: t('AnalysisMetadataTable.time_frame_plain_text'), key: 'TMFRMPT' },
  { title: t('AnalysisMetadataTable.related_activity_groups'), key: 'RACTGRP' },
  {
    title: t('AnalysisMetadataTable.related_activity_subgroups'),
    key: 'RACTSGRP',
  },
  { title: t('AnalysisMetadataTable.related_activities'), key: 'RACT' },
  {
    title: t('AnalysisMetadataTable.related_activity_instances'),
    key: 'RACTINST',
  },
]

const mdVisitHeaders = [
  { title: t('AnalysisMetadataTable.study_id'), key: 'STUDYID' },
  { title: t('AnalysisMetadataTable.visit_type_name'), key: 'VISTPCD' },
  { title: t('AnalysisMetadataTable.visit_num'), key: 'AVISITN' },
  { title: t('AnalysisMetadataTable.visit_name'), key: 'AVISIT' },
  { title: t('AnalysisMetadataTable.visit_short_label'), key: 'VISLABEL' },
  { title: t('AnalysisMetadataTable.day_name'), key: 'AVISIT1' },
  { title: t('AnalysisMetadataTable.day_value'), key: 'AVISIT1N' },
  { title: t('AnalysisMetadataTable.week_name'), key: 'AVISIT2' },
  { title: t('AnalysisMetadataTable.week_value'), key: 'AVISIT2N' },
]
const mdFlowHeaders = [
  { title: t('AnalysisMetadataTable.study_id'), key: 'STUDYID_FLOWCHART' },
  { title: t('AnalysisMetadataTable.visit_num'), key: 'AVISITN' },
  { title: t('AnalysisMetadataTable.param_code'), key: 'PARAMCD' },
  { title: t('AnalysisMetadataTable.visit_name'), key: 'AVISIT' },
  { title: t('AnalysisMetadataTable.param'), key: 'PARAM' },
  { title: t('AnalysisMetadataTable.paramn'), key: 'PARAMN' },
  { title: t('AnalysisMetadataTable.analysis_tpn'), key: 'ATPTN' },
  { title: t('AnalysisMetadataTable.analysis_tp'), key: 'ATPT' },
  { title: t('AnalysisMetadataTable.topic_code'), key: 'TOPICCD' },
  { title: t('AnalysisMetadataTable.baseline_type'), key: 'BASETYPE' },
  { title: t('AnalysisMetadataTable.baseline_record_flag'), key: 'ABLFL' },
  { title: t('AnalysisMetadataTable.assessment_type'), key: 'ASSMTYPE' },
]

const tabs = [
  { tab: 'mdvisit', name: t('AnalysisStudyMetadata.mdvisit') },
  { tab: 'mdendpnt', name: t('AnalysisStudyMetadata.mdendpnt') },
  { tab: 'mdflow', name: t('AnalysisStudyMetadata.mdflow') },
]
</script>
