<template>
  <div class="px-4">
    <div class="page-title">
      {{ codelistAttributes.name }} ({{ $route.params.codelist_id }}) -
      {{ codelistAttributes.submission_value }} /
      {{ $t('CodelistTermsView.terms_listing') }}
    </div>
    <CodelistTermTable
      :catalogue-name="$route.params.catalogue_name"
      :codelist-uid="$route.params.codelist_id"
    />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'
import { useRoute } from 'vue-router'
import controlledTerminology from '@/api/controlledTerminology'
import CodelistTermTable from '@/components/library/CodelistTermTable.vue'

const { t } = useI18n()
const appStore = useAppStore()
const route = useRoute()

const codelistAttributes = ref({})

onMounted(() => {
  appStore.addBreadcrumbsLevel(
    route.params.codelist_id,
    { name: 'CodeListDetail', params: route.params },
    4
  )
  appStore.addBreadcrumbsLevel(t('CodelistTermsView.terms'), {
    name: 'CodelistTerms',
    params: route.params,
  })
  controlledTerminology
    .getCodelistAttributes(route.params.codelist_id)
    .then((resp) => {
      codelistAttributes.value = resp.data
    })
})
</script>
