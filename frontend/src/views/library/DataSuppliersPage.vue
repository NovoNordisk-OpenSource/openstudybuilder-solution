<template>
  <div class="px-4">
    <div class="page-title d-flex align-center justify-space-between">
      <div class="d-flex align-center">
        {{ $t('DataSupplierView.title') }}
        <HelpButton
          :help-text="$t('_help.DataSupplierView.DataSupplierTable.general')"
        />
      </div>
      <v-btn
        v-if="
          tab === 'rules-manager' &&
          !rulesManagerRef?.editMode &&
          accessGuard.checkPermission($roles.LIBRARY_WRITE)
        "
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        :title="$t('NNTableTooltips.edit')"
        data-cy="edit-rules"
        @click="rulesManagerRef?.enterEditMode()"
      >
        <v-icon>mdi-pencil-outline</v-icon>
      </v-btn>
    </div>
    <v-tabs v-model="tab" bg-color="white">
      <v-tab v-for="item of tabs" :key="item.tab" :value="item.tab">
        {{ item.name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab">
      <v-window-item value="data-suppliers">
        <DataSupplierTable />
      </v-window-item>
      <v-window-item value="rules-manager">
        <RulesManager ref="rulesManagerRef" />
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import DataSupplierTable from '@/components/library/DataSupplierTable.vue'
import RulesManager from '@/components/library/RulesManager.vue'
import HelpButton from '@/components/tools/HelpButton.vue'
import { useAccessGuard } from '@/composables/accessGuard'

const { t } = useI18n()
const accessGuard = useAccessGuard()

const tab = ref('data-suppliers')
const rulesManagerRef = ref(null)

const tabs = [
  { tab: 'data-suppliers', name: t('DataSupplierView.tab_data_suppliers') },
  { tab: 'rules-manager', name: t('DataSupplierView.tab_rules_manager') },
]
</script>
