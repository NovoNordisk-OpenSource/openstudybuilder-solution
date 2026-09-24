<template>
  <div class="page-title d-flex align-center">
    {{ $t('Sidebar.study.sdtm_study') }}
    <HelpButton :help-text="$t('_help.SdtmSpecificationTable.general')" />
  </div>
  <NavigationTabs :tabs="tabs">
    <template #default="{ tabKeys }">
      <v-window-item value="tab-0">
        <SdtmDesignTable :key="`tab-0-${tabKeys['tab-0']}`" type="TA" />
      </v-window-item>
      <v-window-item value="tab-1">
        <SdtmDesignTable :key="`tab-1-${tabKeys['tab-1']}`" type="TE" />
      </v-window-item>
      <v-window-item value="tab-2">
        <SdtmDesignTable :key="`tab-2-${tabKeys['tab-2']}`" type="TV" />
      </v-window-item>
      <v-window-item value="tab-3">
        <SdtmDesignTable :key="`tab-3-${tabKeys['tab-3']}`" type="TI" />
      </v-window-item>
      <v-window-item value="tab-4">
        <SdtmDesignTable :key="`tab-4-${tabKeys['tab-4']}`" type="TDM" />
      </v-window-item>
      <v-window-item value="tab-5">
        <SdtmDesignTable :key="`tab-5-${tabKeys['tab-5']}`" type="TS" />
      </v-window-item>
    </template>
  </NavigationTabs>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import SdtmDesignTable from '@/components/studies/SdtmDesignTable.vue'
import HelpButton from '@/components/tools/HelpButton.vue'
import NavigationTabs from '@/components/tools/NavigationTabs.vue'

const { t } = useI18n()

const tabs = [
  { tab: 'tab-0', name: t('SdtmDesignTable.trial_arm') },
  { tab: 'tab-1', name: t('SdtmDesignTable.trial_elem') },
  { tab: 'tab-2', name: t('SdtmDesignTable.trial_visits') },
  { tab: 'tab-3', name: t('SdtmDesignTable.trial_incl_excl') },
  { tab: 'tab-4', name: t('SdtmDesignTable.trial_disease') },
  { tab: 'tab-5', name: t('SdtmDesignTable.trial_summary') },
]
</script>
