<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('DataModels.cdash') }}
      <HelpButton />
    </div>
    <NavigationTabs ref="nvTabs" :tabs="tabs">
      <template #default="{ tabKeys }">
        <v-window-item value="models">
          <DataExchangeStandardsModelsView
            :key="`models-${tabKeys.models}`"
            :headers="modelsHeaders"
            uid="CDASH"
            :redirect-model="redirectModel"
            @redirect-to-guide="redirectToGuide"
          />
        </v-window-item>
        <v-window-item value="guide">
          <DataExchangeStandardsGuideView
            :key="`guide-${tabKeys.guide}`"
            :headers="igHeaders"
            uid="CDASHIG"
            :redirect-guide="redirectGuide"
            @redirect-to-model="redirectToModel"
          />
        </v-window-item>
      </template>
    </NavigationTabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import DataExchangeStandardsModelsView from '@/components/library/DataExchangeStandardsModelsView.vue'
import DataExchangeStandardsGuideView from '@/components/library/DataExchangeStandardsGuideView.vue'
import HelpButton from '@/components/tools/HelpButton.vue'
import NavigationTabs from '@/components/tools/NavigationTabs.vue'

const { t } = useI18n()

const tabs = [
  { tab: 'models', name: t('DataModels.cdash_models') },
  { tab: 'guide', name: t('DataModels.cdash_ig') },
]

const nvTabs = ref()
const redirectModel = ref({})
const redirectGuide = ref({})
const modelsHeaders = ref([
  { title: t('DataModels.ordinal'), key: 'dataset_class.ordinal' },
  { title: t('_global.name'), key: 'uid' },
  { title: t('DataModels.label'), key: 'label' },
  { title: t('DataModels.definition'), key: 'description' },
  { title: t('DataModels.question_text'), key: 'question_text' },
  { title: t('DataModels.prompt'), key: 'prompt' },
  { title: t('DataModels.data_type'), key: 'simple_datatype' },
  { title: t('DataModels.impl_notes'), key: 'implementation_notes' },
  { title: t('DataModels.mapping_inst'), key: 'mapping_instructions' },
  { title: t('DataModels.mapping_targets'), key: 'has_mapping_target.uid' },
  { title: t('DataModels.code_list'), key: 'referenced_codelist.uid' },
])
const igHeaders = ref([
  { title: t('DataModels.ordinal'), key: 'dataset.ordinal' },
  { title: t('_global.name'), key: 'uid' },
  { title: t('DataModels.label'), key: 'label' },
  { title: t('DataModels.definition'), key: 'description' },
  { title: t('DataModels.question_text'), key: 'question_text' },
  { title: t('DataModels.prompt'), key: 'prompt' },
  { title: t('DataModels.data_type'), key: 'simple_datatype' },
  { title: t('DataModels.impl_notes'), key: 'implementation_notes' },
  { title: t('DataModels.mapping_inst'), key: 'mapping_instructions' },
  { title: t('DataModels.mapping_targets'), key: 'has_mapping_target.uid' },
  { title: t('DataModels.code_list'), key: 'referenced_codelist.uid' },
])

function redirectToGuide(item) {
  redirectGuide.value = item
  nvTabs.value.tab = 'guide'
}
function redirectToModel(item) {
  redirectModel.value = item
  nvTabs.value.tab = 'models'
}
</script>
