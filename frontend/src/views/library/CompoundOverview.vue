<template>
  <div class="px-4">
    <div class="d-flex page-title">
      {{ compound.name }}
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
    <CompoundOverview :compound="compound" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import CompoundOverview from '@/components/library/CompoundOverview.vue'
import compounds from '@/api/concepts/compounds'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const route = useRoute()
const appStore = useAppStore()

const compound = ref({})

compounds.getObject(route.params.id).then((resp) => {
  compound.value = resp.data
  appStore.addBreadcrumbsLevel(
    compound.value.name,
    { name: 'CompoundOverview', params: route.params },
    4
  )
})

function close() {
  router.push({ name: 'Interventions' })
}
</script>
