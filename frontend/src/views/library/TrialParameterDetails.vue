<template>
  <TrialParameterDetails :term-uid="$route.params.term_id" />
</template>
<script setup>
import TrialParameterDetails from '@/components/library/TrialParameterDetails.vue'
import { useAppStore } from '@/stores/app'
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const appStore = useAppStore()

onMounted(() => {
  appStore.addBreadcrumbsLevel(
    t('CodeListDetail.code_list'),
    { name: 'TrialSummaryParameters' },
    1,
    false
  )

  appStore.addBreadcrumbsLevel(
    t('TrialSummaryParameters.title'),
    { name: 'TrialSummaryParameters' },
    2,
    true
  )
})
</script>
