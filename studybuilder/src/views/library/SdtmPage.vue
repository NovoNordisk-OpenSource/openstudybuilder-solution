<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('DataModels.sdtm') }}
      <HelpButton />
    </div>
    <NavigationTabs ref="nvTabs" :tabs="tabs">
      <template #default="{ tabKeys }">
        <v-window-item value="models">
          <DataExchangeStandardsModelsView
            :key="`models-${tabKeys.models}`"
            :headers="modelsHeaders"
            uid="SDTM"
            :redirect-model="redirectModel"
            @redirect-to-guide="redirectToGuide"
          />
        </v-window-item>
        <v-window-item value="SDTMIG">
          <DataExchangeStandardsGuideView
            :key="`SDTMIG-${tabKeys.SDTMIG}`"
            :headers="igHeaders"
            uid="SDTMIG"
            :redirect-guide="redirectGuide"
            @redirect-to-model="redirectToModel"
            @redirect-to-model-with-variable="redirectToModelWithVariable"
          />
        </v-window-item>
        <v-window-item value="SDTMIG__AP">
          <DataExchangeStandardsGuideView
            :key="`SDTMIG__AP-${tabKeys.SDTMIG__AP}`"
            :headers="igHeaders"
            uid="SDTMIG__AP"
            :redirect-guide="redirectGuide"
            @redirect-to-model="redirectToModel"
            @redirect-to-model-with-variable="redirectToModelWithVariable"
          />
        </v-window-item>
        <v-window-item value="SDTMIG__MD">
          <DataExchangeStandardsGuideView
            :key="`SDTMIG__MD-${tabKeys.SDTMIG__MD}`"
            :headers="igHeaders"
            uvalue="SDTMIG__MD"
            :redirect-guide="redirectGuide"
            @redirect-to-model="redirectToModel"
            @redirect-to-model-with-variable="redirectToModelWithVariable"
          />
        </v-window-item>
        <v-window-item value="SENDIG">
          <DataExchangeStandardsGuideView
            :key="`SENDIG-${tabKeys.SENDIG}`"
            :headers="igHeaders"
            uvalue="SENDIG"
            :redirect-guide="redirectGuide"
            @redirect-to-model="redirectToModel"
            @redirect-to-model-with-variable="redirectToModelWithVariable"
          />
        </v-window-item>
        <v-window-item value="SENDIG__AR">
          <DataExchangeStandardsGuideView
            :key="`SENDIG__AR-${tabKeys.SENDIG__AR}`"
            :headers="igHeaders"
            uvalue="SENDIG__AR"
            :redirect-guide="redirectGuide"
            @redirect-to-model="redirectToModel"
            @redirect-to-model-with-variable="redirectToModelWithVariable"
          />
        </v-window-item>
        <v-window-item value="SENDIG__DART">
          <DataExchangeStandardsGuideView
            :key="`SENDIG__DART-${tabKeys.SENDIG__DART}`"
            :headers="igHeaders"
            uvalue="SENDIG__DART"
            :redirect-guide="redirectGuide"
            @redirect-to-model="redirectToModel"
            @redirect-to-model-with-variable="redirectToModelWithVariable"
          />
        </v-window-item>
        <v-window-item value="SENDIG__GENETOX">
          <DataExchangeStandardsGuideView
            :key="`SENDIG__GENETOX-${tabKeys.SENDIG__GENETOX}`"
            :headers="igHeaders"
            uid="SENDIG__GENETOX"
            :redirect-guide="redirectGuide"
            @redirect-to-model="redirectToModel"
            @redirect-to-model-with-variable="redirectToModelWithVariable"
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
  { tab: 'models', name: t('DataModels.sdtm_models') },
  { tab: 'SDTMIG', name: t('DataModels.sdtm_ig') },
  { tab: 'SDTMIG__AP', name: t('DataModels.sdtmig_ap') },
  { tab: 'SDTMIG__MD', name: t('DataModels.sdtmig_md') },
  { tab: 'SENDIG', name: t('DataModels.sendig') },
  { tab: 'SENDIG__AR', name: t('DataModels.sendig_ar') },
  { tab: 'SENDIG__DART', name: t('DataModels.sendig_dart') },
  { tab: 'SENDIG__GENETOX', name: t('DataModels.sendig_genetox') },
]

const nvTabs = ref()
const redirectModel = ref({})
const redirectGuide = ref({})
const modelsHeaders = ref([
  { title: t('DataModels.ordinal'), key: 'dataset_class.ordinal' },
  { title: t('_global.name'), key: 'uid' },
  { title: t('DataModels.label'), key: 'label' },
  { title: t('DataModels.data_type'), key: 'simple_datatype' },
  { title: t('DataModels.role'), key: 'role' },
  { title: t('DataModels.qualifies_variable'), key: 'qualifies_variable.uid' },
  {
    title: t('DataModels.described_value_domain'),
    key: 'described_value_domain',
  },
  { title: t('DataModels.notes'), key: 'notes' },
  { title: t('DataModels.usage_restrictions'), key: 'usage_restrictions' },
  { title: t('_global.description'), key: 'description' },
  { title: t('DataModels.c_code'), key: 'referenced_codelist.uid' },
  { title: t('DataModels.examples'), key: 'examples' },
])
const igHeaders = ref([
  { title: t('DataModels.ordinal'), key: 'dataset.ordinal' },
  { title: t('_global.name'), key: 'uid' },
  { title: t('DataModels.label'), key: 'label' },
  { title: t('DataModels.data_type'), key: 'simple_datatype' },
  { title: t('DataModels.role'), key: 'role' },
  { title: t('DataModels.core'), key: 'core' },
  { title: t('DataModels.codelist'), key: 'referenced_codelist.uid' },
  { title: t('DataModels.desc_value'), key: 'described_value_domain' },
  { title: t('DataModels.implements'), key: 'implements_variable.uid' },
  { title: t('DataModels.value_list'), key: 'value_list' },
  { title: t('_global.description'), key: 'description' },
])

function redirectToGuide(item) {
  redirectGuide.value = item
  nvTabs.value.tab = tabs.value.indexOf(
    tabs.value.find((tab) => tab.tab === item.uid)
  )
}
function redirectToModel(item) {
  redirectModel.value = item
  nvTabs.value.tab = 'models'
}
function redirectToModelWithVariable(data) {
  redirectModel.value = data
  nvTabs.value.tab = 'models'
}
</script>
