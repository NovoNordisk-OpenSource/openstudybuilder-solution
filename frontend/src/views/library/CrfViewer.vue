<template>
  <div class="px-4">
    <div class="d-flex page-title">
      {{ $t('CRFViewer.title') }}
    </div>
    <NavigationTabs :tabs="tabs" :breadcrumbs-level="2">
      <template #default>
        <v-window-item value="odm-viewer">
          <OdmViewer />
        </v-window-item>
      </template>
    </NavigationTabs>
  </div>
</template>

<script setup>
import OdmViewer from '@/components/library/crfs/OdmViewer.vue'
import { useI18n } from 'vue-i18n'
import NavigationTabs from '@/components/tools/NavigationTabs.vue'

const { t } = useI18n()

const tabs = [{ tab: 'odm-viewer', name: t('CRFViewer.tab1_title') }]
</script>
