<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('CriteriaView.title') }}
      <HelpButton :help-text="$t('_help.ObjectivesTable.general')" />
    </div>
    <v-tabs v-model="tab" bg-color="white">
      <v-tab
        v-for="type in criteriaTypes"
        :key="type.term_uid"
        :value="type.sponsor_preferred_name"
      >
        {{ type.name.sponsor_preferred_name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab">
      <v-window-item
        v-for="type in criteriaTypes"
        :key="type.term_uid"
        :value="type.sponsor_preferred_name"
      >
        <CriteriaTable
          :key="`${type.sponsor_preferred_name}-${tabKeys[type.sponsor_preferred_name]}`"
          :criteria-type="type"
        />
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import CriteriaTable from '@/components/library/CriteriaTable.vue'
import HelpButton from '@/components/tools/HelpButton.vue'
import terms from '@/api/controlledTerminology/terms'
import { useAppStore } from '@/stores/app'
import { useTabKeys } from '@/composables/tabKeys'

const router = useRouter()
const route = useRoute()
const appStore = useAppStore()
const { tabKeys, updateTabKey } = useTabKeys()

const criteriaTypes = ref([])
const tab = ref(null)

watch(tab, (newValue) => {
  router.push({
    name: 'CriteriaInstances',
    params: { tab: newValue },
  })
  updateTabKey(newValue)
  appStore.addBreadcrumbsLevel(newValue, undefined, 3, true)
})

onMounted(() => {
  terms.getTermsByCodelist('criteriaTypes', { unSorted: true }).then((resp) => {
    criteriaTypes.value = resp.data.items
    tab.value =
      route.params.tab || criteriaTypes.value[0].sponsor_preferred_name
  })
})
</script>
