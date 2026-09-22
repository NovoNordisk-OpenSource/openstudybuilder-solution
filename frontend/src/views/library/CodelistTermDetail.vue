<template>
  <div class="px-4">
    <div class="page-title">
      {{ $t('CodelistTermDetail.term_detail') }} ({{
        $t('CodelistTermDetail.term_uid')
      }}: {{ $route.params.term_id }})
    </div>
    <CodelistTermDetail :term-uid="$route.params.term_id" />
  </div>
</template>

<script>
import CodelistTermDetail from '@/components/library/CodelistTermDetail.vue'
import { useAppStore } from '@/stores/app'

export default {
  components: {
    CodelistTermDetail,
  },
  setup() {
    const appStore = useAppStore()
    return {
      addBreadcrumbsLevel: appStore.addBreadcrumbsLevel,
    }
  },
  data() {
    return {}
  },
  mounted() {
    this.addBreadcrumbsLevel(this.$t('CodeListDetail.code_list'))
    this.addBreadcrumbsLevel(this.$t('CodelistTermsView.terms'))
    this.addBreadcrumbsLevel(this.$t('CodelistTermDetail.term_detail'))
    this.addBreadcrumbsLevel(this.$route.params.term_id)
  },
}
</script>
