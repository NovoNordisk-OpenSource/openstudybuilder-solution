<template>
  <div class="px-4">
    <div class="page-title">
      {{ $t('CtPackageCodelistHistoryView.title') }}
    </div>
    <CtPackageCodelistHistory
      :catalogue-name="$route.params.catalogue_name"
      :codelist-uid="$route.params.codelist_id"
      :from-date="$route.query.fromDate"
      :to-date="$route.query.toDate"
    />
  </div>
</template>

<script>
import CtPackageCodelistHistory from '@/components/library/CtPackageCodelistHistory.vue'
import { useAppStore } from '@/stores/app'

export default {
  components: {
    CtPackageCodelistHistory,
  },
  setup() {
    const appStore = useAppStore()
    return {
      addBreadcrumbsLevel: appStore.addBreadcrumbsLevel,
    }
  },
  mounted() {
    this.addBreadcrumbsLevel(this.$route.params.codelist_id)
  },
}
</script>
