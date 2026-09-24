<template>
  <div class="px-4">
    <div class="d-flex page-title">
      {{ product.derived_name }}
      <v-spacer />
      <v-btn
        size="small"
        :title="$t('_global.close')"
        class="ml-2"
        variant="text"
        @click="close"
      >
        <v-icon icon="mdi-close"></v-icon>
      </v-btn>
    </div>
    <PharmaceuticalProductOverview :pharmaceutical-product="product" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import pharmaceuticalProductsApi from '@/api/concepts/pharmaceuticalProducts'
import PharmaceuticalProductOverview from '@/components/library/PharmaceuticalProductOverview.vue'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const route = useRoute()
const appStore = useAppStore()

const product = ref({})

pharmaceuticalProductsApi.getObject(route.params.id).then((resp) => {
  product.value = resp.data
  appStore.addBreadcrumbsLevel(
    product.value.derived_name,
    { name: 'PharmaceuticalProductOverview', params: route.params },
    4
  )
})

function close() {
  router.push({
    name: 'Interventions',
    params: { tab: 'pharmaceutical-products' },
  })
}
</script>
